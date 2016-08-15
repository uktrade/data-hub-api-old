import logging
import sqlparse


def is_create(token):
    'Return a boolean representation of whether a token is a CREATE statement'
    return token.get_type() == 'CREATE'

def is_parens(token):
    'Return a boolean representation of whether a token is a parenthesis'
    return isinstance(token, sqlparse.sql.Parenthesis)

OUTPUT_TEMPLATE = '{0}\n{1}\n'


def main(schema):
    '''
    Open the SQL schema at the passed file name and return the same schema
    transformed such that foreign key constraints appear onlyl after table
    creation statements.

    NOTE: It is assumed that the SQL is the result of running the script in
    odata_sql_schema.py; ie. it's SQL output by PySLET.
    '''
    logger = logging.getLogger('separate_constraints')
    logger.info('Parsing generated schema ...')
    parsed = sqlparse.parse(schema)

    creates = []
    alters = []

    for table_number, original_create in enumerate(filter(is_create, parsed)):
        table_name = original_create.get_name()
        logger.debug(
            "Processing table number {0} ({1}) ...".format(
                table_number + 1, table_name
            )
        )
        original_columns = list(next(filter(is_parens, original_create.tokens)).flatten())
        for index, token in enumerate(original_columns):
            if token.match(sqlparse.tokens.Keyword, 'CONSTRAINT'):
                # happily, pyslet arranges constraints to be at the end, so we
                # can just bisect the token list
                columns = original_columns[:index - 2]  # strip comma
                constraints = original_columns[index:-1]
                break
        else:
            # this table doesn't have any constraints, let's keep the original
            # create statement
            creates.append(str(original_create))
            continue

        creates.append(
            '''CREATE TABLE "{0}" {1});'''.format(
                table_name, ''.join(map(str, columns))
            )
        )

        alters.append(
            '''ALTER TABLE "{0}" {1};'''.format(
                table_name, ''.join(map(str, constraints))
            ).replace('CONSTRAINT', 'ADD CONSTRAINT')
        )
    return OUTPUT_TEMPLATE.format(
        ''.join((map(str, creates))),
        ''.join((map(str, alters))),
    )
