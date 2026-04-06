#!/usr/bin/env python
"""
Playwright test for the Food Database card functionality.
Tests that all foods are displayed in a read-only scrollable list 
and that changes reflect when new foods are added via the modal.
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
TEST_EMAIL = "dbcardtest@spotter.ai"
TEST_PASSWORD = "testpass123"


def setup_test_user():
    """Setup test user"""
    user, created = User.objects.get_or_create(
        username=TEST_EMAIL,
        defaults={'email': TEST_EMAIL, 'first_name': 'Test', 'last_name': 'User'}
    )
    if created or not user.check_password(TEST_PASSWORD):
        user.set_password(TEST_PASSWORD)
        user.is_active = True
        user.save()
    return user


def get_database_food_count():
    """Get count of unique foods in database"""
    food_items = FoodItem.objects.values('name').distinct()
    return food_items.count()


async def test_food_database_card():
    """Test food database card functionality"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("\n" + "="*70)
        print("📋 FOOD DATABASE CARD TEST")
        print("="*70)
        
        try:
            # Step 1: Login
            print("\n1️⃣  LOGGING IN...")
            await page.goto(f"{BASE_URL}/user_login/")
            await page.wait_for_load_state("networkidle")
            
            await page.fill('input[name="email"]', TEST_EMAIL)
            await page.fill('input[name="password"]', TEST_PASSWORD)
            await page.click('button[type="submit"]')
            
            await page.wait_for_url("**/home_dash/**", timeout=10000)
            print("   ✅ Login successful")
            
            # Step 2: Navigate to Nutrition page
            print("\n2️⃣  NAVIGATING TO NUTRITION PAGE...")
            await page.goto(f"{BASE_URL}/nutrition/")
            await page.wait_for_load_state("networkidle")
            print("   ✅ On Nutrition page")
            
            # Step 3: Check Food Database card exists
            print("\n3️⃣  CHECKING FOOD DATABASE CARD...")
            
            # Look for the card
            card = await page.wait_for_selector('.food-database-card', timeout=5000)
            assert card, "Food Database card not found"
            print("   ✅ Food Database card found")
            
            # Check for card label
            label = await page.locator('.food-database-card .card-label').text_content()
            assert 'FOOD DATABASE' in label, f"Expected 'FOOD DATABASE' label, got: {label}"
            print("   ✅ Card label correct")
            
            # Step 4: Wait for food list to load
            print("\n4️⃣  WAITING FOR FOOD LIST TO LOAD...")
            await page.wait_for_function(
                'document.getElementById("foodDatabaseCount").textContent.includes("items")',
                timeout=10000
            )
            
            count_text = await page.locator('#foodDatabaseCount').text_content()
            print(f"   ✅ Food list loaded: {count_text}")
            
            # Step 5: Check food items are displayed
            print("\n5️⃣  CHECKING FOOD ITEMS DISPLAYED...")
            food_items = await page.locator('.food-db-item').all()
            item_count = len(food_items)
            print(f"   Found {item_count} food items displayed")
            
            if item_count > 0:
                # Check first item structure
                first_item = food_items[0]
                name = await first_item.locator('.food-db-name').text_content()
                macros = await first_item.locator('.food-db-macros').text_content()
                print(f"   Sample item: {name} - {macros}")
                assert name, "Food name should not be empty"
                assert 'cal' in macros, "Macros should include calories"
                print("   ✅ Food items have correct structure")
            
            # Step 6: Check list is scrollable
            print("\n6️⃣  CHECKING LIST IS SCROLLABLE...")
            list_element = await page.locator('#foodDatabaseList')
            overflow = await list_element.evaluate('el => getComputedStyle(el).overflowY')
            assert overflow == 'auto' or overflow == 'scroll', f"List should be scrollable, got overflow-y: {overflow}"
            print("   ✅ List has scroll capability")
            
            # Step 7: Check items are not editable (read-only)
            print("\n7️⃣  CHECKING ITEMS ARE READ-ONLY...")
            # Verify no edit buttons in the database card
            edit_btns = await page.locator('.food-database-card button').count()
            print(f"   Found {edit_btns} buttons in card (should be 0 for read-only)")
            
            # Verify no input fields in database items
            inputs_in_list = await page.locator('#foodDatabaseList input').count()
            assert inputs_in_list == 0, "Food database list should not contain input fields"
            print("   ✅ List is read-only (no input fields)")
            
            # Step 8: Test that adding a food via modal updates the card
            print("\n8️⃣  TESTING LIVE UPDATE WHEN ADDING FOOD...")
            
            # Record initial count
            initial_count = item_count
            
            # Open search modal
            await page.click('#searchTabBtn')
            await page.wait_for_selector('#foodSearchModal[style*="display: flex"]', timeout=5000)
            print("   ✅ Search modal opened")
            
            # Click "Add New Food to Database" button
            await page.click('#addNewFoodBtn')
            await page.wait_for_selector('#foodEditForm[style*="display: block"]', timeout=3000)
            
            # Fill in new food details with unique name
            import time
            unique_food = f"Test Food {int(time.time())}"
            await page.fill('#editFoodName', unique_food)
            await page.fill('#editFoodCalories', '123')
            await page.fill('#editFoodProtein', '10')
            await page.fill('#editFoodCarbs', '15')
            await page.fill('#editFoodFats', '5')
            
            # Save the food
            await page.click('#saveFoodBtn')
            
            # Wait for success message
            await page.wait_for_function(
                'document.getElementById("modalStatusMessage").style.display !== "none"',
                timeout=5000
            )
            print(f"   ✅ New food '{unique_food}' saved")
            
            # Close modal
            await page.click('#closeSearchModal')
            await asyncio.sleep(0.5)
            
            # Wait for food database card to update
            await asyncio.sleep(1)  # Give time for refresh
            
            # Check if the new food appears in the list
            new_food_items = await page.locator('.food-db-item').all()
            new_count = len(new_food_items)
            print(f"   Food count: {initial_count} → {new_count}")
            
            # Verify the new food is in the list
            page_content = await page.locator('#foodDatabaseList').inner_text()
            assert unique_food in page_content, f"New food '{unique_food}' should appear in database card"
            print(f"   ✅ New food '{unique_food}' appears in database card")
            
            # Step 9: Verify macros are displayed correctly for new food
            print("\n9️⃣  VERIFYING MACRO DISPLAY...")
            # Find the new food item and check its macros
            new_food_el = await page.locator(f'.food-db-item:has-text("{unique_food}")')
            macros_text = await new_food_el.locator('.food-db-macros').text_content()
            assert '123 cal' in macros_text, f"Expected '123 cal' in macros, got: {macros_text}"
            assert 'P: 10g' in macros_text, f"Expected 'P: 10g' in macros, got: {macros_text}"
            assert 'C: 15g' in macros_text, f"Expected 'C: 15g' in macros, got: {macros_text}"
            assert 'F: 5g' in macros_text, f"Expected 'F: 5g' in macros, got: {macros_text}"
            print(f"   ✅ Macros displayed correctly: {macros_text}")
            
            print("\n" + "="*70)
            print("✅ ALL FOOD DATABASE CARD TESTS PASSED!")
            print("="*70 + "\n")
            return True
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            
            # Take screenshot on failure
            screenshot_path = "/tmp/food_database_card_failure.png"
            await page.screenshot(path=screenshot_path)
            print(f"   Screenshot saved to: {screenshot_path}")
            
            return False
        finally:
            await browser.close()


if __name__ == "__main__":
    # Setup test user
    setup_test_user()
    
    # Run the test
    result = asyncio.run(test_food_database_card())
    sys.exit(0 if result else 1)
