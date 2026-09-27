#!/usr/bin/env bash
# exit on error
set -o errexit

# Add 'todoproject/' before the filenames
pip install -r todoproject/requirements.txt

python todoproject/manage.py collectstatic --no-input
python todoproject/manage.py migrate
