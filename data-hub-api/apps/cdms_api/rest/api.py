from django.conf import settings

from .auth.active_directory import ActiveDirectoryAuth


class CDMSRestApi(object):
    """
    Instance of a connection to the Microsoft Dynamics 2011 REST API.
    """

    CRM_REST_BASE_URL = '/'.join([
        settings.CDMS_BASE_URL.rstrip('/'),
        'XRMServices/2011/OrganizationData.svc'
    ])

    def __init__(self, auth=None):
        """
        Args:
            auth (Optional): An authentication instance. Defaults to a default
                instance of ActiveDirectoryAuth.
        """
        if auth is not None:
            self.auth = auth
        else:
            self.auth = ActiveDirectoryAuth()

    def make_request(self, verb, url, data=None):
        """
        Route a request through the authentication layer
        """
        if data is None:
            data = {}
        return self.auth.make_request(verb, url, data=data)

    def list(self, service, top=50, skip=0, select=None, filters=None, order_by=None):
        params = {}
        if filters:
            params['$filter'] = filters

        if select:
            params['$select'] = ','.join(select)

        if order_by:
            if isinstance(order_by, str):
                order_by = [order_by]
            params['$orderby'] = ','.join(order_by)

        url = "{base_url}/{service}Set?$top={top}&$skip={skip}&{params}".format(
            base_url=self.CRM_REST_BASE_URL,
            service=service,
            top=top,
            skip=skip,
            params='&'.join(sorted([u'%s=%s' % (k, v) for k, v in params.items()]))
        )

        results = self.make_request('get', url)
        return results['results']

    def get(self, service, guid):
        url = "{base_url}/{service}Set(guid'{guid}')".format(
            base_url=self.CRM_REST_BASE_URL,
            service=service,
            guid=guid
        )
        return self.make_request('get', url)

    def update(self, service, guid, data):
        url = "{base_url}/{service}Set(guid'{guid}')".format(
            base_url=self.CRM_REST_BASE_URL,
            service=service,
            guid=guid
        )

        # PUT returns 204 so we need to make an extra GET query to return the latest values
        self.make_request('put', url, data=data)
        return self.get(service, guid)

    def create(self, service, data):
        url = "{base_url}/{service}Set".format(
            base_url=self.CRM_REST_BASE_URL,
            service=service
        )
        return self.make_request('post', url, data=data)

    def delete(self, service, guid):
        """
        Returns:
            requests.models.Response: A Response object with 204 status_code
                and no content on success.
        """
        url = "{base_url}/{service}Set(guid'{guid}')".format(
            base_url=self.CRM_REST_BASE_URL,
            service=service,
            guid=guid
        )
        return self.make_request('delete', url)
