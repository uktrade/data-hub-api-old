import os

from django.conf import settings
from django.test import TestCase, override_settings


class EnvSettingsAssertion:

    def assertSettingEnvExpected(self, environment_name, django_name, default):
        """
        Given a pair of environment variable and Django setting names and a
        default value, assert that Django loaded the expected value into the
        Django setting.

        NOTE: Exceptions could be coerced to AssertionError.

        Args:
            environment_name (str): Name of environment variable.
            django_name (str): Name of Django setting to be checked. If setting
                is a dictionary (like 'DATABASES') then entries can be
                specified using '.' as a separator. For example,
                'DATABASES.default.HOST'.
            default (object): Any value that could be set as a default in the
                case that the env var does not exist.

        Raises:
            AttributeError: In that case that the Django setting does not
                exist.
            KeyError: In the case that the Django setting dict does not have
                the expected key.
        """
        django_name_parts = django_name.split('.')
        django_value = getattr(settings, django_name_parts.pop(0))

        while len(django_name_parts) > 0:
            django_value = django_value[django_name_parts.pop(0)]

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

    def test_TEST_INTEGRATION(self):
        """
        TEST_INTEGRATION setting is loaded as expected

        Slightly different test required because TEST_INTEGRATION uses a truthy
        value.
        """
        try:
            value = bool(os.environ['DJANGO__TEST_INTEGRATION'])
            self.assertEqual(settings.TEST_INTEGRATION, value)
        except KeyError:
            with self.assertRaises(AttributeError):
                settings.TEST_INTEGRATION

    def test_DATABASE_default_NAME(self):
        """
        DATABASES.default.NAME is loaded as expected

        Slightly dirty because it's creating the test database name and testing
        against that by prefixing 'test_'
        """
        self.assertSettingEnvExpected(
            environment_name='DJANGO__DB_NAME',
            django_name='DATABASES.default.NAME',
            default='test_data-hub-api',
        )

    def test_DATABASE_default_USERNAME(self):
        """
        DATABASES.default.USERNAME is loaded as expected
        """
        self.assertSettingEnvExpected(
            environment_name='DJANGO__DB_USERNAME',
            django_name='DATABASES.default.USER',
            default='',
        )

    def test_DATABASE_default_PASSWORD(self):
        """
        DATABASES.default.NAME is loaded as expected
        """
        self.assertSettingEnvExpected(
            environment_name='DJANGO__DB_PASSWORD',
            django_name='DATABASES.default.PASSWORD',
            default='',
        )

    def test_DATABASE_default_HOST(self):
        """
        DATABASES.default.HOST is loaded as expected
        """
        self.assertSettingEnvExpected(
            environment_name='DJANGO__DB_HOST',
            django_name='DATABASES.default.HOST',
            default='',
        )

    def test_DATABASE_default_PORT(self):
        """
        DATABASES.default.PORT is loaded as expected
        """
        self.assertSettingEnvExpected(
            environment_name='DJANGO__DB_PORT',
            django_name='DATABASES.default.PORT',
            default='5432',
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
            self.assertSettingEnvExpected('__ENV_NAME__', '__DJANGO_NAME__', '__DEFAULT__')


class TestAssertSettingsEnvExpectedDict(TestCase, EnvSettingsAssertion):
    """
    Given an environment variable '__ENV_NAME__'
    Given a Django setting '__DJANGO_NAME__["key1"]["key2"]'
    Given a default value for the Django setting of '__KEYED_VAL__'

    Assert that assertSettingEnvExpected can read the nested value.
    """

    @override_settings(
        __DJANGO_NAME__={
            'key1': {
                'key2': '__KEYED_VAL__',
                'keya': '__OTHER_VAL__',
            },
            'keyz': 'thing',
        },
    )
    def test_value_value(self):
        """
        assertSettingEnvExpected: envvar has value, setting dict value matches
        """
        os.environ['__ENV_NAME__'] = '__KEYED_VAL__'

        self.assertSettingEnvExpected('__ENV_NAME__', '__DJANGO_NAME__.key1.key2', '__DEFAULT__')

    @override_settings(
        __DJANGO_NAME__={
            'key1': {
                'key2': '__OTHER_VAL__',
                'keya': '__OTHER_VAL__',
            },
            'keyz': 'thing',
        },
    )
    def test_value_other(self):
        """
        assertSettingEnvExpected: envvar has value, setting dict value other
        """
        os.environ['__ENV_NAME__'] = '__KEYED_VAL__'

        with self.assertRaises(AssertionError):
            self.assertSettingEnvExpected('__ENV_NAME__', '__DJANGO_NAME__.key1.key2', '__DEFAULT__')

    @override_settings(
        __DJANGO_NAME__={
            'key1': {
                'keya': '__OTHER_VAL__',
            },
            'keyz': 'thing',
        },
    )
    def test_value_missing(self):
        """
        assertSettingEnvExpected: envvar has value, setting dict missing
        """
        os.environ['__ENV_NAME__'] = '__KEYED_VAL__'

        with self.assertRaises(KeyError):
            self.assertSettingEnvExpected('__ENV_NAME__', '__DJANGO_NAME__.key1.key2', '__DEFAULT__')
