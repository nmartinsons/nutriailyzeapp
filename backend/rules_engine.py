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
    
    if raw_goal in lose_keywords:
        target_multiplier = 0.85  # 15% Deficit
    elif raw_goal in gain_keywords:
        target_multiplier = 1.10  # 10% Surplus
    else:
        target_multiplier = 1.00  # Maintain
    
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

def _get_calculation_weight(user: UserProfile) -> float:
    """
    Determines the weight used for macro calculations.
    For Obese individuals (BMI > 30), protein/fat needs should be based on 
    Lean Body Mass (estimated via 'Target BMI 25' weight) rather than total weight.
    This prevents prescribing 300g Protein to a 150kg person.
    """
    bmi = calc_bmi(user)
    if bmi > 30:
        # Calculate weight if BMI was 25 (Upper end of normal)
        height_m = user.height / 100
        adjusted_weight = 25 * (height_m ** 2)
        # Use the average of actual and adjusted to be safe/satiating
        return (user.weight + adjusted_weight) / 2
    return user.weight

def calc_training_intensity_score(user: UserProfile) -> float:
    if not user.activities: return 0.0
    #  A Normalized Ratio (0.0 to 1.0) indicating how "Glycolytic" (Carb-demanding) the training style is.
    INTENSITY_WEIGHTS = {
        Intensity.NONE: 0.0, 
        Intensity.LOW: 0.2, # Mostly burns fat, needs very few extra carbs.
        Intensity.MODERATE: 0.5, # Aerobic/cardio style, moderate carb needs.
        Intensity.HIGH: 0.8, # Lactate Threshold. The body stops burning fat almost entirely because it's too slow. It switches to 80-90% Carbs for fuel.
        Intensity.VERY_HIGH: 1.0 # Explosive effort. The body uses 100% Phosphocreatine and Glycogen (Carbs). Fat cannot be used as fuel at this intensity.
    }
    # Weighted average based on hours spent at each intensity
    total_weighted_hours = 0.0
    # Total hours spent training
    total_hours = 0.0
    # For loop through all activities
    for act in user.activities:
        weight = INTENSITY_WEIGHTS.get(act.intensity, 0.0)
        total_weighted_hours += weight * act.hours
        total_hours += act.hours
    
    if total_hours == 0: return 0.0
    # Dividing the weighted total by the actual time. This gives the Average Intensity of the user's lifestyle.
    avg_intensity = total_weighted_hours / total_hours
    
    # This ensures that someone who trains a lot at high intensity gets a higher score, while someone who trains less or at lower intensity gets a lower score.
    volume_bonus = min(total_hours / 10, 0.2) 
    
    return min(avg_intensity + volume_bonus, 1.0)

# Function for calculating daily protein target in grams, based on bodyweight and diet style constraints.
def calc_protein_target(user: UserProfile, explicit_goal: str = None, is_senior: bool = False, macro_style: str = None) -> float:
    # Use Adjusted Weight
    calc_weight = _get_calculation_weight(user)
    
    # Get Weight Category for Metabolic Context
    bmi = calc_bmi(user)
    weight_category = determine_weight_cat(bmi)
    
    if macro_style == "keto": 
        g_per_kg = 1.6
    elif macro_style == "heart_healthy":
        g_per_kg = 1.4
    elif macro_style == "diabetic_friendly":
        g_per_kg = 1.5
    elif macro_style == "low_carb":
        g_per_kg = 1.8
    elif macro_style == "high_protein": 
        g_per_kg = 2.2
    elif macro_style == "vegan" or macro_style == "vegetarian": 
        g_per_kg = 1.8
    elif weight_category in ["overweight", "obese"]:
        g_per_kg = 2.0
        print(f"METABOLIC ADJUSTMENT: Lowering protein for {weight_category} category.")
    elif weight_category == "underweight":
        g_per_kg = 1.8 
        print(f"METABOLIC ADJUSTMENT: Increasing protein for {weight_category} category.")
    else:
        goal = str(explicit_goal).lower() if explicit_goal else ""
        if is_senior: 
            g_per_kg = 1.8
        elif goal in lose_keywords: 
            g_per_kg = 2.0
        elif goal in gain_keywords: 
            g_per_kg = 2.0
        else: 
            g_per_kg = 1.6 
    
    return calc_weight * g_per_kg

# Fnction for calculating minimum fat target in grams, based on bodyweight and diet style constraints.
def calc_min_fat_target(user: UserProfile, macro_style: str = None) -> float:
    """
    Calculate MINIMUM fat target in GRAMS based on bodyweight.
    Adjusted for diet style constraints.
    """
    # Uses Adjusted Weight (same as protein function)
    calc_weight = _get_calculation_weight(user)
    
    # Get Weight Category for Metabolic Context
    bmi = calc_bmi(user)
    weight_category = determine_weight_cat(bmi)
    
    # 1. DIET STYLE OVERRIDES
    if macro_style == "keto": 
        min_g_per_kg = 1.2  # Keto requires high fat for energy
    elif macro_style == "low_carb":
        min_g_per_kg = 1.0  # Higher fat needed to replace carb energy
    elif macro_style == "diabetic_friendly":
        min_g_per_kg = 0.9  # Moderate fat helps stabilize blood sugar
    elif macro_style == "vegan" or macro_style == "vegetarian":
        min_g_per_kg = 0.9  # Plant-based diets need healthy fats for satiety
    elif macro_style == "heart_healthy": 
        min_g_per_kg = 0.6  # Lower floor, prioritizes unsaturated fats later
    elif macro_style == "high_protein":
        min_g_per_kg = 0.7  # Keep fat floor low to save calories for protein
    elif weight_category in ["overweight", "obese"]:
        min_g_per_kg = 0.75
        print(f"METABOLIC ADJUSTMENT: Lowering fat for {weight_category} category.")
    elif weight_category == "underweight":
        min_g_per_kg = 0.9 
        print(f"METABOLIC ADJUSTMENT: Increasing fat for {weight_category} category.")
    
    # 2. ACTIVITY FALLBACK
    else:
        # Active people need slightly more fat for hormone regulation/recovery
        if user.activities and len(user.activities) > 0: 
            min_g_per_kg = 0.8
        else: 
            min_g_per_kg = 0.7
    
    return calc_weight * min_g_per_kg


def get_carb_fat_split(total_calories: int, protein_grams: float, min_fat_grams: float,
                       user: UserProfile, explicit_goal: str = None, macro_style: str = None) -> tuple:
    
    # First, we calculate how many calories are taken up by protein. This is important because protein has a fixed calorie per gram (4 calories/gram), and we need to know how many calories are left for carbs and fat after accounting for protein.
    protein_calories = protein_grams * 4
    remaining_calories = total_calories - protein_calories
    
    # SAFTEY CHECK: If remaining calories are already negative or zero. If so, we can't allocate anything to carbs or fat, and we should return 0 for carbs and the minimum fat grams (which will be converted to calories later). 
    # This is a safety check to ensure we don't end up with negative calories for carbs/fat.
    if remaining_calories <= 0: 
        return (0.0, min_fat_grams)
    
    # The training intensity score is a value between 0.0 and 1.0 that indicates how demanding the user's training style is in terms of carbohydrate needs. A higher score means the user does more high-intensity training, which relies more on carbohydrates for fuel, while a lower score indicates a more sedentary lifestyle or low-intensity training, which relies more on fat for fuel. 
    # This score will be used to dynamically adjust the carb/fat split based on the user's actual activity patterns, rather than just their stated goal or diet style.
    training_score = calc_training_intensity_score(user)
    goal = str(explicit_goal).lower() if explicit_goal else ""
    
    # Get Weight Category for Metabolic Context
    bmi = calc_bmi(user)
    weight_category = determine_weight_cat(bmi)
    
    # Determines Carb Ratio of REMAINING calories
    if macro_style == "keto": 
        # KETO EXCEPTION: Do NOT scale with activity. 
        # Ketosis requires low carbs regardless of how much you run.
        # We rely on FAT to fuel the activity here.
        carb_ratio = 0.10 # 10% of remainder
    elif macro_style == "low_carb": 
        carb_ratio = 0.25 + (training_score * 0.10)
    elif macro_style == "diabetic_friendly": 
        carb_ratio = 0.30 + (training_score * 0.10)
    elif macro_style == "heart_healthy":
        carb_ratio = 0.50 + (training_score * 0.15)
    elif macro_style == "high_protein":
        carb_ratio = 0.40 + (training_score * 0.15)
    elif macro_style == "vegan" or macro_style == "vegetarian": 
        carb_ratio = 0.55 + (training_score * 0.15)
    elif weight_category in ["overweight", "obese"]:
        # Insulin Control Logic: Lower baseline carbs, rely more on fats/protein.
        # Base 30% carbs + up to 15% for training. 
        # (Max carbs ~45% of remainder, preventing huge insulin spikes)
        carb_ratio = 0.30 + (training_score * 0.15)
        print(f"METABOLIC ADJUSTMENT: Lowering carbs for {weight_category} category.")
    elif weight_category == "underweight":
        # Restoration Logic: Higher baseline carbs for easy energy.
        # Base 50% carbs + training bonus.
        carb_ratio = 0.50 + (training_score * 0.10)
        print(f"METABOLIC ADJUSTMENT: Increasing carbs for {weight_category} category.")
    else:
        # Dynamic based on activity
        if goal in gain_keywords:
            carb_ratio = 0.55 + (training_score * 0.15) # Up to 70% of remainder
        elif goal in lose_keywords:
            carb_ratio = 0.30 + (training_score * 0.10)
        else:
            carb_ratio = 0.45 + (training_score * 0.10)
            
    # Calculating calories for carbs and fat based on the remaining calories after protein, and the dynamically determined carb ratio. 
    # The rest of the remaining calories after allocating for carbs will go to fat.
    carb_calories = remaining_calories * carb_ratio
    fat_calories = remaining_calories - carb_calories
    
    # We convert those calorie amounts into grams (4 calories per gram of carbs, 9 calories per gram of fat).
    carb_grams = carb_calories / 4
    fat_grams = fat_calories / 9
    
    # Fat Safety Floor
    # This ensures that we never go below the minimum fat target, which is important for hormone production, nutrient absorption, and overall health. 
    # If the calculated fat grams are below the minimum, we set fat grams to the minimum and recalculate carb grams based on the new fat calories.
    if fat_grams < min_fat_grams:
        fat_grams = min_fat_grams
        fat_calories = fat_grams * 9
        carb_calories = remaining_calories - fat_calories
        # If carb calories go negative due to the fat floor, we set carbs to 0 to avoid negative macros.
        carb_grams = max(carb_calories / 4, 0)
        
    return (carb_grams, fat_grams)

def calculate_daily_macros(total_calories: int, user: UserProfile, explicit_goal: str = None, 
                          is_senior: bool = False, macro_style: str = None) -> dict:
    
    protein_grams = calc_protein_target(user, explicit_goal, is_senior, macro_style)
    min_fat_grams = calc_min_fat_target(user, macro_style)
    
    carb_grams, fat_grams = get_carb_fat_split(
        total_calories, protein_grams, min_fat_grams,
        user, explicit_goal, macro_style
    )
    
    return {
        "protein": int(protein_grams),
        "carbs": int(carb_grams),
        "fat": int(fat_grams)
    }
    
    
# Distributes calories and macros across meals based on meal count and user profile
def distrib_of_cal_for_meals(total_calories: int, meal_count: int, user: UserProfile, explicit_goal: str = None, is_senior: bool = False, macro_style: str = None) -> list:

    # 1. Get Daily Totals (Grams)
    daily_macros = calculate_daily_macros(
        total_calories, user, explicit_goal, is_senior, macro_style
    )
    daily_protein = daily_macros["protein"]
    daily_carbs = daily_macros["carbs"]
    daily_fat = daily_macros["fat"]

    # 2. Defining Time Ratios
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


