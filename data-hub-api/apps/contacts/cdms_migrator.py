from cdms_api import fields as cdms_fields

from migrator.cdms_migrator import BaseCDMSMigrator


class ContactMigrator(BaseCDMSMigrator):
    fields = {
        'first_name': cdms_fields.StringField('FirstName'),
        'last_name': cdms_fields.StringField('LastName')
    }
    service = 'Contact'
