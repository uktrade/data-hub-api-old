from django.conf import settings
from django.test import TestCase


class TestEnv(TestCase):

    def test_happy(self):
        """
        Default values for settings are loaded

        This serves to test the default fall through for these settings since
        they can be overridden by the environment.
        """
        self.assertEqual(settings.CDMS_BASE_URL, 'https://example.com')
        self.assertEqual(settings.CDMS_USERNAME, 'username')
        self.assertEqual(settings.CDMS_PASSWORD, 'password')
        with self.assertRaises(AttributeError):
            settings.TEST_INTEGRATION
