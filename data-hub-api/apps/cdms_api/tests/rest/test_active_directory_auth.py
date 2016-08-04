import unittest

from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from ...cookie_storage import CookieStorage
from ...rest.api import ActiveDirectoryAuth
from .cookie_storage_test_case import CookieStorageTestCase


class TestInit(CookieStorageTestCase):

    @unittest.mock.patch.object(ActiveDirectoryAuth, 'setup_session', auto_spec=True)
    def test_happy(self, m_setup_session):
        """
        ActiveDirectoryAuth can be initialised with default settings

        Cookie storage is initialised, `setup_session` is called.
        """
        result = ActiveDirectoryAuth()

        self.assertIsInstance(result.cookie_storage, CookieStorage)
        m_setup_session.assert_called_once_with()

    @override_settings(CDMS_ADFS_URL='')
    def test_missing_adfs_url(self):
        """
        ActiveDirectoryAuth raises if ADFS URL is not in settings
        """
        with self.assertRaises(ImproperlyConfigured) as context_manager:
            ActiveDirectoryAuth()

        self.assertIn('CDMS_ADFS_URL', context_manager.exception.args[0])

    @override_settings(CDMS_BASE_URL='')
    def test_missing_base_url(self):
        """
        ActiveDirectoryAuth raises if CDMS_BASE_URL is not in settings
        """
        with self.assertRaises(ImproperlyConfigured) as context_manager:
            ActiveDirectoryAuth()

        self.assertIn('CDMS_BASE_URL', context_manager.exception.args[0])

    @override_settings(CDMS_USERNAME='')
    def test_missing_username(self):
        """
        ActiveDirectoryAuth raises if CDMS_USERNAME is not in settings
        """
        with self.assertRaises(ImproperlyConfigured) as context_manager:
            ActiveDirectoryAuth()

        self.assertIn('CDMS_USERNAME', context_manager.exception.args[0])

    @override_settings(CDMS_PASSWORD='')
    def test_missing_password(self):
        """
        ActiveDirectoryAuth raises if CDMS_PASSWORD is not in settings
        """
        with self.assertRaises(ImproperlyConfigured) as context_manager:
            ActiveDirectoryAuth()

        self.assertIn('CDMS_PASSWORD', context_manager.exception.args[0])
