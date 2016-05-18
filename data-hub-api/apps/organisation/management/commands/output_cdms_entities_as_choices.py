from django.core.management.base import BaseCommand

from cdms_api.connection import api


class Command(BaseCommand):
    help = 'Prints list of entities as Django choices'

    def add_arguments(self, parser):
        parser.add_argument('entity', type=str, help='CDMS Entity e.g. Account (without the postfix Set)')
        parser.add_argument(
            '--name_property',
            dest='name_prop',
            default='optevia_name',
            help='Name of prop to output (together with the id). Defaults to optevia_name'
        )

    def handle(self, *args, **options):
        entity = options['entity']
        id_prop = '{}Id'.format(entity)

        total_results = []
        page = 0
        top = 50
        while True:
            results = api.list(entity, top=top, skip=(top * page))
            results = [
                "    ('{}', '{}'),".format(result[id_prop], result[options['name_prop']])
                for result in results
            ]
            total_results += results
            if not results or len(results) < top:
                break
            page += 1

        print('(\n{}\n)'.format('\n'.join(total_results)))
