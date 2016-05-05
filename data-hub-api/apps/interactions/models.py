from django.db import models

from reversion import revisions as reversion

from core.fields import UKTIForeignKey
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
class EmailInteraction(CRMBaseModel):

    # Strictly speaking, this shouldn't be a foreign key so much as a
    # polymorphic primary key, but merging django-polymorphic with our own
    # CDMS-dependent architecture is asking for a headache.
    interaction = UKTIForeignKey(Interaction, related_name="emails")

    message_id = models.CharField(max_length=64)

    sender = models.ForeignKey(Contact)
    sender_address = models.EmailField()  # Can be removed post-CDMS

    receiver = models.ForeignKey(Contact)
    receiver_address = models.EmailField()  # Can be removed post-CDMS

    subject = models.CharField(max_length=256)
    body = models.TextField()
    raw = models.TextField()

    objects = CRMManager()
    cdms_migrator = EmailInteractionMigrator()

    def __str__(self):
        return "Email from {} to {} at {}".format(
            self.email.sender,
            self.email.receiver,
            self.created
        )
