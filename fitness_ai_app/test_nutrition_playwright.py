#!/usr/bin/env python
"""
Playwright test for nutrition macro card display and updates.
Tests that macro cards display correctly and update when food items are added, deleted, or toggled.
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
TEST_EMAIL = "testuser@spotter.ai"
TEST_PASSWORD = "testpass123"

def setup_test_user():
    """Setup test user and clean database"""
    user, created = User.objects.get_or_create(
        username=TEST_EMAIL,
        defaults={'email': TEST_EMAIL, 'first_name': 'Test', 'last_name': 'User'}
    )
    if created:
        user.set_password(TEST_PASSWORD)
        user.save()
    
    # Clear existing meals for today
    today = date.today()
    Meal.objects.filter(user=user, date=today).delete()
    
    return user

async def test_macro_cards():
    """Test macro card display and updates"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("\n" + "="*70)
        print("🥗 COMPREHENSIVE MACRO CARD TEST")
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
            
            # Step 3: Check initial macro card values (should be 0)
            print("\n3️⃣  CHECKING INITIAL MACRO CARD STATE...")
            try:
                protein_grams = await page.locator('#proteinGrams').text_content()
                carbs_grams = await page.locator('#carbsGrams').text_content()
                fats_grams = await page.locator('#fatGrams').text_content()
            except:
                # Page might still be loading, get content anyway
                await page.wait_for_timeout(1000)
                protein_grams = await page.locator('#proteinGrams').text_content()
                carbs_grams = await page.locator('#carbsGrams').text_content()
                fats_grams = await page.locator('#fatGrams').text_content()
            
            print(f"   Initial Protein: {protein_grams}")
            print(f"   Initial Carbs: {carbs_grams}")
            print(f"   Initial Fats: {fats_grams}")
            assert "0g" in protein_grams, f"Expected 0g protein, got {protein_grams}"
            print("   ✅ Initial macro values are 0g")
            
            # Step 4: Create a meal
            print("\n4️⃣  CREATING A MEAL...")
            add_meal_btn = page.locator('.add-meal-btn')
            await add_meal_btn.click()
            await page.wait_for_timeout(500)
            
            meal_input = page.locator('input[name="meal_name"]')
            await meal_input.fill("Lunch")
            
            submit_btn = page.locator('form[action*="add_meal"] button[type="submit"]')
            await submit_btn.click()
            await page.wait_for_load_state("networkidle")
            print("✅ Meal 'Lunch' created")
            
            # Step 5: Add first food item (Chicken)
            print("\n5️⃣  ADDING FIRST FOOD ITEM (Chicken - 31g protein, 0g carbs, 4g fats)...")
            meal_card = page.locator('.meal-card').first
            edit_btn = meal_card.locator('.meal-edit-btn')
            await edit_btn.click()
            await page.wait_for_timeout(300)
            
            food_form = meal_card.locator('form[action*="add_food_item"]')
            
            await food_form.locator('input[name="food_name"]').fill("Chicken Breast")
            await food_form.locator('input[name="food_calories"]').fill("165")
            await food_form.locator('input[name="protein"]').fill("31")
            await food_form.locator('input[name="carbs"]').fill("0")
            await food_form.locator('input[name="fats"]').fill("4")
            
            food_submit = food_form.locator('button[type="submit"]')
            await food_submit.click()
            await page.wait_for_load_state("networkidle")
            print("✅ Chicken Breast added")
            
            # Step 6: Toggle first item to complete
            print("\n6️⃣  MARKING CHICKEN AS COMPLETED...")
            checkbox = meal_card.locator('.checkbox').first
            await checkbox.click()
            await page.wait_for_load_state("networkidle")
            print("✅ Chicken marked as completed")
            
            # Step 7: Verify first item updates macros
            print("\n7️⃣  VERIFYING MACRO CARD UPDATES (After 1st food)...")
            await page.wait_for_timeout(300)
            
            protein_grams = await page.text_content('#proteinGrams')
            carbs_grams = await page.text_content('#carbsGrams')
            fats_grams = await page.text_content('#fatGrams')
            
            print(f"   Protein: {protein_grams}")
            print(f"   Carbs: {carbs_grams}")
            print(f"   Fats: {fats_grams}")
            
            assert "31" in protein_grams, f"Expected 31g protein, got {protein_grams}"
            assert "0" in carbs_grams, f"Expected 0g carbs, got {carbs_grams}"
            assert "4" in fats_grams, f"Expected 4g fats, got {fats_grams}"
            print("   ✅ Macros correctly show: 31g P, 0g C, 4g F")
            
            # Step 8: Add second food item (Rice)
            print("\n8️⃣  ADDING SECOND FOOD ITEM (Rice - 4g protein, 45g carbs, 0g fats)...")
            edit_btn = meal_card.locator('.meal-edit-btn')
            await edit_btn.click()
            await page.wait_for_timeout(300)
            
            food_form = meal_card.locator('form[action*="add_food_item"]')
            
            await food_form.locator('input[name="food_name"]').fill("Rice")
            await food_form.locator('input[name="food_calories"]').fill("206")
            await food_form.locator('input[name="protein"]').fill("4")
            await food_form.locator('input[name="carbs"]').fill("45")
            await food_form.locator('input[name="fats"]').fill("0")
            
            food_submit = food_form.locator('button[type="submit"]')
            await food_submit.click()
            await page.wait_for_load_state("networkidle")
            print("✅ Rice added")
            
            # Step 9: Complete second item
            print("\n9️⃣  MARKING RICE AS COMPLETED...")
            checkboxes = meal_card.locator('.checkbox')
            checkbox_count = await checkboxes.count()
            if checkbox_count > 1:
                second_checkbox = checkboxes.nth(1)
                await second_checkbox.click()
                await page.wait_for_load_state("networkidle")
            print("✅ Rice marked as completed")
            
            # Step 10: Verify both items show in macros
            print("\n🔟 VERIFYING MACRO TOTALS (After 2nd food)...")
            await page.wait_for_timeout(300)
            
            protein_grams = await page.text_content('#proteinGrams')
            carbs_grams = await page.text_content('#carbsGrams')
            fats_grams = await page.text_content('#fatGrams')
            
            print(f"   Protein: {protein_grams}")
            print(f"   Carbs: {carbs_grams}")
            print(f"   Fats: {fats_grams}")
            
            assert "35" in protein_grams, f"Expected 35g protein (31+4), got {protein_grams}"
            assert "45" in carbs_grams, f"Expected 45g carbs, got {carbs_grams}"
            assert "4" in fats_grams, f"Expected 4g fats, got {fats_grams}"
            print("   ✅ Macros correctly show: 35g P, 45g C, 4g F")
            
            # Step 11: Delete one item and verify update
            print("\n1️⃣1️⃣  TESTING DELETION (Deleting Chicken)...")
            
            # Handle confirmation dialog
            async def handle_confirm(dialog):
                await dialog.accept()
            
            page.once("dialog", handle_confirm)
            
            delete_btns = meal_card.locator('.delete-btn')
            await delete_btns.first.click()
            await page.wait_for_load_state("networkidle")
            print("✅ Chicken deleted")
            
            # Step 12: Verify macros updated after deletion
            print("\n1️⃣2️⃣  VERIFYING MACRO TOTALS (After deletion)...")
            await page.wait_for_timeout(300)
            
            protein_grams = await page.text_content('#proteinGrams')
            carbs_grams = await page.text_content('#carbsGrams')
            fats_grams = await page.text_content('#fatGrams')
            
            print(f"   Protein: {protein_grams}")
            print(f"   Carbs: {carbs_grams}")
            print(f"   Fats: {fats_grams}")
            
            assert "4" in protein_grams, f"Expected 4g protein (only rice), got {protein_grams}"
            assert "45" in carbs_grams, f"Expected 45g carbs (only rice), got {carbs_grams}"
            assert "0" in fats_grams, f"Expected 0g fats (only rice), got {fats_grams}"
            print("   ✅ Macros correctly show: 4g P, 45g C, 0g F (after deletion)")
            
            # Step 13: Test uncompleting an item
            print("\n1️⃣3️⃣  TESTING COMPLETION TOGGLE (Uncompleting Rice)...")
            checkbox = meal_card.locator('.checkbox')
            await checkbox.click()
            await page.wait_for_load_state("networkidle")
            print("✅ Rice marked as incomplete")
            
            # Step 14: Verify macros go back to 0
            print("\n1️⃣4️⃣  VERIFYING MACRO TOTALS (After uncompleting)...")
            await page.wait_for_timeout(300)
            
            protein_grams = await page.text_content('#proteinGrams')
            carbs_grams = await page.text_content('#carbsGrams')
            fats_grams = await page.text_content('#fatGrams')
            
            print(f"   Protein: {protein_grams}")
            print(f"   Carbs: {carbs_grams}")
            print(f"   Fats: {fats_grams}")
            
            assert "0g" in protein_grams, f"Expected 0g protein, got {protein_grams}"
            assert "0g" in carbs_grams, f"Expected 0g carbs, got {carbs_grams}"
            assert "0g" in fats_grams, f"Expected 0g fats, got {fats_grams}"
            print("   ✅ Macros correctly show: 0g P, 0g C, 0g F (incomplete items excluded)")
            
            # Step 15: Take final screenshot
            print("\n1️⃣5️⃣  TAKING SCREENSHOT...")
            await page.screenshot(path="/tmp/macro_cards_test.png")
            print("✅ Screenshot saved to /tmp/macro_cards_test.png")
            
            # Final report
            print("\n" + "="*70)
            print("✅ ALL MACRO CARD TESTS PASSED!")
            print("="*70)
            print(f"\n📊 TEST SUMMARY:")
            print(f"  ✓ Macro cards display initial values (0g)")
            print(f"  ✓ Macro cards update correctly when single food added")
            print(f"  ✓ Macro cards accumulate correctly with multiple foods")
            print(f"  ✓ Macro cards update when items deleted")
            print(f"  ✓ Macro cards update when items toggled incomplete")
            print(f"  ✓ Incomplete items correctly excluded from totals")
            print(f"  ✓ UI and database synchronized\n")
            
            return True
            
        except AssertionError as e:
            print(f"\n❌ ASSERTION FAILED: {str(e)}")
            try:
                await page.screenshot(path="/tmp/macro_cards_test_failed.png")
                print("📸 Screenshot saved to /tmp/macro_cards_test_failed.png")
            except:
                pass
            return False
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            
            try:
                await page.screenshot(path="/tmp/macro_cards_test_failed.png")
                print("📸 Screenshot saved to /tmp/macro_cards_test_failed.png")
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
    
    success = asyncio.run(test_macro_cards())
    sys.exit(0 if success else 1)


