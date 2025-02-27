"""Source decision helper"""
from enum import Enum
from typing import Any, Optional, Type

from django.contrib import messages
from django.db import IntegrityError
from django.db.models.query_utils import Q
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from structlog.stdlib import get_logger

from authentik.core.models import (
    Source,
    SourceUserMatchingModes,
    User,
    UserSourceConnection,
)
from authentik.core.sources.stage import (
    PLAN_CONTEXT_SOURCES_CONNECTION,
    PostUserEnrollmentStage,
)
from authentik.events.models import Event, EventAction
from authentik.flows.models import Flow, Stage, in_memory_stage
from authentik.flows.planner import (
    PLAN_CONTEXT_PENDING_USER,
    PLAN_CONTEXT_REDIRECT,
    PLAN_CONTEXT_SOURCE,
    PLAN_CONTEXT_SSO,
    FlowPlanner,
)
from authentik.flows.views import NEXT_ARG_NAME, SESSION_KEY_GET, SESSION_KEY_PLAN
from authentik.lib.utils.urls import redirect_with_qs
from authentik.policies.utils import delete_none_keys
from authentik.stages.password.stage import PLAN_CONTEXT_AUTHENTICATION_BACKEND
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT


class Action(Enum):
    """Actions that can be decided based on the request
    and source settings"""

    LINK = "link"
    AUTH = "auth"
    ENROLL = "enroll"
    DENY = "deny"


class SourceFlowManager:
    """Help sources decide what they should do after authorization. Based on source settings and
    previous connections, authenticate the user, enroll a new user, link to an existing user
    or deny the request."""

    source: Source
    request: HttpRequest

    identifier: str

    connection_type: Type[UserSourceConnection] = UserSourceConnection

    def __init__(
        self,
        source: Source,
        request: HttpRequest,
        identifier: str,
        enroll_info: dict[str, Any],
    ) -> None:
        self.source = source
        self.request = request
        self.identifier = identifier
        self.enroll_info = enroll_info
        self._logger = get_logger().bind(source=source, identifier=identifier)

    # pylint: disable=too-many-return-statements
    def get_action(self, **kwargs) -> tuple[Action, Optional[UserSourceConnection]]:
        """decide which action should be taken"""
        new_connection = self.connection_type(
            source=self.source, identifier=self.identifier
        )
        # When request is authenticated, always link
        if self.request.user.is_authenticated:
            new_connection.user = self.request.user
            new_connection = self.update_connection(new_connection, **kwargs)
            new_connection.save()
            return Action.LINK, new_connection

        existing_connections = self.connection_type.objects.filter(
            source=self.source, identifier=self.identifier
        )
        if existing_connections.exists():
            connection = existing_connections.first()
            return Action.AUTH, self.update_connection(connection, **kwargs)
        # No connection exists, but we match on identifier, so enroll
        if self.source.user_matching_mode == SourceUserMatchingModes.IDENTIFIER:
            # We don't save the connection here cause it doesn't have a user assigned yet
            return Action.ENROLL, self.update_connection(new_connection, **kwargs)

        # Check for existing users with matching attributes
        query = Q()
        # Either query existing user based on email or username
        if self.source.user_matching_mode in [
            SourceUserMatchingModes.EMAIL_LINK,
            SourceUserMatchingModes.EMAIL_DENY,
        ]:
            if not self.enroll_info.get("email", None):
                self._logger.warning("Refusing to use none email", source=self.source)
                return Action.DENY, None
            query = Q(email__exact=self.enroll_info.get("email", None))
        if self.source.user_matching_mode in [
            SourceUserMatchingModes.USERNAME_LINK,
            SourceUserMatchingModes.USERNAME_DENY,
        ]:
            if not self.enroll_info.get("username", None):
                self._logger.warning(
                    "Refusing to use none username", source=self.source
                )
                return Action.DENY, None
            query = Q(username__exact=self.enroll_info.get("username", None))
        self._logger.debug("trying to link with existing user", query=query)
        matching_users = User.objects.filter(query)
        # No matching users, always enroll
        if not matching_users.exists():
            self._logger.debug("no matching users found, enrolling")
            return Action.ENROLL, self.update_connection(new_connection, **kwargs)

        user = matching_users.first()
        if self.source.user_matching_mode in [
            SourceUserMatchingModes.EMAIL_LINK,
            SourceUserMatchingModes.USERNAME_LINK,
        ]:
            new_connection.user = user
            new_connection = self.update_connection(new_connection, **kwargs)
            new_connection.save()
            return Action.LINK, new_connection
        if self.source.user_matching_mode in [
            SourceUserMatchingModes.EMAIL_DENY,
            SourceUserMatchingModes.USERNAME_DENY,
        ]:
            self._logger.info("denying source because user exists", user=user)
            return Action.DENY, None
        # Should never get here as default enroll case is returned above.
        return Action.DENY, None

    def update_connection(
        self, connection: UserSourceConnection, **kwargs
    ) -> UserSourceConnection:
        """Optionally make changes to the connection after it is looked up/created."""
        return connection

    def get_flow(self, **kwargs) -> HttpResponse:
        """Get the flow response based on user_matching_mode"""
        try:
            action, connection = self.get_action(**kwargs)
        except IntegrityError as exc:
            self._logger.warning("failed to get action", exc=exc)
            return redirect("/")
        self._logger.debug("get_action() says", action=action, connection=connection)
        if connection:
            if action == Action.LINK:
                self._logger.debug("Linking existing user")
                return self.handle_existing_user_link(connection)
            if action == Action.AUTH:
                self._logger.debug("Handling auth user")
                return self.handle_auth_user(connection)
            if action == Action.ENROLL:
                self._logger.debug("Handling enrollment of new user")
                return self.handle_enroll(connection)
        # Default case, assume deny
        messages.error(
            self.request,
            _(
                (
                    "Request to authenticate with %(source)s has been denied. Please authenticate "
                    "with the source you've previously signed up with."
                )
                % {"source": self.source.name}
            ),
        )
        return redirect("/")

    # pylint: disable=unused-argument
    def get_stages_to_append(self, flow: Flow) -> list[Stage]:
        """Hook to override stages which are appended to the flow"""
        if flow.slug == self.source.enrollment_flow.slug:
            return [
                in_memory_stage(PostUserEnrollmentStage),
            ]
        return []

    def _handle_login_flow(self, flow: Flow, **kwargs) -> HttpResponse:
        """Prepare Authentication Plan, redirect user FlowExecutor"""
        # Ensure redirect is carried through when user was trying to
        # authorize application
        final_redirect = self.request.session.get(SESSION_KEY_GET, {}).get(
            NEXT_ARG_NAME, "authentik_core:if-admin"
        )
        kwargs.update(
            {
                # Since we authenticate the user by their token, they have no backend set
                PLAN_CONTEXT_AUTHENTICATION_BACKEND: "django.contrib.auth.backends.ModelBackend",
                PLAN_CONTEXT_SSO: True,
                PLAN_CONTEXT_SOURCE: self.source,
                PLAN_CONTEXT_REDIRECT: final_redirect,
            }
        )
        if not flow:
            return HttpResponseBadRequest()
        # We run the Flow planner here so we can pass the Pending user in the context
        planner = FlowPlanner(flow)
        plan = planner.plan(self.request, kwargs)
        for stage in self.get_stages_to_append(flow):
            plan.append(stage)
        self.request.session[SESSION_KEY_PLAN] = plan
        return redirect_with_qs(
            "authentik_core:if-flow",
            self.request.GET,
            flow_slug=flow.slug,
        )

    # pylint: disable=unused-argument
    def handle_auth_user(
        self,
        connection: UserSourceConnection,
    ) -> HttpResponse:
        """Login user and redirect."""
        messages.success(
            self.request,
            _(
                "Successfully authenticated with %(source)s!"
                % {"source": self.source.name}
            ),
        )
        flow_kwargs = {PLAN_CONTEXT_PENDING_USER: connection.user}
        return self._handle_login_flow(self.source.authentication_flow, **flow_kwargs)

    def handle_existing_user_link(
        self,
        connection: UserSourceConnection,
    ) -> HttpResponse:
        """Handler when the user was already authenticated and linked an external source
        to their account."""
        # Connection has already been saved
        Event.new(
            EventAction.SOURCE_LINKED,
            message="Linked Source",
            source=self.source,
        ).from_http(self.request)
        messages.success(
            self.request,
            _("Successfully linked %(source)s!" % {"source": self.source.name}),
        )
        # When request isn't authenticated we jump straight to auth
        if not self.request.user.is_authenticated:
            return self.handle_auth_user(connection)
        return redirect(
            reverse(
                "authentik_core:if-admin",
            )
            + f"#/user;page-{self.source.slug}"
        )

    def handle_enroll(
        self,
        connection: UserSourceConnection,
    ) -> HttpResponse:
        """User was not authenticated and previous request was not authenticated."""
        messages.success(
            self.request,
            _(
                "Successfully authenticated with %(source)s!"
                % {"source": self.source.name}
            ),
        )

        # We run the Flow planner here so we can pass the Pending user in the context
        if not self.source.enrollment_flow:
            self._logger.warning("source has no enrollment flow")
            return HttpResponseBadRequest()
        return self._handle_login_flow(
            self.source.enrollment_flow,
            **{
                PLAN_CONTEXT_PROMPT: delete_none_keys(self.enroll_info),
                PLAN_CONTEXT_SOURCES_CONNECTION: connection,
            },
        )
