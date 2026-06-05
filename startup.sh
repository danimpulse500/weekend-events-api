#!/bin/bash

# Run migrations
python manage.py migrate

# Create superuser
python manage.py create_superuser

# Start the server
gunicorn config.wsgi:application
