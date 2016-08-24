import uuid

from ....exceptions import CDMSNotFoundException
from ..client_test_case import ClientTestCase


class TestGetEmpty(ClientTestCase):

    def test_set_up(self):
        """
        setUp: No Accounts in CRM
        """
        self.assertServiceEmpty('Account')

    def test_missing(self):
        """
        Client GET raises if entity not found
        """
        with self.assertRaises(CDMSNotFoundException):
            self.client.delete('Account', uuid.uuid4())


class TestGetData(ClientTestCase):

    def setUp(self):
        """
        Create 3 test accounts

        --------+---------------+--------------------------
         Name   | Telephone1    | Task
        --------+---------------+--------------------------
         A Ltd  | 112233        | Nothing, padding
         B Ltd  | +32 11 22 33  | GET using test
         C Ltd  | __number__    | Nothing, padding
        --------+---------------+--------------------------
        """
        super().setUp()
        data = {
            'a': {
                'Name': 'A Ltd',
                'Telephone1': '112233',
            },
            'b': {
                'Name': 'B Ltd',
                'Telephone1': '+32 11 22 33',
            },
            'c': {
                'Name': 'C Ltd',
                'Telephone1': '__number__',
            },
        }
        self.guids = {}
        for account_char, account_data in data.items():
            response = self.client.create('Account', account_data)
            self.guids[account_char] = response['AccountId']

    def test_set_up(self):
        """
        setUp: 3 Accounts exist, 1 will be loaded (GET). Guids have been saved
        """
        self.assertServiceCountEqual('Account', 3)
        self.assertGreater(self.guids['a'], '')
        self.assertGreater(self.guids['b'], '')
        self.assertGreater(self.guids['c'], '')

    def test_happy_a(self):
        """
        Client GET can load Account A Ltd
        """
        result = self.client.get('Account', self.guids['a'])

        self.assertEqual(result['Name'], 'A Ltd')
        self.assertEqual(result['Telephone1'], '112233')

    def test_happy_b(self):
        """
        Client GET can load Account B Ltd
        """
        result = self.client.get('Account', self.guids['b'])

        self.assertEqual(result['Name'], 'B Ltd')
        self.assertEqual(result['Telephone1'], '+32 11 22 33')

    def test_happy_c(self):
        """
        Client GET can load Account C Ltd
        """
        result = self.client.get('Account', self.guids['c'])

        self.assertEqual(result['Name'], 'C Ltd')
        self.assertEqual(result['Telephone1'], '__number__')

    def test_empty_data_none(self):
        """
        Client GET returns missing fiels as `None`
        """
        result = self.client.get('Account', self.guids['a'])

        self.assertIsNone(result['VersionNumber'])
