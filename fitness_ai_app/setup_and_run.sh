#!/usr/bin/env bash

if [ ! -d ~/venv_dev2-cust1 ]; then
  python3 -m venv ~/venv_dev2-cust1 --system-site-packages
fi

source ~/venv_dev2-cust1/bin/activate
pip install django djangorestframework pytest
python manage.py collectstatic
python manage.py runserver 0.0.0.0:3000
