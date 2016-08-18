from .client_test_case import ClientTestCase


class TestAssertServiceCountEqual(ClientTestCase):

    def test_set_up(self):
        """
        TestAssertServiceCountEqual starts with empty Accounts
        """
        self.assertEqual(len(self.client.list('Account')), 0)

    def test_empty(self):
        """
        assertServiceCountEqual matches 0 service instances (Accounts)
        """
        self.assertServiceCountEqual('Account', 0)

    def test_one(self):
        """
        assertServiceCountEqual matches 1 service instance (Account)
        """
        account = self.client.create('Account', {'Name': 'assertServiceCountEqual one'})
        account['AccountId']

        self.assertServiceCountEqual('Account', 1)

    def test_many(self):
        """
        assertServiceCountEqual matches 5 Account instances

        Also since all Accounts are created with the same name, asserts that
        vanilla doesn't care about name clashes.
        """
        for _ in range(5):
            self.client.create('Account', {'Name': 'assertServiceCountEqual many'})

        self.assertServiceCountEqual('Account', 5)


class TestAssertServiceEmpty(ClientTestCase):

    def test_set_up(self):
        """
        TestAssertServiceEmpty starts with empty Accounts
        """
        self.assertEqual(len(self.client.list('Account')), 0)

    def test_empty(self):
        """
        assertServiceEmpty passes when none of service instance (Accounts)
        """
        self.assertServiceEmpty('Account')

    def test_one(self):
        """
        assertServiceEmpty fails with a single instance (Account)
        """
        account = self.client.create('Account', {'Name': 'assertServiceEmpty one'})
        account['AccountId']

        with self.assertRaises(AssertionError):
            self.assertServiceEmpty('Account')
