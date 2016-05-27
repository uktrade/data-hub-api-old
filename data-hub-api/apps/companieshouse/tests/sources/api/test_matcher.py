import json
import responses

from django.test.testcases import TestCase

from companieshouse.sources.api import COMPANIES_HOUSE_BASE_URL
from companieshouse.sources.api.matcher import ChAPIMatcher


class APIMatcherTestCase(TestCase):
    def get_ch_search_url(self, q):
        return '{}search/companies?q={}'.format(COMPANIES_HOUSE_BASE_URL, q)

    def build_body_response(self, items):
        return json.dumps({
            'start_index': 0,
            'page_number': 1,
            'kind': 'search#companies',
            'items': items,
            'total_results': len(items),
            'items_per_page': 20
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
            self.get_ch_search_url(name),
            match_querystring=True,
            body=self.build_body_response([]),
            content_type='application/json'
        )

        matcher = ChAPIMatcher(name=name, postcode=postcode)
        best_match = matcher.find()
        self.assertEqual(best_match, None)
        self.assertEqual(matcher.findings, [])

    @responses.activate
    def test_with_one_finding(self):
        """
        In case of one finding
            => best_match == CH record
        """
        item = {
            "matches": {
                "title": [1, 2, 4, 10]
            },
            "title": "MY COMPANY",
            "company_number": "00000001",
            "description": "00000001 - Incorporated on  1 January 2000",
            "snippet": "Buckingham Palace Road, London, SW1A 1AA",
            "company_type": "ltd",
            "kind": "searchresults#company",
            "description_identifier": [
                "incorporated-on"
            ],
            "address": {
                "address_line_1": "Buckingham Palace Road",
                "address_line_2": "",
                "locality": "LONDON",
                "postal_code": "SW1A 1AA",
                "region": "LONDON"
            },
            "date_of_creation": "2000-01-01",
            "company_status": "active",
            "links": {
                "self": "/company/00000001"
            }
        }

        name = 'my company ltd'
        postcode = 'SW1A 1AA'

        responses.add(
            responses.GET,
            self.get_ch_search_url(name),
            match_querystring=True,
            body=self.build_body_response([item]),
            content_type='application/json'
        )

        matcher = ChAPIMatcher(name=name, postcode=postcode)
        best_match = matcher.find()
        self.assertTrue(best_match)
        self.assertFindingEqual(
            best_match,
            name=item['title'],
            company_number=item['company_number'],
            postcode=item['address']['postal_code'],
            proximity=1,
            raw=item
        )
        self.assertEqual(len(matcher.findings), 1)

    @responses.activate
    def test_with_some_findings(self):
        """
        In case of more than one findings
            => best_match == record with higher proximity
        """
        item_075 = {
            "matches": {
                "title": [1, 2, 4, 10]
            },
            "title": "MY COMPANY",
            "company_number": "00000001",
            "description": "00000001 - Incorporated on  1 January 2000",
            "snippet": "Buckingham Palace Road, London, SW1A 1AB",
            "company_type": "ltd",
            "kind": "searchresults#company",
            "description_identifier": [
                "incorporated-on"
            ],
            "address": {
                "address_line_1": "Buckingham Palace Road",
                "address_line_2": "",
                "locality": "LONDON",
                "postal_code": "SW1A 1AB",
                "region": "LONDON"
            },
            "date_of_creation": "2000-01-01",
            "company_status": "active",
            "links": {
                "self": "/company/00000001"
            }
        }

        item_025 = {
            "matches": {
                "title": [1, 2, 4, 10]
            },
            "title": "MY COMPANY TEST",
            "company_number": "00000002",
            "description": "00000002 - Incorporated on  1 January 2000",
            "snippet": "Buckingham Palace Road, London, W1 1BB",
            "company_type": "ltd",
            "kind": "searchresults#company",
            "description_identifier": [
                "incorporated-on"
            ],
            "address": {
                "address_line_1": "Buckingham Palace Road",
                "address_line_2": "W1 1BB",
                "locality": "LONDON",
                "postal_code": "",
                "region": "LONDON"
            },
            "date_of_creation": "2000-01-01",
            "company_status": "active",
            "links": {
                "self": "/company/00000002"
            }
        }

        name = 'my company ltd'
        postcode = 'SW1A 1AA'

        responses.add(
            responses.GET,
            self.get_ch_search_url(name),
            match_querystring=True,
            body=self.build_body_response([item_025, item_075]),
            content_type='application/json'
        )

        matcher = ChAPIMatcher(name=name, postcode=postcode)
        best_match = matcher.find()
        self.assertTrue(best_match)
        self.assertFindingEqual(
            best_match,
            name=item_075['title'],
            company_number=item_075['company_number'],
            postcode=item_075['address']['postal_code'],
            proximity=0.75,
            raw=item_075
        )
        self.assertEqual(len(matcher.findings), 2)
