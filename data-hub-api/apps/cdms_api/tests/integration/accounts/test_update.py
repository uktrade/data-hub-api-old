from ....exceptions import ErrorResponseException
from ..client_test_case import ClientTestCase


class TestUpdate(ClientTestCase):

    def setUp(self):
        """
        Create 3 test accounts

        ----------------+---------------+--------------------------
         Name           | Telephone1    | Task
        ----------------+---------------+--------------------------
         Á la café Ltd  | 112233        | Does not change
         Børt Limited   | +32 11 22 33  | Will be updated by tests
         Crapola Ltd.   | __number__    | Does not change
        ----------------+---------------+--------------------------
        """
        super().setUp()
        data = {
            'a': {
                'Name': 'Á la café Ltd',
                'Telephone1': '112233',
            },
            'b': {
                'Name': 'Børt Limited',
                'Telephone1': '+32 11 22 33',
            },
            'c': {
                'Name': 'Crapola Ltd.',
                'Telephone1': '__number__',
            },
        }
        self.guids = {}
        for account_char, account_data in data.items():
            response = self.client.create('Account', account_data)
            self.guids[account_char] = response['AccountId']

    def test_set_up(self):
        """
        setUp: 3 Accounts exist, 1 will be updated
        """
        self.assertServiceCountEqual('Account', 3)

        result = self.client.get('Account', self.guids['b'])

        self.assertEqual(result['Name'], 'Børt Limited')
        self.assertEqual(result['Telephone1'], '+32 11 22 33')

    def test_happy_name(self):
        """
        Client can update an existing record with partial data

        Erné has become a title member, but the phone number has stayed the
        same. Other records remain the same.
        """
        data = {
            'Name': 'Børt and Erné PLC.',
        }

        result = self.client.update('Account', self.guids['b'], data)

        self.assertEqual(result['Name'], 'Børt and Erné PLC.')
        self.assertEqual(result['Telephone1'], '+32 11 22 33')
        a_account = self.client.get('Account', self.guids['a'])
        self.assertEqual(a_account['Name'], 'Á la café Ltd')
        self.assertEqual(a_account['Telephone1'], '112233')
        c_account = self.client.get('Account', self.guids['c'])
        self.assertEqual(c_account['Name'], 'Crapola Ltd.')
        self.assertEqual(c_account['Telephone1'], '__number__')

    def test_happy_add(self):
        """
        Client can update an existing record with extra data
        """
        data = {
            'Telephone2': '+1 234 567 890 ext 1234',
        }

        result = self.client.update('Account', self.guids['b'], data)

        self.assertEqual(result['Name'], 'Børt Limited')
        self.assertEqual(result['Telephone1'], '+32 11 22 33')
        self.assertEqual(result['Telephone2'], '+1 234 567 890 ext 1234')

    def test_missing(self):
        """
        Client attempts to add field that does not exist, raises
        """
        data = {
            '__OTHER__': 1,
        }

        with self.assertRaises(ErrorResponseException) as context:
            self.client.update('Account', self.guids['b'], data)

        self.assertEqual(context.exception.status_code, 400)

    def test_remove_data_empty_string(self):
        """
        Client can update a record and remove data with empty string
        """
        data = {
            'Name': '',
        }

        result = self.client.update('Account', self.guids['b'], data)

        self.assertIsNone(result['Name'])

    def test_remove_data_none(self):
        """
        Client can update a record and remove data with None
        """
        data = {
            'Name': None,
        }

        result = self.client.update('Account', self.guids['b'], data)

        self.assertIsNone(result['Name'])
