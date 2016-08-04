#!/usr/bin/env python

#   Postgres SQL container for pyslet Odata implementation
#   Copyright (C), 2014 Chris Daley <chebizarro@gmail.com>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

# This module implements a Postgres SQL import and export dialog to connect
# to a Postgres SQL database server as well as an export module to dump a diagram
# to Postgres SQL compatible SQL.
#

import psycopg2
from pyslet.odata2 import sqlds

class PgSQLEntityContainer(sqlds.SQLEntityContainer):

    """Creates a container that represents a PgSQL database.

    Additional keyword arguments:

    pgsql_options
                A dictionary of additional options to pass as named arguments
                to the connect method.  It defaults to an empty dictionary

                For more information see psycopg2

    ..  psycopg2:   http://initd.org/psycopg/

    All other keyword arguments required to initialise the base class must be
    passed on construction except *dbapi* which is automatically set to the
    Python psycopg2 module."""

    def __init__(self, pgsql_options={}, **kwargs):
        super(PgSQLEntityContainer, self).__init__(dbapi=psycopg2, **kwargs)
        self.pgsql_options = pgsql_options
        self.ParamsClass = PyFormatParams

    def get_collection_class(self):
        'Overridden to return :py:class:`PgSQLEntityCollection`'
        return PgSQLEntityCollection

    def get_symmetric_navigation_class(self):
        'Overridden to return :py:class:`PgSQLAssociationCollection`'
        return PgSQLAssociationCollection

    def get_fk_class(self):
        'Overridden to return :py:class:`PgSQLForeignKeyCollection`'
        return PgSQLForeignKeyCollection

    def get_rk_class(self):
        'Overridden to return :py:class:`PgSQLReverseKeyCollection`'
        return PgSQLReverseKeyCollection

    def open(self):
        'Calls the underlying connect method.'
        dbc = self.dbapi.connect(**self.pgsql_options)
        return dbc

    def break_connection(self, connection):
        'Calls the underlying interrupt method.'
        connection.interrupt()

    def prepare_sql_type(self, simple_value, params, nullable=None):
        '''
        Performs PgSQL custom mappings

        We inherit most of the type mappings but the following types use custom
        mappings:

        ==================  ===================================
            EDM Type         PgSQL Equivalent
        ------------------  -----------------------------------
        Edm.Binary          BYTEA
        Edm.Guid            UUID
        Edm.String          TEXT
        ==================  ===================================
        '''

        p = simple_value.pDef
        column_def = []

        if isinstance(simple_value, edm.BinaryValue):
            column_def.append(u"BYTEA")
        elif isinstance(simple_value, edm.GuidValue):
            column_def.append(u"UUID")
        elif isinstance(simple_value, edm.StringValue):
            if p.unicode is None or p.unicode:
                n = ""  # formerly "N", but "NVARCHAR" isn't a thing
                        # in postgres
            else:
                n = ""
            if p.fixedLength:
                if p.maxLength:
                    column_def.append(u"%sCHAR(%i)" % (n, p.maxLength))
                else:
                    raise edm.ModelConstraintError("Edm.String of fixed length missing max: %s" % p.name)
            elif p.maxLength:
                column_def.append(u"%sVARCHAR(%i)" % (n, p.maxLength))
            else:
                column_def.append(u"TEXT")
        else:
            return super(PgSQLEntityContainer, self).prepare_sql_type(
                simple_value, params, nullable
            )
        null_conditions = (
            nullable is not None and not nullable,
            nullable is None and not p.nullable,
        )
        if any(null_conditions):
            column_def.append(u' NOT NULL')
        if simple_value:
            # Format the default
            column_def.append(u' DEFAULT ')
            column_def.append(
                params.add_param(self.prepare_sql_value(simple_value))
            )
        return ''.join(column_def)

    def prepare_sql_value(self, simple_value):
        '''
        Returns a python value suitable for passing as a parameter.

        We inherit most of the value mappings but the following types have
        custom mappings.

        ==================  =============================================
            EDM Type         Python value added as parameter
        ------------------  ---------------------------------------------
        Edm.Binary          buffer object
        Edm.Guid            buffer object containing bytes representation
        ==================  ==============================================

        Our use of buffer type is not ideal as it generates warning when Python
        is run with the -3 flag (to check for Python 3 compatibility) but it
        seems unavoidable at the current time.
        '''
        if not simple_value:
            return None
        elif isinstance(simple_value, edm.BinaryValue):
            return buffer(simple_value.value)
        elif isinstance(simple_value, edm.GuidValue):
            return buffer(simple_value.value.bytes)
        else:
            return super(PgSQLEntityContainer, self).prepare_sql_value(
                simple_value
            )

    def read_sql_value(self, simple_value, new_value):
        'Reverses the transformation performed by prepare_sql_value'
        if new_value is None:
            simple_value.SetNull()
        elif isinstance(new_value, types.BufferType):
            new_value = str(new_value)
            simple_value.SetFromValue(new_value)
        else:
            simple_value.SetFromValue(new_value)

    def new_from_sql_value(self, sql_value):
        '''
        Returns a new simple value instance initialised from *sql_value*

        Overridden to ensure that buffer objects returned by the underlying DB
        API are converted to strings.  Otherwise *sql_value* is passed directly
        to the parent.
        '''
        if isinstance(sql_value, types.BufferType):
            result = edm.BinaryValue()
            result.SetFromValue(str(sql_value))
            return result
        else:
            return super(PgSQLEntityContainer, self).new_from_sql_value(
                sql_value
            )


class PgSQLEntityCollectionBase(sqlds.SQLCollectionBase):
    '''
    Base class for PgSQL SQL custom mappings.

    This class provides some PgSQL specific mappings for certain functions to
    improve compatibility with the OData expression language.
    '''

    def sql_expression_mod(self, expression, params, context):
        'Converts the mod expression'
        'Converts the div expression: maps to SQL "/" '  # TODO: What is this doing here?
        return self.sql_expression_generic_binary(
            expression, params, context, '%'
        )

    def sql_expression_replace(self, expression, params, context):
        'Converts the replace method'
        query = ["replace("]
        query.append(self.sql_expression(expression.operands[0], params, ','))
        query.append(")")
        return ''.join(query)  # don't bother with brackets!

    def sql_expression_length(self, expression, params, context):
        'Converts the length method: maps to length( op[0] )'
        query = ["length("]
        query.append(self.sql_expression(expression.operands[0], params, ','))
        query.append(")")
        return ''.join(query)  # don't bother with brackets!

    def sql_expression_round(self, expression, params, context):
        'Converts the round method'
        query = ["round("]
        query.append(self.sql_expression(expression.operands[0], params, ','))
        query.append(")")
        return ''.join(query)  # don't bother with brackets!

    def sql_expression_floor(self, expression, params, context):
        'Converts the floor method'
        query = ["floor("]
        query.append(self.sql_expression(expression.operands[0], params, ','))
        query.append(")")
        return ''.join(query)  # don't bother with brackets!

    def sql_expression_ceiling(self, expression, params, context):
        'Converts the ceiling method'
        query = ["ceil("]
        query.append(self.sql_expression(expression.operands[0], params, ','))
        query.append(")")
        return ''.join(query)  # don't bother with brackets!


class PgSQLEntityCollection(PgSQLEntityCollectionBase, sqlds.SQLEntityCollection):
    'PgSQL-specific collection for entity sets'
    pass

class PgSQLAssociationCollection(PgSQLEntityCollectionBase, sqlds.SQLAssociationCollection):
    'PgSQL-specific collection for symmetric association sets'
    pass


class PgSQLForeignKeyCollection(PgSQLEntityCollectionBase, sqlds.SQLForeignKeyCollection):
    'PgSQL-specific collection for navigation from a foreign key'
    pass


class PgSQLReverseKeyCollection(PgSQLEntityCollectionBase, sqlds.SQLReverseKeyCollection):
    'PgSQL-specific collection for navigation to a foreign key'
    pass


class PyFormatParams(sqlds.SQLParams):
    'A class for building parameter lists using ":1", ":2",... syntax'

    def __init__(self):
        super(PyFormatParams, self).__init__()
        self.params = []

    def add_param(self, value):
        self.params.append(value)
        return "%s"
