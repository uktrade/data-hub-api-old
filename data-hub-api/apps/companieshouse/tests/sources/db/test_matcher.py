from django.test.testcases import TestCase

from companieshouse.models import Company
from companieshouse.sources.db.matcher import ChDBMatcher


class ChDBMatcherTestCase(TestCase):
    def setUp(self):
        Company.objects.bulk_create([
            Company(
                number='001', name='MY COMPANY LIMITED',
                postcode='SW1A1AA', raw={}
            ),
            Company(
                number='002', name='The little white corporation',
                postcode='SW1A1AA', raw={}
            )
        ])

    def test_with_substring_match(self):
        """
        The matcher should find company 001 as its name is ILIKE 'my company'.
        """
        name = 'MY COMPANY LTD.'
        postcode = 'SW1A 1AA'

        matcher = ChDBMatcher(name=name, postcode=postcode)
        best_match = matcher.find()

        self.assertTrue(best_match)
        self.assertEqual(best_match.company_number, '001')
        self.assertEqual(len(matcher.findings), 1)

    def test_with_similarity_match(self):
        """
        The matcher should find company 002 as its name is postgres similar ( % ) to 'little corporation'.
        """
        name = 'little corporation'
        postcode = 'SW1A1AA'

        matcher = ChDBMatcher(name=name, postcode=postcode)
        best_match = matcher.find()

        self.assertTrue(best_match)
        self.assertEqual(best_match.company_number, '002')
        self.assertEqual(len(matcher.findings), 1)

    def test_without_match(self):
        """
        The matcher should not find any match as the name is different from the ones in the db.
        """
        name = 'name without match'
        postcode = 'SW1A 1AA'

        matcher = ChDBMatcher(name=name, postcode=postcode)
        best_match = matcher.find()

        self.assertEqual(best_match, None)
