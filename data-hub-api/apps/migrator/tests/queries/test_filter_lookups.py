from unittest import skip

from django.utils import timezone

from migrator.tests.queries.models import SimpleObj
from migrator.tests.queries.base import BaseMockedCDMSApiTestCase


class FilterLookupsTestCase(BaseMockedCDMSApiTestCase):
    def setUp(self):
        super(FilterLookupsTestCase, self).setUp()
        self.obj = SimpleObj.objects.skip_cdms().create(
            cdms_pk='cdms-pk', name='before something after'
        )

    def test_exact(self):
        list(SimpleObj.objects.filter(name__exact='something'))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "Name eq 'something'"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_iexact(self):
        list(SimpleObj.objects.filter(name__iexact='something'))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "Name eq 'something'"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_contains(self):
        list(SimpleObj.objects.filter(name__contains='something'))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "substringof('something', Name)"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_icontains(self):
        list(SimpleObj.objects.filter(name__icontains='something'))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "substringof('something', Name)"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_in(self):
        self.assertRaises(
            NotImplementedError,
            list, SimpleObj.objects.filter(name__in=['something', 'something else'])
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_gt(self):
        list(SimpleObj.objects.filter(name__gt='something'))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "Name gt 'something'"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_gte(self):
        list(SimpleObj.objects.filter(name__gte='something'))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "Name ge 'something'"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_lt(self):
        list(SimpleObj.objects.filter(name__lt='something'))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "Name lt 'something'"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_lte(self):
        list(SimpleObj.objects.filter(name__lte='something'))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "Name le 'something'"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_startswith(self):
        list(SimpleObj.objects.filter(name__startswith='something'))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "startswith(Name, 'something')"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_istartswith(self):
        list(SimpleObj.objects.filter(name__istartswith='something'))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "startswith(Name, tolower('something'))"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_endswith(self):
        list(SimpleObj.objects.filter(name__endswith='something'))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "endswith(Name, 'something')"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_iendswith(self):
        list(SimpleObj.objects.filter(name__iendswith='something'))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "endswith(Name, tolower('something'))"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_range(self):
        dt = timezone.now()
        self.assertRaises(
            NotImplementedError,
            list, SimpleObj.objects.filter(dt_field__range=(dt, dt))
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_year(self):
        list(SimpleObj.objects.filter(dt_field__year=2016))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "year(DateTimeField) eq 2016"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_month(self):
        list(SimpleObj.objects.filter(dt_field__month=12))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "month(DateTimeField) eq 12"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_day(self):
        list(SimpleObj.objects.filter(dt_field__day=1))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "day(DateTimeField) eq 1"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_week_day(self):
        self.assertRaises(
            NotImplementedError,
            list, SimpleObj.objects.filter(dt_field__week_day=1)
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_hour(self):
        list(SimpleObj.objects.filter(dt_field__hour=1))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "hour(DateTimeField) eq 1"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_minute(self):
        list(SimpleObj.objects.filter(dt_field__minute=1))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "minute(DateTimeField) eq 1"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_second(self):
        list(SimpleObj.objects.filter(dt_field__second=1))

        self.assertAPIListCalled(
            SimpleObj, kwargs={'filters': "second(DateTimeField) eq 1"}
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    @skip('TODO we should probably support this')
    def test_isnull(self):
        self.assertRaises(
            NotImplementedError,
            list, SimpleObj.objects.filter(dt_field__isnull=True)
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_search(self):
        self.assertRaises(
            NotImplementedError,
            list, SimpleObj.objects.filter(name__search='name')
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_regex(self):
        self.assertRaises(
            NotImplementedError,
            list, SimpleObj.objects.filter(name__regex=r'.*')
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])

    def test_iregex(self):
        self.assertRaises(
            NotImplementedError,
            list, SimpleObj.objects.filter(name__iregex=r'.*')
        )
        self.assertAPINotCalled(['create', 'update', 'delete', 'get'])
