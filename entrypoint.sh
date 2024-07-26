#!/bin/bash

# Apply database migrations
python manage.py migrate
# Use gunicorn to run the application
exec gunicorn ePubColab.wsgi:wsgi_application --bind 0.0.0.0:8000 --workers 3
