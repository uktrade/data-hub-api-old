import os
import sys

from django.utils.text import slugify


# PATH vars

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
root = lambda *x: os.path.join(BASE_DIR, *x)  # flake8: noqa

sys.path.insert(0, root('apps'))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'CHANGE THIS!!!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
IN_TESTING = sys.argv[1:2] == ['test']

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_countries',

    'reversion',
    'companieshouse',
]

PROJECT_APPS = []

INSTALLED_APPS += PROJECT_APPS

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'data-hub-api.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'data-hub-api.wsgi.application'

# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'data-hub-api',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': '',  # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',  # Set to empty string for default.
        'TEST': {
            'SERIALIZE': False,
        },
    }
}

# Internationalization

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = "Europe/London"

USE_I18N = False

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'


# Additional locations of static files

STATICFILES_DIRS = (
    root('assets'),
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'DIRS': [
            root('templates'),
        ],
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages"
            ],
        },
    }
]

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# CDMS SETTINGS

CDMS_BASE_URL = ''
CDMS_ADFS_URL = ''
CDMS_RSTS_URL = ''
CDMS_USERNAME = ''
CDMS_PASSWORD = ''
CDMS_COOKIE_KEY = b''
COOKIE_FILE = '/tmp/cdms_cookie_{slug}.tmp'.format(
    slug=slugify(CDMS_BASE_URL)
)

# SOURCES
COMPANIES_HOUSE_TOKEN = ''
DUEDIL_TOKEN = ''
MATCHER_CLASSES = [  # the order is important, the classes will be used from first to last
    'companieshouse.sources.db.matcher.ChDBMatcher',
    'companieshouse.sources.api.matcher.ChAPIMatcher',
    'companieshouse.sources.duedil.matcher.DueDilMatcher'
]
MATCHER_ACCEPTANCE_PROXIMITY = 0.5  # any proximity matches >= this value will be a hit


# .local.py overrides all the common settings.
try:
    from .local import *  # noqa
except ImportError:
    pass


# importing test settings file if necessary
if IN_TESTING:
    from .testing import *  # noqa
