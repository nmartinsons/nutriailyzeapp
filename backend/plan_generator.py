import os
import json
import copy
import requests
from dotenv import load_dotenv
from knn import KNN
import pandas as pd
from rules_engine import (
    calc_bmi, calc_bmr, calc_tdee, adjust_caloric_intake, 
    determine_weight_cat, distrib_of_cal_for_meals, is_senior, 
    calculate_daily_macros
)
from intent_parser import IntentParser
from db_access import fetch_all_data

# Loading Gemini API Key from .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# MealPlanGenerator Class for generating meal plans based on user profile and intent
class MealPlanGenerator:
    # Constructor initializes the generator with user profile, fetches data, and sets up KNN and Intent Parser
    def __init__(self, user_profile):
        self.user = user_profile
        self.k = 50  # Number of neighbors for KNN
        
        # 1. Fetching data using the fetch_all_data function, which takes care of Supabase connection and data retrieval
        raw_foods, raw_boosters = self._fetch_data()
        
        # 2. Converting to Pandas DataFrame if they are lists
        # This handles the AttributeError: 'list' object has no attribute 'columns'
        if isinstance(raw_foods, list):
            self.foods = pd.DataFrame(raw_foods)
        # If it's already a DataFrame, use it directly
        else:
            self.foods = raw_foods
        if isinstance(raw_boosters, list):
            self.boosters = pd.DataFrame(raw_boosters)
        else:
            self.boosters = raw_boosters
        
        # 3. Ensures 'name' is available as a column
        # This ensures that data frame contains 'name' column, which is crucial for KNN operations. If not, it resets index and renames if necessary.
        if 'name' not in self.foods.columns:
            self.foods = self.foods.reset_index()
            if 'name' not in self.foods.columns and 'index' in self.foods.columns:
                 self.foods = self.foods.rename(columns={'index': 'name'})

        if 'name' not in self.boosters.columns:
            self.boosters = self.boosters.reset_index()
            if 'name' not in self.boosters.columns and 'index' in self.boosters.columns:
                 self.boosters = self.boosters.rename(columns={'index': 'name'})

        # 4. Initializing KNN
        self.knn = KNN(self.foods, self.boosters, user_allergies=self.user.allergies, k=self.k)
        self.intent_parser = IntentParser()
        
    # Fetches data from the database using the fetch_all_data function defined in db_access.py. 
    def _fetch_data(self):
        return fetch_all_data()
    
    # Generates a raw meal plan based on user profile and intent. This is the core function that combines intent parsing, rules engine calculations, and KNN recommendations to create a meal plan.
    def generate_raw_plan(self):
        # 1. Parsing User Intent
        intent_config = self.intent_parser.parse(self.user.text_input)
        print(f"Intent Config: {json.dumps(intent_config, indent=2)}")

        # 2. Calculating Biometric Metrics
        tdee = calc_tdee(self.user)
        bmr = calc_bmr(self.user)
        bmi = calc_bmi(self.user)
        weight_cat = determine_weight_cat(bmi)
        
        # Extracting Intent Parameters
        macro_style = intent_config.get('macro_style')      
        goal_override = intent_config.get('goal_override')  
        pref_style = intent_config.get('preferred_style')
        
        # Get foods to avoid based on medical conditions, dislikes, and style preferences
        avoids = intent_config.get('avoid_keywords', [])
        if avoids is None: avoids = []
            
        # Focus ingredients are the specific foods that the user should prioritize based on their condition and goals. These will be given extra weight in the KNN algorithm to ensure they are included in the meal plan.
        focus_foods = intent_config.get('focus_ingredients', []) 

        # Applying Goal Overrides if specified in the intent. This allows the user to explicitly state a goal in their free-text input, which can override the default goal derived from their profile.
        effective_goal = goal_override if goal_override else self.user.goal.value
        # Adjusts the caloric intake based on the user's goal (lose, maintain, gain) and other factors. This is crucial for ensuring that the meal plan aligns with the user's objectives.
        daily_cals = adjust_caloric_intake(tdee, self.user, bmr, explicit_goal=effective_goal)
        
        # Calculating daily macronutrient targets based on the adjusted caloric intake, user profile, and intent parameters.
        is_sen = is_senior(self.user.age)
        daily_macros = calculate_daily_macros(
            daily_cals, 
            self.user, 
            explicit_goal=effective_goal, 
            is_senior=is_sen, 
            macro_style=macro_style
        )
        
        # Combining all the calculated and parsed information into a single configuration object that will be used for meal generation.
        daily_targets = {
            "calories": int(daily_cals),
            "protein": int(daily_macros["protein"]),
            "carbs": int(daily_macros["carbs"]),
            "fat": int(daily_macros["fat"])
        }
        
        # Adding these for KNN to use as features. This ensures that the KNN algorithm has access to the correct target values for protein, carbs, and fat when generating meal recommendations.
        daily_targets["protein, total (g)"] = daily_targets["protein"]
        daily_targets["carbohydrate, available (g)"] = daily_targets["carbs"]
        daily_targets["fat, total (g)"] = daily_targets["fat"]

        # Exclusion map for different macro styles. This is a critical part of the filtering logic that ensures the meal plan adheres to the user's dietary preferences and restrictions based on their chosen macro style.
        style_exclusion_map = {
            "vegan": [
                    # GENERAL ANIMAL PRODUCTS
                    "meat", "animal", "seafood", "fish", "dairy", "egg", 
                    "honey", "gelatin", "whey", "casein", "lactose", "albumin",
                    "steak", "fillet", "broth", "stock", "buttermilk",
                    "yolk", 
                    
                    # DAIRY & FATS
                    "milk", "cheese", "yoghurt", "yogurt", "cream", "butter", 
                    "ghee", "lard", "tallow", "ice cream", "custard", "pudding",
                    "mayonnaise", "mayo", "cottage", "curd", "" "sour cream", 
                    "kefir", "skyr", "quark", "creme", "latte", "cappuccino", "mocha",
                    "mousse", "cream cheese", "cheesy", "cheddar", "parmesan", "brie", "camembert",
                    "feata", "gouda", "swiss", "provolone", "ricotta", "monterey", "colby",

                    # POULTRY
                    "chicken", "turkey", "duck", "goose", "quail", "poultry", "wings",

                    # RED MEAT
                    "beef", "pork", "lamb", "veal", "venison", "goat", 
                    "rabbit", "reindeer", "mutton", "buffalo", "bison", "game",

                    # PROCESSED/CUTS
                    "ham", "bacon", "sausage", "steak", "salami", "pepperoni", 
                    "chorizo", "burger", "meatball", "liver", "kidney", "ribs", "chop",

                    # SEAFOOD/FISH
                    "salmon", "tuna", "trout", "cod", "herring", "sardine", 
                    "anchovy", "mackerel", "pollock", "haddock", "saithe", "eel", 
                    "snapper", "tilapia", "halibut", "flounder",

                    # SHELLFISH/MOLLUSKS
                    "shrimp", "prawn", "crab", "lobster", "crayfish", 
                    "mussel", "clam", "oyster", "scallop", "squid", 
                    "octopus", "calamari", "caviar", "roe", "sushi"
                ],
            "vegetarian": ["chicken", "beef", "pork", "meat", "fish", "seafood", "ham", "bacon", "sausage", "sausage", "turkey", "duck", "lamb", "veal", 
                           "venison", "goat", "rabbit", "mussel", "shrimp", "prawn", "crab", "lobster", "saithe", "anchovy", "caviar", "eel", "herring", 
                           "trout", "tuna", "salmon", "sardine", "squid", "octopus", "clam", "scallop", "steak", "reindeer"],
            "pescatarian": ["chicken", "beef", "pork", "meat", "ham", "bacon", "sausage", "turkey", "duck", "lamb", "veal", "venison", "goat", "rabbit",
                            "steak", "reindeer", "meatball", "burger", "chop", "liver", "kidney", "ribs", "salami", "pepperoni", "chorizo"],
            "heart_healthy": ["fried", "fatty", "saturated", "processed", "sugar", "syrup", "honey", "salty", "salted", "bacon", "sausage", "ham", "salami", "pepperoni", "chorizo"],
            "diabetic_friendly": [
                "sugar", "syrup", "honey", "juice", "soda", "cake", "cookie", 
                "sweet", "chocolate", "jam", "white bread", "white rice",
                "smoothie", "fruit_drink", "nectar", "dried fruit", "candy", "pie", "pastry", "custard",
                "ice cream", "pudding", "muffin", "biscuit", "donut", "waffle", "pancake", "crepe",
                "sugary"
            ],
            "low_carb": [
                "rice", "pasta", "bread", "sugar", "smoothie", "juice", "macaroni",
                "cake", "cookie", "potato", "starch", "cereal", "flour", "banana", "grape",
                "wheat", "grain", "oat", "corn", "flake", "maize", "gruel", "couscous", "semolina",
                "pastry", "pie", "bun", "roll", "custard", "honey", "syrup", "jam", "jelly",
                "buckwheat", "noodle", "spaghetti", "lasagna", "dumpling", "tortilla", "pizza"
            ],
            "keto": [
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

        # If a macro style is specified and it has associated exclusions, add those to the avoids list. This ensures that the meal plan generation process takes into account the user's chosen dietary style and filters out foods accordingly.
        if macro_style and macro_style in style_exclusion_map:
            print(f"Applying filters for style: {macro_style}") 
            avoids.extend(style_exclusion_map[macro_style])

        # List to hold expanded avoids. This will include the original avoids plus any semantically related terms that should also be excluded based on the user's intent.
        expanded_avoids = []
        
        # For loop to expand the avoids list with semantic expansions.
        for word in avoids:
            # This helps to ensure that the filtering is case-insensitive and doesn't have issues with extra spaces.
            word = word.lower().strip()
            # If the word is empty after stripping, skip it to avoid adding empty strings to the avoids list.
            if not word: continue
            
            # Appending the original word to the expanded avoids list. This ensures that the explicitly mentioned foods are always included in the avoids.
            expanded_avoids.append(word) 
            
            # This check is a simple heuristic to catch plural forms. If the word ends with 's' and is longer than 3 characters (to avoid short words like "is", "as"), it adds the singular form to the avoids list. 
            # For instance, this helps to catch both "nut" and "nuts".
            if word.endswith('s') and len(word) > 3:
                expanded_avoids.append(word[:-1])

            # This section expands the avoids list based on common categories. For example, if the user says "dairy", it adds a comprehensive list of dairy-related foods to the avoids.
            if any(k in word for k in ["dairy", "lactose", "milk", "cheese", "cream", "yogurt"]):
                expanded_avoids.extend([
                    "milk", "cheese", "yoghurt", "yogurt", "cream", "curd", 
                    "kefir", "butter", "whey", "casein", "skyr", "quark", 
                    "sour milk", "buttermilk", "creme", "ice cream", "custard", 
                    "latte", "cappuccino", "mousse", "pudding"
                ])
            elif "nut" in word: # Matches "nuts", "peanut", "walnut"
                expanded_avoids.extend([
                    "nut", "nuts", "almond", "cashew", "walnut", "pecan", "peanut", 
                    "hazelnut", "pistachio", "macadamia", "chestnut", "pine nut", 
                    "kernel", "nut butter"
                ])
            elif "gluten" in word or "bread" in word:
                expanded_avoids.extend([
                    "wheat", "rye", "barley", "bread", "pasta", "flour", 
                    "cake", "cookie", "biscuit", "spaghetti", "macaroni", "cereal", 
                    "bran", "roll", "bun", "baguette", "toast", "croissant", "pastry", "pie",
                    "muffin", "scone", "dough", "noodle", "lasagna", "tortilla", "pizza",
                    "crumb", "crust", "cracker"
                ])
            elif "fruit" in word: 
                expanded_avoids.extend([
                    "apple", "banana", "orange", "pear", "grape", "mango", "pineapple",
                    "fruit", "fruits", "juice", "smoothie", "nectar", "date", "fig", "raisin", "prune",
                    "berry", "berries", "kiwi", "peach", "plum", "cherry", "apricot", "citrus",
                    "melon", "watermelon", "papaya", "pomegranate"
                    
                ])
            elif "grain" in word or "starch" in word or "cereal" in word: 
                expanded_avoids.extend([
                    "rice", "oat", "corn", "maize", "millet", "quinoa", "buckwheat",
                    "couscous", "bulgur", "semolina", "sorghum", "amaranth", "teff",
                    "cereal", "muesli", "granola", "porridge", "gruel", "flake", "bran",
                    "starch", "starchy", "potato", "sweet potato"
                ])

        final_avoids = list(set(expanded_avoids))

        # Adding style-based craving keywords. This helps to ensure that the meal plan not only avoids certain foods but also includes foods that align with the user's preferred style, making the recommendations more appealing and personalized.
        vibe_keywords = []
        if pref_style:
            style_map = {
                "spicy": ["chili", "pepper", "curry", "hot", "spicy", "mexican", "thai", "indian", "salsa", "jalapeno"],
                "comfort": ["stew", "soup", "casserole", "mash", "porridge", "warm", "baked", "roast", "gravy", "pie", "pasta", "lasagna"],
                "simple": ["raw", "salad", "fruit", "nut", "steak", "fillet", "boiled", "grilled", "egg", "toast"],
                "quick": ["salad", "smoothie", "sandwich", "canned", "ready", "frozen", "powder", "toast", "wrap"],
                "cold": ["salad", "raw", "smoothie", "sandwich", "cold", "yoghurt", "cottage cheese", "milk", "curd", "kefir"],
                "raw": ["salad", "raw", "fruit", "nut", "smoothie", "sushi", "carpaccio"]
            }
            vibe_keywords = style_map.get(pref_style.lower(), [])
            
        # This section adds staple foods for specific macro styles to the focus ingredients list.
        if macro_style == 'keto':
            keto_staples = [
                "salmon", "pork", "beef mince", "fatty fish", "avocado", 
                "egg", "olive oil", "coconut oil", "bacon", "sausage", "duck",
                "ground beef", "ribeye", "thigh", "beef", "chicken thigh", "chicken breast",
                "sardines", "avocado", "mackerel", "nut", "seeds", "cheese", "butter",
                "7%", "5%", "10%", "cheese", "lentils", "spinach", "broccoli", "cauliflower", "zucchini"
            ]
            # Add these to focus foods so KNN prioritizes them
            focus_foods.extend(keto_staples)
            
        user_cravings = intent_config.get('include_keywords', []) + vibe_keywords
        ai_focus_foods = intent_config.get('focus_ingredients', [])

        # Generates the initial meal structure with target macros for each meal slot. This is where the rules engine comes into play to determine how to distribute calories and macros across meals based on the user's profile and intent.
        structure = distrib_of_cal_for_meals(
            daily_cals, 
            self.user.meal_amount, 
            self.user,
            explicit_goal=effective_goal, 
            is_senior=is_sen,
            macro_style=macro_style
        )
        
        # Raw plan list that will hold the initial meal recommendations before scaling and rescue operations. This is the core output of the KNN-based meal generation process, which will later be refined to better meet the user's daily targets.
        raw_plan_list = []
        # List for tracking foods used in the current day's plan to avoid repetition.
        daily_used_foods = [] 
        
        # KETO MODE: Boost fat targets for initial meal selection
        is_keto = macro_style == 'keto'
        if is_keto:
            print("Keto Mode: Increasing fat allocation for meal selection")
            # Increase fat target for each meal by 20%
            for slot in structure:
                # Helps to choose meals that are more likely to be higher in fat, which is crucial for a ketogenic diet.
                slot['target_macros']['fat'] = int(slot['target_macros'].get('fat', 0) * 1.2)
                slot['target_macros']['fat, total (g)'] = slot['target_macros']['fat']

        def _find_emergency_option(target_macros: dict):
            emergency_options = self.knn.find_single_food(
                target_macros,
                meal_type="snack",
                only_healthy=False,
                ignore_names=[],
                ignore_keywords=None,
                include_keywords=None,
                craving_keywords=None,
            )
            if emergency_options:
                return emergency_options

            return self.knn.find_composite_meal(
                target_macros,
                meal_type="lunch",
                only_healthy=False,
                ignore_names=[],
                ignore_keywords=None,
                include_keywords=None,
                craving_keywords=None,
            )
                
        for slot in structure:
            meal_name = slot['meal_name'].lower()
            target = slot['target_macros']
            
            # Ensures calories are included in the target macros for KNN. 
            # This is important because the KNN algorithm uses calories as a key feature for finding similar meals, and having it explicitly in the target ensures that the recommendations are aligned with the user's caloric needs.
            if 'calories' not in target: 
                target['calories'] = slot['calories']
            
            # Adding these for KNN to use as features. 
            # This ensures that the KNN algorithm has access to the correct target values for protein, carbs, and fat when generating meal recommendations.
            target["protein, total (g)"] = target.get("protein", 0)
            target["carbohydrate, available (g)"] = target.get("carbs", 0)
            target["fat, total (g)"] = target.get("fat", 0)

            # Determines whether to search for a composite meal (like a full lunch or dinner) or a single food item (like a snack) based on the meal name.
            if "lunch" in meal_name or "dinner" in meal_name or "breakfast" in meal_name:
                current_type = "breakfast" if "breakfast" in meal_name else "lunch"
                composite_attempts = [
                    {
                        "stage": "strict",
                        "only_healthy": True,
                        "ignore_names": daily_used_foods,
                        "ignore_keywords": final_avoids,
                        "include_keywords": ai_focus_foods,
                        "craving_keywords": user_cravings,
                    },
                    {
                        "stage": "allow_repeats",
                        "only_healthy": True,
                        "ignore_names": [],
                        "ignore_keywords": final_avoids,
                        "include_keywords": ai_focus_foods,
                        "craving_keywords": user_cravings,
                    },
                    {
                        "stage": "relax_health",
                        "only_healthy": False,
                        "ignore_names": [],
                        "ignore_keywords": final_avoids,
                        "include_keywords": ai_focus_foods,
                        "craving_keywords": user_cravings,
                    },
                    {
                        "stage": "general_fallback",
                        "only_healthy": False,
                        "ignore_names": [],
                        "ignore_keywords": final_avoids,
                        "include_keywords": None,
                        "craving_keywords": None,
                    },
                ]

                options = []
                for attempt in composite_attempts:
                    options = self.knn.find_composite_meal(
                        target,
                        meal_type=current_type,
                        only_healthy=attempt["only_healthy"],
                        ignore_names=attempt["ignore_names"],
                        ignore_keywords=attempt["ignore_keywords"],
                        include_keywords=attempt["include_keywords"],
                        craving_keywords=attempt["craving_keywords"],
                    )
                    if options:
                        break
            else:
                single_attempts = [
                    {
                        "stage": "strict",
                        "only_healthy": True,
                        "ignore_names": daily_used_foods,
                        "ignore_keywords": final_avoids,
                        "include_keywords": ai_focus_foods,
                        "craving_keywords": user_cravings,
                    },
                    {
                        "stage": "allow_repeats",
                        "only_healthy": True,
                        "ignore_names": [],
                        "ignore_keywords": final_avoids,
                        "include_keywords": ai_focus_foods,
                        "craving_keywords": user_cravings,
                    },
                    {
                        "stage": "relax_health",
                        "only_healthy": False,
                        "ignore_names": [],
                        "ignore_keywords": final_avoids,
                        "include_keywords": ai_focus_foods,
                        "craving_keywords": user_cravings,
                    },
                    {
                        "stage": "general_fallback",
                        "only_healthy": False,
                        "ignore_names": [],
                        "ignore_keywords": final_avoids,
                        "include_keywords": None,
                        "craving_keywords": None,
                    },
                ]

                options = []
                for attempt in single_attempts:
                    options = self.knn.find_single_food(
                        target,
                        meal_type="snack",
                        only_healthy=attempt["only_healthy"],
                        ignore_names=attempt["ignore_names"],
                        ignore_keywords=attempt["ignore_keywords"],
                        include_keywords=attempt["include_keywords"],
                        craving_keywords=attempt["craving_keywords"],
                    )
                    if options:
                        break

            if not options:
                print(f"KNN fallback exhausted for user {self.user.id}, slot '{slot['meal_name']}'. Trying emergency search.")
                options = _find_emergency_option(target)

            if not options and raw_plan_list:
                print(f"No emergency option for user {self.user.id}, slot '{slot['meal_name']}'. Reusing previous meal.")
                options = [copy.deepcopy(raw_plan_list[-1]['food_data'])]
            
            if options:
                # Rotation Selection
                # This allows to cycle through the top recommendations in a deterministic way based on the user's generation index, which helps to provide variety in the meal plans while still being consistent for the user.
                current_seed = self.user.generation_index # This is the number of times the user has generated a plan, which we can use to rotate through options. # It increases by +1 every time they request a new plan.
                top_n = 3 # Considers only the top 3 options for rotation
                count = len(options) # How many options did KNN find
                selection_index = current_seed % min(count, top_n)
                selected_meal = options[selection_index]
                
                # Add to blacklist
                for key in ['main_dish', 'side_dish', 'soup', 'drink']:
                    if key in selected_meal and selected_meal[key]:
                        name = selected_meal[key]['name']
                        daily_used_foods.append(name)
                        daily_used_foods.append(name.strip().lower())

                raw_plan_list.append({
                    "slot_name": slot['meal_name'], # e.g., "Lunch"
                    "target_macros": target, # What we aimed for 
                    "food_data": selected_meal # What we actually picked (The food object)
                })
            else:
                print(f"WARNING: Could not fill slot '{slot['meal_name']}' for user {self.user.id}.")
        
        # This line extracts just the food data from the raw plan list to prepare for the rescue operations. The rescue functions will modify this list in place to adjust the meals to better meet the daily targets, while respecting the avoid keywords.
        meals_only = [m['food_data'] for m in raw_plan_list]
        
        # Protein rescue
        meals = self.knn.rescue_protein_deficit(meals_only, daily_targets, ignore_keywords=final_avoids)
        
        if is_keto:
            print("Keto Mode: Aggressive fat rescue (targeting 95% of goal)")
            # Copying daily targets to modify fat target for keto rescue without affecting the original targets used for other rescues and scaling. 
            # This allows us to have a more aggressive fat rescue strategy specifically for keto diets, while still using the original targets for protein and carb rescues.
            keto_fat_target = daily_targets.copy()
            # Creating a strict target: Must reach at least 95% of the total fat goal
            keto_fat_target['fat, total (g)'] = int(daily_targets['fat, total (g)'] * 0.95)
            meals = self.knn.rescue_fat_deficit(meals, keto_fat_target, ignore_keywords=final_avoids)
        else:
            # Other diets: Standard fat rescue targeting 100% of the goal
            meals = self.knn.rescue_fat_deficit(meals, daily_targets, ignore_keywords=final_avoids)
        
        # Carb rescue
        meals = self.knn.rescue_carb_deficit(meals, daily_targets, ignore_keywords=final_avoids)
        # Global scaling to hit calorie target while respecting the macro ratios as much as possible. 
        # This is the final step to ensure that the meal plan meets the user's daily caloric needs while still adhering to the desired macro distribution, and it takes into account all the adjustments made during the rescue operations.
        meals = self.knn.scale_meals_globally(meals, daily_targets)
        
        # To see the final list of avoid keywords after all expansions and style-based additions (for debudging purposes). 
        print("Final avoid keywords:", final_avoids)
        
        # Updating the raw plan list with the final scaled meals after all rescue operations. This ensures that the meal data in the final output reflects all the adjustments made to meet the user's targets and preferences.
        for i, scaled_meal in enumerate(meals_only):
            raw_plan_list[i]['food_data'] = scaled_meal
            
        return {
            "daily_targets": daily_targets,
            "meals": raw_plan_list
        }
    
    # Function to enrich the raw meal plan data using Gemini API. This function sends the raw plan data to Gemini with a detailed prompt and expects a structured JSON response that includes culinary names, meal components, and health tips.
    def enrich_with_gemini(self, raw_plan_data):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}

        plan_str = json.dumps(raw_plan_data, indent=2)
        targets = raw_plan_data['daily_targets']

        prompt = f"""
        You are a professional nutritionist API. 
        Convert the raw meal plan below into a structured JSON response.

        RULES:
        1. Keep grams exactly as provided.
        2. Rename foods to be culinary/appetizing.
        3. Identify components (Main, Side, Soup, Drink, Booster).
        4. Add a short "health_tip" explaining why this meal fits the goal.

        INPUT DATA:
        {plan_str}

        OUTPUT SCHEMA:
        {{
            "daily_summary": "A 2-sentence summary of how this plan meets the {self.user.goal.name} goal.",
            "daily_targets": {{
                "calories": {targets['calories']},
                "protein": {targets['protein']},
                "carbs": {targets['carbs']},
                "fat": {targets['fat']}
            }},
            "meals": [
                {{
                    "title": "Lunch",
                    "display_name": "Chicken & Rice",
                    "total_calories": 800,
                    "ingredients": [
                        {{ "name": "Grilled Chicken", "amount": "150g", "type": "Main" }}
                    ],
                    "macros": {{ "protein": 40, "carbs": 60, "fat": 20 }},
                    "health_tip": "..."
                }}
            ]
        }}
        """

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                return json.loads(response.json()['candidates'][0]['content']['parts'][0]['text'])
            else:
                print(f"Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Exception: {e}")
            return None

