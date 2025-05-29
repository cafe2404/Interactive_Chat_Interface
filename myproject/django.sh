#!/bin/bash
echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate
echo "Migrations done."

echo "Starting Daphne..."
exec daphne -b 0.0.0.0 -p 8000 myproject.asgi:application



