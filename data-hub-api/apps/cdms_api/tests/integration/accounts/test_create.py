from ..client_test_case import ClientTestCase


class TestCreate(ClientTestCase):

    def test_no_data(self):
        """
        Client CREATE with no data creates an Account with no data
        """
        result = self.client.create('Account', {})

        self.assertServiceCountEqual('Account', 1)
        self.assertIsNone(result['Name'])
        guid = result['AccountId']
        self.assertGreater(guid, '')

    def test_required_field(self):
        """
        Client CREATE with required field saves that value

        NOTE: UTF8 characters appear to work end to end. No whitespace is
        stripped off the Name.
        """
        data = {
            'Name': ' Aché Pharma £td. ',
        }

        result = self.client.create('Account', data)

        self.assertServiceCountEqual('Account', 1)
        self.assertEqual(result['Name'], ' Aché Pharma £td. ')

    def test_empty_field(self):
        """
        Client CREATE with just whitespace keeps the whitespace
        """
        data = {
            'Name': '    ',
        }

        result = self.client.create('Account', data)

        self.assertServiceCountEqual('Account', 1)
        self.assertEqual(result['Name'], '    ')

    def test_ignored_data(self):
        """
        Client CREATE with data that doesn't match fields gets 400
        """
        result = self.client.create('Account', {'__WIBBLE__': '__VALUE__'})

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.reason, 'Bad Request')

    def test_extra_data(self):
        """
        Client CREATE with additional data gets saved
        """
        data = {
            'Name': 'René Limited.',
            'Telephone1': '+32 77 47 38 47 ext 112233'
        }

        result = self.client.create('Account', data)

        self.assertServiceCountEqual('Account', 1)
        self.assertEqual(result['Name'], 'René Limited.')
        self.assertEqual(result['Telephone1'], '+32 77 47 38 47 ext 112233')
