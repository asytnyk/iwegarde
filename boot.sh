#!/bin/sh
sleep 5
source venv/bin/activate
flask db upgrade
#exec gunicorn --certfile fullchain.pem --keyfile privkey.pem -b :5000 --access-logfile - --error-logfile - iwegarde:app
exec gunicorn -b :5000 --access-logfile - --error-logfile - iwegarde:app
