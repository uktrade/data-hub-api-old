import re
import datetime

from companieshouse import constants

SIC_CODE_RE = re.compile(r"^(\d+)")


class Parser(object):
    def parse(self, row):
        raise NotImplementedError()


class SimpleParser(Parser):
    def _parse(self, val):
        return val

    def parse(self, row):
        val = next(row)
        if not val:
            return val
        return self._parse(val)
simple_parser = SimpleParser()


class DateParser(SimpleParser):
    def _parse(self, val):
        return datetime.datetime.strptime(val, '%d/%m/%Y').date().isoformat()
date_parser = DateParser()


class IntParser(SimpleParser):
    def _parse(self, val):
        return int(val)
int_parser = IntParser()


class SentenceParser(SimpleParser):
    def _parse(self, val):
        norm_val = val.lower()
        return '{}{}'.format(norm_val[0].upper(), norm_val[1:])
sentence_parser = SentenceParser()


class SicCodeParser(SimpleParser):
    def _parse(self, val):
        parts = SIC_CODE_RE.findall(val)
        if not parts:
            return None
        return parts[0]
siccode_parser = SicCodeParser()


class CompanyTypeParser(SimpleParser):
    SUBSTITUTES = {
        'European public limited-liability company (se)': 'European public limited liability company (SE)',
        'Pri/ltd by guar/nsc (private, limited by guarantee, no share capital)': 'Private limited by guarantee without share capital',  # noqa
        'Pri/lbg/nsc (private, limited by guarantee, no share capital, use of \'limited\' exemption)': 'Private Limited Company by guarantee without share capital, use of &#39;Limited&#39; exemption',  # noqa
        'Community interest company': 'Other company type',
        'Private unlimited': 'Private unlimited company',
        'Registered society': 'Other company type',
        'Investment company with variable capital(umbrella)': 'Investment company with variable capital',
        'Investment company with variable capital (securities)': 'Investment company with variable capital',
        'Priv ltd sect. 30 (private limited company, section 30 of the companies act)': 'Private limited company',
    }
    CHOICES = constants.COMPANY_TYPES

    def _parse(self, val):
        val = sentence_parser._parse(val)

        key = self.SUBSTITUTES.get(val, val)

        try:
            return self.CHOICES.displays[key].value
        except KeyError:
            print(
                "Warning COMPANY_TYPE '{}' not found, using the default '{}' instead".format(
                    key, self.CHOICES.OTHER
                )
            )
            return self.CHOICES.OTHER
company_type_parser = CompanyTypeParser()


class CompanyStatusParser(SimpleParser):
    SUBSTITUTES = {
        'Active - Proposal to Strike off': 'Active',
        'ADMINISTRATION ORDER': 'In Administration',
        'Live but Receiver Manager on at least one charge': 'Active',
        'In Administration/Administrative Receiver': 'In Administration',
        'In Administration/Receiver Manager': 'In Administration',
        'RECEIVERSHIP': 'Receivership',
        'ADMINISTRATIVE RECEIVER': 'In Administration',
        'RECEIVER MANAGER / ADMINISTRATIVE RECEIVER': 'In Administration',
        'VOLUNTARY ARRANGEMENT / ADMINISTRATIVE RECEIVER': 'Voluntary Arrangement',
        'VOLUNTARY ARRANGEMENT / RECEIVER MANAGER': 'Voluntary Arrangement',
    }
    CHOICES = constants.COMPANY_STATUSES

    def _parse(self, val):
        status_key = self.SUBSTITUTES.get(val, val)

        try:
            status = self.CHOICES.displays[status_key].value
        except KeyError:
            print(
                "Warning COMPANY_STATUS '{}' not found, using the default '{}' instead".format(
                    status_key, self.CHOICES.ACTIVE
                )
            )
            status = self.CHOICES.ACTIVE
        return status
company_status_parser = CompanyStatusParser()


class PropertyParser(Parser):
    def __init__(self, prop, parser=simple_parser):
        self.prop = prop
        self.parser = parser

    def parse(self, row):
        val = self.parser.parse(row)
        if not val:
            return {}
        return {
            self.prop: val
        }


class DictParser(Parser):
    def __init__(self, property_parsers):
        self.parsers = property_parsers

    def parse(self, row):
        data = {}
        for parser in self.parsers:
            val = parser.parse(row)
            if val:
                data.update(val)
        return data


class ListParser(Parser):
    def __init__(self, parser, number):
        self.parser = parser
        self.number = number

    def parse(self, row):
        data = []
        for index in range(self.number):
            val = self.parser.parse(row)
            if val:
                data.append(val)
        return data


class CSVImporter(DictParser):
    """
    Used to import a CSV row (representing a company) from the Companies House dataset.

    e.g.
        importer = CSVImporter()
        data = importer.parse(iter(row))
    """
    PARSERS = [
        PropertyParser('company_name'),
        PropertyParser('company_number'),
        PropertyParser(
            'registered_office_address',
            DictParser([
                PropertyParser('care_of'),
                PropertyParser('po_box'),
                PropertyParser('address_line_1'),
                PropertyParser('address_line_2'),
                PropertyParser('locality'),
                PropertyParser('region'),
                PropertyParser('country'),
                PropertyParser('postal_code'),
            ])
        ),
        PropertyParser('type', company_type_parser),
        PropertyParser('company_status', company_status_parser),
        PropertyParser('country_of_origin'),
        PropertyParser('date_of_dissolution', date_parser),
        PropertyParser('date_of_creation', date_parser),
        PropertyParser(
            'accounts',
            DictParser([
                PropertyParser(
                    'accounting_reference_date',
                    DictParser([
                        PropertyParser('day', int_parser),
                        PropertyParser('month', int_parser),
                    ])
                ),
                PropertyParser('next_due', date_parser),
                PropertyParser('next_made_up_to', date_parser),
                PropertyParser('category'),
            ])
        ),
        PropertyParser(
            'annual_return',
            DictParser([
                PropertyParser('next_due', date_parser),
                PropertyParser('last_made_up_to', date_parser),
            ])
        ),
        PropertyParser(
            'mortgages',
            DictParser([
                PropertyParser('num_made_up_to', int_parser),
                PropertyParser('num_outstanding', int_parser),
                PropertyParser('num_part_satisfied', int_parser),
                PropertyParser('num_satisfied', int_parser),
            ])
        ),
        PropertyParser(
            'sic_codes',
            ListParser(siccode_parser, 4)
        ),
        PropertyParser(
            'limited_partnerships',
            DictParser([
                PropertyParser('num_gen_partners', int_parser),
                PropertyParser('num_lim_partners', int_parser),
            ])
        ),
        PropertyParser('URI'),
        PropertyParser(
            'previous_names',
            ListParser(
                DictParser([
                    PropertyParser('date', date_parser),
                    PropertyParser('company_name'),
                ]),
                10
            )
        )
    ]

    def __init__(self):
        super(CSVImporter, self).__init__(self.PARSERS)
