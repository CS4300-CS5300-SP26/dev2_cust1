Feature: Achievements and Challenges
  As a user I want to earn achievements and complete weekly challenges
  so that I can track milestones and stay motivated.

  Background:
    Given I am logged in as "achuser@spotter.ai" with password "testpass123"

  # --- Social page access ---

  Scenario: Social page loads for authenticated user
    When I visit "/social/"
    Then the response status code should be 200
    And I should see "Achievements"
    And I should see "Weekly Challenges"

  Scenario: Social page requires authentication
    Given I am not logged in
    When I visit "/social/"
    Then I should be redirected to the login page

  # --- Achievement progress API ---

  Scenario: Achievements progress API requires authentication
    Given I am not logged in
    When I visit "/api/achievements/progress/"
    Then I should be redirected to the login page

  Scenario: Achievements progress API returns JSON for authenticated user
    When I visit "/api/achievements/progress/"
    Then the response status code should be 200
    And the response is valid JSON
    And the JSON has key "earned_ids"
    And the JSON has key "achievements"
    And the JSON has key "challenges"
    And the JSON has key "stats"

  Scenario: New user starts with no earned achievements
    When I visit "/api/achievements/progress/"
    Then the response status code should be 200
    And the JSON "earned_ids" list is empty

  # --- Achievement: First Rep ---

  Scenario: Earn First Rep by completing an exercise
    Given a completed workout exists for today with a completed exercise
    When I visit "/api/achievements/progress/"
    Then "first_rep" is in the earned achievement IDs

  Scenario: First Rep not earned without completed exercises
    Given a completed workout exists for today with no exercises
    When I visit "/api/achievements/progress/"
    Then "first_rep" is not in the earned achievement IDs

  # --- Achievement: Nutrition Nerd ---

  Scenario: Earn Nutrition Nerd by logging meals on 7 different days
    Given I have logged meals on 7 different days
    When I visit "/api/achievements/progress/"
    Then "nutrition_nerd" is in the earned achievement IDs

  Scenario: Nutrition Nerd not earned with only 6 meal days
    Given I have logged meals on 6 different days
    When I visit "/api/achievements/progress/"
    Then "nutrition_nerd" is not in the earned achievement IDs

  # --- Weekly challenge: Workout 3x ---

  Scenario: Workout 3x challenge increments on completed workout
    Given I have completed 2 workouts this week
    When I visit "/api/achievements/progress/"
    Then the challenge "workout_3x" has progress 2

  Scenario: Workout 3x challenge completes after 3 workouts this week
    Given I have completed 3 workouts this week
    When I visit "/api/achievements/progress/"
    Then the challenge "workout_3x" is completed

  Scenario: Workout from last week does not count for this week's challenge
    Given I completed a workout 8 days ago
    When I visit "/api/achievements/progress/"
    Then the challenge "workout_3x" has progress 0

  # --- Weekly challenge: Fuel Your Gains ---

  Scenario: Fuel Your Gains requires both workout and meal on the same day
    Given I completed a workout today
    And I have not logged any meals today
    When I visit "/api/achievements/progress/"
    Then the challenge "fuel_gains" has progress 0

  Scenario: Fuel Your Gains counts when workout and meal are on the same day
    Given I completed a workout today
    And I have logged a meal today
    When I visit "/api/achievements/progress/"
    Then the challenge "fuel_gains" has progress 1

  Scenario: Fuel Your Gains does not count meal without workout
    Given I have not completed any workouts this week
    And I have logged a meal today
    When I visit "/api/achievements/progress/"
    Then the challenge "fuel_gains" has progress 0

  # --- complete_workout API includes achievement progress ---

  Scenario: Completing a workout via API returns achievement progress
    Given a planned workout exists for today
    When I complete that workout via the API
    Then the response status code should be 200
    And the response is valid JSON
    And the JSON has key "achievement_progress"
    And the achievement progress has "earned_ids"
    And the achievement progress has "challenges"
    And the achievement progress has "stats"

  Scenario: Workout 3x progress appears in complete_workout response
    Given a planned workout exists for today
    When I complete that workout via the API
    Then the workout_3x challenge progress is at least 1 in the response

  # --- User data isolation ---

  Scenario: Achievements are isolated per user
    Given another user has completed 50 exercises
    When I visit "/api/achievements/progress/"
    Then "iron_will" is not in the earned achievement IDs
    And the JSON stats "total_exercises" is 0
