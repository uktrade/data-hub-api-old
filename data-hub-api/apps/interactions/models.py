from django.db import models

from reversion import revisions as reversion

from core.models import CRMBaseModel
from core.managers import CRMManager
from .cdms_migrator import InteractionMigrator, EmailInteractionMigrator

from contacts.models import Contact


@reversion.register()
class Interaction(CRMBaseModel):

    objects = CRMManager()
    cdms_migrator = InteractionMigrator()

    def __str__(self):
        return str(self.created)


@reversion.register()
class EmailInteraction(Interaction):

    sender = models.ForeignKey(Contact)
    receiver = models.ForeignKey(Contact)
    body = models.TextField()
    raw = models.TextField()
    created = models.DateTimeField(editable=False)

    objects = CRMManager()
    cdms_migrator = EmailInteractionMigrator()

    def __str__(self):
        return "Email from {} to {} at {}".format(
            self.email.sender,
            self.email.receiver,
            self.created
        )
