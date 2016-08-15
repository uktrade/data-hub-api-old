from django.test import TestCase

from ...rest.api import CDMSRestApi
from ...rest.auth.ntlm import NTLMAuth
from ..decorators import skipIntegration


@skipIntegration
class TestClient(TestCase):

    def test_happy(self):
        """
        Client can List Organisations returns single entry: Test organisation
        """
        client = CDMSRestApi(auth=NTLMAuth())

        result = client.list('Organization')

        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertEqual(entry['Name'], 'UKTI Test')
