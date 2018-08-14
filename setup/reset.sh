#!/usr/bin/env bash

pkill -f "celery"
rm ../*.pyc
rm ../lib/*.pyc
rm ../csdb.sqlite3
echo "flushdb" | redis-cli
/etc/init.d/redis-server restart
