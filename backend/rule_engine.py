import numpy as np
import pandas as pd

from models import UserProfile as up

# Calculating Body Mass Index (BMI)
# For determining weight category
def calc_bmi(user: up):
    height_m = user.height / 100
    bmi = user.weight / (height_m)**2
    return bmi

# Calculating Basal Metabolic Rate (BMR) using Mifflin-St Jeor (MSJ) equation
# Energy expenditure at complete rest
def calc_bmr(user: up):
    height_cm = user.height # Height in cm
    if user.gender == "male":
        bmr = 10 * user.weight + 6.25 * height_cm - 5 * user.age + 5
    else:
        bmr = 10 * user.weight + 6.25 * height_cm - 5 * user.age - 161
    return bmr

# Calculating Total Daily Energy Expenditure (TDEE) dynamically based on
# Biometrics (BMR) and Lifestyle Composite Score (Occupation + Dual-Activity METs)
def calc_tdee(user: up):
    """
    Calculates TDEE by combining:
    1. Basal Metabolic Rate (Mifflin-St Jeor)
    2. Non-Exercise Activity Thermogenesis (NEAT) from Occupation
    3. Exercise Activity Thermogenesis (EAT) from Primary & Secondary Workouts (METs)
    """
    activity_multipliers = {
        "sedentary": 1.2,
        "lightly active": 1.375,
        "moderately active": 1.55,
        "very active": 1.725,
        "extra_active": 1.9
    }
    
    base_pal = activity_multipliers.get(user.daily_activity.lower(), 1.2)
   
    # Calculating increase in PAL based on Metabolic Equivalent of Task (MET) values
    met_map = {
        "none": 0,     # User selected nothing
        "low": 3,      # Walking, yoga
        "moderate": 5, # Jogging, light lifting
        "high": 8,     # HIIT, Running
        "very_high": 11 # Sprinting, competitive sports
    }

    # Metabolic Equivalent of Task (MET) method
    # Exercise Energy Expenditure (EEE) calculation
    # Loop through every activity the user sent
    total_weekly_eee = 0.0
    for act in user.activities:
        # Get MET (default to 0 if invalid string)
        met_val = met_map.get(act.intensity.lower(), 0.0)
        
        # Calculate burn for this specific activity
        burn = met_val * act.hours * user.weight
        
        # Add to total
        total_weekly_eee += burn
    # Calculte daily EEE
    daily_eee = total_weekly_eee / 7.0
    
    pal_increase = daily_eee / calc_bmr(user)
    raw_pal = base_pal + pal_increase
    # Calculate total TDEE
    final_pal = min(raw_pal, 2.2)  # Cap PAL at 2.2 to avoid overestimation
    tdee = calc_bmr(user) * final_pal
    return tdee

# Determine weight category based on BMI to adjust meal plans
def determine_weight_cat(bmi: float):
    if bmi < 18.5:
        return "underweight"
    elif bmi < 25.0:  # Covers everything from 18.5 up to 24.999...
        return "normal weight"
    elif bmi < 30.0:  # Covers everything from 25.0 up to 29.999...
        return "overweight"
    else:
        return "obese"
    
portion_multiplier = {
    "underweight": 1.15,   # +15% Surplus to gain weight
    "normal weight": 1.00, # Maintenance
    "overweight": 0.90,    # -10% Deficit (Sustainable loss)
    "obese": 0.80          # -20% Deficit (More aggressive)
}

def adjust_caloric_intake(tdee: float, weight_cat: str, bmr: float) -> int:
    """
    Adjusts the TDEE based on weight goal (Gain/Maintain/Lose).
    Includes a SAFETY CHECK to ensure calories never drop below BMR.
    """
    # 1. Get the multiplier (Default to 1.0 if category error)
    multiplier = portion_multiplier.get(weight_cat, 1.0)
    
    # 2. Calculate the target
    adjusted_calories = tdee * multiplier
    
    # 3. SAFETY CHECK: The "Starvation" Floor
    # Example: A short obese woman might have TDEE 1500.
    # 1500 * 0.80 = 1200. If her BMR is 1300, 1200 is too low.
    # We force the minimum to be the BMR.
    if adjusted_calories < bmr:
        adjusted_calories = bmr
    # Return integer for clean UI
    return int(adjusted_calories)

def distrib_of_cal_for_meals(total_calories: int, meal_count: int, weight_category: str):
    # 1. Get the Dynamic Macro Split
    p_ratio, c_ratio, f_ratio = get_macro_split(weight_category)

    # 2. Meal Timing Ratios
    time_ratios = {
        2: [
            ("Breakfast/Lunch", 0.55),
            ("Dinner", 0.45)
        ],
        3: [
            ("Breakfast", 0.45),
            ("Lunch", 0.30), 
            ("Dinner", 0.25)
        ],
        4: [
            ("Breakfast", 0.40),
            ("Lunch", 0.30),
            ("Snack", 0.10),
            ("Dinner", 0.20)
        ],
        5: [
            ("Breakfast", 0.35),
            ("Morning Snack", 0.10),
            ("Lunch", 0.25),
            ("Afternoon Snack", 0.10),
            ("Dinner", 0.20)
        ],
         6: [
            ("Breakfast", 0.25),
            ("Morning Snack", 0.10),
            ("Lunch", 0.25),
            ("Afternoon Snack", 0.10),
            ("Dinner", 0.20),
            ("Late Snack", 0.10)
        ]
    }

    # 3. Get the specific plan (Default is 3 meals)
    selected_plan = time_ratios.get(meal_count, time_ratios[3])

    # 4. Calculate Calories and Macros per meal
    meal_plan = []
    
    for meal_name, cal_percentage in selected_plan:
        calories = int(total_calories * cal_percentage)
        
        meal_plan.append({
            "meal_name": meal_name,
            "calories": calories,
            "target_macros": {
                # P/C = 4 kcal/g, F = 9 kcal/g
                "protein": int((calories * p_ratio) / 4),
                "carbs":   int((calories * c_ratio) / 4),
                "fat":     int((calories * f_ratio) / 9)
            }
        })

    return meal_plan

# Emphasizes must be placed on the quality over rigid percentages.
def get_macro_split(weight_category: str):
    if weight_category in ["overweight", "obese"]:
        # Metabolic reset / insulin resistance focus
        # Lower carb, moderate protein, higher healthy fat
        # Split: 40% Protein, 25% Carbs, 35% Fat
        # Emphasizing protein since it boosts metabolism, makes person feel fuller, preserves muscle mass, and increase calorie burn
        # Higher healthy fat amount replaces carbs.
        # Higher healthy fat increase satiety, stabilize blood sugar to prevent fat storage, boost metabolism, and provide essential 
        # building blocks for cells and hormones, helping reverse fat-storing cycles caused by sugar/carb-heavy diets, all leading to 
        # reduced hunger, cravings, and ultimately, becoming lean
        # When sugars and carbs are reduced and healthy fats increased, body shifts from storing fat to burning it for energy. 
        return (0.40, 0.25, 0.35)
        
    elif weight_category == "underweight":
        # Weight gain focus using whole-food carbs and fats
        # Split: 25% Protein, 40% Carbs, 35% Fat
        return (0.25, 0.40, 0.35)
       
    else: # Normal Weight
        # Maintenance
        # Split: 30% Protein, 35% Carbs, 35% Fat
        return (0.30, 0.35, 0.35)
    
    # Based on the text input macro ratios will be overwritten; however, the general rules still must work.
    # NLP should extract specific foods and preferences; however, it should ensure that it is allowed.
    # NLP should extract health goals; for instance, user is athlete and he wants to gain more muscle mass and needs more calories.
    # More protein for older people (age 60+) to combat sarcopenia -  muscle loss.