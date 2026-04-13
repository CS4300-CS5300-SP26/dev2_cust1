#!/usr/bin/env python
"""
Playwright test to verify supplement text sizing matches food items.
Run dev server first: cd fitness_ai_app && ./setup_and_run.sh
Then run: python test_supplement_text_fix.py
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import date

BASE_URL = "http://localhost:3000"
TEST_EMAIL = "supplement_test@spotter.ai"
TEST_PASSWORD = "testpass123"

async def main():
    print("\n" + "="*70)
    print("🧪 SUPPLEMENT TEXT SIZING TEST")
    print("="*70)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to login
            print("\n[STEP 1] Navigating to login page...")
            await page.goto(f'{BASE_URL}/login/')
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Try to find email field, might already be logged in
            email_field = await page.query_selector('input[name="email"]')
            if not email_field:
                print("! Already logged in or redirected, going to nutrition page...")
                await page.goto(f'{BASE_URL}/nutrition/')
            else:
                # Check if user exists, if not register
                print("[STEP 2] Attempting login...")
                await page.fill('input[name="email"]', TEST_EMAIL)
                await page.fill('input[name="password"]', TEST_PASSWORD)
                await page.click('button[type="submit"]')
                
                # Wait for either login success or error
                try:
                    await page.wait_for_url(f'{BASE_URL}/nutrition/', timeout=5000)
                    print("✓ Login successful")
                except:
                    # Might need to register
                    print("! Login failed, attempting signup...")
                    await page.goto(f'{BASE_URL}/get_started/')
                    await page.wait_for_selector('input[name="email"]', timeout=5000)
                    await page.fill('input[name="email"]', TEST_EMAIL)
                    await page.fill('input[name="password"]', TEST_PASSWORD)
                    await page.fill('input[name="password_confirm"]', TEST_PASSWORD)
                    
                    # Accept terms
                    checkbox = await page.query_selector('input[name="agree_terms"]')
                    if checkbox:
                        await page.check('input[name="agree_terms"]')
                    
                    await page.click('button[type="submit"]')
                    await page.wait_for_url(f'{BASE_URL}/nutrition/', timeout=10000)
                    print("✓ Signup successful")
            
            # Navigate to nutrition page
            print("\n[STEP 3] Waiting for nutrition page to load...")
            await page.goto(f'{BASE_URL}/nutrition/')
            await page.wait_for_selector('.meal-card', timeout=5000)
            
            # Add a meal if none exists
            print("[STEP 4] Checking for meals or creating one...")
            meals = await page.locator('.meal-card').count()
            
            if meals == 0:
                print("  ! No meals found, creating one...")
                await page.click('.add-meal-btn')
                await page.wait_for_selector('#addMealForm', timeout=5000)
                await page.click('button[type="submit"]')
                await page.wait_for_timeout(2000)
            
            # Click "Add to Meal" button
            print("[STEP 5] Adding items to meal...")
            await page.click('.meal-edit-btn')
            await page.wait_for_selector('#addItemModal', timeout=5000)
            
            # Add food item
            print("  - Adding food item...")
            await page.click('button:has-text("Food Item")')
            await page.wait_for_selector('#foodItemForm', timeout=5000)
            
            await page.fill('.food-search-input', 'Apple')
            await page.wait_for_timeout(1000)
            
            # If search results appear, click first one; otherwise fill manually
            results = await page.locator('.food-search-item').count()
            if results > 0:
                await page.click('.food-search-item:first-child')
            else:
                await page.fill('.food-calories-input', '95')
                await page.fill('.food-protein-input', '0')
                await page.fill('.food-carbs-input', '25')
                await page.fill('.food-fats-input', '0')
            
            await page.click('button:has-text("Add Food Item")')
            await page.wait_for_timeout(2000)
            
            # Add supplement item
            print("  - Adding supplement...")
            await page.click('.meal-edit-btn')
            await page.wait_for_selector('#addItemModal', timeout=5000)
            await page.click('button:has-text("Supplement")')
            await page.wait_for_selector('#supplementForm', timeout=5000)
            
            await page.fill('.supplement-search-input', 'Vitamin C')
            await page.wait_for_timeout(1000)
            
            # If search results appear, click first one
            results = await page.locator('.supplement-search-item').count()
            if results > 0:
                await page.click('.supplement-search-item:first-child')
                await page.wait_for_timeout(500)
            
            await page.click('#saveSupplementBtn')
            await page.wait_for_timeout(2000)
            
            # Close modal
            try:
                await page.click('#closeAddItemModal')
            except:
                pass
            
            # Wait for items to be displayed
            print("\n[STEP 6] Verifying text sizing...")
            await page.wait_for_selector('.food-item', timeout=5000)
            await page.wait_for_selector('.supplement-item', timeout=5000)
            
            # Get computed styles
            food_name = await page.locator('.food-name').first
            supplement_name = await page.locator('.supplement-name').first
            
            food_size = await food_name.evaluate('el => window.getComputedStyle(el).fontSize')
            supplement_size = await supplement_name.evaluate('el => window.getComputedStyle(el).fontSize')
            
            food_color = await food_name.evaluate('el => window.getComputedStyle(el).color')
            supplement_color = await supplement_name.evaluate('el => window.getComputedStyle(el).color')
            
            print(f"\n  Food item:")
            print(f"    Font size: {food_size}")
            print(f"    Color: {food_color}")
            
            print(f"\n  Supplement item:")
            print(f"    Font size: {supplement_size}")
            print(f"    Color: {supplement_color}")
            
            # Check if they match
            if food_size == supplement_size:
                print("\n✓ TEXT SIZES MATCH!")
            else:
                print(f"\n✗ TEXT SIZES DO NOT MATCH")
                print(f"  Food: {food_size}, Supplement: {supplement_size}")
            
            # Take screenshots for visual comparison
            print("\n[STEP 7] Taking screenshots...")
            await page.screenshot(path='/home/student/dev2_cust1/supplement_test_full.png', full_page=False)
            
            # Get meal card area
            meal_card = await page.locator('.meal-card').first
            if meal_card:
                await meal_card.screenshot(path='/home/student/dev2_cust1/supplement_test_card.png')
                print("✓ Screenshot saved to supplement_test_card.png")
            
            print("\n" + "="*70)
            print("✓ TEST COMPLETE")
            print("="*70)
            
        except Exception as e:
            print(f"\n✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
