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

  Scenario: Today button context always reflects current date
    When I visit "/nutrition/?date=2025-06-15"
    Then the today_string context should match today's date

  # --- Meal management ---

  Scenario: Add a meal
    When I add a meal named "Breakfast" for date "2025-06-15"
    Then a meal named "Breakfast" should exist for date "2025-06-15"

  Scenario: Add a meal with missing name auto-generates one
    When I try to add a meal with no name for date "2025-06-15"
    Then a meal with an auto-generated name should exist for date "2025-06-15"

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

  Scenario: Edit a food item saves recalculated calories without persisting serving size
    Given a meal named "Breakfast" exists for today
    And a food item "Chicken" with 200 calories exists in that meal
    When I edit the food item with 2 servings and 400 calories
    Then the food item should have 400 calories

  Scenario: Adding a food item persists the chosen serving size
    Given a meal named "Breakfast" exists for today
    When I add a food item "Oatmeal" with 300 calories and 2 servings of "cup" to that meal
    Then the food item should have serving size 2 and unit "cup"

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

  # --- Saved items ---

  Scenario: Save a food item
    Given a meal named "Breakfast" exists for today
    And a food item "Eggs" with 200 calories exists in that meal
    When I save the food item via API
    Then the food item should be in my saved foods

  Scenario: Saving duplicate food item returns already_saved flag
    Given a meal named "Breakfast" exists for today
    And a food item "Eggs" with 200 calories exists in that meal
    And the food item is already saved
    When I save the food item via API
    Then the response should indicate already saved

  Scenario: Save food item with out-of-range calories is rejected
    When I try to save a food item with calories 10000
    Then the response status code should be 400

  Scenario: Save food item requires POST
    When I GET the save food item endpoint
    Then the response status code should be 405

  Scenario: Save a meal as template
    Given a meal named "Lunch" exists for today
    And a food item "Rice" with 300 calories exists in that meal
    When I save the meal as a template
    Then the meal template should be in my saved meals

  Scenario: Add a saved food to a meal via ajax endpoint
    Given a meal named "Breakfast" exists for today
    And I have a saved food item "Banana"
    When I add the saved food to that meal via ajax
    Then a food item named "Banana" with 100 calories should exist

  Scenario: Delete a saved food item
    Given I have a saved food item "Banana"
    When I delete the saved food item
    Then the saved food item should no longer exist

  Scenario: Add saved meal to a date
    Given I have a saved meal template "Dinner Plan" with 2 food items
    When I add the saved meal to today
    Then a meal named "Dinner Plan" should exist for today

  Scenario: Adding a saved meal with more than 30 items is rejected
    Given I have a saved meal template "Huge Meal" with 31 food items
    When I add the saved meal to today
    Then the response status code should be 400

  # --- System food database visibility ---

  Scenario: System food database foods appear in search results
    Given the system food database contains "Grilled Chicken Breast (100g)"
    When I search foods for "Grilled Chicken"
    Then the search results should include "Grilled Chicken Breast (100g)"

  Scenario: System food database foods appear in get_all_foods
    Given the system food database contains "Brown Rice Cooked (1 cup)"
    When I fetch all foods
    Then the all-foods response should include "Brown Rice Cooked (1 cup)"
