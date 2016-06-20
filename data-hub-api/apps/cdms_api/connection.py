from django.conf import settings

if settings.IN_TESTING:
    from .tests.rest.utils import get_mocked_cdms_connection
    rest_connection = get_mocked_cdms_connection()
else:
    from .rest.api import CDMSRestApi
    rest_connection = CDMSRestApi()
