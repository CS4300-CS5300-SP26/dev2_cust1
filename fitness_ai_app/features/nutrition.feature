Feature: Nutrition Tracking
  As a user I want to track meals and food items
  so that I can monitor my daily calorie intake.

  Background:
    Given I am logged in as "nutrition@spotter.ai" with password "testpass123"

  # --- Page access ---

  Scenario: Nutrition page loads for authenticated user
    When I visit "/nutrition/"
    Then the response status code should be 200
    And I should see "Nutrition"

  Scenario: Nutrition page requires authentication
    Given I am not logged in
    When I visit "/nutrition/"
    Then I should be redirected to the login page

  # --- Date navigation ---

  Scenario: Default date is today
    When I visit "/nutrition/"
    Then the response status code should be 200

  Scenario: Navigate to a specific date
    When I visit "/nutrition/?date=2025-06-15"
    Then the response status code should be 200

  Scenario: Invalid date falls back to today
    When I visit "/nutrition/?date=not-a-date"
    Then the response status code should be 200

  # --- Meal management ---

  Scenario: Add a meal
    When I add a meal named "Breakfast" for date "2025-06-15"
    Then a meal named "Breakfast" should exist for date "2025-06-15"

  Scenario: Add a meal with missing name is rejected
    When I try to add a meal with no name for date "2025-06-15"
    Then no meals should exist

  Scenario: Add a meal with invalid date is rejected
    When I try to add a meal with name "Lunch" for date "bad-date"
    Then no meals should exist

  # --- Food item management ---

  Scenario: Add a food item to a meal
    Given a meal named "Breakfast" exists for today
    When I add a food item "Eggs" with 200 calories to that meal
    Then a food item named "Eggs" with 200 calories should exist

  Scenario: Add a food item with invalid calories is rejected
    Given a meal named "Breakfast" exists for today
    When I try to add a food item "Eggs" with "abc" calories to that meal
    Then no food items should exist

  Scenario: Toggle a food item completed
    Given a meal named "Breakfast" exists for today
    And a food item "Eggs" with 200 calories exists in that meal
    When I toggle the food item
    Then the food item should be marked as completed

  Scenario: Toggle a food item back to incomplete
    Given a meal named "Breakfast" exists for today
    And a completed food item "Eggs" with 200 calories exists in that meal
    When I toggle the food item
    Then the food item should be marked as incomplete

  Scenario: Delete a food item
    Given a meal named "Breakfast" exists for today
    And a food item "Eggs" with 200 calories exists in that meal
    When I delete the food item
    Then the food item should no longer exist

  # --- Calorie tracking ---

  Scenario: Total calories count only completed items
    Given a meal named "Breakfast" exists for today
    And a completed food item "Eggs" with 200 calories exists in that meal
    And a food item "Toast" with 150 calories exists in that meal
    When I visit "/nutrition/"
    Then the total calories should be 200

  # --- Authorization ---

  Scenario: Cannot access another user's meal items
    Given another user has a meal named "Secret Meal"
    When I try to add a food item to the other user's meal
    Then the response status code should be 404
