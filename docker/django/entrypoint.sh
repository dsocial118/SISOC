#!/bin/sh


echo "Waiting for MySQL to be ready..."
while ! mysqladmin ping -h"$DATABASE_HOST" --silent; do
    sleep 5
done

# Add a delay to ensure MySQL dump is fully processed
sleep 10

echo "MySQL is up and ready"

# Migrate and start the Django server
python manage.py migrate --noinput
python manage.py runserver 0.0.0.0:8000
