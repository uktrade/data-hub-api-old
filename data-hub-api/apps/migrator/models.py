from contextlib import ContextDecorator

from django.db import models, transaction

from core.lib_models import TimeStampedModel


class override_skip_cdms(ContextDecorator):
    """
    Context Manager used to temporarily override the _cdms_skip
    class attribute with the `overriding_skip_cdms` given.
    """
    def __init__(self, obj, overriding_skip_cdms):
        self.obj = obj
        self.overriding_skip_cdms = overriding_skip_cdms

    def __enter__(self):
        self.original_skip_cdms = self.obj._cdms_skip
        self.obj._cdms_skip = self.overriding_skip_cdms
        return self

    def __exit__(self, *exc):
        self.obj._cdms_skip = self.original_skip_cdms
        del self.original_skip_cdms
        return False


class CDMSModel(TimeStampedModel):
    cdms_pk = models.CharField(max_length=255, blank=True)

    cdms_migrator = None  # should be subclass of migrator.cdms_migrator.BaseCDMSMigrator

    def __init__(self, *args, **kwargs):
        super(CDMSModel, self).__init__(*args, **kwargs)
        self._cdms_skip = False

    def save(self, *args, **kwargs):
        overriding_skip_cdms = kwargs.pop('skip_cdms', self._cdms_skip)
        with override_skip_cdms(self, overriding_skip_cdms):
            return super(CDMSModel, self).save(*args, **kwargs)

    def _do_insert(self, manager, using, fields, update_pk, raw):
        if self._cdms_skip:
            manager = manager.skip_cdms()
        return super(CDMSModel, self)._do_insert(manager, using, fields, update_pk, raw)

    def _do_update(self, base_qs, using, pk_val, values, update_fields, forced_update):
        """
        This method will try to update the model. If the model was updated (in
        the sense that an update query was done and a matching row was found
        from the DB) the method will return True.

        NOTE: this is copy/paste from Django +
        - cmd_skip if requested
        - call to _update_with_modified instead of _update to make clear that it's a new method not the
            django one
        """
        if self._cdms_skip:
            base_qs = base_qs.skip_cdms()

        filtered = base_qs.filter(pk=pk_val)
        if not values:
            # We can end up here when saving a model in inheritance chain where
            # update_fields doesn't target any field in current model. In that
            # case we just say the update succeeded. Another case ending up here
            # is a model with just PK - in that case check that the PK still
            # exists.
            return update_fields is not None or filtered.exists()
        if self._meta.select_on_save and not forced_update:
            if filtered.exists():
                # It may happen that the object is deleted from the DB right after
                # this check, causing the subsequent UPDATE to return zero matching
                # rows. The same result can occur in some rare cases when the
                # database returns zero despite the UPDATE being executed
                # successfully (a row is matched and updated). In order to
                # distinguish these two cases, the object's existence in the
                # database is again checked for if the UPDATE query returns 0.
                n_records, modified = filtered._update_with_modified(values)
                if modified:
                    self.modified = modified
                return n_records > 0 or filtered.exists()
            else:
                return False

        n_records, modified = filtered._update_with_modified(values)
        if modified:
            self.modified = modified
        return n_records > 0

    def _do_delete_cdms_obj(self):
        """
        Private method which only deletes the cdms object. Not meant to be used publicly.
        """
        from .query import DeleteQuery

        assert self.cdms_pk, \
            "%s object can't be deleted because its cdms_pk attribute is not set." % self._meta.object_name

        query = DeleteQuery(self.__class__)
        query.set_cdms_pk(self.cdms_pk)
        query.get_compiler().execute()

    def delete(self, *args, **kwargs):
        ret = None
        overriding_skip_cdms = kwargs.pop('skip_cdms', self._cdms_skip)
        with override_skip_cdms(self, overriding_skip_cdms):
            with transaction.atomic():
                ret = super(CDMSModel, self).delete(*args, **kwargs)

                if not self._cdms_skip:
                    self._do_delete_cdms_obj()

        return ret

    class Meta:
        abstract = True
