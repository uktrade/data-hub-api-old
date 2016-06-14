import datetime

from django.test.testcases import TestCase

from companieshouse.sources.db.importers import CSVImporter
from companieshouse import constants


FULL_DATA = [
    "MY COMPANY NAME", "00000001", "Some care of", "Some po box", "1 HOUSE NAME", "NEW ROAD", "LONDON", "LONDON",
    "ENGLAND", "SW1A 1AA", "Private Limited Company", "Active", "UNITED KINGDOM", "01/01/2011", "01/01/2001",
    "1", "1", "01/01/2002", "01/01/2001", "DORMANT", "02/02/2016", "02/02/2015", "1", "2", "3", "4",
    "91040", "07210", "2040", "2020", "1", "2", "http://business.data.gov.uk/id/company/08209948",
    "1/1/1999", "previous name 1", "1/2/1999", "previous name 2", "1/3/1999", "previous name 3",
    "1/4/1999", "previous name 4", "1/5/1999", "previous name 5", "1/6/1999", "previous name 6",
    "1/7/1999", "previous name 7", "1/8/1999", "previous name 8", "1/9/1999", "previous name 9",
    "1/10/1999", "previous name 10"
]

MINIMAL_DATA = [
    "MY COMPANY NAME", "00000001", "", "", "", "", "", "",
    "", "", "Private Limited Company", "Active", "", "", "",
    "", "", "", "", "", "", "", "", "", "", "",
    "", "", "", "", "", "", "",
    "", "", "", "", "", "",
    "", "", "", "", "", "",
    "", "", "", "", "", "",
    "", ""
]


class CSVImporterBaseTestCase(TestCase):
    def setUp(self):
        self.importer = CSVImporter()

    def assert_date(self, csv_value, value):
        if not csv_value or not value:
            self.assertEqual(csv_value, value)
            return

        self.assertEqual(
            datetime.datetime.strptime(csv_value, '%d/%m/%Y').date().isoformat(),
            value
        )

    def assert_registered_office_address(self, csv_data, data):
        if not list(filter(None, csv_data)):
            self.assertFalse(data)
            return

        for index, prop in enumerate([
            'care_of', 'po_box', 'address_line_1', 'address_line_2', 'locality', 'region', 'country', 'postal_code'
        ]):
            self.assertEqual(data[prop], csv_data[index])

    def assert_accounts(self, csv_data, data):
        if not list(filter(None, csv_data)):
            self.assertFalse(data)
            return

        if 'accounting_reference_date' in data:
            self.assertEqual(int(csv_data[0]), data['accounting_reference_date']['day'])
            self.assertEqual(int(csv_data[1]), data['accounting_reference_date']['month'])
        else:
            self.assertFalse(csv_data[0])
            self.assertFalse(csv_data[1])
        self.assert_date(csv_data[2], data['next_due'])
        self.assert_date(csv_data[3], data['next_made_up_to'])
        self.assertEqual(csv_data[4], data['category'])

    def assert_annual_return(self, csv_data, data):
        if not list(filter(None, csv_data)):
            self.assertFalse(data)
            return

        self.assert_date(csv_data[0], data['next_due'])
        self.assert_date(csv_data[1], data['last_made_up_to'])

    def assert_mortgages(self, csv_data, data):
        if not list(filter(None, csv_data)):
            self.assertFalse(data)
            return

        for index, prop in enumerate([
            'num_made_up_to', 'num_outstanding', 'num_part_satisfied', 'num_satisfied'
        ]):
            self.assertEqual(int(csv_data[index]), data[prop])

    def assert_sic_codes(self, csv_data, data):
        if not list(filter(None, csv_data)):
            self.assertFalse(data)
            return

        for csv_code, data_code in zip(csv_data, data):
            self.assertEqual(csv_code, data_code)

    def assert_limited_partnerships(self, csv_data, data):
        if not list(filter(None, csv_data)):
            self.assertFalse(data)
            return

        for index, prop in enumerate(['num_gen_partners', 'num_lim_partners']):
            self.assertEqual(int(csv_data[index]), data[prop])

    def assert_previous_names(self, csv_data, data):
        if not list(filter(None, csv_data)):
            self.assertFalse(data)
            return

        index = 0
        for csv_date, csv_previous_name in zip(csv_data[0::2], csv_data[1::2]):
            self.assert_date(csv_date, data[index]['date'])
            self.assertEqual(csv_previous_name, data[index]['company_name'])
            index += 1

    def assert_data(self, csv_row, data):
        self.assertEqual(csv_row[0], data['company_name'])
        self.assertEqual(csv_row[1], data['company_number'])

        self.assert_registered_office_address(csv_row[2:10], data.get('registered_office_address'))

        self.assertEqual(
            csv_row[10].lower(),
            constants.COMPANY_TYPES.values[data['type']].display.lower()
        )
        self.assertEqual(
            csv_row[11].lower(),
            constants.COMPANY_STATUSES.values[data['company_status']].display.lower()
        )
        self.assertEqual(csv_row[12], data.get('country_of_origin', ''))

        self.assert_date(csv_row[13], data.get('date_of_dissolution', ''))
        self.assert_date(csv_row[14], data.get('date_of_creation', ''))

        self.assert_accounts(csv_row[15:20], data.get('accounts'))
        self.assert_annual_return(csv_row[20:22], data.get('annual_return'))
        self.assert_mortgages(csv_row[22:26], data.get('mortgages'))
        self.assert_sic_codes(csv_row[26:30], data.get('sic_codes'))

        self.assert_limited_partnerships(csv_row[30:32], data.get('limited_partnerships'))
        self.assertEqual(csv_row[32], data.get('URI', ''))

        self.assert_previous_names(csv_row[33:], data.get('previous_names'))


class CSVImporterTestCase(CSVImporterBaseTestCase):
    def test_full_data(self):
        data = self.importer.parse(iter(FULL_DATA))
        self.assert_data(FULL_DATA, data)

    def test_minimum_of_data(self):
        data = self.importer.parse(iter(MINIMAL_DATA))
        self.assert_data(MINIMAL_DATA, data)


class CompanyStatusTestCase(CSVImporterBaseTestCase):
    def test_known_substitute(self):
        csv_data = list(MINIMAL_DATA)
        csv_data[11] = 'In Administration/Receiver Manager'

        data = self.importer.parse(iter(csv_data))
        self.assertEqual(data['company_status'], 'administration')

    def test_unknown_substitute(self):
        """
        In case of an unknown status, the default 'active' value will be used instead.
        """
        csv_data = list(MINIMAL_DATA)
        csv_data[11] = 'some unknown status'

        data = self.importer.parse(iter(csv_data))
        self.assertEqual(data['company_status'], 'active')


class CompanyTypeTestCase(CSVImporterBaseTestCase):
    def test_known_substitute(self):
        csv_data = list(MINIMAL_DATA)
        csv_data[10] = 'Pri/ltd by guar/nsc (private, limited by guarantee, no share capital)'

        data = self.importer.parse(iter(csv_data))
        self.assertEqual(data['type'], 'private-limited-guarant-nsc')

    def test_unknown_substitute(self):
        csv_data = list(MINIMAL_DATA)
        csv_data[10] = 'some unknown types'

        data = self.importer.parse(iter(csv_data))
        self.assertEqual(data['type'], 'other')


class SicCodeTestCase(CSVImporterBaseTestCase):
    def test_clean_code(self):
        csv_data = list(MINIMAL_DATA)
        csv_data[26] = '23640'

        data = self.importer.parse(iter(csv_data))
        self.assertEqual(data['sic_codes'], ['23640'])

    def test_dirty_code(self):
        csv_data = list(MINIMAL_DATA)
        csv_data[26] = '23640-plus something else'

        data = self.importer.parse(iter(csv_data))
        self.assertEqual(data['sic_codes'], ['23640'])

    def test_invalid_code(self):
        csv_data = list(MINIMAL_DATA)
        csv_data[26] = 'invalid23640'

        data = self.importer.parse(iter(csv_data))
        self.assertFalse('sic_codes' in data)
