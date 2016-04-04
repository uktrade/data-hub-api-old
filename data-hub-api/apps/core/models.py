from migrator.models import CDMSModel

from reversion import revisions as reversion


class CRMBaseModel(CDMSModel):
    """
    This extends CDMSModel, when it's time to get rid of CDMS,
    just extend TimeStampedModel instead of CDMSModel and all the
    related logic goes away.

    NOTE: to be used with core.models.CRMManager.
    """
    class Meta:
        abstract = True

    @reversion.create_revision()
    def save(self, *args, **kwargs):
        return super(CRMBaseModel, self).save(*args, **kwargs)
