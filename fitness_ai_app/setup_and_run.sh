#!/usr/bin/env bash

if [ ! -d ~/myenv ]; then
  python3 -m venv ~/myenv --system-site-packages
fi
source ~/myenv/bin/activate
python manage.py runserver 0.0.0.0:3000
