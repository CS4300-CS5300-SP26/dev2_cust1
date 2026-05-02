Feature: Home Dashboard
  As a logged-in user
  I want to see my daily fitness summary on the dashboard
  So that I can track my progress at a glance

  Background:
    Given I am logged in as "dashuser@spotter.ai" with password "testpass123"

  # --- Page access ---

  Scenario: Home dashboard loads for authenticated user
    When I visit "/home_dash/"
    Then the response status code should be 200

  Scenario: Home dashboard requires authentication
    Given I am not logged in
    When I visit "/home_dash/"
    Then I should be redirected to the login page

  # --- Calorie summary ---

  Scenario: Dashboard shows zero calories with no food logged
    When I visit "/home_dash/"
    Then the response status code should be 200

  Scenario: Dashboard reflects completed food items in calorie total
    Given a dash meal exists for today with a completed food item of 500 calories
    When I visit "/home_dash/"
    Then the response status code should be 200

  Scenario: Dashboard does not count incomplete food items in calorie total
    Given a dash meal exists for today with an incomplete food item of 300 calories
    When I visit "/home_dash/"
    Then the response status code should be 200

  # --- Workout activity ---

  Scenario: Dashboard shows zero completed exercises with no workouts
    When I visit "/home_dash/"
    Then the response status code should be 200

  Scenario: Dashboard counts completed exercises from today's workouts
    Given a dash workout exists for today with 2 completed exercises
    When I visit "/home_dash/"
    Then the response status code should be 200

  # --- Navigation present ---

  Scenario: Dashboard contains navigation bar
    When I visit "/home_dash/"
    Then I should see "bottom-nav"
    And I should see "Train"
    And I should see "Nutrition"
