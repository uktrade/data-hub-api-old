from django.test.testcases import TestCase

from companieshouse.sources.matcher import BaseMatcher, FindingResult


class MyMatcher(BaseMatcher):
    """
    Testing Matcher that allows settinging findings to check that the logic works
    """
    def set_findings(self, findings):
        self.findings = findings


class BaseMatcherTestCase(TestCase):
    def setUp(self):
        self.matcher = MyMatcher(
            name='some company', postcode='SW1A 1AA'
        )

    def test_without_findings(self):
        """
        No findings => return None
        """
        self.matcher.set_findings([])

        best_match = self.matcher.find()
        self.assertEqual(best_match, None)

    def test_with_one_finding(self):
        """
        Just one finding => return exacly that one
        """
        finding = FindingResult(
            company_number='0',
            name='company name',
            postcode='SW1A1AA',
            proximity=1,
            raw={'company_number': '0'}
        )
        self.matcher.set_findings([finding])

        best_match = self.matcher.find()
        self.assertTrue(best_match)
        self.assertEqual(best_match, finding)

    def test_with_some_findings(self):
        """
        More than one finding => return the one with higher proximity
        """
        finding_025 = FindingResult(
            company_number='025',
            name='company 025',
            postcode='SW1A1AA',
            proximity=0.25,
            raw={'company_number': '025'}
        )
        finding_075 = FindingResult(
            company_number='075',
            name='company 075',
            postcode='SW1A1AA',
            proximity=0.75,
            raw={'company_number': '075'}
        )
        finding_050 = FindingResult(
            company_number='050',
            name='company 050',
            postcode='SW1A1AA',
            proximity=0.5,
            raw={'company_number': '050'}
        )
        self.matcher.set_findings([
            finding_025, finding_075, finding_050
        ])

        best_match = self.matcher.find()
        self.assertTrue(best_match)
        self.assertEqual(best_match, finding_075)


class GetCHPostcodeTestCase(TestCase):
    def setUp(self):
        self.matcher = MyMatcher(
            name='some company', postcode='SW1A 1AA'
        )

    def test_with_no_props(self):
        self.assertEqual(
            self.matcher._get_ch_postcode({}),
            None
        )

    def test_with_registered_address_prop(self):
        data = {
            'registered_office_address': {
                'postal_code': 'SW1A 1AA'
            }
        }
        self.assertEqual(
            self.matcher._get_ch_postcode(data),
            'SW1A 1AA'
        )

    def test_with_address_prop(self):
        data = {
            'address': {
                'postal_code': 'SW1A 1AA'
            }
        }
        self.assertEqual(
            self.matcher._get_ch_postcode(data),
            'SW1A 1AA'
        )

    def test_with_both_registered_address_and_address_props(self):
        data = {
            'registered_office_address': {
                'postal_code': 'SW1A 1AA'
            },
            'address': {
                'postal_code': 'SW1A 1AB'
            }
        }
        self.assertEqual(
            self.matcher._get_ch_postcode(data),
            'SW1A 1AA'
        )
