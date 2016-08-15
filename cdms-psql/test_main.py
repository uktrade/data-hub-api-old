import os
import tempfile
from separate_constraints import main as separate_constraints
from main import main

TEST_CASES_SEPARATE_CONSTRAINTS = (
    (
        'Contactcontactorders_associationSalesOrder.sql',
        'Contactcontactorders_associationSalesOrder-out.sql',
    ),
    (
        'SystemUserSet.sql',
        'SystemUserSet-out.sql',
    ),
)

TEST_CASES_MAIN = (
    ('weather-metadata.xml', 'weather.sql', 'WeatherSchema.CambridgeWeather'),
)

def test_separate_constraints():
    for name_in, expected_name in TEST_CASES_SEPARATE_CONSTRAINTS:
        with open(os.path.join('fixtures', expected_name), 'r') as expected_fh:
            expected = expected_fh.read()
        with open(os.path.join('fixtures', name_in), 'r') as metadata_fh:
            out = separate_constraints(metadata_fh.read())
            assert out == expected

def test_main():
    for name_in, expected_name, entity_container_key in TEST_CASES_MAIN:
        with open(os.path.join('fixtures', expected_name), 'r') as expected_fh:
            expected = expected_fh.read()
        with tempfile.NamedTemporaryFile() as temp_fh:
            main(os.path.join('fixtures', name_in), temp_fh.name, entity_container_key)
            temp_fh.seek(0)  # needed?
            assert expected == temp_fh.read().decode('utf8')

