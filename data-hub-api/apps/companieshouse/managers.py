from django.db import models
from companieshouse.utils import clean_country


class CompanyManager(models.Manager):
    def update_from_CH_data(self, ch_data, company=None):
        """
        Updates the `company` object from the CH record represented by `ch_data`.
        If `company` is None, it'll get the object from the db if it exists or create a fresh one otherwise.

        The format of `ch_data` should be as similar as the official one as possible:
        https://developer.companieshouse.gov.uk/api/docs/company/company_number/companyProfile-resource.html
        """
        if not company:
            try:
                company = self.get(number=ch_data['company_number'])
            except self.model.DoesNotExist:
                company = self.model()
        to_create = not company.name  # this optimises the query a bit

        company.number = ch_data['company_number']
        company.name = ch_data['company_name']

        registered_office_address = ch_data.get('registered_office_address', {})
        company.address_line1 = registered_office_address.get('address_line_1', '')
        company.address_line2 = registered_office_address.get('address_line_2', '')
        company.postcode = registered_office_address.get('postal_code', '')
        company.region = registered_office_address.get('region', '')
        company.locality = registered_office_address.get('locality', '')
        company.country = clean_country(ch_data.get('country_of_origin')) or ''

        company.company_type = ch_data['type']
        company.status = ch_data['company_status']

        company.date_of_creation = ch_data.get('date_of_creation')
        company.date_of_dissolution = ch_data.get('date_of_dissolution')

        company.raw = ch_data

        company.save(force_insert=to_create, force_update=(not to_create))

        # sic codes
        existing_sic_codes = sorted(list(company.companysiccode_set.values_list('code', flat=True)))
        sic_codes = sorted(ch_data.get('sic_codes') or [])

        if existing_sic_codes != sic_codes:  # different => delete and re-add
            company.companysiccode_set.all().delete()
            for sic_code in sic_codes:
                company.companysiccode_set.create(code=sic_code)

        # previous names
        existing_previous_names = sorted(list(company.companypreviousname_set.values_list('name', flat=True)))
        previous_names = sorted([name_data['company_name'] for name_data in (ch_data.get('previous_names', ) or [])])

        # different => delete and re-add
        if existing_previous_names != previous_names:
            company.companypreviousname_set.all().delete()
            for name_data in (ch_data.get('previous_names') or []):
                company.companypreviousname_set.create(
                    change_date=name_data['date'],
                    name=name_data['company_name']
                )

        return company
