Feature: AI Chat
  As a logged-in user
  I want to access the AI chat assistant
  So that I can get personalized fitness guidance

  Background:
    Given I am logged in as "aiuser@spotter.ai" with password "testpass123"

  # --- AI chat page ---

  Scenario: AI chat page loads for authenticated user
    When I visit "/ai/"
    Then the response status code should be 200

  Scenario: AI chat page requires authentication
    Given I am not logged in
    When I visit "/ai/"
    Then I should be redirected to the login page

  # --- Chat history API ---

  Scenario: Chat history API requires authentication
    Given I am not logged in
    When I visit "/api/chat/history/"
    Then I should be redirected to the login page

  Scenario: Chat history API returns JSON for authenticated user
    When I visit "/api/chat/history/"
    Then the response status code should be 200
    And the response is valid JSON
    And the JSON has key "conversations"

  Scenario: New user has empty chat history
    When I visit "/api/chat/history/"
    Then the JSON "conversations" list is empty

  Scenario: Chat history includes created conversations
    Given an AI chat conversation "My Workout Plan" exists for this user
    When I visit "/api/chat/history/"
    Then the response status code should be 200
    And the JSON "conversations" list is not empty

  # --- Chat history detail API ---

  Scenario: Chat history detail returns conversation and messages
    Given an AI chat conversation "Nutrition Advice" exists for this user
    When I visit the chat history detail for that conversation
    Then the response status code should be 200
    And the response is valid JSON
    And the JSON has key "conversation"
    And the JSON has key "messages"

  Scenario: Chat history detail for another user's conversation returns 404
    Given another AI user has a conversation
    When I visit the chat history detail for the other user's conversation
    Then the response status code should be 404
