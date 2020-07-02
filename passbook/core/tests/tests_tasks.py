"""passbook user view tests"""
from django.test import TestCase
from django.utils.timezone import now
from guardian.shortcuts import get_anonymous_user

from passbook.core.models import Token
from passbook.core.tasks import clean_tokens


class TestTasks(TestCase):
    """Test Tasks"""

    def test_token_cleanup(self):
        """Test Token cleanup task"""
        Token.objects.create(expires=now(), user=get_anonymous_user())
        self.assertEqual(Token.objects.all().count(), 1)
        clean_tokens()
        self.assertEqual(Token.objects.all().count(), 0)