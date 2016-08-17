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


class TestAssertServiceEmpty(ClientTestCase):

    def test_set_up(self):
        """
        TestAssertServiceEmpty starts with empty Accounts
        """
        self.assertEqual(len(self.client.list('Account')), 0)

    def test_empty(self):
        """
        TestAssertServiceEmpty passes when none of service instance (Accounts)
        """
        self.assertServiceEmpty('Account')
