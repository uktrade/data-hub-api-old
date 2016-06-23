import datetime

from django.utils import timezone

from reversion import revisions as reversion
from reversion.models import Revision, Version

from migrator.tests.models import SimpleObj
from migrator.tests.base import BaseMockedCDMSRestApiTestCase

from cdms_api.tests.rest.utils import mocked_cdms_list


class AllTestCase(BaseMockedCDMSRestApiTestCase):
    def test_all_with_some_local_objs(self):
        """
        Klass.objects.all() will:
            - hit cdms to get the objs
            - create or update local objs if necessary
            - return local objs

        In this case:
            - cdms-pk1 does not exist in local =>
                - local obj should get created
                - revisions created
            - cdms-pk2 is in sync with local obj =>
                - local obj should not change
                - no revisions should get created
            - cdms-pk3 is more up-to-date than local =>
                - local obj should get updated
                - revisions created
        """
        obj2 = SimpleObj.objects.skip_cdms().create(
            cdms_pk='cdms-pk2', name='name2', int_field=10
        )
        obj3 = SimpleObj.objects.skip_cdms().create(
            cdms_pk='cdms-pk3', name='name3', int_field=20
        )
        self.reset_revisions()

        mocked_list = [
            {
                'SimpleId': 'cdms-pk1',
                'Name': 'name1',
                'CreatedOn': (timezone.now() - datetime.timedelta(days=2)).replace(microsecond=0),
                'ModifiedOn': (timezone.now() - datetime.timedelta(days=1)).replace(microsecond=0),
                'DateTimeField': None,
                'IntField': None,
                'FKField': None
            },
            {
                'SimpleId': 'cdms-pk2',
                'Name': 'name2',
                'ModifiedOn': obj2.modified,
                'DateTimeField': None,
                'IntField': 20,
                'FKField': None
            },
            {
                'SimpleId': 'cdms-pk3',
                'Name': 'name3',
                'ModifiedOn': obj3.modified + datetime.timedelta(days=1),
                'DateTimeField': None,
                'IntField': 20,
                'FKField': None
            },
        ]
        self.mocked_cdms_api.list.side_effect = mocked_cdms_list(
            list_data=mocked_list
        )

        objs = SimpleObj.objects.all()
        self.assertEqual(len(objs), 3)
        objs_dict = {obj.cdms_pk: obj for obj in objs}

        # cdms-pk1
        obj1 = objs_dict['cdms-pk1']
        self.assertEqual(obj1.modified, mocked_list[0]['ModifiedOn'])
        self.assertEqual(obj1.created, mocked_list[0]['CreatedOn'])
        obj1 = SimpleObj.objects.skip_cdms().get(pk=obj1.pk)  # reload and double check
        self.assertEqual(obj1.modified, mocked_list[0]['ModifiedOn'])
        self.assertEqual(obj1.created, mocked_list[0]['CreatedOn'])

        # cdms-pk2
        obj2 = objs_dict['cdms-pk2']
        self.assertEqual(obj2.modified, mocked_list[1]['ModifiedOn'])
        self.assertEqual(obj2.int_field, 10)  # not 20 as records in sync
        obj2 = SimpleObj.objects.skip_cdms().get(pk=obj2.pk)  # reload and double check
        self.assertEqual(obj2.modified, mocked_list[1]['ModifiedOn'])
        self.assertEqual(obj2.int_field, 10)  # not 20 as records in sync

        # cdms-pk3
        obj3 = objs_dict['cdms-pk3']
        self.assertEqual(obj3.modified, mocked_list[2]['ModifiedOn'])
        self.assertEqual(obj3.int_field, 20)  # not 10 as record updated from cdms
        obj3 = SimpleObj.objects.skip_cdms().get(pk=obj3.pk)  # reload and double check
        self.assertEqual(obj3.modified, mocked_list[2]['ModifiedOn'])
        self.assertEqual(obj3.int_field, 20)  # not 10 as record updated from cdms

        self.assertAPINotCalled(['get', 'create', 'delete', 'update'])

        # check versions
        self.assertEqual(Version.objects.count(), 2)
        self.assertEqual(Revision.objects.count(), 2)

        # obj1
        version_list_obj1 = reversion.get_for_object(obj1)
        self.assertEqual(len(version_list_obj1), 1)
        version = version_list_obj1[0]
        version_data = version.field_dict
        self.assertIsCDMSRefreshRevision(version.revision)
        self.assertEqual(version_data['cdms_pk'], obj1.cdms_pk)
        self.assertEqual(version_data['modified'], obj1.modified)
        self.assertEqual(version_data['created'], obj1.created)

        # obj3
        version_list_obj3 = reversion.get_for_object(obj3)
        self.assertEqual(len(version_list_obj3), 1)
        version = version_list_obj3[0]
        version_data = version.field_dict
        self.assertIsCDMSRefreshRevision(version.revision)
        self.assertEqual(version_data['cdms_pk'], obj3.cdms_pk)
        self.assertEqual(version_data['modified'], obj3.modified)
        self.assertEqual(version_data['created'], obj3.created)

    def test_filter_all(self):
        """
        Klass.objects.filter() should work as Klass.objects.all().
        """
        self.mocked_cdms_api.list.return_value = []

        results = list(SimpleObj.objects.filter())
        self.assertEqual(results, [])

    def test_exception(self):
        """
        In case of exceptions during cdms calls, the exception gets propagated.
        No changes or revisions happen.
        """
        self.mocked_cdms_api.list.side_effect = Exception

        self.assertRaises(
            Exception,
            list, SimpleObj.objects.all()
        )
        self.assertAPINotCalled(['get', 'create', 'delete', 'update'])
        self.assertNoRevisions()

    def test_all_skip_cdms(self):
        """
        Klass.objects.skip_cdms().all() should not hit cdms and should not create any extra revisions.
        """
        list(SimpleObj.objects.skip_cdms().all())
        self.assertNoAPICalled()
        self.assertNoRevisions()
