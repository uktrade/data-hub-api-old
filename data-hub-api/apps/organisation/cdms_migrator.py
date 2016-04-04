from cdms_api import fields as cdms_fields

from migrator.cdms_migrator import BaseCDMSMigrator


class OrganisationMigrator(BaseCDMSMigrator):
    fields = {
        'name': cdms_fields.StringField('Name'),
        'alias': cdms_fields.StringField('optevia_Alias'),
        'uk_organisation': cdms_fields.BooleanField('optevia_ukorganisation'),
        'country': cdms_fields.IdRefField('optevia_Country'),
        'postcode': cdms_fields.StringField('optevia_PostCode'),
        'address1': cdms_fields.StringField('optevia_Address1'),
        'city': cdms_fields.StringField('optevia_TownCity'),
        'uk_region': cdms_fields.IdRefField('optevia_UKRegion'),
        'country_code': cdms_fields.StringField('optevia_CountryCode'),
        'area_code': cdms_fields.StringField('optevia_AreaCode'),
        'phone_number': cdms_fields.StringField('optevia_TelephoneNumber'),
        'email_address': cdms_fields.StringField('EMailAddress1'),
        'sector': cdms_fields.IdRefField('optevia_Sector'),
    }
    service = 'Account'

    def update_cdms_data_from_local(self, local_obj, cdms_data):
        """
        Add PAFOverride value to cdms_data.
        """
        cdms_data = super(OrganisationMigrator, self).update_cdms_data_from_local(
            local_obj, cdms_data
        )

        if cdms_data:
            cdms_data['optevia_PAFOverride'] = True
        return cdms_data


class ContactMigrator(BaseCDMSMigrator):
    fields = {
        'first_name': cdms_fields.StringField('FirstName'),
        'last_name': cdms_fields.StringField('LastName'),
        'organisation': cdms_fields.ForeignKeyField(
            'ParentCustomerId',
            fk_model='organisation.Organisation'
        )
    }
    service = 'Contact'
