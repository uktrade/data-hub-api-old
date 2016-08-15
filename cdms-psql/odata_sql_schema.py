import datetime
import logging
import os
import tempfile

import pyslet.odata2.metadata as edmx
import pgsql_entitycontainer
from separate_constraints import main as separate_constraints



def main(name_in, entity_container_key):
    '''
    Call table creation method on PgSQLEntityContainer extended PySLET OData
    entity container class for the entity container at the passed
    entity_container_key. Returns a str containing the SQL representation of
    the OData metadata file passed as this functions first argument.
    '''
    logger = logging.getLogger('odata_sql_schema')
    doc = edmx.Document()
    start_time = datetime.datetime.now()
    with open(name_in, 'rb') as metadata_fh:
        logger.info('Loading metadata XML file %s ...', name_in)
        doc.Read(metadata_fh)  # would love to be able to cache this but
                               # the `doc` object won't pickle
    logger.info(
        'It only took %s seconds',
        (datetime.datetime.now() - start_time).seconds
    )
    logger.info('Loading entity container element ...')
    entity_container = doc.root.DataServices[entity_container_key]
    # we don't define pgsql_options arg here, since the sql won't load directly
    # into a database due to lack of dependency resultion
    logger.info('Creating PSQL entity container ...')
    container = pgsql_entitycontainer.PgSQLEntityContainer(
        container=entity_container
    )
    with tempfile.TemporaryFile() as temp_fh:
        # instead we just dump out the sql statements to
        # a file for manual re-ordering
        logger.info('Writing schema to temp file ...')
        container.create_all_tables(out=temp_fh)
        # done
        temp_fh.seek(0)
        return temp_fh.read().decode('utf8')
