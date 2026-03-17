Feature: App Navigation
  As a logged-in user
  I want to navigate between all sections of the app
  So that I can access all fitness features

  Background:
    Given I am logged in as "navuser@spotter.ai" with password "testpass123"

  Scenario Outline: Protected pages require authentication
    Given I am not logged in
    When I visit "<url>"
    Then I should be redirected to the login page

    Examples:
      | url         |
      | /home_dash/ |
      | /train/     |
      | /nutrition/ |
      | /ai/        |
      | /social/    |

  Scenario Outline: Authenticated user can access all pages
    When I visit "<url>"
    Then the response status should be 200

    Examples:
      | url         |
      | /home_dash/ |
      | /train/     |
      | /nutrition/ |
      | /ai/        |
      | /social/    |

  Scenario Outline: Bottom navigation bar is present on all pages
    When I visit "<url>"
    Then I should see "bottom-nav"
    And I should see "Home"
    And I should see "Train"
    And I should see "Nutrition"
    And I should see "AI"
    And I should see "Social"

    Examples:
      | url         |
      | /home_dash/ |
      | /train/     |
      | /nutrition/ |
      | /social/    |

  Scenario Outline: Profile bubble and logout link are on all pages
    When I visit "<url>"
    Then I should see "profile-btn"
    And I should see "profile-dropdown"
    And I should see "Log Out"

    Examples:
      | url         |
      | /home_dash/ |
      | /train/     |
      | /nutrition/ |
      | /social/    |

  Scenario Outline: Logo is present on all pages
    When I visit "<url>"
    Then I should see "logo-container"

    Examples:
      | url         |
      | /home_dash/ |
      | /train/     |
      | /nutrition/ |
      | /social/    |
