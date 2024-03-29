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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DJANGO__DB_NAME', 'data-hub-api'),
        'USER': os.environ.get('DJANGO__DB_USERNAME', ''),
        'PASSWORD': os.environ.get('DJANGO__DB_PASSWORD', ''),
        'HOST': os.environ.get('DJANGO__DB_HOST', ''),
        'PORT': os.environ.get('DJANGO__DB_PORT', '5432'),
    }
}

if os.environ.get('DJANGO__TEST_INTEGRATION'):
    TEST_INTEGRATION = True
