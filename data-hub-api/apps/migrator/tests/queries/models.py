from django.db import models
from migrator.models import CDMSModel
from migrator.managers import CDMSManager
from migrator.cdms_migrator import BaseCDMSMigrator

from cdms_api import fields as cdms_fields

from migrator.fields import CDMSForeignKey


class MigratorManager(CDMSManager):
    use_for_related_fields = True


class ParentObjMigrator(BaseCDMSMigrator):
    fields = {
        'name': cdms_fields.StringField('Name')
    }
    service = 'Parent'


class ParentObj(CDMSModel):
    name = models.CharField(max_length=250)

    objects = MigratorManager()
    cdms_migrator = ParentObjMigrator()

    class Meta:
        ordering = ['modified']


class SimpleMigrator(BaseCDMSMigrator):
    fields = {
        'name': cdms_fields.StringField('Name'),
        'dt_field': cdms_fields.DateTimeField('DateTimeField'),
        'int_field': cdms_fields.IntegerField('IntField'),
        'fk_obj': cdms_fields.ForeignKeyField('FKField', 'migrator.tests.queries.ParentObj'),
    }
    service = 'Simple'


class SimpleObj(CDMSModel):
    name = models.CharField(max_length=250)
    dt_field = models.DateTimeField(null=True)
    int_field = models.IntegerField(null=True)
    fk_obj = CDMSForeignKey(ParentObj, null=True)

    d_field = models.DateField(null=True)

    objects = MigratorManager()
    cdms_migrator = SimpleMigrator()

    class Meta:
        ordering = ['modified']
