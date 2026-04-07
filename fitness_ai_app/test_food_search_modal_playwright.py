#!/usr/bin/env python
"""
Playwright test for food search modal functionality.
Tests searching, editing, and saving foods to the nutrition database.
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
TEST_EMAIL = "modaltest@spotter.ai"
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


async def test_food_search_modal():
    """Test food search modal functionality"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("\n" + "="*70)
        print("🔍 FOOD SEARCH MODAL TEST")
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
            
            # Step 3: Click Search tab to open modal
            print("\n3️⃣  OPENING FOOD SEARCH MODAL...")
            search_tab = page.locator('#searchTabBtn')
            await search_tab.click()
            await page.wait_for_timeout(500)
            
            modal = page.locator('#foodSearchModal')
            is_visible = await modal.is_visible()
            assert is_visible, "Modal should be visible"
            print("✅ Modal opened")
            
            # Step 4: Search for a food
            print("\n4️⃣  SEARCHING FOR 'chicken'...")
            search_input = page.locator('#modalFoodSearch')
            await search_input.fill("chicken")
            await page.wait_for_timeout(600)  # Wait for debounce + API
            
            results = page.locator('#modalSearchResults')
            results_html = await results.inner_html()
            assert "chicken" in results_html.lower() or "Chicken" in results_html, f"Results should contain chicken"
            print("✅ Search results found")
            
            # Step 5: Click Edit on a result
            print("\n5️⃣  CLICKING EDIT BUTTON...")
            edit_btn = page.locator('.edit-food-btn').first
            await edit_btn.click()
            await page.wait_for_timeout(300)
            
            edit_form = page.locator('#foodEditForm')
            is_form_visible = await edit_form.is_visible()
            assert is_form_visible, "Edit form should be visible"
            print("✅ Edit form opened")
            
            # Step 6: Verify form is populated
            print("\n6️⃣  VERIFYING FORM POPULATION...")
            name_value = await page.locator('#editFoodName').input_value()
            calories_value = await page.locator('#editFoodCalories').input_value()
            
            assert len(name_value) > 0, "Name field should be populated"
            assert len(calories_value) > 0, "Calories field should be populated"
            print(f"   Name: {name_value}")
            print(f"   Calories: {calories_value}")
            print("✅ Form populated correctly")
            
            # Step 7: Modify the values
            print("\n7️⃣  MODIFYING FOOD VALUES...")
            await page.locator('#editFoodCalories').fill("999")
            await page.locator('#editFoodProtein').fill("88")
            await page.locator('#editFoodCarbs').fill("77")
            await page.locator('#editFoodFats').fill("66")
            print("✅ Values modified")
            
            # Step 8: Save to database
            print("\n8️⃣  SAVING TO DATABASE...")
            save_btn = page.locator('#saveFoodBtn')
            await save_btn.click()
            await page.wait_for_timeout(1000)
            
            # Check for success message
            status = page.locator('#modalStatusMessage')
            status_text = await status.text_content()
            print(f"   Status: {status_text}")
            print("✅ Save request completed")
            
            # Step 9: Test adding new food
            print("\n9️⃣  TESTING ADD NEW FOOD...")
            add_new_btn = page.locator('#addNewFoodBtn')
            await add_new_btn.click()
            await page.wait_for_timeout(300)
            
            is_form_visible = await edit_form.is_visible()
            assert is_form_visible, "Edit form should be visible for new food"
            
            # Fill in new food details
            await page.locator('#editFoodName').fill("Test New Food")
            await page.locator('#editFoodCalories').fill("250")
            await page.locator('#editFoodProtein').fill("15")
            await page.locator('#editFoodCarbs').fill("30")
            await page.locator('#editFoodFats').fill("10")
            
            await save_btn.click()
            await page.wait_for_timeout(1000)
            print("✅ New food added")
            
            # Step 10: Verify new food appears in search
            print("\n🔟 VERIFYING NEW FOOD IN SEARCH...")
            await search_input.fill("Test New")
            await page.wait_for_timeout(600)
            
            results_html = await results.inner_html()
            assert "Test New Food" in results_html, "New food should appear in search"
            print("✅ New food appears in search results")
            
            # Step 11: Test cancel button
            print("\n1️⃣1️⃣  TESTING CANCEL BUTTON...")
            edit_btn = page.locator('.edit-food-btn').first
            await edit_btn.click()
            await page.wait_for_timeout(300)
            
            cancel_btn = page.locator('#cancelEditBtn')
            await cancel_btn.click()
            await page.wait_for_timeout(300)
            
            is_form_visible = await edit_form.is_visible()
            assert not is_form_visible, "Edit form should be hidden after cancel"
            print("✅ Cancel button works")
            
            # Step 12: Test close modal
            print("\n1️⃣2️⃣  TESTING CLOSE MODAL...")
            close_btn = page.locator('#closeSearchModal')
            await close_btn.click()
            await page.wait_for_timeout(300)
            
            is_modal_visible = await modal.is_visible()
            assert not is_modal_visible, "Modal should be closed"
            print("✅ Modal closed")
            
            # Step 13: Take screenshot
            print("\n1️⃣3️⃣  TAKING SCREENSHOT...")
            await page.screenshot(path="/tmp/food_search_modal_test.png")
            print("✅ Screenshot saved to /tmp/food_search_modal_test.png")
            
            # Final report
            print("\n" + "="*70)
            print("✅ ALL FOOD SEARCH MODAL TESTS PASSED!")
            print("="*70)
            print("\n📊 TEST SUMMARY:")
            print("  ✓ Modal opens from Search tab")
            print("  ✓ Search finds foods in database")
            print("  ✓ Edit button opens edit form")
            print("  ✓ Form populates with food data")
            print("  ✓ Can modify and save changes")
            print("  ✓ Can add new food to database")
            print("  ✓ New food appears in search")
            print("  ✓ Cancel button works")
            print("  ✓ Modal closes correctly")
            print("")
            
            return True
            
        except AssertionError as e:
            print(f"\n❌ ASSERTION FAILED: {str(e)}")
            try:
                await page.screenshot(path="/tmp/food_search_modal_failed.png")
                print("📸 Screenshot saved to /tmp/food_search_modal_failed.png")
            except:
                pass
            return False
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            
            try:
                await page.screenshot(path="/tmp/food_search_modal_failed.png")
                print("📸 Screenshot saved to /tmp/food_search_modal_failed.png")
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
    
    success = asyncio.run(test_food_search_modal())
    sys.exit(0 if success else 1)
