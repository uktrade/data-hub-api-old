from django.db import models

from reversion import revisions as reversion

from core.models import CRMBaseModel
from core.managers import CRMManager

from .cdms_migrator import ContactMigrator


@reversion.register()
class Contact(CRMBaseModel):

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    objects = CRMManager()
    cdms_migrator = ContactMigrator()

    def __str__(self):
        return "{} {}".format(self.first_name, self.last_name)
