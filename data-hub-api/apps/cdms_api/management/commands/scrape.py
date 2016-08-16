import functools
import itertools
import multiprocessing
import os
import pickle

from django.core.management.base import BaseCommand, CommandError
from cdms_api.connection import rest_connection as api

from lxml import etree

FORBIDDEN_ENTITIES = set((
    'Competitor',
    'ConstraintBasedGroup',
    'Contract',
    'ContractDetail',
    'ContractTemplate',
    'CustomerOpportunityRole',
    'CustomerRelationship',
    'Discount',
    'DiscountType',
    'Invoice',
    'InvoiceDetail',
    'Lead',
    'LookUpMapping',
    'Opportunity',
    'OpportunityProduct',
    'OrganizationUI',
    'Post',
    'PostComment',
    'PostFollow',
    'PostLike',
    'PriceLevel',
    'Product',
    'ProductPriceLevel',
    'Quote',
    'QuoteDetail',
    'RelationshipRole',
    'RelationshipRoleMap',
    'Resource',
    'ResourceGroup',
    'ResourceSpec',
    'SalesLiterature',
    'SalesLiteratureItem',
    'SalesOrder',
    'SalesOrderDetail',
    'Service',
    'Territory',
    'UoM',
    'UoMSchedule',
    'detica_optionsetfield',
    'detica_portalpage',
    'mtc_licensing',
    'optevia_omisorder',
    'optevia_uktiorder',
))

with open('cdms-psql/entity-table-map/entities', 'r') as entities_fh:
    ENTITY_NAMES = []
    for line in entities_fh.readlines():
        entity_name = line.strip()
        if entity_name not in FORBIDDEN_ENTITIES:
            ENTITY_NAMES.append(entity_name)

ENTITY_INT_MAP = {
    name: index for index, name in enumerate(ENTITY_NAMES)
}


def file_leaf(*args):
    path = os.path.join(*map(str, args))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def entry_cache_key(service, guid):
    return file_leaf('cache', 'entry', service, guid)


def list_cache_key(service, offset):
    return file_leaf('cache', 'list', service, offset)


class CDMSEntryCache(object):

    def get(self, service, guid):
        raise NotImplementedError()

    def set(self, service, guid, entry):
        cache_key = entry_cache_key(service, guid)
        with open(cache_key, 'wb') as cache_fh:
            cache_fh.write(entry)

    def holds(self, service, guid):
        return os.path.isfile(entry_cache_key(service, guid))



class CDMSListRequestCache(object):

    def __init__(self):
        self.entry_cache = CDMSEntryCache()

    def holds(self, service, skip):
        return os.path.isfile(list_cache_key(service, skip))

    def list(self, service, skip):
        path = list_cache_key(service, skip)
        if self.holds(service, skip):
            with open(path, 'rb') as cache_fh:
                return pickle.load(cache_fh)
        resp = api.list(service, skip=skip)
        if not resp.ok:
            return resp
        with open(path, 'wb') as cache_fh:
            pickle.dump(resp, cache_fh)
        try:
            root = etree.fromstring(resp.content)
        except etree.XMLSyntaxError as exc:
            # assume we got the login page, just try again
            api.setup_session(True)
            return self.list(service, skip)
        for entry in root.iter('{http://www.w3.org/2005/Atom}entry'):
            guid = entry.find('{http://www.w3.org/2005/Atom}id').text[-38:-2]
            if not self.entry_cache.holds(service, guid):
                self.entry_cache.set(
                    service, guid, etree.tostring(entry, pretty_print=True)
                )
        return resp


def cache_passthrough(cache, entity_name, offset):
    resp = cache.list(entity_name, offset)
    if resp.status_code >= 400:
        if resp.status_code == 500:
            try:
                root = etree.fromstring(resp.content)
                if 'paging' in root.find('{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}message').text:
                    print("spent: {0}".format(entity_name))
                    # let's pretend this means we reached the end and set this
                    # entity type to spent
                    SPENT[ENTITY_INT_MAP[entity_name]] = 1
                    return
            except Exception as exc:
                print("{0} ({1}): {2}".format(resp.status_code, offset, entity_name))
                # something bad happened
                pass
        else:
            print("{0} ({1}): {2}".format(resp.status_code, offset, entity_name))

SPENT = multiprocessing.Array('i', len(ENTITY_NAMES))
class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('service', nargs='?')
        parser.add_argument('guid', nargs='?')

    def handle(self, *args, **options):
        cache = CDMSListRequestCache()
        pool = multiprocessing.Pool(processes=8)
        offset = 0
        api.setup_session(True)
        for index in range(len(ENTITY_NAMES)):
            SPENT[index] = 0
        while True:
            starmap_args = []
            for entity_name in ENTITY_NAMES:
                if SPENT[ENTITY_INT_MAP[entity_name]] == 1:
                    # we've downloaded everything there
                    continue
                starmap_args.append((cache, entity_name, offset))
            result = pool.starmap_async(cache_passthrough, starmap_args)
            result.get()
            offset += 50
