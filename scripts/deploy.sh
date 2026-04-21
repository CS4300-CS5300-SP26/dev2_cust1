#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# deploy.sh  –  Run on the Droplet by the GitHub Actions deploy workflow.
#
# Strategy for gunicorn worker stability:
#   "systemctl reload gunicorn" sends SIGHUP to the master process, which
#   spawns fresh workers with the new code and only terminates old workers
#   once they have finished their current requests.  This is a zero-dropped-
#   request reload, unlike "restart" which kills everything immediately.
#
#   nginx holds the Unix socket open between reloads, so incoming requests
#   are queued at the socket level rather than receiving a connection error.
# ---------------------------------------------------------------------------
set -euo pipefail

APP_DIR="/var/www/fitness-ai-app"
VENV="$APP_DIR/venv/bin/activate"
DJANGO_DIR="$APP_DIR/fitness_ai_app"

echo "==> [1/6] Pulling latest code from main..."
cd "$APP_DIR"
git pull origin main

echo "==> [2/6] Installing Python dependencies..."
# shellcheck source=/dev/null
source "$VENV"
pip install --quiet -r "$DJANGO_DIR/requirements.txt"

echo "==> [3/6] Collecting static files..."
cd "$DJANGO_DIR"
python manage.py collectstatic --noinput --clear

echo "==> [4/6] Running database migrations..."
python manage.py migrate --noinput
python manage.py populate_exercise_db --noinput

echo "==> [5/6] Setting up social app logins..."
python manage.py setup_social_apps

echo "==> [6/6] Gracefully reloading gunicorn workers..."
# reload (SIGHUP) lets in-flight requests finish before workers are replaced.
# If gunicorn is not running at all, fall back to a clean start.
if systemctl is-active --quiet gunicorn; then
    sudo systemctl reload gunicorn
else
    echo "    gunicorn was not running – starting it now."
    sudo systemctl start gunicorn
fi

echo ""
echo "✓  Deployment complete."
