import sqlparse


def is_create(token):
    return token.get_type() == 'CREATE'

def is_parens(token):
    return isinstance(token, sqlparse.sql.Parenthesis)

def main():
    # with open('cdms-pgsql.sql', 'r') as schema_fh:
    with open('SystemUserSet.sql', 'r') as schema_fh:
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
                columns = original_columns.tokens[:index]
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
        alters.append(
            "ALTER TABLE {0} ({1}".format(
                name, ''.join(map(str, constraints))
            )
        )
    list(map(print, creates))
    list(map(print, alters))


if __name__ == '__main__':
    main()
