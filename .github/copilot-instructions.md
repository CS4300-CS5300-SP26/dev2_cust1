Repository: Fitness AI App (Django)

Purpose
- Guide Copilot sessions with repository-specific commands, architecture notes, and conventions.

Build, test, and lint commands
- Setup & run local dev server (creates venv and .env if needed):
  - cd fitness_ai_app && ./setup_and_run.sh
- Install dependencies: pip install -r requirements.txt (run from fitness_ai_app)

- Run full test suite (recommended):
  - python manage.py test_all
    - Runs Django unit tests (core) and Behave BDD tests with coverage.

- Run unit tests only:
  - python manage.py test core -v2
  - From CI/workflow and hooks the shorter command used is: coverage run --source=core manage.py test core -v2

- Run BDD tests only:
  - python manage.py behave
  - In CI: coverage run -a --source=core manage.py behave --no-capture

- Generate HTML coverage report (after running test_all):
  - coverage html (output: htmlcov/index.html)

- Pre-commit hook (runs tests on staged changes):
  - bash install_hooks.sh (then commits trigger the hook)
  - To skip tests for a single commit: SKIP_TESTS=1 git commit -m "message"

High-level architecture
- Django project: fitness_ai_app/fitness_ai_app (settings, wsgi, asgi)
- Main app: core/ — business logic, API views, management commands (including test_all)
- BDD tests: features/ — behave scenarios and step implementations that exercise end-to-end flows
- Tests & coverage:
  - Unit tests target 'core' app and are instrumented for coverage reporting.
  - Behave scenarios run against the Django test environment via behave-django.
- Environment loading:
  - dotenv is used to load environment variables from a repository-root .env (loaded in settings.py)
  - setup_and_run.sh will copy .env.example → .env if missing.
- CI:
  - .github/workflows/tests.yml runs unit tests + BDD tests and reports coverage.
  - .github/workflows/ai-code-review.yml runs ai_review.py using OPENAI_API_KEY secret to generate PR feedback.

Key conventions / patterns
- Single-test targeting:
  - Use python manage.py test core.tests.SomeTestClass.test_method (Django test discovery) to run a single test.
- Coverage-first test flow:
  - Commands and hooks prefer running tests under coverage (coverage run) and appending BDD results with --append.
- Env file location:
  - .env is expected at repository root (fitness_ai_app/settings.py loads BASE_DIR/'.env'). Do not assume fitness_ai_app/.env.dev.
- Pre-commit behavior:
  - A repository pre-commit hook exists under fitness_ai_app/hooks/pre-commit. Use install_hooks.sh to copy it into .git/hooks.
- BDD step design:
  - Behave steps rely on Django models and the test database (use behave-django integration). Tests may mock environment variables using mock.patch.dict.
- Management commands:
  - test_all is the canonical way to run both unit and BDD tests for CI parity; prefer it when reproducing CI locally.

AI/assistant-specific notes
- When suggesting code changes that affect runtime behavior (settings, env vars, DB), ensure changes are reflected in setup_and_run.sh, README.md, and .github workflows to keep parity.
- The repo includes an AI code-review workflow that requires OPENAI_API_KEY; do not hardcode secrets in code or suggested patches.
- Avoid editing generated/third-party files (e.g., .github/workflows/*) unless the change is directly required for CI behavior.
- Do NOT commit changes to the repository. All edits should be proposed as patch suggestions and left uncommitted for the reviewer to commit manually.

Files to check when changing environment or tests
- fitness_ai_app/fitness_ai_app/settings.py
- fitness_ai_app/setup_and_run.sh
- fitness_ai_app/.env.example
- fitness_ai_app/core/management/commands/test_all.py
- fitness_ai_app/hooks/pre-commit
- .github/workflows/tests.yml and ai-code-review.yml

MCP Servers
- (None configured by default.)

Summary
- Added focused, repo-specific instructions for running, testing, and changing behavior. Ask if you want additional sections (e.g., database dev setup, common debugging commands, or a short glossary of core modules).