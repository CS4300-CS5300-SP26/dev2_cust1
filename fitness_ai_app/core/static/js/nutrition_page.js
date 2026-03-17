document.addEventListener('DOMContentLoaded', function() {
    // Calculate total calories
    updateCalories();
});

function updateCalories() {
    let totalCalories = 0;
    const foodItems = document.querySelectorAll('.food-calories');
    foodItems.forEach(item => {
        totalCalories += parseInt(item.textContent) || 0;
    });
    
    const consumedElement = document.getElementById('totalCalories');
    if (consumedElement) {
        consumedElement.textContent = totalCalories;
        // Update progress bar (assuming 2400 kcal as target)
        const percentage = Math.min((totalCalories / 2400) * 100, 100);
        const progressFill = document.getElementById('progressFill');
        if (progressFill) {
            progressFill.style.width = percentage + '%';
        }
    }
    
    // Update meal totals
    const mealCalTotals = document.querySelectorAll('.meal-cal-total');
    mealCalTotals.forEach(total => {
        const mealId = total.dataset.mealId;
        let mealTotal = 0;
        // Find all food items for this meal
        const mealCard = total.closest('.meal-card');
        if (mealCard) {
            const items = mealCard.querySelectorAll('.food-calories');
            items.forEach(item => {
                mealTotal += parseInt(item.textContent) || 0;
            });
            total.textContent = mealTotal + ' kcal';
        }
    });
}
