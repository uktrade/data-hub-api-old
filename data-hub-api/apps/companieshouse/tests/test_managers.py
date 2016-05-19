import datetime

from django.test.testcases import TestCase
from django_countries import countries

from companieshouse.models import Company, CompanySicCode


FULL_DATA = {
    "URI": "http://business.data.gov.uk/id/company/00000001",
    "type": "ltd",
    "accounts": {
        "category": "DORMANT",
        "next_due": "2002-01-01",
        "next_made_up_to": "2001-01-01",
        "accounting_reference_date": {
            "day": 1,
            "month": 1
        }
    },
    "sic_codes": ["91040", "07210"],
    "company_name": "MY COMPANY NAME",
    "annual_return": {
        "next_due": "2016-02-02",
        "last_made_up_to": "2015-02-02"
    },
    "mortgages": {
        "num_made_up_to": 1,
        "num_outstanding": 2,
        "num_part_satisfied": 3,
        "num_satisfied": 4
    },
    "limited_partnerships": {
        "num_gen_partners": 1,
        "num_lim_partners": 2
    },
    "company_number": "00000001",
    "company_status": "active",
    "date_of_creation": "2001-01-01",
    "date_of_dissolution": "2011-01-01",
    "country_of_origin": "United Kingdom",
    "registered_office_address": {
        "care_of": "Some care of",
        "po_box": "Some po box",
        "locality": "LONDON",
        "region": "LONDON",
        "postal_code": "SW1A 1AA",
        "address_line_1": "1 HOUSE NAME",
        "address_line_2": "NEW ROAD",
        "country": "ENGLAND"
    },
    "previous_names": [
        {
            "date": "1999-12-1",
            "company_name": "my previous name"
        },
        {
            "date": "1999-11-1",
            "company_name": "my other previous name"
        }
    ]
}

MINIMAL_DATA = {
    "type": "ltd",
    "company_name": "MY COMPANY NAME",
    "company_number": "00000001",
    "company_status": "active"
}


class BaseFromCHTestCasea(TestCase):
    def convert_to_date(self, data_value):
        return datetime.datetime.strptime(data_value, '%Y-%m-%d').date()

    def assert_date(self, date_value, data_value):
        if not date_value or not data_value:
            self.assertEqual(date_value, data_value)
            return

        self.assertEqual(date_value, self.convert_to_date(data_value))

    def assert_company(self, company, data):
        self.assertEqual(company.number, data['company_number'])
        self.assertEqual(company.name, data['company_name'])

        registered_office_address = data.get('registered_office_address', {})
        self.assertEqual(company.address_line1, registered_office_address.get('address_line_1', ''))
        self.assertEqual(company.address_line2, registered_office_address.get('address_line_2', ''))
        self.assertEqual(company.postcode, registered_office_address.get('postal_code', ''))
        self.assertEqual(company.region, registered_office_address.get('region', ''))
        self.assertEqual(company.locality, registered_office_address.get('locality', ''))

        country_of_origin = data.get('country_of_origin')
        if not country_of_origin:
            self.assertEqual(company.country, country_of_origin)
        else:
            self.assertEqual(company.country.code, countries.by_name(data['country_of_origin']))

        self.assertEqual(company.company_type, data['type'])
        self.assertEqual(company.status, data['company_status'])
        self.assert_date(company.date_of_creation, data.get('date_of_creation'))
        self.assert_date(company.date_of_dissolution, data.get('date_of_dissolution'))
        self.assertTrue(company.raw)

    def assert_sic_codes(self, company, sic_codes):
        self.assertEqual(company.companysiccode_set.count(), len(sic_codes))

        self.assertListEqual(
            sorted(company.companysiccode_set.values_list('code', flat=True)),
            sorted(sic_codes)
        )

    def assert_previous_names(self, company, previous_names):
        self.assertEqual(company.companypreviousname_set.count(), len(previous_names))

        self.assertListEqual(
            sorted(list(company.companypreviousname_set.values_list('name', flat=True))),
            sorted([data['company_name'] for data in previous_names])
        )
        self.assertListEqual(
            sorted(list(company.companypreviousname_set.values_list('change_date', flat=True))),
            sorted([self.convert_to_date(data['date']) for data in previous_names])
        )


class CreateFromCHTestCase(BaseFromCHTestCasea):
    def test_full_data(self):
        data = dict(FULL_DATA)
        self.assertEqual(Company.objects.count(), 0)

        Company.objects.update_from_CH_data(data)

        self.assertEqual(Company.objects.count(), 1)
        company = Company.objects.first()

        self.assert_company(company, data)
        self.assert_sic_codes(company, data['sic_codes'])
        self.assert_previous_names(company, data['previous_names'])

    def test_minimum_of_data(self):
        data = dict(MINIMAL_DATA)
        self.assertEqual(Company.objects.count(), 0)

        Company.objects.update_from_CH_data(data)

        self.assertEqual(Company.objects.count(), 1)
        company = Company.objects.first()

        self.assert_company(company, data)
        self.assert_sic_codes(company, [])
        self.assert_previous_names(company, [])


class UpdateFromCHTestCase(BaseFromCHTestCasea):
    def setUp(self):
        company = Company.objects.create(
            number='00000001',
            name='My OLD COMPANY NAME',
            address_line1='MY OLD ADDRESS 1',
            address_line2='MY OLD ADDRESS 2',
            postcode='W1 1BB',
            region='OLD REGION',
            locality='OLD LOCALITY',
            country='FR',
            company_type='llp',
            status='dismissed',
            date_of_creation=datetime.date(year=1999, month=2, day=2),
            date_of_dissolution=datetime.date(year=2000, month=2, day=2),
            raw={
                'something': 'something-else'
            }
        )
        company.companysiccode_set.create(code='19100')
        company.companypreviousname_set.create(
            name='something-else', change_date=datetime.date(year=1980, month=1, day=1)
        )

    def test_full_data(self):
        data = dict(FULL_DATA)

        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(CompanySicCode.objects.count(), 1)

        Company.objects.update_from_CH_data(data)

        self.assertEqual(Company.objects.count(), 1)
        company = Company.objects.first()

        self.assert_company(company, data)
        self.assert_sic_codes(company, data['sic_codes'])
        self.assert_previous_names(company, data['previous_names'])

    def test_minimum_of_data(self):
        data = dict(MINIMAL_DATA)

        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(CompanySicCode.objects.count(), 1)

        Company.objects.update_from_CH_data(data)

        self.assertEqual(Company.objects.count(), 1)
        company = Company.objects.first()

        self.assert_company(company, data)
        self.assert_sic_codes(company, [])
        self.assert_previous_names(company, [])
