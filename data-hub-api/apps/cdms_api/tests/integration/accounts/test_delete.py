import uuid

from ....exceptions import CDMSNotFoundException
from ..client_test_case import ClientTestCase


MSDCRM11_ERROR_DOES_NOT_EXIST = '-2147220969'


class TestDelete(ClientTestCase):

    def test_set_up(self):
        """
        TestDelete starts with no Accounts
        """
        self.assertServiceEmpty('Account')

    def test_bad_request(self):
        """
        Client DELETE without a full guid gets 400
        """
        result = self.client.delete('Account', '1234')

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.reason, 'Bad Request')

    def test_missing(self):
        """
        Client DELETEs missing Account, gets 404

        Assert that MSDCRM11's error code matches the expected.
        """
        with self.assertRaises(CDMSNotFoundException) as context:
            self.client.delete('Account', uuid.uuid4())

        self.assertEqual(context.exception.message['error']['code'], MSDCRM11_ERROR_DOES_NOT_EXIST)

    def test_existing(self):
        """
        Client DELETEs existing Account, gets 204

        TODO: Remove bootstrapped manually created Account
        """
        a_id = 'DFB77162-9164-E611-80CF-000D3AB34C09'

        result = self.client.delete('Account', a_id)

        self.assertEqual(result.status_code, 204)
        self.assertEqual(result.content, b'')
        self.assertEqual(len(self.client.list('Account')), 0)
