import slumber

from django.conf import settings

from requests.auth import AuthBase


DUEDIL_BASE_URL = "http://api.duedil.com/open/"


class DueDilApikeyAuth(AuthBase):
    """
    Auth object that appends a `api_key` to every request.
    """
    def __init__(self, api_key):
        self.api_key = api_key

    def __call__(self, r):
        r.prepare_url(r.url, params={
            'api_key': self.api_key
        })
        return r


api = slumber.API(
    DUEDIL_BASE_URL,
    auth=DueDilApikeyAuth(settings.DUEDIL_TOKEN),
    append_slash=False
)
