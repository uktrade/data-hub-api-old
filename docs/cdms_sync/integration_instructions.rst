Integration instructions
------------------------

How it works
............

A custom django manager / queryset intercepts reads / writes and takes care of all the CDMS operations.
This means that developers can ignore this extra complexity and use the django orm api as usual.

That being said, only a subset of the django orm api have been implemented and are even possible.
Check :ref:`django_ORM_integration` for the full list of the ORM calls supported.

Project setup
.............

The ``cdms_api`` app contains the CDMS API library whilst the ``migrator`` app defines all the code needed for
the synchronisation.

.. note:: It's really important that you keep all the logic related to the CDMS sync in one place
          and to a minimum so that it's easy to get rid of it when it's time to shut down CDMS and
          delete the sync layer altogether.

          For this reason, we decided to keep this logic in the ``migrator`` app and in one single file
          per django app (conventionally called ``cdms_migrator.py``).

Your app and your Django model
..............................

 1. Set up Django app/model

  Create a new Django app or simply a new Django Model as needed.

 2. CDMSMigrator

  In a module called ``<your-app>/cdms_migrator.py`` , subclass ``migrator.cdms_migrator.BaseCDMSMigrator``
  and define the mapping fields and the CDMS service.

  Add the CDMSMigrator to the Django Model as per step 3.

 3. Configure your model

  Change your model so that it looks like the one below:

  .. note:: for Foreign key fields, you should use ``core.fields.UKTIForeignKey`` instead of the Django one.

  .. code:: python

    from reversion import revisions as reversion

    from django.db import models

    from core.models import CRMBaseModel
    from core.managers import CRMManager

    from .cdms_migrator import MyModelMigrator

    @reversion.register()
    class MyModel(CRMBaseModel):
        ....

        objects = CRMManager()
        cdms_migrator = MyModelMigrator()


 4. Create a migration for your model as usual

  .. code:: python

   ./manage.py makemigrations
   ./manage.py migrate


CDMSMigrator
............

The mapping between your model and the CDMS one is defined in your model's CDMSMigrator class which should
be in ``<your-app>/cdms_migrator.py``.

Extend the ``migrator.cdms_migrator.BaseCDMSMigrator`` class and define the ``fields`` and ``service`` attributes.

For example

.. code:: python

  from cdms_api import fields as cdms_fields

  from migrator.cdms_migrator import BaseCDMSMigrator


  class OrganisationMigrator(BaseCDMSMigrator):
      fields = {
          'name': cdms_fields.StringField('Name'),
          'uk_organisation': cdms_fields.BooleanField('optevia_ukorganisation'),
          ...
      }
      service = 'Account'  # this is the Dynamics resource name
