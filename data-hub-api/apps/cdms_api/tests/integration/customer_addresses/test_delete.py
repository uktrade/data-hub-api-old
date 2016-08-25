from ....exceptions import CDMSNotFoundException
from ..client_test_case import ClientTestCase


class TestDelete(ClientTestCase):

    def setUp(self):
        """
        Create Account. Child CustomerAddresses will be created.
        """
        super().setUp()
        account = self.client.create('Account', data={})
        self.guids = {
            'account': account['AccountId'],
            'address1': account['Address1_AddressId'],
            'address2': account['Address2_AddressId'],
        }

    def test_set_up(self):
        """
        setUp: 2 CustomerAddresses in CRM, both can be loaded
        """
        self.assertServiceCountEqual('CustomerAddress', 2)
        address1 = self.client.get('CustomerAddress', self.guids['address1'])
        self.client.get('CustomerAddress', self.guids['address2'])

    def test_delete_cascade(self):
        """
        Client delete on Account deletes 2 child CustomerAddresses
        """
        self.client.delete('Account', self.guids['account'])

        self.assertServiceCountEqual('CustomerAddress', 0)
        with self.assertRaises(CDMSNotFoundException):
            self.client.get('CustomerAddress', self.guids['address1'])
        with self.assertRaises(CDMSNotFoundException):
            self.client.get('CustomerAddress', self.guids['address2'])

    def test_delete_stand_alone(self):
        """
        Client deletes a single CustomerAddress from Account

        Dynamics creates a new CustomerAddress entity to replace it so that the
        number remains the same. New CustomerAddress can be loaded and is
        empty. Original Address2 remains the same and in place.
        """
        self.assertServiceCountEqual('CustomerAddress', 2)

        self.client.delete('CustomerAddress', self.guids['address1'])

        with self.assertRaises(CDMSNotFoundException):
            self.client.get('CustomerAddress', self.guids['address1'])
        self.client.get('CustomerAddress', self.guids['address2'])
