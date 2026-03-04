import random
import json

# CONFIGURATION
SEED = 42
NUM_USERS = 100

# Matches the Enums in models.py
GENDERS = ["male", "female"]
GOALS = ["lose weight", "maintain", "gain muscle"]
ACTIVITY_LEVELS = [
    "sedentary", 
    "lightly active", 
    "moderately active", 
    "very active", 
    "extra active"
]
# Matching string values  with models.py
MACRO_STYLES = ["balanced", "low_carb", "keto", "high_protein", "vegan", "vegetarian", "diabetic_friendly", "heart_healthy"]

ALLERGENS_POOL = ["nuts", "dairy", "gluten", "shellfish", "eggs", "soy", "fish"]
CRAVINGS_POOL = ["broccoli", "chicken", "lamb", "tomato", "rice", "smoothie", "soup", "tofu", "cottage cheese", "beans"]
MEDICAL_TEXTS = ["I have diabetes", "I am lactose intolerant", "I have celiac disease", "No nuts please", "I want to avoid gluten"]

# Matching Intensity Enum in models.py
EXERCISE_POOL = {
    "low",
    "moderate",
    "high",
    "very_high"
}

def generate_synthetic_users():
    random.seed(SEED)
    profiles = []

    for i in range(NUM_USERS):
        gender = random.choice(GENDERS)
        age = random.randint(18, 65)
        
        if gender == "male":
            height = random.randint(165, 195)
        else:
            height = random.randint(150, 180)

        # Generate scientifically valid weight based on BMI
        target_bmi = random.uniform(16.0, 35.0) 
        # Using BMI formula: weight (kg) = BMI * (height (m))^2
        weight = round(target_bmi * ((height / 100) ** 2), 1)

        activity_level = random.choice(ACTIVITY_LEVELS)
        
        # Generate Activities
        num_activities = random.choices([0, 1, 2, 3], weights=[30, 40, 20, 10])[0]
        user_activities = []
        for _ in range(num_activities):
            intensity_key = random.choice(list(EXERCISE_POOL))
            hours = random.randint(1, 6)
            
            # Structure matches UserActivity logic, 
            # though your model only strictly needs 'hours' and 'intensity'
            user_activities.append({
                "intensity": intensity_key, 
                "hours": float(hours),
            })

        # Goal Logic
        # Simulatimg real user behavior: those with very high BMI likely want to lose weight, those with very low BMI want to gain muscle.
        if target_bmi > 30:
            goal = "lose weight"
        elif target_bmi < 18.5:
            goal = "gain muscle"
        else:
            goal = random.choice(GOALS)

        # Diet/Allergies
        if random.random() < 0.3:
            style = random.choice(MACRO_STYLES)
        else:
            style = "balanced"

        allergies = []
        if random.random() < 0.20:
            allergies.append(random.choice(ALLERGENS_POOL))

        # Text Input
        text_input = ""
        dice = random.random()
        if dice < 0.20: 
            craving = random.choice(CRAVINGS_POOL)
            text_input = f"I really want {craving} for lunch."
        elif dice < 0.35:
            text_input = random.choice(MEDICAL_TEXTS)
        elif dice < 0.50:
            text_input = f"I want to {goal} fast."
        
        user_profile = {
            "id": i + 1,
            "age": age,
            "gender": gender,
            "weight": weight,
            "height": float(height),
            "daily_activity": activity_level, # Matches Pydantic field name
            "activities": user_activities,
            "goal": goal,
            "allergies": allergies,
            "macro_style": style, # Note: Not in UserProfile, used by Intent logic simulation
            "text_input": text_input,
            "meal_amount": 4
        }
        
        profiles.append(user_profile)

    return profiles

if __name__ == "__main__":
    users = generate_synthetic_users()
    with open("test_users.json", "w") as f:
        json.dump(users, f, indent=2)