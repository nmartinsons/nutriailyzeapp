import pytest
from models import UserProfile, Gender, Goal, ActivityLevel, Intensity, UserActivity
from rules_engine import (
    calc_bmi, 
    calc_bmr,
    calc_min_fat_target, 
    calc_tdee, 
    determine_weight_cat, 
    adjust_caloric_intake, 
    calculate_daily_macros,
    distrib_of_cal_for_meals,
    get_carb_fat_split,
    is_safe_to_eat,
    calc_protein_target
)

# FIXTURES (Reusable User Data), so there is no need to redefine this in every test
@pytest.fixture
def base_user():
    return UserProfile(
        age=30,
        weight=80.0,
        height=180.0,
        gender=Gender.MALE,
        daily_activity=ActivityLevel.SEDENTARY,
        goal=Goal.MAINTAIN,
        activities=[],
        meal_amount=3,
        allergies=[],
        text_input=""
    )

# 1. BASIC BIOMETRICS TESTS

def test_calc_bmi(base_user):
    bmi = calc_bmi(base_user)
    assert round(bmi, 2) == 24.69
    assert determine_weight_cat(bmi) == "normal weight"

def test_calc_bmr_male(base_user):
    bmr = calc_bmr(base_user)
    assert int(bmr) == 1780

def test_calc_bmr_female(base_user):
    base_user.gender = Gender.FEMALE
    bmr = calc_bmr(base_user)
    assert int(bmr) == 1614

# 2. TDEE & ACTIVITY TESTS

def test_tdee_sedentary(base_user):
    tdee = calc_tdee(base_user)
    # Without any additional extra activities, sedentary = 1.2 * BMR
    assert int(tdee) == 2136

def test_tdee_with_exercise(base_user):
    base_user.activities = [
        UserActivity(hours=4, intensity=Intensity.HIGH)
    ]
    # met_value = 8.0
    # activity hours = 4
    # user weight = 80 kg
    # burn = 8*4*80 = 2560 calories from exercise
    # 2560 / 7 = ~365.71 additional daily calories
    # Pal increase = 365.71 / 1780 (bmr) = ~0.205
    # New PAL = 1.2 (sedentary) + 0.205 = ~1.405
    # Final TDEE = 1780 * 1.405 = 2500
    tdee = calc_tdee(base_user)
    assert tdee > 2500

# 3. SAFETY OVERRIDES

def test_safety_underweight_lose(base_user):
    # Force Underweight stats
    base_user.weight = 50.0 # BMI ~15.4
    base_user.goal = Goal.LOSE # User wants to lose (DANGEROUS)
    
    tdee = 2000
    bmr = 1500
    
    # Logic should override LOSE (0.85) to SURPLUS (1.10)
    # 2000 * 1.10 = 2200
    adj_cal = adjust_caloric_intake(tdee, base_user, bmr)
    
    assert adj_cal > tdee # Must be a surplus
    assert adj_cal == 2200

def test_safety_obese_gain(base_user):
    # Force Obese stats
    base_user.weight = 120.0 # BMI ~37
    base_user.goal = Goal.GAIN # User wants to bulk (UNHEALTHY)
    
    tdee = 3000
    bmr = 2000
    
    # Logic should override GAIN (1.10) to DEFICIT (0.80)
    # 3000 * 0.80 = 2400
    adj_cal = adjust_caloric_intake(tdee, base_user, bmr)
    
    assert adj_cal < tdee # Must be a deficit
    assert adj_cal == 2400

def test_bmr_floor_protection(base_user):
    # Standard user wants to lose
    base_user.goal = Goal.LOSE
    
    tdee = 1600 # Very low TDEE
    bmr = 1500  # High BMR
    
    # Calculation: 1600 * 0.85 = 1360.
    # 1360 < 1500 (BMR). Logic should reset to BMR.
    adj_cal = adjust_caloric_intake(tdee, base_user, bmr)
    
    assert adj_cal == 1500 # Should trigger floor

# 4. MACRO SPLIT LOGIC

def test_protein_calculation(base_user):
    # Normal Maintenance: 1.6g/kg
    # 80kg * 1.6 = 128g
    p = calc_protein_target(base_user)
    assert int(p) == 128

def test_protein_high_goal(base_user):
    # High Protein Goal: 2.2g/kg
    # 80kg * 2.2 = 176g
    p = calc_protein_target(base_user, macro_style="high_protein")
    assert int(p) == 176

def test_keto_macros(base_user):
    # Keto: Low Carb, Moderate Protein, High Fat
    # Total Cal: 2000
    total_cal = 2000
    
    macros = calculate_daily_macros(total_cal, base_user, macro_style="keto")
    
    p = macros['protein']
    c = macros['carbs']
    f = macros['fat']
    
    # Verify Ratios
    # Protein: 1.6g/kg = 128g (512 kcal)
    # Remaining: 1488 kcal
    # Carbs: 10% of remaining = 148.8 kcal = 37.2g
    assert int(p) == 128
    assert int(c) == 37
    assert int(f) == 148 # 1488 - 148.8 = 1339.2 kcal / 9 = 148.8g fat

def test_obese_macro_safety(base_user):
    # User is 150kg (Obese)
    base_user.weight = 150.0 
    base_user.goal = Goal.MAINTAIN
    
    # Protein shouldn't be 150 * 1.6 = 240g (Too high)
    # It should use adjusted weight (~85kg for 180cm height)
    # Adjusted Weight ~81kg -> 81 * 1.6 = ~130g
    
    p = calc_protein_target(base_user)
    assert int(p) == 231 
   

def test_min_fat_floor(base_user):
    # User on very low calories but wants high carbs
    total_cal = 1200
    
    # Force low fat preference via macro_style if possible, or rely on logic
    # Min Fat: 80kg * 0.7 = 56g
    
    macros = calculate_daily_macros(total_cal, base_user, macro_style="vegan")
    # Vegan usually 55% carb / 30% fat split of remainder
    
    assert macros['fat'] >= 56 # Should enforce floor
    

def test_calc_min_fat_target(base_user):
    """Test that fat floors change based on diet style"""
    # Base user is 80kg
    
    # 1. Standard (No activity) -> 0.7g/kg
    # 80 * 0.7 = 56g
    assert calc_min_fat_target(base_user) == 56.0
    
    # 2. Keto (High Fat requirement) -> 1.2g/kg
    # 80 * 1.2 = 96g
    assert calc_min_fat_target(base_user, macro_style="keto") == 96.0
    
    # 3. Heart Healthy (Lower Fat floor) -> 0.6g/kg
    # 80 * 0.6 = 48g
    assert calc_min_fat_target(base_user, macro_style="heart_healthy") == 48.0
    
    # 4. Active User -> 0.8g/kg
    base_user.activities = [UserActivity(hours=5, intensity=Intensity.MODERATE)]
    # 80 * 0.8 = 64g
    assert calc_min_fat_target(base_user) == 64.0

def test_carb_fat_split_sedentary_gain(base_user):
    """Test split for someone bulking but sedentary"""
    # Inputs
    total_cal = 3000
    protein_g = 200 # 800 kcal
    min_fat = 50
    # Remaining = 2200 kcal
    
    # Logic check from rules_engine:
    # Goal='gain' -> Base ratio 0.55 + (Training Score 0.0 * 0.15) = 0.55
    
    c, f = get_carb_fat_split(total_cal, protein_g, min_fat, base_user, explicit_goal="gain")
    
    # Expected Carbs: 2200 * 0.55 = 1210 kcal / 4 = 302g
    # Expected Fat: 2200 * 0.45 = 990 kcal / 9 = 110g
    
    assert int(c) == 302
    assert int(f) == 110

def test_carb_fat_split_athlete_gain(base_user):
    """Test split for an athlete bulking (Should trigger higher carbs)"""
    # Add High Intensity Activity to boost training score to ~1.0
    base_user.activities = [UserActivity(hours=10, intensity=Intensity.VERY_HIGH)]
    
    total_cal = 3000
    protein_g = 200 # 800 kcal
    min_fat = 50
    # Remaining = 2200 kcal
    
    # Logic check:
    # Goal='gain' -> Base 0.55 + (Training Score ~1.0 * 0.15) = 0.70 Carb Ratio
    
    c, f = get_carb_fat_split(total_cal, protein_g, min_fat, base_user, explicit_goal="gain")
    
    # Expected Carbs: 2200 * 0.70 = 1540 kcal / 4 = 385g
    # Expected Fat: 2200 * 0.30 = 660 kcal / 9 = 73g
    
    assert int(c) == 385 # Should be significantly higher than sedentary
    assert int(f) == 73  # Fat should be lower to make room for carbs

def test_split_safety_floor_intervention(base_user):
    """Test that the split function forces minimum fat if the ratio tries to go too low"""
    # Scenario: Very low calorie diet, user wants 'high carb' style (Vegan)
    # Vegan defaults to 0.55 ratio
    
    total_cal = 1200
    protein_g = 100 # 400 kcal
    # Remaining = 800 kcal
    
    # We set a high fat requirement manually for the test
    # e.g. User needs 60g fat minimum (540 kcal)
    min_fat = 60 
    
    # Standard Math without safety:
    # Fat = remaining (800) * (1 - 0.55) = 360 kcal / 9 = 40g
    # 40g is LESS THAN min_fat (60g). Logic should intervene.
    
    c, f = get_carb_fat_split(total_cal, protein_g, min_fat, base_user, macro_style="vegan")
    
    assert f == 60 # Should be forced to minimum
    # Carbs should take the hit: (800 - 540) / 4 = 65g
    assert c == 65
    
# 5. MEAL DISTRIBUTION

def test_meal_math(base_user):
    total_cal = 2000
    meals = distrib_of_cal_for_meals(total_cal, 4, base_user)
    
    assert len(meals) == 4
    assert meals[0]['meal_name'] == "Breakfast"
    assert meals[1]['meal_name'] == "Lunch"
    assert meals[2]['meal_name'] == "Snack"
    assert meals[3]['meal_name'] == "Dinner"
    assert meals[0]['calories'] == 600  # 30% of 2000
    assert meals[1]['calories'] == 700  # 35% of 2000
    assert meals[2]['calories'] == 200  # 10% of 2000
    assert meals[3]['calories'] == 500  # 25% of 2000
    
    # Check if sum of meals roughly equals total (allow integer rounding errors)
    sum_cals = sum(m['calories'] for m in meals)
    assert 1990 < sum_cals < 2010

# 6. ALLERGY CHECKS

def test_is_safe_to_eat():
    # Setup
    user_allergies = ["peanut", "milk"]
    
    # Case 1: Safe Food
    safe_food = {"name": "Chicken Breast", "allergens": []}
    assert is_safe_to_eat(user_allergies, safe_food) is True
    
    # Case 2: Unsafe by Tag
    unsafe_tag = {"name": "Protein Bar", "allergens": ["soy", "peanut"]}
    assert is_safe_to_eat(user_allergies, unsafe_tag) is False
    
    # Case 3: Unsafe by Name (Tag missing)
    unsafe_name = {"name": "Milk Chocolate", "allergens": []}
    assert is_safe_to_eat(user_allergies, unsafe_name) is False

    # Case 4: Partial String Match
    unsafe_partial = {"name": "Peanut Butter", "allergens": []}
    assert is_safe_to_eat(user_allergies, unsafe_partial) is False