from .base import *  # noqa


INSTALLED_APPS += (
    'migrator.tests',
)

CDMS_ADFS_URL = 'https://adfs.example.com'
CDMS_BASE_URL = 'https://example.com'
CDMS_RSTS_URL = 'https://sso.example.com'
CDMS_USERNAME = 'username'
CDMS_PASSWORD = 'password'
CDMS_COOKIE_KEY = b'RKfgWE-GYNy3mWHm5wEUZavralDzSMKDguBfyuBag8A='
