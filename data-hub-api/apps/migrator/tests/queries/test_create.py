import datetime

from django.utils import timezone

from cdms_api.tests.utils import mocked_cdms_create

from migrator.tests.queries.models import SimpleObj
from migrator.tests.queries.base import BaseMockedCDMSApiTestCase


class CreateWithSaveTestCase(BaseMockedCDMSApiTestCase):
    def test_success(self):
        """
        obj.save() should create a new obj in local and cdms if it doesn't exist.
        """
        modified_on = (timezone.now() - datetime.timedelta(days=1)).replace(microsecond=0)
        cdms_id = 'brand new id'
        self.mocked_cdms_api.create.side_effect = mocked_cdms_create(
            create_data={
                'SimpleId': cdms_id,
                'ModifiedOn': modified_on
            }
        )

        obj = SimpleObj()
        obj.name = 'simple obj'
        obj.dt_field = datetime.datetime(2016, 1, 1).replace(tzinfo=datetime.timezone.utc)
        obj.int_field = 10

        self.assertEqual(obj.cdms_pk, '')
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)
        obj.save()
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 1)
        self.assertEqual(obj.cdms_pk, cdms_id)
        self.assertEqual(obj.modified, modified_on)

        self.assertAPICreateCalled(
            SimpleObj, kwargs={
                'data': {
                    'Name': 'simple obj',
                    'DateTimeField': '/Date(1451606400000)/',
                    'IntField': 10,
                    'FKField': None
                }
            }
        )
        self.assertAPINotCalled(['list', 'update', 'delete', 'get'])

        # reload obj and check cdms_pk and modified
        obj = SimpleObj.objects.skip_cdms().get(pk=obj.pk)
        self.assertEqual(obj.cdms_pk, cdms_id)
        self.assertEqual(obj.modified, modified_on)

    def test_exception_triggers_rollback(self):
        """
        In case of exceptions during cdms calls, no changes should be reflected in the db.
        """
        self.mocked_cdms_api.create.side_effect = Exception

        obj = SimpleObj()
        obj.name = 'simple obj'

        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)
        self.assertRaises(Exception, obj.save)
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)

        self.assertAPINotCalled(['list', 'update', 'delete', 'get'])


class CreateWithManagerTestCase(BaseMockedCDMSApiTestCase):
    def test_success(self):
        """
        MyObject.objects.create() should create a new obj in local and cdms.
        """
        modified_on = (timezone.now() - datetime.timedelta(days=1)).replace(microsecond=0)
        cdms_id = 'brand new id'

        self.mocked_cdms_api.create.side_effect = mocked_cdms_create(
            create_data={
                'SimpleId': cdms_id,
                'ModifiedOn': modified_on
            }
        )

        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)
        obj = SimpleObj.objects.create(name='simple obj')
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 1)
        self.assertEqual(obj.cdms_pk, cdms_id)
        self.assertEqual(obj.modified, modified_on)

        self.assertAPICreateCalled(
            SimpleObj, kwargs={
                'data': {
                    'Name': 'simple obj',
                    'DateTimeField': None,
                    'IntField': None,
                    'FKField': None
                }
            }
        )
        self.assertAPINotCalled(['list', 'update', 'delete', 'get'])

        # reload obj and check cdms_pk and modified
        obj = SimpleObj.objects.skip_cdms().get(pk=obj.pk)
        self.assertEqual(obj.cdms_pk, cdms_id)
        self.assertEqual(obj.modified, modified_on)

    def test_exception_triggers_rollback(self):
        """
        In case of exceptions during cdms calls, no changes should be reflected in the db.
        """
        self.mocked_cdms_api.create.side_effect = Exception

        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)
        self.assertRaises(
            Exception,
            SimpleObj.objects.create, name='simple obj'
        )
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)

        self.assertAPINotCalled(['list', 'update', 'delete', 'get'])

    def test_with_bulk_create(self):
        """
        bulk_create() not currently implemented.
        """
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)
        self.assertRaises(
            NotImplementedError,
            SimpleObj.objects.bulk_create,
            [
                SimpleObj(name='simple obj1'),
                SimpleObj(name='simple obj2')
            ]
        )
        self.assertNoAPICalled()


class CreateWithSaveSkipCDMSTestCase(BaseMockedCDMSApiTestCase):
    def test_success(self):
        """
        When calling obj.save(skip_cdms=True), changes should only happen in local, not in cdms.
        """
        obj = SimpleObj()
        obj.name = 'simple obj'

        self.assertEqual(obj.cdms_pk, '')
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)
        obj.save(skip_cdms=True)
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 1)
        self.assertEqual(obj.cdms_pk, '')

        self.assertNoAPICalled()


class CreateWithManagerSkipCDMSTestCase(BaseMockedCDMSApiTestCase):
    def test_with_create(self):
        """
        When calling MyObject.objects.skip_cdms().create(), changes should only happen in local, not in cdms.
        """
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)
        obj = SimpleObj.objects.skip_cdms().create(name='simple obj')
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 1)
        self.assertEqual(obj.cdms_pk, '')

        self.assertNoAPICalled()

    def test_with_bulk_create(self):
        """
        When calling MyObject.objects.skip_cdms().bulk_create(obj1, obj2), changes should only happen in local,
        not in cdms.
        """
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)
        SimpleObj.objects.skip_cdms().bulk_create([
            SimpleObj(name='simple obj1'),
            SimpleObj(name='simple obj2')
        ])

        self.assertNoAPICalled()
