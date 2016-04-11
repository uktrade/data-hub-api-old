import datetime

from django.utils import timezone

from reversion import revisions as reversion
from reversion.models import Revision, Version

from cdms_api.tests.utils import mocked_cdms_create

from migrator.tests.models import SimpleObj
from migrator.tests.base import BaseMockedCDMSApiTestCase


class CreateWithSaveTestCase(BaseMockedCDMSApiTestCase):
    def test_success(self):
        """
        obj.save() should create a new obj in local and cdms if it doesn't exist.
        The operation should create a revision with the change as well.
        """
        modified_on = (timezone.now() - datetime.timedelta(days=1)).replace(microsecond=0)
        cdms_id = 'brand new id'
        self.mocked_cdms_api.create.side_effect = mocked_cdms_create(
            create_data={
                'SimpleId': cdms_id,
                'ModifiedOn': modified_on
            }
        )

        self.assertNoRevisions()

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

        # check versions
        self.assertEqual(Version.objects.count(), 1)
        self.assertEqual(Revision.objects.count(), 1)

        version_list = reversion.get_for_object(obj)
        self.assertEqual(len(version_list), 1)
        version = version_list[0]
        self.assertIsNotCDMSRefreshRevision(version.revision)
        version_data = version.field_dict
        self.assertEqual(version_data['cdms_pk'], obj.cdms_pk)
        self.assertEqual(version_data['modified'], obj.modified)
        self.assertEqual(version_data['created'], obj.created)

    def test_exception_triggers_rollback(self):
        """
        In case of exceptions during cdms calls, no changes should be reflected in the db and no revisions
        should be created.
        """
        self.mocked_cdms_api.create.side_effect = Exception

        obj = SimpleObj()
        obj.name = 'simple obj'

        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)
        self.assertRaises(Exception, obj.save)
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)

        self.assertAPINotCalled(['list', 'update', 'delete', 'get'])
        self.assertNoRevisions()


class CreateWithManagerTestCase(BaseMockedCDMSApiTestCase):
    def test_success(self):
        """
        MyObject.objects.create() should create a new obj in local and cdms.
        The operation should create a revision with the change as well.
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

        # check versions
        self.assertEqual(Version.objects.count(), 1)
        self.assertEqual(Revision.objects.count(), 1)

        version_list = reversion.get_for_object(obj)
        self.assertEqual(len(version_list), 1)
        version = version_list[0]
        self.assertIsNotCDMSRefreshRevision(version.revision)
        version_data = version.field_dict
        self.assertEqual(version_data['cdms_pk'], obj.cdms_pk)
        self.assertEqual(version_data['modified'], obj.modified)
        self.assertEqual(version_data['created'], obj.created)

    def test_exception_triggers_rollback(self):
        """
        In case of exceptions during cdms calls, no changes should be reflected in the db and no revisions
        should be created.
        """
        self.mocked_cdms_api.create.side_effect = Exception

        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)
        self.assertRaises(
            Exception,
            SimpleObj.objects.create, name='simple obj'
        )
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)

        self.assertAPINotCalled(['list', 'update', 'delete', 'get'])
        self.assertNoRevisions()

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
        self.assertNoRevisions()

    def test_with_bulk_create_private(self):
        """
        bulk_create() using the private django method.
        """
        self.assertRaises(
            NotImplementedError,
            SimpleObj.objects._insert,
            [
                SimpleObj(id=1000, name='simple obj1'),
                SimpleObj(id=1001, name='simple obj2')
            ], SimpleObj._meta.fields
        )


class CreateWithSaveSkipCDMSTestCase(BaseMockedCDMSApiTestCase):
    def test_success(self):
        """
        When calling obj.save(skip_cdms=True), changes should only happen in local, not in cdms.
        The operation should create a revision with the change as usual.
        """
        obj = SimpleObj()
        obj.name = 'simple obj'

        self.assertEqual(obj.cdms_pk, '')
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)
        obj.save(skip_cdms=True)
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 1)
        self.assertEqual(obj.cdms_pk, '')

        self.assertNoAPICalled()

        # check versions
        self.assertEqual(Version.objects.count(), 1)
        self.assertEqual(Revision.objects.count(), 1)


class CreateWithManagerSkipCDMSTestCase(BaseMockedCDMSApiTestCase):
    def test_with_create(self):
        """
        When calling MyObject.objects.skip_cdms().create(), changes should only happen in local, not in cdms.
        The operation should create a revision with the change as usual.
        """
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)
        obj = SimpleObj.objects.skip_cdms().create(name='simple obj')
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 1)
        self.assertEqual(obj.cdms_pk, '')

        self.assertNoAPICalled()

        # check versions
        self.assertEqual(Version.objects.count(), 1)
        self.assertEqual(Revision.objects.count(), 1)

    def test_with_bulk_create(self):
        """
        When calling MyObject.objects.skip_cdms().bulk_create(obj1, obj2), changes should only happen in local,
        not in cdms.
        The operation does NOT create any revisions as bulk_create is a low level call intended to skip all
        custom and non custom logic and hit the db directly.
        """
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)
        SimpleObj.objects.skip_cdms().bulk_create([
            SimpleObj(name='simple obj1'),
            SimpleObj(name='simple obj2')
        ])

        self.assertNoAPICalled()
        self.assertNoRevisions()  # no revisions as this is a low level call without signals

    def test_create_without_objects(self):
        self.assertEqual(
            SimpleObj.objects.skip_cdms()._batched_insert([], None, None),
            None
        )
