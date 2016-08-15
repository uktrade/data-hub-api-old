import sys
import logging

from odata_sql_schema import main as odata_sql_schema
from separate_constraints import main as separate_constraints

logging.basicConfig(level=logging.INFO)


def main(name_in, name_out, entity_container_key=None):
    'Convert OData metadata.xml to SQL schema'
    if entity_container_key is None:
        # allow other metadata layouts for testing, but default to CDMS key
        entity_container_key = 'Microsoft.Crm.Sdk.Data.Services.UKTIContext'
    with open(name_out, 'w') as cdmspsql_fh:
        cdmspsql_fh.write(
            separate_constraints(
                odata_sql_schema(name_in, entity_container_key)
            )
        )

if __name__ == '__main__':
    main(*sys.argv[1:])
