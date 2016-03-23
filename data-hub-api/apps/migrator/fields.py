from django.utils.functional import cached_property
from django.db.models.fields.related import ForeignKey
from django.db.models.fields.related_descriptors import ReverseManyToOneDescriptor, \
    create_reverse_many_to_one_manager


def create_reverse_cdms_many_to_one_manager(superclass, rel):
    subclass = create_reverse_many_to_one_manager(
        superclass, rel
    )

    class RelatedManager(subclass):
        def __init__(self, *args, **kwargs):
            super(RelatedManager, self).__init__(*args, **kwargs)
            self.cdms_skip = False

        def __call__(self, **kwargs):
            # We use **kwargs rather than a kwarg argument to enforce the
            # `manager='manager_name'` syntax.
            manager = getattr(self.model, kwargs.pop('manager'))
            manager_class = create_reverse_cdms_many_to_one_manager(manager.__class__, rel)
            return manager_class(self.instance)
        do_not_call_in_templates = True

        def skip_cdms(self):
            """
            Needs to be redefined because of Django madness :-|
            """
            self.cdms_skip = True
            return self

        def get_queryset(self):
            qs = super(RelatedManager, self).get_queryset()

            qs.cdms_skip = self.cdms_skip
            qs._cdms_known_related_objects = {self.field.name: {self.instance.cdms_pk: self.instance}}
            return qs

        def add(self, *args, **kwargs):
            raise NotImplementedError()

        def create(self, *args, **kwargs):
            raise NotImplementedError()

        def get_or_create(self, *args, **kwargs):
            raise NotImplementedError()

        def update_or_create(self, *args, **kwargs):
            raise NotImplementedError()

        def remove(self, *args, **kwargs):
            raise NotImplementedError()

        def clear(self, *args, **kwargs):
            raise NotImplementedError()

    return RelatedManager


class ReverseManyToOneDescriptor(ReverseManyToOneDescriptor):
    @cached_property
    def related_manager_cls(self):
        return create_reverse_cdms_many_to_one_manager(
            self.rel.related_model._default_manager.__class__,
            self.rel,
        )


class CDMSForeignKey(ForeignKey):
    related_accessor_class = ReverseManyToOneDescriptor
