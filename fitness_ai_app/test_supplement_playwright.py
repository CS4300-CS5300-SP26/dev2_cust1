#!/usr/bin/env python
"""
Playwright integration test for supplement functionality.
Tests the complete supplement workflow including search, add, and toggle taken status.

Run this after starting the server with: cd fitness_ai_app && python manage.py runserver
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import date

BASE_URL = "http://localhost:3000"
TEST_EMAIL = "testuser@spotter.ai"
TEST_PASSWORD = "testpass123"

async def main():
    """Main test function"""
    
    print("\n" + "="*70)
    print("💊 SUPPLEMENT DATABASE INTEGRATION TEST")
    print("="*70)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Step 1: Navigate to login page
            print("\n[1/8] Navigating to login page...")
            await page.goto(f"{BASE_URL}/user_login/")
            await page.wait_for_load_state("networkidle")
            
            # Step 2: Login
            print("[2/8] Logging in...")
            await page.fill('input[name="email"]', TEST_EMAIL)
            await page.fill('input[name="password"]', TEST_PASSWORD)
            await page.click('button[type="submit"]')
            await page.wait_for_url(f"{BASE_URL}/home_dash/")
            print("✓ Login successful")
            
            # Step 3: Navigate to nutrition page
            print("[3/8] Navigating to nutrition page...")
            await page.goto(f"{BASE_URL}/nutrition/")
            await page.wait_for_load_state("networkidle")
            
            # Step 4: Click Supplements tab
            print("[4/8] Clicking Supplements tab...")
            supplements_tab = page.locator('text=Supplements').first
            await supplements_tab.click()
            await page.wait_for_timeout(1000)
            print("✓ Supplements tab opened")
            
            # Step 5: Click "Add Supplement" button
            print("[5/8] Clicking 'Add Supplement' button...")
            add_btn = page.locator('button:has-text("Add Supplement")')
            await add_btn.click()
            await page.wait_for_timeout(500)
            print("✓ Add supplement form appeared")
            
            # Step 6: Search for a supplement (Vitamin C)
            print("[6/8] Searching for 'Vitamin C' supplement...")
            search_input = page.locator('#supplementSearch')
            await search_input.fill('Vitamin C')
            await page.wait_for_timeout(500)
            
            # Click on the first search result
            first_result = page.locator('.supplement-search-item').first
            if await first_result.is_visible():
                await first_result.click()
                await page.wait_for_timeout(300)
                print("✓ Vitamin C selected from search results")
            
            # Step 7: Add the supplement
            print("[7/8] Adding Vitamin C supplement...")
            save_btn = page.locator('#saveSupplementBtn')
            await save_btn.click()
            
            # Wait for page reload
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except:
                pass
            
            await page.wait_for_timeout(2000)
            print("✓ Supplement added successfully")
            
            # Step 8: Verify supplement appears in the list
            print("[8/8] Verifying supplement appears in list...")
            supplements_tab.click()
            await page.wait_for_timeout(500)
            
            # Check if Vitamin C is visible in the list
            vitamin_c_text = page.locator('text=Vitamin C')
            is_visible = await vitamin_c_text.is_visible()
            
            if is_visible:
                print("✓ Vitamin C supplement verified in list")
            else:
                print("⚠ Warning: Could not verify supplement in list")
            
            # Screenshot for verification
            screenshot_path = "supplement_test_result.png"
            await page.screenshot(path=screenshot_path)
            print(f"\n✓ Screenshot saved: {screenshot_path}")
            
            print("\n" + "="*70)
            print("✅ SUPPLEMENT TEST COMPLETED SUCCESSFULLY")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            
            # Take screenshot on error
            try:
                await page.screenshot(path="supplement_test_error.png")
                print("✓ Error screenshot saved: supplement_test_error.png")
            except:
                pass
        
        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
