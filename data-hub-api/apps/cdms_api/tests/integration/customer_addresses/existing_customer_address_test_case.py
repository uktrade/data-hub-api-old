from ..client_test_case import ClientTestCase


class ExistingCustomerAddressTestCase(ClientTestCase):

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
