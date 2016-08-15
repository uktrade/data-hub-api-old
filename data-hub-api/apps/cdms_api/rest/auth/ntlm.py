import json

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from requests import Session
from requests_ntlm import HttpNtlmAuth


class NTLMAuth:
    """
    Handle authentication using NTLM.

    NOTE there is common code between this and ActiveDirectoryAuth:

    * Handling of config checking at init time.
    * Setting of headers and encoding json data.
    * Handling of errors / exceptions (TODO).
    """

    def __init__(self):
        """
        Raises:
            ImproperlyConfigured: If `CDMS_BASE_URL`, `CDMS_USERNAME` or
                `CDMS_PASSWORD` are not provided via Django settings.
        """
        for setting_name in ['CDMS_BASE_URL', 'CDMS_USERNAME', 'CDMS_PASSWORD']:
            if not getattr(settings, setting_name):
                raise ImproperlyConfigured('{} setting required'.format(setting_name))

        self.session = Session()
        self.session.auth = HttpNtlmAuth(settings.CDMS_USERNAME, settings.CDMS_PASSWORD)

    def make_request(self, verb, url, data=None):
        """
        Pass through calls to self.session
        """
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

        if data is None:
            data = {}
        else:
            data = json.dumps(data)

        resp = getattr(self.session, verb)(url, data=data, headers=headers)

        if resp.status_code in (200, 201):
            return resp.json()['d']

        return resp
