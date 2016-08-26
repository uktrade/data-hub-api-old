import unittest

from django.conf import settings
from django.test import TestCase, override_settings

from .decorators import skipIntegration


def fake_t_fn(self):
    """A fake test function"""
    return self


class TestSkipIntegrationFunc(TestCase):

    def test_wrap(self):
        """
        skipIntegration wraps a function and preserves its docstring
        """
        result = skipIntegration(fake_t_fn)

        self.assertEqual(result.__doc__, 'A fake test function')

    @override_settings(TEST_INTEGRATION=False)
    def test_exec_false(self):
        """
        skipIntegration skips test if TEST_INTEGRATION is false

        Test function is skipped because it raises SkipTest exception.
        """
        wrapped_fn = skipIntegration(fake_t_fn)

        with self.assertRaises(unittest.SkipTest) as context:
            wrapped_fn()

        self.assertEqual(context.exception.args[0], 'Integration tests turned off')

    @override_settings(TEST_INTEGRATION=True)
    def test_exec_true(self):
        """
        skipIntegration runs test if TEST_INTEGRATION is true
        """
        wrapped_fn = skipIntegration(fake_t_fn)

        result = wrapped_fn('__ARG__')

        self.assertEqual(result, '__ARG__')

    @override_settings()
    def test_exec_no_setting(self):
        """
        skipIntegration skips if there is no TEST_INTEGRATION setting

        Trusts:
            test_exec_false: Exception message is as expected.
        """
        del settings.TEST_INTEGRATION
        wrapped_fn = skipIntegration(fake_t_fn)

        with self.assertRaises(unittest.SkipTest):
            wrapped_fn()


class TestSkipIntegrationClass(TestCase):

    def test_wrap(self):
        """
        skipIntegration wraps a class and preserves its docstring
        """
        FakeTestCase = type('FakeTestCase', (), {'__doc__': 'Fake test suite'})

        result = skipIntegration(FakeTestCase)

        self.assertEqual(result, FakeTestCase)
        self.assertEqual(result.__doc__, 'Fake test suite')

    @override_settings(TEST_INTEGRATION=True)
    def test_wrap_true(self):
        """
        skipIntegration passes through class if TEST_INTEGRATION is True
        """
        FakeTestCase = type('FakeTestCase', (), {})

        result = skipIntegration(FakeTestCase)

        self.assertEqual(result, FakeTestCase)
        self.assertFalse(hasattr(result, '__unittest_skip__'))
        self.assertFalse(hasattr(result, '__unittest_skip_why__'))

    @override_settings(TEST_INTEGRATION=False)
    def test_wrap_false(self):
        """
        skipIntegration marks class for skipping if TEST_INTEGRATION is False

        Class is skipped because internal arguments are added which Unittest
        checks for.
        """
        FakeTestCase = type('FakeTestCase', (), {})

        result = skipIntegration(FakeTestCase)

        self.assertEqual(result, FakeTestCase)
        self.assertIs(result.__unittest_skip__, True)
        self.assertEqual(result.__unittest_skip_why__, 'Integration tests turned off')

    @override_settings()
    def test_wrap_missing(self):
        """
        skipIntegration marks class if there is no TEST_INTEGRATION setting

        Trusts:
            test_wrap_false: Correct message was set.
        """
        del settings.TEST_INTEGRATION
        FakeTestCase = type('FakeTestCase', (), {})

        result = skipIntegration(FakeTestCase)

        self.assertEqual(result, FakeTestCase)
        self.assertIs(result.__unittest_skip__, True)
