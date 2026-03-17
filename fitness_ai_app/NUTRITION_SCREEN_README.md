# NutritionScreen Documentation

## Overview

A comprehensive nutrition tracking screen built for the Spotter.ai fitness application. The screen follows the dark theme design system with an orange accent color (#e85c00) and provides a complete interface for tracking daily nutrition, meals, and macronutrient information.

**URL**: `/nutrition/`  
**Template**: `core/templates/core/nutrition.html`

## Features

### 1. **Tab Navigation**
Horizontal scrollable tab bar with 4 tabs:
- **Today** (active by default) - Shows today's nutrition data
- **History** - Placeholder for historical data
- **Search** - Placeholder for food search
- **Supplements** - Placeholder for supplement tracking

**Design**:
- Inactive tabs: dark border (#2e2e2e), gray text (#888)
- Active tab: orange border (#e85c00), orange text, subtle orange background

### 2. **Date Navigator**
Allows users to navigate between dates:
- Left chevron: Previous day
- Center label: Current date (formatted as "Fri, Mar 14")
- Right chevron: Next day
- Calendar icon: Open date picker (placeholder)

**Functionality**:
- Clicking chevrons updates the selected date
- Date automatically updates the label

### 3. **Calories Card**
Main nutritional metric card displaying daily calorie intake:
- Label: "CALORIES — TODAY"
- Display: "1820 / 2400 kcal" (consumed / goal)
- Orange progress bar showing percentage
- Clickable for edit functionality

**Styling**:
- Dark card (#181818), 1px border (#242424)
- Border-radius: 14px
- Monospace font for numbers

### 4. **Macros Card**
Three-column grid of macro nutrients:
- **Protein**: 73% | 148g (orange border)
- **Carbs**: 50% | 210g (rose border #e83355)
- **Fat**: 35% | 62g (gray border)

**Styling**:
- Pill-shaped cells with colored borders
- Percentage in large monospace font
- Macro name in uppercase
- Grams in smaller monospace

### 5. **Today's Meals Section**
Displays list of meals with their food items:

#### Section Header
- "TODAY'S MEALS" label
- "+" button to add new meal

#### Meal Card Structure
```
┌─────────────────────────────────────┐
│ Meal Name    |    XXX kcal    | ✎   │  ← Meal header
├─────────────────────────────────────┤
│ ☑ Food name 1                   150 │  ← Completed item
│ ☐ Food name 2                   200 │  ← Incomplete item
│ ☐ + Add food item                   │
└─────────────────────────────────────┘
```

**Interactions**:
- Checkbox toggle: Mark food items as completed
- Completed items: strikethrough + gray text
- Delete button (🗑️): Remove food item
- Pencil button: Edit meal name
- "+ Add food item": Add new food to meal
- "+ Log a meal / supplement": Add new meal (dashed border)

### 6. **Bottom Navigation Bar**
Fixed 5-item navigation bar:
- Home (home icon)
- Train (activity icon)
- **Nutrition** (pie-chart icon, active in orange)
- AI (cpu icon)
- Social (users icon)

**Styling**:
- Fixed position at bottom
- Active tab highlighted in orange (#e85c00)
- Inactive tabs in gray (#444)

## Design Tokens

```css
--background: #0f0f0f          /* Main background */
--card: #181818                /* Card background */
--border: #242424              /* Border color */
--accent: #e85c00              /* Primary accent (orange) */
--accentDim: rgba(232, 92, 0, 0.08)  /* Subtle orange tint */
--textPrimary: #ffffff         /* Main text */
--textSecondary: #cccccc       /* Secondary text */
--textMuted: #555555           /* Muted text */
--proteinColor: #e85c00        /* Protein color (orange) */
--carbColor: #e83355           /* Carbs color (rose) */
--fatColor: #888888            /* Fat color (gray) */
```

## Responsive Design

- **Mobile-first** approach
- Macros grid adjusts from 3 columns to 1 column on small screens
- Bottom navigation remains fixed and accessible
- Content container respects max-width for readability

## JavaScript Functionality

The page includes interactive features:

### Date Navigation
- `#prevDateBtn`: Subtract 1 day from selected date
- `#nextDateBtn`: Add 1 day to selected date
- `#dateLabel`: Displays formatted date (auto-updates)

### Tab Switching
- Click any tab button to switch tabs
- Active state updates visually
- Currently placeholder for other tabs

### Food Item Interactions
- **Checkbox toggle**: Toggle `completed` state
- **Delete button**: Remove food item (with confirmation)
- **Completed styling**: Strikethrough + gray text

### Add/Edit Features (Placeholder)
- Add Meal buttons show alert (ready for modal implementation)
- Edit buttons show alert (ready for modal implementation)
- Card click handlers show alert (ready for modal implementation)

## State Management

Current implementation uses vanilla JavaScript for basic state:
- `selectedDate`: Tracks current date
- Checkbox/completion states stored in DOM classes

**Future Enhancement**: Integrate with React or full JavaScript framework for:
- Complete modal dialogs
- Calorie/macro editing
- Meal management
- Persistent storage (API integration)

## File Structure

```
core/
├── templates/
│   └── core/
│       ├── nutrition.html          (Main template - 33KB)
│       ├── splash.html              (Splash screen)
│       └── nutrition.html          (This file)
├── views.py                         (nutrition() view)
├── urls.py                          (nutrition/ route)
```

## Usage

### Access the page
```
http://localhost:3000/nutrition/
```

### View in browser
The page is fully responsive and optimized for:
- Mobile devices (320px+)
- Tablets
- Desktop browsers

## Future Enhancements

1. **Modal Implementation**
   - Edit calories modal
   - Edit macros modal
   - Add meal modal
   - Add food item modal
   - Edit meal/food modals

2. **Backend Integration**
   - API endpoints for CRUD operations
   - User authentication
   - Database persistence

3. **Advanced Features**
   - Date picker modal using datetime picker
   - Swipe gestures for food item deletion
   - Long-press for inline editing
   - Search functionality for meals
   - Historical data tracking

4. **Real-time Updates**
   - Auto-calculate macro percentages
   - Real-time calorie sum
   - Sync with backend

## Browser Compatibility

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance Notes

- Single HTML file with embedded CSS and JavaScript
- No external dependencies
- Fast load times
- Smooth animations (CSS transitions)
- Optimized for touch interactions

## Accessibility

- Semantic HTML structure
- ARIA labels on interactive elements
- Keyboard navigation support
- High contrast design (#0f0f0f background with white text)
- Touch-friendly button sizes (16px checkboxes, proper spacing)

---

**Created**: March 14, 2026  
**Version**: 1.0.0  
**Framework**: Django Template Engine (with vanilla JavaScript)
