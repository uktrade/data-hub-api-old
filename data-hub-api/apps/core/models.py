from migrator.models import CDMSModel


class CRMBaseModel(CDMSModel):
    """
    This extends CDMSModel, when it's time to get rid of CDMS,
    just extend TimeStampedModel instead of CDMSModel and all the
    related logic goes away.

    NOTE: to be used with core.models.CRMManager.
    """
    class Meta:
        abstract = True
