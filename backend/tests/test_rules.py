import pytest
from models import UserProfile, Gender, Goal, ActivityLevel, Intensity, UserActivity
from rules_engine import (
    calc_bmi, 
    calc_bmr, 
    calc_tdee, 
    determine_weight_cat, 
    adjust_caloric_intake, 
    get_macro_split,
    distrib_of_cal_for_meals,
    is_safe_to_eat
)

# FIXTURES (Reusable User Data)

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

def test_macro_priority_keto(base_user):
    # AI Text input "keto" should override generic goals
    p, c, f = get_macro_split("normal", explicit_goal="lose_weight", macro_style="keto")
    
    assert f == 0.70 # Fat should be high
    assert c == 0.10 # Carbs should be low (Keto rules)
    assert p == 0.20 # Protein moderate

def test_macro_explicit_text_goal(base_user):
    # User selected "Maintain" in dropdown, but typed "gain muscle" in text
    p, c, f = get_macro_split("normal", explicit_goal="gain muscle")
    
    assert p == 0.35 # High protein for gain
    assert c == 0.45 # High carb for gain
    assert f == 0.20 # Fat moderate

def test_macro_senior(base_user):
    # Senior should get balanced protein even if maintaining
    p, c, f = get_macro_split("normal", is_senior=True)
    assert p == 0.35 
    assert c == 0.35
    assert f == 0.30

# 5. MEAL DISTRIBUTION

def test_meal_math(base_user):
    total_cal = 2000
    meals = distrib_of_cal_for_meals(total_cal, 4, "normal")
    
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