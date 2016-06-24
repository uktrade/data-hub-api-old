.. _REST_API:

REST API
--------

The Microsoft documentation says that you can only access Dynamics using REST API if you have gone through the web
authentication process. This was mainly introduced to allow Microsoft javascript to make direct calls to the endpoints.

The library `cdms_api.rest.api` uses requests and some html parsing in order to simulate the login process and obtain an
authenticated cookie which will be used to make REST API calls to Dynamics endpoints.

The cookie is encrypted and stored so that it can be used transparently.

After authenticated, Dynamics allows REST API requests to the endpoint ```/XRMServices/2011/OrganizationData.svc/<ServiceSet>```
using standard GET/POST/DELETE verbs and json request/responses.

Useful links:

- `What's the difference between ADFS, WIF, WS Federation, SAML, and STS? <http://stackoverflow.com/questions/7979254/whats-the-difference-between-adfs-wif-ws-federation-saml-and-sts>`_ to understand the concepts.
- `OData System Query Options Using the REST Endpoint <https://msdn.microsoft.com/en-gb/library/gg309461(v=crm.5).aspx>`_. explains how requests can be construct. The library `cdms_api.rest.api` makes this easy to use and the django app `migrator` implements most of them already.
- `Examples of REST OData requests <https://docs.google.com/spreadsheets/d/1ikPylNc4aNo6EKU7-kCx3nGrVnwmtU6qbTE7acd2tgU/edit?hl=en_GB&authkey=CNjdm5sH#gid=0>`_ contains a list of examples on how to use the oData syntax.
