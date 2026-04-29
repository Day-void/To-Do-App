#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Move into the folder where manage.py lives
# cd todoproject

python manage.py collectstatic --no-input
python manage.py migrate
