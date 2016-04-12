Revisions
---------

We use `django-reversion <https://github.com/etianen/django-reversion>`_ for creating revisions and versions.

How django-reversion works
..........................

django-reversion uses revisions and versions.

**Revisions** are blocks of code where some changes happen. One or more objects could potentially change
in the same block.

**Versions** are changes to an object in a given revision. Versions always have a foreign key to the related
revision.

Revisions can have the following metadata:

- *user*: who made the changes
- *comment*: optional text

Metadata has to be set manually for obvious reasons.

Usually you implement django-reversion in various ways:

- via the admin integration so that every time a user uses the admin, changes are saved automatically
- via an explicit context manager with the possibility to set metadata programmatically


How django-reversion is used
............................

As we wanted to create revisions/versions automatically and not lose any changes, we implemented
django-reversion at a lower level.

In our system we have 2 types of changes:

- *CDMS refresh changes*: where we refresh a local object (update or create) from CDMS.
  This happens automatically by creating a version of the object with the comment `CDMS refresh`.

- *local changes*: where we make a change to the objects of our system.
  This happens every time the ``.save()`` method is called and it's automatic.

.. note:: As we can't access the user automatically, we are currently not setting the related metadata on the
        revision. We need to look into this, it might just be a matter of using the context manager in API views.
