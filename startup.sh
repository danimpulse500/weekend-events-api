#!/bin/bash
set -e  # Exit on any error

echo "Starting application..."

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Create superuser
echo "Creating superuser..."
python manage.py create_superuser

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the server
echo "Starting Gunicorn..."
gunicorn config.wsgi:application
