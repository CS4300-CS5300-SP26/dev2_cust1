### Fitness AI App

A Django-based fitness AI web application.

## Getting Started
`cd /dev2_cust1/fitness_ai_app`

`./setup_and_run.sh`

Visit http://localhost:3000 to see the app running

## Email varification for development 
1. Open the file .env.dev inside fitness_ai_app
2. At the bottom where it says "EMAIL_VERIFICATION_ENABLED" change "False" to "True" to enable the email varifications.
   If you don't want email varification for testing puposes, keep it on "False"
NOTE: Make sure you rerun the server manually when switching the between False and True, and vice versa. Also
   make sure your .env.dev file already exists. If not then run the setup_and_run.sh in the fitness_ai_app directory.

## Run tests

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
pip install -r requirements.txt
```

4. **Run all tests with coverage (recommended):**
```
python manage.py test_all
```
This single command runs all Django unit tests and Behave BDD tests with coverage, then prints a coverage report at the end.

5. Run unit tests only:
```
python manage.py test core -v2
```

6. Run BDD/acceptance tests only:
```
python manage.py behave
```

7. Generate an HTML coverage report (after running `test_all`):
```
coverage html
```
The report will be in `htmlcov/index.html`. Coverage threshold is set to 80%.

8. Install the pre-commit hook (runs tests automatically before each commit):
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
