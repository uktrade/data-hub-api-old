from ..client_test_case import ClientTestCase


class TestList(ClientTestCase):

    def test_empty(self):
        """
        Client Lists Accounts which is empty and none are returned
        """
        result = self.client.list('Account')

        self.assertEqual(len(result), 0)
