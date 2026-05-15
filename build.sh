#!/usr/bin/env bash
# build.sh — Render build script
# Runs automatically during each Render deploy.
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py create_superuser_if_missing
