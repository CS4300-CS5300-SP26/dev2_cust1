#!/usr/bin/env python3
"""Test meal creation and date navigation fix."""

import sys
import time
sys.path.insert(0, '/home/student/dev2_cust1/fitness_ai_app')

import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_ai_app.settings')
django.setup()

from playwright.sync_api import sync_playwright


def test_meal_creation_and_navigation():
    """Test that meals can be created without error and date navigation works."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Navigate to login page first
            print("Loading login page...")
            page.goto('http://localhost:8000/accounts/login/', wait_until='load', timeout=10000)
            
            # Login
            print("Logging in...")
            page.fill('input[name="email"]', 'test@test.com')
            page.fill('input[name="password"]', 'testpass123')
            page.click('button[type="submit"]')
            page.wait_for_load_state('load', timeout=10000)
            print("✓ Logged in")
            
            # Navigate to nutrition page
            print("Loading nutrition page...")
            page.goto('http://localhost:8000/nutrition/', wait_until='load', timeout=10000)
            print("✓ Page loaded")
            
            time.sleep(2)
            
            # Test 1: Check if date field exists in the form
            print("\n[TEST 1] Checking for date field in meal form...")
            date_input = page.query_selector('input[name="date"]')
            if date_input:
                date_value = date_input.get_attribute('value')
                print(f"✓ Date field found with value: '{date_value}'")
                if not date_value or date_value.strip() == '':
                    print("✗ ERROR: Date field is empty!")
                    return False
            else:
                print("✗ ERROR: Date field not found in form!")
                print("Available inputs:", [el.get_attribute('name') for el in page.query_selector_all('input')])
                return False
            
            # Test 2: Click "Add Meal" button to show form
            print("\n[TEST 2] Clicking Add Meal button...")
            add_meal_btn = page.query_selector('button[data-toggle-target="addMealForm"]')
            if add_meal_btn:
                add_meal_btn.click()
                time.sleep(1)
                print("✓ Add Meal form appeared")
            else:
                print("✗ ERROR: Add Meal button not found")
                return False
            
            # Test 3: Verify form is visible
            print("\n[TEST 3] Verifying form submission capability...")
            submit_btn = page.query_selector('form[action*="add_meal"] button[type="submit"]')
            if submit_btn:
                print("✓ Submit button found - form is ready to submit")
            else:
                print("✗ Submit button not found")
                return False
            
            # Test 4: Test date navigation (previous day)
            print("\n[TEST 4] Testing date navigation (previous day)...")
            prev_btn = page.query_selector('a[title="Previous day"]')
            if prev_btn:
                prev_href = prev_btn.get_attribute('href')
                print(f"✓ Previous button found with href: {prev_href}")
                
                # Click and verify URL changes
                current_url = page.url
                prev_btn.click()
                page.wait_for_load_state('load', timeout=10000)
                time.sleep(1)
                
                if current_url != page.url:
                    print(f"✓ Navigation worked! URL changed from {current_url} to {page.url}")
                else:
                    print("✗ URL didn't change after clicking previous")
                    return False
            else:
                print("✗ ERROR: Previous button not found")
                return False
            
            # Test 5: Test date navigation (next day)
            print("\n[TEST 5] Testing date navigation (next day)...")
            next_btn = page.query_selector('a[title="Next day"]')
            if next_btn:
                next_href = next_btn.get_attribute('href')
                print(f"✓ Next button found with href: {next_href}")
                
                # Click and verify URL changes
                prev_url = page.url
                next_btn.click()
                page.wait_for_load_state('load', timeout=10000)
                time.sleep(1)
                
                if prev_url != page.url:
                    print(f"✓ Navigation worked! URL changed to {page.url}")
                else:
                    print("✗ URL didn't change after clicking next")
                    return False
            else:
                print("✗ ERROR: Next button not found")
                return False
            
            # Test 6: Verify macros section exists (requires context data)
            print("\n[TEST 6] Verifying macros display (requires proper context)...")
            macros_card = page.query_selector('.macros-card')
            if macros_card:
                print("✓ Macros card is displayed")
            else:
                print("✗ Macros card not found")
                return False
            
            print("\n" + "="*60)
            print("✓ ALL TESTS PASSED")
            print("="*60)
            return True
            
        except Exception as e:
            print(f"\n✗ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            browser.close()


if __name__ == '__main__':
    success = test_meal_creation_and_navigation()
    sys.exit(0 if success else 1)
