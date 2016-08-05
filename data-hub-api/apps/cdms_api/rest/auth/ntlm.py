from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from requests import Session
from requests_ntlm import HttpNtlmAuth


class NTLMAuth:
    """
    Handle authentication using NTLM.
    """

    def __init__(self):
        """
        Raises:
            ImproperlyConfigured: If `CDMS_ADFS_URL` or `CDMS_BASE_URL` are not
                provided via Django settings.
        """
        for setting_name in ['CDMS_BASE_URL', 'CDMS_USERNAME', 'CDMS_PASSWORD']:
            if not getattr(settings, setting_name):
                raise ImproperlyConfigured('{} setting required'.format(setting_name))

        self.session = Session()
        self.session.auth = HttpNtlmAuth(settings.CDMS_USERNAME, settings.CDMS_PASSWORD)
