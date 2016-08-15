import unittest
import functools

from django.conf import settings


def skipIntegration(test_item):
    """
    Skip integration tests if TEST_INTEGRATION setting is True.
    """
    reason = 'Integration tests turned off'

    should_run = False
    try:
        if settings.TEST_INTEGRATION:
            should_run = True
    except AttributeError:
        pass

    if isinstance(test_item, type):
        if should_run:
            return test_item
        test_item.__unittest_skip__ = True
        test_item.__unittest_skip_why__ = reason
        return test_item

    @functools.wraps(test_item)
    def decorator(*args, **kwargs):
        if should_run:
            return test_item(*args, **kwargs)
        raise unittest.SkipTest(reason)
    return decorator
