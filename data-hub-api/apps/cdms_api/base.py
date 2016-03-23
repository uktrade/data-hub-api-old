import json
import requests
import pickle
import os
import logging

from django.conf import settings
from django.utils.text import slugify

from pyquery import PyQuery

from .exceptions import CDMSException, CDMSUnauthorizedException, CDMSNotFoundException

CRM_BASE_URL = settings.CDMS_BASE_URL

COOKIE_FILE = '/tmp/cdms_cookie_{slug}.tmp'.format(
    slug=slugify(CRM_BASE_URL)
)

logger = logging.getLogger('cmds_api')


class CDMSApi(object):
    CRM_BASE_URL = settings.CDMS_BASE_URL
    CRM_ADFS_URL = settings.CDMS_ADFS_URL
    CRM_REST_BASE_URL = '%s/XRMServices/2011/OrganizationData.svc' % CRM_BASE_URL

    EXCEPTIONS_MAP = {
        401: CDMSUnauthorizedException,
        404: CDMSNotFoundException
    }

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.setup_session()

    def setup_session(self, force=False):
        """
        So that we don't login every time during dev, we save the cookie
        in a file and load it afterwards.
        """
        if force and os.path.exists(COOKIE_FILE):
            os.remove(COOKIE_FILE)

        if not os.path.exists(COOKIE_FILE):
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

    def login(self):
        session = requests.session()

        # login form
        login_form_response = session.get(
            '{base}/?whr={adfs}'.format(
                base=self.CRM_BASE_URL,
                adfs=self.CRM_ADFS_URL
            ),
            verify=False
        )

        html_parser = PyQuery(login_form_response.content)
        username_field_name = html_parser('input[name*=Username]')[0].name
        password_field_name = html_parser('input[name*=Password]')[0].name
        submit_field = html_parser('input[name*=Submit]')[0]
        login_data = {
            field.name: field.value for field in html_parser('[type=hidden]')
        }

        login_data.update({
            username_field_name: self.username,
            password_field_name: self.password,
            submit_field.name: submit_field.value
        })

        # first submit
        login_resp = session.post(login_form_response.url, login_data)

        # second submit
        html_parser = PyQuery(login_resp.content)
        confirm_url = html_parser('form').attr('action')

        resp = session.post(
            confirm_url, {
                field.get('name'): field.get('value') for field in html_parser('input')
            }
        )

        # third submit
        html_parser = PyQuery(resp.content)
        confirm_url = html_parser('form').attr('action')

        resp = session.post(
            confirm_url, {
                field.get('name'): field.get('value') for field in html_parser('input')
            },
            verify=False
        )
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
        resp = getattr(self.session, verb)(url, data=data, headers=headers, verify=False)

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
            params='&'.join([u'%s=%s' % (k, v) for k, v in params.items()])
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
