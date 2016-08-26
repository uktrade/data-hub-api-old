from .existing_customer_address_test_case import ExistingCustomerAddressTestCase


class TestExistingCustomerAddressTestCase(ExistingCustomerAddressTestCase):

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
