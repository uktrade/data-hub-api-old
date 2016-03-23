from django.db import models

from .fields import AutoCreatedField, AutoLastModifiedField


class TimeStampedModel(models.Model):
    created = AutoCreatedField()
    modified = AutoLastModifiedField()

    class Meta:
        abstract = True
