from django.db import models, connections
from django.db.models.query_utils import Q

from django.core.exceptions import ObjectDoesNotExist

from cdms_api.exceptions import CDMSNotFoundException

from .decorators import only_with_cdms_skip
from .query import CDMSQuery, CDMSModelIterable, RefreshQuery, \
    InsertQuery, UpdateQuery


class CDMSQuerySet(models.QuerySet):
    def __init__(self, model=None, query=None, using=None, hints=None):
        super(CDMSQuerySet, self).__init__(model=model, query=query, using=using, hints=hints)
        self.cdms_skip = False

        self.cdms_query = CDMSQuery(model)
        self._cdms_known_related_objects = {}  # {rel_field_name, {cdms_pk: rel_obj}}
        self._iterable_class = CDMSModelIterable

    def skip_cdms(self):
        self.cdms_skip = True
        return self

    def _clone(self, **kwargs):
        clone = super(CDMSQuerySet, self)._clone(**kwargs)
        clone.cdms_query = self.cdms_query  # we might need to clone this
        clone.cdms_skip = self.cdms_skip

        clone._cdms_known_related_objects = self._cdms_known_related_objects
        return clone

    def none(self):
        self.cdms_query.set_empty()
        return super(CDMSQuerySet, self).none()

    def get(self, *args, **kwargs):
        original_cdms_skip = self.cdms_skip
        self.cdms_skip = True
        try:
            obj = super(CDMSQuerySet, self).get(*args, **kwargs)

            if not original_cdms_skip:
                # get cdms object
                query = RefreshQuery(self.model)
                query.set_local_obj(obj)
                obj = query.get_compiler().execute()
        except ObjectDoesNotExist as e:
            # if not cdms_skip and get(cdms_pk=...), try to get the obj from cdms instead
            cdms_pk = kwargs.get('cdms_pk')
            if not original_cdms_skip and len(kwargs) == 1 and cdms_pk:
                try:
                    # get cdms object
                    query = RefreshQuery(self.model)
                    query.set_cdms_pk(cdms_pk)

                    obj = query.get_compiler().execute()
                except CDMSNotFoundException:
                    raise e
            else:
                raise e
        finally:
            # restore old setting
            self.cdms_skip = original_cdms_skip
        return obj

    def create(self, **kwargs):
        """
        Creates a new object with the given kwargs, saving it to the database
        and returning the created object.
        """
        obj = self.model(**kwargs)
        self._for_write = True
        obj.save(force_insert=True, using=self.db, skip_cdms=self.cdms_skip)
        return obj

    def order_by(self, *field_names):
        ret = super(CDMSQuerySet, self).order_by(*field_names)

        if not self.cdms_skip:
            ret.cdms_query.clear_ordering()
            ret.cdms_query.add_ordering(*field_names)

        return ret

    def _is_q_pk_only(self, q):
        """
        Returns True if the Q object is simply filtering by 'id' or 'pk' and no other field.
        """
        if not isinstance(q, Q):
            return q[0] in ('id', 'pk')
        if len(q) != 1 or len(q.children) != 1:
            return False
        return self._is_q_pk_only(q.children[0])

    def _filter_or_exclude(self, negate, *args, **kwargs):
        if not self.cdms_skip:
            if args or kwargs:
                assert self.query.can_filter(), \
                    "Cannot filter a query once a slice has been taken."

            if not args and not kwargs:
                if not self.query.has_filters():
                    raise NotImplementedError(
                        'Cannot yet get all objects, not implemented yet'
                    )

            q = Q(*args, **kwargs)

            if not self._is_q_pk_only(q):
                clone = self._clone()

                if negate:
                    clone.query.add_q(~q)
                    clone.cdms_query.add_q(~q)
                else:
                    clone.query.add_q(q)
                    clone.cdms_query.add_q(q)
        return super(CDMSQuerySet, self)._filter_or_exclude(negate, *args, **kwargs)

    def _batched_insert(self, objs, fields, batch_size):
        """
        Django private method.
        Overridden in order to set the cdms_skip flag if necessary.
        """
        if not objs:
            return
        ops = connections[self.db].ops
        batch_size = (batch_size or max(ops.bulk_batch_size(fields, objs), 1))
        batches = [objs[i:i + batch_size] for i in range(0, len(objs), batch_size)]
        for batch in batches:
            mngr = self.model._base_manager
            if self.cdms_skip:
                mngr = mngr.skip_cdms()

            mngr._insert(
                batch, fields=fields, using=self.db
            )

    def _insert(self, objs, fields, return_id=False, raw=False, using=None):
        return_val = super(CDMSQuerySet, self)._insert(objs, fields, return_id=return_id, raw=raw, using=using)

        if not self.cdms_skip:
            if not return_id or len(objs) > 1:
                raise NotImplementedError(
                    'Bulk create not implemented yet'
                )

            # insert in cdms
            obj = objs[0]
            query = InsertQuery(self.model)
            query.insert_value(obj)
            cdms_pk, modified_on = query.get_compiler().execute()

            # update cdms_pk local
            obj.cdms_pk = cdms_pk
            obj.modified = modified_on
            self._clone().skip_cdms().filter(pk=return_val).update(
                cdms_pk=cdms_pk, modified=modified_on
            )

        return return_val

    def _update(self, values):
        raise NotImplementedError()

    def _update_with_modified(self, values):
        """
        The same as _update but returns the modified_on date from cdms as well if the update
        happened. I preferred not to override _update as I'm changing the return values from int to tuple (int, dt).

        This is not ideal but we need to update the model based on the new modified_on value and Django really
        doesn't help you in this case.
        """
        modified_on = None
        return_val = super(CDMSQuerySet, self)._update(values)

        if not self.cdms_skip:
            model_values = []
            cdms_pk = None
            for field, _, value in values:
                if field.name == 'cdms_pk':
                    cdms_pk = value
                else:
                    model_values.append(
                        (field.name, value)
                    )

            assert cdms_pk, 'Cannot update without cdms pk'

            query = UpdateQuery(self.model)
            query.add_update_fields(cdms_pk, model_values)
            modified_on = query.get_compiler().execute()

            super(CDMSQuerySet, self)._update([
                (self.model._meta.get_field('modified'), None, modified_on)
            ])

        return return_val, modified_on

    @only_with_cdms_skip
    def annotate(self, *args, **kwargs):
        return super(CDMSQuerySet, self).annotate(*args, **kwargs)

    @only_with_cdms_skip
    def reverse(self, *args, **kwargs):
        return super(CDMSQuerySet, self).reverse(*args, **kwargs)

    @only_with_cdms_skip
    def select_for_update(self, *args, **kwargs):
        return super(CDMSQuerySet, self).select_for_update(*args, **kwargs)

    @only_with_cdms_skip
    def distinct(self, *args, **kwargs):
        return super(CDMSQuerySet, self).distinct(*args, **kwargs)

    @only_with_cdms_skip
    def values(self, *args, **kwargs):
        return super(CDMSQuerySet, self).values(*args, **kwargs)

    @only_with_cdms_skip
    def values_list(self, *args, **kwargs):
        return super(CDMSQuerySet, self).values_list(*args, **kwargs)

    @only_with_cdms_skip
    def select_related(self, *args, **kwargs):
        return super(CDMSQuerySet, self).select_related(*args, **kwargs)

    def prefetch_related(self, *args, **kwargs):
        """
        Technically possible to implement in cdms_skip mode but not as easy as I would have expected so not worth it.
        """
        raise NotImplementedError()

    @only_with_cdms_skip
    def extra(self, *args, **kwargs):
        return super(CDMSQuerySet, self).extra(*args, **kwargs)

    @only_with_cdms_skip
    def defer(self, *args, **kwargs):
        return super(CDMSQuerySet, self).defer(*args, **kwargs)

    @only_with_cdms_skip
    def only(self, *args, **kwargs):
        return super(CDMSQuerySet, self).only(*args, **kwargs)

    @only_with_cdms_skip
    def raw(self, *args, **kwargs):
        return super(CDMSQuerySet, self).raw(*args, **kwargs)

    @only_with_cdms_skip
    def get_or_create(self, *args, **kwargs):
        return super(CDMSQuerySet, self).get_or_create(*args, **kwargs)

    @only_with_cdms_skip
    def update_or_create(self, *args, **kwargs):
        return super(CDMSQuerySet, self).update_or_create(*args, **kwargs)

    @only_with_cdms_skip
    def count(self, *args, **kwargs):
        return super(CDMSQuerySet, self).count(*args, **kwargs)

    @only_with_cdms_skip
    def in_bulk(self, *args, **kwargs):
        return super(CDMSQuerySet, self).in_bulk(*args, **kwargs)

    @only_with_cdms_skip
    def earliest(self, *args, **kwargs):
        return super(CDMSQuerySet, self).earliest(*args, **kwargs)

    @only_with_cdms_skip
    def latest(self, *args, **kwargs):
        return super(CDMSQuerySet, self).latest(*args, **kwargs)

    @only_with_cdms_skip
    def first(self, *args, **kwargs):
        return super(CDMSQuerySet, self).first(*args, **kwargs)

    @only_with_cdms_skip
    def last(self, *args, **kwargs):
        return super(CDMSQuerySet, self).last(*args, **kwargs)

    @only_with_cdms_skip
    def aggregate(self, *args, **kwargs):
        return super(CDMSQuerySet, self).aggregate(*args, **kwargs)

    @only_with_cdms_skip
    def exists(self, *args, **kwargs):
        return super(CDMSQuerySet, self).exists(*args, **kwargs)

    @only_with_cdms_skip
    def bulk_create(self, *args, **kwargs):
        return super(CDMSQuerySet, self).bulk_create(*args, **kwargs)

    @only_with_cdms_skip
    def update(self, *args, **kwargs):
        return super(CDMSQuerySet, self).update(*args, **kwargs)

    @only_with_cdms_skip
    def delete(self, *args, **kwargs):
        return super(CDMSQuerySet, self).delete(*args, **kwargs)


class CDMSManager(models.Manager.from_queryset(CDMSQuerySet)):
    pass
