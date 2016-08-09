from unittest.mock import Mock, patch

from django.test import TestCase

from ...rest.api import CDMSRestApi
from ...rest.auth.active_directory import ActiveDirectoryAuth


class TestAPIInit(TestCase):

    @patch('apps.cdms_api.rest.api.ActiveDirectoryAuth')
    def test_happy_default(self, m_ActiveDirectoryAuth):
        """
        CDMSRestApi initialises an ActiveDirectoryAuth instance by default

        NOTE: ActiveDirectoryAuth's setup_session has to be mocked out or it
        will start the login process automatically.
        """
        i_ActiveDirectoryAuth = Mock(spec=ActiveDirectoryAuth)
        m_ActiveDirectoryAuth.return_value = i_ActiveDirectoryAuth

        result = CDMSRestApi()

        m_ActiveDirectoryAuth.assert_called_once_with()
        self.assertEqual(result.auth, i_ActiveDirectoryAuth)

    def test_happy_custom(self):
        """
        CDMSRestApi can be initialised with a custom auth
        """
        m_auth = Mock(name='Auth instance')

        result = CDMSRestApi(auth=m_auth)

        self.assertEqual(result.auth, m_auth)
