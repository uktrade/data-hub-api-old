.. _django_ORM_integration:

Django ORM integration
----------------------

Operations that cause synchronisation
.....................................

``.filter(...)`` operations make a CDMS API call to get the CDMS objects with the same translated filtering,
refresh the local objects by updating or creating them and then return the standard Django results.

``.get(...)`` operations get the object in local and in CDMS, compare the two, update the local one if
needed and then return the standard Django result.

``.create(...)`` or ``.save()`` operations create the object in local and in CDMS. In case of exceptions
with CDMS the local changes are rolled back.

``.save()`` operations update the object in local and in CDMS. In case of exceptions with CDMS the local
changes are rolled back.

``.delete()`` operations delete the object in local and in CDMS. In case of exceptions with CDMS the local
changes are rolled back.


.. raw:: html

   <hr>


✔ Supported
✘ Not supported


.. list-table:: Lookups
  :widths: 55 45
  :header-rows: 1

  * - API
    - Description
  * - ✔ Klass.objects.filter(field__exact=...)
    -
  * - ✔ Klass.objects.filter(field__iexact=...)
    -
  * - ✔ Klass.objects.filter(field__contains=...)
    -
  * - ✔ Klass.objects.filter(field__icontains=...)
    -
  * - ✘ Klass.objects.filter(field__in=...)
    -
  * - ✔ Klass.objects.filter(field__gt=...)
    -
  * - ✔ Klass.objects.filter(field__gte=...)
    -
  * - ✔ Klass.objects.filter(field__lt=...)
    -
  * - ✔ Klass.objects.filter(field__lte=...)
    -
  * - ✔ Klass.objects.filter(field__startswith=...)
    -
  * - ✔ Klass.objects.filter(field__istartswith=...)
    -
  * - ✔ Klass.objects.filter(field__endswith=...)
    -
  * - ✔ Klass.objects.filter(field__iendswith=...)
    -
  * - ✘ Klass.objects.filter(field__range=...)
    -
  * - ✔ Klass.objects.filter(field__year=...)
    -
  * - ✔ Klass.objects.filter(field__day=...)
    -
  * - ✘ Klass.objects.filter(field__week_day=...)
    -
  * - ✔ Klass.objects.filter(field__hour=...)
    -
  * - ✔ Klass.objects.filter(field__minute=...)
    -
  * - ✔ Klass.objects.filter(field__second=...)
    -
  * - ✘ Klass.objects.filter(field__isnull=...)
    - Not yet implemented but we should really support it.
  * - ✘ Klass.objects.filter(field__search=...)
    -
  * - ✘ Klass.objects.filter(field__regex=...)
    -
  * - ✘ Klass.objects.filter(field__iregex=...)
    -


.. list-table:: Filtering
  :widths: 55 45
  :header-rows: 1

  * - API
    - Description
  * - ✔ Klass.objects.all()
    - It only syncs the top 50 objects from CDMS as it would be infeasible to sync all of them.
  * - ✔ Klass.objects.filter(field=...)
    -
  * - ✔ Klass.objects.filter(Q(field=...))
    -
  * - ✔ Klass.objects.filter(field1=..., field2=...)
    -
  * - ✔ Klass.objects.filter(Q(field1=...) & Q(field2=...))
    -
  * - ✔ Klass.objects.filter(Q(field1=...) | Q(field2=...))
    -
  * - ✔ Klass.objects.filter(field1=...).filter(field2=...)
    -
  * - ✔ Klass.objects.filter(Q(Q(field1=...) & Q(field2=...)) & Q(field3=...))
    -
  * - ✔ Klass.objects.exclude(field=...)
    -
  * - ✔ Klass.objects.exclude(field1=..., field2=...)
    -
  * - ✔ Klass.objects.exclude(field1=...).exclude(field2=...)
    -
  * - ✔ Klass.objects.exclude(Q(field1=...) | Q(field2=...))
    -
  * - ✔ Klass.objects.exclude(Q(field1=...) & Q(field2=...))
    -
  * - ✔ Klass.objects.filter(field1=...).exclude(field2=...)
    -
  * - ✔ Klass.objects.filter(Q(field1=...) | Q(field2=...)).exclude(Q(field3=...) & Q(field4=...))
    -


.. list-table:: Order by
  :widths: 55 45
  :header-rows: 1

  * - API
    - Description
  * - ✔ Klass.objects.all().order_by('field')
    -
  * - ✔ Klass.objects.all().order_by('-field')
    -
  * - ✔ Klass.objects.all().order_by('field1', '-field2')
    -
  * - ✘ Klass.objects.all().order_by('?')
    -


.. list-table:: Get
  :widths: 55 45
  :header-rows: 1

  * - API
    - Description
  * - ✔ Klass.objects.get(pk=...)
    - Gets the obj from local, the one in CDMS, compares the two and updates the local before returning it if necessary
  * - ✔ Klass.objects.get(cdms_pk=...)
    - Gets the obj from local or CDMS if doesn't exist in local, updates or creates the local before returning it if necessary
  * - ✔ Klass.objects.get(field=...)
    - Like .get(pk=...)


.. list-table:: Create
  :widths: 55 45
  :header-rows: 1

  * - API
    - Description
  * - ✔ obj = Klass(field=...); obj.save()
    -
  * - ✔ Klass.objects.create(field=...)
    -
  * - ✘ Klass.objects.bulk_create(...)
    -


.. list-table:: Update
  :widths: 55 45
  :header-rows: 1

  * - API
    - Description
  * - ✔ obj.save()
    -
  * - ✘ Klass.objects.filter(field=...).update(...)
    -
  * - ✘ Klass.objects.select_for_update(...)
    -


.. list-table:: Delete
  :widths: 55 45
  :header-rows: 1

  * - API
    - Description
  * - ✔ obj.delete()
    -
  * - ✘ Klass.objects.filter(field=...).delete()
    -


.. list-table:: Misc
  :widths: 55 45
  :header-rows: 1

  * - API
    - Description
  * - ✘ Klass.objects.annotate(...)
    -
  * - ✘ Klass.objects.reverse(...)
    -
  * - ✘ Klass.objects.distinct(...)
    -
  * - ✘ Klass.objects.values(...)
    -
  * - ✘ Klass.objects.values_list(...)
    -
  * - ✘ Klass.objects.dates(...)
    -
  * - ✘ Klass.objects.datetimes(...)
    -
  * - ✔ Klass.objects.none()
    -
  * - ✘ Klass.objects.select_related(...)
    -
  * - ✘ Klass.objects.prefetch_related(...)
    -
  * - ✘ Klass.objects.extra(...)
    -
  * - ✘ Klass.objects.defer(...)
    -
  * - ✘ Klass.objects.only(...)
    -
  * - ✘ Klass.objects.raw(...)
    -
  * - ✘ Klass.objects.get_or_create(...)
    -
  * - ✘ Klass.objects.update_or_create(...)
    -
  * - ✘ Klass.objects.count(...)
    -
  * - ✘ Klass.objects.in_bulk(...)
    -
  * - ✘ Klass.objects.latest(...)
    -
  * - ✘ Klass.objects.earliest(...)
    -
  * - ✘ Klass.objects.first(...)
    -
  * - ✘ Klass.objects.last(...)
    -
  * - ✘ Klass.objects.aggregate(...)
    -
  * - ✘ Klass.objects.exists(...)
    -


Operations that skip synchronisation
.....................................

Most of the time, you can skip CDMS operations by using the ``skip_cdms()`` method on the manager
or the ``skip_cdms`` param on the save/delete methods.

.. note:: Do not skip the cdms operations when writing as the objects would then become out of sync.
    If this is really required, maybe we need to rename the `modified` field into something like
    `cdms_modified` and have a different one for `modified`.


✔ Supported
✘ Not supported


.. list-table:: Filtering
  :widths: 55 45
  :header-rows: 1

  * - API
    - Description
  * - ✔ Klass.objects.skip_cdms().all()
    -
  * - ✔ Klass.objects.skip_cdms().filter(...)
    -
  * - ✔ Klass.objects.skip_cdms().exclude(...)
    -
  * - ✔ Klass.objects.skip_cdms().all().order_by(...)
    -


.. list-table:: Get
  :widths: 55 45
  :header-rows: 1

  * - API
    - Description
  * - ✔ Klass.objects.skip_cdms().get()
    -


.. list-table:: Create
  :widths: 55 45
  :header-rows: 1

  * - API
    - Description
  * - ✔ obj = Klass(field=...); obj.save(skip_cdms=True)
    -
  * - ✔ Klass.objects.skip_cdms().create(field=...)
    -
  * - ✔ Klass.objects.skip_cdms().bulk_create(field=...)
    -

.. list-table:: Update
  :widths: 55 45
  :header-rows: 1

  * - API
    - Description
  * - ✔ obj.save(skip_cdms=True)
    -
  * - ✔ Klass.objects.skip_cdms().filter(field=...).update(...)
    -
  * - ✔ Klass.objects.skip_cdms().select_for_update(...)
    -

.. list-table:: Delete
  :widths: 55 45
  :header-rows: 1

  * - API
    - Description
  * - ✔ obj.delete(skip_cdms=True)
    -
  * - ✔ Klass.objects.skip_cdms().filter(field=...).delete()
    -


.. list-table:: Misc
  :widths: 55 45
  :header-rows: 1

  * - API
    - Description
  * - ✔ Klass.objects.skip_cdms().annotate(...)
    -
  * - ✔ Klass.objects.skip_cdms().reverse(...)
    -
  * - ✔ Klass.objects.skip_cdms().distinct(...)
    -
  * - ✔ Klass.objects.skip_cdms().values(...)
    -
  * - ✔ Klass.objects.skip_cdms().values_list(...)
    -
  * - ✔ Klass.objects.skip_cdms().dates(...)
    -
  * - ✔ Klass.objects.skip_cdms().datetimes(...)
    -
  * - ✔ Klass.objects.skip_cdms().none()
    -
  * - ✔ Klass.objects.skip_cdms().select_related(...)
    -
  * - ✘ Klass.objects.skip_cdms().prefetch_related(...)
    -
  * - ✔ Klass.objects.skip_cdms().extra(...)
    -
  * - ✔ Klass.objects.skip_cdms().defer(...)
    -
  * - ✔ Klass.objects.skip_cdms().only(...)
    -
  * - ✔ Klass.objects.skip_cdms().raw(...)
    -
  * - ✔ Klass.objects.skip_cdms().get_or_create(...)
    -
  * - ✔ Klass.objects.skip_cdms().update_or_create(...)
    -
  * - ✔ Klass.objects.skip_cdms().count(...)
    -
  * - ✔ Klass.objects.skip_cdms().in_bulk(...)
    -
  * - ✔ Klass.objects.skip_cdms().latest(...)
    -
  * - ✔ Klass.objects.skip_cdms().earliest(...)
    -
  * - ✔ Klass.objects.skip_cdms().first(...)
    -
  * - ✔ Klass.objects.skip_cdms().last(...)
    -
  * - ✔ Klass.objects.skip_cdms().aggregate(...)
    -
  * - ✔ Klass.objects.skip_cdms().exists(...)
    -
