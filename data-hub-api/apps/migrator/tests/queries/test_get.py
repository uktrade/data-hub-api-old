import datetime

from django.utils import timezone
from django.core.exceptions import MultipleObjectsReturned

from cdms_api.exceptions import CDMSNotFoundException

from migrator.tests.queries.models import SimpleObj
from migrator.tests.queries.base import BaseMockedCDMSApiTestCase
from migrator.exceptions import ObjectsNotInSyncException

from cdms_api.tests.utils import mocked_cdms_get


class BaseGetTestCase(BaseMockedCDMSApiTestCase):
    def setUp(self):
        super(BaseGetTestCase, self).setUp()
        self.obj = SimpleObj.objects.skip_cdms().create(
            cdms_pk='cdms-pk', name='name'
        )


class GetByIdTestCase(BaseGetTestCase):
    def test_local_exists(self):
        """
        MyObject.objects.get(pk=..) should hit the cdms api and return the local obj.
        """
        obj = SimpleObj.objects.get(pk=self.obj.pk)
        self.assertEqual(obj.pk, self.obj.pk)

        self.assertAPIGetCalled(
            SimpleObj, kwargs={'guid': self.obj.cdms_pk}
        )
        self.assertAPINotCalled(['list', 'update', 'delete', 'create'])

    def test_local_doesnt_exist(self):
        """
        MyObject.objects.get(pk=..) should raise DoesNotExist and not hit the db if the local obj doesn't exist
        """
        self.assertRaises(
            SimpleObj.DoesNotExist,
            SimpleObj.objects.get,
            pk=0
        )

        self.assertNoAPICalled()


class GetByCmdPKTestCase(BaseGetTestCase):
    def test_local_exists(self):
        """
        MyObject.objects.get(cdms_pk=..) when local obj exists,
        should hit the cdms api and return the local obj.
        """
        obj = SimpleObj.objects.get(cdms_pk=self.obj.cdms_pk)
        self.assertEqual(obj.pk, self.obj.pk)

        self.assertAPIGetCalled(
            SimpleObj, kwargs={'guid': self.obj.cdms_pk}
        )
        self.assertAPINotCalled(['list', 'update', 'delete', 'create'])

    def test_local_doesnt_exist(self):
        """
        MyObject.objects.get(cdms_pk=..) when local obj does not exist,
        should hit the cdms api, create a local obj and return it.
        """
        modified_on = (timezone.now() + datetime.timedelta(days=1)).replace(microsecond=0)
        self.mocked_cdms_api.get.side_effect = mocked_cdms_get(
            get_data={
                'ModifiedOn': modified_on,
                'Name': 'new name',
                'DateTimeField': None,
                'IntField': None,
                'FKField': None
            }
        )

        SimpleObj.objects.skip_cdms().all().delete()
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)

        obj = SimpleObj.objects.get(cdms_pk='cdms-pk')
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 1)
        self.assertEqual(obj.cdms_pk, 'cdms-pk')
        self.assertEqual(obj.name, 'new name')
        self.assertEqual(obj.modified, modified_on)

        self.assertAPIGetCalled(
            SimpleObj, kwargs={'guid': 'cdms-pk'}
        )
        self.assertAPINotCalled(['list', 'update', 'delete', 'create'])

        # reload obj and check
        obj = SimpleObj.objects.skip_cdms().get(pk=obj.pk)
        self.assertEqual(obj.cdms_pk, 'cdms-pk')
        self.assertEqual(obj.name, 'new name')
        self.assertEqual(obj.modified, modified_on)

    def test_neither_local_nor_cdms_obj_exists(self):
        """
        MyObject.objects.get(cdms_pk=..) when neither local nor cdms obj exists
        should raise MyObject.DoesNotExist.
        """
        self.mocked_cdms_api.get.side_effect = CDMSNotFoundException('not found')

        SimpleObj.objects.skip_cdms().all().delete()
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)

        self.assertRaises(
            SimpleObj.DoesNotExist,
            SimpleObj.objects.get, cdms_pk='cdms-pk'
        )
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)

        self.assertAPIGetCalled(
            SimpleObj, kwargs={'guid': 'cdms-pk'}
        )
        self.assertAPINotCalled(['list', 'update', 'delete', 'create'])


class GetByOtherFieldsTestCase(BaseGetTestCase):
    def test(self):
        """
        MyObject.objects.get(other_field=..) should work as with pk or id.
        """
        obj = SimpleObj.objects.get(name='name')
        self.assertEqual(obj.pk, self.obj.pk)

        self.assertAPIGetCalled(
            SimpleObj, kwargs={'guid': self.obj.cdms_pk}
        )
        self.assertAPINotCalled(['list', 'update', 'delete', 'create'])

    def test_multiple_objects_returned(self):
        SimpleObj.objects.skip_cdms().create(cdms_pk='cdms-pk1', name='name')
        SimpleObj.objects.skip_cdms().create(cdms_pk='cdms-pk2', name='name')

        self.assertRaises(
            MultipleObjectsReturned,
            SimpleObj.objects.get,
            name='name'
        )

        self.assertNoAPICalled()


class SyncGetTestCase(BaseGetTestCase):
    def test_with_objs_in_sync(self):
        """
        If the cdms obj and local obj are in sync:
            - get obj from local db
            - get cdms_obj from cdms
            - no local changes happen
        """
        self.mocked_cdms_api.get.side_effect = mocked_cdms_get(
            get_data={
                'ModifiedOn': self.obj.modified
            }
        )

        obj = SimpleObj.objects.get(pk=self.obj.pk)
        self.assertEqual(obj.modified, self.obj.modified)

        self.assertAPIGetCalled(
            SimpleObj, kwargs={'guid': self.obj.cdms_pk}
        )

        self.assertAPINotCalled(['list', 'update', 'delete', 'create'])

    def test_with_local_more_up_to_date(self):
        """
        If the local obj is more up to date, it means that the last syncronisation didn't
        work as it should have, so we raise ObjectsNotInSyncException.
        """
        modified_on = self.obj.modified - datetime.timedelta(seconds=0.001)

        self.mocked_cdms_api.get.side_effect = mocked_cdms_get(
            get_data={
                'ModifiedOn': modified_on
            }
        )

        self.assertRaises(
            ObjectsNotInSyncException, SimpleObj.objects.get, pk=self.obj.pk
        )

        self.assertAPIGetCalled(
            SimpleObj, kwargs={'guid': self.obj.cdms_pk}
        )

        self.assertAPINotCalled(['list', 'update', 'delete', 'create'])

    def test_with_cdms_more_up_to_date(self):
        """
        If the cdms obj includes more recent changes:
            - get obj from local db
            - get cdms_obj from cdms
            - update obj from cdms_obj
        """
        modified_on = self.obj.modified + datetime.timedelta(seconds=1)
        self.mocked_cdms_api.get.side_effect = mocked_cdms_get(
            get_data={
                'ModifiedOn': modified_on,
                'Name': 'new name',
                'DateTimeField': '/Date(1451606400000)/',
                'IntField': 10,
                'FKField': None
            }
        )

        obj = SimpleObj.objects.get(pk=self.obj.pk)
        self.assertEqual(obj.name, 'new name')
        self.assertEqual(obj.dt_field, datetime.datetime(2016, 1, 1).replace(tzinfo=datetime.timezone.utc))
        self.assertEqual(obj.int_field, 10)
        self.assertEqual(obj.modified, modified_on)
        self.assertEqual(obj.created, self.obj.created)

        self.assertAPIGetCalled(
            SimpleObj, kwargs={'guid': self.obj.cdms_pk}
        )

        self.assertAPINotCalled(['list', 'update', 'delete', 'create'])

        # reload obj and check
        obj = SimpleObj.objects.skip_cdms().get(pk=obj.pk)
        self.assertEqual(obj.cdms_pk, 'cdms-pk')
        self.assertEqual(obj.name, 'new name')
        self.assertEqual(obj.modified, modified_on)

    def test_cdms_exception_triggers_exception(self):
        """
        If an exception happens when accessing cdms, the exception is propagated.
        """
        self.mocked_cdms_api.get.side_effect = Exception

        self.assertRaises(
            Exception, SimpleObj.objects.get, pk=self.obj.pk
        )


class GetSkipCDMSTestCase(BaseGetTestCase):
    def test_get_by_any_fields(self):
        """
        Klass.objects.skip_cdms().get(...) should not hit cdms.
        """
        SimpleObj.objects.skip_cdms().get(pk=self.obj.pk)
        self.assertNoAPICalled()

        SimpleObj.objects.skip_cdms().get(cdms_pk=self.obj.cdms_pk)
        self.assertNoAPICalled()

    def test_object_not_found(self):
        """
        Klass.objects.skip_cdms().get(...) should raise DoesNotExist and not hit cdms.
        """
        self.assertRaises(
            SimpleObj.DoesNotExist,
            SimpleObj.objects.skip_cdms().get,
            cdms_pk='invalid'
        )
        self.assertNoAPICalled()
