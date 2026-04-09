# Fitness AI App (Django)

## Build, Test, and Lint

```bash
# Setup & run dev server (from fitness_ai_app/)
./setup_and_run.sh

# Run full test suite with coverage (recommended)
python manage.py test_all

# Run a single test (unit tests)
python manage.py test core.tests.SomeTestClass.test_method

# Run unit tests only
python manage.py test core -v2

# Run BDD tests only
python manage.py behave

# Run Playwright integration tests
python test_nutrition_macro_playwright.py

# Generate HTML coverage report (after test_all)
coverage html   # output: htmlcov/index.html

# Install pre-commit hook (runs tests automatically before each commit)
bash install_hooks.sh
# To skip tests on a commit: SKIP_TESTS=1 git commit -m "message"
```

**Test Coverage Threshold:** 80% minimum (enforced by `.coveragerc`)

## Architecture

```
fitness_ai_app/
├── fitness_ai_app/        # Django project config (settings.py, urls.py)
├── core/                  # Main app: models, views, forms, templates
│   ├── models.py          # User, EmailVerification, Meal, FoodItem, Workout
│   ├── views.py           # Auth flows, nutrition CRUD, OpenAI chat, workouts
│   ├── forms.py           # Django forms for meals, food items
│   ├── adapter.py         # Custom django-allauth social adapter
│   ├── admin.py           # Django admin configuration
│   ├── management/commands/test_all.py  # Custom command: runs unit + BDD tests
│   ├── static/            # CSS, JavaScript
│   └── templates/         # Organized by feature (see below)
├── features/              # Behave BDD tests (*.feature + steps/)
├── db.sqlite3             # Local development database (SQLite)
└── .env                   # Environment config (copied from .env.example)
```

**Key Models:**
- `User`: Django default user model with email-based auth (django-allauth)
- `EmailVerification`: Tracks verification status and tokens
- `Meal`: Container for food items, belongs to user, has created_at timestamp
- `FoodItem`: Nutrition data (name, calories, protein, carbs, fats), includes completed toggle
- `Workout`: Exercise tracking with goal types and status

**Template Organization by Feature:**
```
core/templates/
├── core/                      # Base templates (login, signup, navbar, base.html)
├── home_dash_dir/             # Home dashboard feature
├── nutrition_dir/             # Nutrition tracking (meals, food items, macro display)
├── ai_dir/                    # AI chat integration
├── train_dir/                 # Workout/training feature
└── socal_dir/                 # Social/profile features
```

## Key Conventions

### Environment & Configuration
- **`.env` location:** Lives at `fitness_ai_app/.env` (loaded via python-dotenv in settings.py)
- **Database:** SQLite locally (`db.sqlite3`); PostgreSQL in production (via `DATABASE_URL`)
- **Virtual environment:** Located at `~/venv_dev2-cust1/` (created by setup_and_run.sh)

### Authentication
- **Framework:** django-allauth with social login (Google, Apple, Facebook, Instagram)
- **Social setup:** Run `python manage.py setup_social_apps` after adding OAuth credentials to `.env`
- **Email verification:** Controlled by `EMAIL_VERIFICATION_ENABLED` env var (False = auto-activate in dev)

### Testing & Coverage
- **Coverage threshold:** 80% minimum (enforced by `.coveragerc`)
- **Canonical test command:** `python manage.py test_all` (runs unit tests under coverage, then appends BDD results)
- **Test database:** Uses behave-django integration; test DB created/destroyed per run
- **Single test:** `python manage.py test core.tests.SomeTestClass.test_method`
- **Playwright tests:** Written in Python (not JavaScript); run against a live dev server

### Pre-commit Hook
- **Hook location:** `fitness_ai_app/hooks/pre-commit`
- **Installation:** `bash install_hooks.sh` copies hook to `.git/hooks/pre-commit`
- **Behavior:** Runs `python manage.py test_all` on every commit
- **Skip behavior:** Use `SKIP_TESTS=1 git commit -m "message"` to bypass tests

### File Synchronization
When changing environment variables, tests, or Django configuration, keep these in sync:
- `fitness_ai_app/settings.py`
- `fitness_ai_app/.env.example`
- `fitness_ai_app/setup_and_run.sh`
- `.github/workflows/tests.yml` (for CI)

## Common Development Tasks

### Adding a Feature
1. Create Django model in `core/models.py`
2. Create migration: `python manage.py makemigrations`
3. Apply migration: `python manage.py migrate`
4. Add view logic in `core/views.py` or create new views
5. Create template in `core/templates/{feature}_dir/`
6. **Always write tests first:** Add unit tests and BDD scenarios
7. Run `python manage.py test_all` to verify 80% coverage

### Modifying the Data Model
- After changing `core/models.py`, run: `python manage.py makemigrations && python manage.py migrate`
- **Important:** Test migrations with Behave tests to ensure data persists correctly
- FoodItem macros (protein, carbs, fats) are PositiveIntegerField with default=0

### Testing Nutrition Features
- Macro calculation happens in views.py (sums FoodItem fields where completed=True)
- Test with `python test_nutrition_macro_playwright.py` (requires running dev server)
- Unit tests in `core/tests.py`; BDD tests in `features/`

### Handling Environment Variables
- All env vars loaded at Django startup via `load_dotenv()`
- Use `env_bool()` helper in settings.py for boolean values
- `env_list()` helper for comma-separated lists
- Example: `EMAIL_VERIFICATION_ENABLED = env_bool('EMAIL_VERIFICATION_ENABLED', False)`

### Git Workflow
- Pre-commit hook runs `test_all` automatically on every commit
- If tests fail, commit is rejected
- Use `SKIP_TESTS=1 git commit -m "..."` to bypass (rarely needed)
- All code commits must include: `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>` (if AI-generated)
