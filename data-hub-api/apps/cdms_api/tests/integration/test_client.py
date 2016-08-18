from .client_test_case import ClientTestCase


class TestClient(ClientTestCase):

    def test_happy(self):
        """
        Client can List Organisations returns single entry: Test organisation
        """
        result = self.client.list('Organization')

        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry['Name'], 'UKTI Test')
