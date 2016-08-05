from unittest.mock import patch

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


class TestMakeRequest(TestCase):
    """
    Simple mocked test to ensure that parts are in place.
    """

    expected_headers = {
        'Content-type': 'application/json',
        'Accept': 'application/json',
    }

    def setUp(self):
        """
        Set up request's Session object to have a mocked out 'get' function
        verb that returns a simple string as response.
        """
        super().setUp()
        self.auth = NTLMAuth()
        p_get = patch.object(Session, 'get', autospec=True)
        self.m_get = p_get.start()
        self.m_get.return_value = '__RESPONSE__'
        self.addCleanup(p_get.stop)

    def test_get_passthrough(self):
        """
        NTLMAuth make_request does GET with no data using its session
        """
        result = self.auth.make_request('get', '__URL__')

        self.assertEqual(result, '__RESPONSE__')
        self.m_get.assert_called_once_with(
            self.auth.session,
            '__URL__',
            data={},
            headers=self.expected_headers,
        )

    def test_get_passthrough_data(self):
        """
        NTLMAuth make_request does GET with data encoded using its session
        """
        data = {
            '__KEY__': '__VALUE__',
        }

        result = self.auth.make_request('get', '__URL__', data=data)

        self.assertEqual(result, '__RESPONSE__')
        expected_data = '{"__KEY__": "__VALUE__"}'
        self.m_get.assert_called_once_with(
            self.auth.session,
            '__URL__',
            data=expected_data,
            headers=self.expected_headers,
        )
