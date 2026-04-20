#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
mkdir -p lint-reports

echo "Running flake8... (output -> lint-reports/flake8.txt)"
flake8 . --exclude=venv,env,.venv,staticfiles,core/migrations,fitness_ai_app/migrations --max-line-length=120 --exit-zero > lint-reports/flake8.txt || true

echo "Running pylint... (output -> lint-reports/pylint.json)"
# Run pylint on app modules only, ignore migrations
pylint --output-format=json --ignore=migrations core fitness_ai_app > lint-reports/pylint.json || true

echo "Lint reports written to lint-reports/ (flake8.txt, pylint.json)"
