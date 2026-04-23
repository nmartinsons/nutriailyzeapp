import random
import json
# IMPORT YOUR REAL LOGIC
from rules_engine import calc_tdee, calc_bmr
# You need a dummy class to pass data to the rules engine
class DummyUser:
    def __init__(self, age, weight, height, gender, daily_activity, activities):
        self.age = age
        self.weight = weight
        self.height = height
        self.gender = gender
        self.daily_activity = daily_activity
        self.activities = activities
        self.goal = "maintain" # Goal doesn't affect TDEE calculation, only adjustment

# CONFIGURATION
SEED = 2026
NUM_USERS = 100

GENDERS = ["male", "female"]
GOALS = ["lose weight", "maintain", "gain muscle"]
ACTIVITY_LEVELS = ["sedentary", "lightly active", "moderately active", "very active", "extra active"]
MACRO_STYLES = ["low_carb", "keto", "high_protein", "vegan", "vegetarian", "diabetic_friendly", "heart_healthy"]
ALLERGENS_POOL = ["nuts", "milk", "gluten", "shellfish", "eggs", "soy", "fish"]
CRAVINGS_POOL = ["broccoli", "chicken", "lamb", "tomato", "rice", "smoothie", "soup", "tofu", "cottage cheese", "beans"]
MEDICAL_TEXTS = ["I have diabetes", "I am lactose intolerant", "I have celiac disease", "I have high cholesterol", "I have hypertension"]
EXERCISE_POOL = {"low", "moderate", "high", "very_high"}

class DummyActivity:
    def __init__(self, intensity, hours):
        self.intensity = intensity
        self.hours = hours

def generate_synthetic_users():
    random.seed(SEED)
    profiles = []

    for i in range(NUM_USERS):
        # 1. BIOMETRICS
        gender = random.choice(GENDERS)
        age = random.randint(18, 65)
        if gender == "male":
            height = random.randint(165, 205)
        else:
            height = random.randint(150, 185)

        target_bmi = random.uniform(16.0, 35.0) 
        weight = round(target_bmi * ((height / 100) ** 2), 1)
        activity_level = random.choice(ACTIVITY_LEVELS)

        # 2. ACTIVITIES
        num_activities = random.choices([0, 1, 2, 3], weights=[30, 40, 20, 10])[0]
        user_activities_dicts = [] # For JSON output
        dummy_activities = []      # For Rules Engine calculation

        for _ in range(num_activities):
            intensity_key = random.choice(list(EXERCISE_POOL))
            hours = random.randint(1, 6)
            
            # Create Dict for JSON
            user_activities_dicts.append({
                "intensity": intensity_key, 
                "hours": float(hours),
            })
            # Create Object for Rules Engine
            dummy_activities.append(DummyActivity(intensity_key, float(hours)))

        # 3. CALCULATE REAL TDEE
        # Create a temporary user object just to run the math
        temp_user = DummyUser(age, weight, height, gender, activity_level, dummy_activities)
        
        # Calculate precise TDEE using your actual app logic
        real_tdee = calc_tdee(temp_user)
        
        # Determine Meal Count based on REAL Caloric Load
        if real_tdee > 3500:
            meal_amount = random.choice([5, 6])
        elif real_tdee > 2600:
            meal_amount = random.choice([4, 5, 6])
        elif real_tdee < 1700:
            meal_amount = random.choice([3, 4])
        else:
            meal_amount = random.randint(3, 5)

        # 4. GOAL LOGIC
        if target_bmi > 30: 
            goal = "lose weight"
        elif target_bmi < 18.5: 
            goal = "gain muscle"
        else: 
            goal = random.choice(GOALS)

        # 5. DIET STYLE & ALLERGIES
        if random.random() < 0.3: 
            style = random.choice(MACRO_STYLES)
        else: 
            style = "balanced"

        allergies = []
        if random.random() < 0.40:
            allergies.append(random.choice(ALLERGENS_POOL))

        # 6. TEXT INPUT
        text_input = ""
        dice = random.random()
        if dice < 0.30: 
            craving = random.choice(CRAVINGS_POOL)
            text_input = f"I really want {craving}."
            style = "balanced"
        elif dice < 0.50:
            med_text = random.choice(MEDICAL_TEXTS)
            text_input = med_text
            if "diabetes" in med_text: 
                style = "diabetic_friendly"
            elif "cholesterol" in med_text or "hypertension" in med_text: 
                style = "heart_healthy"
            else: style = "balanced"
        elif dice < 0.80: 
            selected_style = random.choice(MACRO_STYLES)
            style = selected_style
            text_input = f"I want to follow a {selected_style} diet."
        else:
            text_input = ""
            style = "balanced"

        # 7. CONSTRUCT FINAL OBJECT
        user_profile = {
            "id": i + 1,
            "age": age,
            "gender": gender,
            "weight": weight,
            "height": float(height),
            "daily_activity": activity_level, 
            "activities": user_activities_dicts, 
            "goal": goal,
            "allergies": allergies,
            "macro_style": style,
            "text_input": text_input,
            "meal_amount": meal_amount 
        }
        
        profiles.append(user_profile)

    return profiles

if __name__ == "__main__":
    users = generate_synthetic_users()
    with open("test_users.json", "w") as f:
        json.dump(users, f, indent=2)
    
    print(f"Generated {len(users)} users.")