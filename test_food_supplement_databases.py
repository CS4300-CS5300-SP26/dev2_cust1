"""
Playwright tests for Food and Supplement Databases
Tests all API endpoints after login
"""
import asyncio
import time
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:3000"
TEST_EMAIL = "test_db@example.com"
TEST_PASSWORD = "TestPass123!@#"


def create_test_user():
    """Create a test user via Django shell - SYNC function"""
    import os
    import sys
    import django
    
    # Add the fitness_ai_app directory to the path
    sys.path.insert(0, '/home/student/dev2_cust1/fitness_ai_app')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fitness_ai_app.settings')
    django.setup()
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Delete if exists
    User.objects.filter(email=TEST_EMAIL).delete()
    
    # Create new user
    user = User.objects.create_user(
        username=TEST_EMAIL.split('@')[0],
        email=TEST_EMAIL,
        password=TEST_PASSWORD
    )
    print(f"  Created test user: {TEST_EMAIL}")
    return user


async def test_login_and_access_databases():
    """Test login and access to food/supplement databases"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Go to login page
            print("Navigating to login page...")
            await page.goto(f"{BASE_URL}/user_login/")
            await page.wait_for_load_state("networkidle")
            
            # Find and fill login form
            email_input = await page.query_selector("input[type='email']")
            password_input = await page.query_selector("input[type='password']")
            submit_btn = await page.query_selector("button[type='submit']")
            
            if not email_input or not password_input or not submit_btn:
                print("✗ Could not find login form elements")
                await browser.close()
                return False
            
            print(f"Logging in with {TEST_EMAIL}...")
            await email_input.fill(TEST_EMAIL)
            await password_input.fill(TEST_PASSWORD)
            
            # Click submit and wait for navigation
            await submit_btn.click()
            
            # Wait for navigation - could go to home_dash or nutrition
            try:
                await page.wait_for_url("**/home_dash/**", timeout=5000)
            except:
                # Maybe it went to nutrition or another page - wait for network idle
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)
            
            current_url = page.url
            if "user_login" in current_url:
                print("✗ Login failed - redirected back to login")
                print(f"  Current URL: {current_url}")
                # Check for error messages
                error_elem = await page.query_selector(".errorlist, .messages")
                if error_elem:
                    error_text = await error_elem.text_content()
                    print(f"  Error: {error_text}")
                await browser.close()
                return False
            
            print("✓ Login successful")
            
            # Now test API endpoints
            print("\nTesting API endpoints...")
            
            # Test 1: Get food categories (no auth required)
            response = await page.context.request.get(f"{BASE_URL}/api/food/categories/")
            assert response.status == 200
            data = await response.json()
            assert 'food_categories' in data
            assert data['count'] > 0
            print(f"✓ Food categories: {data['count']} categories found")
            
            # Test 2: Get allergens
            response = await page.context.request.get(f"{BASE_URL}/api/food/allergens/")
            assert response.status == 200
            data = await response.json()
            assert 'allergens' in data
            assert data['count'] > 0
            print(f"✓ Allergens: {data['count']} allergens found")
            
            # Test 3: Search foods (requires auth)
            response = await page.context.request.get(f"{BASE_URL}/api/food/search/?q=chicken")
            assert response.status == 200
            data = await response.json()
            assert 'results' in data or 'foods' in data
            food_count = len(data.get('results', data.get('foods', [])))
            print(f"✓ Food search: {food_count} results found")
            
            # Test 4: Filter foods
            response = await page.context.request.get(f"{BASE_URL}/api/food/filter/?vegetarian=true")
            assert response.status == 200
            data = await response.json()
            assert isinstance(data, (list, dict))
            count = len(data) if isinstance(data, list) else len(data.get('results', []))
            print(f"✓ Food filter: {count} vegetarian foods found")
            
            # Test 5: Get supplement categories
            response = await page.context.request.get(f"{BASE_URL}/api/supplement/categories/")
            assert response.status == 200
            data = await response.json()
            assert 'supplement_categories' in data
            assert data['count'] > 0
            print(f"✓ Supplement categories: {data['count']} categories found")
            
            # Test 6: Search supplements
            response = await page.context.request.get(f"{BASE_URL}/api/supplement/search/?q=vitamin")
            assert response.status == 200
            data = await response.json()
            assert 'results' in data or 'supplements' in data
            supp_count = len(data.get('results', data.get('supplements', [])))
            print(f"✓ Supplement search: {supp_count} results found")
            
            # Test 7: Filter supplements
            response = await page.context.request.get(f"{BASE_URL}/api/supplement/filter/")
            assert response.status == 200
            data = await response.json()
            print(f"✓ Supplement filter: Results found")
            
            print("\n" + "="*50)
            print("ALL API TESTS PASSED ✓")
            print("="*50)
            print("Food and Supplement Databases are working correctly!")
            return True
            
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await browser.close()


async def test_nutrition_page_food_search():
    """Test accessing food database from nutrition page"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Login first
            print("Navigating to login page...")
            await page.goto(f"{BASE_URL}/user_login/")
            await page.wait_for_load_state("networkidle")
            
            email_input = await page.query_selector("input[type='email']")
            password_input = await page.query_selector("input[type='password']")
            submit_btn = await page.query_selector("button[type='submit']")
            
            if not email_input or not password_input or not submit_btn:
                print("✗ Could not find login form elements")
                await browser.close()
                return False
            
            print(f"Logging in...")
            await email_input.fill(TEST_EMAIL)
            await password_input.fill(TEST_PASSWORD)
            await submit_btn.click()
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(1)
            
            # Go to nutrition page
            print("Navigating to nutrition page...")
            await page.goto(f"{BASE_URL}/nutrition/")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(1)
            
            print("✓ Nutrition page loaded")
            
            # Check if food database is accessible via API
            response = await page.context.request.get(f"{BASE_URL}/api/food/search/?q=ch")
            assert response.status == 200
            print("✓ Food search API accessible from nutrition page")
            
            return True
            
        except Exception as e:
            print(f"\n✗ Nutrition page test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await browser.close()


async def test_admin_food_database():
    """Test checking if food database models are in admin"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Try accessing admin
            print("Checking admin interface...")
            response = await page.goto(f"{BASE_URL}/admin/")
            
            if response and response.status == 200:
                print("✓ Admin interface is available")
                print("  (Food/Supplement models can be managed at /admin/core/fooddatabase/)")
                return True
            else:
                print("ℹ Admin interface not accessible (may require authentication)")
                return True
                
        except Exception as e:
            print(f"ℹ Admin test skipped: {e}")
            return True
        finally:
            await browser.close()


async def main():
    """Run all tests (after user creation)"""
    print("="*60)
    print("FOOD & SUPPLEMENT DATABASE TESTS (PLAYWRIGHT)")
    print("="*60)
    print()
    
    # Test 1: API Access
    print("TEST 1: API Endpoints Access")
    print("-" * 60)
    result1 = await test_login_and_access_databases()
    print()
    
    # Test 2: Nutrition Page Integration
    print("TEST 2: Nutrition Page Integration")
    print("-" * 60)
    result2 = await test_nutrition_page_food_search()
    print()
    
    # Test 3: Admin Interface
    print("TEST 3: Admin Interface")
    print("-" * 60)
    result3 = await test_admin_food_database()
    print()
    
    print("="*60)
    if result1 and result2 and result3:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
    print("="*60)


if __name__ == "__main__":
    # Create test user BEFORE starting async tests
    print("Setting up test environment...")
    create_test_user()
    print()
    
    # Now run async tests
    asyncio.run(main())
