from ....exceptions import CDMSNotFoundException
from ..client_test_case import ClientTestCase


class TestDeleteAllNone(ClientTestCase):

    def test_none(self):
        """
        Client delete_all with no entities does nothing
        """
        result = self.client.delete_all('Account')

        self.assertEqual(result, 0)

    def test_missing(self):
        """
        Client delete_all raises if service does not exist
        """
        with self.assertRaises(CDMSNotFoundException):
            self.client.delete_all('__NO_SERVICE__')


class TestDeleteAllSome(ClientTestCase):

    def setUp(self):
        """
        Build 3 Accounts to be deleted
        """
        super().setUp()
        self.guids = []
        for i in range(3):
            name = 'delete_all {}'.format(i)
            account = self.client.create('Account', {'Name': name})
            self.guids.append(account['AccountId'])

    def tearDown(self):
        for guid in self.guids:
            try:
                self.client.delete('Account', guid)
            except CDMSNotFoundException:
                pass

    def test_set_up(self):
        """
        setUp: Three Accounts exist
        """
        self.assertServiceCountEqual('Account', 3)

    def test_happy(self):
        """
        Client delete_all deletes multiple entities and leaves service empty
        """
        result = self.client.delete_all('Account')

        self.assertServiceEmpty('Account')
        self.assertEqual(result, 3)
