from django.db import models
from django.core.urlresolvers import reverse

from core.models import CRMBaseModel
from core.managers import CRMManager
from core.fields import UKTIForeignKey

from .cdms_migrator import OrganisationMigrator, ContactMigrator


COUNTRY_CHOICES = (
    ('80756b9a-5d95-e211-a939-e4115bead28a', 'United Kingdom'),
)

UK_REGION_CHOICES = (
    ('874cd12a-6095-e211-a939-e4115bead28a', 'London'),
)

SECTOR_CHOICES = (
    ('a538cecc-5f95-e211-a939-e4115bead28a', 'Food & Drink'),
)


class Organisation(CRMBaseModel):
    name = models.CharField(max_length=255)
    alias = models.CharField(max_length=255, blank=True)

    uk_organisation = models.BooleanField(default=True)
    country = models.CharField(
        max_length=255,
        choices=COUNTRY_CHOICES
    )
    postcode = models.CharField(max_length=255)
    address1 = models.CharField(max_length=255)
    city = models.CharField(max_length=255, blank=True)
    uk_region = models.CharField(
        max_length=255,
        choices=UK_REGION_CHOICES,
        blank=True
    )

    country_code = models.CharField(max_length=255)
    area_code = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)

    email_address = models.CharField(max_length=255)

    sector = models.CharField(
        max_length=255,
        choices=SECTOR_CHOICES
    )

    objects = CRMManager()
    cdms_migrator = OrganisationMigrator()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('organisation:update', args=[str(self.id)])


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
