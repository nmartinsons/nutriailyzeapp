from models import UserProfile, Intensity, ActivityLevel


lose_keywords = ['lose', 'lose weight', 'cut', 'diet', 'fat loss', 
                    'weight loss', 'shred', 'deficit', 'cutting', 
                    'fat reduction', 'slim down', 'fat burn', 'fat burning',
                    'get lean', 'fat loss program', 'weight reduction', 
                    'drop weight', 'slimming', 'trim down', 'lean out']
gain_keywords = ['gain', 'gain muscle', 'bulk', 'muscle gain', 
                      'muscle building', 'mass gain', 'bulking', 'build muscle', 
                      'increase muscle', 'muscle growth', 'put on muscle', 
                      'add muscle', 'muscle increase', 'muscle development',
                      'grow muscle', 'muscle enhancement', 'build mass',
                      'increase mass', 'mass building', 'muscle hypertrophy',
                      'lean bulk', 'clean bulk']
# Calculating Body Mass Index (BMI)
# For determining weight category
def calc_bmi(user: UserProfile):
    if user.height <= 0:
        return 0.0
    height_m = user.height / 100
    bmi = user.weight / (height_m)**2
    return bmi

# Calculating Basal Metabolic Rate (BMR) using Mifflin-St Jeor (MSJ) equation
# Energy expenditure at complete rest
def calc_bmr(user: UserProfile):
    if user.gender.lower() == "male":
        bmr = (10 * user.weight) + (6.25 * user.height) - (5 * user.age) + 5
    else:
        bmr = (10 * user.weight) + (6.25 * user.height) - (5 * user.age) - 161
    return bmr

# Calculating Total Daily Energy Expenditure (TDEE) dynamically based on
# Biometrics (BMR) and Lifestyle Composite Score (Occupation + Dual-Activity METs)
def calc_tdee(user: UserProfile):
    """
    Calculates TDEE by combining:
    1. Basal Metabolic Rate (Mifflin-St Jeor)
    2. Non-Exercise Activity Thermogenesis (NEAT) from Occupation
    3. Exercise Activity Thermogenesis (EAT) from Primary & Secondary Workouts (METs)
    """
    PAL_VALUES = {
        ActivityLevel.SEDENTARY: 1.2,
        ActivityLevel.LIGHT: 1.375,
        ActivityLevel.MODERATE: 1.55,
        ActivityLevel.VERY: 1.725,
        ActivityLevel.EXTRA: 1.9
    }
   
    # Calculating increase in PAL based on Metabolic Equivalent of Task (MET) values
    MET_VALUES = {
        Intensity.NONE: 0,
        Intensity.LOW: 3,      # Walking, yoga
        Intensity.MODERATE: 5, # Jogging, light lifting
        Intensity.HIGH: 8,     # HIIT, Running
        Intensity.VERY_HIGH: 11 # Sprinting, competitive sports
    }
    # Calculate Basal Metabolic Rate
    bmr = calc_bmr(user)
    
    # Get Base PAL from Occupation
    base_pal = PAL_VALUES.get(user.daily_activity.lower(), 1.2)

    # Metabolic Equivalent of Task (MET) method
    # Exercise Energy Expenditure (EEE) calculation
    # Loop through every activity the user sent
    total_weekly_eee = 0.0
    for act in user.activities:
        # Get MET (default to 0 if invalid string)
        met_val = MET_VALUES.get(act.intensity, 0.0)
        
        # Calculate burn for this specific activity
        burn = met_val * act.hours * user.weight
        
        # Add to total
        total_weekly_eee += burn
    # Calculte daily EEE
    daily_eee = total_weekly_eee / 7.0
    
    # Avoid division by zero if BMR is somehow 0
    if bmr == 0: return 0
    
    pal_increase = daily_eee / bmr
    raw_pal = base_pal + pal_increase
    # Calculate total TDEE
    final_pal = min(raw_pal, 2.4)  # Cap PAL at 2.4 to avoid overestimation
    tdee = bmr * final_pal
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
    
def adjust_caloric_intake(tdee: float, user: UserProfile, bmr: float, explicit_goal: str = None) -> int:
    """
    Adjusts TDEE based on the User's Goal (Dropdown OR Text Input), 
    but applies a BMI HEALTH OVERRIDE if the goal conflicts with health safety.
    """
    # Calculate BMI
    bmi = calc_bmi(user)
    
    # 1. DETERMINE EFFECTIVE GOAL
    # Prioritize the AI text input. If that's None, use the Dropdown value.
    # Convert to string/lowercase to handle Enums correctly.
    raw_goal = explicit_goal if explicit_goal else user.goal.value
    raw_goal = str(raw_goal).lower()
    
    # APPLY MEDICAL SAFETY OVERRIDES
    # SCENARIO: UNDERWEIGHT (BMI < 18.5)
    # Medical Rule: Never allow a deficit. Ideally, force a surplus.
    if bmi < 18.5:
        if target_multiplier < 1.0: # User asked to LOSE
            print(f"SAFETY INTERVENTION: User is Underweight ({bmi:.1f}) but asked to Lose. Forcing Surplus.")
            target_multiplier = 1.10 # Force Weight Gain
        elif target_multiplier == 1.0: # User asked to MAINTAIN
            print(f"HEALTH NUDGE: User is Underweight ({bmi:.1f}). Nudging towards slight surplus.")
            target_multiplier = 1.05 # Slight surplus to encourage healthy weight

    # SCENARIO: OBESE
    elif bmi >= 30.0:
        if target_multiplier > 1.0: # User asked to GAIN
            print(f"SAFETY INTERVENTION: User is Obese ({bmi:.1f}) but asked to Bulk. Forcing Deficit for Body Recomp.")
            target_multiplier = 0.80 

    # SCENARIO: OVERWEIGHT
    elif bmi >= 25.0:
        if target_multiplier > 1.0: # User asked to GAIN
            print(f"HEALTH NUDGE: User is Overweight ({bmi:.1f}). Switching Bulk to Maintenance/Recomp.")
            target_multiplier = 0.90 

    # 4. CALCULATE CALORIES
    adjusted_calories = tdee * target_multiplier
    
    # 5. ABSOLUTE SAFETY FLOOR
    if adjusted_calories < bmr:
        print(f"SAFETY FLOOR: Target {int(adjusted_calories)} is below BMR {int(bmr)}. Resetting to BMR.")
        adjusted_calories = bmr

    return int(adjusted_calories)

# Check for Sarcopenia risk (Age 60+)
def is_senior(age: int) -> bool:
    return age >= 60

# Emphasizes must be placed on the quality over rigid percentages.
def get_macro_split(weight_category: str, explicit_goal: str = None, is_senior: bool = False, macro_style: str = None):
        # Metabolic reset / insulin resistance focus
        # Lower carb, moderate protein, higher healthy fat
        # Split: 40% Protein, 25% Carbs, 35% Fat
        # Emphasizing protein since it boosts metabolism, makes person feel fuller, preserves muscle mass, and increase calorie burn
        # Higher healthy fat amount replaces carbs.
        # Higher healthy fat increase satiety, stabilize blood sugar to prevent fat storage, boost metabolism, and provide essential 
        # building blocks for cells and hormones, helping reverse fat-storing cycles caused by sugar/carb-heavy diets, all leading to 
        # reduced hunger, cravings, and ultimately, becoming lean
        # When sugars and carbs are reduced and healthy fats increased, body shifts from storing fat to burning it for energy. 
     
    # 1. AI / DIET OVERRIDES
    # These come from explicit user text input indicating a specific diet style.
    # However, system still respects conflicting health rules.
    # Protein/Carb/Fat ratios for specific diets
    if macro_style == "keto":
        return (0.20, 0.10, 0.70) # High Fat, very low carb
    if macro_style == "low_carb":
        return (0.35, 0.20, 0.45) # Controlled carbs, higher protein/fat
    if macro_style == "diabetic_friendly":
        return (0.40, 0.25, 0.35) # Balanced to control blood sugar
    if macro_style == "high_protein":
        return (0.35, 0.40, 0.25)
    if macro_style == "heart_healthy":
        return (0.30, 0.45, 0.25) # Moderate everything, lower fat
    if macro_style == "vegan" or macro_style == "vegetarian":
        return (0.25, 0.40, 0.35) # Plants are usually higher carb 
      
    goal = str(explicit_goal).lower() if explicit_goal else ""
    # EXPLICIT TEXT GOALS
    if goal in gain_keywords:
        return (0.35, 0.45, 0.20) # High Carb/Protein for lifting
    if goal in lose_keywords:
        return (0.35, 0.25, 0.40) # High Protein/Fat for satiety
    if explicit_goal == "maintain":
        return (0.35, 0.35, 0.30) # High Protein/Fat for satiety

    # Older adults need more protein to maintain muscle mass (Sarcopenia) even if they are just "maintaining" weight.
    if is_senior:
        # Boost Protein to 35%, reduce Carbs slightly
        return (0.35, 0.35, 0.30) 

    # STANDARD BMI LOGIC (Fallback)
    if weight_category in ["overweight", "obese"]:
        return (0.40, 0.25, 0.35) # Insulin control
        
    elif weight_category == "underweight":
        return (0.25, 0.40, 0.35) 
       
    else: # Normal Weight (< 60 years old)
        return (0.35, 0.35, 0.30) # Balanced

# Distributes calories and macros across meals based on meal count and user profile
def distrib_of_cal_for_meals(total_calories: int, meal_count: int, weight_category: str, explicit_goal: str = None, is_senior: bool = False):
    # 1. Getting Daily Ratios based on user profile and explicit goal
    p_ratio, c_ratio, f_ratio = get_macro_split(weight_category, explicit_goal, is_senior)

    # 2. Calculating Daily Gram Totals. This translates the abstract calorie goal into concrete macro gram targets for the day, which are essential for KNN meal selection.
    # 1g Protein = 4 Calories
    # 1g Carbs = 4 Calories
    # 1g Fat = 9 Calories
    daily_protein = (total_calories * p_ratio) / 4
    daily_carbs   = (total_calories * c_ratio) / 4
    daily_fat     = (total_calories * f_ratio) / 9

    # 3. Defining Time Ratios
    time_ratios = {
        2: [("Breakfast/Lunch", 0.55), ("Dinner", 0.45)],
        3: [("Breakfast", 0.35), ("Lunch", 0.35), ("Dinner", 0.30)],
        4: [("Breakfast", 0.30), ("Lunch", 0.35), ("Snack", 0.10), ("Dinner", 0.25)],
        5: [("Breakfast", 0.30), ("Morning Snack", 0.10), ("Lunch", 0.30), ("Afternoon Snack", 0.10), ("Dinner", 0.20)],
        6: [("Breakfast", 0.25), ("Morning Snack", 0.10), ("Lunch", 0.25), ("Afternoon Snack", 0.10), ("Dinner", 0.20), ("Late Snack", 0.10)]
    }
    # Getting the selected meal plan based on the user's meal count. If the meal count is outside the defined range, it defaults to the 3-meal plan.
    selected_plan = time_ratios.get(meal_count, time_ratios[3])
    meal_plan = []
    
    # Loops through each meal in the selected plan, calculating the calorie and macro targets for that meal based on the defined ratios. This creates a 
    # structured meal plan that can be used for KNN meal selection, ensuring that each meal aligns with the user's overall caloric and macronutrient goals 
    # while also adhering to the time-based distribution preferences.
    for meal_name, ratio in selected_plan:
        # Calculating calories for this meal by applying the time-based ratio to the total daily calories.
        meal_cal = int(total_calories * ratio)
        
        # 4. Assigning the calculated calorie and macro targets to the meal plan structure. 
        # It creates a structured dictionary for one specific meal.
        meal_plan.append({
            "meal_name": meal_name, # Tells KNN which meal to look for
            "calories": meal_cal, # Tells KNN look for meals around this calorie count
            # THE TARGET VECTOR for KNN MEAL SELECTION
            "target_macros": {
                "calories": meal_cal,
                # Explicitly calculating per-meal limits, these keys are used for frontend display
                "protein": int(daily_protein * ratio),
                "carbs":   int(daily_carbs   * ratio),
                "fat":     int(daily_fat     * ratio),
                # Keeping these keys for compatibility with existing KNN keys
                # These keys match colums in the db
                "protein, total (g)": int(daily_protein * ratio),
                "carbohydrate, available (g)": int(daily_carbs * ratio),
                "fat, total (g)": int(daily_fat * ratio)
            }
        })

    return meal_plan

# Allergy Safety Check
def is_safe_to_eat(user_allergies: list[str], food: dict) -> bool:
    """
    Checks safety based on:
    1. The 'allergens' column
    2. The 'name' column (Simple substring match).
    """
    
    # Optimization: If user has no allergies, everything is safe
    if not user_allergies:
        return True

    # CHECK 1: TAG MATCH
    food_tags = food.get('allergens')
    # Ensures tags exist AND are in the expected list format. If not, we skip to name matching.
    if food_tags and isinstance(food_tags, list):
        # Convert both to sets for instant intersection check
        # e.g., User: {'gluten'}, Food: {'gluten', 'soy'} -> Intersection: {'gluten'} -> UNSAFE
        common_allergens = set(user_allergies).intersection(set(food_tags))
        
        if common_allergens:
            return False # Unsafe (Found a matching allergy tag)

    # CHECK 2: NAME MATCH (Fallback)
    # Only if tags didn't catch it, or as a double-check
    food_name = food.get('name', "").lower()
    
    for allergy in user_allergies:
        # Simple substring check
        # e.g. "milk" in "milk chocolate"
        if allergy.lower() in food_name:
            return False # Unsafe

    return True # Safe


