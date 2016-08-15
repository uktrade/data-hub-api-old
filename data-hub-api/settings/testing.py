import os

from .base import *  # noqa


INSTALLED_APPS += (  # noqa
    'django_nose',
    'migrator.tests',
)

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_ARGS = [
    '--nologcapture',
    '--with-doctest',
    '--with-yanc',
]


CDMS_ADFS_URL = 'https://adfs.example.com'
CDMS_BASE_URL = os.environ.get('DJANGO__CDMS_BASE_URL', 'https://example.com')
CDMS_RSTS_URL = 'https://sso.example.com'
CDMS_USERNAME = os.environ.get('DJANGO__CDMS_USERNAME', 'username')
CDMS_PASSWORD = os.environ.get('DJANGO__CDMS_PASSWORD', 'password')
CDMS_COOKIE_KEY = b'RKfgWE-GYNy3mWHm5wEUZavralDzSMKDguBfyuBag8A='
