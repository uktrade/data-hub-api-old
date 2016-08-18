from unittest.mock import Mock, patch

from django.test import TestCase

from ...rest.api import CDMSRestApi
from ...rest.auth.active_directory import ActiveDirectoryAuth


class TestAPIInit(TestCase):

    @patch('apps.cdms_api.rest.api.ActiveDirectoryAuth')
    def test_happy_default(self, mock_ActiveDirectoryAuth):
        """
        CDMSRestApi initialises an ActiveDirectoryAuth instance by default

        NOTE: ActiveDirectoryAuth's setup_session has to be mocked out or it
        will start the login process automatically.
        """
        instance_ActiveDirectoryAuth = Mock(spec=ActiveDirectoryAuth)
        mock_ActiveDirectoryAuth.return_value = instance_ActiveDirectoryAuth

        result = CDMSRestApi()

        mock_ActiveDirectoryAuth.assert_called_once_with()
        self.assertEqual(result.auth, instance_ActiveDirectoryAuth)

    def test_happy_custom(self):
        """
        CDMSRestApi can be initialised with a custom auth
        """
        mock_auth = Mock(name='Auth instance')

        result = CDMSRestApi(auth=mock_auth)

        self.assertEqual(result.auth, mock_auth)
