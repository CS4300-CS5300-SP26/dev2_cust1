document.addEventListener('DOMContentLoaded', function() {
    // Set date input to current selected date
    const dateInput = document.getElementById('dateInput');
    if (dateInput) {
        dateInput.value = dateInput.dataset.dateString || '';
    }
    
    // Initialize flatpickr if available
    if (typeof flatpickr !== 'undefined') {
        flatpickr('#dateInput', {
            mode: 'single',
            dateFormat: 'Y-m-d',
            onChange: function(selectedDates) {
                if (selectedDates.length > 0) {
                    const date = selectedDates[0];
                    const year = date.getFullYear();
                    const month = String(date.getMonth() + 1).padStart(2, '0');
                    const day = String(date.getDate()).padStart(2, '0');
                    window.location.href = `/nutrition/?date=${year}-${month}-${day}`;
                }
            }
        });
    }
    
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
