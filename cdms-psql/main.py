from odata_sql_schema import main as odata_sql_schema
from separate_constraints import main as separate_constraints


def main(name_in, name_out):
    'Convert OData metadata.xml to SQL schema'
    with open(name_out, 'w') as cdmspsql_fh:
        cdmspsql_fh.write(separate_constraints(odata_sql_schema(name_in)))
