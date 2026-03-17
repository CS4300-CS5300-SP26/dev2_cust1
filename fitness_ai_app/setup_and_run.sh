#!/usr/bin/env bash

if [ ! -d ~/venv_dev2-cust1 ]; then
  python3 -m venv ~/venv_dev2-cust1 --system-site-packages
fi

source ~/venv_dev2-cust1/bin/activate
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ../.env ]; then
  cat > ../.env << 'EOF'
# Gmail SMTP Configuration for Email Verification
# Get these credentials from: https://myaccount.google.com/apppasswords
# Steps:
# 1. Enable 2-Step Verification in your Google Account
# 2. Go to App passwords and generate a password for "Mail"
# 3. Copy the 16-character password below (without spaces)

EMAIL_HOST_USER=spotter.ai2026@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password-here
DEFAULT_FROM_EMAIL="Spotter.ai <spotter.ai2026@gmail.com>"
EOF
  echo "📧 Created .env file - Please add your Gmail App Password!"
  echo "   Edit ../.env and replace EMAIL_HOST_PASSWORD with your actual password"
else
  echo "✓ .env file already exists"
fi

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver 0.0.0.0:3000
