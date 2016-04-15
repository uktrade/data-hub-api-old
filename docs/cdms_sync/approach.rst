The problem, the options and our approach
-----------------------------------------


The problem
...........

We are migrating away from Microsoft Dynamics 2011 (**CDMS**) and decided to build a new CRM system (**Data Hub**)
using a gradual incremental approach.

During a period of several months, the following constraints apply:

-  data between CDMS and Data Hub needs to be kept in sync
-  Data Hub needs allow re-modeling by adding/removing types/properties
-  some users would continue to use CDMS whilst we transition from one system to the other

The options
...........

We considered different approaches including:

-  use CDMS as data store and access it directly. This has many disadvantages including hosting CDMS,
   not being able to easily change the schemas, architecture complexity etc.
-  use two data stores with some sort of low level synchronization (via database or processes).
   This as well has many disadvantages including integrating with old technologies (Dynamics 2011), two separate
   layers (code and sync logic) depending on each other tightly and hard to manage, synchronisation conflicts etc.
-  use two data stores with code-managed synchronization. This is the chosen architecture and
   has some disadvantages as well that we will explain later.

The chosen approach
...................

Two data stores with reads and writes to CDMS happening as usual and synchronisation triggered from io actions in
Data Hub.

Writes to Data Hub will:
  * get the object from CDMS (if it exists)
  * apply the changes and write to CDMS
  * apply the changes in Data Hub

Reads from Data Hub will:
  * get the object from the Data Hub data store
  * get the related object from CDMS
  * check if CDMS was updated after the last synchronisation
  * if so, update the Data Hub object
  * return the local results

Read and write operations are performed as a single transaction so that changes are rolled back in case of
exceptions with CDMS.

The same object on both systems is considered in sync if the `modified` field value is the same.
If the `modified` value of the CDMS version is more recent, it means that the Data Hub object has to be updated
from the CDMS one.
If the `modified` value of the Data Hub version is more recent, an exception is triggered as this should never
happen. This is because writes on the Data Hub always generate writes in CDMS but the vice versa is obviously not true.

The possibility of conflicts is low as:

-  objects on the two systems are kept in sync via the *modified* field updated after each CDMS get
-  concurrent operations to a single object are low or non-existent in volume

In case two updates happen at approximately the same time, the last one wins.
This should not be a problem as the system keeps a history of the changes.

Limitations
...........

There are some limitations in using this approach:

  * Amount of requests. This has not been measured yet but could (and should) be partially addressed
    by using some sort of caching strategy
  * The synchronisation happens using one common CDMS user
  * Some Django ORM API cannot be easily implemented. E.g. ``Model.objects.count()``,
    ``Model.objects.filter(field1__field2='something')``. This is mainly because of the old CDMS technologies
  * It might not be easy to change the Django schema in many cases as the sync layer prefers a one-to-one mapping.
