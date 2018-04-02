#!/bin/sh
source venv/bin/activate
flask db upgrade
exec gunicorn --certfile fullchain.pem --keyfile privkey.pem -b :443 --access-logfile - --error-logfile - iwegarde:app
