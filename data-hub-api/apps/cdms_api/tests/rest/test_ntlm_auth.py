from unittest.mock import Mock, patch

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
        patch_get = patch.object(Session, 'get', autospec=True)
        self.mock_get = patch_get.start()
        self.response = Mock(name='Response')
        self.mock_get.return_value = self.response
        self.addCleanup(patch_get.stop)

    def test_get_passthrough(self):
        """
        NTLMAuth make_request does GET with no data using its session
        """
        self.response.status_code = 404

        result = self.auth.make_request('get', '__URL__')

        self.assertEqual(result, self.response)
        self.mock_get.assert_called_once_with(
            self.auth.session,
            '__URL__',
            data={},
            headers=self.expected_headers,
        )

    def test_get_passthrough_data(self):
        """
        NTLMAuth make_request does GET with data encoded using its session
        """
        self.response.status_code = 404
        data = {
            '__KEY__': '__VALUE__',
        }

        result = self.auth.make_request('get', '__URL__', data=data)

        self.assertEqual(result, self.response)
        expected_data = '{"__KEY__": "__VALUE__"}'
        self.mock_get.assert_called_once_with(
            self.auth.session,
            '__URL__',
            data=expected_data,
            headers=self.expected_headers,
        )

    def test_get_return_data(self):
        """
        NTLMAuth make_request returns 'd' content of json on success
        """
        self.response.status_code = 200
        self.response.json.return_value = {
            'd': '__DATA__',
        }

        result = self.auth.make_request('get', '__URL__')

        self.assertEqual(result, '__DATA__')
