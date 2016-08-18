import os

from django.conf import settings
from django.test import TestCase, override_settings


class EnvSettingsAssertion:

    def assertSettingEnvExpected(self, environment_name, django_name, default):
        """
        Given a pair of environment variable and Django setting names and a
        default value, assert that Django loaded the expected value into the
        Django setting.
        """
        django_value = getattr(settings, django_name)

        try:
            expected_value = os.environ[environment_name]
        except KeyError:
            expected_value = default

        self.assertEqual(django_value, expected_value)


class TestEnv(TestCase, EnvSettingsAssertion):
    """
    Asserts that default values for settings are loaded if no envvar is set. In
    the case that the suite is run when there *is* an envvar, then the expected
    value is checked.

    This serves to test the default fall through for these settings since they
    can be overridden by the environment.
    """

    def test_CDMS_USERNAME(self):
        """
        CDMS_USERNAME setting is loaded as expected
        """
        self.assertSettingEnvExpected(
            environment_name='DJANGO__CDMS_USERNAME',
            django_name='CDMS_USERNAME',
            default='username',
        )

    def test_CDMS_PASSWORD(self):
        """
        CDMS_PASSWORD setting is loaded as expected
        """
        self.assertSettingEnvExpected(
            environment_name='DJANGO__CDMS_PASSWORD',
            django_name='CDMS_PASSWORD',
            default='password',
        )

    def test_CDMS_BASE_URL(self):
        """
        CDMS_BASE_URL setting is loaded as expected
        """
        self.assertSettingEnvExpected(
            environment_name='DJANGO__CDMS_BASE_URL',
            django_name='CDMS_BASE_URL',
            default='https://example.com',
        )


class TestAssertSettingsEnvExpected(TestCase, EnvSettingsAssertion):
    """
    Given an environment variable '__ENV_NAME__'
    Given a Django setting '__DJANGO_NAME__'
    Given a default value for the Django setting of '__DEFAULT__'

    Then test the following states:

    ----------------+-------------------+-----------
     __ENV_NAME__   | __DJANGO_NAME__   | Result
    ----------------+-------------------+-----------
     None           | '__DEFAULT__'     | Pass
     None           | '__OTHER__'       | Fail
     '__VALUE__'    | '__DEFAULT__'     | Fail
     '__VALUE__'    | '__VALUE__'       | Pass
     '__VALUE__'    | '__OTHER__'       | Fail
    ----------------+-------------------+-----------
    """

    def tearDown(self):
        """
        Remove any left over envvar otherwise it'll hang over to the next test
        """
        try:
            del(os.environ['__ENV_NAME__'])
        except KeyError:
            pass
        super().tearDown()

    def test_set_up(self):
        """
        setUp: assertSettingEnvExpected tests start with no env var
        """
        self.assertFalse('__ENV_NAME__' in os.environ)

    @override_settings(__DJANGO_NAME__='__DEFAULT__')
    def test_none_default(self):
        """
        assertSettingEnvExpected: No envvar, Django setting is default value
        """

        self.assertSettingEnvExpected('__ENV_NAME__', '__DJANGO_NAME__', '__DEFAULT__')

    @override_settings(__DJANGO_NAME__='__OTHER__')
    def test_none_other(self):
        """
        assertSettingEnvExpected: No envvar, Django setting other value
        """
        try:
            del(os.environ['__ENV_NAME__'])
        except KeyError:
            pass

        with self.assertRaises(AssertionError):
            self.assertSettingEnvExpected('__ENV_NAME__', '__DJANGO_NAME__', '__DEFAULT__')

    @override_settings(__DJANGO_NAME__='__DEFAULT__')
    def test_value_default(self):
        """
        assertSettingEnvExpected: envvar has value, setting is default
        """
        os.environ['__ENV_NAME__'] = '__VALUE__'

        with self.assertRaises(AssertionError):
            self.assertSettingEnvExpected('__ENV_NAME__', '__DJANGO_NAME__', '__DEFAULT__')

    @override_settings(__DJANGO_NAME__='__VALUE__')
    def test_value_value(self):
        """
        assertSettingEnvExpected: envvar has value, setting is value
        """
        os.environ['__ENV_NAME__'] = '__VALUE__'

        self.assertSettingEnvExpected('__ENV_NAME__', '__DJANGO_NAME__', '__DEFAULT__')

    @override_settings(__DJANGO_NAME__='__OTHER__')
    def test_value_other(self):
        """
        assertSettingEnvExpected: envvar has value, setting is other
        """
        os.environ['__ENV_NAME__'] = '__VALUE__'

        with self.assertRaises(AssertionError):
            self.assertSettingEnvExpected('__ENV_NAME__', '__DJANGO_NAME__', '__OTHER__')
