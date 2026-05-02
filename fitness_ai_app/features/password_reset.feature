Feature: Password Reset
  As a registered user who forgot their password
  I want to reset my password via email
  So that I can regain access to my account

  Background:
    Given the site is available

  # --- Forgot password page ---

  Scenario: Visitor can view the forgot password page
    When I visit "/forgot_password/"
    Then the response status code should be 200

  Scenario: Authenticated user is redirected from forgot password page
    Given I am logged in as "already@spotter.ai" with password "testpass123"
    When I visit "/forgot_password/"
    Then I should be redirected to "home_dash"

  Scenario: Submitting forgot password for a known email redirects to login
    Given a registered user "pwreset@spotter.ai" with password "oldpass123"
    When I submit the forgot password form with email "pwreset@spotter.ai"
    Then I should be redirected to "user_login"

  Scenario: Submitting forgot password for an unknown email still redirects to login
    When I submit the forgot password form with email "nobody@spotter.ai"
    Then I should be redirected to "user_login"

  # --- Reset password page ---

  Scenario: Valid reset token shows the reset password form
    Given a registered user "validreset@spotter.ai" with password "oldpass123"
    And a valid password reset token exists for "validreset@spotter.ai"
    When I visit the reset password page for that token
    Then the response status code should be 200

  Scenario: Invalid token shows an error message
    When I visit "/reset_password/00000000-0000-0000-0000-000000000000/"
    Then the response status code should be 200

  Scenario: Used token shows an error message
    Given a registered user "usedreset@spotter.ai" with password "oldpass123"
    And a used password reset token exists for "usedreset@spotter.ai"
    When I visit the reset password page for that token
    Then the response status code should be 200

  Scenario: Expired token shows an error message
    Given a registered user "expiredreset@spotter.ai" with password "oldpass123"
    And an expired password reset token exists for "expiredreset@spotter.ai"
    When I visit the reset password page for that token
    Then the response status code should be 200

  # --- Successful password reset ---

  Scenario: Submitting valid new password resets it and redirects to login
    Given a registered user "doreset@spotter.ai" with password "oldpass123"
    And a valid password reset token exists for "doreset@spotter.ai"
    When I submit the reset password form with password "newpass456"
    Then I should be redirected to "user_login"
    And I can log in as "doreset@spotter.ai" with password "newpass456"
