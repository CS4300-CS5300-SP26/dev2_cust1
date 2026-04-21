### Fitness AI App

A Django-based fitness AI web application.

## Getting Started
`cd /dev2_cust1/fitness_ai_app`

`./setup_and_run.sh`

Visit http://localhost:3000 to see the app running

The setup script also seeds the exercise database for Django admin (`TrainingExercise`, `ExerciseType`, `MuscleGroup`, `Muscle`, `Equipment`) so these models are visible with data on first run.

## Social Authentication Setup

The app supports social authentication via Google, Facebook, Apple, and Instagram.

### Environment Variables Required

To enable social authentication, add the following variables to your `.env` file:

```
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Facebook OAuth (optional)
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_SECRET=your_facebook_secret

# Apple OAuth (optional)
APPLE_CLIENT_ID=your_apple_client_id
APPLE_SECRET=your_apple_secret

# Instagram OAuth (optional)
INSTAGRAM_APP_ID=your_instagram_app_id
INSTAGRAM_SECRET=your_instagram_secret
```

### Setting Up Social Apps

After populating your `.env` file with OAuth credentials, run:

```bash
python manage.py setup_social_apps
```

This command registers your OAuth applications with Django's socialaccount framework. The setup script reads credentials from your `.env` file and creates the necessary SocialApp objects in the database.

**Note:** If you already have a `.env` file and add new social auth credentials, simply run the `setup_social_apps` command again to register them.

## Email verification for development 
1. Open the file .env at the repository root
2. At the bottom where it says "EMAIL_VERIFICATION_ENABLED" change "False" to "True" to enable the email verifications.
   If you don't want email verification for testing purposes, keep it on "False"
NOTE: Make sure you rerun the server manually when switching between False and True, and vice versa. Also
   make sure your .env file already exists. If not then run the setup_and_run.sh in the fitness_ai_app directory.

### Email delivery in production (Droplet)

DigitalOcean Droplets can block outbound SMTP on ports 25/465/587. If password reset or verification emails hang/fail in production:

1. Use environment-based email transport settings (`EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`).
2. Prefer an email provider API over HTTPS, or SMTP on an alternate port like `2525` if supported by your provider.
3. Ensure `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`, and `EMAIL_VERIFICATION_ENABLED=True` are set in production.

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
