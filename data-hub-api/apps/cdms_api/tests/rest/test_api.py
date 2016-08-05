from unittest.mock import Mock, patch

from django.test import TestCase

from ...rest.api import CDMSRestApi
from ...rest.auth.active_directory import ActiveDirectoryAuth


class TestAPIInit(TestCase):

    @patch.object(ActiveDirectoryAuth, 'setup_session')
    def test_happy_default(self, m_setup_session):
        """
        CDMSRestApi initialises an ActiveDirectoryAuth instance by default

        NOTE: ActiveDirectoryAuth's setup_session has to be mocked out or it
        will start the login process automatically.
        """
        result = CDMSRestApi()

        self.assertIsInstance(result.auth, ActiveDirectoryAuth)

    def test_happy_custom(self):
        """
        CDMSRestApi can be initialised with a custom auth
        """
        m_auth = Mock(name='Auth instance')

        result = CDMSRestApi(auth=m_auth)

        self.assertEqual(result.auth, m_auth)
