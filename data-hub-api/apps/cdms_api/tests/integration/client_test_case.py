from django.test import TestCase

from ...rest.api import CDMSRestApi
from ...rest.auth.ntlm import NTLMAuth
from ..decorators import skipIntegration


@skipIntegration
class ClientTestCase(TestCase):

    def setUp(self):
        super().setUp()
        self.client = CDMSRestApi(auth=NTLMAuth())

    def assertServiceEmpty(self, service):
        """
        Assert that service has no entities
        """
        self.assertServiceCountEqual(service, 0)

    def assertServiceCountEqual(self, service, num):
        """
        Assert that service has number of entities
        """
        self.assertEqual(len(self.client.list(service)), num)
