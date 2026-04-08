#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# setup_droplet.sh  –  One-time setup for a fresh DigitalOcean Droplet.
#
# Run this manually as root (or with sudo) the first time only.
# After this, all subsequent deploys are handled by deploy.sh via GitHub Actions.
#
# Assumptions:
#   - Ubuntu 22.04 LTS Droplet
#   - You have SSH access as root or a sudo user
#   - Your GitHub repo is accessible (public, or you add a deploy key)
# ---------------------------------------------------------------------------
set -euo pipefail

REPO_URL="https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO.git"
APP_DIR="/var/www/fitness-ai-app"
PYTHON_VERSION="python3.12"

echo "==> Installing system packages..."
apt-get update -qq
apt-get install -y git nginx "$PYTHON_VERSION" "$PYTHON_VERSION"-venv "$PYTHON_VERSION"-dev \
    build-essential libpq-dev

echo "==> Creating app directory and cloning repo..."
mkdir -p "$APP_DIR"
git clone "$REPO_URL" "$APP_DIR"

echo "==> Creating Python virtual environment..."
"$PYTHON_VERSION" -m venv "$APP_DIR/venv"
source "$APP_DIR/venv/bin/activate"
pip install --quiet -r "$APP_DIR/fitness_ai_app/requirements.txt"

echo "==> Creating .env file..."
cp "$APP_DIR/fitness_ai_app/.env.example" "$APP_DIR/fitness_ai_app/.env"
echo ""
echo "  !! Edit $APP_DIR/fitness_ai_app/.env now with your production values."
echo "  !! At minimum set: DJANGO_SECRET_KEY, DATABASE_URL, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS"
echo ""
read -rp "Press Enter once .env is ready..."

echo "==> Running initial migrations and collectstatic..."
cd "$APP_DIR/fitness_ai_app"
python manage.py migrate --noinput
python manage.py collectstatic --noinput --clear

echo "==> Creating Django superuser..."
python manage.py createsuperuser

echo "==> Creating log directory for gunicorn..."
mkdir -p /var/log/gunicorn
chown www-data:www-data /var/log/gunicorn

echo "==> Setting ownership..."
chown -R www-data:www-data "$APP_DIR"

echo "==> Making deploy script executable..."
chmod +x "$APP_DIR/scripts/deploy.sh"

echo "==> Installing systemd service files..."
cp "$APP_DIR/scripts/gunicorn.socket"  /etc/systemd/system/gunicorn.socket
cp "$APP_DIR/scripts/gunicorn.service" /etc/systemd/system/gunicorn.service

systemctl daemon-reload
systemctl enable --now gunicorn.socket
systemctl enable gunicorn

echo "==> Installing nginx config..."
cp "$APP_DIR/scripts/nginx.conf" /etc/nginx/sites-available/fitness-ai-app
ln -sf /etc/nginx/sites-available/fitness-ai-app /etc/nginx/sites-enabled/fitness-ai-app
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo ""
echo "==> Allowing the deploy user (www-data) to reload gunicorn without a password..."
echo "www-data ALL=(ALL) NOPASSWD: /bin/systemctl reload gunicorn, /bin/systemctl start gunicorn" \
    >> /etc/sudoers.d/gunicorn-deploy
chmod 440 /etc/sudoers.d/gunicorn-deploy

echo ""
echo "✓  Droplet setup complete."
echo ""
echo "Next steps:"
echo "  1. Add the following secrets to your GitHub repo (Settings → Secrets → Actions):"
echo "       DROPLET_IP    – this Droplet's public IP"
echo "       DROPLET_USER  – the SSH user (e.g. root or deploy)"
echo "       DROPLET_SSH_KEY – private key whose public key is in ~/.ssh/authorized_keys here"
echo "  2. Push to main – the GitHub Actions deploy workflow will trigger automatically"
echo "     after the test suite passes."
