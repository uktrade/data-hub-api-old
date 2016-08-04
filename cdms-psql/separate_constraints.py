import sqlparse


def is_create(token):
    return token.get_type() == 'CREATE'

def is_parens(token):
    return isinstance(token, sqlparse.sql.Parenthesis)

def main(name):
    with open(name, 'r') as schema_fh:
        parsed = sqlparse.parse(schema_fh.read())

    creates = []
    alters = []

    for original_create in filter(is_create, parsed):
        name = original_create.get_name()
        original_columns = next(filter(is_parens, original_create.tokens))
        for index, token in enumerate(original_columns.tokens):
            if token.match(sqlparse.tokens.Keyword, 'CONSTRAINT'):
                # happily, pyslet arranges constraints to be at the end, so we
                # can just bisect the token list
                columns = original_columns.tokens[:index - 2]  # strip comma
                constraints = original_columns.tokens[index:]
                break
        else:
            # this table doesn't have any constraints, let's keep the original
            # create statement
            creates.append(str(original_create))
            continue

        creates.append(
            "CREATE TABLE {0} {1});".format(
                name, ''.join(map(str, columns))
            )
        )

        '''
        indices = []  # where we need to put add an ADD
        for index, token in enumerate(constraints):
            if token.match(sqlparse.tokens.Keyword, 'CONSTRAINT'):
                indices.append(index)

        for index in indices[1:]:
            constraints.insert(index, ' , ADD')
        '''

        alters.append(
            "ALTER TABLE {0} ({1};".format(
                name, ''.join(map(str, constraints))
            ).replace('CONSTRAINT', 'ADD CONSTRAINT')
        )
    list(map(print, creates))
    list(map(print, alters))


if __name__ == '__main__':
    main('./Contactcontactorders_associationSalesOrder.sql')
