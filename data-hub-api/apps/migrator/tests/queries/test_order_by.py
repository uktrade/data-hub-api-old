from migrator.tests.queries.models import SimpleObj
from migrator.tests.queries.base import BaseMockedCDMSApiTestCase


class OrderByTestCase(BaseMockedCDMSApiTestCase):
    def test_order_by_default(self):
        """
        If order_by not specified, the default 'modified' field should be used.
        """
        list(SimpleObj.objects.all())

        self.assertAPIListCalled(
            SimpleObj,
            kwargs={
                'filters': '',
                'order_by': ['ModifiedOn asc']
            }
        )
        self.assertAPINotCalled(['get', 'create', 'delete', 'update'])

    def test_order_by_name_asc(self):
        """
        Given the field 'myfield' mapped to the cdms field 'myCDMSfield':

        Klass.objects.all().order_by('myfield') should make a cdms call ordered by 'myCDMSfield asc'.
        """
        list(SimpleObj.objects.all().order_by('name'))

        self.assertAPIListCalled(
            SimpleObj,
            kwargs={
                'filters': '',
                'order_by': ['Name asc']
            }
        )
        self.assertAPINotCalled(['get', 'create', 'delete', 'update'])

    def test_order_by_name_desc(self):
        """
        Given the field 'myfield' mapped to the cdms field 'myCDMSfield':

        Klass.objects.all().order_by('-myfield') should order by 'myCDMSfield desc'.
        """
        list(SimpleObj.objects.all().order_by('-name'))

        self.assertAPIListCalled(
            SimpleObj,
            kwargs={
                'filters': '',
                'order_by': ['Name desc']
            }
        )
        self.assertAPINotCalled(['get', 'create', 'delete', 'update'])

    def test_order_by_two_fields(self):
        """
        Given the fields 'myfield1' and 'myfield2' mapped to the cdms fields 'myCDMSfield1' and 'myCDMSfield2':

        Klass.objects.all().order_by('myfield1', '-myfield2') should make a cdms call
        order by 'myCDMSfield1 asc AND myCDMSfield2 desc'.
        """
        list(SimpleObj.objects.all().order_by('modified', '-name'))

        self.assertAPIListCalled(
            SimpleObj,
            kwargs={
                'filters': '',
                'order_by': ['ModifiedOn asc', 'Name desc']
            }
        )
        self.assertAPINotCalled(['get', 'create', 'delete', 'update'])

    def test_order_by_non_cdms_field(self):
        """
        Ordering by a non-cdms field is not allowed as the cdms call to get the list would not be ordered by
        the same field.
        """
        self.assertRaises(
            NotImplementedError,
            list,
            SimpleObj.objects.all().order_by('d_field')
        )

        self.assertAPINotCalled(['get', 'create', 'delete', 'update'])

    def test_order_randomly(self):
        """
        Klass.objects.all().order_by('?') not currently implemented.
        """
        self.assertRaises(
            NotImplementedError,
            list,
            SimpleObj.objects.all().order_by('?')
        )

        self.assertAPINotCalled(['get', 'create', 'delete', 'update'])

    def test_order_by_related_obj_field(self):
        """
        Klass.objects.all().order_by('fk_obj') should order by foreign key field.
        """
        list(SimpleObj.objects.all().order_by('fk_obj'))

        self.assertAPIListCalled(
            SimpleObj,
            kwargs={
                'filters': '',
                'order_by': ['FKField asc']
            }
        )
        self.assertAPINotCalled(['get', 'create', 'delete', 'update'])


class OrderBySkipCDMSTestCase(BaseMockedCDMSApiTestCase):
    def test_order_by_default(self):
        """
        Klass.objects.skip_cdms().all() should not hit cdms.
        """
        list(SimpleObj.objects.skip_cdms().all())
        self.assertNoAPICalled()

    def test_order_by_name(self):
        """
        Klass.objects.skip_cdms().all().order_by('field') should not hit cdms.
        """
        list(SimpleObj.objects.skip_cdms().all().order_by('name'))
        self.assertNoAPICalled()

    def test_order_by_two_fields(self):
        """
        Klass.objects.skip_cdms().all().order_by('field1', '-field2') should not hit cdms.
        """
        list(SimpleObj.objects.skip_cdms().all().order_by('modified', '-name'))
        self.assertNoAPICalled()

    def test_order_randomly(self):
        """
        Klass.objects.skip_cdms().all().order_by('?') should not hit cdms.
        """
        list(SimpleObj.objects.skip_cdms().all().order_by('?'))
        self.assertNoAPICalled()

    def test_order_by_related_obj_field(self):
        list(SimpleObj.objects.skip_cdms().all().order_by('fk_obj'))
        self.assertNoAPICalled()
