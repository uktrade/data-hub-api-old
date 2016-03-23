from .base import *  # noqa


INSTALLED_APPS += (
    'migrator.tests.queries',
)

CDMS_BASE_URL = 'https://testing.com'
CDMS_USERNAME = 'username'
CDMS_PASSWORD = 'password'
