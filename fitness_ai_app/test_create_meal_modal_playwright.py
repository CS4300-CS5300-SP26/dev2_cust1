#!/usr/bin/env python
"""Playwright test for the 🍴 Meal group flow in the Add-to-Meal modal.

Exercises:
  - Opening the modal from a meal card's "+" button
  - Selecting the 🍴 "Meal" option
  - Naming the group and clicking Continue
  - Continuously adding food items (one custom, one from DB search)
  - Clicking "Done" and asserting items appear inside a named sub-group section
    on reload

Requires the dev server on http://localhost:3000 and a test user
testuser@spotter.ai / testpass123 with at least one existing meal (the script
will seed one if none exist).
"""

import asyncio
import sys
from datetime import date

from playwright.async_api import async_playwright

BASE_URL = "http://localhost:3000"
TEST_EMAIL = "testuser@spotter.ai"
TEST_PASSWORD = "testpass123"
GROUP_NAME = "PW Test Group"


async def login(page):
    await page.goto(f"{BASE_URL}/user_login/")
    await page.fill('input[name="email"]', TEST_EMAIL)
    await page.fill('input[name="password"]', TEST_PASSWORD)
    await page.click('button[type="submit"]')
    await page.wait_for_url(f"{BASE_URL}/home_dash/")


async def ensure_existing_meal(page, today):
    meal_cards = await page.query_selector_all(".meal-card")
    if meal_cards:
        return
    print("No existing meal; creating one via add_meal form")
    await page.evaluate(
        """(today) => {
            const f = document.querySelector('form[action="/nutrition/add_meal/"]');
            f.querySelector('input[name=meal_name]').value = 'Seed Meal';
            f.querySelector('input[name=date]').value = today;
            f.submit();
        }""",
        today,
    )
    await page.wait_for_load_state("networkidle")


async def first_meal_name(page):
    return await page.evaluate(
        "() => { const n = document.querySelector('.meal-card .meal-name'); return n ? n.textContent.trim() : null; }"
    )


async def run():
    today = date.today().strftime("%Y-%m-%d")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        print("1. Logging in...")
        await login(page)

        print("2. Opening nutrition page...")
        await page.goto(f"{BASE_URL}/nutrition/?date={today}")
        await page.wait_for_load_state("networkidle")

        await ensure_existing_meal(page, today)

        target_meal = await first_meal_name(page)
        assert target_meal, "No meal card to target"
        print(f"   Targeting meal: {target_meal}")

        print("3. Opening Add-to-Meal modal...")
        await page.click(".meal-card .meal-edit-btn")
        await page.wait_for_selector("#addItemModal", state="visible")

        print("4. Verifying three choices...")
        choices = await page.query_selector_all("#itemTypeChoices > button")
        assert len(choices) == 3, f"Expected 3 choices, got {len(choices)}"
        meal_btn = await page.query_selector("#chooseMealBtn")
        assert meal_btn is not None, "Meal choice button missing"

        print("5. Selecting Meal option...")
        await meal_btn.click()
        await page.wait_for_selector("#mealGroupNameStep", state="visible")

        print("6. Entering group name and continuing...")
        await page.fill("#mealGroupNameInput", GROUP_NAME)
        await page.click("#mealGroupContinueBtn")
        await page.wait_for_selector("#mealItemsStep", state="visible")
        header = await page.text_content("#mealItemsHeader")
        assert GROUP_NAME in header, f"Header missing group name: {header!r}"

        print("7. Adding a custom food item...")
        await page.fill("#mealFoodNameInput", "Playwright Custom Food")
        await page.fill("#mealFoodCaloriesInput", "321")
        await page.fill("#mealFoodProteinInput", "10")
        await page.click("#mealAddItemBtn")
        await page.wait_for_function(
            "document.querySelectorAll('#mealItemsList .meal-flow-added-item').length === 1"
        )

        print("8. Adding a second item via DB search...")
        await page.fill("#mealFoodNameInput", "ap")
        await page.wait_for_selector("#mealFoodSearchResults .meal-search-result", timeout=3000)
        await page.click("#mealFoodSearchResults .meal-search-result")
        cal_val = await page.input_value("#mealFoodCaloriesInput")
        assert cal_val and cal_val != "", "Calories should be auto-populated from DB search"
        await page.click("#mealAddItemBtn")
        await page.wait_for_function(
            "document.querySelectorAll('#mealItemsList .meal-flow-added-item').length === 2"
        )

        print("9. Clicking Done...")
        await page.click("#mealDoneBtn")
        await page.wait_for_load_state("networkidle")

        print("10. Asserting group sub-section visible on the meal card...")
        body = await page.text_content("body")
        assert "Playwright Custom Food" in body, "Custom item missing after reload"
        assert GROUP_NAME in body, f"Group name '{GROUP_NAME}' missing after reload"

        group_section = await page.query_selector(".food-group-section")
        assert group_section is not None, "No .food-group-section found on the page"

        group_items = await page.query_selector_all(".food-group-section .food-item")
        assert len(group_items) == 2, f"Expected 2 items in group section, got {len(group_items)}"

        print("\nPASS: Food-group batch-add flow passed end-to-end.")
        await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except AssertionError as e:
        print(f"\nFAIL: Assertion failed: {e}")
        sys.exit(1)
