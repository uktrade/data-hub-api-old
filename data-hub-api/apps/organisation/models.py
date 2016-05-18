from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.urlresolvers import reverse

from reversion import revisions as reversion

from core.models import CRMBaseModel
from core.managers import CRMManager
from core.fields import UKTIForeignKey
from core.lib_models import TimeStampedModel

from .cdms_migrator import OrganisationMigrator, ContactMigrator
from . import constants


class CHOrganisation(TimeStampedModel):
    number = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=500)
    source = models.CharField(max_length=10, choices=constants.CH_SOURCES)
    raw = JSONField()

    def __str__(self):
        return '#{} - {} from {}'.format(self.number, self.name, self.source)


@reversion.register()
class Organisation(CRMBaseModel):
    name = models.CharField(max_length=1000)
    alias = models.CharField(max_length=1200, blank=True)
    local_name = models.CharField(max_length=1200, blank=True)

    product_description = models.CharField(max_length=20000, blank=True)
    description = models.CharField(max_length=20000, blank=True)

    sector = models.CharField(
        max_length=255, null=True, blank=True,
        choices=constants.SECTOR_CHOICES
    )
    uk_region = models.CharField(
        max_length=255,
        blank=True, null=True,
        choices=constants.UK_REGION_CHOICES
    )
    investment_experience = models.CharField(
        max_length=255, null=True, blank=True,
        choices=constants.INVESTMENT_EXPERIENCE_CHOICES
    )
    export_experience = models.CharField(
        max_length=255, null=True, blank=True,
        choices=constants.EXPORT_EXPERIENCE_CHOICES
    )

    export_experience = models.CharField(
        max_length=255, null=True, blank=True,
        choices=constants.EXPORT_EXPERIENCE_CHOICES
    )
    business_type = models.CharField(
        max_length=255,
        blank=True, null=True,
        choices=constants.BUSINESS_TYPE_CHOICES
    )

    address1 = models.CharField(max_length=1200, blank=True)
    address1_name = models.CharField(max_length=1200, blank=True)
    address1_county = models.CharField(max_length=1200, blank=True)
    address1_fax = models.CharField(max_length=1200, blank=True)
    address1_post_office_box = models.CharField(max_length=1200, blank=True)
    address1_telephone2 = models.CharField(max_length=1200, blank=True)
    address1_primary_contact_name = models.CharField(max_length=1200, blank=True)
    address1_ups_zone = models.CharField(max_length=1200, blank=True)
    address1_postal_code = models.CharField(max_length=1200, blank=True)
    address1_telephone1 = models.CharField(max_length=1200, blank=True)
    address1_state_or_province = models.CharField(max_length=1200, blank=True)
    address1_line1 = models.CharField(max_length=1200, blank=True)
    address1_utc_offset = models.IntegerField(null=True, blank=True)
    address1_country = models.CharField(max_length=1200, blank=True)
    address1_line3 = models.CharField(max_length=1200, blank=True)
    address1_city = models.CharField(max_length=1200, blank=True)
    address1_line2 = models.CharField(max_length=1200, blank=True)
    address1_telephone3 = models.CharField(max_length=1200, blank=True)
    address1_freight_terms_code = models.CharField(max_length=1200, blank=True, null=True)
    address1_shipping_method_code = models.IntegerField(null=True, blank=True)  # not sure what this is
    address1_address_type_code = models.IntegerField(null=True, blank=True)  # not sure what this is
    address1_latitude = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=10)
    address1_longitude = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=10)
    address1_address_cdms_pk = models.CharField(max_length=1200, blank=True, null=True)  # should be fk to address

    address2 = models.CharField(max_length=1200, blank=True)
    address2_line1 = models.CharField(max_length=1200, blank=True)
    address2_telephone1 = models.CharField(max_length=1200, blank=True)
    address2_city = models.CharField(max_length=1200, blank=True)
    address2_postal_code = models.CharField(max_length=1200, blank=True)
    address2_name = models.CharField(max_length=1200, blank=True)
    address2_line3 = models.CharField(max_length=1200, blank=True)
    address2_county = models.CharField(max_length=1200, blank=True)
    address2_telephone3 = models.CharField(max_length=1200, blank=True)
    address2_post_office_box = models.CharField(max_length=1200, blank=True)
    address2_ups_zone = models.CharField(max_length=1200, blank=True)
    address2_country = models.CharField(max_length=1200, blank=True)
    address2_line2 = models.CharField(max_length=1200, blank=True)
    address2_telephone2 = models.CharField(max_length=1200, blank=True)
    address2_fax = models.CharField(max_length=1200, blank=True)
    address2_primary_contact_name = models.CharField(max_length=1200, blank=True)
    address2_utc_offset = models.IntegerField(null=True, blank=True)
    address2_state_or_province = models.CharField(max_length=1200, blank=True)
    address2_freight_terms_code = models.CharField(max_length=1200, blank=True, null=True)
    address2_shipping_method_code = models.IntegerField(null=True, blank=True)  # not sure what this is
    address2_address_type_code = models.IntegerField(null=True, blank=True)  # not sure what this is
    address2_latitude = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=10)
    address2_longitude = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=10)
    address2_address_cdms_pk = models.CharField(max_length=1200, blank=True, null=True)  # should be fk to address

    address3 = models.CharField(max_length=1200, blank=True)
    address4 = models.CharField(max_length=1200, blank=True)

    address_type = models.CharField(
        max_length=255,
        blank=True, null=True,
        choices=constants.ADDRESS_TYPE_CHOICES
    )
    address_comment = models.CharField(max_length=1200, blank=True)
    local_language_address = models.CharField(max_length=1200, blank=True)
    og_address_id = models.CharField(max_length=1200, blank=True)
    temp_address = models.CharField(max_length=1200, blank=True)
    extra_address_ref = models.CharField(max_length=1200, blank=True)
    concatenated_address = models.CharField(max_length=1200, blank=True)
    complete_address = models.CharField(max_length=1200, blank=True)
    townCity = models.CharField(max_length=1200, blank=True)
    city = models.CharField(max_length=1200, blank=True)
    telephone1 = models.CharField(max_length=1200, blank=True)
    telephone2 = models.CharField(max_length=1200, blank=True)
    telephone3 = models.CharField(max_length=1200, blank=True)
    full_telephone_number = models.CharField(max_length=1200, blank=True)
    telephone_number = models.CharField(max_length=1200, blank=True)
    og_telephone_id = models.CharField(max_length=1200, blank=True)
    fax = models.CharField(max_length=1200, blank=True)
    area_code = models.CharField(max_length=1200, blank=True)
    country_code = models.CharField(max_length=1200, blank=True)
    postcode = models.CharField(max_length=500)
    state_county = models.CharField(max_length=1200, blank=True)
    shipping_method_code = models.IntegerField(null=True, blank=True)  # not sure what this is
    country = models.CharField(
        max_length=255,
        blank=True, null=True,
        choices=constants.COUNTRY_CHOICES
    )

    email_address_type = models.CharField(
        max_length=255,
        blank=True, null=True,
        choices=constants.EMAIL_ADDRESS_TYPE_CHOICES
    )
    email_address1 = models.CharField(max_length=1200, blank=True)
    email_address2 = models.CharField(max_length=1200, blank=True)
    email_address3 = models.CharField(max_length=1200, blank=True)
    og_email_address_id = models.CharField(max_length=1200, blank=True)

    do_not_bulk_postal_mail = models.BooleanField(default=False)
    do_not_postal_mail = models.BooleanField(default=False)
    do_not_bulk_email = models.BooleanField(default=False)
    do_not_phone = models.BooleanField(default=False)
    do_not_fax = models.BooleanField(default=False)
    do_not_email = models.BooleanField(default=False)
    do_not_send_mm = models.BooleanField(default=False)

    twitter = models.CharField(max_length=1200, blank=True)
    website_url = models.CharField(max_length=1200, blank=True)
    linkedin = models.CharField(max_length=1200, blank=True)
    yomi_name = models.CharField(max_length=1200, blank=True)
    ftp_site_url = models.CharField(max_length=1200, blank=True)

    territory_code = models.IntegerField(null=True, blank=True)  # not sure what this is
    companies_house_status = models.CharField(
        max_length=1200, null=True, blank=True,
        choices=constants.COMPANIES_HOUSE_STATUS_CHOICES
    )
    last_used_in_campaign = models.DateTimeField(null=True, blank=True)
    timezone_rule_version_number = models.IntegerField(null=True, blank=True)
    overridden_created_on = models.DateTimeField(null=True, blank=True)
    vat_number = models.CharField(max_length=1200, blank=True)
    ownership_code = models.CharField(max_length=1200, null=True, blank=True)  # not sure what this is
    customer_size_code = models.IntegerField(null=True, blank=True)  # not sure what this is
    balance_sheet = models.CharField(max_length=1200, blank=True)
    version_number = models.IntegerField(null=True, blank=True)
    opt_number_of_employees = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=10)
    exchange_rate = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=10)
    revision = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=10)
    local_language_postcode = models.CharField(max_length=1200, blank=True)
    extension = models.CharField(max_length=1200, blank=True)
    merged = models.BooleanField(default=False)
    parent_owned = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=10)
    og_organization_id = models.CharField(max_length=1200, blank=True)
    companies_house_number = models.CharField(max_length=255, blank=True)
    ticker_symbol = models.CharField(max_length=1200, blank=True)
    sic = models.CharField(max_length=1200, blank=True)
    ukti_registration_number = models.CharField(max_length=1200, blank=True)
    organisation_size_year = models.CharField(max_length=1200, blank=True)
    extra_telephone_ref = models.CharField(max_length=1200, blank=True)
    utc_conversion_timezone_code = models.IntegerField(null=True, blank=True)
    last_verified = models.DateTimeField(null=True, blank=True)
    number_of_employees = models.IntegerField(null=True, blank=True)
    balance_sheet_year = models.CharField(max_length=1200, blank=True)
    participates_in_workflow = models.BooleanField(default=False)
    reference_code = models.CharField(max_length=1200, blank=True)
    comments = models.CharField(max_length=20000, blank=True)
    organisation_sector_ref = models.CharField(max_length=1200, blank=True)
    credit_on_hold = models.BooleanField(default=False)
    created_on = models.DateTimeField(null=True, blank=True)
    source_obsolete = models.IntegerField(null=True, blank=True)
    extra_email_ref = models.CharField(max_length=1200, blank=True)
    account_number = models.CharField(max_length=1200, blank=True)
    stopflag = models.BooleanField(default=False)
    uk_organisation = models.BooleanField(default=True)
    og_modified_by = models.CharField(max_length=1200, blank=True)
    stock_exchange = models.CharField(max_length=1200, blank=True)
    og_created = models.DateTimeField(null=True, blank=True)
    shares_outstanding = models.IntegerField(null=True, blank=True)
    paf_override = models.BooleanField(default=True)
    modified_on = models.DateTimeField(null=True, blank=True)
    import_sequence_number = models.IntegerField(null=True, blank=True)

    credit_limit = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=4)
    credit_limit_base = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=4)
    aging_90 = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=4)
    aging_90_base = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=4)
    aging_60 = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=4)
    aging_60_base = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=4)
    aging_30 = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=4)
    aging_30_base = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=4)
    revenue = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=4)
    revenue_base = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=4)
    market_cap = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=4)
    market_cap_base = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=4)
    turnover = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=4)
    turnover_base = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=4)

    owning_business_unit = models.CharField(
        max_length=255, null=True, blank=True,
        choices=constants.BUSINESS_UNIT_CHOICES
    )

    location_type = models.CharField(
        max_length=255, null=True, blank=True,
        choices=constants.LOCATION_TYPE_CHOICES
    )

    preferred_appointment_day_code = models.CharField(max_length=1200, null=True, blank=True)  # not sure what this is
    payment_terms_code = models.CharField(max_length=1200, null=True, blank=True)  # not sure what this is

    status_code = models.IntegerField(null=True, blank=True)  # not sure what this is
    industry_code = models.CharField(max_length=1200, null=True, blank=True)  # not sure what this is
    database_source = models.CharField(max_length=1200, null=True, blank=True)  # should always be null
    preferred_appointment_time_code = models.CharField(max_length=1200, null=True, blank=True)  # not sure what this is
    preferred_contact_method_code = models.CharField(max_length=1200, null=True, blank=True)  # not sure what this is
    business_type_code = models.IntegerField(null=True, blank=True)  # not sure what this is
    account_classification_code = models.IntegerField(null=True, blank=True)  # not sure what this is
    account_category_code = models.IntegerField(null=True, blank=True)  # not sure what this is
    state_code = models.IntegerField(null=True, blank=True)  # not sure what this is
    customer_type_code = models.IntegerField(null=True, blank=True)  # not sure what this is
    account_rating_code = models.IntegerField(null=True, blank=True)  # not sure what this is

    sector_nature_of_interest = models.CharField(
        max_length=255,
        blank=True, null=True,
        choices=constants.SECTOR_NATURE_OF_INTEREST_CHOICES
    )

    employee_range = models.CharField(
        max_length=255,
        blank=True, null=True,
        choices=constants.EMPLOYEE_RANGE_CHOICES
    )

    account_classification = models.CharField(
        max_length=255,
        blank=True, null=True,
        choices=constants.ACCOUNT_CLASSIFICATION_CHOICES
    )

    turnover_range = models.CharField(
        max_length=255,
        blank=True, null=True,
        choices=constants.TURNOVER_RANGE_CHOICES
    )

    telephone_type = models.CharField(
        max_length=255,
        blank=True, null=True,
        choices=constants.TELEPHONE_TYPE_CHOICES
    )

    balance_sheet_range = models.CharField(
        max_length=255,
        blank=True, null=True,
        choices=constants.BALANCE_SHEET_RANGE_CHOICES
    )

    organisation_size = models.CharField(
        max_length=255,
        blank=True, null=True,
        choices=constants.ORGANISATION_SIZE_CHOICES
    )

    transaction_currency_id = models.CharField(
        max_length=255,
        blank=True, null=True,
        choices=constants.TRANSACTION_CURRENCY_CHOICES
    )

    master_cdms_pk = models.CharField(max_length=1200, blank=True, null=True)  # ref to master (for duplicates)
    parent_cdms_pk = models.CharField(max_length=1200, blank=True, null=True)  # ref to parent
    preferred_equipment_id = models.CharField(max_length=1200, blank=True, null=True)  # always None
    territory_id = models.CharField(max_length=1200, blank=True, null=True)  # always None
    preferred_service_id = models.CharField(max_length=1200, blank=True, null=True)  # always None
    default_price_level_id = models.CharField(max_length=1200, blank=True, null=True)  # always None
    preferred_system_user_id = models.CharField(max_length=1200, blank=True, null=True)  # always None
    owning_team = models.CharField(max_length=1200, blank=True, null=True)  # always None
    originating_lead_id = models.CharField(max_length=1200, blank=True, null=True)  # always None

    primary_contact_cdms_pk = models.CharField(max_length=1200, blank=True, null=True)  # should be fk to contact
    owner_id = models.CharField(max_length=1200, blank=True, null=True)  # should be fk to ...

    og_modified = models.DateTimeField(null=True, blank=True)
    og_created_by = models.CharField(max_length=1200, blank=True)
    owning_user = models.CharField(max_length=1200, blank=True, null=True)
    created_on_behalf_by = models.CharField(max_length=1200, blank=True, null=True)
    created_by = models.CharField(max_length=1200, blank=True, null=True)
    modified_by = models.CharField(max_length=1200, blank=True, null=True)
    modified_on_behalf_by = models.CharField(max_length=1200, blank=True, null=True)

    verified_ch_data = models.ForeignKey(CHOrganisation, null=True, blank=True)
    last_checked = models.DateTimeField(null=True, blank=True)

    objects = CRMManager()
    cdms_migrator = OrganisationMigrator()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('organisation:update', args=[str(self.id)])


@reversion.register()
class Contact(CRMBaseModel):
    organisation = UKTIForeignKey(Organisation)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    objects = CRMManager()
    cdms_migrator = ContactMigrator()

    def __str(self):
        return '{first} {second}'.format(
            first=self.first_name,
            last=self.last_name
        )
