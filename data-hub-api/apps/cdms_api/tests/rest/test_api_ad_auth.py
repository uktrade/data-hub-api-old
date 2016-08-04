import os
import responses
import json
from urllib.parse import urlparse

from django.template import Engine, Context
from django.conf import settings
from django.test import override_settings
from django.core.exceptions import ImproperlyConfigured

from cdms_api.rest.api import CDMSRestApi
from cdms_api.exceptions import LoginErrorException, UnexpectedResponseException, CDMSUnauthorizedException, \
    CDMSNotFoundException, ErrorResponseException
from .cookie_storage_test_case import CookieStorageTestCase


class TestSetUp(CookieStorageTestCase):

    @override_settings(
        CDMS_ADFS_URL='',
        CDMS_BASE_URL='',
        CDMS_USERNAME='username',
        CDMS_PASSWORD='password',
    )
    def test_exception_if_urls_not_configured(self):
        """
        CDMSRestApi raises when CDMS URL settings are left blank
        """
        with self.assertRaises(ImproperlyConfigured):
            CDMSRestApi()

    @override_settings(
        CDMS_ADFS_URL='adfs_url',
        CDMS_BASE_URL='base_url',
        CDMS_USERNAME='',
        CDMS_PASSWORD='',
    )
    def test_exception_if_credentials_configured(self):
        """
        CDMSRestApi raises when CDMS un / pw settings are left blank
        """
        with self.assertRaises(ImproperlyConfigured):
            CDMSRestApi()


class MockedResponseMixin(object):
    """
    Mixin to easily mock the login reponses.
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LOGIN_URL = '{}/?whr={}'.format(settings.CDMS_BASE_URL, settings.CDMS_ADFS_URL)

    LOGIN_STEPS = [
        (LOGIN_URL, 'login_form.html'),
        (LOGIN_URL, 'auth_form.html'),
        ('https://auth1.example.com/', 'auth_form.html'),
        ('https://auth2.example.com/', 'successful_login.html'),
    ]

    def get_mocked_html_response(self, template_name, variables={}):
        """
        Returns the 'template_name' with the 'variables' as a resolved string.
        """
        template_engine = Engine(dirs=[os.path.join(self.BASE_DIR, 'responses')])
        template = template_engine.get_template(template_name)
        return template.render(Context(variables))

    def mock_initial_login(self, status_code=200):
        """
        Mocks the initial auth page which usually contains a form with username/password fields.
        """
        step_url, step_template_name = self.LOGIN_STEPS[0]

        body = None
        if status_code == 200:
            body = self.get_mocked_html_response(
                step_template_name, {
                    'url': step_url
                }
            )

        responses.add(
            responses.GET, step_url, match_querystring=True,
            body=body, status=status_code
        )

    def mock_login_step(self, step, errors=False, status_code=200):
        """
        Mocks an auth form for the step x based on the 'LOGIN_STEPS' param.
        """
        assert step >= 1, 'Use mock_initial_login instead'
        if errors:
            step_url, step_template_name = self.LOGIN_STEPS[step - 1]
            next_url = step_url
        else:
            step_url, step_template_name = self.LOGIN_STEPS[step]
            try:
                next_url, _ = self.LOGIN_STEPS[step + 1]
            except IndexError:
                next_url = None

        if status_code == 200:
            body = self.get_mocked_html_response(
                step_template_name, {
                    'url': next_url,
                    'errors': errors
                }
            )
        else:
            body = None

        responses.add(
            responses.POST, step_url, match_querystring=True,
            body=body, status=status_code
        )

    def mock_cookie(self):
        """
        Makes sure that the cookie is there.
        """
        from http.cookiejar import Cookie
        self.cookie_storage.write({
            'example.com': {
                '/': {
                    'NID': Cookie(
                        version=0, name='NID', value='0000', port=None, port_specified=False,
                        domain='example.com', domain_specified=True, domain_initial_dot=True,
                        path='/', path_specified=True, secure=False, expires=1476201395,
                        discard=False, comment=None, comment_url=None, rest={'HttpOnly': None},
                        rfc2109=False
                    )
                }
            }
        })


class LoginTestCase(MockedResponseMixin, CookieStorageTestCase):
    @responses.activate
    def test_invalid_credentials(self):
        """
        In case of invalid credentials, the constructor should raise LoginErrorException.
        """
        self.mock_initial_login()
        self.mock_login_step(1, errors=True)

        self.assertRaises(LoginErrorException, CDMSRestApi)

    @responses.activate
    def test_first_successful_login(self):
        """
        When logging in for the first time (=> no cookie exists), the constructor should log in and save
        the valid cookie on the filesystem.
        """
        self.assertFalse(self.cookie_storage.exists())

        self.mock_initial_login()
        self.mock_login_step(1)
        self.mock_login_step(2)
        self.mock_login_step(3)

        api = CDMSRestApi()
        self.assertTrue(self.cookie_storage.exists())
        self.assertTrue(api.session)

    @responses.activate
    def test_exception_with_initial_form(self):
        """
        In case of exception with the initial login url, the constructor should raise UnexpectedResponseException.
        """
        self.mock_initial_login(status_code=500)
        self.assertRaises(UnexpectedResponseException, CDMSRestApi)

    @responses.activate
    def test_exception_with_auth_step_1_form(self):
        """
        In case of exception with the step 1 of the auth process, the constructor should
        raise UnexpectedResponseException.
        """
        self.mock_initial_login()
        self.mock_login_step(1, status_code=500)
        self.assertRaises(UnexpectedResponseException, CDMSRestApi)

    @responses.activate
    def test_exception_with_auth_step_2_form(self):
        """
        In case of exception with the step 2 of the auth process, the constructor should
        raise UnexpectedResponseException.
        """
        self.mock_initial_login()
        self.mock_login_step(1)
        self.mock_login_step(2, status_code=500)
        self.assertRaises(UnexpectedResponseException, CDMSRestApi)

    @responses.activate
    def test_exception_with_final_form(self):
        """
        In case of exception with the final step of the auth process, the constructor should
        raise UnexpectedResponseException.
        """
        self.mock_initial_login()
        self.mock_login_step(1)
        self.mock_login_step(2)
        self.mock_login_step(3, status_code=500)
        self.assertRaises(UnexpectedResponseException, CDMSRestApi)

    @responses.activate
    def test_reuse_existing_cookie(self):
        """
        If the cookie file exists, use that without making any auth calls.
        """
        self.mock_cookie()

        api = CDMSRestApi()
        self.assertEqual(len(responses.calls), 0)
        self.assertTrue(api.session)


class MakeRequestTestCase(MockedResponseMixin, CookieStorageTestCase):
    def setUp(self):
        super(MakeRequestTestCase, self).setUp()
        self.mock_cookie()

    @responses.activate
    def test_setup_session_if_cookie_expired(self):
        """
        If the cookie is expired, a call to an arbitrary endpoint should reauthenticate and retry one more time
        transparently.
        """
        url = 'https://test/'
        body_response = 'success'

        def endpoint_callback():
            index = 0

            def wrapper(request):
                nonlocal index
                status_code = 200 if index else 401
                index += 1
                return (status_code, [], json.dumps({'d': body_response}))
            return wrapper

        responses.add_callback(
            responses.GET, url, match_querystring=True,
            callback=endpoint_callback()
        )
        self.mock_initial_login()
        self.mock_login_step(1)
        self.mock_login_step(2)
        self.mock_login_step(3)

        api = CDMSRestApi()
        resp = api.make_request('get', url)
        self.assertEqual(resp, body_response)
        self.assertTrue(api.session)

    @responses.activate
    def test_setup_session_tries_only_once_if_cookie_expired(self):
        """
        If the cookie is expired, a call to an arbitrary endpoint should retry just once and fail after that.
        """
        url = 'https://test/'
        responses.add(responses.GET, url, match_querystring=True, status=401)

        self.mock_initial_login()
        self.mock_login_step(1)
        self.mock_login_step(2)
        self.mock_login_step(3)

        api = CDMSRestApi()
        self.assertRaises(
            CDMSUnauthorizedException,
            api.make_request, 'get', url
        )
        self.assertEqual(len(responses.calls), 6)

    @responses.activate
    def test_404(self):
        """
        Endpoint returning 404 should raise CDMSNotFoundException.
        """
        url = 'https://test/'
        responses.add(responses.GET, url, match_querystring=True, status=404)

        api = CDMSRestApi()
        self.assertRaises(
            CDMSNotFoundException,
            api.make_request, 'get', url
        )

    @responses.activate
    def test_500(self):
        """
        Endpoint returning an error other than 401/404 should raise ErrorResponseException.
        """
        url = 'https://test/'
        responses.add(responses.GET, url, match_querystring=True, status=500)

        api = CDMSRestApi()
        self.assertRaises(
            ErrorResponseException,
            api.make_request, 'get', url
        )


class ListTestCase(MockedResponseMixin, CookieStorageTestCase):
    def setUp(self):
        super(ListTestCase, self).setUp()
        self.mock_cookie()

        self.service = 'MyService'
        self.url = '{}/{}Set'.format(CDMSRestApi.CRM_REST_BASE_URL, self.service)
        responses.add(
            responses.GET, self.url,
            status=200, body=json.dumps({'d': {'results': []}})
        )

    @responses.activate
    def test_defaults(self):
        """
        Call to the list endpoint with the defaults params.
        """
        api = CDMSRestApi()
        api.list(self.service)

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            urlparse(responses.calls[0].request.url).query,
            '$top=50&$skip=0&'
        )

    @responses.activate
    def test_complete(self):
        """
        Call to the list endpoint with all params defined.
        """
        api = CDMSRestApi()
        api.list(self.service, top=10, skip=1, select=['a', 'b'], filters='c,d', order_by=['e', 'f'])

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            urlparse(responses.calls[0].request.url).query,
            '$top=10&$skip=1&$filter=c,d&$orderby=e,f&$select=a,b'
        )

    @responses.activate
    def test_order_by_as_string(self):
        """
        Call to the list endpoint with the order_by param as a string instead of a list.
        """
        api = CDMSRestApi()
        api.list(self.service, order_by='something')

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            urlparse(responses.calls[0].request.url).query,
            '$top=50&$skip=0&$orderby=something'
        )


class GetTestCase(MockedResponseMixin, CookieStorageTestCase):
    def setUp(self):
        super(GetTestCase, self).setUp()
        self.mock_cookie()

        self.service = 'MyService'
        self.guid = '001122'
        self.url = "{}/{}Set(guid'{}')".format(CDMSRestApi.CRM_REST_BASE_URL, self.service, self.guid)
        responses.add(
            responses.GET, self.url,
            status=200, body=json.dumps({'d': 'something'})
        )

    @responses.activate
    def test_get(self):
        api = CDMSRestApi()
        resp = api.get(self.service, self.guid)

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(resp, 'something')


class UpdateTestCase(MockedResponseMixin, CookieStorageTestCase):
    def setUp(self):
        super(UpdateTestCase, self).setUp()
        self.mock_cookie()

        self.service = 'MyService'
        self.guid = '001122'
        self.url = "{}/{}Set(guid'{}')".format(CDMSRestApi.CRM_REST_BASE_URL, self.service, self.guid)
        self.data = {'key': 'value'}
        responses.add(responses.PUT, self.url, status=204)
        responses.add(
            responses.GET, self.url,
            status=200, body=json.dumps({'d': 'something updated'})
        )

    @responses.activate
    def test_update(self):
        api = CDMSRestApi()
        resp = api.update(self.service, self.guid, data=self.data)

        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(resp, 'something updated')
        self.assertDictEqual(
            json.loads(responses.calls[0].request.body), self.data
        )


class CreateTestCase(MockedResponseMixin, CookieStorageTestCase):
    def setUp(self):
        super(CreateTestCase, self).setUp()
        self.mock_cookie()

        self.service = 'MyService'
        self.url = "{}/{}Set".format(CDMSRestApi.CRM_REST_BASE_URL, self.service)
        self.data = {'key': 'value'}
        responses.add(
            responses.POST, self.url,
            status=200, body=json.dumps({'d': 'something'})
        )

    @responses.activate
    def test_create(self):
        api = CDMSRestApi()
        resp = api.create(self.service, data=self.data)

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(resp, 'something')
        self.assertDictEqual(
            json.loads(responses.calls[0].request.body), self.data
        )


class DeleteTestCase(MockedResponseMixin, CookieStorageTestCase):
    def setUp(self):
        super(DeleteTestCase, self).setUp()
        self.mock_cookie()

        self.service = 'MyService'
        self.guid = '001122'
        self.url = "{}/{}Set(guid'{}')".format(CDMSRestApi.CRM_REST_BASE_URL, self.service, self.guid)
        responses.add(
            responses.DELETE, self.url,
            status=204
        )

    @responses.activate
    def test_delete(self):
        api = CDMSRestApi()
        api.delete(self.service, self.guid)
        self.assertEqual(len(responses.calls), 1)
