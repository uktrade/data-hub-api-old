from ..client_test_case import ClientTestCase


class TestListEmpty(ClientTestCase):

    def test_set_up(self):
        """
        setUp: no Accounts
        """
        self.assertServiceEmpty('Account')

    def test_empty(self):
        """
        Client Lists Accounts which is empty and none are returned
        """
        result = self.client.list('Account')

        self.assertEqual(len(result), 0)


class TestListOne(ClientTestCase):

    def setUp(self):
        """
        Create Account for use in listing
        """
        super().setUp()
        account = self.client.create('Account', {'Name': 'TestListOne'})
        self.guid = account['AccountId']

    def tearDown(self):
        self.client.delete('Account', self.guid)
        super().tearDown()

    def test_set_up(self):
        """
        setUp: One Account exists
        """
        self.assertServiceCountEqual('Account', 1)

    def test_one(self):
        """
        Client Lists Accounts when one exists, gets one entry
        """
        result = self.client.list('Account')

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['Name'], 'TestListOne')
        self.assertEqual(result[0]['AccountId'], self.guid)
