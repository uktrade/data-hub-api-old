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

    def test_account_create_cascade(self):
        """
        Client creating Account will feed data into Address instances

        When CustomerAddress entities are loaded back fields do not need the
        prefix.
        """
        data = {
            'Address1_City': '北京',
            'Address2_City': 'Auckland',
        }

        result = self.client.create('Account', data=data)

        self.assertEqual(result['Address1_City'], '北京')
        self.assertEqual(result['Address2_City'], 'Auckland')
        address1 = self.client.get('CustomerAddress', result['Address1_AddressId'])
        self.assertEqual(address1['City'], '北京')
        address2 = self.client.get('CustomerAddress', result['Address2_AddressId'])
        self.assertEqual(address2['City'], 'Auckland')

    def test_no_create_stand_alone(self):
        """
        Client can not create CustomerAddress with no data, has no parent

        NOTE: This is considered a server-side error and not a bad request,
        unlike other fails that are simpler.
        """
        with self.assertRaises(ErrorResponseException) as context:
            self.client.create('CustomerAddress', data={})

        self.assertEqual(context.exception.status_code, 500)
        message_str = context.exception.message['error']['message']['value']
        self.assertIn(' parented ', message_str)

    def test_account_can_not_create(self):
        """
        Client can not create Address, not top level resource

        Even the if current address1 is deleted before the creation, it still
        fails.
        """
        account = self.client.create('Account', data={})
        data = {
            'ParentId': account['AccountId'],
            'City': 'Newcastle',
        }

        with self.assertRaises(ErrorResponseException) as context:
            self.client.create('CustomerAddress', data=data)

        message_str = context.exception.message['error']['message']['value']
        self.assertIn('top-level resource', message_str)
