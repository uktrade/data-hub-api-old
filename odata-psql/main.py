import os
import tempfile

import pyslet.odata2.metadata as edmx
import pgsql



def main():
    'Convert OData metadata.xml to SQL schema'
    doc = edmx.Document()
    with open('cdms-metadata.xml', 'rb') as metadata_fh:
        doc.read(metadata_fh)  # would love to be able to cache this but
                               # the `doc` object won't pickle
    entity_container_key = 'Microsoft.Crm.Sdk.Data.Services.UKTIContext'
    entity_container = doc.root.DataServices[entity_container_key]
    # we don't define pgsql_options arg here, since the sql won't load directly
    # into a database due to lack of dependency resultion
    container = pgsql.PgSQLEntityContainer(container=entity_container)
    with open('cdms-pgsql.sql', 'w') as cdmspgsql_fh:
        # instead we just dump out the sql statements to
        # a file for manual re-ordering
        container.create_all_tables(out=cdmspgsql_fh)
    # done

if __name__ == '__main__':
    main()
