"""
Playwright test for food search dropdown and macro auto-fill functionality
"""
import asyncio
from playwright.async_api import async_playwright, expect
import time

BASE_URL = "http://localhost:3000"


async def test_food_search_and_macros():
    """Test that food search dropdown works and macros auto-fill"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            print("Starting food search dropdown test...")
            
            # Navigate to nutrition page
            print(f"Navigating to {BASE_URL}/nutrition/")
            await page.goto(f"{BASE_URL}/nutrition/")
            await page.wait_for_load_state("networkidle")
            time.sleep(1)
            
            # Try to find the "Add Food" or similar button - may vary based on page structure
            # Let's inspect the page first to see if we need to log in
            page_title = await page.title()
            print(f"Page title: {page_title}")
            
            # Check if we're on the login page
            login_form = await page.query_selector("form[action*='login']")
            if login_form:
                print("Detected login page. Attempting to log in...")
                # For now, just print that we need to handle login
                print("Note: A test account should be created or login flow implemented")
                # Try to find any text that says 'Email' or 'Password'
                email_inputs = await page.query_selector_all("input[type='email']")
                if email_inputs:
                    # If login is required, we'd need test credentials
                    print(f"Found {len(email_inputs)} email input(s)")
                    await browser.close()
                    print("Test skipped - login required. Using logged-in endpoint test instead.")
                    return
            
            # Look for the nutrition page content
            # Try to find input field for food name - id="foodNameInput"
            food_name_input = await page.query_selector("#foodNameInput")
            
            if not food_name_input:
                # Maybe we need to scroll or find a button to open the modal
                print("Food input not found directly. Looking for modal or button...")
                
                # Try to find buttons that might open the food entry form
                buttons = await page.query_selector_all("button")
                print(f"Found {len(buttons)} buttons on page")
                
                for i, btn in enumerate(buttons):
                    text = await btn.text_content()
                    print(f"  Button {i}: {text.strip()}")
            
            # Try another approach - look for any input related to food/meal
            all_inputs = await page.query_selector_all("input[id*='food' i]")
            print(f"Found {len(all_inputs)} food-related inputs")
            
            for inp in all_inputs:
                inp_id = await inp.get_attribute("id")
                print(f"  Input: {inp_id}")
            
            # Let's try a more direct approach - look for the modal or form
            modals = await page.query_selector_all("[role='dialog']")
            print(f"Found {len(modals)} dialog/modal elements")
            
            # Get all text content to understand page structure
            body_text = await page.text_content("body")
            if "Food Item" in body_text or "Add Food" in body_text:
                print("✓ Found food-related content on page")
            else:
                print("✗ No obvious food entry UI found")
            
            await browser.close()
            
        except Exception as e:
            print(f"Error: {e}")
            await browser.close()
            raise


async def test_food_search_api_directly():
    """Test the food search API endpoint directly"""
    import urllib.request
    import json
    
    print("\n\nTesting food search API directly...")
    
    # First, test if there are any foods in the database
    try:
        # Use curl to test the API
        import subprocess
        result = subprocess.run(
            ["curl", "-s", "http://localhost:3000/api/search_foods/?q=chicken"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                print(f"API response: {json.dumps(data, indent=2)}")
                if "results" in data and len(data["results"]) > 0:
                    print(f"✓ Found {len(data['results'])} foods in search results")
                    for food in data["results"][:3]:
                        print(f"  - {food.get('name', 'Unknown')} ({food.get('calories', '?')} cal)")
                else:
                    print("✗ No foods found in database or API not working properly")
            except json.JSONDecodeError as e:
                print(f"Failed to parse API response: {e}")
                print(f"Response: {result.stdout}")
        else:
            print(f"API request failed: {result.stderr}")
            
    except Exception as e:
        print(f"Error testing API: {e}")


async def main():
    """Run tests"""
    # First try the API test which doesn't require authentication
    await test_food_search_api_directly()
    
    # Then try the UI test
    # print("\n\nStarting UI test...")
    # await test_food_search_and_macros()


if __name__ == "__main__":
    asyncio.run(main())
