# Nutrition Macro Integration - Playwright Test Guide

## Quick Start

### Prerequisites
- Server running: `cd fitness_ai_app && ./setup_and_run.sh`
- Virtual environment activated: `source ~/venv_dev2-cust1/bin/activate`
- Playwright installed (included in requirements.txt)

### Run the Test

```bash
cd fitness_ai_app
source ~/venv_dev2-cust1/bin/activate

# Make sure server is running in another terminal first!
# Then run the test:
python test_nutrition_macro_playwright.py
```

## What the Test Does

1. **Authentication**
   - Logs in as testuser@spotter.ai
   - Redirects to home_dash on success

2. **Nutrition Page**
   - Navigates to /nutrition/
   - Verifies page loads with "Nutrition" heading

3. **Meal Creation**
   - Clicks "Add Meal" button
   - Creates meal named "Breakfast"
   - Submits and verifies creation

4. **Food Item Creation with Macros**
   Adds 3 food items to breakfast:
   
   | Item | Calories | Protein | Carbs | Fats |
   |------|----------|---------|-------|------|
   | Oatmeal | 150 | 5g | 27g | 3g |
   | Eggs | 155 | 13g | 1g | 11g |
   | Berries | 80 | 1g | 19g | 0g |
   | **TOTAL** | **385** | **19g** | **47g** | **14g** |

5. **UI Verification**
   - Verifies all 3 food items display on page
   - Checks meal total calories shows
   - Takes screenshot for visual verification

6. **Screenshot Output**
   - Success: `/tmp/nutrition_macro_test.png`
   - Failure: `/tmp/nutrition_macro_test_failed.png`

## Expected Output

```
======================================================================
🍎 NUTRITION FOOD MACRO INTEGRATION TEST
======================================================================

1️⃣  NAVIGATING TO LOGIN...
✅ Login page loaded

2️⃣  LOGGING IN...
✅ Successfully logged in and redirected to home_dash

3️⃣  NAVIGATING TO NUTRITION PAGE...
✅ Nutrition page loaded: Nutrition

4️⃣  CREATING A NEW MEAL...
✅ Meal 'Breakfast' created

5️⃣  ADDING FOOD ITEMS WITH MACROS...

   📝 Adding Oatmeal...
   ✅ Oatmeal added (150kcal)

   📝 Adding Eggs...
   ✅ Eggs added (155kcal)

   📝 Adding Berries...
   ✅ Berries added (80kcal)

6️⃣  VERIFYING FOOD ITEMS IN UI...
✅ 3 food items displayed on page
   ✅ Oatmeal visible
   ✅ Eggs visible
   ✅ Berries visible

7️⃣  CHECKING MEAL TOTALS...
✅ Meal total displayed: 385 kcal

8️⃣  TAKING SCREENSHOT...
✅ Screenshot saved to /tmp/nutrition_macro_test.png

======================================================================
✅ ALL TESTS PASSED!
======================================================================

📊 TEST SUMMARY:
  ✓ User authentication successful
  ✓ Nutrition page loaded
  ✓ Meal created: Breakfast
  ✓ 3 food items added with macros
  ✓ Total macros: 385 calories
  ✓ Food items displayed correctly in UI
  ✓ Macros integration working end-to-end
```

## Test Files

### test_nutrition_macro_playwright.py
- **Location**: `fitness_ai_app/test_nutrition_macro_playwright.py`
- **Type**: End-to-end browser automation test
- **Framework**: Playwright (async)
- **Headless**: Yes (no browser window)
- **Duration**: ~15-30 seconds

### test_nutrition_macros_integration.py (Alternative)
- **Location**: `fitness_ai_app/test_nutrition_macros_integration.py`
- **Type**: Mixed integration test with browser
- **Combines**: Django ORM validation + Playwright
- **Includes**: Database verification after UI actions

## Troubleshooting

### Test fails: "net::ERR_CONNECTION_REFUSED"
**Solution**: Make sure server is running
```bash
# Terminal 1:
cd fitness_ai_app
./setup_and_run.sh

# Terminal 2 (after server is ready):
source ~/venv_dev2-cust1/bin/activate
python test_nutrition_macro_playwright.py
```

### Test fails: "Login failed"
**Solution**: Verify test user exists
```bash
cd fitness_ai_app
python manage.py shell
>>> from django.contrib.auth.models import User
>>> user, _ = User.objects.get_or_create(username="testuser@spotter.ai")
>>> user.set_password("testpass123")
>>> user.save()
```

### Test times out on page navigation
**Solution**: Increase timeout in test file
```python
# Change this line in test:
await page.wait_for_url(f"{BASE_URL}/home_dash/", timeout=15000)
# To:
await page.wait_for_url(f"{BASE_URL}/home_dash/", timeout=30000)
```

## Manual Testing

If you prefer to test manually:

1. **Start server**: `cd fitness_ai_app && ./setup_and_run.sh`
2. **Login**: Navigate to `http://localhost:3000/user_login/`
   - Email: `testuser@spotter.ai`
   - Password: `testpass123`
3. **Go to Nutrition**: Click nutrition tab or visit `http://localhost:3000/nutrition/`
4. **Add Meal**: Click "Log a meal" button, enter "Breakfast"
5. **Add Food Items**: 
   - Click edit button on meal
   - Fill out form with food name, calories, and macros
   - Submit form
   - Repeat for each food item
6. **Verify**: Check that all items appear in the meal card with correct totals

## Integration Points

### Frontend → Backend Flow
1. User fills food form with macros
2. Form submits to `/nutrition/add_food_item/` (POST)
3. Django view validates data
4. FoodItem created in database with macros
5. Page redirects to nutrition view
6. Template displays updated meals with food items

### Database
- **Model**: `FoodItem` (core/models.py)
- **Fields**: calories, protein, carbs, fats, completed
- **Relations**: Many-to-one with Meal

### Template
- **File**: `core/templates/nutrition_dir/nutrition_page.html`
- **Form**: Lines 155-169 contain macro input fields
- **Display**: Lines 129-153 display food items with calories

## Performance Notes

- **Test Duration**: 15-30 seconds
- **Browser**: Chromium (headless, fast)
- **Network**: All requests to localhost:3000
- **Screenshot**: Taken at end of test (PNG format)

## CI/CD Integration

To run this in a CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run Nutrition Macro Test
  working-directory: fitness_ai_app
  run: |
    source ~/venv_dev2-cust1/bin/activate
    # Start server in background
    python manage.py runserver 0.0.0.0:3000 &
    SERVER_PID=$!
    sleep 5
    
    # Run test
    python test_nutrition_macro_playwright.py
    TEST_RESULT=$?
    
    # Kill server
    kill $SERVER_PID
    
    exit $TEST_RESULT
```

## Next Steps

- Extend test to cover edge cases (invalid input, empty fields)
- Add tests for macro totals calculation
- Test date filtering with macros
- Add performance benchmarks
- Test with different user accounts
