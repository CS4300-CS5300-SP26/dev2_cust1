Feature: User Authentication
  As a visitor or registered user
  I want to register, log in, and log out
  So that I can securely access my fitness data

  Background:
    Given the site is available

  Scenario: Visitor views the splash page
    When I visit the home page
    Then I should see "Spotter.ai"
    And the response status should be 200

  Scenario: Authenticated user is redirected from splash page
    Given I am logged in as "splash@spotter.ai" with password "testpass123"
    When I visit the home page
    Then I should be redirected to "home_dash"

  Scenario: Visitor views the registration page
    When I visit the registration page
    Then I should see "Get Started"
    And the response status should be 200

  Scenario: Successful user registration
    When I register with email "newuser@spotter.ai" and password "securepass123"
    Then I should be redirected to "user_login"

  Scenario: Registration rejected when passwords do not match
    When I register with email "mismatch@spotter.ai" password "securepass123" confirm "differentpass"
    Then the response status should be 200
    And the user "mismatch@spotter.ai" should not exist

  Scenario: Registration rejected for duplicate email
    Given a user exists with email "existing@spotter.ai"
    When I register with email "existing@spotter.ai" and password "securepass123"
    Then the response status should be 200

  Scenario: Visitor views the login page
    When I visit the login page
    Then I should see "Log In"
    And the response status should be 200

  Scenario: Successful login with valid credentials
    Given a registered user "loginbdd@spotter.ai" with password "testpass123"
    When I log in as "loginbdd@spotter.ai" with password "testpass123"
    Then I should be redirected to "home_dash"

  Scenario: Login fails with wrong password
    Given a registered user "wrongpw@spotter.ai" with password "testpass123"
    When I log in as "wrongpw@spotter.ai" with password "badpassword"
    Then the response status should be 200

  Scenario: Login page shows social login buttons
    When I visit the login page
    Then I should see "/login/google/"
    And I should see "/login/apple/"
    And I should see "/login/facebook/"
    And I should see "/login/instagram/"

  Scenario: Authenticated user is redirected from login page
    Given I am logged in as "alreadyin@spotter.ai" with password "testpass123"
    When I visit the login page
    Then I should be redirected to "home_dash"

  Scenario: Logged in user can log out
    Given I am logged in as "logout@spotter.ai" with password "testpass123"
    When I log out
    Then I should be redirected to the splash page

  Scenario: After logout, protected pages redirect to login
    Given I am logged in as "logout2@spotter.ai" with password "testpass123"
    When I log out
    And I visit "/home_dash/"
    Then I should be redirected to the login page
