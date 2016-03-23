import datetime
from numbers import Number

from django.utils import tree

from .models import CDMSModel


class Lookup(object):
    AND = 'AND'
    OR = 'OR'
    EXPRS = {
        'exact': '{field} eq {value}',
        'iexact': '{field} eq {value}',
        'lt': '{field} lt {value}',
        'lte': '{field} le {value}',
        'gt': '{field} gt {value}',
        'gte': '{field} ge {value}',
        'contains': 'substringof({value}, {field})',
        'icontains': 'substringof({value}, {field})',
        'startswith': 'startswith({field}, {value})',
        'istartswith': 'startswith({field}, tolower({value}))',
        'endswith': 'endswith({field}, {value})',
        'iendswith': 'endswith({field}, tolower({value}))',
        'year': 'year({field}) eq {value}',
        'month': 'month({field}) eq {value}',
        'day': 'day({field}) eq {value}',
        'hour': 'hour({field}) eq {value}',
        'minute': 'minute({field}) eq {value}',
        'second': 'second({field}) eq {value}',
    }

    def __init__(self, field, expr, value):
        self.field = field
        self.expr = expr
        self.value = value

    def convert_value(self, value):
        if isinstance(value, Number):
            return value
        if isinstance(value, datetime.datetime):
            return "datetime'{value}'".format(value=value.strftime("%Y-%m-%dT%H:%M:%S"))

        if isinstance(value, CDMSModel):
            return "guid'{value}'".format(value=value.cdms_pk)
        return "'{value}'".format(value=value)

    def as_filter_string(self):
        cdms_expr = self.EXPRS.get(self.expr)
        if not cdms_expr:
            raise NotImplementedError('Expression %s not recognised yet' % self.expr)

        return cdms_expr.format(field=self.field, value=self.convert_value(self.value))


class FilterNode(tree.Node):
    """
    Node subclass which can be used to construct cdms filter queries.

    Technically a tree with FilterNode as nodes and leaves as python objects with a `as_filter_string` method.

    See tests for examples of how to use it.
    """

    def as_filter_string(self):
        result = []
        for child in self.children:
            filter_string = child.as_filter_string()
            if filter_string:
                result.append(filter_string)
        conn = ' %s ' % self.connector
        filters_string = conn.lower().join(sorted(result))

        if filters_string:
            if self.negated:
                filters_string = 'not (%s)' % filters_string
            elif len(result) > 1:
                filters_string = '(%s)' % filters_string
        return filters_string
