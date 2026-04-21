#!/usr/bin/env bash

if [ ! -d ~/venv_dev2-cust1 ]; then
  python3 -m venv ~/venv_dev2-cust1 --system-site-packages
fi

source ~/venv_dev2-cust1/bin/activate
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ./.env ]; then
  cp ./.env.example ./.env
  echo ""
  echo "🔑 New .env file created from .env.example"
  echo "⚠️  IMPORTANT: Add your OAuth credentials to .env:"
  echo "   - GOOGLE_CLIENT_ID"
  echo "   - GOOGLE_CLIENT_SECRET"
  echo "   - (and any other provider secrets)"
  echo ""
  echo "📧 For email delivery in production, also set:"
  echo "   - EMAIL_BACKEND / EMAIL_HOST / EMAIL_PORT / EMAIL_USE_TLS / EMAIL_USE_SSL"
  echo "   - EMAIL_HOST_USER / EMAIL_HOST_PASSWORD / DEFAULT_FROM_EMAIL"
  echo ""
  echo "Then run this script again to register them."
  echo "################################################################################"
  exit 0
else
  echo "✓ .env file already exists"
fi

python manage.py migrate
python manage.py populate_exercise_db
python manage.py collectstatic --noinput
python manage.py setup_social_apps
python manage.py runserver 0.0.0.0:3000
