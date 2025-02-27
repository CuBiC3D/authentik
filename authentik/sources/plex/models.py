"""Plex source"""
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from rest_framework.fields import CharField
from rest_framework.serializers import BaseSerializer

from authentik.core.models import Source, UserSourceConnection
from authentik.core.types import UILoginButton
from authentik.flows.challenge import Challenge, ChallengeTypes
from authentik.providers.oauth2.generators import generate_client_id


class PlexAuthenticationChallenge(Challenge):
    """Challenge shown to the user in identification stage"""

    client_id = CharField()
    slug = CharField()


class PlexSource(Source):
    """Authenticate against plex.tv"""

    client_id = models.TextField(
        default=generate_client_id,
        help_text=_("Client identifier used to talk to Plex."),
    )
    allowed_servers = ArrayField(
        models.TextField(),
        default=list,
        blank=True,
        help_text=_(
            (
                "Which servers a user has to be a member of to be granted access. "
                "Empty list allows every server."
            )
        ),
    )
    allow_friends = models.BooleanField(
        default=True,
        help_text=_("Allow friends to authenticate, even if you don't share a server."),
    )
    plex_token = models.TextField(help_text=_("Plex token used to check firends"))

    @property
    def component(self) -> str:
        return "ak-source-plex-form"

    @property
    def serializer(self) -> BaseSerializer:
        from authentik.sources.plex.api import PlexSourceSerializer

        return PlexSourceSerializer

    @property
    def ui_login_button(self) -> UILoginButton:
        return UILoginButton(
            challenge=PlexAuthenticationChallenge(
                {
                    "type": ChallengeTypes.NATIVE.value,
                    "component": "ak-flow-sources-plex",
                    "client_id": self.client_id,
                    "slug": self.slug,
                }
            ),
            icon_url=static("authentik/sources/plex.svg"),
            name=self.name,
        )

    class Meta:

        verbose_name = _("Plex Source")
        verbose_name_plural = _("Plex Sources")


class PlexSourceConnection(UserSourceConnection):
    """Connect user and plex source"""

    plex_token = models.TextField()
    identifier = models.TextField()

    class Meta:

        verbose_name = _("User Plex Source Connection")
        verbose_name_plural = _("User Plex Source Connections")
