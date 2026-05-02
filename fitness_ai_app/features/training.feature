Feature: Training / Workout Tracking
  As a logged-in user
  I want to manage workouts and exercises
  So that I can track my training progress

  Background:
    Given I am logged in as "trainuser@spotter.ai" with password "testpass123"

  # --- Page access ---

  Scenario: Training page loads for authenticated user
    When I visit "/train/"
    Then the response status code should be 200
    And I should see "Train"

  Scenario: Training page requires authentication
    Given I am not logged in
    When I visit "/train/"
    Then I should be redirected to the login page

  # --- Date navigation ---

  Scenario: Training page loads for a specific date
    When I visit "/train/?date=2025-06-15"
    Then the response status code should be 200

  Scenario: Training page falls back to today on invalid date
    When I visit "/train/?date=not-a-date"
    Then the response status code should be 200

  # --- Workout management ---

  Scenario: Add a planned workout
    When I add a workout named "Morning Run" with goal "strength" and status "planned" for today
    Then a workout named "Morning Run" should exist for today

  Scenario: Add a workout missing name is rejected
    When I try to add a workout with no name for today
    Then no new workout should exist

  Scenario: Delete a workout
    Given a workout named "Leg Day" exists for today
    When I delete that workout
    Then no workout named "Leg Day" should exist

  # --- Exercise management ---

  Scenario: Add an exercise to a workout
    Given a workout named "Push Day" exists for today
    When I add an exercise "Push-up" in muscle group "chest" to that workout
    Then an exercise named "Push-up" should exist in the workout

  Scenario: Add exercise missing name is rejected
    Given a workout named "Push Day" exists for today
    When I try to add an exercise with no name to that workout
    Then no exercise should exist in the workout

  Scenario: Toggle an exercise to completed
    Given a workout named "Pull Day" exists for today
    And an exercise "Pull-up" in muscle group "back" exists in that workout
    When I toggle that exercise
    Then the exercise should be marked as completed

  Scenario: Toggle a completed exercise back to incomplete
    Given a workout named "Pull Day" exists for today
    And a completed exercise "Pull-up" in muscle group "back" exists in that workout
    When I toggle that exercise
    Then the exercise should be marked as incomplete

  Scenario: Delete an exercise
    Given a workout named "Core Day" exists for today
    And an exercise "Plank" in muscle group "core" exists in that workout
    When I delete that exercise
    Then the exercise should no longer exist

  Scenario: Edit an exercise
    Given a workout named "Arm Day" exists for today
    And an exercise "Curl" in muscle group "arms" exists in that workout
    When I edit that exercise to name "Bicep Curl" in muscle group "arms"
    Then an exercise named "Bicep Curl" should exist in the workout

  # --- complete_workout JSON API ---

  Scenario: Complete a workout via API
    Given a planned workout named "API Workout" exists for today
    When I complete that workout via the complete_workout API
    Then the response status code should be 200
    And the response is valid JSON
    And the JSON has key "success"
    And the JSON has key "achievement_progress"

  Scenario: Complete workout API returns error for missing workout_id
    When I POST to "/api/workout/complete/" with JSON "{}"
    Then the response status code should be 400

  Scenario: Complete workout API returns 404 for another user's workout
    Given another training user has a workout
    When I try to complete the other user's workout via the API
    Then the response status code should be 404

  # --- save_workout_time API ---

  Scenario: Save workout time via API
    Given a planned workout named "Timed Workout" exists for today
    When I save workout time of 600 seconds via the API
    Then the response status code should be 200
    And the JSON has key "total_seconds"

  Scenario: Save workout time with missing fields returns error
    When I POST to "/api/workout/save_time/" with JSON "{}"
    Then the response status code should be 400

  # --- complete_exercises_by_ids API ---

  Scenario: Complete multiple exercises by IDs via API
    Given a planned workout named "Batch Day" exists for today
    And an exercise "Squat" in muscle group "legs" exists in that workout
    When I complete all exercises in that workout via the API
    Then the response status code should be 200
    And the JSON has key "completed_count"

  # --- set_progress APIs ---

  Scenario: Save set progress via API
    Given a planned workout named "Set Day" exists for today
    And an exercise "Bench Press" in muscle group "chest" exists in that workout
    When I save set progress for that exercise
    Then the response status code should be 200
    And the JSON has key "saved_count"

  Scenario: Get set progress for a workout
    Given a planned workout named "Get Set Day" exists for today
    When I get set progress for that workout
    Then the response status code should be 200
    And the JSON has key "set_progress"

  Scenario: Get set progress requires workout_id
    When I GET "/api/set_progress/get/" without workout_id
    Then the response status code should be 400

  # --- Authorization ---

  Scenario: Cannot delete another user's workout
    Given another training user has a workout
    When I try to delete the other user's workout
    Then the other user's workout should still exist
