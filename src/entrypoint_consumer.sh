#!/bin/sh
set -e

# Ожидание RabbitMQ (если нужно)
if [ -n "$RABBIT_HOST" ]; then
    echo "Waiting for RabbitMQ..."
    while ! nc -z "$RABBIT_HOST" "$RABBIT_PORT"; do
        sleep 1
    done
    echo "RabbitMQ started"
fi

# Ожидание базы данных (если consumer использует БД)
if [ -n "$DB_HOST" ]; then
    echo "Waiting for database..."
    while ! nc -z "$DB_HOST" "$DB_PORT"; do
        sleep 1
    done
    echo "Database started"
fi

exec "$@"