from .base import *  # noqa

INSTALLED_APPS += (
    'django_jenkins',
)


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'data-hub-api',
        'USER': os.environ['DB_USERNAME'],
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': '',
    }
}

TEST_RUNNER = 'django_jenkins.runner.CITestSuiteRunner'
