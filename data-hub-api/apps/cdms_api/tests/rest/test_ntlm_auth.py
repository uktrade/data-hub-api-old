from django.core.exceptions import ImproperlyConfigured
from django.test.testcases import TestCase, override_settings
from requests import Session
from requests_ntlm import HttpNtlmAuth

from ...rest.auth.ntlm import NTLMAuth


class TestInit(TestCase):

    def test_happy(self):
        """
        NTLMAuth inits a session containing an HttpNtlmAuth instance
        """
        result = NTLMAuth()

        self.assertIsInstance(result.session, Session)
        self.assertIsInstance(result.session.auth, HttpNtlmAuth)

    @override_settings(CDMS_BASE_URL='')
    def test_missing_base_url(self):
        """
        NTLMAuth raises if CDMS_BASE_URL is not in settings
        """
        with self.assertRaises(ImproperlyConfigured) as context_manager:
            NTLMAuth()

        self.assertIn('CDMS_BASE_URL', context_manager.exception.args[0])

    @override_settings(CDMS_USERNAME='')
    def test_missing_username(self):
        """
        NTLMAuth raises if CDMS_USERNAME is not in settings
        """
        with self.assertRaises(ImproperlyConfigured) as context_manager:
            NTLMAuth()

        self.assertIn('CDMS_USERNAME', context_manager.exception.args[0])

    @override_settings(CDMS_PASSWORD='')
    def test_missing_password(self):
        """
        NTLMAuth raises if CDMS_PASSWORD is not in settings
        """
        with self.assertRaises(ImproperlyConfigured) as context_manager:
            NTLMAuth()

        self.assertIn('CDMS_PASSWORD', context_manager.exception.args[0])
