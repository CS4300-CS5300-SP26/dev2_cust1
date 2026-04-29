"""Step definitions for authentication-related BDD scenarios."""

from behave import given, when, then
from django.contrib.auth.models import User


# ── Given steps ──────────────────────────────────────────────────────────────

@given('the site is available')
def step_site_available(context):
    pass


@given('I am logged in as "{email}" with password "{password}"')
def step_logged_in(context, email, password):
    User.objects.filter(username=email).delete()
    User.objects.create_user(username=email, email=email, password=password)
    context.test.client.login(username=email, password=password)


@given('I am not logged in')
def step_not_logged_in(context):
    context.test.client.logout()


@given('a user exists with email "{email}"')
def step_user_exists(context, email):
    User.objects.get_or_create(
        username=email,
        defaults={'email': email, 'is_active': True}
    )


@given('a registered user "{email}" with password "{password}"')
def step_user_exists_with_password(context, email, password):
    User.objects.filter(username=email).delete()
    User.objects.create_user(username=email, email=email, password=password)

# ── When steps ───────────────────────────────────────────────────────────────


@when('I visit the home page')
def step_visit_home(context):
    context.response = context.test.client.get('/')


@when('I visit the registration page')
def step_visit_registration(context):
    context.response = context.test.client.get('/user_get_started/')


@when('I visit the login page')
def step_visit_login(context):
    context.response = context.test.client.get('/user_login/')


@when('I visit "{url}"')
def step_visit_url(context, url):
    context.response = context.test.client.get(url)


@when('I register with email "{email}" and password "{password}"')
def step_register(context, email, password):
    context.response = context.test.client.post('/user_get_started/', {
        'email': email,
        'password': password,
        'confirm_password': password,
    })


@when('I register with email "{email}" password "{password}" confirm "{confirm}"')
def step_register_confirm(context, email, password, confirm):
    context.response = context.test.client.post('/user_get_started/', {
        'email': email,
        'password': password,
        'confirm_password': confirm,
    })


@when('I log in as "{email}" with password "{password}"')
def step_login(context, email, password):
    context.response = context.test.client.post('/user_login/', {
        'email': email,
        'password': password,
    })


@when('I log out')
def step_logout(context):
    context.response = context.test.client.get('/user_logout/')


# ── Then steps ───────────────────────────────────────────────────────────────

@then('the response status should be {code:d}')
def step_response_status(context, code):
    assert context.response.status_code == code, (
        f'Expected {code}, got {context.response.status_code}'
    )


@then('I should see "{text}"')
def step_see_text(context, text):
    content = context.response.content.decode()
    assert text in content, f'"{text}" not found in response'


@then('I should be redirected to "{name}"')
def step_redirected_to(context, name):
    assert context.response.status_code == 302, (
        f'Expected redirect (302), got {context.response.status_code}'
    )
    assert name in context.response.url, (
        f'Expected redirect to contain "{name}", got "{context.response.url}"'
    )


@then('I should be redirected to the splash page')
def step_redirected_splash(context):
    assert context.response.status_code == 302


@then('I should be redirected to the login page')
def step_redirected_login(context):
    assert context.response.status_code == 302
    assert 'user_login' in context.response.url or 'login' in context.response.url, (
        f'Expected redirect to login page, got "{context.response.url}"'
    )


@then('the user "{email}" should not exist')
def step_user_not_exist(context, email):
    assert not User.objects.filter(username=email).exists(), (
        f'User "{email}" unexpectedly exists'
    )


@then('the user "{email}" should be active')
def step_user_active(context, email):
    user = User.objects.get(username=email)
    assert user.is_active, f'User "{email}" is not active'
