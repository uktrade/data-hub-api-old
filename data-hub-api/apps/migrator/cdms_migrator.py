from cdms_api.utils import cdms_datetime_to_datetime
from cdms_api import fields as cdms_fields

from .exceptions import NotMappingFieldException, ObjectsNotInSyncException


class BaseCDMSMigrator(object):
    fields = {}
    service = None

    def __init__(self):
        self.all_fields = self.build_filters()

    def build_filters(self):
        all_fields = {
            'modified': cdms_fields.DateTimeField('ModifiedOn')
        }
        all_fields.update(self.fields)
        return all_fields

    def get_cdms_pk(self, cdms_data):
        return cdms_data['{service}Id'.format(service=self.service)]

    def get_modified_on(self, cdms_data):
        return cdms_datetime_to_datetime(cdms_data['ModifiedOn'])

    def clean_up_cdms_data_before_changes(self, data):
        data.pop('optevia_LastVerified', None)
        data.pop('ModifiedOn', None)
        data.pop('CreatedOn', None)
        return data

    def has_cdms_obj_changed(self, local_obj, cdms_data):
        cdms_modified_on = self.get_modified_on(cdms_data)
        cdms_created_on = cdms_datetime_to_datetime(cdms_data['CreatedOn'])

        change_delta = (cdms_modified_on - local_obj.modified).total_seconds()

        if change_delta < 0:
            raise ObjectsNotInSyncException(
                'Django Model changed without being syncronised to CDMS, this should not happen'
            )

        return change_delta, cdms_modified_on, cdms_created_on

    def get_cdms_field(self, field_name):
        cdms_field = self.all_fields.get(field_name)
        if not cdms_field:
            raise NotMappingFieldException(
                'No mapping found for field {field}'.format(field=field_name)
            )

        return cdms_field

    def update_cdms_data_from_local(self, local_obj, cdms_data):
        values = [
            (field.name, getattr(local_obj, field.name)) for field in local_obj._meta.fields
        ]
        return self.update_cdms_data_from_values(values, cdms_data)

    def update_cdms_data_from_values(self, values, cdms_data):
        for field_name, value in values:
            try:
                cdms_field = self.get_cdms_field(field_name)
            except NotMappingFieldException:
                continue

            value = cdms_field.to_cdms_value(value)
            cdms_data[cdms_field.cdms_name] = value
        return cdms_data

    def update_local_from_cdms_data(self, local_obj, cdms_data, cdms_known_related_objects={}):
        for field in local_obj._meta.fields:
            field_name = field.name
            try:
                cdms_field = self.get_cdms_field(field_name)
            except NotMappingFieldException:
                continue

            value = cdms_field.from_cdms_value(cdms_data[cdms_field.cdms_name])
            if field_name in cdms_known_related_objects:
                related_obj = cdms_known_related_objects.get(field_name, {}).get(value.cdms_pk)

                if related_obj:
                    value = related_obj

            setattr(local_obj, field_name, value)

        return local_obj

    def get_conflicting_fields(self, local_obj, cdms_data):
        """
        Returns the list of fields conflicting between local_obj and cdms_data.
        """
        conflicting_fields = {}
        for field in local_obj._meta.fields:
            field_name = field.name
            try:
                cdms_field = self.get_cdms_field(field_name)
            except NotMappingFieldException:
                continue

            cdms_value = cdms_field.from_cdms_value(cdms_data[cdms_field.cdms_name])
            local_value = getattr(local_obj, field_name)

            if cdms_value != local_value:
                conflicting_fields[field_name] = {
                    'theirs': cdms_value,
                    'yours': local_value
                }
        return conflicting_fields
