#!/usr/bin/env bash

if [ ! -d ~/venv_dev2-cust1 ]; then
  python3 -m venv ~/venv_dev2-cust1 --system-site-packages
fi

source ~/venv_dev2-cust1/bin/activate
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ./.env.dev ]; then
  cp ./.env.example ./.env.dev
  echo "############################ Don't forget to set up the environment passwords ###########################"
else
  echo "✓ .env.dev file already exists"
fi

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver 0.0.0.0:3000
