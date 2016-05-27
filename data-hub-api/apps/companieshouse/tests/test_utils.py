from django.test.testcases import TestCase

from companieshouse.utils import clean_country


class CleanCountryTestCase(TestCase):
    def test_uppercase(self):
        self.assertEqual(
            clean_country('UNITED KINGDOM'),
            'GB'
        )

    def test_invalid(self):
        self.assertEqual(
            clean_country('Igaly'),
            None
        )

    def test_None(self):
        self.assertEqual(
            clean_country(None),
            None
        )

    def test_empty(self):
        self.assertEqual(
            clean_country(''),
            None
        )
