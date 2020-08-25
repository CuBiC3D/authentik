"""passbook proxy models"""
from typing import Optional, Type

from django.core.validators import URLValidator
from django.db import models
from django.forms import ModelForm
from django.http import HttpRequest
from django.utils.translation import gettext as _

from passbook.lib.utils.template import render_to_string
from passbook.providers.oauth2.constants import (
    SCOPE_OPENID,
    SCOPE_OPENID_EMAIL,
    SCOPE_OPENID_PROFILE,
)
from passbook.providers.oauth2.models import (
    ClientTypes,
    JWTAlgorithms,
    OAuth2Provider,
    ResponseTypes,
    ScopeMapping,
)


class ProxyProvider(OAuth2Provider):
    """Protect applications that don't support any of the other
    Protocols by using a Reverse-Proxy."""

    internal_host = models.TextField(
        validators=[URLValidator(schemes=("http", "https"))]
    )
    external_host = models.TextField(
        validators=[URLValidator(schemes=("http", "https"))]
    )

    def form(self) -> Type[ModelForm]:
        from passbook.providers.proxy.forms import ProxyProviderForm

        return ProxyProviderForm

    def html_setup_urls(self, request: HttpRequest) -> Optional[str]:
        """return template and context modal with URLs for authorize, token, openid-config, etc"""
        from passbook.providers.proxy.views import DockerComposeView

        docker_compose_yaml = DockerComposeView(request=request).get_compose(self)
        return render_to_string(
            "providers/proxy/setup_modal.html",
            {"provider": self, "docker_compose": docker_compose_yaml},
        )

    def set_oauth_defaults(self):
        """Ensure all OAuth2-related settings are correct"""
        self.client_type = ClientTypes.CONFIDENTIAL
        self.response_type = ResponseTypes.CODE
        self.jwt_alg = JWTAlgorithms.HS256
        scopes = ScopeMapping.objects.filter(
            scope_name__in=[SCOPE_OPENID, SCOPE_OPENID_PROFILE, SCOPE_OPENID_EMAIL]
        )
        self.property_mappings.set(scopes)
        self.redirect_uris = "\n".join(
            [
                f"{self.external_host}/oauth2/callback",
                f"{self.internal_host}/oauth2/callback",
            ]
        )

    def __str__(self):
        return self.name

    class Meta:

        verbose_name = _("Proxy Provider")
        verbose_name_plural = _("Proxy Providers")