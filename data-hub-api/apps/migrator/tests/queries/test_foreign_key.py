from django.db.models import Q
from django.utils import timezone

from cdms_api.tests.utils import mocked_cdms_create

from migrator.exceptions import NotMappingFieldException

from migrator.tests.queries.models import SimpleObj, ParentObj
from migrator.tests.queries.base import BaseMockedCDMSApiTestCase


class BaseForeignKeyTestCase(BaseMockedCDMSApiTestCase):
    def setUp(self):
        super(BaseForeignKeyTestCase, self).setUp()
        self.parent_obj = ParentObj.objects.skip_cdms().create(
            cdms_pk='cdms-pk', name='name'
        )


class GetFromParentTestCase(BaseForeignKeyTestCase):
    def test_all(self):
        """
        obj.child_set.all() should hit the cdms list endpoint and return all local children objs.
        """
        list(self.parent_obj.simpleobj_set.all())

        self.assertAPIListCalled(
            SimpleObj, kwargs={
                'filters': "FKField/Id eq guid'{0}'".format(self.parent_obj.cdms_pk)
            }
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_filter_children(self):
        """
        obj.child_set.filter(Q(field=...) | Q(field=...)).exclude(Q(field=...) | Q(field=...))
        should hit the cdms list endpoint and return all local children objs filtered by the django query specified.
        """
        list(
            self.parent_obj.simpleobj_set.filter(
                Q(name='name1') | Q(name='name2')
            ).exclude(
                Q(name='name3') | Q(name='name4')
            )
        )

        self.assertAPIListCalled(
            SimpleObj, kwargs={
                'filters':
                    "((Name eq 'name1' or Name eq 'name2') "
                    "and FKField/Id eq guid'{0}' "
                    "and not ((Name eq 'name3' or Name eq 'name4')))".format(
                        self.parent_obj.cdms_pk
                    )
            }
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_filter_children_skip_cdms(self):
        """
        obj.child_set.skip_cdms().filter(Q(field=...) | Q(field=...)).exclude(Q(field=...) | Q(field=...))
        should not hit cdms.
        """
        list(
            self.parent_obj.simpleobj_set.skip_cdms().filter(
                Q(name='name1') | Q(name='name2')
            ).exclude(
                Q(name='name3') | Q(name='name4')
            )
        )
        self.assertNoAPICalled()

    def test_filter_parent_by_children(self):
        """
        ParentClass.objects.filter(child_set__field=...) not implemented as not currently possible with cdms.
        """
        self.simple_obj = SimpleObj.objects.skip_cdms().create(
            cdms_pk='simple-obj', fk_obj=self.parent_obj
        )

        self.assertRaises(
            NotMappingFieldException,
            ParentObj.objects.filter,
            simpleobj=self.simple_obj
        )
        self.assertNoAPICalled()

    def test_filter_parent_by_children_skip_cdms(self):
        """
        ParentClass.objects.skip_cdms().filter(related__name=...) should not hit cdms.
        """
        self.simple_obj = SimpleObj.objects.skip_cdms().create(
            cdms_pk='simple-obj', fk_obj=self.parent_obj
        )

        list(ParentObj.objects.skip_cdms().filter(simpleobj=self.simple_obj))
        self.assertNoAPICalled()


class FilterByParentTestCase(BaseForeignKeyTestCase):
    def test_filter_by_parent(self):
        """
        ChildClass.objects.filter(parent_fk=obj)

        should filter by parent in cdms and then in local.
        """
        list(SimpleObj.objects.filter(fk_obj=self.parent_obj))

        self.assertAPIListCalled(
            SimpleObj, kwargs={
                'filters': "FKField/Id eq guid'{0}'".format(self.parent_obj.cdms_pk)
            }
        )

    def test_filter_by_parent_id(self):
        """
        ChildClass.objects.filter(parent_fk=obj.pk)

        currently not implemented as we need the related object in order to get the `cdms_pk` field value.
        """
        self.assertRaises(
            NotImplementedError,
            SimpleObj.objects.filter,
            fk_obj=self.parent_obj.pk
        )

        self.assertNoAPICalled()

    def test_filter_by_parent_field(self):
        """
        ChildClass.objects.filter(parent_fk__field=...)

        currently not implemented as cdms doesn't like it too much.
        NOTE: It could potentially be possible so investigate further if worth.
        """
        self.assertRaises(
            NotImplementedError,
            SimpleObj.objects.filter,
            fk_obj__name=self.parent_obj.name
        )

        self.assertNoAPICalled()

    def test_filter_by_parent_field_skip_cdms(self):
        """
        Filtering after calling skip_cdms(), should not hit cdms.
        """
        list(SimpleObj.objects.skip_cdms().filter(fk_obj__name=self.parent_obj.name))
        self.assertNoAPICalled()


class GetParentFromChildTestCase(BaseForeignKeyTestCase):
    def test_get(self):
        """
        obj.fk should hit cdms before querying the local db.
        """
        self.simple_obj = SimpleObj.objects.skip_cdms().create(
            cdms_pk='simple-obj', fk_obj=self.parent_obj
        )

        obj = SimpleObj.objects.get(pk=self.simple_obj.pk)

        self.assertAPIGetCalled(
            SimpleObj, kwargs={'guid': self.simple_obj.cdms_pk}
        )
        self.assertAPINotCalled(['list', 'update', 'delete', 'create'])

        self.mocked_cdms_api.reset_mock()

        self.assertEqual(obj.fk_obj.pk, self.parent_obj.pk)
        self.assertEqual(obj.fk_obj.name, self.parent_obj.name)

        self.assertAPIGetCalled(
            ParentObj, kwargs={'guid': self.parent_obj.cdms_pk}
        )

    def test_get_does_not_exist(self):
        """
        obj.fk should not hit cdms if the property is not set in local.
        """
        self.simple_obj = SimpleObj.objects.skip_cdms().create(
            cdms_pk='simple-obj', fk_obj=None
        )

        obj = SimpleObj.objects.get(pk=self.simple_obj.pk)

        self.assertAPIGetCalled(
            SimpleObj, kwargs={'guid': self.simple_obj.cdms_pk}
        )
        self.assertAPINotCalled(['list', 'update', 'delete', 'create'])

        self.mocked_cdms_api.reset_mock()

        self.assertEqual(obj.fk_obj, None)

        self.assertNoAPICalled()


class CreateChildTestCase(BaseForeignKeyTestCase):
    def test_create(self):
        """
        obj = ChildClass(parent_fk=...)
        obj.save()

        should create the object in local and in cdms with the related `parent_fk` set.
        """
        self.mocked_cdms_api.create.side_effect = mocked_cdms_create(
            create_data={
                'SimpleId': 'simple id',
                'ModifiedOn': timezone.now()
            }
        )

        obj = SimpleObj(
            name='simple obj',
            fk_obj=self.parent_obj
        )
        obj.save()
        self.assertEqual(SimpleObj.objects.skip_cdms().count(), 1)

        self.assertAPICreateCalled(
            SimpleObj, kwargs={
                'data': {
                    'Name': 'simple obj',
                    'DateTimeField': None,
                    'IntField': None,
                    'FKField': {
                        'Id': self.parent_obj.cdms_pk
                    }
                }
            }
        )
        self.assertAPINotCalled(['list', 'update', 'delete', 'get'])

        # reload obj and check cdms_pk and modified
        obj = SimpleObj.objects.skip_cdms().get(pk=obj.pk)
        self.assertEqual(obj.fk_obj.cdms_pk, self.parent_obj.cdms_pk)

    def test_create_skip_cdms(self):
        """
        obj = ChildClass(parent_fk=...)
        obj.save(skip_cdms=True)

        should not hit cdms.
        """
        obj = SimpleObj(
            name='simple obj',
            fk_obj=self.parent_obj
        )
        obj.save(skip_cdms=True)

        self.assertNoAPICalled()


class ExtraOpsFromParentTestCase(BaseForeignKeyTestCase):
    def test_add(self):
        """
        obj.child_set.add(...) currently not implemented.
        """
        self.assertRaises(
            NotImplementedError,
            self.parent_obj.simpleobj_set.add, SimpleObj(name='name')
        )

    def test_add_skip_cdms(self):
        """
        obj.child_set.add(...) currently not implemented.
        It's technically possible to implement but it would require a lot of effort
        and it's not widely used so it's not worth it.
        """
        self.assertRaises(
            NotImplementedError,
            self.parent_obj.simpleobj_set.skip_cdms().add, SimpleObj(name='name')
        )

    def test_create(self):
        """
        obj.child_set.create(...) currently not implemented.
        """
        self.assertRaises(
            NotImplementedError,
            self.parent_obj.simpleobj_set.create, name='name'
        )

    def test_create_skip_cdms(self):
        """
        obj.child_set.skip_cdms().create(...) currently not implemented.
        It's technically possible to implement but it would require a lot of effort
        and it's not widely used so it's not worth it.
        """
        self.assertRaises(
            NotImplementedError,
            self.parent_obj.simpleobj_set.skip_cdms().create, name='name'
        )

    def test_get_or_create(self):
        """
        obj.child_set.get_or_create(...) currently not implemented.
        """
        self.assertRaises(
            NotImplementedError,
            self.parent_obj.simpleobj_set.get_or_create
        )

    def test_get_or_create_skip_cdms(self):
        """
        obj.child_set.skip_cdms().get_or_create(...) currently not implemented.
        It's technically possible to implement but it would require a lot of effort
        and it's not widely used so it's not worth it.
        """
        self.assertRaises(
            NotImplementedError,
            self.parent_obj.simpleobj_set.skip_cdms().get_or_create
        )

    def test_update_or_create(self):
        """
        obj.child_set.update_or_create(...) currently not implemented.
        """
        self.assertRaises(
            NotImplementedError,
            self.parent_obj.simpleobj_set.update_or_create
        )

    def test_update_or_create_skip_cdms(self):
        """
        obj.child_set.skip_cdms().update_or_create(...) currently not implemented.
        It's technically possible to implement but it would require a lot of effort
        and it's not widely used so it's not worth it.
        """
        self.assertRaises(
            NotImplementedError,
            self.parent_obj.simpleobj_set.skip_cdms().update_or_create
        )

    def test_remove(self):
        """
        obj.child_set.remove(...) currently not implemented.
        """
        self.assertRaises(
            NotImplementedError,
            self.parent_obj.simpleobj_set.remove
        )

    def test_remove_skip_cdms(self):
        """
        obj.child_set.skip_cdms().remove(...) currently not implemented.
        It's technically possible to implement but it would require a lot of effort
        and it's not widely used so it's not worth it.
        """
        self.assertRaises(
            NotImplementedError,
            self.parent_obj.simpleobj_set.skip_cdms().remove
        )

    def test_clear(self):
        """
        obj.child_set.clear(...) currently not implemented.
        """
        self.assertRaises(
            NotImplementedError,
            self.parent_obj.simpleobj_set.clear
        )

    def test_clear_skip_cdms(self):
        """
        obj.child_set.skip_cdms().clear(...) currently not implemented.
        It's technically possible to implement but it would require a lot of effort
        and it's not widely used so it's not worth it.
        """
        self.assertRaises(
            NotImplementedError,
            self.parent_obj.simpleobj_set.skip_cdms().clear
        )
