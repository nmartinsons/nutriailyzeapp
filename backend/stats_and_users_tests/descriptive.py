import json
import statistics
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
GENERATED_JSON = BASE_DIR / 'generated_plans.json'
FAILURES_JSON = BASE_DIR / 'failed_profiles.json'

CRAVINGS_POOL = [
    "I really want broccoli", "I really want chicken", "I really want lamb", "I really want tomato", "I really want rice",
    "I really want smoothie", "I really want soup", "I really want tofu", "I really want cottage cheese", "I really want beans"
]

MEDICAL_TEXTS = [
    "I have diabetes", "I am lactose intolerant", "I have celiac disease",
    "I have high cholesterol", "I have hypertension"
]

DIET_TEXTS = [
    "I want to follow a low_carb diet.",
    "I want to follow a keto diet.",
    "I want to follow a vegan diet.",
    "I want to follow a vegetarian diet.",
    "I want to follow a diabetic_friendly diet.",
    "I want to follow a heart_healthy diet.",
    "I want to follow a high_protein diet.",
]

# Load your generated users/plans
with open(GENERATED_JSON, 'r') as f:
    data = json.load(f)

# Extract lists of values
ages = [user['age'] for user in data]
weights = [user['weight'] for user in data]
heights = [user['height'] for user in data]
calories = [user['daily_targets']['calories'] for user in data]
protein = [user['daily_targets']['protein'] for user in data]
carbs = [user['daily_targets']['carbs'] for user in data]
fat = [user['daily_targets']['fat'] for user in data]

def print_stats(name, values):
    mean_val = statistics.mean(values)
    stdev_val = statistics.stdev(values) if len(values) > 1 else 0
    min_val = min(values)
    max_val = max(values)
    print(f"{name:<15} | Mean: {mean_val:>6.2f} | SD: {stdev_val:>6.2f} | Range: {min_val:.2f} - {max_val:.2f}")

print("--- SYNTHETIC USER DEMOGRAPHICS ---")
print_stats("Age", ages)
print_stats("Weight (kg)", weights)
print_stats("Height (cm)", heights)
print_stats("Target kcal", calories)
print_stats("Target Protein (g)", protein)
print_stats("Target Carbs (g)", carbs)
print_stats("Target Fats (g)", fat)

# For categorical data (e.g., genders)
genders = [user['gender'] for user in data]
print(f"Male: {genders.count('male')} | Female: {genders.count('female')}")
daily_activities = [user['daily_activity'] for user in data]
print(f"Sedentary: {daily_activities.count('sedentary')} | Lightly Active: {daily_activities.count('lightly active')} | Moderately Active: {daily_activities.count('moderately active')} | Very Active: {daily_activities.count('very active')} | Extra Active: {daily_activities.count('extra active')}")
goals = [user['goal'] for user in data]
print(f"Lose Weight: {goals.count('lose weight')} | Maintain: {goals.count('maintain')} | Gain Muscle: {goals.count('gain muscle')}")
allergies = [allergy for user in data for allergy in user['allergies']]
print(f"Allergies - Nuts: {allergies.count('nuts')} | Milk: {allergies.count('milk')} | Gluten: {allergies.count('gluten')} | Shellfish: {allergies.count('shellfish')} | Eggs: {allergies.count('eggs')} | Soy: {allergies.count('soy')} | Fish: {allergies.count('fish')}")

# Text-input subset stats for cravings and medical-condition prompts
text_inputs = [(user.get('text_input') or '').lower() for user in data]
cravings_counts = {
    craving: sum(1 for txt in text_inputs if craving.lower() in txt)
    for craving in CRAVINGS_POOL
}
medical_counts = {
    phrase: sum(1 for txt in text_inputs if phrase.lower() in txt)
    for phrase in MEDICAL_TEXTS
}
diet_counts = {
    phrase: sum(1 for txt in text_inputs if phrase.lower() in txt)
    for phrase in DIET_TEXTS
}

profiles_with_any_craving = sum(
    1 for txt in text_inputs
    if any(craving.lower() in txt for craving in CRAVINGS_POOL)
)
profiles_with_any_medical = sum(
    1 for txt in text_inputs
    if any(phrase.lower() in txt for phrase in MEDICAL_TEXTS)
)
profiles_with_any_diet_text = sum(
    1 for txt in text_inputs
    if any(phrase.lower() in txt for phrase in DIET_TEXTS)
)

print("\n--- Text Input Profile Distribution ---")
print(f"Profiles with any CRAVINGS_POOL phrase: {profiles_with_any_craving} out of {len(data)}")
for craving, cnt in cravings_counts.items():
    print(f"  - craving '{craving}': {cnt}")

print(f"Profiles with any MEDICAL_TEXTS phrase: {profiles_with_any_medical} out of {len(data)}")
for phrase, cnt in medical_counts.items():
    print(f"  - medical '{phrase}': {cnt}")

print(f"Profiles with any DIET_TEXTS phrase: {profiles_with_any_diet_text} out of {len(data)}")
for phrase, cnt in diet_counts.items():
    print(f"  - diet text '{phrase}': {cnt}")


print("\n=== GENERATED MEAL PLAN CHARACTERISTICS ===")

actual_calories =[]
actual_proteins = []
actual_carbs = []
actual_fats =[]
meal_counts =[]

# Counters for totals and categories
total_users = len(data)
total_meals_generated = 0
meal_categories_count = {} 
meal_structure_count = {
    'composite_meal': 0,
    'single_food': 0,
    'unknown': 0,
}
meal_component_count = {
    'main_dish': 0,
    'side_dish': 0,
    'soup': 0,
    'drink': 0,
    'boosters': 0,
}

for user in data:
    meals = user.get('meals', user.get('generated_meals', []))
        
    meal_counts.append(len(meals))
    total_meals_generated += len(meals)
    
    user_p = 0
    user_c = 0
    user_f = 0
    
    for meal in meals:
        # Track Meal Categories (Breakfast, Lunch, Snacks, etc.)
        # Generator saves this as 'slot_name'
        cat_name = meal.get('slot_name') or meal.get('meal_name') or 'Unknown'
        meal_categories_count[cat_name] = meal_categories_count.get(cat_name, 0) + 1

        # Track meal structure/type (main meal vs snack-style meal)
        food_data = meal.get('food_data', {}) if isinstance(meal, dict) else {}
        meal_type = food_data.get('type', 'unknown')
        if meal_type not in meal_structure_count:
            meal_type = 'unknown'
        meal_structure_count[meal_type] += 1

        # Track components present in generated meals
        if isinstance(food_data, dict):
            for comp in ['main_dish', 'side_dish', 'soup', 'drink']:
                if food_data.get(comp):
                    meal_component_count[comp] += 1
            if isinstance(food_data.get('boosters'), list) and len(food_data['boosters']) > 0:
                meal_component_count['boosters'] += 1
        
        # Calculate macros
        if 'food_data' in meal and 'total_macros' in meal['food_data']:
            macros = meal['food_data']['total_macros']
            user_p += macros.get('protein', 0)
            user_c += macros.get('carbs', 0)
            user_f += macros.get('fat', 0)
        
    # Calculate Calories (Atwater factors)
    user_cal = (user_p * 4) + (user_c * 4) + (user_f * 9)
    
    actual_proteins.append(user_p)
    actual_carbs.append(user_c)
    actual_fats.append(user_f)
    actual_calories.append(user_cal)


# Print Structural Summary
print("\n--- Structural Overview ---")
print(f"Sample Size (N)             : {total_users} synthetic profiles")
print(f"Total Meals Generated       : {total_meals_generated} individual meals")

avg_meals = statistics.mean(meal_counts)
min_meals = min(meal_counts)
max_meals = max(meal_counts)
sd_meals = statistics.stdev(meal_counts) if len(meal_counts) > 1 else 0

print(f"Average Meals per User: {avg_meals:.2f} (Range: {min_meals} - {max_meals}) (SD:{sd_meals:.2f})")

print("\n--- Meal Categories (Slot Names) Distribution ---")
# Sort categories from most common to least common
for cat, count in sorted(meal_categories_count.items(), key=lambda x: x[1], reverse=True):
    # Calculate what percentage of users got this meal
    percent_of_users = (count / total_users) * 100
    print(f"  - {cat:<15}: {count} total generated (present in {percent_of_users:.1f}% of daily plans)")

print("\n--- Meal Structure Distribution ---")
for structure_name, count in meal_structure_count.items():
    pct_meals = (count / total_meals_generated * 100) if total_meals_generated > 0 else 0
    print(f"  - {structure_name:<15}: {count} meals ({pct_meals:.1f}% of all generated meals)")

print("\n--- Meal Components Presence ---")
for comp_name, count in meal_component_count.items():
    pct_meals = (count / total_meals_generated * 100) if total_meals_generated > 0 else 0
    print(f"  - {comp_name:<15}: present in {count} meals ({pct_meals:.1f}% of all generated meals)")


print("\n--- Nutritional Output Stats ---")
print_stats("Actual Kcal", actual_calories)
print_stats("Actual Protein", actual_proteins)
print_stats("Actual Carbs", actual_carbs)
print_stats("Actual Fat", actual_fats)

# Allergy / Constraint Prevalence
users_with_allergies = sum(1 for user in data if user.get('allergies'))
print(f"\nPlans with Allergens: {users_with_allergies} out of {total_users} profiles")

# Allergy-user subset details and exact subgroup distributions
allergy_profiles = [
    user for user in data
    if isinstance(user.get('allergies'), list) and len(user.get('allergies')) > 0
]

if allergy_profiles:
    allergy_genders = [u.get('gender', 'Unknown') for u in allergy_profiles]
    allergy_daily_activities = [u.get('daily_activity', 'Unknown') for u in allergy_profiles]
    allergy_goals = [u.get('goal', 'Unknown') for u in allergy_profiles]
    allergy_styles = [u.get('macro_style', None) for u in allergy_profiles]

    print("\n--- Allergy Users: Categorical Breakdown ---")
    print(f"Gender -> Male: {allergy_genders.count('male')} | Female: {allergy_genders.count('female')}")
    print(
        "Daily Activity -> "
        f"Sedentary: {allergy_daily_activities.count('sedentary')} | "
        f"Lightly Active: {allergy_daily_activities.count('lightly active')} | "
        f"Moderately Active: {allergy_daily_activities.count('moderately active')} | "
        f"Very Active: {allergy_daily_activities.count('very active')} | "
        f"Extra Active: {allergy_daily_activities.count('extra active')}"
    )
    print(
        "Goal -> "
        f"Lose Weight: {allergy_goals.count('lose weight')} | "
        f"Maintain: {allergy_goals.count('maintain')} | "
        f"Gain Muscle: {allergy_goals.count('gain muscle')}"
    )

if FAILURES_JSON.exists():
    with open(FAILURES_JSON, 'r') as f:
        failed = json.load(f)
    print(f"Failed Profiles Logged: {len(failed)} (see {FAILURES_JSON.name})")
