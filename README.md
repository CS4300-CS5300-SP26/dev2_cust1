# Getting Started
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

4. Run all tests:
```
python manage.py test core -v2
```
python manage.py test core -v0  (if you want compacted version)
```
