from django.db import connection
from django.core.management.base import BaseCommand

from organisation.constants import BUSINESS_TYPE_CHOICES


def perc(num, tot):
    return round((num / tot) * 100, 2)


def get_business_type(guid):
    return dict(BUSINESS_TYPE_CHOICES).get(guid, 'None')


class Command(BaseCommand):
    help = 'Returns a summary of some analysis on organisations'

    def handle(self, *args, **options):
        cursor = connection.cursor()

        not_duplicate_where = "master_cdms_pk is null and not (name ILIKE '%duplicate%') and not (name ILIKE '%not use%')"  # noqa

        # totals
        cursor.execute("SELECT count(*) from organisation_organisation")
        tot_organisations_with_duplicates = cursor.fetchone()[0]

        # duplicates
        cursor.execute("SELECT count(*) from organisation_organisation where master_cdms_pk is not null or name ILIKE '%duplicate%' or name ILIKE '%not use%'")  # noqa
        marked_duplicates = cursor.fetchone()[0]

        tot_organisations = tot_organisations_with_duplicates - marked_duplicates

        # uk / non-uk
        cursor.execute("SELECT uk_organisation, count(*) from organisation_organisation where {} group by uk_organisation".format(not_duplicate_where))  # noqa
        uk_non_uk = cursor.fetchall()
        tot_uk_orgs = [data[1] for data in uk_non_uk if data[0]][0]
        tot_non_uk_orgs = [data[1] for data in uk_non_uk if not data[0]][0]

        # per year
        cursor.execute("SELECT EXTRACT(YEAR FROM created_on) as created_on_year, count(*) from organisation_organisation where {} group by created_on_year order by created_on_year".format(not_duplicate_where))  # noqa
        orgs_per_year = cursor.fetchall()

        # companies house
        cursor.execute("SELECT count(*) from organisation_organisation where {} and companies_house_number != ''".format(not_duplicate_where))  # noqa
        orgs_with_CH = cursor.fetchone()[0]

        # company type
        cursor.execute("SELECT business_type, count(*) from organisation_organisation where {} group by business_type".format(not_duplicate_where))  # noqa
        orgs_per_business_types = cursor.fetchall()

        print(self.style.SUCCESS('\n********** ANALYSIS: RESULTS **********'))
        print('Total orgs (including duplicates): ', tot_organisations_with_duplicates)
        print(
            'Total records marked as duplicates: {} - {}%'.format(
                marked_duplicates, perc(marked_duplicates, tot_organisations_with_duplicates)
            )
        )
        print(self.style.SUCCESS('\n********** ANALYSIS: RESULTS IGNORING DUPLICATES **********'))
        print('Total orgs: ', tot_organisations)
        print('UK orgs: {} - {}%'.format(tot_uk_orgs, perc(tot_uk_orgs, tot_organisations)))
        print('Non-UK orgs: {} - {}%'.format(tot_non_uk_orgs, perc(tot_non_uk_orgs, tot_organisations)))
        print('Orgs created per year: \n', '\n'.join(['\t{}: {}'.format(int(org[0]), org[1]) for org in orgs_per_year]))  # noqa
        print('Orgs with CH: ', orgs_with_CH)
        print('Orgs grouped by business type: \n', '\n'.join([
            '\t{}: {} - {}%'.format(
                get_business_type(org[0]),
                org[1],
                perc(org[1], tot_organisations)
            )
            for org in orgs_per_business_types
        ]))

        print(self.style.SUCCESS('\n********** ANALYSIS: UK BUSINESSES **********'))

        cursor.execute("SELECT count(*) from organisation_organisation where {} and uk_organisation is True".format(not_duplicate_where))  # noqa
        tot_uk_orgs = cursor.fetchone()[0]

        cursor.execute("SELECT count(*) from organisation_organisation where {} and uk_organisation is True and (business_type in ('98d14e94-5d95-e211-a939-e4115bead28a', '9ad14e94-5d95-e211-a939-e4115bead28a') or business_type is Null)".format(not_duplicate_where))  # noqa
        tot_uk_companies = cursor.fetchone()[0]

        cursor.execute("SELECT count(*) from organisation_organisation where {} and uk_organisation is True and (business_type in ('98d14e94-5d95-e211-a939-e4115bead28a', '9ad14e94-5d95-e211-a939-e4115bead28a') or business_type is Null) and companies_house_number = ''".format(not_duplicate_where))  # noqa
        tot_non_matched_uk_companies = cursor.fetchone()[0]

        print('Total orgs: {}'.format(tot_uk_orgs))
        print('Total companies (ltd, lp): {}'.format(tot_uk_companies))
        print('Total non-matched companies (ltd, lp): {}'.format(tot_non_matched_uk_companies))
