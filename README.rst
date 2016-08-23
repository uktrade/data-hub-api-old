Data Hub API Overview
=====================

API for the UKTI Data Hub.

Official docs on `Read the Docs <http://data-hub-api.readthedocs.org/>`_


Dependencies
............

- (non-essential) `Virtualenv <http://www.virtualenv.org/en/latest/>`_

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

- For development:

  * `Pip 8 <https://pypi.python.org/pypi/pip>`_ : This particular version is
    advanced enough to be used by `pip-tools
    <https://github.com/nvie/pip-tools>`_.


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

Tests should be run by typing a command into your computer terminal. That
command is this::

    make test

There is further documentation about running tests in ``Makefile``.


Requirements
............

Requirements are managed with ``pip-tools``, and the packages required are
defined in ``*.in`` files instead of ``requirements*.txt`` files. The
``pip-tools`` suite is installed as part of the local requirements.

To add a dependency, locate the appropriate ``*.in`` file and add there as you
would with a standard Pip requirements file.

To update all requirements (including updating all packages that are not pinned
in the ``.in`` file with a particular version number), the default ``make``
command will clean out all ``*.txt`` files and rebuild them all::

    make requirements

To update a particular requirements file use ``make [file].txt`` (or find the
specific commands at the top of any of the ``.txt`` files)::

    cd requirements
    make testing.txt

Recompiling a single ``.txt`` file will maintain the package versions that it
contains and just update any new / remove any missing packages.
