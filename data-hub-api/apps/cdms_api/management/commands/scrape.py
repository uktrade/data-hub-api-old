import uuid
import datetime
import multiprocessing
import os
import pickle
import time

from django.core.management.base import BaseCommand, CommandError
from cdms_api.connection import rest_connection as api

from lxml import etree

MESSAGE_TAG = '{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}message'

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

with open('cdms-psql/entity-table-map/entities-optimisable', 'r') as entities_fh:
    ENTITY_NAMES = []
    for line in entities_fh.readlines():
        entity_name = line.strip()
        if entity_name not in FORBIDDEN_ENTITIES:
            ENTITY_NAMES.append(entity_name)

ENTITY_INT_MAP = {
    name: index for index, name in enumerate(ENTITY_NAMES)
}
ENTITY_OFFSETS = []

SHOULD_REQUEST = multiprocessing.Array('i', len(ENTITY_NAMES))
AUTH_IN_PROGRESS = multiprocessing.Value('i', 0)


def file_leaf(*args):
    path = os.path.join(*map(str, args))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def list_cache_key(service, offset):
    return file_leaf('cache', 'list', service, offset)


def timing_record(service, offset):
    return file_leaf('cache', 'timing', service, offset)


class CDMSListRequestCache(object):

    def holds(self, service, skip):
        path = list_cache_key(service, skip)
        if not os.path.isfile(path):
            return False
        try:
            with open(path, 'rb') as cache_fh:
                etree.fromstring(pickle.load(cache_fh))
        except etree.XMLSyntaxError as exc:
            return False
        return True

    def list(self, service, skip):
        while AUTH_IN_PROGRESS.value == 1:
            return
        cache_path = list_cache_key(service, skip)
        if self.holds(service, skip):
            return  # kick out early
        start_time = datetime.datetime.now()
        resp = api.list(service, skip=skip, order_by='CreatedOn')
        if not resp.ok:
            return resp
        with open(timing_record(service, skip), 'w') as timing_fh:
            time_delta = (datetime.datetime.now() - start_time).seconds
            timing_fh.write(str(time_delta))
        try:
            etree.fromstring(resp.content)  # check XML is parseable
        except etree.XMLSyntaxError as exc:
            # assume we got de-auth'd, trust poll_auth to fix it
            print("{0} ({1}) {2}s (FAIL)".format(service, skip, time_delta))
            return
        print("{0} ({1}) {2}s".format(service, skip, time_delta))
        with open(cache_path, 'wb') as cache_fh:
            pickle.dump(resp, cache_fh)
        return resp


def cache_passthrough(cache, entity_name, offset):
    identifier = uuid.uuid4()
    print("Starting {0} {1} {2}".format(entity_name, offset, identifier))
    resp = cache.list(entity_name, offset)
    if not resp:
        SHOULD_REQUEST[ENTITY_INT_MAP[entity_name]] = 1  # mark entity as open
    if resp.status_code >= 400:
        if resp.status_code == 500:
            try:
                root = etree.fromstring(resp.content)
                if 'paging' in root.find(MESSAGE_TAG).text:
                    # let's pretend this means we reached the end and set this
                    # entity type to spent
                    print("Spent {0} {1} {2}".format(entity_name, offset, identifier))
                    SHOULD_REQUEST[ENTITY_INT_MAP[entity_name]] = 0
                    return
            except Exception as exc:
                print("Failing {0} {1} {2}".format(entity_name, offset, identifier))
                SHOULD_REQUEST[ENTITY_INT_MAP[entity_name]] = 0
                # something bad, unknown and unknowable happened
                pass
        else:
            SHOULD_REQUEST[ENTITY_INT_MAP[entity_name]] = 0
            print("Failing {0} {1} {2}".format(entity_name, offset, identifier))
    else:
        # everything went according to plan
        entity_index = ENTITY_INT_MAP[entity_name]
        ENTITY_OFFSETS[entity_index] += 50  # bump offset
        SHOULD_REQUEST[entity_index] = 1  # mark entity as open
        print("Completing {0} {1} {2}".format(entity_name, offset, identifier))


def poll_auth(n):
    print("AUTH POLL {0}".format(n))
    resp = api.list('FixedMonthlyFiscalCalendar')  # requests here seem fast
    if not resp.ok:
        time.sleep(1)
        return poll_auth(True)
    try:
        etree.fromstring(resp.content)  # check XML is parseable
    except etree.XMLSyntaxError as exc:
        print('AUTH REFRESH')
        # assume we got the login page, just try again
        AUTH_IN_PROGRESS.value = 1
        api.setup_session(True)
        AUTH_IN_PROGRESS.value = 0


class Command(BaseCommand):
    help = 'Download and cache XML files from CDMS'

    def handle(self, *args, **options):
        cache = CDMSListRequestCache()
        pool = multiprocessing.Pool(processes=PROCESSES)
        for entity_name in ENTITY_NAMES:
            try:
                caches = os.listdir(os.path.join('cache', 'list', entity_name))
                ENTITY_OFFSETS.append(max(map(int, caches)) + 50)
            except (FileNotFoundError, ValueError) as exc:
                ENTITY_OFFSETS.append(0)
        api.setup_session(True)
        for index in range(len(ENTITY_NAMES)):
            SHOULD_REQUEST[index] = 1
        last_polled = 0
        while True:
            if pool._taskqueue.qsize() > PROCESSES - 1:
                continue
            starmap_args = []
            for entity_name in ENTITY_NAMES:
                entity_index = ENTITY_INT_MAP[entity_name]
                if SHOULD_REQUEST[entity_index] == 0:
                    continue
                starmap_args.append((cache, entity_name, ENTITY_OFFSETS[entity_index]))
                SHOULD_REQUEST[entity_index] = 0  # mark entity as closed

            now = datetime.datetime.now()
            if now.second and now.second % 5 == 0 and last_polled != now.second:
                last_polled = now.second
                poll_auth(now.second)
            pool.starmap_async(cache_passthrough, starmap_args)
