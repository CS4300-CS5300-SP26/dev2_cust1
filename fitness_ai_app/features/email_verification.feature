Feature: Email Verification
  As a newly registered user
  I want to verify my email address
  So that I can activate my account

  Background:
    Given the site is available

  Scenario: Valid verification token activates user account
    Given an unverified user "evbdd@spotter.ai" with a valid verification token
    When I visit the verification link for "evbdd@spotter.ai"
    Then I should be redirected to "home_dash"
    And the user "evbdd@spotter.ai" should be active

  Scenario: Already verified token redirects to login
    Given a user "evbdd2@spotter.ai" whose token is already verified
    When I visit the verification link for "evbdd2@spotter.ai"
    Then I should be redirected to "user_login"

  Scenario: Expired token deletes the user account
    Given an unverified user "evbdd3@spotter.ai" with an expired verification token
    When I visit the verification link for "evbdd3@spotter.ai"
    Then I should be redirected to "user_get_started"
    And the user "evbdd3@spotter.ai" should not exist

  Scenario: Invalid token redirects to login
    When I visit an invalid verification link
    Then I should be redirected to "user_login"
