from django.conf import settings
from django.test import TestCase

from ..decorators import skipIntegration


@skipIntegration
class TestEnv(TestCase):

    def test_happy(self):
        """
        Non-Default values for settings are loaded

        Vanilla MSDCRM11 needs custom configuration - if the defaults from
        settings are in place then tests will fail.
        """
        self.assertNotEqual(settings.CDMS_BASE_URL, 'https://example.com')
        self.assertNotEqual(settings.CDMS_USERNAME, 'username')
        self.assertNotEqual(settings.CDMS_PASSWORD, 'password')
