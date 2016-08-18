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

Tests should be run by typing a command into your computer terminal. That
command is this::

    make test

There is further documentation about running tests in ``Makefile``.

There is a set of integration tests which use private configuration to connect
to a vanilla Microsoft Dynamics CRM 2011 server. These use NTLM authentication
and require the following settings:

* ``CDMS_BASE_URL``
* ``CDMS_USERNAME``
* ``CDMS_PASSWORD``

In addition, the ``TEST_INTEGRATION`` setting must be set to ``True`` for
integration tests to be run (and not skipped). Default behaviour if this
setting is missing is for the tests to be skipped by the ``skipIntegration``
decorator.

The settings above can all be set via environment variables - ``DJANGO__``
(Django dunder) should be prepended to the setting name. For example, override
the ``CDMS_PASSWORD`` setting by creating the ``DJANGO__CDMS_PASSWORD`` env
var.


Requirements
............

Requirements are managed with ``pip-tools``, and the packages required are
defined in ``*.in`` files instead of ``requirements*.txt`` files. The
``pip-tools`` suite is installed as part of the local requirements.

To add a dependency, locate the appropriate ``*.in`` file and add just the name
of it there. The version number is only required if a particular version of the
library is required. The latest version will be chosen by default when
compiling.

To recompile the requirements which will add any new packages specified in the
``*.in`` files do::

    make requirements

In order to update a single package version, remove its lines from the compiled
corresponding ``.txt`` files. The next call to ``make requirements`` will
reevaluate the latest version for packages that do not have corresponding lines
in the ``.txt`` file and they will be updated as required.

To update all requirements to the latest version (including updating all
packages that are not pinned in the ``.in`` file with a particular version
number), the ``clean`` recipe will clean out all ``*.txt`` files if you have
``pip-tools`` installed. Then the ``all`` recipe can be used to rebuild them
all::

    cd requirements
    make clean all

To update a particular requirements file use ``make [file].txt`` (or find the
specific commands at the top of any of the ``.txt`` files)::

    cd requirements
    make testing.txt

Recompiling a single ``.txt`` file will maintain the package versions that it
contains and just update any new / remove any missing packages.

If in doubt about what ``make`` is about to run at any stage, it can be helpful
to ask for a dry-run and inspect the commands that were planned::

    make -n requirements
