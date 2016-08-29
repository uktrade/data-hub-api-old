import datetime
import multiprocessing
import os
import pickle
import time

from django.core.management.base import BaseCommand, CommandError
from cdms_api.connection import rest_connection as api

from lxml import etree

PROCESSES = 32
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

INFINITE_ENTITIES = set()  # (  # API requests generate rows here?
'''
    'Queue',
    'detica_optevia_servicedelivery_detica_typeofsu',
    'optevia_exportlog',
    'RolePrivileges',
    'SystemUserProfiles',
    'SystemUserRoles',
))
'''
with open('spent', 'r') as spent_fh:
    SPENT_HERE = [line.strip() for line in spent_fh.readlines()]

with open('cdms-psql/entity-table-map/entities', 'r') as entities_fh:
    ENTITY_NAMES = []
    for line in entities_fh.readlines():
        entity_name = line.strip()
        conditions = (
            entity_name not in FORBIDDEN_ENTITIES,
            entity_name not in INFINITE_ENTITIES,
        )
        if all(conditions):
            ENTITY_NAMES.append(entity_name)

ENTITY_INT_MAP = {
    name: index for index, name in enumerate(ENTITY_NAMES)
}

SHOULD_REQUEST = multiprocessing.Array('i', len(ENTITY_NAMES))
AUTH_IN_PROGRESS = multiprocessing.Value('i', 0)


def file_leaf(*args):
    path = os.path.join(*map(str, args))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def entry_cache_key(service, guid):
    return file_leaf('cache', 'entry', service, guid)


def list_cache_key(service, offset):
    return file_leaf('cache', 'list', service, offset)


def timing_record(service, offset):
    return file_leaf('cache', 'timing', service, offset)


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
        '''  too expensive
        path = list_cache_key(service, skip)
        if not os.path.isfile(path):
            return False
        try:
            with open(path, 'rb') as cache_fh:
                etree.fromstring(pickle.load(cache_fh))
        except etree.XMLSyntaxError as exc:
            return False
        return True
        '''

    def list(self, service, skip):
        while AUTH_IN_PROGRESS.value == 1:
            print("{0} ({1}) is waiting for auth".format(service, skip))
            time.sleep(3)
            continue
        path = list_cache_key(service, skip)
        if self.holds(service, skip):
            return  # kick out early
            with open(path, 'rb') as cache_fh:
                try: return pickle.load(cache_fh)
                except: pass
        start_time = datetime.datetime.now()
        resp = api.list(service, skip=skip)
        if not resp.ok:
            return resp
        with open(timing_record(service, skip), 'w') as timing_fh:
            time_delta = (datetime.datetime.now() - start_time).seconds
            timing_fh.write(str(time_delta))
        print("{0} ({1}) {2}s".format(service, skip, time_delta))
        with open(path, 'wb') as cache_fh:
            pickle.dump(resp, cache_fh)
        try:
            root = etree.fromstring(resp.content)
        except etree.XMLSyntaxError as exc:
            # assume we got the login page, just try again
            print("{0} ({1}) is refreshing auth".format(service, skip))
            AUTH_IN_PROGRESS.value = 1
            api.setup_session(True)
            AUTH_IN_PROGRESS.value = 0
            print("{0} ({1}) has refreshed auth".format(service, skip))
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
    if not resp:
        SHOULD_REQUEST[ENTITY_INT_MAP[entity_name]] = 1  # mark entity as open
    if resp.status_code >= 400:
        if resp.status_code == 500:
            try:
                root = etree.fromstring(resp.content)
                if 'paging' in root.find('{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}message').text:
                    print("spent: {0}".format(entity_name))
                    # let's pretend this means we reached the end and set this
                    # entity type to spent
                    SHOULD_REQUEST[ENTITY_INT_MAP[entity_name]] = 0
                    return
            except Exception as exc:
                print("{0} ({1}): {2}".format(resp.status_code, offset, entity_name))
                SHOULD_REQUEST[ENTITY_INT_MAP[entity_name]] = 0
                # something bad happened
                pass
        else:
            SHOULD_REQUEST[ENTITY_INT_MAP[entity_name]] = 0
            print("{0} ({1}): {2}".format(resp.status_code, offset, entity_name))
    else:
        root = etree.fromstring(resp.content)
        if not root.findall('{http://www.w3.org/2005/Atom}entry'):
            print("spent other: {0}".format(entity_name))
            SHOULD_REQUEST[ENTITY_INT_MAP[entity_name]] = 0  # the other way to page out?
        else:
            SHOULD_REQUEST[ENTITY_INT_MAP[entity_name]] = 1  # mark entity as open


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument('service', nargs='?')
        parser.add_argument('guid', nargs='?')

    def handle(self, *args, **options):
        cache = CDMSListRequestCache()
        pool = multiprocessing.Pool(processes=PROCESSES)
        offsets = []
        for entity_name in ENTITY_NAMES:
            try:
                offsets.append(max(map(int, os.listdir(os.path.join('cache', 'list', entity_name)))) + 50)
            except (FileNotFoundError, ValueError):
                offsets.append(0)
        api.setup_session(True)
        for index in range(len(ENTITY_NAMES)):
            SHOULD_REQUEST[index] = 1
        while True:
            if pool._taskqueue.qsize() > PROCESSES:
                continue
            starmap_args = []
            for entity_name in ENTITY_NAMES:
                entity_index = ENTITY_INT_MAP[entity_name]
                if SHOULD_REQUEST[entity_index] == 0:
                    continue
                starmap_args.append((cache, entity_name, offsets[entity_index]))
                SHOULD_REQUEST[entity_index] = 0  # mark entity as closed
                offsets[entity_index] += 50
            pool.starmap_async(cache_passthrough, starmap_args)
