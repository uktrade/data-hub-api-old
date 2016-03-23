from django.db import models
from django.utils.timezone import now

from migrator.fields import CDMSForeignKey


class UKTIForeignKey(CDMSForeignKey):
    pass


def now_without_millisecs(*args, **kwargs):
    return now(*args, **kwargs).replace(microsecond=0)


class AutoCreatedField(models.DateTimeField):
    """
    A DateTimeField that automatically populates itself at object creation.
    By default, sets editable=False, default=datetime.now and without microseconds
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('editable', False)
        kwargs.setdefault('default', now_without_millisecs)
        super(AutoCreatedField, self).__init__(*args, **kwargs)


class AutoLastModifiedField(AutoCreatedField):
    """
    A DateTimeField that updates itself on each save() of the model.
    By default, sets editable=False and default=datetime.now and without microseconds
    """

    def pre_save(self, model_instance, add):
        value = now_without_millisecs()
        setattr(model_instance, self.attname, value)
        return value
