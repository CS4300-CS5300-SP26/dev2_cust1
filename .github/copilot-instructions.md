# Fitness AI App (Django)

## Build, Test, and Lint

```bash
# Setup & run dev server (from fitness_ai_app/)
./setup_and_run.sh

# Run full test suite with coverage (recommended)
python manage.py test_all

# Run a single test
python manage.py test core.tests.SomeTestClass.test_method

# Run unit tests only
python manage.py test core -v2

# Run BDD tests only
python manage.py behave

# Generate HTML coverage report (after test_all)
coverage html   # output: htmlcov/index.html

# Install pre-commit hook
bash install_hooks.sh
# Skip tests for a single commit: SKIP_TESTS=1 git commit -m "message"
```

## Architecture

```
fitness_ai_app/
├── fitness_ai_app/     # Django project config (settings.py, urls.py)
├── core/               # Main app: models, views, forms, templates
│   ├── templates/      # Organized by feature: home_dash_dir/, nutrition_dir/, etc.
│   └── management/commands/test_all.py
├── features/           # Behave BDD tests (*.feature + steps/)
└── .env                # Environment config (copied from .env.example)
```

**Key modules:**
- `core/models.py`: User-related models (EmailVerification, Meal, FoodItem)
- `core/views.py`: Auth flows, nutrition CRUD, OpenAI chat integration
- `core/adapter.py`: Custom django-allauth social adapter

**Templates follow feature-based directories:** `core/templates/{feature}_dir/`

## Key Conventions

- **Environment:** `.env` lives at `fitness_ai_app/.env` (loaded via python-dotenv in settings.py)
- **Coverage threshold:** 80% minimum (configured in `.coveragerc`)
- **Authentication:** Uses django-allauth for social login (Google, Apple, Facebook, Instagram)
- **Email verification:** Toggle with `EMAIL_VERIFICATION_ENABLED` env var (False = auto-activate for dev)
- **Database:** SQLite locally; PostgreSQL in production (via `DATABASE_URL`)

## When Changing Environment or Tests

Keep these files in sync:
- `fitness_ai_app/settings.py`
- `fitness_ai_app/.env.example`
- `fitness_ai_app/setup_and_run.sh`
- `.github/workflows/tests.yml`