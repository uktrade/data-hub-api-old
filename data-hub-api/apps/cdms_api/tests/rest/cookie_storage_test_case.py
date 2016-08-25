from django.test import TestCase, override_settings

from cdms_api.cookie_storage import CookieStorage


class CookieStorageTestCase(TestCase):

    def setUp(self):
        """
        Assert no cookies exist before running tests
        """
        super().setUp()
        self.cookie_storage = CookieStorage()

    def tearDown(self):
        """
        Delete any cookies created during tests
        """
        self.cookie_storage.reset()
        super().tearDown()


class TestCookieStorageTestCaseSetUp(CookieStorageTestCase):

    def test_clean(self):
        """
        CookieStorageTestCase starts up with no cookie file
        """
        self.assertFalse(self.cookie_storage.exists())


@override_settings(COOKIE_FILE='/tmp/_test_cookie.tmp')
class TestCookieStorageTestCaseTearDown(TestCase):
    """
    Ideally this would make use of pyfakefs or similar which would guarantee no
    naming clashes and teardown the file system automatically at the end of
    testing. For now continue with filesystem.
    """

    def setUp(self):
        """
        Prepare CookieStorageTestCase for testing, create cookie storage file
        """
        super().setUp()
        CookieStorageTestCase.fake_test = lambda _: None
        self.test_case = CookieStorageTestCase('fake_test')
        self.test_case.setUp()
        CookieStorage().write('stuff')

    def tearDown(self):
        del CookieStorageTestCase.fake_test
        CookieStorage().reset()
        super().tearDown()

    def test_set_up(self):
        """
        CookieStorage file is available for testing tearDown
        """
        self.assertTrue(CookieStorage().exists())

    def test_clean(self):
        """
        CookieStorageTestCase tearDown cleans up cookie storage file
        """
        self.test_case.tearDown()

        self.assertFalse(CookieStorage().exists())

    def test_clean_2(self):
        """
        CookieStorageTestCase tearDown passes when there is no cookie file
        """
        self.test_case.tearDown()
