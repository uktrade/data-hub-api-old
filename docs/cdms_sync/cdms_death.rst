Shutting down CDMS
------------------

If you are reading this it means that it's probably time to shut down CDMS and get rid of all that crazy
sync shit. **Congratulations and well done!**

Hopefully, the past developers made your life easier and removing all dependencies means that you only need to:

 * change ``core.models.CRMBaseModel`` so that it extends ``core.lib_models.TimeStampedModel`` instead of
   ``migrator.models.CDMSModel``
 * change ``core.models.managers.CDMSManager`` so that it extends the django default manager instead of
   ``migrator.managers.CDMSManager``
 * delete the ``migrator`` and the ``cdms_api`` apps
 * delete the ``cdms_migrator`` file in every django app
 * clean up the settings with all unused values
 * run ``makemigrations`` and ``migrate``
