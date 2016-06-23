import mock
import datetime
import os
import responses

from django.utils import timezone
from django.test.testcases import TestCase
from django.core.exceptions import ImproperlyConfigured

from cdms_api.exceptions import ErrorResponseException, UnexpectedResponseException, LoginErrorException
from cdms_api.soap.api import CDMSSoapAPI, flatten_xml_string, get_request_now

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_mocked_response(template_name):
    """
    Gets the mocked response from the filesystem in the './responses' folder.
    """
    file_path = os.path.join(BASE_DIR, 'responses', template_name)
    with open(file_path) as f:
        return f.read()

ID_PROVIDER_SUCCESS_RESPONSE = get_mocked_response('id_provider_success.xml')
SERVER_ERROR_RESPONSE = get_mocked_response('auth_server_error.xml')
AUTHENTICATION_ERROR_RESPONSE = get_mocked_response('authentication_error.xml')
WHO_AM_I_RESPONSE = get_mocked_response('who_am_I.xml')
GET_USER_NOT_FOUND_RESPONSE = get_mocked_response('get_user_not_found.xml')
GET_USER_RESPONSE = get_mocked_response('get_user_success.xml')


class BaseSoapApiTestCase(TestCase):
    def mock_success_auth_responses(self):
        """
        Mocks the authentication responses to return 200.
        """
        responses.add(
            responses.POST, CDMSSoapAPI.CRM_ADFS_ENDPOINT, status=200,
            body=ID_PROVIDER_SUCCESS_RESPONSE
        )
        responses.add(
            responses.POST, CDMSSoapAPI.CRM_RSTS_ENDPOINT, status=200,
            body=ID_PROVIDER_SUCCESS_RESPONSE
        )

    def assertRaisesWithStatusCode(self, exception, status_code, callable, *args, **kwds):
        try:
            callable(*args, **kwds)
        except exception as e:
            self.assertEqual(e.status_code, status_code)
        else:
            assert False, 'Should raise {}'.format(exception.__name__)


class SetUpTestCase(BaseSoapApiTestCase):
    def test_exception_if_urls_not_configured(self):
        """
        If CDMS settings are left blank, the constructor should raise ImproperlyConfigured.
        """
        with self.settings(
            CDMS_ADFS_URL='',
            CDMS_BASE_URL='',
            CDMS_RSTS_URL=''
        ):
            self.assertRaises(ImproperlyConfigured, CDMSSoapAPI, 'some-username', 'some-password')


class AuthTestCase(BaseSoapApiTestCase):
    @responses.activate
    def test_id_provider_returns_server_error(self):
        """
        If the ID Provider returns a 500 error, raise UnexpectedResponseException.
        """
        responses.add(
            responses.POST, CDMSSoapAPI.CRM_ADFS_ENDPOINT, status=500,
            body=SERVER_ERROR_RESPONSE
        )

        api = CDMSSoapAPI('username', 'password')
        self.assertRaisesWithStatusCode(UnexpectedResponseException, 500, api._make_auth_id_provider_soap_request)

    @responses.activate
    def test_id_provider_doesnt_validate_creds(self):
        """
        If the creds are invalid when contacting the ID Provider, raise LoginErrorException.
        """
        responses.add(
            responses.POST, CDMSSoapAPI.CRM_ADFS_ENDPOINT, status=500,
            body=AUTHENTICATION_ERROR_RESPONSE
        )

        api = CDMSSoapAPI('invalid', 'invalid')
        self.assertRaisesWithStatusCode(LoginErrorException, 400, api._make_auth_id_provider_soap_request)

    @responses.activate
    def test_RSTS_returns_server_error(self):
        """
        If the id provider returns OK but the RSTS returns a 500 error, raise UnexpectedResponseException.
        """
        responses.add(
            responses.POST, CDMSSoapAPI.CRM_ADFS_ENDPOINT, status=200,
            body=ID_PROVIDER_SUCCESS_RESPONSE
        )
        responses.add(
            responses.POST, CDMSSoapAPI.CRM_RSTS_ENDPOINT, status=500,
            body=SERVER_ERROR_RESPONSE
        )

        api = CDMSSoapAPI('username', 'password')
        self.assertRaisesWithStatusCode(UnexpectedResponseException, 500, api._make_auth_RSTS_token_soap_request)
        self.assertEqual(len(responses.calls), 2)

    @responses.activate
    def test_RSTS_doesnt_validate_token(self):
        """
        If the id provider returns OK but the RSTS says that the user cannot access the system he's trying
        to gain access to, return LoginErrorException.
        """
        responses.add(
            responses.POST, CDMSSoapAPI.CRM_ADFS_ENDPOINT, status=200,
            body=ID_PROVIDER_SUCCESS_RESPONSE
        )
        responses.add(
            responses.POST, CDMSSoapAPI.CRM_RSTS_ENDPOINT, status=500,
            body=AUTHENTICATION_ERROR_RESPONSE
        )

        api = CDMSSoapAPI('username', 'password')
        self.assertRaisesWithStatusCode(LoginErrorException, 400, api._make_auth_RSTS_token_soap_request)
        self.assertEqual(len(responses.calls), 2)

    @responses.activate
    def test_authenticates(self):
        """
        If the creds are valid and the user can access CDMS, the RSTS returns 200.
        """
        responses.add(
            responses.POST, CDMSSoapAPI.CRM_ADFS_ENDPOINT, status=200,
            body=ID_PROVIDER_SUCCESS_RESPONSE
        )
        responses.add(
            responses.POST, CDMSSoapAPI.CRM_RSTS_ENDPOINT, status=200,
            body=ID_PROVIDER_SUCCESS_RESPONSE
        )

        api = CDMSSoapAPI('username', 'password')
        resp = api._make_auth_RSTS_token_soap_request()
        self.assertEqual(resp.status_code, 200)

    @responses.activate
    def test_remember_auth_token_during_calls(self):
        """
        When making more than one call using the `make_authenticated_soap_request` method, the auth data
        should be cached so that can be reused for subsequent calls.
        """
        self.mock_success_auth_responses()

        to_address = 'https://test.com'
        responses.add(
            responses.POST, to_address, status=200, body=''
        )

        api = CDMSSoapAPI('username', 'password')

        # first call => authentication happen and call to `to_address` returns 200
        resp = api.make_authenticated_soap_request(to_address, 'execute.xml', {})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(responses.calls), 3)

        # second call => authentication reused and only extra call to `to_address` made
        resp = api.make_authenticated_soap_request(to_address, 'execute.xml', {})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(responses.calls), 4)

    @responses.activate
    def test_reauthenticates_if_token_is_expired(self):
        """
        When making more than one call using the `make_authenticated_soap_request` method and the auth data
        is expired, subsequent calls should re-authenticate.
        """
        self.mock_success_auth_responses()

        to_address = 'https://test.com'
        responses.add(
            responses.POST, to_address, status=200, body=''
        )

        api = CDMSSoapAPI('username', 'password')

        # first call => authentication happen and call to `to_address` returns 200
        resp = api.make_authenticated_soap_request(to_address, 'execute.xml', {})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(responses.calls), 3)

        # expiring the auth data explicitly
        api.auth_context['expiration_date_dt'] = api.auth_context['expiration_date_dt'] - datetime.timedelta(days=1)

        # second call => reauthenticates again
        resp = api.make_authenticated_soap_request(to_address, 'execute.xml', {})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(responses.calls), 6)


class GetWhoAmITestCase(BaseSoapApiTestCase):
    @responses.activate
    def test_valid_request(self):
        """
        Tests that the `get_whoami()` call returns a dict of ids.
        """
        self.mock_success_auth_responses()

        responses.add(
            responses.POST, CDMSSoapAPI.CRM_DATA_ENDPOINT, status=200,
            body=WHO_AM_I_RESPONSE
        )

        api = CDMSSoapAPI('username', 'password')

        resp = api.get_whoami()
        self.assertDictEqual(resp, {
            'UserId': '001',
            'BusinessUnitId': '002',
            'OrganizationId': '003'
        })


class GetUserTestCase(BaseSoapApiTestCase):
    @responses.activate
    def test_not_found(self):
        """
        Tests that when calling get_user with an invalid guid, it raises an exception.
        At the moment it raises a generic ErrorResponseException (which status code 500 :-|) but it should really
        improved to return a better exception instead (e.g. CDMSNotFoundException).
        """
        self.mock_success_auth_responses()

        responses.add(
            responses.POST, CDMSSoapAPI.CRM_DATA_ENDPOINT, status=500,
            body=GET_USER_NOT_FOUND_RESPONSE
        )

        api = CDMSSoapAPI('username', 'password')

        self.assertRaisesWithStatusCode(
            ErrorResponseException, 500, api.get_user, '0a0a00a0-0000-a000-a00a-a0000aaaa00a'
        )

    @responses.activate
    def test_valid_request(self):
        """
        Tests that when calling get_user with a valid guid, it returns a dict of user data.
        """
        self.mock_success_auth_responses()

        responses.add(
            responses.POST, CDMSSoapAPI.CRM_DATA_ENDPOINT, status=200,
            body=GET_USER_RESPONSE
        )

        api = CDMSSoapAPI('username', 'password')
        user_data = api.get_user('0a0a00a0-0000-a000-a00a-a0000aaaa00a')

        self.assertDictEqual(
            user_data, {
                'lastname': 'doe',
                'systemuserid': '0a0a00a0-0000-a000-a00a-a0000aaaa00a',
                'internalemailaddress': 'john.doe@example.com',
                'firstname': 'john'
            }
        )


class FlattenXmlStringTestCase(TestCase):
    def test_valid(self):
        response = flatten_xml_string("""
some line


    tabs



            more lines
""")
        self.assertEqual(response, "some linetabsmore lines")


class TestGetRequestNow(TestCase):
    @mock.patch('cdms_api.soap.api.timezone.now')
    def test_valid_gmt_offset(self, mocked_timezone_now):
        """
        Test that when now is before March 27 2016, the offset is == utc
        so get_request_now == the datetime param but without timezone info
        """
        mocked_timezone_now.return_value = datetime.datetime(
            year=2016, month=3, day=27, hour=0
        ).replace(tzinfo=timezone.utc)

        response = get_request_now()
        self.assertEqual(
            response,
            datetime.datetime(year=2016, month=3, day=27, hour=0)
        )

    @mock.patch('cdms_api.soap.api.timezone.now')
    def test_valid_bst_offset(self, mocked_timezone_now):
        """
        Test that when now is after March 27 2016, the offset is == utc+1
        so get_request_now == the datetime param +1 hour but without timezone info
        """
        mocked_timezone_now.return_value = datetime.datetime(
            year=2016, month=3, day=28, hour=0
        ).replace(tzinfo=timezone.utc)

        response = get_request_now()
        self.assertEqual(
            response,
            datetime.datetime(year=2016, month=3, day=28, hour=1)
        )
