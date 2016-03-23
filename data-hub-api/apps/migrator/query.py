import sys
import warnings
import datetime

from django.db import transaction, models
from django.db.models.sql.query import get_field_names_from_opts, get_order_dir
from django.db.models.constants import LOOKUP_SEP
from django.utils.tree import Node
from django.utils import timezone
from django.core.exceptions import FieldDoesNotExist, FieldError

from cdms_api import api as cdms_conn

from .models import CDMSModel
from .exceptions import NotMappingFieldException
from .lookups import FilterNode, Lookup


class CDMSCompiler(object):
    def __init__(self, query):
        self.query = query

    def get_service(self):
        return self.get_migrator().service

    def get_migrator(self):
        return self.query.model.cdms_migrator

    def execute(self):
        raise NotImplementedError()


class CDMSSelectCompiler(CDMSCompiler):
    def get_filters(self):
        return self.query.filters.as_filter_string()

    def get_order_by(self):
        cdms_orderby = []

        if self.query.order_by:
            ordering = self.query.order_by
        else:
            ordering = self.query.model._meta.ordering
            if not ordering:
                warnings.warn(
                    "{0} does not have a default ordering so cdms calls and local ones "
                    "are not similarly ordered. We strongly recommend you should add "
                    "a Meta class with ordering = ['modified'] or similar.".format(self.query.model.__name__)
                )
                ordering = ['modified']

        for field in ordering:
            col, order = get_order_dir(field, 'ASC')
            try:
                cdms_field = self.get_migrator().get_cdms_field(col)
            except NotMappingFieldException:
                raise NotImplementedError(
                    'Cannot order by {0}, only ordering by direct fields currently implemented'.format(col)
                )

            cdms_orderby.append(
                '{0} {1}'.format(cdms_field.cdms_name, order.lower())
            )
        return cdms_orderby

    def execute(self):
        if self.query.empty:
            return []

        return cdms_conn.list(
            self.get_service(),
            filters=self.get_filters(),
            order_by=self.get_order_by()
        )


class CDMSInsertCompiler(CDMSCompiler):
    def execute(self):
        data = self.get_migrator().clean_up_cdms_data_before_changes(self.query.cdms_data)
        results = cdms_conn.create(
            self.get_service(), data=data
        )
        return (
            self.get_migrator().get_cdms_pk(results),
            self.get_migrator().get_modified_on(results)
        )


class CDMSGetCompiler(CDMSCompiler):
    def execute(self):
        return cdms_conn.get(
            self.get_service(),
            guid=self.query.cdms_pk
        )


class CDMSUpdateCompiler(CDMSCompiler):
    def execute(self):
        data = self.get_migrator().clean_up_cdms_data_before_changes(self.query.cdms_data)
        results = cdms_conn.update(
            self.get_service(),
            guid=self.query.cdms_pk,
            data=data
        )
        return self.get_migrator().get_modified_on(results)


class CDMSRefreshCompiler(CDMSGetCompiler):
    def get_cdms_data(self):
        if self.query.cdms_data:
            return self.query.cdms_data
        return super(CDMSRefreshCompiler, self).execute()

    def get_local_obj(self):
        if self.query.local_obj:
            return (self.query.local_obj, False)

        results = self.query.model.objects.skip_cdms().filter(cdms_pk=self.query.cdms_pk)
        if results:
            return (results[0], False)

        obj = self.query.model()
        obj.modified = timezone.now() - datetime.timedelta(days=(50 * 365))
        obj.created = obj.modified
        return (obj, True)

    def execute(self):
        migrator = self.get_migrator()
        manager = self.query.model.objects
        cdms_data = self.get_cdms_data()
        obj, new_obj = self.get_local_obj()

        # check if local obj has to be updated
        changed, modified_on, created_on = migrator.has_cdms_obj_changed(obj, cdms_data)
        if changed:
            # 1st save for the fields
            migrator.update_local_from_cdms_data(
                obj, cdms_data,
                cdms_known_related_objects=self.query.cdms_known_related_objects
            )
            obj.save(skip_cdms=True)

            # 2nd save for the modified/created field (this can be improved)
            update_fields = {}
            obj.modified = modified_on
            update_fields['modified'] = modified_on

            if new_obj:
                obj.created = created_on
                obj.cdms_pk = self.query.cdms_pk
                update_fields['created'] = obj.created
                update_fields['cdms_pk'] = obj.cdms_pk
            manager.skip_cdms().filter(pk=obj.pk).update(**update_fields)

        return obj


class CDMSDeleteCompiler(CDMSGetCompiler):
    def execute(self):
        return cdms_conn.delete(
            self.get_service(),
            guid=self.query.cdms_pk
        )


class CDMSModelIterable(models.query.ModelIterable):
    def __iter__(self):

        # NOTE: do keep the sys.exc_info check otherwise django
        # will keep calling this method over and over again when
        # trying to print the 500 error page which is NOT what we want
        if not self.queryset.cdms_skip and not sys.exc_info()[0]:
            with transaction.atomic():
                cdms_query = self.queryset.cdms_query
                results = CDMSSelectCompiler(cdms_query).execute()

                for result in results:
                    query = RefreshQuery(self.queryset.model)
                    query.set_cdms_known_related_objects(self.queryset._cdms_known_related_objects)
                    query.set_cdms_data(result)
                    query.get_compiler().execute()

        return super(CDMSModelIterable, self).__iter__()


class CDMSQuery(object):
    compiler = CDMSCompiler

    def __init__(self, model):
        self.model = model

        self.filters = FilterNode()
        self.empty = False
        self.cdms_known_related_objects = {}
        self.order_by = []

    def set_cdms_known_related_objects(self, cdms_known_related_objects):
        self.cdms_known_related_objects = cdms_known_related_objects

    def set_empty(self):
        self.empty = True

    def add_q(self, q_object):
        clause = self._add_q(q_object)
        if clause:
            self.filters.add(clause, Lookup.AND)

    def _add_q(self, q_object, branch_negated=False, current_negated=False):
        connector = q_object.connector
        current_negated = current_negated ^ q_object.negated
        branch_negated = branch_negated or q_object.negated
        target_clause = FilterNode(connector=connector, negated=q_object.negated)
        for child in q_object.children:
            if isinstance(child, Node):
                child_clause = self._add_q(
                    child, branch_negated,
                    current_negated
                )
            else:
                child_clause = self.build_filter(
                    child, branch_negated=branch_negated,
                    connector=connector,
                    current_negated=current_negated
                )
            if child_clause:
                target_clause.add(child_clause, connector)
        return target_clause

    def solve_lookup_type(self, lookup):
        """
        Solve the lookup type from the lookup (eg: 'foobar__id__icontains')
        """
        lookup_splitted = lookup.split(LOOKUP_SEP)
        _, field, _, lookup_parts = self.names_to_path(lookup_splitted, self.model._meta)

        field_parts = lookup_splitted[0:len(lookup_splitted) - len(lookup_parts)]
        if len(lookup_parts) == 0:
            lookup_parts = ['exact']
        elif len(lookup_parts) > 1:
            if not field_parts:
                raise FieldError(
                    'Invalid lookup "%s" for model %s".' %
                    (lookup, self.model.__name__))
        return lookup_parts, field_parts, False

    def names_to_path(self, names, opts, fail_on_missing=False):
        path = []
        for pos, name in enumerate(names):
            if name == 'pk':
                name = opts.pk.name

            field = None
            try:
                field = opts.get_field(name)
            except FieldDoesNotExist:
                pass

            if field is not None:
                if field.is_relation and not field.related_model:
                    raise NotImplementedError(
                        'Generic relationships not implemented yet'
                    )

                if field.is_relation and not isinstance(field.related_model(), CDMSModel):
                    raise NotImplementedError(
                        'Relations not of type CDMSModel not yet implemented'
                    )

                if field.is_relation and len(names) > 1:
                    # cdms doesn't like 'relatedField/Field' so much but it could potentially
                    # be possible so investigate further if worth.
                    raise NotImplementedError(
                        'Only filtering by foreign key allowed at the moment'
                    )

                try:
                    model = field.model._meta.concrete_model
                except AttributeError:
                    model = None
            else:
                # We didn't find the current field, so move position back
                # one step.
                pos -= 1
                if pos == -1 or fail_on_missing:
                    field_names = list(get_field_names_from_opts(opts))
                    available = sorted(field_names)
                    raise FieldError("Cannot resolve keyword %r into field. "
                                     "Choices are: %s" % (name, ", ".join(available)))
                break

            # Check if we need any joins for concrete inheritance cases (the
            # field lives in parent, but we are currently in one of its
            # children)
            if model is not opts.model:
                raise NotImplementedError(
                    'Proxy objects not yet implemented'
                )

            if hasattr(field, 'get_path_info'):
                pathinfos = field.get_path_info()
                last = pathinfos[-1]
                final_field = last.join_field
                targets = (field,)

                break
            else:
                # Local non-relational field.
                final_field = field
                targets = (field,)
                if fail_on_missing and pos + 1 != len(names):
                    raise FieldError(
                        "Cannot resolve keyword %r into field. Join on '%s'"
                        " not permitted." % (names[pos + 1], name))
                break
        return path, final_field, targets, names[pos + 1:]

    def build_filter(self, filter_expr, branch_negated=False, current_negated=False, connector=None):
        arg, value = filter_expr
        lookups, parts, reffed_expression = self.solve_lookup_type(arg)

        value, lookups = self.prepare_lookup_value(value, lookups)

        if len(lookups) != 1:
            raise NotImplementedError('Only one lookup implemented at the moment')

        if reffed_expression:
            raise NotImplementedError('Reffed expressions not implemented yet')

        _, field, targets, _ = self.names_to_path(
            parts, self.model._meta, fail_on_missing=True
        )

        field_name = field.name
        cdms_field = self.model.cdms_migrator.get_cdms_field(field_name)

        if field.is_relation:
            if not isinstance(value, CDMSModel):
                raise NotImplementedError('Please use an object as value of relation fields')
            cdms_field_name = '{field}/Id'.format(field=cdms_field.cdms_name)
        else:
            cdms_field_name = cdms_field.cdms_name

        return Lookup(cdms_field_name, lookups[0], value)

    def prepare_lookup_value(self, value, lookups):
        # Default lookup if none given is exact.
        if len(lookups) == 0:
            lookups = ['exact']
        # Interpret '__exact=None' as the sql 'is NULL'; otherwise, reject all
        # uses of None as a query value.
        if value is None:
            raise NotImplementedError('Cannot use None as value, not implemented yet')
        elif hasattr(value, 'resolve_expression'):
            raise NotImplementedError('Can only use raw values, anything else has not been implemented yet')

        # Subqueries need to use a different set of aliases than the
        # outer query. Call bump_prefix to change aliases of the inner
        # query (the value).
        if hasattr(value, 'query') and hasattr(value.query, 'bump_prefix'):
            raise NotImplementedError('Can only use raw values, anything else has not been implemented yet')
        if hasattr(value, 'bump_prefix'):
            raise NotImplementedError('Can only use raw values, anything else has not been implemented yet')

        return value, lookups

    def add_ordering(self, *ordering):
        self.order_by.extend(ordering)

    def clear_ordering(self):
        self.order_by = []

    def get_compiler(self):
        return self.compiler(query=self)


class GetQuery(CDMSQuery):
    compiler = CDMSGetCompiler

    def __init__(self, *args, **kwargs):
        super(GetQuery, self).__init__(*args, **kwargs)
        self.cdms_pk = None

    def set_cdms_pk(self, cdms_pk):
        self.cdms_pk = cdms_pk


class InsertQuery(CDMSQuery):
    compiler = CDMSInsertCompiler

    def __init__(self, *args, **kwargs):
        super(InsertQuery, self).__init__(*args, **kwargs)
        self.cdms_data = {}

    def insert_value(self, obj):
        self.cdms_data = self.model.cdms_migrator.update_cdms_data_from_local(obj, {})


class UpdateQuery(CDMSQuery):
    compiler = CDMSUpdateCompiler

    def __init__(self, *args, **kwargs):
        super(UpdateQuery, self).__init__(*args, **kwargs)
        self.cdms_pk = None
        self.cdms_data = {}

    def get_cdms_obj(self):
        query = GetQuery(self.model)
        query.set_cdms_pk(self.cdms_pk)
        return query.get_compiler().execute()

    def add_update_fields(self, cdms_pk, values):
        self.cdms_pk = cdms_pk
        cdms_data = self.get_cdms_obj()
        self.cdms_data = self.model.cdms_migrator.update_cdms_data_from_values(values, cdms_data)


class RefreshQuery(GetQuery):
    compiler = CDMSRefreshCompiler

    def __init__(self, *args, **kwargs):
        super(GetQuery, self).__init__(*args, **kwargs)
        self.local_obj = None
        self.cdms_data = None

    def set_local_obj(self, obj):
        assert not self.cdms_data, \
            "you can either call set_local_obj or set_cdms_data but not both"
        self.set_cdms_pk(obj.cdms_pk)
        self.local_obj = obj

    def set_cdms_data(self, cdms_data):
        assert not self.local_obj, \
            "you can either call set_local_obj or set_cdms_data but not both"
        self.cdms_pk = self.model.cdms_migrator.get_cdms_pk(cdms_data)
        self.cdms_data = cdms_data


class DeleteQuery(GetQuery):
    compiler = CDMSDeleteCompiler
