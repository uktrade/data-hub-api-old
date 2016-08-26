import json

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from requests import Session
from requests_ntlm import HttpNtlmAuth

from ...exceptions import CDMSNotFoundException, ErrorResponseException


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

        NOTE: There are some major functional differences between this and the
        AD auth implementation.

            DIFF: JSON error messages are decoded before offloading them into
            exceptions. AD just dumps the JSON.

            DIFF: When a PUT is received it is converted to POST + MERGE. This
            does not happen in AD.

        NOTE: Hiding the reponse code from the client layer makes it hard to
        take different actions per verb. E.g. 200 vs 201 on success.
        """
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

        if verb == 'put':
            # Execute verb tunnelling
            verb = 'post'
            headers['X-HTTP-Method'] = 'MERGE'

        if data is None:
            data = {}
        else:
            data = json.dumps(data)

        resp = getattr(self.session, verb)(url, data=data, headers=headers)

        if resp.status_code in (200, 201):
            return resp.json()['d']

        if resp.status_code >= 400:

            EXCEPTIONS_MAP = {
                # 401: CDMSUnauthorizedException, < No test for this yet, so not including
                404: CDMSNotFoundException
            }
            ExceptionClass = EXCEPTIONS_MAP.get(resp.status_code, ErrorResponseException)
            raise ExceptionClass(
                resp.json(),
                status_code=resp.status_code
            )

        return resp
