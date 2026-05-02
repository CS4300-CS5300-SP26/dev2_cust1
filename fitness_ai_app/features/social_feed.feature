Feature: Social River Feed
  As a logged-in user
  I want to interact with the social activity feed
  So that I can see and respond to community fitness events

  Background:
    Given I am logged in as "riveruser@spotter.ai" with password "testpass123"

  # --- River feed API ---

  Scenario: River feed API requires authentication
    Given I am not logged in
    When I visit "/api/river/feed/"
    Then I should be redirected to the login page

  Scenario: River feed API returns JSON for authenticated user
    When I visit "/api/river/feed/"
    Then the response status code should be 200
    And the response is valid JSON
    And the JSON has key "events"

  Scenario: River feed includes a recently created event
    Given a river event titled "Completed a workout" exists
    When I visit "/api/river/feed/"
    Then the response status code should be 200
    And the response is valid JSON

  Scenario: River feed events have required fields
    Given a river event titled "Test event" exists
    When I visit "/api/river/feed/"
    Then the first river event has field "id"
    And the first river event has field "title"
    And the first river event has field "event_type"
    And the first river event has field "spark_count"
    And the first river event has field "comments"

  # --- River comment API ---

  Scenario: Posting a comment on a river event returns 201
    Given a river event titled "Leg Day complete" exists
    When I post a comment "Great job!" on that river event
    Then the response status code should be 201
    And the response is valid JSON
    And the JSON has key "text"

  Scenario: River comment requires authentication
    Given I am not logged in
    And a river event titled "No Auth Event" exists
    When I post a comment "Nope" on that river event
    Then I should be redirected to the login page

  Scenario: River comment with empty text is rejected
    Given a river event titled "Empty Comment Event" exists
    When I post an empty comment on that river event
    Then the response status code should be 400

  Scenario: River comment longer than 300 chars is rejected
    Given a river event titled "Long Comment Event" exists
    When I post a comment that is 301 characters long on that river event
    Then the response status code should be 400

  Scenario: River comment on non-existent event returns 404
    When I post a comment "Hello" on river event id 999999
    Then the response status code should be 404

  # --- River spark API ---

  Scenario: Sparking a river event adds the spark
    Given a river event titled "Spark Test" exists
    When I spark that river event
    Then the response status code should be 200
    And the response is valid JSON
    And the JSON has key "sparked"
    And the JSON has key "spark_count"

  Scenario: Sparking the same event twice removes the spark
    Given a river event titled "Double Spark" exists
    When I spark that river event
    And I spark that river event again
    Then the sparked field is false

  Scenario: River spark requires authentication
    Given I am not logged in
    And a river event titled "No Auth Spark" exists
    When I spark that river event
    Then I should be redirected to the login page

  Scenario: Sparking non-existent event returns 404
    When I spark river event id 999999
    Then the response status code should be 404
