from django.test import TestCase

from ...rest.api import CDMSRestApi
from ...rest.auth.ntlm import NTLMAuth
from ..decorators import skipIntegration


@skipIntegration
class ClientTestCase(TestCase):

    def setUp(self):
        super().setUp()
        self.client = CDMSRestApi(auth=NTLMAuth())
