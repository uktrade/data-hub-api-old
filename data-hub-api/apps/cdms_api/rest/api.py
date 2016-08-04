import json
import requests
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from pyquery import PyQuery

from ..exceptions import (
    ErrorResponseException,
    CDMSUnauthorizedException,
    CDMSNotFoundException,
    LoginErrorException,
    UnexpectedResponseException,
)
from ..cookie_storage import CookieStorage


logger = logging.getLogger('cmds_api.rest.api')


class ActiveDirectoryAuth:
    """
    Handle authentication via Active Directory using form submission, cookie
    retrieval and storage.

    Wraps a `requests.session` instance which it populates with Auth data.

    NOTE this is an extraction of auth functionality. Although the tests pass,
    many of them are mocked and this does not prove that auth works with API.
    """

    def __init__(self):
        """
        Raises:
            ImproperlyConfigured: If `CDMS_ADFS_URL` or `CDMS_BASE_URL` are not
                provided via Django settings.
        """
        for setting_name in ['CDMS_ADFS_URL', 'CDMS_BASE_URL', 'CDMS_USERNAME', 'CDMS_PASSWORD']:
            if not getattr(settings, setting_name):
                raise ImproperlyConfigured('{} setting required'.format(setting_name))

        self.cookie_storage = CookieStorage()
        self.setup_session()

    def setup_session(self, force=False):
        """
        So that we don't login every time, we save the cookie and load it afterwards.
        """
        if force:
            self.cookie_storage.reset()

        cookie = self.cookie_storage.read()
        if cookie:
            session = requests.session()
            jar = requests.cookies.RequestsCookieJar()
            jar._cookies = cookie
            session.cookies = jar
            self.session = session
        else:
            self.session = self.login()
            self.cookie_storage.write(self.session.cookies._cookies)

    def login(self):
        """
        This goes through the following steps:

        1. get login page
        2. submit the form with username and password
        3. the result is a form with a security token issued by the STS and the url of the next STS
            to validate the token
        4. submit the form of step 3. without making any changes
        5. repeat step 3. and 4 one more time to get the valid authentication cookie

        For more details, check: https://msdn.microsoft.com/en-us/library/aa480563.aspx
        """
        session = requests.session()

        # 1. get login page
        url = '{}/?whr={}'.format(settings.CDMS_BASE_URL, settings.CDMS_ADFS_URL)
        resp = session.get(url)
        if not resp.ok:
            raise UnexpectedResponseException(
                '{} for status code {}'.format(url, resp.status_code),
                content=resp.content,
                status_code=resp.status_code
            )

        html_parser = PyQuery(resp.content)
        username_field_name = html_parser('input[name*=Username]')[0].name
        password_field_name = html_parser('input[name*=Password]')[0].name

        # 2. submit the login form with username and password
        resp = self._submit_form(
            session, resp.content,
            url=resp.url,
            params={
                username_field_name: settings.CDMS_USERNAME,
                password_field_name: settings.CDMS_PASSWORD,
            }
        )

        # 3. and 4. re-submit the resulting form containing the security token so that the next STS can validate it
        resp = self._submit_form(session, resp.content)

        # 5. re-submit the form again to validate the token and get as result the authenticated cookie
        self._submit_form(session, resp.content)
        return session

    def _submit_form(self, session, source, url=None, params={}):
        """
        It submits the form contained in the `source` param optionally overriding form `params` and form `url`.

        This is needed as UKTI has a few STSes and the token has to be validated by all of them.
        For more details, check: https://msdn.microsoft.com/en-us/library/aa480563.aspx
        """
        html_parser = PyQuery(source)
        form_action = html_parser('form').attr('action')

        # get all inputs in the source + optional params passed in
        data = {field.get('name'): field.get('value') for field in html_parser('input')}
        data.update(params)

        url = url or form_action
        resp = session.post(url, data)

        # check status code
        if not resp.ok:
            raise UnexpectedResponseException(
                '{} for status code {}'.format(url, resp.status_code),
                content=resp.content,
                status_code=resp.status_code
            )

        # check response, if form action of source == form action of response => error page
        html_parser = PyQuery(resp.content)

        if form_action == html_parser('form').attr('action'):
            error_els = html_parser('[id$=ErrorTextLabel]')
            if error_els:
                raise LoginErrorException(', '.join([error_el.text for error_el in error_els]))
            raise UnexpectedResponseException(  # we don't know exactly what happened...
                'Unexpected Response.', content=resp.content
            )
        return resp

    def make_request(self, verb, url, data=dict()):
        """
        Makes the call to CDMS, if 401 is found, it reauthenticates
        and tries again making the same call
        """
        try:
            return self._make_request(verb, url, data=data)
        except CDMSUnauthorizedException:
            logger.debug('Session expired, reauthenticating and trying again')
            self.setup_session(force=True)
        return self._make_request(verb, url, data=data)

    def _make_request(self, verb, url, data=dict()):
        logger.debug('Calling CDMS url (%s) on %s' % (verb, url))
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

        if data:
            data = json.dumps(data)
        resp = getattr(self.session, verb)(url, data=data, headers=headers)

        if resp.status_code >= 400:
            logger.debug('Got CDMS error (%s): %s' % (resp.status_code, resp.content))

            EXCEPTIONS_MAP = {
                401: CDMSUnauthorizedException,
                404: CDMSNotFoundException
            }
            ExceptionClass = EXCEPTIONS_MAP.get(resp.status_code, ErrorResponseException)
            raise ExceptionClass(
                resp.content,
                status_code=resp.status_code
            )

        if resp.status_code in (200, 201):
            return resp.json()['d']

        return resp


class CDMSRestApi(object):
    """
    Instance of a connection to the Microsoft Dynamics 2011 REST API.
    """

    CRM_REST_BASE_URL = '/'.join([
        settings.CDMS_BASE_URL.rstrip('/'),
        'XRMServices/2011/OrganizationData.svc'
    ])

    def __init__(self):
        self.auth = ActiveDirectoryAuth()

    def make_request(self, verb, url, data=dict()):
        """
        Route a request through the authentication layer
        """
        return self.auth.make_request(verb, url, data=data)

    def list(self, service, top=50, skip=0, select=None, filters=None, order_by=None):
        params = {}
        if filters:
            params['$filter'] = filters

        if select:
            params['$select'] = ','.join(select)

        if order_by:
            if isinstance(order_by, str):
                order_by = [order_by]
            params['$orderby'] = ','.join(order_by)

        url = "{base_url}/{service}Set?$top={top}&$skip={skip}&{params}".format(
            base_url=self.CRM_REST_BASE_URL,
            service=service,
            top=top,
            skip=skip,
            params='&'.join(sorted([u'%s=%s' % (k, v) for k, v in params.items()]))
        )

        results = self.make_request('get', url)
        return results['results']

    def get(self, service, guid):
        url = "{base_url}/{service}Set(guid'{guid}')".format(
            base_url=self.CRM_REST_BASE_URL,
            service=service,
            guid=guid
        )
        return self.make_request('get', url)

    def update(self, service, guid, data):
        url = "{base_url}/{service}Set(guid'{guid}')".format(
            base_url=self.CRM_REST_BASE_URL,
            service=service,
            guid=guid
        )

        # PUT returns 204 so we need to make an extra GET query to return the latest values
        self.make_request('put', url, data=data)
        return self.get(service, guid)

    def create(self, service, data):
        url = "{base_url}/{service}Set".format(
            base_url=self.CRM_REST_BASE_URL,
            service=service
        )
        return self.make_request('post', url, data=data)

    def delete(self, service, guid):
        url = "{base_url}/{service}Set(guid'{guid}')".format(
            base_url=self.CRM_REST_BASE_URL,
            service=service,
            guid=guid
        )
        return self.make_request('delete', url)
