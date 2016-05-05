from cdms_api import fields as cdms_fields

from migrator.cdms_migrator import BaseCDMSMigrator


class InteractionMigrator(BaseCDMSMigrator):
    service = 'ActivityPointer'


class EmailInteractionMigrator(BaseCDMSMigrator):
    fields = {
        'sender_address': cdms_fields.StringField('Sender'),
        'receiver_address': cdms_fields.StringField('ToRecipients'),
        'message_id': cdms_fields.StringField('MessageId'),
        'subject': cdms_fields.StringField('Subject'),
        'organisation': cdms_fields.ForeignKeyField(
            'ParentCustomerId',
            fk_model='organisation.Organisation'
        )
    }
    service = 'Email'

    def update_cdms_data_from_values(self, values, cdms_data):
        r = super(EmailInteractionMigrator, self).update_cdms_data_from_values(values, cdms_data)
        r["ActivityTypeCode"] = "Email"
        return r
