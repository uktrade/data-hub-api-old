import datetime

from django.test.testcases import TestCase

from cdms_api.fields import StringField, IntegerField, DateTimeField, BooleanField


class StringFieldTestCase(TestCase):
    def setUp(self):
        super(StringFieldTestCase, self).setUp()
        self.field = StringField('name')

    def test_from_cdms_value(self):
        self.assertEqual(
            self.field.from_cdms_value('a string'),
            'a string'
        )

    def test_from_cdms_value_None_with_nullable_field(self):
        """
        When null=True, None values are returned untouched.
        """
        field = StringField('name', null=True)
        self.assertEqual(
            field.from_cdms_value(None),
            None
        )

    def test_from_cdms_value_None_without_nullable_field(self):
        """
        When null=False, None values are returned as empty strings.
        """
        field = StringField('name', null=False)
        self.assertEqual(
            field.from_cdms_value(None),
            ''
        )

    def test_to_cdms_value(self):
        self.assertEqual(
            self.field.to_cdms_value('a string'),
            'a string'
        )

    def test_to_cdms_value_None(self):
        self.assertEqual(
            self.field.to_cdms_value(None),
            None
        )


class IntegerFieldTestCase(TestCase):
    def setUp(self):
        super(IntegerFieldTestCase, self).setUp()
        self.field = IntegerField('name')

    def test_from_cdms_value(self):
        self.assertEqual(
            self.field.from_cdms_value(10),
            10
        )

    def test_from_cdms_value_None(self):
        self.assertEqual(
            self.field.from_cdms_value(None),
            None
        )

    def test_to_cdms_value(self):
        self.assertEqual(
            self.field.to_cdms_value(10),
            10
        )

    def test_to_cdms_value_None(self):
        self.assertEqual(
            self.field.to_cdms_value(None),
            None
        )


class BooleanFieldTestCase(TestCase):
    def setUp(self):
        super(BooleanFieldTestCase, self).setUp()
        self.field = BooleanField('name')

    def test_from_cdms_value(self):
        self.assertEqual(
            self.field.from_cdms_value(False),
            False
        )

    def test_from_cdms_value_None(self):
        self.assertEqual(
            self.field.from_cdms_value(None),
            None
        )

    def test_to_cdms_value(self):
        self.assertEqual(
            self.field.to_cdms_value(False),
            False
        )

    def test_to_cdms_value_None(self):
        self.assertEqual(
            self.field.to_cdms_value(None),
            None
        )


class DateTimeFieldTestCase(TestCase):
    def setUp(self):
        super(DateTimeFieldTestCase, self).setUp()
        self.field = DateTimeField('name')

    def test_from_cdms_value(self):
        dt = datetime.datetime(2016, 1, 1).replace(tzinfo=datetime.timezone.utc)
        self.assertEqual(
            self.field.from_cdms_value('/Date(1451606400000)/'),
            dt
        )

    def test_from_cdms_value_None(self):
        self.assertEqual(
            self.field.from_cdms_value(None),
            None
        )

    def test_to_cdms_value(self):
        dt = datetime.datetime(2016, 1, 1).replace(tzinfo=datetime.timezone.utc)
        self.assertEqual(
            self.field.to_cdms_value(dt),
            '/Date(1451606400000)/'
        )

    def test_to_cdms_value_None(self):
        self.assertEqual(
            self.field.to_cdms_value(None),
            None
        )
