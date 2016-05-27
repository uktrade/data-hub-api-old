import csv
import os
import glob
from multiprocessing import Pool

from django.core.management.base import BaseCommand, CommandError

from companieshouse.importers import CSVImporter
from companieshouse.models import Company


def import_csv(path):
    importer = CSVImporter()
    with open(path, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # headers

        for row in reader:
            if not row:
                continue

            try:
                raw_row = list(row)
                data = importer.parse(iter(row))
                Company.objects.update_from_CH_data(data)
            except Exception as e:
                print(
                    "Skipping. Row {} triggered the following error {}".format(
                        raw_row, e
                    )
                )


class Command(BaseCommand):
    """
    This could be optimised quite a lot by generating sha1 hashes of the csv row, saving them in the db and
    checking the two hashes during the next import. If they are the same, skip the line.
    """
    help = 'Imports csv files of companies house data by creating/updating db records'

    def add_arguments(self, parser):
        parser.add_argument(
            'folder', type=str,
            help=(
                'Path to directory containing csv files. '
                'Download them here: http://download.companieshouse.gov.uk/en_output.html'
            )
        )

    def _get_filepaths(self, folder):
        os.chdir(folder)
        paths = [os.path.join(folder, path) for path in glob.glob("*.csv")]

        if not paths:
            raise CommandError('Folder {} does not contain any csv files'.format(folder))
        return paths

    def handle(self, *args, **options):
        paths = self._get_filepaths(options['folder'])

        p = Pool(maxtasksperchild=4)
        p.map(import_csv, paths)
