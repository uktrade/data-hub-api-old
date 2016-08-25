from ....exceptions import ErrorResponseException
from ..client_test_case import ClientTestCase


class TestCreate(ClientTestCase):

    def test_set_up(self):
        """
        setUp: No CustomerAddresses in CRM
        """
        self.assertServiceEmpty('CustomerAddress')

    def test_account_creates(self):
        """
        Client creating Account creates two CustomerAddress entities
        """
        self.client.create('Account', data={})

        self.assertServiceCountEqual('CustomerAddress', 2)

    def test_create_stand_alone(self):
        """
        Client can not create CustomerAddress with no data, has no parent

        NOTE: This is considered a server-side error and not a bad request,
        unlike other fails that are simpilar.
        """
        with self.assertRaises(ErrorResponseException) as context:
            self.client.create('CustomerAddress', data={})

        self.assertEqual(context.exception.status_code, 500)
