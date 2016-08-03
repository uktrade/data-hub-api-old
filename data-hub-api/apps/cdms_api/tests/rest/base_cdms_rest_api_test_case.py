from django.test import TestCase

from cdms_api.cookie_storage import CookieStorage


class BaseCDMSRestApiTestCase(TestCase):

    def setUp(self):
        """
        Assert no cookies exist before running tests
        """
        super().setUp()
        self.cookie_storage = CookieStorage()
        self.assertFalse(self.cookie_storage.exists())

    def tearDown(self):
        """
        Delete any cookies created during tests
        """
        self.cookie_storage.reset()
        self.assertFalse(self.cookie_storage.exists())
        super().tearDown()
