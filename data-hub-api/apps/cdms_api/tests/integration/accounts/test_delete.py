import uuid

from ....exceptions import CDMSNotFoundException
from ..client_test_case import ClientTestCase


MSDCRM11_ERROR_DOES_NOT_EXIST = '-2147220969'


class TestDelete(ClientTestCase):

    def test_set_up(self):
        """
        setUp: no Accounts
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
        """
        account = self.client.create('Account', {'Name': 'test_delete.test_existing'})
        a_id = account['AccountId']

        result = self.client.delete('Account', a_id)

        self.assertEqual(result.status_code, 204)
        self.assertEqual(result.content, b'')
        self.assertServiceEmpty('Account')
