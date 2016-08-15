#!/bin/bash
RELEASE="REL9_5_3"
set -e
git clone --branch $RELEASE https://github.com/postgres/postgres.git
cd postgres
git checkout $RELEASE
git apply ../postgres-namedatalen.patch
./configure
make
sudo make install
mkdir ~/db
/usr/local/pgsql/bin/initdb ~/db
/usr/local/pgsql/bin/pg_ctl -D ~/db -l logfile start
# boom
