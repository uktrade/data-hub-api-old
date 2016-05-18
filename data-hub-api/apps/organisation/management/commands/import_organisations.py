import functools
import datetime
from multiprocessing import Pool

from django.db import connection
from django.core.management.base import BaseCommand, CommandError

from cdms_api.connection import api

from organisation.models import Organisation

TOP = 50
CEIL_PAGE = 1000


def build_obj(cdms_data):
    obj = Organisation()
    Organisation.cdms_migrator.update_local_from_cdms_data(obj, cdms_data)
    obj.cdms_pk = cdms_data['AccountId']
    return obj


def import_organisations(page, from_datetime=None):
    print('importing page: {}'.format(page))
    try:
        list_kwargs = {
            'skip': (TOP * page),
            'order_by': 'CreatedOn asc'
        }
        if from_datetime:
            list_kwargs['filters'] = "CreatedOn gt datetime'{}'".format(from_datetime)

        results = api.list(
            'Account',
            **list_kwargs
        )

        objs = [build_obj(result) for result in results]
        Organisation.objects.skip_cdms().bulk_create(objs)
        print('********** Page {}, imported {}'.format(page, len(objs)))
    except Exception as e:
        print('********** Page {}, ERROR: '.format(page), e)


class Command(BaseCommand):
    help = 'Import organisations from CDMS'

    def add_arguments(self, parser):
        parser.add_argument('from_page', type=int, help='From page (>=0)')
        parser.add_argument('to_page', type=int, help='To page')

        # Named (optional) arguments
        parser.add_argument(
            '--no-multithreading',
            dest='no_multithreading',
            default=False,
            help='Execute the script not in parallel.'
        )

        parser.add_argument(
            '--from-datetime',
            dest='from_datetime',
            default=None,
            help=(
                'Limits the cdms query to speed things up. If specified, '
                'it will import only records created after that date. '
                '(e.g. 2008-12-23T14:54:13)'
            )
        )

    def _get_suggested_from_datetime(self):
        sql = "select created_on from organisation_organisation order by created_on desc LIMIT 1"
        cursor = connection.cursor()

        # totals
        cursor.execute(sql)
        suggested_from_datetime = cursor.fetchone()
        if not suggested_from_datetime:
            return None
        suggested_from_datetime = suggested_from_datetime[0]
        suggested_from_datetime -= datetime.timedelta(hours=1)  # TODO fix problem with timezones
        return suggested_from_datetime.strftime("%Y-%m-%dT%H:%M:%S")

    def check_arguments(self, **options):
        from_page = options['from_page']
        to_page = options['to_page']

        no_multithreading = options['no_multithreading']
        from_datetime = options['from_datetime']

        if to_page < from_page:
            raise CommandError('from_page should be <= to_page')

        if from_page >= CEIL_PAGE or to_page > CEIL_PAGE:
            suggested_from_datetime = self._get_suggested_from_datetime()
            if suggested_from_datetime:
                error_msg = (
                    'When using pages > {}, the cdms query can become really slow and return errors. '
                    'We suggest you should run the following command instead: '
                    '\n\t./manage.py import_organisations 0 <to-page> --from-datetime={}'
                ).format(CEIL_PAGE, suggested_from_datetime)
            else:
                error_msg = (
                    'When using pages > {}, the cdms query can become really slow and return errors. '
                    'We suggest you should run the command instead with to-page <= {}'
                ).format(CEIL_PAGE, CEIL_PAGE)
            raise CommandError(error_msg)

        return from_page, to_page, no_multithreading, from_datetime

    def handle(self, *args, **options):
        from_page, to_page, no_multithreading, from_datetime = self.check_arguments(**options)

        if no_multithreading:
            for page in range(from_page, to_page + 1):
                import_organisations(page, from_datetime=from_datetime)
        else:
            p = Pool(processes=6, maxtasksperchild=4)
            p.map(
                functools.partial(import_organisations, from_datetime=from_datetime),
                range(from_page, to_page + 1)
            )
