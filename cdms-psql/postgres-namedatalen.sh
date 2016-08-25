set -e
git clone https://github.com/postgres/postgres.git
cd postgres
git checkout "REL9_5_3"
git apply ../postgres-namedatalen.patch
./configure
make
make install
/usr/local/pgsql/bin/initdb /usr/local/var/postgres
/usr/local/pgsql/bin/pg_ctl -D /usr/local/var/postgres -l logfile start
# boom
