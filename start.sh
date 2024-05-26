#!/usr/bin/env bash

docker-compose down

set -e

docker-compose up -d
python3 api_broker/manage.py runserver --noreload 127.0.0.1:8080

