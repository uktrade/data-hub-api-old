import os
import tempfile

import pyslet.odata2.metadata as edmx
import pgsql_entitycontainer
from separate_constraints import main as separate_constraints



def main(name_in):
    '''
    Call table creation method on PgSQLEntityContainer extended PySLET OData
    entity container class to get SQL representation of the OData metadata file
    passed as this functions only argument.
    '''
    doc = edmx.Document()
    with open(name_in, 'rb') as metadata_fh:
        doc.Read(metadata_fh)  # would love to be able to cache this but
                               # the `doc` object won't pickle
    entity_container_key = 'Microsoft.Crm.Sdk.Data.Services.UKTIContext'
    entity_container = doc.root.DataServices[entity_container_key]
    # we don't define pgsql_options arg here, since the sql won't load directly
    # into a database due to lack of dependency resultion
    container = pgsql_entitycontainer.PgSQLEntityContainer(
        container=entity_container
    )
    with tempfile.TemporaryFile() as temp_fh:
        # instead we just dump out the sql statements to
        # a file for manual re-ordering
        container.create_all_tables(out=temp_fh)
        # done
        temp_fh.seek(0)
        return temp_fh.read()
