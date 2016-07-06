Data Hub API Overview
=====================

API for the UKTI Data Hub.

Official docs on `Read the Docs <http://data-hub-api.readthedocs.org/>`_


Dependencies
............

- (non-essential) `Virtualenv <http://www.virtualenv.org/en/latest/>`_

- Pip 8.1.1. This particular version is advanced enough to be used by
  `pip-tools <https://github.com/nvie/pip-tools`_, but not too advanced that
  the latest version breaks it.

- `Python 3.5 <http://www.python.org/>`_ (Can be installed using ``brew``)

- `Postgres 9.5+ <http://www.postgresql.org/>`_ :

    * Libraries are required to build psycopg2. For debian flavoured linux::

        sudo apt-get install postgresql postgresql-server-dev-9.5

    * Postgres user that will create / manage databases should also be able to
      create / install extensions.

    * Postgres user configured by the default settings files is 'postgres'. You
      will either want to override this with your own settings file, or use the
      'postgres' user.

- XML processing is provided by ``lxml`` which has its own dependencies::

      sudo apt-get install libxml2-dev libxslt-dev python3-dev

- Crypto is provided by ``cryptography``, which needs SSL and FFI libraries::

      sudo apt-get install libssl-dev libffi-dev


Installation
............

Clone the repository::

    git clone git@github.com:UKTradeInvestment/data-hub-api.git

Next, create the environment and start it up::

    cd data-hub-api
    make venv

    source env/bin/activate

Install python dependencies::

    pip install -r requirements/local.txt

Create the database in postgres called `data-hub-api`.

For OSX, update the ``PATH`` and ``DYLD_LIBRARY_PATH`` environment
variables if necessary::

    export PATH="/Applications/Postgres.app/Contents/MacOS/bin/:$PATH"
    export DYLD_LIBRARY_PATH="/Applications/Postgres.app/Contents/MacOS/lib/:$DYLD_LIBRARY_PATH"

Create a ``local.py`` settings file from the example file and set the CDMS
settings/credentials::

    cp data-hub-api/settings/local.example.py data-hub-api/settings/local.py

Sync and migrate the database::

    ./manage.py migrate

Start the server::

    ./manage.py runserver 8000


Testing
.......

Tests should be run with the testing settings file::

    ./manage.py test --settings=data-hub-api.settings.testing


Requirements
............

Requirements are managed with ``pip-tools``. This is installed as part of the
local requirements.

To update all requirements, the default ``make`` command will clean out all
``*.txt`` files and rebuild them all::

    make requirements

To update a particular requirements file use ``make [file].txt`` (or find the
specific commands at the top of any of the ``.txt`` files)::

    cd requirements
    make testing.txt
