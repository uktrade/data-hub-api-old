import itertools
import collections
import sqlalchemy as sqla


def table_dep_names(metadata, table_name, depth):
    print("{0}{1}".format(depth * ' ', table_name))
    table = metadata.tables[table_name]
    return set(filter(
        lambda dep_name: dep_name != table_name,  # ignore self-reference
        map(
            lambda fkey: fkey.column.table.name,
            filter(
                lambda fkey: not fkey.column.nullable,  # ignore nullable
                table.foreign_keys
            )
        )
    ))


def follow_deps(metadata, table_name, depth=0):
    if depth > 10:
        return
    for dep_name in table_dep_names(metadata, table_name, depth):
        follow_deps(metadata, dep_name, depth + 1)


def main():
    engine = sqla.create_engine('postgresql://localhost/cdms_psql')
    metadata = sqla.MetaData(bind=engine)
    metadata.reflect()
    dependencies = collections.defaultdict(set)
    added = set()
    table = metadata.tables['AuditSet']
    import ipdb;ipdb.set_trace()
    for table_name in metadata.tables:
        # table = metadata.tables[table_name]
        follow_deps(metadata, table_name)
    '''
        if len(metadata.tables[table_name].foreign_keys) == 0:
            dependencies[0].add(table_name)
            added.add(table_name)
    depth = 1
    # while sum(1 for _ in itertools.chain.from_iterable(dependencies.values())) < len(metadata.tables):
    while len(added) < len(metadata.tables):
        print('--')
        for table_name in filter(lambda x: x not in added, metadata.tables):
            for dep_name in table_deps:
                if dep_name not in added:

            if table_deps.issubset(added.union({table_name})):
                dependencies[depth].add(table_name)
                added.add(table_name)
            else:
                if len(table_deps.intersection(added)) > 0:
                    print(table_name)
                pass
        depth += 1
        if depth > 10:
            break
    '''

if __name__ == '__main__':
    main()
