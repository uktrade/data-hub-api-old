import os
import pickle
from unittest import mock
from cryptography.fernet import Fernet

from django.conf import settings
from django.test.testcases import TestCase
from django.core.exceptions import ImproperlyConfigured

from cdms_api.cookie_storage import CookieStorage


class BaseCookieStorageTestCase(TestCase):
    def setUp(self):
        self.fernet = Fernet(settings.CDMS_COOKIE_KEY)
        if os.path.exists(settings.COOKIE_FILE):
            os.remove(settings.COOKIE_FILE)

    def write_cookie(self, cookie={}):
        ciphertext = self.fernet.encrypt(pickle.dumps(cookie))
        with open(settings.COOKIE_FILE, 'wb') as f:
            f.write(ciphertext)

    def assertCookieDoesNotExist(self):
        self.assertFalse(os.path.exists(settings.COOKIE_FILE))


class SetupStorageTestCase(BaseCookieStorageTestCase):
    def test_non_valid_key(self):
        with self.settings(
            CDMS_COOKIE_KEY=b'something'
        ):
            self.assertRaises(ImproperlyConfigured, CookieStorage)


class ReadCookieStorageTestCase(BaseCookieStorageTestCase):
    def test_returns_None_if_cookie_doesnt_exist(self):
        storage = CookieStorage()
        self.assertEqual(storage.read(), None)

    def test_returns_None_if_cookie_invalid(self):
        """
        If the cookie is invalid (e.g. not encrypted) => return None and delete cookie.
        """
        self.write_cookie()

        with mock.patch(
            'cdms_api.cookie_storage.open',
            mock.mock_open(read_data='something')
        ):
            storage = CookieStorage()
            self.assertEqual(storage.read(), None)

        self.assertCookieDoesNotExist()

    def test_returns_None_if_encrypted_with_different_key(self):
        """
        If the cookie was encrypted with different secret key => return None and delete cookie.
        """
        self.write_cookie()
        encrypted_cookie = Fernet(Fernet.generate_key()).encrypt(pickle.dumps('something'))

        with mock.patch(
            'cdms_api.cookie_storage.open',
            mock.mock_open(read_data=encrypted_cookie)
        ):
            storage = CookieStorage()
            self.assertEqual(storage.read(), None)

        self.assertCookieDoesNotExist()

    def test_read(self):
        cookie = {'key': 'value'}
        self.write_cookie(cookie)

        storage = CookieStorage()
        self.assertEqual(
            storage.read(), cookie
        )


class WriteCookieStorageTestCase(BaseCookieStorageTestCase):
    def test_write(self):
        cookie = {'key': 'value'}

        storage = CookieStorage()
        storage.write(cookie)

        with open(settings.COOKIE_FILE, 'rb') as f:
            ciphertext = self.fernet.decrypt(f.read())
            cookie_on_fs = pickle.loads(ciphertext)

        self.assertEqual(cookie_on_fs, cookie)


class ExistsCookieStorageTestCase(BaseCookieStorageTestCase):
    def test_doesnt_exists(self):
        self.assertFalse(os.path.exists(settings.COOKIE_FILE))

    def test_exists(self):
        self.write_cookie()
        self.assertTrue(os.path.exists(settings.COOKIE_FILE))


class ResetCookieStorageTestCase(BaseCookieStorageTestCase):
    def test_reset(self):
        self.write_cookie()

        storage = CookieStorage()
        storage.reset()

        self.assertFalse(os.path.exists(settings.COOKIE_FILE))
