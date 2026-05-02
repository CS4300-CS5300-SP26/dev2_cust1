Feature: Supplements Tracking
  As a logged-in user
  I want to track supplements in my meals and standalone entries
  So that I can monitor my supplement intake

  Background:
    Given I am logged in as "suppuser@spotter.ai" with password "testpass123"

  # --- Meal supplements ---

  Scenario: Add a supplement to a meal
    Given a supp meal named "Breakfast" exists for today
    When I add a supplement "Creatine" to that meal
    Then the supplement "Creatine" should exist in the meal

  Scenario: Add supplement with missing name is rejected
    Given a supp meal named "Lunch" exists for today
    When I try to add a supplement with no name to that meal
    Then no meal supplement should exist in the meal

  Scenario: Toggle a meal supplement as taken
    Given a supp meal named "Dinner" exists for today
    And a supplement "Whey Protein" exists in that meal and is not taken
    When I toggle that meal supplement
    Then the supplement should be marked as taken

  Scenario: Toggle a taken supplement back to not taken
    Given a supp meal named "Supper" exists for today
    And a taken supplement "Fish Oil" exists in that meal
    When I toggle that meal supplement
    Then the supplement should be marked as not taken

  Scenario: Delete a meal supplement
    Given a supp meal named "Snack" exists for today
    And a supplement "Vitamin C" exists in that meal and is not taken
    When I delete that meal supplement
    Then no supplement named "Vitamin C" should exist in the meal

  # --- Standalone supplement entries API ---

  Scenario: Get supplement entries for today returns JSON
    When I GET "/api/supplement_entries/?date=2025-06-15"
    Then the response status code should be 200
    And the response is valid JSON
    And the JSON has key "entries"

  Scenario: Supplement entries GET requires authentication
    Given I am not logged in
    When I GET "/api/supplement_entries/"
    Then I should be redirected to the login page

  Scenario: Create a standalone supplement entry via POST
    When I POST a supplement entry with name "Magnesium" for today
    Then the response status code should be 200
    And the response is valid JSON
    And the JSON has key "success"

  Scenario: Create supplement entry with no name is rejected
    When I POST a supplement entry with no name
    Then the response status code should be 400

  # --- Toggle supplement taken PATCH API ---

  Scenario: Toggle supplement taken status via PATCH
    Given a standalone supplement entry "ZMA" exists for today
    When I toggle that supplement entry taken status
    Then the response status code should be 200
    And the JSON has key "taken"

  Scenario: Toggle supplement taken for another user's entry returns 404
    Given another supp user has a supplement entry
    When I try to toggle the other user's supplement entry
    Then the response status code should be 404
