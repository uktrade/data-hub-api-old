import json
import requests
import pickle
import os
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.text import slugify

from pyquery import PyQuery

from .exceptions import CDMSException, CDMSUnauthorizedException, CDMSNotFoundException, \
    LoginErrorException, UnexpectedResponseException

COOKIE_FILE = '/tmp/cdms_cookie_{slug}.tmp'.format(
    slug=slugify(settings.CDMS_BASE_URL)
)

logger = logging.getLogger('cmds_api')


def cookie_exists():
    return os.path.exists(COOKIE_FILE)


def delete_cookie():
    if cookie_exists():
        os.remove(COOKIE_FILE)


class CDMSApi(object):
    CRM_REST_BASE_URL = '%s/XRMServices/2011/OrganizationData.svc' % settings.CDMS_BASE_URL

    EXCEPTIONS_MAP = {
        401: CDMSUnauthorizedException,
        404: CDMSNotFoundException
    }

    def __init__(self):
        if not settings.CDMS_ADFS_URL or not settings.CDMS_ADFS_URL:
            raise ImproperlyConfigured('Please set CDMS_ADFS_URL and CDMS_ADFS_URL in your settings.')
        if not settings.CDMS_USERNAME or not settings.CDMS_PASSWORD:
            raise ImproperlyConfigured('Please set CDMS_USERNAME and CDMS_PASSWORD in your settings.')

        self.setup_session()

    def setup_session(self, force=False):
        """
        So that we don't login every time during dev, we save the cookie
        in a file and load it afterwards.
        """
        if force and cookie_exists():
            delete_cookie()

        if not cookie_exists():
            session = self.login()
            with open(COOKIE_FILE, 'wb') as f:
                pickle.dump(session.cookies._cookies, f)

        with open(COOKIE_FILE, 'rb') as f:
            cookies = pickle.load(f)
            session = requests.session()
            jar = requests.cookies.RequestsCookieJar()
            jar._cookies = cookies
            session.cookies = jar

        self.session = session

    def _submit_form(self, session, source, url=None, params={}):
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
                content=resp.content
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

    def login(self):
        session = requests.session()

        # login form
        url = '{}/?whr={}'.format(settings.CDMS_BASE_URL, settings.CDMS_ADFS_URL)
        resp = session.get(url)
        if not resp.ok:
            raise UnexpectedResponseException(
                '{} for status code {}'.format(url, resp.status_code),
                content=resp.content
            )

        html_parser = PyQuery(resp.content)
        username_field_name = html_parser('input[name*=Username]')[0].name
        password_field_name = html_parser('input[name*=Password]')[0].name

        # first submit
        resp = self._submit_form(
            session, resp.content,
            url=resp.url,
            params={
                username_field_name: settings.CDMS_USERNAME,
                password_field_name: settings.CDMS_PASSWORD,
            }
        )

        # second submit
        resp = self._submit_form(session, resp.content)

        # third submit
        self._submit_form(session, resp.content)
        return session

    def make_request(self, verb, url, data={}):
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

    def _make_request(self, verb, url, data={}):
        logger.debug('Calling CDMS url (%s) on %s' % (verb, url))
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

        if data:
            data = json.dumps(data)
        resp = getattr(self.session, verb)(url, data=data, headers=headers)

        if resp.status_code >= 400:
            logger.debug('Got CDMS error (%s): %s' % (resp.status_code, resp.content))

            ExceptionClass = self.EXCEPTIONS_MAP.get(resp.status_code, CDMSException)
            raise ExceptionClass(
                resp.content,
                status_code=resp.status_code
            )

        if resp.status_code in (200, 201):
            return resp.json()['d']

        return resp

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
