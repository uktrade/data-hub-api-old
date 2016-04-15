Data Hub API Overview
=====================

API for the UKTI Data Hub.

Official docs on `Read the Docs <http://data-hub-api.readthedocs.org/>`_


Dependencies
............

-  `Virtualenv <http://www.virtualenv.org/en/latest/>`_
-  `Most recent version of pip`
-  `Python 3.5 <http://www.python.org/>`_ (Can be installed using ``brew``)
-  `Postgres 9.5+ <http://www.postgresql.org/>`_

Installation
............

Clone the repository:

::

    git clone git@github.com:UKTradeInvestment/data-hub-api.git


Next, create the environment and start it up:

::

    cd data-hub-api
    virtualenv env --python=python3.5

    source env/bin/activate


Update pip to the latest version:

::

    pip install -U pip


Install python dependencies:

::

    pip install -r requirements/local.txt


Create the database in postgres called `data-hub-api`.


For OSX, update the ``PATH`` and ``DYLD_LIBRARY_PATH`` environment
variables if necessary:

::

    export PATH="/Applications/Postgres.app/Contents/MacOS/bin/:$PATH"
    export DYLD_LIBRARY_PATH="/Applications/Postgres.app/Contents/MacOS/lib/:$DYLD_LIBRARY_PATH"


Create a ``local.py`` settings file from the example file and set the CDMS settings/credentials:

::

    cp data-hub-api/settings/local.example.py data-hub-api/settings/local.py


Sync and migrate the database:

::

    ./manage.py migrate


Start the server:

::

    ./manage.py runserver 8000
