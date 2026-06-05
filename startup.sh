#!/usr/bin/env bash
set -e

# Run Django migrations and collect static files, then start Gunicorn.
# Designed for render.com where $PORT is provided by the platform.

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3
