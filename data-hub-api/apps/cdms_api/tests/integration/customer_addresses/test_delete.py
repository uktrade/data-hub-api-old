from ....exceptions import CDMSNotFoundException
from ..client_test_case import ClientTestCase


class TestDelete(ClientTestCase):

    def setUp(self):
        """
        Create Account. Child CustomerAddresses will be created.
        """
        super().setUp()
        data = {
            'Address1_Line1': '1 National Stadium S Rd',
            'Address1_Line2': 'Chaoyang',
            'Address1_City': '北京',
            'Address1_Country': 'China',
            'Address2_Line1': 'Victoria St W & Federal St',
            'Address2_City': 'Auckland 1010',
            'Address2_Country': 'New Zealand',
        }
        account = self.client.create('Account', data=data)
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
        self.assertEqual(address1['Line1'], '1 National Stadium S Rd')
        account = self.client.get('Account', self.guids['account'])
        self.assertEqual(account['Address1_Line1'], '1 National Stadium S Rd')
        address2 = self.client.get('CustomerAddress', self.guids['address2'])
        self.assertEqual(address2['Line1'], 'Victoria St W & Federal St')

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

        Dynamics creates a new CustomerAddress entity to replace it so that the
        number remains the same. New CustomerAddress can be loaded and is
        empty. Original Address2 remains the same and in place.
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
