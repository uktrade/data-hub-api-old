from unittest import skip

from reversion import revisions as reversion
from reversion.models import Revision, Version

from migrator.tests.models import SimpleObj
from migrator.tests.base import BaseMockedCDMSApiTestCase


class RevisionTestCase(BaseMockedCDMSApiTestCase):
    @skip('Not supported out-of-the-box, to be implemented if needed')
    def test_revert_deleted_object(self):
        """
        After deleting an object with revision, I should be able to revert to the last non-deleted version.

        Unfortunately, the django-reversion code is a bit dirty at this point so the reversion.get_deleted(...)
        method call does not work out of the box.

        We would have to implement it manually when/if needed.
        """
        obj = SimpleObj.objects.skip_cdms().create(
            name='test', cdms_pk='cdms-pk'
        )
        obj_id = obj.pk
        self.reset_revisions()

        self.assertEqual(Version.objects.count(), 0)
        self.assertEqual(Revision.objects.count(), 0)

        obj.save()
        obj.delete()

        # check cdms calls
        self.assertEqual(self.mocked_cdms_api.get.call_count, 1)
        self.assertEqual(self.mocked_cdms_api.update.call_count, 1)
        self.assertEqual(self.mocked_cdms_api.delete.call_count, 1)
        self.assertAPINotCalled(['list', 'create'])

        self.mocked_cdms_api.reset_mock()

        # check versions
        self.assertEqual(Version.objects.count(), 1)
        self.assertEqual(Revision.objects.count(), 1)

        deleted_list = reversion.get_deleted(SimpleObj)
        delete_version = deleted_list.get(id=obj_id)

        # revert deleted version
        delete_version.revert()

        obj = SimpleObj.objects.skip_cdms().get(pk=obj_id)
        self.assertEqual(obj.name, 'test')

    def test_revert_to_previous_revision(self):
        """
        Saving an object in two different revisions and then reverting back to the first one should
        make a single extra cdms call to update the object with the previous data.
        """
        obj = SimpleObj.objects.skip_cdms().create(
            name='test', cdms_pk='cdms-pk'
        )
        self.reset_revisions()

        # revision 1
        obj.name = 'test old'
        obj.save()

        # revision 2
        obj.name = 'test latest'
        obj.save()

        # check cdms calls
        self.assertEqual(self.mocked_cdms_api.get.call_count, 2)
        self.assertEqual(self.mocked_cdms_api.update.call_count, 2)
        self.assertAPINotCalled(['list', 'create', 'delete'])

        self.mocked_cdms_api.reset_mock()

        # check versions
        self.assertEqual(Version.objects.count(), 2)
        self.assertEqual(Revision.objects.count(), 2)

        version_list = reversion.get_for_object(obj)
        self.assertEqual(len(version_list), 2)

        version_old = version_list[1]
        self.assertEqual(version_old.field_dict['name'], 'test old')

        version_latest = version_list[0]
        self.assertEqual(version_latest.field_dict['name'], 'test latest')

        # revert to old version
        version_old.revert()

        obj = SimpleObj.objects.skip_cdms().get(pk=obj.pk)
        self.assertEqual(obj.name, 'test old')

        # check cdms update called
        self.assertAPIUpdateCalled(
            SimpleObj,
            kwargs={
                'guid': 'cdms-pk',
                'data': {
                    'Name': 'test old',
                    'DateTimeField': None,
                    'IntField': None,
                    'SimpleId': 'cdms-pk',
                    'FKField': None
                }
            }
        )
        self.assertAPINotCalled(['list', 'create', 'delete'])
