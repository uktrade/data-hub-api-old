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
        """
        Load a single entity from the service with the provided ID.

        Args:
            service (str): Name of entity type. For example, 'Account'.
            guid (str): UUID of entity to be deleted.

        Returns:
            dict: A dictionary containing the content of the entity. Any fields
                that have no data will be included in the dictionary with
                `None` values. 400 Bad Request will be returned if guid is not
                valid.

        Raises:
            CDMSNotFoundException: If instance with provided guid can't be
                found.
        """
        url = "{base_url}/{service}Set(guid'{guid}')".format(
            base_url=self.CRM_REST_BASE_URL,
            service=service,
            guid=guid
        )
        return self.make_request('get', url)

    def update(self, service, guid, data):
        """
        Update a single entity from the service identified with the guid using
        the provided data. Will only update the fields provided by using a POST
        request with a MERGE in the method header (this translation from PUT
        happens in the client).

        Args:
            service (str): Name of entity type. For example, 'Account'.
            guid (str): UUID of entity to be deleted.
            data (dict): Partial data used to update the entity. Empty data can
                be sent. Any invalid key will crash the API.

        Raises:
            ErrorResponseException: If there is an error with the POST request
                that makes the update.
        """
        url = "{base_url}/{service}Set(guid'{guid}')".format(
            base_url=self.CRM_REST_BASE_URL,
            service=service,
            guid=guid
        )

        # TODO: check on POST response
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
        Delete a single entity from the service with the provided ID.

        Args:
            service (str): Name of entity type. For example, 'Account'.
            guid (str): UUID of entity to be deleted.

        Returns:
            requests.models.Response: A Response object with 204 status_code
                and no content on success. 400 Bad Request will be returned if
                guid is not valid.

        Raises:
            CDMSNotFoundException: If instance with provided guid can't be
                found.
        """
        url = "{base_url}/{service}Set(guid'{guid}')".format(
            base_url=self.CRM_REST_BASE_URL,
            service=service,
            guid=guid
        )
        return self.make_request('delete', url)

    def delete_all(self, service):
        """
        Remove all entities of a type. Used in tearing down testing.

        NOTE does not currently paginate - only deletes the first 50 entities.

        Args:
            service (str): Name of entity type. For example, 'Account'.

        Returns:
            int: Number of entities deleted.
        """
        counter = 0
        id_name = '{}Id'.format(service)

        for entity in self.list(service):
            response = self.delete(service, entity[id_name])
            if response.status_code == 204:
                counter += 1

        return counter
