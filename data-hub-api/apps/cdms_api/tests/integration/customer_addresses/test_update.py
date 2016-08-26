# from ....exceptions import CDMSNotFoundException
from .existing_customer_address_test_case import ExistingCustomerAddressTestCase


class TestUpdate(ExistingCustomerAddressTestCase):
    """
    In both tests below:

    * On address line 2 replace 'Chaoyang' with empty string.
    * Create a (new) postcode entry for the address.
    * Number of addresses stayed the same. Address1 guid remained unchanged and
        its entity was updated.
    """

    def test_update_direct(self):
        """
        Client can update a single CustomerAddress directly
        """
        data = {
            'Line1': 'Buckingham Palace',
            'Line2': '',
            'City': 'London',
            'PostalCode': 'SW1A 1AA',
            'Country': 'UK',
        }

        result = self.client.update('CustomerAddress', self.guids['address1'], data=data)

        self.assertServiceCountEqual('CustomerAddress', 2)
        self.assertEqual(result['ParentId']['Id'], self.guids['account'])
        self.assertEqual(result['CustomerAddressId'], self.guids['address1'])
        self.assertEqual(result['Line1'], 'Buckingham Palace')
        self.assertIsNone(result['Line2'])
        self.assertEqual(result['City'], 'London')
        self.assertEqual(result['PostalCode'], 'SW1A 1AA')
        self.assertEqual(result['Country'], 'UK')
        account = self.client.get('Account', self.guids['account'])
        self.assertEqual(account['Address1_Line1'], 'Buckingham Palace')
        self.assertEqual(account['Address1_AddressId'], self.guids['address1'])
        self.assertEqual(account['Address2_AddressId'], self.guids['address2'])

    def test_update_through(self):
        """
        Client can update a single CustomerAddresses via its parent Account
        """
        data = {
            'Address1_Line1': 'Buckingham Palace',
            'Address1_Line2': '',
            'Address1_City': 'London',
            'Address1_PostalCode': 'SW1A 1AA',
            'Address1_Country': 'UK',
        }

        result = self.client.update('Account', self.guids['account'], data=data)

        self.assertServiceCountEqual('CustomerAddress', 2)
        self.assertEqual(result['Address1_AddressId'], self.guids['address1'])
        self.assertEqual(result['Address1_Line1'], 'Buckingham Palace')
        self.assertIsNone(result['Address1_Line2'])
        self.assertEqual(result['Address1_City'], 'London')
        self.assertEqual(result['Address1_PostalCode'], 'SW1A 1AA')
        self.assertEqual(result['Address1_Country'], 'UK')
        self.assertEqual(result['Address2_AddressId'], self.guids['address2'])
        self.assertEqual(result['Address2_Line1'], 'Victoria St W & Federal St')
