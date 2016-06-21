import os
import hmac
import base64
import hashlib
import datetime
import requests
import logging
from uuid import uuid4

from suds.sax.parser import Parser

from django.utils import timezone
from django.conf import settings
from django.template import Engine, Context
from django.core.exceptions import ImproperlyConfigured

from ..exceptions import ErrorResponseException, LoginErrorException, UnexpectedResponseException

logger = logging.getLogger('cmds_api.soap.api')

CDMS_EXPIRATION_TOKEN_DELTA = 5  # in mins

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def flatten_xml_string(xml_string):
    """
    Flatten the xml string so that the output is in one line and without spaces/tabs etc.
    This is because otherwise the request is not valid and gets rejected.
    """
    return ''.join([line.strip() for line in xml_string.split('\n')])


def render_to_string(template_name, context):
    """
    The same as the Django one but this only searches for templates in the './templates' folder.
    """
    template_engine = Engine(dirs=[os.path.join(BASE_DIR, 'templates')])
    template = template_engine.get_template(template_name)
    return template.render(Context(context))


def get_request_now():
    """
    When constructing the SOAP request, the timestamps have to be naive but with localtime values.
    E.g. if the current offset is utc+1 and the utc now is 2016/03/30 0:00, the SOAP endpoint expects 2016/03/30 1:00
    without tzinfo. That's pretty ugly but ¯\_(ツ)_/¯

    In order to do that, this function gets the utc value, translates it into a local one and makes it naive by
    deleting the tzinfo.
    """
    now = timezone.localtime(timezone.now())
    return timezone.make_naive(now)


class CDMSSoapAPI(object):
    """
    Object used to make SOAP requests to CDMS.
    At the moment it's quite basic as it's meant to be used only for authentication but it can definitely be extended
    and improved.

    Example usage:

        api = CDMSSoapAPI(username, password)
        api.get_whoami()  # returns dict with user id
        api.get_user(user_id)  # returns data about user with id == 'user_id'

    That's pretty much it.
    The methods raise `ErrorResponseException` for generic errors with raw SOAP response in `e.content` or
    `LoginErrorException` in case of errors with (username, password) authentication/authorization.

    In theory you would try/catch LoginErrorException and return invalid creds error msg.
    To use the module for determining if a user can access CDMS, you only need to do something like:

        api = CDMSSoapAPI(username, password)
        try:
            user_ids = api.get_whoami()
            user_data = api.get_user(user_ids['UserId'])

            # valid username/password
        except LoginErrorException:
            # wrong username/password

    The error triggering logic can be improved as it could really be more error specific (e.g. 404, 400 etc.).
    For now, we only need to catch LoginErrorExceptions so it's good enough.
    The annoying thing is that the response have status code == 500 in all cases so you have to parse
    the msg and try to find the real reason (I know, right?).

    Behind the scenes, the code
        - uses the creds to authenticate against the ID Provider which returns a token if everything is fine
        - uses that token to ask the STS for a CDMS auth token instead
        - this last token can then be used to make authenticated calls to Dynamics and get back objects

    The authentication data is cached so that subsequent calls don't have to re-authenticate if the token has not
    expired.
    """
    CRM_DATA_ENDPOINT = '{}/XRMServices/2011/Organization.svc'.format(settings.CDMS_BASE_URL)
    CRM_ADFS_ENDPOINT = '{}/13/usernamemixed'.format(settings.CDMS_ADFS_URL)
    CRM_RSTS_ENDPOINT = '{}/adfs/services/trust/13/IssuedTokenMixedSymmetricBasic256'.format(settings.CDMS_RSTS_URL)

    def __init__(self, username, password):
        if not settings.CDMS_BASE_URL or not settings.CDMS_ADFS_URL or not settings.CDMS_RSTS_URL:
            raise ImproperlyConfigured(
                'Please set CDMS_BASE_URL, CDMS_ADFS_URL and CDMS_RSTS_URL in your settings.'
            )

        self.username = username
        self.password = password

        self.auth_context = {}

    # #### AUTH METHODS #### #

    def _generate_hmac_signature(self, binary_secret, creation_date, expiration_date):
        """
        Internal method which returns data used for the SOAP request signature.
        """
        timestamp = render_to_string(
            'partials/timestamp.xml', {
                'creation_date': creation_date,
                'expiration_date': expiration_date
            }
        )
        timestamp = flatten_xml_string(timestamp)

        timestamp_hasher = hashlib.sha1()
        timestamp_hasher.update(timestamp.encode('utf8'))
        timestamp_digest = base64.b64encode(timestamp_hasher.digest()).decode('ascii')
        signed_info = render_to_string(
            'partials/hmac.xml', {'signature_digest': timestamp_digest}
        )
        signed_info = flatten_xml_string(signed_info)

        hmac_hash = hmac.new(base64.b64decode(binary_secret), digestmod=hashlib.sha1)
        hmac_hash.update(signed_info.encode('utf8'))
        hashed = base64.b64encode(hmac_hash.digest()).decode('ascii')

        return hashed, timestamp_digest

    def _extract_auth_tokens(self, resp_content):
        """
        Internal method which extracts the auth data from the content of a SOAP response, generates signatures
        and other related fields needed for the next SOAP request and returns a dict with all of them.
        """
        parser = Parser()
        doc = parser.parse(string=resp_content)

        now = get_request_now()
        creation_date = now.isoformat()
        expiration_date_dt = (now + datetime.timedelta(minutes=CDMS_EXPIRATION_TOKEN_DELTA))
        expiration_date = expiration_date_dt.isoformat()

        rst_resp = doc.childAtPath('Envelope/Body/RequestSecurityTokenResponseCollection/RequestSecurityTokenResponse')
        enc_data = rst_resp.childAtPath('RequestedSecurityToken/EncryptedData')

        key_identifier = rst_resp.childAtPath('RequestedAttachedReference/SecurityTokenReference/KeyIdentifier').text
        ciphertext_key = enc_data.childAtPath('KeyInfo/EncryptedKey/CipherData/CipherValue').text
        ciphertext_token = enc_data.childAtPath('CipherData/CipherValue').text

        x509_info = enc_data.childAtPath(
            'KeyInfo/EncryptedKey/KeyInfo/SecurityTokenReference/X509Data/X509IssuerSerial'
        )
        x509_issuer_name = x509_info.childAtPath('X509IssuerName').text
        x509_serial_number = x509_info.childAtPath('X509SerialNumber').text

        binary_secret = rst_resp.childAtPath('RequestedProofToken/BinarySecret').text
        signature, signature_digest = self._generate_hmac_signature(binary_secret, creation_date, expiration_date)

        return {
            'ciphertext_key': ciphertext_key,
            'ciphertext_token': ciphertext_token,
            'key_identifier': key_identifier,
            'creation_date': creation_date,
            'expiration_date': expiration_date,
            'expiration_date_dt': expiration_date_dt,
            'X509_issuer_name': x509_issuer_name,
            'X509_serial_number': x509_serial_number,
            'signature_digest': signature_digest,
            'signature': signature,
        }

    def _make_soap_request_for_authentication(self, to_address, template, context):
        """
        This is the same as `make_raw_soap_request` but it's internally used to make auth SOAP requests.
        It expects requests to return 'OK' in most cases.

        The only 2 cases where the requests could fail are:
            - auth/authorization error: => raises LoginErrorException
            - server error: => raises UnexpectedResponseException
        """
        try:
            return self.make_raw_soap_request(to_address, template, context)
        except ErrorResponseException as e:
            if e.status_code == 500:
                """
                As the response is most of the time a 500 error with the 'message' being slightly different and
                somewhat meanful in each case, we need to parse the xml and try to find out what
                the real error is.

                In this case, we are matching the exact text response (I know :-|) to see if it's an
                authentication/authorization error.
                """

                parser = Parser()
                doc = parser.parse(string=e.content)
                reason = doc.childAtPath('Envelope/Body/Fault/Reason/Text').text.lower()

                if (reason == 'at least one security token in the message could not be validated.'):
                    # not sure 'fixing' the status code is a good idea here but to me it makes sense
                    raise LoginErrorException(
                        'Invalid credentials', status_code=400, content=e.content
                    )
                else:
                    raise UnexpectedResponseException(
                        e, status_code=e.status_code, content=e.content
                    )
            raise e

    def _make_auth_id_provider_soap_request(self):
        """
        Makes a request to the ID Provider and returns the SOAP response if it succeeds.
        Raises
            - LoginErrorException if username/password are invalid
            - UnexpectedResponseException in case of other errors
        """
        now = get_request_now()

        template = 'request_id_provider_token.xml'
        applies_to_address = '{}/adfs/services/trust'.format(
            settings.CDMS_RSTS_URL.replace('https', 'http')
        )  # doesn't like https here ¯\_(ツ)_/¯
        req_context = {
            'creation_date': now.isoformat(),
            'expiration_date': (now + datetime.timedelta(minutes=CDMS_EXPIRATION_TOKEN_DELTA)).isoformat(),
            'username': self.username,
            'password': self.password,
            'applies_to_address': applies_to_address
        }

        return self._make_soap_request_for_authentication(self.CRM_ADFS_ENDPOINT, template, req_context)

    def _make_auth_RSTS_token_soap_request(self):
        """
        Makes a request to:
            - the ID Provider to get the authentication token
            - the RSTS to get the CDMS token from the ID Prov token

        Raises:
            - LoginErrorException if username/password are invalid or the user can't access CDMS
            - UnexpectedResponseException in case of other errors
        """
        id_provider_token_response = self._make_auth_id_provider_soap_request()
        req_context = self._extract_auth_tokens(id_provider_token_response.content)

        template = 'request_RSTS_token.xml'
        req_context.update({
            'applies_to_address': settings.CDMS_BASE_URL
        })

        return self._make_soap_request_for_authentication(self.CRM_RSTS_ENDPOINT, template, req_context)

    # #### BASE SOAP REQUEST METHODS #### #

    def make_raw_soap_request(self, to_address, template, context):
        """
        Base method used to make SOAP requests to `to_address` using the resolved template/context as
        request body. It raises a generic ErrorResponseException if things fail.

        Unless you know what you're doing, you probably want to use the `make_authenticated_soap_request`
        method instead of this one.
        This is a base method and doesn't have much logic in it.
        """
        logger.debug('Calling CDMS URL {}'.format(to_address))
        headers = {'Content-Type': 'application/soap+xml; charset=UTF-8'}

        # request context with defaults values overridable by context
        req_context = {
            'random_uuid': uuid4,
            'to_address': to_address,
        }
        req_context.update(context)

        req_body = render_to_string(template, req_context)
        req_body = flatten_xml_string(req_body)

        resp = requests.post(to_address, req_body, headers=headers, verify=False)
        if not resp.ok:
            logger.debug('Got CDMS error (%s): %s' % (resp.status_code, resp.content))

            raise ErrorResponseException(
                '{} with status code {}'.format(to_address, resp.status_code),
                content=resp.content.decode('utf-8'),
                status_code=resp.status_code
            )

        return resp

    def _has_auth_context_expired(self):
        """
        Internal method used to determine if a cached authentication token exists and can be used.
        This is to avoid asking for a new token for every SOAP request.
        """
        if not self.auth_context:
            return True
        expiration_date = self.auth_context['expiration_date_dt']

        expired = (get_request_now() - datetime.timedelta(minutes=1)) >= expiration_date
        if expired:
            self.auth_context = {}  # so that next time it's faster
        return expired

    def make_authenticated_soap_request(self, to_address, template, context):
        """
        Higher level SOAP request method used to call `to_address` using the resolved template/context as
        request body.

        This uses the cached authentication token or gets a new token if that doesn't exist or is expired.

        It's meant to make life easier for devs that don't have to deal with the auth logic and can just
        focus on the actual SOAP request they want to make.

        Note: it can be made more efficient by refreshing the token instead of authenticating again if necessary.
        If I'm not wrong, there's a special endpoint with action "ReIssue" for refreshing expired tokens of
        something like that.
        """
        if self._has_auth_context_expired():
            logger.debug('Session expired, reauthenticating')

            token_resp = self._make_auth_RSTS_token_soap_request()
            self.auth_context = self._extract_auth_tokens(token_resp.content)

        req_context = dict(self.auth_context)
        req_context.update(context)
        return self.make_raw_soap_request(to_address, template, req_context)

    # #### SPECIFIC SOAP REQUEST METHODS #### #

    def make_execute_soap_request(self, request_name):
        """
        High level method used to make "Execute" SOAP requests.
        """
        template = 'execute.xml'
        context = {
            'request_name': request_name,
        }

        return self.make_authenticated_soap_request(
            self.CRM_DATA_ENDPOINT, template, context
        )

    def make_retrieve_soap_request(self, entity_name, entity_id, entity_props):
        """
        High level method used to make "Retrieve" SOAP requests. A Retrieve request is really just a GET by object id.

        entity_name: name of the object
        entity_id: id of the object
        entity_props: fields of the objects you want in the response. There's an option to return all fields but
            has not been implemented because of lack of time
        """
        template = 'retrieve.xml'
        context = {
            'entity_name': entity_name,
            'entity_id': entity_id,
            'entity_props': entity_props
        }

        return self.make_authenticated_soap_request(
            self.CRM_DATA_ENDPOINT, template, context
        )

    # #### NON-SOAP RESPONSES, THEY RETURN PYTHON TYPES, NOT SOAP NONSENSE #### #

    def get_whoami(self):
        """
        Returns the ids of the logged in user as a dict of type:
        {
            'UserId': ...,
            'BusinessUnitId': ...,
            'OrganizationId': ...
        }
        """
        response = self.make_execute_soap_request('WhoAmI')

        parser = Parser()
        doc = parser.parse(string=response.content)

        results_el = doc.childAtPath('Envelope/Body/ExecuteResponse/ExecuteResult/Results')
        data = {}
        for result_el in results_el:
            key = result_el.getChild('key').text
            value = result_el.getChild('value').text
            data[key] = value

        return data

    def get_user(self, user_id):
        """
        Returns data of the user with id == `user_id` as a dict of type:
        {
            'firstname': ...,
            'lastname': ...,
            'internalemailaddress': ...,
            'systemuserid': ...,
        }
        """
        response = self.make_retrieve_soap_request(
            'systemuser', user_id, ['firstname', 'lastname', 'internalemailaddress']
        )

        parser = Parser()
        doc = parser.parse(string=response.content)

        attrs_el = doc.childAtPath('Envelope/Body/RetrieveResponse/RetrieveResult/Attributes')
        data = {}
        for attr_el in attrs_el:
            key = attr_el.getChild('key').text
            value = attr_el.getChild('value').text
            data[key] = value

        return data
