#!/bin/bash

echo Connecting to DB...
while ! nc -z $POSTGRES_HOST $PGPORT; do
      sleep 0.5
done 

echo Applying migrations...
alembic upgrade head

exec "$@"