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
        cache_path = list_cache_key(service, skip)
        if self.holds(service, skip):
            with open(cache_path, 'rb') as cache_fh:
                return pickle.load(cache_fh)
        start_time = datetime.datetime.now()
        resp = api.list(service, skip=skip)
        with open(timing_record(service, skip), 'w') as timing_fh:
            time_delta = (datetime.datetime.now() - start_time).seconds
            timing_fh.write(str(time_delta))
        if not resp.ok:
            return resp  # don't cache fails
        try:
            etree.fromstring(resp.content)  # check XML is parseable
        except etree.XMLSyntaxError as exc:
            # assume we got de-auth'd, trust poll_auth to fix it, don't cache
            # print("{0} ({1}) {2}s (FAIL)".format(service, skip, time_delta))
            return False
        # print("{0} ({1}) {2}s".format(service, skip, time_delta))
        with open(cache_path, 'wb') as cache_fh:
            pickle.dump(resp, cache_fh)
        return resp


def cache_passthrough(cache, entity_name, offset):
    entity_index = ENTITY_INT_MAP[entity_name]
    identifier = uuid.uuid4()
    # print("Starting {0} {1} {2}".format(entity_name, offset, identifier))
    resp = cache.list(entity_name, offset)
    '''
    print(
        "RESPONSE {0} {1} {2} {3}".format(
            getattr(resp, 'status_code', 403), entity_name, offset, identifier
        )
    )
    '''

    if resp is False:
        # means deauth'd
        print("setting 1 because deauth for {0}".format(entity_name))
        SHOULD_REQUEST[entity_index] = 1  # mark entity as open
                                          # don't increment offset
        return

    if resp.ok:
        try:
            etree.fromstring(resp.content)  # check XML is parseable
        except etree.XMLSyntaxError as exc:
            # need to auth
            return
        # everything went according to plan
        print("setting 1 because success for {0}".format(entity_name))
        SHOULD_REQUEST[entity_index] = 1  # mark entity as open
        ENTITY_OFFSETS[entity_index] += 50  # bump offset
        # print("Completing {0} {1} {2}".format(entity_name, offset, identifier))
        return

    if not resp.ok:
        print("setting 0 because not resp.ok for {0}".format(entity_name))
        SHOULD_REQUEST[entity_index] = 0
        if resp.status_code == 500:
            try:
                root = etree.fromstring(resp.content)
                if 'paging' in root.find(MESSAGE_TAG).text:
                    # let's pretend this means we reached the end and set this
                    # entity type to spent
                    # print("Spent {0} {1} {2}".format(entity_name, offset, identifier))
                    return
                # print("Error {0} {1} {2}".format(entity_name, offset, identifier))
            except Exception as exc:
                # print("Failing {0} {1} {2}".format(entity_name, offset, identifier))
                print("setting 0 because error for {0}".format(entity_name))
                SHOULD_REQUEST[entity_index] = 0
                # something bad, unknown and unknowable happened
                return
        else:
            print("setting 0 because big error for {0}".format(entity_name))
            SHOULD_REQUEST[entity_index] = 0
            # print("Failing {0} {1} {2}".format(entity_name, offset, identifier))
            return


def poll_auth(n):
    resp = api.list('FixedMonthlyFiscalCalendar')  # requests here seem fast
    if not resp.ok:
        time.sleep(1)
        return poll_auth(True)
    try:
        etree.fromstring(resp.content)  # check XML is parseable
    except etree.XMLSyntaxError as exc:
        # assume we got the login page, just try again
        AUTH_IN_PROGRESS.value = 1
        api.setup_session(True)
        AUTH_IN_PROGRESS.value = 0


class Command(BaseCommand):
    help = 'Download and cache XML responses from CDMS'

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
        last_report = 0
        pending = []
        while True:
            if pool._taskqueue.qsize() > PROCESSES - 1:
                continue
            for entity_name in ENTITY_NAMES:
                entity_index = ENTITY_INT_MAP[entity_name]
                if SHOULD_REQUEST[entity_index] == 0:
                    continue
                result = pool.apply_async(
                    cache_passthrough,
                    (cache, entity_name, ENTITY_OFFSETS[entity_index]),
                )
                pending.append(result)
                print("setting 0 to start for {0}".format(entity_name))
                SHOULD_REQUEST[entity_index] = 0  # mark entity as closed

            now = datetime.datetime.now()
            if now.second and now.second % 5 == 0 and last_polled != now.second:
                last_polled = now.second
                poll_auth(now.second)

            if now.second and now.second % 3 == 0 and last_report != now.second:
                last_report = now.second
                pending_swap = []
                for result in pending:
                    if not result.ready():
                        pending_swap.append(result)
                pending = pending_swap
                print("{0}".format(SHOULD_REQUEST[:]))
                print("{0} outstanding".format(len(pending)))
                print("{0} pending".format(len(list(filter(None, SHOULD_REQUEST[:])))))
