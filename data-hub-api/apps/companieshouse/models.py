from django.db import models
from django.contrib.postgres.fields import JSONField

from django_countries.fields import CountryField

from core.lib_models import TimeStampedModel

from . import constants
from .managers import CompanyManager


class Company(TimeStampedModel):
    name = models.CharField(max_length=200)
    number = models.CharField(max_length=10, primary_key=True)

    address_line1 = models.CharField(max_length=500, blank=True)
    address_line2 = models.CharField(max_length=500, blank=True)
    postcode = models.CharField(max_length=20, blank=True)
    region = models.CharField(max_length=100, blank=True)
    locality = models.CharField(max_length=100, blank=True)
    country = CountryField(blank=True)

    company_type = models.CharField(
        max_length=50, choices=constants.COMPANY_TYPES, null=True
    )
    status = models.CharField(
        max_length=150, choices=constants.COMPANY_STATUSES, blank=True
    )

    date_of_creation = models.DateField(null=True)
    date_of_dissolution = models.DateField(null=True)

    raw = JSONField()

    objects = CompanyManager()

    def __str__(self):
        return '#{} - {}'.format(self.number, self.name)


class CompanySicCode(TimeStampedModel):
    code = models.CharField(max_length=10)
    company = models.ForeignKey(Company)

    def __str__(self):
        return 'Sic code {} for company {}'.format(self.code, self.company)


class CompanyPreviousName(TimeStampedModel):
    change_date = models.DateField()
    name = models.CharField(max_length=200)
    company = models.ForeignKey(Company)

    def __str__(self):
        return 'Previous name {} for company {}'.format(self.name, self.company)
