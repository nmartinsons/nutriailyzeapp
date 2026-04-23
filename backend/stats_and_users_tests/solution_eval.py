import json
import re
import random
import time
import traceback
from pathlib import Path
from plan_generator import MealPlanGenerator
from models import UserProfile, UserActivity, Intensity, Gender, Goal, ActivityLevel
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_JSON = BASE_DIR / "test_users.json"
OUTPUT_JSON = BASE_DIR / "stats_and_users" / "generated_plans.json"
FAILURES_JSON = BASE_DIR / "stats_and_users" / "failed_profiles.json"
THESIS_BASE_SEED = 2026

# 1. Loading Test Users
try:
    with open(INPUT_JSON, "r") as f:
        users_data = json.load(f)
    print(f"Loaded {len(users_data)} profiles from '{INPUT_JSON}'")
except FileNotFoundError:
    print(f"Error: '{INPUT_JSON}' not found. Run data_generator.py first!")
    exit()

results =[]
failures = []

for data in users_data:
    try:
        # Deterministic seeding for thesis reproducibility (evaluation only)
        user_id_seed = int(data.get('id', 0)) if str(data.get('id', 0)).isdigit() else sum(ord(ch) for ch in str(data.get('id', '0')))
        run_seed = THESIS_BASE_SEED + user_id_seed
        random.seed(run_seed)
        np.random.seed(run_seed)

        # Data conversion (JSON -> Pydantic Objects)
        
        # 1. Converting Activities
        activity_objects =[]
        if 'activities' in data:
            for act in data['activities']:
                activity_objects.append(
                    UserActivity(
                        hours=act['hours'],
                        intensity=Intensity(act['intensity']) 
                    )
                )

        # 2. Creating User Profile
        user_obj = UserProfile(
            id=data['id'],
            age=data['age'],
            height=data['height'],
            weight=data['weight'],
            gender=Gender(data['gender']),
            daily_activity=ActivityLevel(data['daily_activity']),
            goal=Goal(data['goal']),
            activities=activity_objects,
            meal_amount=data.get('meal_amount', 3),
            allergies=data['allergies'],
            text_input=data['text_input']
        )
        
        # Running Algorithm to Generate Meal Plan
        generator = MealPlanGenerator(user_obj)
        # Generating raw plan (No API calls to Gemini for enrichment so it is faster)
        plan_output = generator.generate_raw_plan()
        
        targets = plan_output['daily_targets']
        meals = plan_output['meals']
        
        # METRIC 1: Nutritional adherence (MAPE)
        
        # Calculate Totals
        actual_p = sum(m['target_macros'].get('protein', 0) if 'total_macros' not in m else m['total_macros'].get('protein', 0) for m in meals)
        actual_c = sum(m['target_macros'].get('carbs', 0) if 'total_macros' not in m else m['total_macros'].get('carbs', 0) for m in meals)
        actual_f = sum(m['target_macros'].get('fat', 0) if 'total_macros' not in m else m['total_macros'].get('fat', 0) for m in meals)
        actual_cal = (actual_p * 4) + (actual_c * 4) + (actual_f * 9)
        
        # Get Targets
        target_cal = targets['calories']
        target_p = targets['protein']
        target_c = targets['carbs']
        target_f = targets['fat']
        
        # Calculate APE (Absolute Percentage Error)
        ape_cal = abs(actual_cal - target_cal) / target_cal * 100 if target_cal > 0 else 0
        ape_p = abs(actual_p - target_p) / target_p * 100 if target_p > 0 else 0
        ape_c = abs(actual_c - target_c) / target_c * 100 if target_c > 0 else 0
        ape_f = abs(actual_f - target_f) / target_f * 100 if target_f > 0 else 0
 
        # METRIC 2: Constraint Adherence (Safety / Allergies)
        style_exclusion_map = {
            "vegan":[
                    "meat", "animal", "seafood", "fish", "dairy", "egg", 
                    "honey", "gelatin", "whey", "casein", "lactose", "albumin",
                    "steak", "fillet", "broth", "stock", "buttermilk",
                    "yolk", "milk", "cheese", "yoghurt", "yogurt", "cream", "butter", 
                    "ghee", "lard", "tallow", "ice cream", "custard", "pudding",
                    "mayonnaise", "mayo", "cottage", "curd", "sour cream", 
                    "kefir", "skyr", "quark", "creme", "latte", "cappuccino", "mocha",
                    "mousse", "cream cheese", "cheesy", "cheddar", "parmesan", "brie", "camembert",
                    "feata", "gouda", "swiss", "provolone", "ricotta", "monterey", "colby",
                    "chicken", "turkey", "duck", "goose", "quail", "poultry", "wings",
                    "beef", "pork", "lamb", "veal", "venison", "goat", 
                    "rabbit", "reindeer", "mutton", "buffalo", "bison", "game",
                    "ham", "bacon", "sausage", "steak", "salami", "pepperoni", 
                    "chorizo", "burger", "meatball", "liver", "kidney", "ribs", "chop",
                    "salmon", "tuna", "trout", "cod", "herring", "sardine", 
                    "anchovy", "mackerel", "pollock", "haddock", "saithe", "eel", 
                    "snapper", "tilapia", "halibut", "flounder",
                    "shrimp", "prawn", "crab", "lobster", "crayfish", 
                    "mussel", "clam", "oyster", "scallop", "squid", 
                    "octopus", "calamari", "caviar", "roe", "sushi"
                ],
            "vegetarian": ["chicken", "beef", "pork", "meat", "fish", "seafood", "ham", "bacon", "sausage", "sausage", "turkey", "duck", "lamb", "veal", 
                           "venison", "goat", "rabbit", "mussel", "shrimp", "prawn", "crab", "lobster", "saithe", "anchovy", "caviar", "eel", "herring", 
                           "trout", "tuna", "salmon", "sardine", "squid", "octopus", "clam", "scallop", "steak", "reindeer", "pike", "mackerel", "pollock", "haddock", "halibut", "flounder"],
            "pescatarian":["chicken", "beef", "pork", "meat", "ham", "bacon", "sausage", "turkey", "duck", "lamb", "veal", "venison", "goat", "rabbit",
                            "steak", "reindeer", "meatball", "burger", "chop", "liver", "kidney", "ribs", "salami", "pepperoni", "chorizo"],
            "heart_healthy":["fried", "fatty", "saturated", "processed", "sugar", "syrup", "honey", "salty", "salted", "bacon", "sausage", "ham", "salami", "pepperoni", "chorizo"],
            "diabetic_friendly":[
                "sugar", "syrup", "honey", "juice", "soda", "cake", "cookie", 
                "sweet", "chocolate", "jam", "white bread", "white rice",
                "smoothie", "fruit_drink", "nectar", "dried fruit", "candy", "pie", "pastry", "custard",
                "ice cream", "pudding", "muffin", "biscuit", "donut", "waffle", "pancake", "crepe",
                "sugary"
            ],
            "low_carb":[
                "rice", "pasta", "bread", "sugar", "smoothie", "juice", "macaroni",
                "cake", "cookie", "potato", "starch", "cereal", "flour", "banana", "grape",
                "wheat", "grain", "oat", "corn", "flake", "maize", "gruel", "couscous", "semolina",
                "pastry", "pie", "bun", "roll", "custard", "honey", "syrup", "jam", "jelly",
                "buckwheat", "noodle", "spaghetti", "lasagna", "dumpling", "tortilla", "pizza"
            ],
            "keto":[
                "rice", "pasta", "bread", "sugar", "smoothie", "juice", "macaroni",
                "cake", "cookie", "potato", "starch", "cereal", "flour", "fruit", 
                "apple", "banana", "orange", "pear", "oat", "porridge", "muesli", 
                "bean", "lentil", "quinoa", "wheat", "rye", "barley", "amaranth", 
                "buckwheat", "grain", "flake", "maize", "gruel", "couscous", "semolina", 
                "root", "beet", "parsnip", "pastry", "pie", "custard", "honey", "syrup",
                "noodle", "spaghetti", "lasagna", "dumpling", "tortilla", "corn", "talkkuna", "mousse",
                "low fat", "low-fat", "0%", "fat free", "skimmed", "light", "reduced fat",
                "sweet", "jam", "jelly", "lean", "egg white"
            ]
        }
        # Identify prohibited items for two separate tracks:
        # 1) explicit allergens 2) dietary/style restrictions inferred from text
        allergy_items = set()
        dietary_items = set()

        # Adding explicit allergies
        if data.get('allergies'):
            for allergy in data['allergies']:
                allergy_clean = allergy.lower().strip()
                if allergy_clean:
                    allergy_items.add(allergy_clean)
                
        # Adding medical/dietary rules based on what the user asked for in their text_input
        user_text = data.get('text_input', '').lower()

        def _normalize_style_text(text: str) -> str:
            # Normalize separators so low_carb, low-carb and low carb are treated the same.
            return " ".join(re.sub(r"[_-]+", " ", text.lower()).split())

        style_trigger_aliases = {
            "vegan": ["vegan"],
            "vegetarian": ["vegetarian"],
            "pescatarian": ["pescatarian"],
            "heart_healthy": ["heart healthy", "heart_healthy", "heart-healthy"],
            "diabetic_friendly": ["diabetic friendly", "diabetic_friendly", "diabetic-friendly", "diabetic"],
            "low_carb": ["low carb", "low_carb", "low-carb"],
            "keto": ["keto", "ketogenic"],
        }

        normalized_user_text = _normalize_style_text(user_text)

        def _matches_style_condition(condition: str) -> bool:
            aliases = style_trigger_aliases.get(condition, [condition])
            for alias in aliases:
                normalized_alias = _normalize_style_text(alias)
                if not normalized_alias:
                    continue
                if re.search(rf"\b{re.escape(normalized_alias)}\b", normalized_user_text):
                    return True
            return False

        for condition, forbidden_foods in style_exclusion_map.items():
            # Match full style phrases/aliases to avoid false positives like "low energy" -> "low_carb".
            if _matches_style_condition(condition):
                for food in forbidden_foods:
                    # Don't add empty strings from your dictionary
                    if food.strip(): 
                        dietary_items.add(food.lower().strip())

        prohibited_items = allergy_items.union(dietary_items)

        # Evaluate meal plan against prohibited items
        # Scores: 1 = Safe (Pass), 0 = Unsafe (Fail), None = N/A
        constraint_score = None
        allergy_constraint_score = None
        dietary_constraint_score = None

        def _extract_allergen_tags(food_item: dict) -> set[str]:
            tags = set()

            raw_direct = food_item.get('allergens')
            if isinstance(raw_direct, list):
                tags.update(str(tag).lower().strip() for tag in raw_direct if str(tag).strip())
            elif isinstance(raw_direct, str) and raw_direct.strip():
                tags.add(raw_direct.lower().strip())

            full_profile = food_item.get('full_profile')
            if isinstance(full_profile, dict):
                raw_nested = full_profile.get('allergens')
                if isinstance(raw_nested, list):
                    tags.update(str(tag).lower().strip() for tag in raw_nested if str(tag).strip())
                elif isinstance(raw_nested, str) and raw_nested.strip():
                    tags.add(raw_nested.lower().strip())

            return tags

        def _extract_food_name(food_item: dict) -> str:
            name = food_item.get('name')
            if isinstance(name, str) and name.strip():
                return name.lower()

            full_profile = food_item.get('full_profile')
            if isinstance(full_profile, dict):
                nested_name = full_profile.get('name', '')
                if isinstance(nested_name, str):
                    return nested_name.lower()

            return ''

        def _keyword_matches_name(keyword: str, food_name: str) -> bool:
            kw = (keyword or '').strip().lower()
            name = (food_name or '').strip().lower()

            if not kw or not name:
                return False

            # "sweet pepper" is a vegetable context, not added sugar.
            if kw == 'sweet' and 'sweet pepper' in name:
                return False

            # Skip if the keyword only appears negated (e.g. "No Herring", "Without Herring").
            negated_pattern = rf"\b(no|without)\s+{re.escape(kw)}\b"
            if re.search(negated_pattern, name):
                cleaned = re.sub(negated_pattern, '', name)
                return re.search(rf"\b{re.escape(kw)}\b", cleaned) is not None

            return re.search(rf"\b{re.escape(kw)}\b", name) is not None

        def _has_violation(check_items: set) -> bool:
            if not check_items:
                return False

            for meal in meals:
                food_data = meal.get('food_data', {})
                if not food_data:
                    continue

                components = ['main_dish', 'side_dish', 'soup', 'drink']
                food_items_to_check = []

                for component in components:
                    food_item = food_data.get(component)
                    if food_item and isinstance(food_item, dict):
                        food_items_to_check.append(food_item)

                boosters = food_data.get('boosters')
                if isinstance(boosters, list):
                    for booster_item in boosters:
                        if booster_item and isinstance(booster_item, dict):
                            food_items_to_check.append(booster_item)
                else:
                    booster_item = food_data.get('booster')
                    if booster_item and isinstance(booster_item, dict):
                        food_items_to_check.append(booster_item)

                for food_item in food_items_to_check:
                    # CHECK 1: DB tags (direct + nested full_profile)
                    food_tags_lower = _extract_allergen_tags(food_item)
                    if check_items.intersection(food_tags_lower):
                        return True

                    # CHECK 2: Name fallback
                    food_name = _extract_food_name(food_item)
                    for item in check_items:
                        if _keyword_matches_name(item, food_name):
                            return True

            return False

        if prohibited_items:
            constraint_score = 0 if _has_violation(prohibited_items) else 1
        if allergy_items:
            allergy_constraint_score = 0 if _has_violation(allergy_items) else 1
        if dietary_items:
            dietary_constraint_score = 0 if _has_violation(dietary_items) else 1

        # METRIC 3: Preference Integration (Cravings)
        keyword_hit = None # None means N/A (User didn't ask for food)
        
        # Heuristic: Detect if input contains "want" but isn't about "diet"
        text_input_lower = data.get('text_input', '').lower()
        if "want" in text_input_lower and "diet" not in text_input_lower:
            # Extract food keyword (e.g., "I really want broccoli" -> "broccoli")
            try:
                parts = text_input_lower.split("want ", 1)
                if len(parts) > 1:
                    requested_food = parts[1].replace(" for lunch.", "").replace(".", "").strip()
                    plan_string = str(meals).lower()
                    keyword_hit = 1 if requested_food in plan_string else 0
            except:
                pass

        # Storing results for this user in the results list (which will be used for the final report and JSON output)
        results.append({
            # INPUTS (From the test_users.json data)
            "id": data['id'],
            "age": data['age'],
            "gender": data['gender'],
            "weight": data['weight'],
            "height": data['height'],
            "daily_activity": data['daily_activity'],
            "goal": data['goal'],
            "macro_style": data['macro_style'],       
            "allergies": data['allergies'],          
            "meal_amount": data.get('meal_amount', 3),
            "text_input": data['text_input'],
            
            # OUTPUTS (Calculated by the App)
            "daily_targets": targets,               
            "meals": meals,                           
            "ape_cal": ape_cal,
            "ape_p": ape_p,
            "ape_c": ape_c,
            "ape_f": ape_f,
            "constraint_score": constraint_score,
            "allergy_constraint_score": allergy_constraint_score,
            "dietary_constraint_score": dietary_constraint_score,
            "keyword_success": keyword_hit
        })

    except Exception as e:
        error_message = f"{type(e).__name__}: {e}"
        print(f"Error with User {data['id']}: {error_message}")
        failures.append({
            "id": data.get("id"),
            "meal_amount": data.get("meal_amount"),
            "macro_style": data.get("macro_style"),
            "text_input": data.get("text_input"),
            "error": error_message,
            "traceback": traceback.format_exc(),
        })


# Writing all generated plans to a JSON file for later analysis in the statistics script
if results:
    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=4)
    print(f"Saved {len(results)} generated plans to '{OUTPUT_JSON}'")

if failures:
    with open(FAILURES_JSON, "w") as f:
        json.dump(failures, f, indent=4)
    print(f"Saved {len(failures)} failed profiles to '{FAILURES_JSON}'")
else:
    if FAILURES_JSON.exists():
        FAILURES_JSON.unlink()
    
