from migrator.managers import CDMSManager


class CRMManager(CDMSManager):
    """
    This extends CDMSManager, when it's time to get rid of CDMS,
    just extend models.Manager instead of CDMSManager and all the
    related logic goes away.

    NOTE: to be used with core.models.CRMBaseModel.
    """
    use_for_related_fields = True
