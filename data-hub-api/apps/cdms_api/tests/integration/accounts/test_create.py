from ..client_test_case import ClientTestCase


class TestCreate(ClientTestCase):

    def test_set_up(self):
        """
        TestCreate starts with no Accounts
        """
        self.assertServiceEmpty('Account')

    def test_happy_no_data(self):
        """
        Client CREATE with no data creates an Account with no data
        """
        result = self.client.create('Account', {})

        self.assertIsNone(result['Name'])
        guid = result['AccountId']
        self.assertGreater(guid, '')
        self.assertServiceCountEqual('Account', 1)
        self.cleanup_helper(guid)

    def cleanup_helper(self, guid):
        self.client.delete('Account', guid)
        self.assertServiceEmpty('Account')
