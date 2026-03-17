# Fitness AI App

A Django-based fitness AI web application.

## Getting Started
`cd /dev2_cust1/fitness_ai_app`

`./setup_and_run.sh`

Visit http://localhost:3000 to see the app running



# Run tests

1. Activate the virtual environment:
```
source ~/venv_dev2-cust1/bin/activate
```

2. Navigate to the project directory:
```
cd dev2_cust1/fitness_ai_app
```

3. Install dependencies (if not already installed):
```
pip install django django-allauth requests PyJWT cryptography
```

4. Run all unit tests:
```
python manage.py test core -v2
```
Or use `-v0` for compact output:
```
python manage.py test core -v0
```

5. Run BDD/acceptance tests:
```
python manage.py behave
```

6. Run tests with coverage:
```
coverage run --source=core manage.py test core
coverage run -a --source=core manage.py behave
coverage report
```
Generate an HTML coverage report:
```
coverage html
```
The report will be in `htmlcov/index.html`. Coverage threshold is set to 80%.

7. Install the pre-commit hook (runs tests automatically before each commit):
```
bash install_hooks.sh
```
To skip tests on a commit: `SKIP_TESTS=1 git commit -m "message"`

## AI Usage Citation

This project was generated with the assistance of **Claude Opus 4.6** (Anthropic), used via **GitHub Copilot CLI**, under the direction of the development team.

### What was used
- **AI Tool:** Claude Opus 4.6 (model ID: `claude-opus-4.6`) through GitHub Copilot CLI

### What it was used for
- Generating the initial Django project structure, including settings, URL configuration, views, and templates
- Creating the setup and run script (`setup_and_run.sh`)
- Writing project boilerplate code (models, views, admin, apps configuration)

### How AI-generated content was incorporated
All AI-generated code was reviewed and approved by the development team before being committed to the repository. The AI served as a code-generation assistant, with the development team directing the design decisions, project requirements, and final implementation.
