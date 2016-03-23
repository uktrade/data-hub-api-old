import datetime

from django.db.models import Q

from migrator.tests.queries.models import SimpleObj
from migrator.tests.queries.base import BaseMockedCDMSApiTestCase


class FilterTestCase(BaseMockedCDMSApiTestCase):
    def test_one_field(self):
        list(SimpleObj.objects.filter(name='something'))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "Name eq 'something'"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_q_one_field(self):
        list(SimpleObj.objects.filter(Q(name='something')))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "Name eq 'something'"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_two_fields(self):
        list(SimpleObj.objects.filter(name='something', int_field=1))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "(IntField eq 1 and Name eq 'something')"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_q_two_fields_in_and(self):
        list(SimpleObj.objects.filter(Q(name='something') & Q(int_field=10)))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "(IntField eq 10 and Name eq 'something')"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_two_fields_in_chain(self):
        list(SimpleObj.objects.filter(name='something').filter(int_field=1))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "(IntField eq 1 and Name eq 'something')"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_two_fields_in_or(self):
        list(SimpleObj.objects.filter(Q(name='something') | Q(int_field=1)))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "(IntField eq 1 or Name eq 'something')"}
        )

        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_q_fields_in_and_in_group(self):
        dt = datetime.datetime(2016, 1, 1).replace(tzinfo=datetime.timezone.utc)
        list(
            SimpleObj.objects.filter(
                Q(Q(name='something') & Q(int_field=10)) & Q(dt_field__gt=dt)
            )
        )

        self.assertAPIListCalled(
            SimpleObj, kwargs={
                'filters':
                    "(DateTimeField gt datetime'2016-01-01T00:00:00' and IntField eq 10 and Name eq 'something')"
            }
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_q_fields_in_and__or_in_group(self):
        dt = datetime.datetime(2016, 1, 1).replace(tzinfo=datetime.timezone.utc)
        list(
            SimpleObj.objects.filter(
                Q(Q(name='something') | Q(int_field=10)) & Q(dt_field__gt=dt)
            )
        )

        self.assertAPIListCalled(
            SimpleObj, kwargs={
                'filters':
                    "((IntField eq 10 or Name eq 'something') and DateTimeField gt datetime'2016-01-01T00:00:00')"
            }
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])


class FilterSkipCDMSTestCase(BaseMockedCDMSApiTestCase):
    def test_filter(self):
        """
        Klass.objects.skip_cdms().filter(field=...) should not hit cdms.
        """
        list(SimpleObj.objects.skip_cdms().filter(name='something'))
        self.assertNoAPICalled()


class ExcludeTestCase(BaseMockedCDMSApiTestCase):
    def test_one_field(self):
        list(SimpleObj.objects.exclude(name='something'))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "not (Name eq 'something')"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_two_fields(self):
        list(SimpleObj.objects.exclude(name='something', int_field=1))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "not (IntField eq 1 and Name eq 'something')"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_two_fields_in_chain(self):
        list(SimpleObj.objects.exclude(name='something').exclude(int_field=1))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "(not (IntField eq 1) and not (Name eq 'something'))"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_two_fields_in_or(self):
        list(SimpleObj.objects.exclude(Q(name='something') | Q(int_field=1)))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "not ((IntField eq 1 or Name eq 'something'))"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_simple_filter_exclude(self):
        list(SimpleObj.objects.filter(name='something').exclude(int_field=1))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "(Name eq 'something' and not (IntField eq 1))"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_complex_filter_exclude(self):
        list(
            SimpleObj.objects.filter(
                Q(name='something') | Q(name='something else')
            ).exclude(
                Q(int_field=1) | Q(int_field=2)
            )
        )

        self.assertAPIListCalled(
            SimpleObj, kwargs={
                'filters':
                "((Name eq 'something else' or Name eq 'something') and not ((IntField eq 1 or IntField eq 2)))"
            }
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])


class ExcludeSkipCDMSTestCase(BaseMockedCDMSApiTestCase):
    """
    Klass.objects.skip_cdms().exclude(field=...) should not hit cdms.
    """
    def test_exclude(self):
        list(SimpleObj.objects.skip_cdms().exclude(name='something'))
        self.assertNoAPICalled()
