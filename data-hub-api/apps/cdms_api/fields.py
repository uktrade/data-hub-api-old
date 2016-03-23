from django.apps import apps

from .utils import datetime_to_cdms_datetime, cdms_datetime_to_datetime


class BaseField(object):
    def __init__(self, cdms_name):
        self.cdms_name = cdms_name

    def to_cdms_value(self, value):
        return value

    def from_cdms_value(self, value):
        return value


class IntegerField(BaseField):
    pass


class StringField(BaseField):
    def __init__(self, cdms_name, null=False):
        super(StringField, self).__init__(cdms_name)
        self.null = null

    def from_cdms_value(self, value):
        if not self.null and not value:
            return ''
        return value


class BooleanField(BaseField):
    pass


class DateTimeField(BaseField):
    def to_cdms_value(self, value):
        if not value:
            return value
        return datetime_to_cdms_datetime(value)

    def from_cdms_value(self, value):
        if not value:
            return value
        return cdms_datetime_to_datetime(value)


class IdRefField(BaseField):
    def to_cdms_value(self, value):
        if not value:
            return value
        return {'Id': value}

    def from_cdms_value(self, value):
        if not value:
            return value
        return value['Id']


class ForeignKeyField(IdRefField):
    model_cdms_pk_field = 'cdms_pk'

    def __init__(self, cdms_name, fk_model):
        super(ForeignKeyField, self).__init__(cdms_name)
        self.fk_model = fk_model

    def get_model(self):
        return apps.get_model(self.fk_model)

    def to_cdms_value(self, value):
        if not value:
            return value
        return super(ForeignKeyField, self).to_cdms_value(
            getattr(value, self.model_cdms_pk_field)
        )

    def from_cdms_value(self, value):
        if not value:
            return value

        cdms_pk = super(ForeignKeyField, self).from_cdms_value(value)
        return self.get_model()(**{
            self.model_cdms_pk_field: cdms_pk
        })
