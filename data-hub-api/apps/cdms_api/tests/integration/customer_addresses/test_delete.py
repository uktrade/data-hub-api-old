from ....exceptions import CDMSNotFoundException
from .existing_customer_address_test_case import ExistingCustomerAddressTestCase


class TestDelete(ExistingCustomerAddressTestCase):

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
        Client deletes single CustomerAddress from Account, Address left None
        """
        self.client.delete('CustomerAddress', self.guids['address1'])

        self.assertServiceCountEqual('CustomerAddress', 1)
        with self.assertRaises(CDMSNotFoundException):
            self.client.get('CustomerAddress', self.guids['address1'])
        self.client.get('CustomerAddress', self.guids['address2'])
        account = self.client.get('Account', self.guids['account'])
        self.assertIsNone(account['Address1_AddressId'])
        self.assertIsNone(account['Address1_Line1'])
        self.assertEqual(account['Address2_Line1'], 'Victoria St W & Federal St')
