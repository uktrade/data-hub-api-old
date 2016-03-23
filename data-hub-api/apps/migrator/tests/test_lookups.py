import datetime

from django.test.testcases import TestCase

from migrator.lookups import FilterNode, Lookup


class LookupTestCase(TestCase):
    def test_simple(self):
        """
        Tests one single filter.
        """
        filters = FilterNode(
            children=[
                Lookup('Field', 'exact', 'my-field')
            ]
        )

        self.assertEqual(
            filters.as_filter_string(),
            "Field eq 'my-field'"
        )

    def test_two_in_AND(self):
        """
        Tests two values in AND.
        """
        filters = FilterNode(
            children=[
                Lookup('Field1', 'exact', 'my-field1'),
                Lookup('Field2', 'exact', 'my-field2')
            ],
            connector=Lookup.AND
        )

        self.assertEqual(
            filters.as_filter_string(),
            "(Field1 eq 'my-field1' and Field2 eq 'my-field2')"
        )

    def test_two_in_OR(self):
        """
        Tests two values in OR.
        """
        filters = FilterNode(
            children=[
                Lookup('Field1', 'exact', 'my-field1'),
                Lookup('Field2', 'exact', 'my-field2')
            ],
            connector=Lookup.OR
        )

        self.assertEqual(
            filters.as_filter_string(),
            "(Field1 eq 'my-field1' or Field2 eq 'my-field2')"
        )

    def test_complex(self):
        """
        Tests multiple values in AND and OR.
        """
        filters = FilterNode(
            children=[
                FilterNode(
                    children=[
                        Lookup('Field2', 'exact', 'my-field2'),
                        FilterNode(
                            children=[
                                Lookup('Field3', 'exact', 'my-field3')
                            ],
                            negated=True
                        ),
                    ],
                    connector=Lookup.OR
                ),
                Lookup('Field1', 'exact', 'my-field1')
            ],
            connector=Lookup.AND
        )

        self.assertEqual(
            filters.as_filter_string(),
            "((Field2 eq 'my-field2' or not (Field3 eq 'my-field3')) and Field1 eq 'my-field1')"
        )


class ValueLookupTestCase(TestCase):
    def test_string(self):
        filters = FilterNode(
            children=[
                Lookup('Field', 'exact', 'my-field')
            ]
        )

        self.assertEqual(
            filters.as_filter_string(),
            "Field eq 'my-field'"
        )

    def test_datetime(self):
        dt = datetime.datetime(day=28, month=2, year=2016).replace(tzinfo=datetime.timezone.utc)
        filters = FilterNode(
            children=[
                Lookup('Field', 'exact', dt)
            ]
        )

        self.assertEqual(
            filters.as_filter_string(),
            "Field eq datetime'2016-02-28T00:00:00'"
        )

    def test_int(self):
        filters = FilterNode(
            children=[
                Lookup('Field', 'exact', 2)
            ]
        )

        self.assertEqual(
            filters.as_filter_string(),
            "Field eq 2"
        )
