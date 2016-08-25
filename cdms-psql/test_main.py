import os
from separate_constraints import main as separate_constraints

TEST_CASES = (
    (
        'Contactcontactorders_associationSalesOrder.sql',
        'Contactcontactorders_associationSalesOrder-out.sql',
    ),
    (
        'SystemUserSet.sql',
        'SystemUserSet-out.sql',
    ),
)

def test():
    for name_in, name_out in TEST_CASES:
        with open(os.path.join('fixtures', name_out), 'r') as out_fh:
            out = separate_constraints(os.path.join('fixtures', name_in))
            expected = out_fh.read()
            assert out == expected
