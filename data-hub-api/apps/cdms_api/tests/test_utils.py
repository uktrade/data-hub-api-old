import datetime

from django.test.testcases import TestCase

from cdms_api.utils import cdms_datetime_to_datetime, datetime_to_cdms_datetime


class CdmsDatetimeToDatetimeTestCase(TestCase):
    def test_valid(self):
        dt = datetime.datetime(2016, 1, 1).replace(tzinfo=datetime.timezone.utc)

        self.assertEqual(
            cdms_datetime_to_datetime('/Date(1451606400000)/'),
            dt
        )

    def test_invalid(self):
        self.assertEqual(cdms_datetime_to_datetime('invalid'), None)

    def test_None(self):
        self.assertEqual(cdms_datetime_to_datetime(None), None)


class DatetimeToCdmsDatetimeTestCase(TestCase):
    def test_valid(self):
        dt = datetime.datetime(2016, 1, 1).replace(tzinfo=datetime.timezone.utc)

        self.assertEqual(
            datetime_to_cdms_datetime(dt),
            '/Date(1451606400000)/'
        )

    def test_None(self):
        self.assertEqual(datetime_to_cdms_datetime(None), None)
