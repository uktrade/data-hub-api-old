import json
import responses

from django.conf import settings
from django.test.testcases import TestCase

from companieshouse.sources.api import COMPANIES_HOUSE_BASE_URL

from companieshouse.sources.duedil import DUEDIL_BASE_URL
from companieshouse.sources.duedil.matcher import DueDilMatcher


class DueDilMatcherTestCase(TestCase):
    def get_duedil_url(self, q):
        return '{}search?q={}&api_key={}'.format(
            DUEDIL_BASE_URL, q, settings.DUEDIL_TOKEN
        )

    def get_ch_company_url(self, company_number):
        return '{}company/{}'.format(COMPANIES_HOUSE_BASE_URL, company_number)

    def build_body_response(self, items):
        return json.dumps({
            'response': {
                'data': items
            }
        })

    def assertFindingEqual(self, finding, company_number, name, postcode, proximity, raw):
        self.assertEqual(finding.company_number, company_number)
        self.assertEqual(finding.name, name)
        self.assertEqual(finding.postcode, postcode)
        self.assertEqual(finding.raw, raw)

    @responses.activate
    def test_without_findings(self):
        """
        In case of no findings
            => best_match == None
        """
        name = 'non-existing'
        postcode = 'SW1A 1AA'

        responses.add(
            responses.GET,
            self.get_duedil_url(name),
            match_querystring=True,
            status=404
        )

        matcher = DueDilMatcher(name=name, postcode=postcode)
        best_match = matcher.find()
        self.assertEqual(best_match, None)
        self.assertEqual(matcher.findings, [])

    @responses.activate
    def test_with_one_finding_without_ch_matching(self):
        """
        In case of one finding without related CH record
            => best_match == DueDil record with partial information
        """
        item = {
            'name': 'MY COMPANY',
            'locale': 'United Kingdom',
            'uri': 'http://api.duedil.com/open/uk/company/00000001.json',
            'company_number': '00000001'
        }

        name = 'my company ltd'
        postcode = 'SW1A 1AA'

        responses.add(
            responses.GET,
            self.get_duedil_url(name),
            match_querystring=True,
            body=self.build_body_response([item]),
            content_type='application/json'
        )

        responses.add(
            responses.GET,
            self.get_ch_company_url(item['company_number']),
            match_querystring=True,
            status=404
        )

        matcher = DueDilMatcher(name=name, postcode=postcode)
        best_match = matcher.find()
        self.assertTrue(best_match)
        self.assertFindingEqual(
            best_match,
            name=item['name'],
            company_number=item['company_number'],
            postcode=None,
            proximity=0.5,
            raw={
                'company_name': item['name'],
                'company_number': item['company_number']
            }
        )
        self.assertEqual(len(matcher.findings), 1)

    @responses.activate
    def test_with_one_finding_with_ch_matching(self):
        """
        In case of one finding with related CH record
            => best_match == DueDil record with full information
        """
        item = {
            'name': 'MY COMPANY',
            'locale': 'United Kingdom',
            'uri': 'http://api.duedil.com/open/uk/company/00000001.json',
            'company_number': '00000001'
        }

        ch_item = {
            'company_name': item['name'],
            'registered_office_address': {
                'postal_code': 'SW1A 1AA'
            }
        }

        name = 'my company ltd'
        postcode = 'SW1A 1AA'

        responses.add(
            responses.GET,
            self.get_duedil_url(name),
            match_querystring=True,
            body=self.build_body_response([item]),
            content_type='application/json'
        )

        responses.add(
            responses.GET,
            self.get_ch_company_url(item['company_number']),
            body=json.dumps(ch_item),
            content_type='application/json'
        )

        matcher = DueDilMatcher(name=name, postcode=postcode)
        best_match = matcher.find()
        self.assertTrue(best_match)
        self.assertFindingEqual(
            best_match,
            name=item['name'],
            company_number=item['company_number'],
            postcode=ch_item['registered_office_address']['postal_code'],
            proximity=1,
            raw=ch_item
        )
        self.assertEqual(len(matcher.findings), 1)

    @responses.activate
    def test_with_some_findings(self):
        """
        In case of more than one findings
            => best_match == record with higher proximity
        """
        item_075 = {
            'name': 'MY COMPANY',
            'locale': 'United Kingdom',
            'uri': 'http://api.duedil.com/open/uk/company/00000001.json',
            'company_number': '00000001'
        }

        ch_item_075 = {
            'company_name': item_075['name'],
            'registered_office_address': {
                'postal_code': 'SW1A 1AB'
            }
        }

        item_025 = {
            'name': 'MY COMPANY TEST',
            'locale': 'United Kingdom',
            'uri': 'http://api.duedil.com/open/uk/company/00000002.json',
            'company_number': '00000002'
        }

        name = 'my company ltd'
        postcode = 'SW1A 1AA'

        responses.add(
            responses.GET,
            self.get_duedil_url(name),
            match_querystring=True,
            body=self.build_body_response([item_025, item_075]),
            content_type='application/json'
        )

        responses.add(
            responses.GET,
            self.get_ch_company_url(item_025['company_number']),
            match_querystring=True,
            status=404
        )

        responses.add(
            responses.GET,
            self.get_ch_company_url(item_075['company_number']),
            body=json.dumps(ch_item_075),
            content_type='application/json'
        )

        matcher = DueDilMatcher(name=name, postcode=postcode)
        best_match = matcher.find()
        self.assertTrue(best_match)
        self.assertFindingEqual(
            best_match,
            name=item_075['name'],
            company_number=item_075['company_number'],
            postcode=ch_item_075['registered_office_address']['postal_code'],
            proximity=0.75,
            raw=ch_item_075
        )
        self.assertEqual(len(matcher.findings), 2)
