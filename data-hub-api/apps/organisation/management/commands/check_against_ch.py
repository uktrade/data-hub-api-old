import time
import random
import requests
from collections import defaultdict, namedtuple

from django.db.models import Q
from django.core.management.base import BaseCommand
from django.conf import settings

from organisation.models import Organisation


def perc(num, tot):
    return round((num / tot) * 100, 2)


def clean_postcode(postcode):
    if not postcode:
        return postcode
    return postcode.lower().replace(' ', '').strip()


def clean_name(name):
    EXCLUDE_WORDS = ['ltd', 'limited', 'inc', 'llc', '.', 'the']
    cleaned_name = name.lower()
    for word in EXCLUDE_WORDS:
        cleaned_name = cleaned_name.replace(word, '')
    return cleaned_name.strip()


class AccuracyCalc(object):
    def __init__(self):
        self.sub_accuracy = 0

    def analyse_names(self, name1, name2):
        cleaned_name1 = clean_name(name1)
        cleaned_name2 = clean_name(name2)

        if cleaned_name1 == cleaned_name2:
            self.sub_accuracy += 1
        else:
            self.sub_accuracy += 0.5

    def analyse_postcodes(self, postcode1, postcode2):
        cleaned_postcode1 = clean_postcode(postcode1) or ''
        cleaned_postcode2 = clean_postcode(postcode2) or ''

        if cleaned_postcode1 == cleaned_postcode2:
            self.sub_accuracy += 1
        elif cleaned_postcode1 and cleaned_postcode1[:3] == cleaned_postcode2[:3]:
            self.sub_accuracy += 0.5

    def get_accuracy(self):
        return self.sub_accuracy / 2


FindingResult = namedtuple('FindingResult', ['name', 'postcode', 'accuracy', 'company_number'])


class BaseSource(object):
    NAME = 'Base'

    def __init__(self, name, postcode):
        super(BaseSource, self).__init__()
        self.name = name
        self.postcode = postcode
        self.findings = None

    def choose_best_finding(self):
        assert self.findings != None  # noqa

        finding = None
        if len(self.findings) >= 1:
            finding = max(self.findings, key=lambda x: x.accuracy)

        return finding

    def _get_ch_address(self, ch_data):
        for prop in ['address', 'registered_office_address']:
            if prop in ch_data:
                return ch_data.get(prop, {}).get('postal_code')
        return None

    def _build_findings(self):
        pass

    def find(self):
        self._build_findings()
        return self.choose_best_finding()


class CHSource(BaseSource):
    NAME = 'CH'

    CH_SEARCH_URL = 'https://api.companieshouse.gov.uk/search/companies?q={}'

    def get_accuracy(self, ch_name, ch_postcode):
        accuracy_calc = AccuracyCalc()
        accuracy_calc.analyse_names(self.name, ch_name)
        accuracy_calc.analyse_postcodes(self.postcode, ch_postcode)
        return accuracy_calc.get_accuracy()

    def _build_findings(self):
        url = self.CH_SEARCH_URL.format(self.name)
        results = requests.get(url, auth=(settings.CH_KEY, '')).json()['items']

        self.findings = []
        for result in results:
            ch_name = result['title']
            ch_postcode = self._get_ch_address(result)
            company_number = result['company_number']
            accuracy = self.get_accuracy(ch_name, ch_postcode)

            self.findings.append(
                FindingResult(
                    name=ch_name, postcode=ch_postcode,
                    accuracy=accuracy, company_number=company_number
                )
            )

        time.sleep(0.5)


class DueDilSource(BaseSource):
    NAME = 'DueDil'

    DUEL_SEARCH_URL = 'http://api.duedil.com/open/search?q={}&api_key={}'
    CH_COMPANY_URL = 'https://api.companieshouse.gov.uk/company/{}'

    def get_accuracy(self, dd_name, ch_postcode):
        accuracy_calc = AccuracyCalc()
        accuracy_calc.analyse_names(self.name, dd_name)
        accuracy_calc.analyse_postcodes(self.postcode, ch_postcode)
        return accuracy_calc.get_accuracy()

    def get_ch_postcode(self, company_number):
        url = self.CH_COMPANY_URL.format(company_number)
        response = requests.get(url, auth=(settings.CH_KEY, ''))
        time.sleep(0.5)
        if not response.ok:
            return None
        result = response.json()
        return self._get_ch_address(result)

    def _build_findings(self):
        self.findings = []

        url = self.DUEL_SEARCH_URL.format(self.name, settings.DUEDIL_KEY)
        response = requests.get(url)
        if not response.ok:
            return

        results = response.json()['response']['data']

        for result in results:
            dd_name = result['name']
            company_number = result['company_number']
            ch_postcode = self.get_ch_postcode(company_number)
            accuracy = self.get_accuracy(dd_name, ch_postcode)

            self.findings.append(
                FindingResult(
                    name=dd_name, postcode=ch_postcode,
                    accuracy=accuracy, company_number=company_number
                )
            )


class Command(BaseCommand):
    help = 'Check matches against Companies House'

    def add_arguments(self, parser):
        parser.add_argument('sample_size', type=int, help='Size of the sample')

    def company_number_finder(self, cdms_org):
        finding = None
        print(self.style.NOTICE('{} - {}'.format(cdms_org.name, cdms_org.postcode)))

        for SourceKlass in [CHSource, DueDilSource]:
            source = SourceKlass(cdms_org.name, cdms_org.postcode)
            finding = source.find()
            print('\t {} (found {}): {}'.format(
                SourceKlass.NAME, len(source.findings),
                'None' if not finding else '{} {} {}'.format(finding.name, finding.postcode, finding.accuracy)
            ))
            if len(source.findings) > 1:
                for r in source.findings:
                    print('\t\t{} {} {}'.format(r.name, r.postcode, r.accuracy))

            if finding and finding.accuracy >= 0.5:
                break

        return finding

    def handle(self, *args, **options):
        orgs = Organisation.objects.skip_cdms().filter(
            uk_organisation=True, companies_house_number='',
            verified_companies_house_number='',
            master_cdms_pk__isnull=True
        ).filter(
            Q(business_type='98d14e94-5d95-e211-a939-e4115bead28a') | Q(business_type__isnull=True),
        ).exclude(
            Q(name__icontains='duplicate') | Q(name__icontains='not use')
        )
        tot_orgs = orgs.count()

        tot_items = options['sample_size']
        stats = defaultdict(int)
        for index in range(0, tot_items):
            org = orgs[random.randint(0, len(orgs))]

            finding = self.company_number_finder(org)

            if finding:
                stats[finding.accuracy] += 1
            else:
                stats[-1] += 1

        self.stdout.write(self.style.SUCCESS('\n********** ANALYSIS: RESULTS **********'))
        print(
            'Tot number: {}\n'.format(tot_orgs),
            'Matching with sources (tot sample: {}): \n'.format(tot_items),
            '\n'.join(
                ['\t{}: {}%'.format(accuracy, perc(count, tot_items)) for accuracy, count in stats.items()]
            )
        )
