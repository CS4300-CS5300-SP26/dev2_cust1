import React, { useState, useReducer } from 'react';
import { ChevronLeft, ChevronRight, Calendar, Plus, Edit2, Trash2, Check } from 'feather-icons-react';
import { format, addDays, subtractDays } from 'date-fns';
import './NutritionScreen.css';

// Design tokens
const THEME = {
  background: '#0f0f0f',
  card: '#181818',
  border: '#242424',
  accent: '#e85c00',
  accentDim: 'rgba(232, 92, 0, 0.08)',
  textPrimary: '#ffffff',
  textSecondary: '#cccccc',
  textMuted: '#555555',
  proteinColor: '#e85c00',
  carbColor: '#e83355',
  fatColor: '#888888',
};

// Initial state
const INITIAL_STATE = {
  activeTab: 'Today',
  selectedDate: new Date(),
  caloriesConsumed: 1820,
  calorieGoal: 2400,
  macros: {
    protein: { pct: 73, grams: 148 },
    carbs: { pct: 50, grams: 210 },
    fat: { pct: 35, grams: 62 },
  },
  meals: [
    {
      id: 'meal-1',
      name: 'Breakfast',
      items: [
        { id: 'food-1', name: 'Greek yogurt, granola', calories: 320, completed: true },
        { id: 'food-2', name: '2 scrambled eggs', calories: 180, completed: true },
        { id: 'food-3', name: 'Black coffee', calories: 5, completed: false },
      ],
    },
    {
      id: 'meal-2',
      name: 'Lunch',
      items: [
        { id: 'food-4', name: 'Grilled chicken breast', calories: 250, completed: true },
        { id: 'food-5', name: 'Brown rice', calories: 215, completed: true },
      ],
    },
    {
      id: 'meal-3',
      name: 'Dinner',
      items: [
        { id: 'food-6', name: 'Salmon fillet', calories: 350, completed: false },
        { id: 'food-7', name: 'Roasted vegetables', calories: 120, completed: false },
      ],
    },
  ],
};

// Reducer function for state management
function nutritionReducer(state, action) {
  switch (action.type) {
    case 'SET_ACTIVE_TAB':
      return { ...state, activeTab: action.payload };
    case 'SET_DATE':
      return { ...state, selectedDate: action.payload };
    case 'UPDATE_CALORIES':
      return {
        ...state,
        caloriesConsumed: action.payload.consumed,
        calorieGoal: action.payload.goal,
      };
    case 'UPDATE_MACROS':
      return {
        ...state,
        macros: action.payload,
      };
    case 'ADD_MEAL':
      return {
        ...state,
        meals: [
          ...state.meals,
          {
            id: `meal-${Date.now()}`,
            name: action.payload,
            items: [],
          },
        ],
      };
    case 'UPDATE_MEAL':
      return {
        ...state,
        meals: state.meals.map((meal) =>
          meal.id === action.payload.mealId
            ? { ...meal, name: action.payload.name }
            : meal
        ),
      };
    case 'ADD_FOOD_ITEM':
      return {
        ...state,
        meals: state.meals.map((meal) =>
          meal.id === action.payload.mealId
            ? {
                ...meal,
                items: [
                  ...meal.items,
                  {
                    id: `food-${Date.now()}`,
                    name: action.payload.name,
                    calories: action.payload.calories,
                    completed: false,
                  },
                ],
              }
            : meal
        ),
      };
    case 'UPDATE_FOOD_ITEM':
      return {
        ...state,
        meals: state.meals.map((meal) =>
          meal.id === action.payload.mealId
            ? {
                ...meal,
                items: meal.items.map((item) =>
                  item.id === action.payload.foodId
                    ? { ...item, name: action.payload.name, calories: action.payload.calories }
                    : item
                ),
              }
            : meal
        ),
      };
    case 'TOGGLE_FOOD_ITEM':
      return {
        ...state,
        meals: state.meals.map((meal) =>
          meal.id === action.payload.mealId
            ? {
                ...meal,
                items: meal.items.map((item) =>
                  item.id === action.payload.foodId
                    ? { ...item, completed: !item.completed }
                    : item
                ),
              }
            : meal
        ),
      };
    case 'DELETE_FOOD_ITEM':
      return {
        ...state,
        meals: state.meals.map((meal) =>
          meal.id === action.payload.mealId
            ? {
                ...meal,
                items: meal.items.filter((item) => item.id !== action.payload.foodId),
              }
            : meal
        ),
      };
    default:
      return state;
  }
}

// Modal components
const Modal = ({ isOpen, title, children, onClose, onSave }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
        </div>
        {children}
      </div>
    </div>
  );
};

const CaloriesEditModal = ({ isOpen, onClose, currentValues, onSave }) => {
  const [consumed, setConsumed] = useState(currentValues?.consumed || '');
  const [goal, setGoal] = useState(currentValues?.goal || '');

  const handleSave = () => {
    onSave({ consumed: parseInt(consumed) || 0, goal: parseInt(goal) || 0 });
    setConsumed('');
    setGoal('');
  };

  return (
    <Modal isOpen={isOpen} title="Edit Calories" onClose={onClose}>
      <div className="modal-body">
        <div className="input-group">
          <label>Calories Consumed</label>
          <input
            type="number"
            value={consumed}
            onChange={(e) => setConsumed(e.target.value)}
            placeholder="e.g., 1820"
          />
        </div>
        <div className="input-group">
          <label>Calorie Goal</label>
          <input
            type="number"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="e.g., 2400"
          />
        </div>
        <div className="modal-buttons">
          <button className="btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-save" onClick={handleSave}>
            Save
          </button>
        </div>
      </div>
    </Modal>
  );
};

const MacrosEditModal = ({ isOpen, onClose, currentValues, onSave }) => {
  const [macros, setMacros] = useState(currentValues || {});

  const handleMacroChange = (macro, field, value) => {
    setMacros({
      ...macros,
      [macro]: {
        ...macros[macro],
        [field]: parseInt(value) || 0,
      },
    });
  };

  const handleSave = () => {
    onSave(macros);
  };

  return (
    <Modal isOpen={isOpen} title="Edit Macros" onClose={onClose}>
      <div className="modal-body">
        {['protein', 'carbs', 'fat'].map((macro) => (
          <div key={macro}>
            <div className="macro-row">
              <label>{macro.charAt(0).toUpperCase() + macro.slice(1)}</label>
              <div className="macro-inputs">
                <input
                  type="number"
                  placeholder="Percentage"
                  value={macros[macro]?.pct || ''}
                  onChange={(e) => handleMacroChange(macro, 'pct', e.target.value)}
                />
                <input
                  type="number"
                  placeholder="Grams"
                  value={macros[macro]?.grams || ''}
                  onChange={(e) => handleMacroChange(macro, 'grams', e.target.value)}
                />
              </div>
            </div>
          </div>
        ))}
        <div className="modal-buttons">
          <button className="btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-save" onClick={handleSave}>
            Save
          </button>
        </div>
      </div>
    </Modal>
  );
};

const AddMealModal = ({ isOpen, onClose, onSave }) => {
  const [mealName, setMealName] = useState('');

  const handleSave = () => {
    if (mealName.trim()) {
      onSave(mealName);
      setMealName('');
    }
  };

  return (
    <Modal isOpen={isOpen} title="Add Meal" onClose={onClose}>
      <div className="modal-body">
        <div className="input-group">
          <label>Meal Name</label>
          <input
            type="text"
            value={mealName}
            onChange={(e) => setMealName(e.target.value)}
            placeholder="e.g., Snack"
          />
        </div>
        <div className="modal-buttons">
          <button className="btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-save" onClick={handleSave}>
            Save
          </button>
        </div>
      </div>
    </Modal>
  );
};

const AddFoodItemModal = ({ isOpen, onClose, onSave }) => {
  const [foodName, setFoodName] = useState('');
  const [calories, setCalories] = useState('');

  const handleSave = () => {
    if (foodName.trim()) {
      onSave({ name: foodName, calories: parseInt(calories) || 0 });
      setFoodName('');
      setCalories('');
    }
  };

  return (
    <Modal isOpen={isOpen} title="Add Food Item" onClose={onClose}>
      <div className="modal-body">
        <div className="input-group">
          <label>Food Name</label>
          <input
            type="text"
            value={foodName}
            onChange={(e) => setFoodName(e.target.value)}
            placeholder="e.g., Apple"
          />
        </div>
        <div className="input-group">
          <label>Calories</label>
          <input
            type="number"
            value={calories}
            onChange={(e) => setCalories(e.target.value)}
            placeholder="e.g., 95"
          />
        </div>
        <div className="modal-buttons">
          <button className="btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-save" onClick={handleSave}>
            Save
          </button>
        </div>
      </div>
    </Modal>
  );
};

const EditFoodItemModal = ({ isOpen, onClose, currentValues, onSave }) => {
  const [foodName, setFoodName] = useState(currentValues?.name || '');
  const [calories, setCalories] = useState(currentValues?.calories || '');

  const handleSave = () => {
    onSave({ name: foodName, calories: parseInt(calories) || 0 });
  };

  return (
    <Modal isOpen={isOpen} title="Edit Food Item" onClose={onClose}>
      <div className="modal-body">
        <div className="input-group">
          <label>Food Name</label>
          <input
            type="text"
            value={foodName}
            onChange={(e) => setFoodName(e.target.value)}
          />
        </div>
        <div className="input-group">
          <label>Calories</label>
          <input
            type="number"
            value={calories}
            onChange={(e) => setCalories(e.target.value)}
          />
        </div>
        <div className="modal-buttons">
          <button className="btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-save" onClick={handleSave}>
            Save
          </button>
        </div>
      </div>
    </Modal>
  );
};

const EditMealModal = ({ isOpen, onClose, currentValues, onSave }) => {
  const [mealName, setMealName] = useState(currentValues?.name || '');

  const handleSave = () => {
    onSave({ name: mealName });
  };

  return (
    <Modal isOpen={isOpen} title="Edit Meal" onClose={onClose}>
      <div className="modal-body">
        <div className="input-group">
          <label>Meal Name</label>
          <input
            type="text"
            value={mealName}
            onChange={(e) => setMealName(e.target.value)}
          />
        </div>
        <div className="modal-buttons">
          <button className="btn-cancel" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-save" onClick={handleSave}>
            Save
          </button>
        </div>
      </div>
    </Modal>
  );
};

// Tab Bar Component
const TabBar = ({ activeTab, tabs, onTabChange }) => {
  return (
    <div className="tab-bar-container">
      <div className="tab-bar">
        {tabs.map((tab) => (
          <button
            key={tab}
            className={`tab-button ${activeTab === tab ? 'active' : ''}`}
            onClick={() => onTabChange(tab)}
          >
            {tab}
          </button>
        ))}
      </div>
    </div>
  );
};

// Date Navigator Component
const DateNavigator = ({ selectedDate, onDateChange, onCalendarClick }) => {
  const dateStr = format(selectedDate, 'EEE, MMM d');

  return (
    <div className="date-navigator">
      <button className="date-nav-btn" onClick={() => onDateChange(subtractDays(selectedDate, 1))}>
        <ChevronLeft size={20} />
      </button>
      <span className="date-label">{dateStr}</span>
      <button className="date-nav-btn" onClick={() => onDateChange(addDays(selectedDate, 1))}>
        <ChevronRight size={20} />
      </button>
      <button className="calendar-btn" onClick={onCalendarClick}>
        <Calendar size={20} />
      </button>
    </div>
  );
};

// Calories Card Component
const CaloriesCard = ({ consumed, goal, onEdit }) => {
  const progress = Math.min(consumed / goal, 1);

  return (
    <div className="card calories-card" onClick={onEdit}>
      <label className="card-label">CALORIES — TODAY</label>
      <div className="calories-display">
        <span className="calories-value">
          {consumed} / {goal}
        </span>
        <span className="calories-unit">kcal</span>
      </div>
      <div className="progress-bar">
        <div className="progress-fill" style={{ width: `${progress * 100}%` }}></div>
      </div>
    </div>
  );
};

// Macros Card Component
const MacrosCard = ({ macros, onEdit }) => {
  const macrosList = [
    { key: 'protein', color: THEME.proteinColor },
    { key: 'carbs', color: THEME.carbColor },
    { key: 'fat', color: THEME.fatColor },
  ];

  return (
    <div className="card macros-card" onClick={onEdit}>
      <label className="card-label">MACROS</label>
      <div className="macros-grid">
        {macrosList.map(({ key, color }) => (
          <div key={key} className="macro-pill" style={{ borderColor: color }}>
            <div className="macro-percentage">{macros[key].pct}%</div>
            <div className="macro-name">{key.toUpperCase()}</div>
            <div className="macro-grams">{macros[key].grams}g</div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Food Item Component
const FoodItem = ({
  item,
  mealId,
  onToggle,
  onEdit,
  onDelete,
}) => {
  return (
    <div
      className={`food-item ${item.completed ? 'completed' : ''}`}
      onContextMenu={(e) => {
        e.preventDefault();
        onEdit();
      }}
    >
      <button
        className={`checkbox ${item.completed ? 'checked' : ''}`}
        onClick={() => onToggle()}
      >
        {item.completed && <Check size={14} />}
      </button>
      <span className="food-name">{item.name}</span>
      <span className="food-calories">{item.calories}</span>
      <button className="delete-btn" onClick={() => onDelete()}>
        <Trash2 size={16} />
      </button>
    </div>
  );
};

// Meal Card Component
const MealCard = ({
  meal,
  onEditMeal,
  onAddFood,
  onToggleFood,
  onEditFood,
  onDeleteFood,
}) => {
  const totalCalories = meal.items.reduce((sum, item) => sum + item.calories, 0);

  return (
    <div className="meal-card">
      <div className="meal-header">
        <span className="meal-name">{meal.name}</span>
        <span className="meal-calories">{totalCalories} kcal</span>
        <button className="meal-edit-btn" onClick={() => onEditMeal(meal)}>
          <Edit2 size={16} />
        </button>
      </div>
      <div className="food-items-list">
        {meal.items.map((item) => (
          <FoodItem
            key={item.id}
            item={item}
            mealId={meal.id}
            onToggle={() => onToggleFood(meal.id, item.id)}
            onEdit={() => onEditFood(meal.id, item)}
            onDelete={() => onDeleteFood(meal.id, item.id)}
          />
        ))}
      </div>
      <button className="add-food-btn" onClick={() => onAddFood(meal.id)}>
        <Plus size={16} />
        <span>Add food item</span>
      </button>
    </div>
  );
};

// Main NutritionScreen Component
const NutritionScreen = () => {
  const [state, dispatch] = useReducer(nutritionReducer, INITIAL_STATE);
  const [caloriesModalOpen, setCaloriesModalOpen] = useState(false);
  const [macrosModalOpen, setMacrosModalOpen] = useState(false);
  const [addMealModalOpen, setAddMealModalOpen] = useState(false);
  const [addFoodModalOpen, setAddFoodModalOpen] = useState(false);
  const [editFoodModalOpen, setEditFoodModalOpen] = useState(false);
  const [editMealModalOpen, setEditMealModalOpen] = useState(false);
  const [currentEditMealId, setCurrentEditMealId] = useState(null);
  const [currentEditFood, setCurrentEditFood] = useState(null);
  const [currentEditMeal, setCurrentEditMeal] = useState(null);
  const [currentAddMealId, setCurrentAddMealId] = useState(null);

  const tabs = ['Today', 'History', 'Search', 'Supplements'];

  const handleCaloriesSave = (values) => {
    dispatch({ type: 'UPDATE_CALORIES', payload: values });
    setCaloriesModalOpen(false);
  };

  const handleMacrosSave = (macros) => {
    dispatch({ type: 'UPDATE_MACROS', payload: macros });
    setMacrosModalOpen(false);
  };

  const handleAddMealSave = (name) => {
    dispatch({ type: 'ADD_MEAL', payload: name });
    setAddMealModalOpen(false);
  };

  const handleAddFoodSave = (food) => {
    if (currentAddMealId) {
      dispatch({
        type: 'ADD_FOOD_ITEM',
        payload: { mealId: currentAddMealId, ...food },
      });
      setAddFoodModalOpen(false);
      setCurrentAddMealId(null);
    }
  };

  const handleEditFoodSave = (food) => {
    if (currentEditFood) {
      dispatch({
        type: 'UPDATE_FOOD_ITEM',
        payload: {
          mealId: currentEditMealId,
          foodId: currentEditFood.id,
          ...food,
        },
      });
      setEditFoodModalOpen(false);
      setCurrentEditFood(null);
      setCurrentEditMealId(null);
    }
  };

  const handleEditMealSave = (data) => {
    if (currentEditMeal) {
      dispatch({
        type: 'UPDATE_MEAL',
        payload: { mealId: currentEditMeal.id, name: data.name },
      });
      setEditMealModalOpen(false);
      setCurrentEditMeal(null);
    }
  };

  const openAddFoodModal = (mealId) => {
    setCurrentAddMealId(mealId);
    setAddFoodModalOpen(true);
  };

  const openEditFoodModal = (mealId, food) => {
    setCurrentEditMealId(mealId);
    setCurrentEditFood(food);
    setEditFoodModalOpen(true);
  };

  const openEditMealModal = (meal) => {
    setCurrentEditMeal(meal);
    setEditMealModalOpen(true);
  };

  return (
    <div className="nutrition-screen" style={{ backgroundColor: THEME.background }}>
      {/* Header */}
      <div className="header">
        <h1>Nutrition</h1>
      </div>

      {/* Tab Bar */}
      <TabBar
        activeTab={state.activeTab}
        tabs={tabs}
        onTabChange={(tab) => dispatch({ type: 'SET_ACTIVE_TAB', payload: tab })}
      />

      {/* Main Content */}
      {state.activeTab === 'Today' && (
        <div className="content-container">
          {/* Date Navigator */}
          <DateNavigator
            selectedDate={state.selectedDate}
            onDateChange={(date) => dispatch({ type: 'SET_DATE', payload: date })}
            onCalendarClick={() => console.log('Calendar clicked')}
          />

          {/* Calories Card */}
          <CaloriesCard
            consumed={state.caloriesConsumed}
            goal={state.calorieGoal}
            onEdit={() => setCaloriesModalOpen(true)}
          />

          {/* Macros Card */}
          <MacrosCard
            macros={state.macros}
            onEdit={() => setMacrosModalOpen(true)}
          />

          {/* Today's Meals Section */}
          <div className="meals-section">
            <div className="section-header">
              <label className="section-label">TODAY'S MEALS</label>
              <button
                className="add-meal-btn"
                onClick={() => setAddMealModalOpen(true)}
              >
                <Plus size={20} />
              </button>
            </div>

            <div className="meals-list">
              {state.meals.map((meal) => (
                <MealCard
                  key={meal.id}
                  meal={meal}
                  onEditMeal={(m) => openEditMealModal(m)}
                  onAddFood={(mealId) => openAddFoodModal(mealId)}
                  onToggleFood={(mealId, foodId) =>
                    dispatch({
                      type: 'TOGGLE_FOOD_ITEM',
                      payload: { mealId, foodId },
                    })
                  }
                  onEditFood={(mealId, food) => openEditFoodModal(mealId, food)}
                  onDeleteFood={(mealId, foodId) =>
                    dispatch({
                      type: 'DELETE_FOOD_ITEM',
                      payload: { mealId, foodId },
                    })
                  }
                />
              ))}
            </div>

            {/* Log a Meal Button */}
            <button
              className="log-meal-btn"
              onClick={() => setAddMealModalOpen(true)}
            >
              <Plus size={20} />
              <span>Log a meal / supplement</span>
            </button>
          </div>
        </div>
      )}

      {/* Other Tabs Placeholder */}
      {state.activeTab !== 'Today' && (
        <div className="content-container">
          <div className="placeholder">
            <p>{state.activeTab} section coming soon</p>
          </div>
        </div>
      )}

      {/* Modals */}
      <CaloriesEditModal
        isOpen={caloriesModalOpen}
        onClose={() => setCaloriesModalOpen(false)}
        currentValues={{ consumed: state.caloriesConsumed, goal: state.calorieGoal }}
        onSave={handleCaloriesSave}
      />

      <MacrosEditModal
        isOpen={macrosModalOpen}
        onClose={() => setMacrosModalOpen(false)}
        currentValues={state.macros}
        onSave={handleMacrosSave}
      />

      <AddMealModal
        isOpen={addMealModalOpen}
        onClose={() => setAddMealModalOpen(false)}
        onSave={handleAddMealSave}
      />

      <AddFoodItemModal
        isOpen={addFoodModalOpen}
        onClose={() => setAddFoodModalOpen(false)}
        onSave={handleAddFoodSave}
      />

      <EditFoodItemModal
        isOpen={editFoodModalOpen}
        onClose={() => setEditFoodModalOpen(false)}
        currentValues={currentEditFood}
        onSave={handleEditFoodSave}
      />

      <EditMealModal
        isOpen={editMealModalOpen}
        onClose={() => setEditMealModalOpen(false)}
        currentValues={currentEditMeal}
        onSave={handleEditMealSave}
      />

      {/* Bottom Navigation */}
      <div className="bottom-nav">
        <button className="nav-item">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
            <polyline points="9 22 9 12 15 12 15 22"></polyline>
          </svg>
          <span>Home</span>
        </button>
        <button className="nav-item">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
            <polyline points="17 6 23 6 23 12"></polyline>
          </svg>
          <span>Train</span>
        </button>
        <button className="nav-item active">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="1"></circle>
            <path d="M12 1v6m0 6v6M4.22 4.22l4.24 4.24m2.12 2.12l4.24 4.24M1 12h6m6 0h6M4.22 19.78l4.24-4.24m2.12-2.12l4.24-4.24M19.78 19.78l-4.24-4.24m-2.12-2.12l-4.24-4.24"></path>
          </svg>
          <span>Nutrition</span>
        </button>
        <button className="nav-item">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2c5.523 0 10 4.477 10 10s-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2z"></path>
            <path d="M12 6v6l4 2"></path>
          </svg>
          <span>AI</span>
        </button>
        <button className="nav-item">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
            <circle cx="9" cy="7" r="4"></circle>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
          </svg>
          <span>Social</span>
        </button>
      </div>
    </div>
  );
};

export default NutritionScreen;
