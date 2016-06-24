Overview
--------

Authentication
..............

To authenticate against CDMS you need to:

- ask and get a token from the UKTI Identity Provider
- request a new token from a Resource Security Token Service (RSTS)
- use this token to make usual SOAP requests to CDMS

The authentication could fail because:

- the credentials are invalid and the Identity Provider cannot authenticate the user
- the Identity Provider can authenticate the user but they don't have access to CDMS so they cannot obtain a token to connect to it

CDMS Access
...........

There are two ways of authenticating and accessing CDMS:

- :ref:`REST_API`.
- :ref:`SOAP_API`.
