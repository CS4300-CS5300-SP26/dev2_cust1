# Copilot Instructions for Fitness AI App

## Build and Run

```bash
cd fitness_ai_app
./setup_and_run.sh        # First-time setup + runs server at localhost:3000
```

Activate the virtual environment for any manual commands:
```bash
source ~/venv_dev2-cust1/bin/activate
cd fitness_ai_app
```

## Testing

```bash
# Run all tests with coverage (recommended)
python manage.py test_all

# Run unit tests only
python manage.py test core -v2

# Run a single test class or method
python manage.py test core.tests.RegistrationFormTests
python manage.py test core.tests.RegistrationFormTests.test_valid_form

# Run BDD tests only
python manage.py behave

# Run a single BDD feature
python manage.py behave --include authentication

# Generate HTML coverage report (after test_all)
coverage html
```

Coverage threshold is **80%** (enforced in `.coveragerc`).

## Project Architecture

This is a Django 4.2 fitness tracking app (codenamed "Spotter.ai") with these layers:

- **`fitness_ai_app/`** - Django project settings, root URL config
- **`core/`** - Main app with all models, views, forms, and templates
- **`features/`** - Behave BDD tests with step definitions in `features/steps/`

### Key Models (core/models.py)
- `EmailVerification` - Email verification tokens for user registration
- `Meal` - User meals for a given date
- `FoodItem` - Food items within a meal, with calorie tracking

### Authentication
- Email/password registration with optional email verification
- Social login via django-allauth (Google, Apple, Facebook, Instagram)
- Set `EMAIL_VERIFICATION_ENABLED=True` in `.env.dev` to require email verification

### URL Structure
All routes are in `core/urls.py`. Main pages: `/`, `/home_dash/`, `/train/`, `/nutrition/`, `/ai/`, `/social/`

## Conventions

### Testing Pattern
- Unit tests in `core/tests.py` using Django's TestCase
- BDD tests in `features/*.feature` with steps in `features/steps/`
- Tests use `@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')` for email tests

### Environment Config
- Copy `.env.example` to `.env.dev` for local development
- Boolean env vars use `env_bool()` helper (accepts `1`, `true`, `yes`, `on`)
- List env vars use `env_list()` helper (comma-separated)

### Views Pattern
- Login-protected views use `@login_required` decorator
- POST-only views use `@require_POST` decorator
- Nutrition views pass date via query param `?date=YYYY-MM-DD`

### Templates
Templates are organized by feature in `core/templates/`:
- `core/` - Auth pages (splash, login, registration)
- `home_dash_dir/`, `train_dir/`, `nutrition_dir/`, `socal_dir/` - Feature pages

### Database
- SQLite for development (auto-created)
- PostgreSQL for production (via `DATABASE_URL` env var)
