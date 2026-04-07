#!/usr/bin/env python
"""
Playwright test for food search functionality on the nutrition page.
Tests that users can search for foods and auto-populate the form with nutritional data.
"""

import asyncio
import sys
from playwright.async_api import async_playwright
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_ai_app.settings')

from django.conf import settings
if not settings.configured:
    django.setup()

from django.contrib.auth.models import User
from core.models import Meal, FoodItem

BASE_URL = "http://localhost:3000"
TEST_EMAIL = "foodsearch@spotter.ai"
TEST_PASSWORD = "testpass123"


def setup_test_user():
    """Setup test user and clean database"""
    user, created = User.objects.get_or_create(
        username=TEST_EMAIL,
        defaults={'email': TEST_EMAIL, 'first_name': 'Test', 'last_name': 'User'}
    )
    if created or not user.check_password(TEST_PASSWORD):
        user.set_password(TEST_PASSWORD)
        user.is_active = True
        user.save()
    
    # Clear existing meals for today for this user
    today = date.today()
    Meal.objects.filter(user=user, date=today).delete()
    
    return user


async def test_food_search():
    """Test food search functionality"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("\n" + "="*70)
        print("🔍 FOOD SEARCH INTEGRATION TEST")
        print("="*70)
        
        try:
            # Step 1: Login
            print("\n1️⃣  LOGGING IN...")
            await page.goto(f"{BASE_URL}/user_login/")
            await page.wait_for_load_state("networkidle")
            
            await page.fill('input[name="email"]', TEST_EMAIL)
            await page.fill('input[name="password"]', TEST_PASSWORD)
            await page.click('button[type="submit"]')
            
            await page.wait_for_url(f"{BASE_URL}/home_dash/", timeout=10000)
            print("✅ Login successful")
            
            # Step 2: Navigate to nutrition page
            print("\n2️⃣  NAVIGATING TO NUTRITION PAGE...")
            await page.goto(f"{BASE_URL}/nutrition/")
            await page.wait_for_load_state("networkidle")
            print("✅ Nutrition page loaded")
            
            # Step 3: Create a meal
            print("\n3️⃣  CREATING A MEAL...")
            add_meal_btn = page.locator('.add-meal-btn')
            await add_meal_btn.click()
            await page.wait_for_timeout(500)
            
            meal_input = page.locator('input[name="meal_name"]')
            await meal_input.fill("Breakfast")
            
            submit_btn = page.locator('form[action*="add_meal"] button[type="submit"]')
            await submit_btn.click()
            await page.wait_for_load_state("networkidle")
            print("✅ Meal 'Breakfast' created")
            
            # Step 4: Open food form
            print("\n4️⃣  OPENING FOOD FORM...")
            meal_card = page.locator('.meal-card').first
            edit_btn = meal_card.locator('.meal-edit-btn')
            await edit_btn.click()
            await page.wait_for_timeout(300)
            print("✅ Food form opened")
            
            # Step 5: Test search functionality - search for "chicken"
            print("\n5️⃣  TESTING FOOD SEARCH (searching for 'chicken')...")
            food_search = meal_card.locator('.food-search-input')
            await food_search.fill("chicken")
            
            # Wait for search results
            await page.wait_for_timeout(500)
            results_div = meal_card.locator('.food-search-results')
            
            # Check if results appeared
            is_visible = await results_div.is_visible()
            if not is_visible:
                await page.wait_for_timeout(500)
                is_visible = await results_div.is_visible()
            
            assert is_visible, "Search results should be visible"
            print("✅ Search results appeared")
            
            # Step 6: Check results contain chicken
            print("\n6️⃣  VERIFYING SEARCH RESULTS...")
            results_html = await results_div.inner_html()
            assert "chicken" in results_html.lower(), f"Results should contain 'chicken': {results_html[:200]}"
            print("✅ Search results contain 'chicken'")
            
            # Step 7: Click on a search result
            print("\n7️⃣  SELECTING SEARCH RESULT...")
            first_result = results_div.locator('.food-search-item').first
            
            # Get the data from the first result
            expected_name = await first_result.get_attribute('data-name')
            expected_calories = await first_result.get_attribute('data-calories')
            expected_protein = await first_result.get_attribute('data-protein')
            expected_carbs = await first_result.get_attribute('data-carbs')
            expected_fats = await first_result.get_attribute('data-fats')
            
            print(f"   Selected: {expected_name}")
            print(f"   Expected: {expected_calories} cal, {expected_protein}g P, {expected_carbs}g C, {expected_fats}g F")
            
            await first_result.click()
            await page.wait_for_timeout(300)
            print("✅ Result selected")
            
            # Step 8: Verify form fields are auto-populated
            print("\n8️⃣  VERIFYING FORM AUTO-POPULATION...")
            
            actual_name = await meal_card.locator('.food-search-input').input_value()
            actual_calories = await meal_card.locator('.food-calories-input').input_value()
            actual_protein = await meal_card.locator('.food-protein-input').input_value()
            actual_carbs = await meal_card.locator('.food-carbs-input').input_value()
            actual_fats = await meal_card.locator('.food-fats-input').input_value()
            
            print(f"   Name field: {actual_name}")
            print(f"   Calories field: {actual_calories}")
            print(f"   Protein field: {actual_protein}")
            print(f"   Carbs field: {actual_carbs}")
            print(f"   Fats field: {actual_fats}")
            
            assert actual_name == expected_name, f"Name mismatch: {actual_name} != {expected_name}"
            assert actual_calories == expected_calories, f"Calories mismatch: {actual_calories} != {expected_calories}"
            assert actual_protein == expected_protein, f"Protein mismatch: {actual_protein} != {expected_protein}"
            assert actual_carbs == expected_carbs, f"Carbs mismatch: {actual_carbs} != {expected_carbs}"
            assert actual_fats == expected_fats, f"Fats mismatch: {actual_fats} != {expected_fats}"
            print("✅ All form fields correctly auto-populated!")
            
            # Step 9: Submit the form
            print("\n9️⃣  SUBMITTING FOOD ITEM...")
            submit_food = meal_card.locator('form.food-form button[type="submit"]')
            await submit_food.click()
            await page.wait_for_load_state("networkidle")
            print("✅ Food item submitted")
            
            # Step 10: Verify food appears in meal
            print("\n🔟 VERIFYING FOOD ITEM IN MEAL...")
            await page.wait_for_timeout(300)
            page_content = await page.content()
            assert expected_name in page_content, f"Food '{expected_name}' should appear on page"
            print(f"✅ '{expected_name}' appears in meal card")
            
            # Step 11: Toggle to complete and verify macros update
            print("\n1️⃣1️⃣  COMPLETING FOOD ITEM AND CHECKING MACROS...")
            meal_card = page.locator('.meal-card').first
            checkbox = meal_card.locator('.checkbox').first
            await checkbox.click()
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(300)
            
            # Check macro values updated
            protein_grams = await page.text_content('#proteinGrams')
            carbs_grams = await page.text_content('#carbsGrams')
            fats_grams = await page.text_content('#fatGrams')
            calories_display = await page.locator('.calories-consumed').text_content()
            
            print(f"   Calories: {calories_display}")
            print(f"   Protein: {protein_grams}")
            print(f"   Carbs: {carbs_grams}")
            print(f"   Fats: {fats_grams}")
            
            assert expected_protein in protein_grams, f"Protein should be {expected_protein}g"
            print("✅ Macro cards updated correctly!")
            
            # Step 12: Test another search - rice
            print("\n1️⃣2️⃣  TESTING SECOND SEARCH (searching for 'rice')...")
            edit_btn = meal_card.locator('.meal-edit-btn')
            await edit_btn.click()
            await page.wait_for_timeout(300)
            
            food_search = meal_card.locator('.food-search-input')
            await food_search.fill("rice")
            await page.wait_for_timeout(500)
            
            results_div = meal_card.locator('.food-search-results')
            is_visible = await results_div.is_visible()
            assert is_visible, "Search results should be visible for 'rice'"
            
            results_html = await results_div.inner_html()
            assert "rice" in results_html.lower(), "Results should contain 'rice'"
            print("✅ Rice search works!")
            
            # Step 13: Take screenshot
            print("\n1️⃣3️⃣  TAKING SCREENSHOT...")
            await page.screenshot(path="/tmp/food_search_test.png")
            print("✅ Screenshot saved to /tmp/food_search_test.png")
            
            # Final report
            print("\n" + "="*70)
            print("✅ ALL FOOD SEARCH TESTS PASSED!")
            print("="*70)
            print("\n📊 TEST SUMMARY:")
            print("  ✓ Food search API returns results")
            print("  ✓ Search results display in dropdown")
            print("  ✓ Clicking result auto-populates all form fields")
            print("  ✓ Food item saved to database correctly")
            print("  ✓ Macro cards update when food completed")
            print("  ✓ Multiple searches work correctly")
            print("")
            
            return True
            
        except AssertionError as e:
            print(f"\n❌ ASSERTION FAILED: {str(e)}")
            try:
                await page.screenshot(path="/tmp/food_search_test_failed.png")
                print("📸 Screenshot saved to /tmp/food_search_test_failed.png")
            except:
                pass
            return False
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            
            try:
                await page.screenshot(path="/tmp/food_search_test_failed.png")
                print("📸 Screenshot saved to /tmp/food_search_test_failed.png")
            except:
                pass
            
            return False
            
        finally:
            await browser.close()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("📋 SETUP PHASE")
    print("="*70)
    try:
        setup_test_user()
        print("✅ Test user prepared")
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)
    
    success = asyncio.run(test_food_search())
    sys.exit(0 if success else 1)
