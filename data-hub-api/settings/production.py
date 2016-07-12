from .base import *  # noqa
import os


DEBUG = False
TEMPLATES['OPTIONS']['debug'] = DEBUG  # noqa

SECRET_KEY = os.environ["SECRET_KEY"]

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

ADMINS = (
    ('UKTI Digital', 'Your email'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'data-hub-api',
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': '',
    }
}

CDMS_ADFS_URL = os.environ["CDMS_ADFS_URL"]
CDMS_BASE_URL = os.environ["CDMS_BASE_URL"]
CDMS_USERNAME = os.environ["CDMS_USERNAME"]
CDMS_PASSWORD = os.environ["CDMS_PASSWORD"]
CDMS_COOKIE_KEY = os.environ["CDMS_COOKIE_KEY"]
