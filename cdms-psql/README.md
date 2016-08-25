# Tools for converting OData `metadata.xml` to PostgreSQL schema

CDMS exposes an OData endpoint, which in turn exposes what is hoped to be the
schema for the underlying MS Dynamics instance. This directory contains scripts
that take in the `metadata.xml` file describing the OData endpoint’s schema and
output an SQL file describing the same schema for Postgres.

There is also a Bash script and Git patch for producing a properly configured
Postgres installation (allowing for long column names). It is tested on OSX El
Capitan, but should run on Linux too.

## Installation

Requirements are listed in `requirements.txt`, if you have Pip you can just use
`pip install -r requirements.txt` to install required packages.

## Usage

The scripts are “packaged” by the entrypoint `main.py` which can be run from
the command line and takes two arguments; the name of the input metadata file
and the name of the output SQL file. For example:

```
python main.py cdms-odata-schema.xml cdms-psql-schema.sql
```

## Tests

There is a very small suite of tests that cover this code, since most of the
functionality comes from the Python library PySLET. These tests can be invoked
by running the following command:

```
py.test
```
