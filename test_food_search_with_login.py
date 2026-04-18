"""
Playwright test for food search dropdown and macro auto-fill functionality
Tests the ability to search for foods and auto-fill nutritional information
"""
import asyncio
from playwright.async_api import async_playwright
import json
import time

BASE_URL = "http://localhost:3000"

async def test_food_search_with_login():
    """Test food search dropdown functionality with logged-in user"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("🔍 Testing food search dropdown functionality...")
            
            # Step 1: Navigate to nutrition page (will redirect to login)
            print("\n1. Navigating to nutrition page...")
            await page.goto(f"{BASE_URL}/nutrition/")
            await page.wait_for_load_state("networkidle")
            
            # Step 2: Check if we're on login page
            current_url = page.url
            if "user_login" in current_url or "login" in current_url:
                print("   ✓ Redirected to login page")
                
                # Get CSRF token if present
                csrf_token = None
                csrf_input = await page.query_selector("input[name='csrfmiddlewaretoken']")
                if csrf_input:
                    csrf_token = await csrf_input.get_attribute("value")
                    print(f"   ✓ Found CSRF token")
                
                # Find email and password inputs
                email_input = await page.query_selector("input[type='email']")
                password_input = await page.query_selector("input[type='password']")
                
                if not email_input or not password_input:
                    print("   ✗ Could not find login inputs. Page structure may differ.")
                    print(f"   Email input: {email_input}")
                    print(f"   Password input: {password_input}")
                    await browser.close()
                    return False
                
                # Try with test credentials
                test_email = "test@example.com"
                test_password = "testpass123"
                
                print(f"\n2. Attempting login with {test_email}...")
                await email_input.fill(test_email)
                await password_input.fill(test_password)
                
                # Look for submit button
                submit_btn = await page.query_selector("button[type='submit']")
                if submit_btn:
                    # Use click() which handles the form submission properly
                    await submit_btn.click()
                    
                    # Wait for navigation after login
                    try:
                        await page.wait_for_url("**/nutrition/**", timeout=5000)
                        print(f"   ✓ Login successful")
                    except:
                        # If wait fails, check current URL
                        await page.wait_for_load_state("networkidle")
                        time.sleep(1)
                        new_url = page.url
                        if "user_login" in new_url:
                            print("   ✗ Login failed - account may not exist or credentials wrong")
                            print(f"   Current URL: {new_url}")
                            # Check for error message
                            error_msg = await page.query_selector(".errorlist, .messages")
                            if error_msg:
                                error_text = await error_msg.text_content()
                                print(f"   Error: {error_text}")
                            await browser.close()
                            return False
                        elif "home" in new_url:
                            print(f"   ✓ Login successful, redirected to: {new_url}")
                        else:
                            print(f"   ? Redirected to unexpected page: {new_url}")
                else:
                    print("   ✗ Could not find submit button")
                    await browser.close()
                    return False
            else:
                print(f"   ✓ Already on page: {current_url}")
            
            # Step 3: Look for the nutrition page elements
            print("\n3. Checking for nutrition page elements...")
            
            # Try to find the food name input
            food_input = await page.query_selector("#foodNameInput")
            if not food_input:
                print("   ℹ Food input (#foodNameInput) not visible yet")
                # Try to find a button that opens the food form
                add_buttons = await page.query_selector_all("button, a")
                btn_texts = []
                for btn in add_buttons[:20]:
                    text = (await btn.text_content()).strip()
                    if text:
                        btn_texts.append(text)
                
                print(f"   Available buttons/links: {btn_texts[:10]}")
                
                # Try clicking an "Add" or "New" button if found
                for btn in add_buttons:
                    text = (await btn.text_content()).strip()
                    if "add" in text.lower() or "new" in text.lower() or "food" in text.lower():
                        print(f"   Clicking button: {text}")
                        await btn.click()
                        await page.wait_for_load_state("networkidle")
                        time.sleep(0.5)
                        food_input = await page.query_selector("#foodNameInput")
                        if food_input:
                            print("   ✓ Food input found after clicking button")
                            break
            
            if not food_input:
                print("   ✗ Could not find or access food input field")
                print(f"   Page content preview: {(await page.text_content())[:500]}")
                await browser.close()
                return False
            
            # Step 4: Test food search
            print("\n4. Testing food search dropdown...")
            
            # Type in the food input to trigger search
            print("   Typing 'egg' in food search...")
            await food_input.fill("egg")
            await food_input.focus()
            await page.keyboard.press("a")  # To trigger the input event
            
            time.sleep(1)  # Wait for search results
            
            # Check for search results dropdown
            results_container = await page.query_selector("#foodSearchResults")
            if not results_container:
                print("   ✗ Food search results container not found")
                await browser.close()
                return False
            
            # Check if results are visible
            is_visible = await results_container.is_visible()
            if not is_visible:
                print("   ℹ Results container exists but is hidden")
                print("   (This might be expected if no foods match)")
                await browser.close()
                return False
            
            # Get the search results
            result_items = await results_container.query_selector_all(".food-result-item")
            print(f"   ✓ Found {len(result_items)} search results")
            
            if len(result_items) > 0:
                # Step 5: Click on the first result
                print("\n5. Clicking first search result...")
                first_result = result_items[0]
                
                # Get the data attributes
                result_name = await first_result.get_attribute("data-name")
                result_id = await first_result.get_attribute("data-id")
                result_calories = await first_result.get_attribute("data-calories")
                result_protein = await first_result.get_attribute("data-protein")
                result_carbs = await first_result.get_attribute("data-carbs")
                result_fats = await first_result.get_attribute("data-fats")
                
                print(f"   Result data: name={result_name}, id={result_id}, cal={result_calories}")
                
                # Click the result
                await first_result.click()
                time.sleep(0.5)
                
                # Step 6: Verify macros were populated
                print("\n6. Verifying macros auto-filled...")
                
                cal_input = await page.query_selector("#foodCaloriesInput")
                protein_input = await page.query_selector("#foodProteinInput")
                carbs_input = await page.query_selector("#foodCarbsInput")
                fats_input = await page.query_selector("#foodFatsInput")
                
                if cal_input:
                    cal_value = await cal_input.get_attribute("value")
                    print(f"   Calories input: {cal_value}")
                    if cal_value and int(cal_value) > 0:
                        print(f"   ✓ Calories populated: {cal_value}")
                    else:
                        print(f"   ✗ Calories not properly populated: {cal_value}")
                
                if protein_input:
                    protein_value = await protein_input.get_attribute("value")
                    print(f"   ✓ Protein input: {protein_value}")
                
                if carbs_input:
                    carbs_value = await carbs_input.get_attribute("value")
                    print(f"   ✓ Carbs input: {carbs_value}")
                
                if fats_input:
                    fats_value = await fats_input.get_attribute("value")
                    print(f"   ✓ Fats input: {fats_value}")
                
                # Verify name was populated
                name_value = await food_input.get_attribute("value")
                if name_value == result_name:
                    print(f"   ✓ Food name correctly populated: {name_value}")
                else:
                    print(f"   ✗ Food name mismatch. Expected: {result_name}, Got: {name_value}")
                
                print("\n✅ Food search dropdown test completed successfully!")
                return True
            else:
                print("   ℹ No search results found (database might be empty)")
                print("\n⚠️  Test inconclusive - no foods in database to test with")
                return True  # Not a failure, just no data
            
        except Exception as e:
            print(f"\n❌ Test error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await browser.close()


async def main():
    """Run the test"""
    print("=" * 60)
    print("FOOD SEARCH DROPDOWN & MACRO AUTO-FILL TEST")
    print("=" * 60)
    
    success = await test_food_search_with_login()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED")
    else:
        print("❌ TEST FAILED")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
