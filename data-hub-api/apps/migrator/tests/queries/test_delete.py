from migrator.tests.queries.models import SimpleObj
from migrator.tests.queries.base import BaseMockedCDMSApiTestCase


class BaseDeleteTestCase(BaseMockedCDMSApiTestCase):
    def setUp(self):
        super(BaseDeleteTestCase, self).setUp()
        self.obj = SimpleObj.objects.skip_cdms().create(
            cdms_pk='cdms-pk', name='name'
        )


class DeleteTestCase(BaseDeleteTestCase):
    def test_from_obj(self):
        """
        obj.delete() should delete the local and the cdms obj.
        """
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 1)
        self.obj.delete()
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)

        self.assertAPIDeleteCalled(
            SimpleObj, kwargs={'guid': self.obj.cdms_pk}
        )
        self.assertAPINotCalled(['list', 'update', 'get', 'create'])

    def test_with_manager(self):
        """
        MyObject.objects.filter(...).delete(...) not currently implemented
        as it's not possible to rollback changes in cdms in case of deletes
        involving multiple objects.
        """
        self.assertRaises(
            NotImplementedError,
            SimpleObj.objects.filter(name__icontains='name').delete
        )
        self.assertNoAPICalled()

    def test_exception_triggers_rollback(self):
        """
        In case of exceptions with the cdms call, no changes should be reflected in the db.
        """
        self.mocked_cdms_api.delete.side_effect = Exception

        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 1)
        self.assertRaises(
            Exception,
            self.obj.delete
        )
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 1)

        self.assertAPINotCalled(['list', 'update', 'get', 'create'])


class DeleteSkipCDMSTestCase(BaseDeleteTestCase):
    def test_from_obj(self):
        """
        obj.delete(skip_cdms=True) should only delete the obj in local.
        """
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 1)
        self.obj.delete(skip_cdms=True)
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)

        self.assertNoAPICalled()

    def test_with_manager(self):
        """
        MyObject.objects.skip_cdms().filter(...).delete(...) should only delete local objs.
        """
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 1)
        SimpleObj.objects.skip_cdms().filter(name='name').delete()
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 0)

        self.assertNoAPICalled()
