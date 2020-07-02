"""user field matcher models"""
from django.db import models
from django.utils.translation import gettext as _

from passbook.core.models import Group
from passbook.policies.models import Policy
from passbook.policies.types import PolicyRequest, PolicyResult


class GroupMembershipPolicy(Policy):
    """Check that the user is member of the selected group."""

    group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL)

    form = "passbook.policies.group_membership.forms.GroupMembershipPolicyForm"

    def passes(self, request: PolicyRequest) -> PolicyResult:
        return PolicyResult(self.group.user_set.filter(pk=request.user.pk).exists())

    class Meta:

        verbose_name = _("Group Membership Policy")
        verbose_name_plural = _("Group Membership Policies")