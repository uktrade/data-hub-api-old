from cdms_api import fields as cdms_fields

from migrator.cdms_migrator import BaseCDMSMigrator


class InteractionMigrator(BaseCDMSMigrator):
    fields = {
        'first_name': cdms_fields.StringField('FirstName'),
        'last_name': cdms_fields.StringField('LastName'),
        'organisation': cdms_fields.ForeignKeyField(
            'ParentCustomerId',
            fk_model='organisation.Organisation'
        )
    }
    service = 'Contact'


class EmailInteractionMigrator(BaseCDMSMigrator):
    fields = {
        'first_name': cdms_fields.StringField('FirstName'),
        'last_name': cdms_fields.StringField('LastName'),
        'organisation': cdms_fields.ForeignKeyField(
            'ParentCustomerId',
            fk_model='organisation.Organisation'
        )
    }
    service = 'Contact'
