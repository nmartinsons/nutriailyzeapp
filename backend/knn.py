import pandas as pd
from sklearn.neighbors import NearestNeighbors
from rules_engine import is_safe_to_eat

class KNN:
    # Constructor. Constructor is called when an instance of the class is created.
    # Why constructor is used? It is used because it initializes the object's attributes and sets up the initial state of the object.
    def __init__(self, food_data: list[dict], boosters_data: list[dict], user_allergies: list[str], k=50):
        self.k = k # Number of neighbors
        self.df = pd.DataFrame(food_data) # Main food items loaded into a DataFrame
        self.boosters_df = pd.DataFrame(boosters_data) # Health boosters loaded into a DataFrame
        
        # Define explicit column names to ensure consistency
        self.COL_PROTEIN = "protein, total (g)"
        self.COL_CARBS = "carbohydrate, available (g)"
        self.COL_FAT = "fat, total (g)"
        
        # The AI will look at these 3 numbers to decide what is "close" to your goal.
        self.features = [self.COL_PROTEIN, self.COL_CARBS, self.COL_FAT]
        
        # Max portion sizes to avoid unrealistic servings
        self.PORTION_CAPS = {
            "liquid": 500.0, # Drinks like smoothies, kefir, juices, milk
            "soup": 400.0, 
            "bakery": 100.0, # Breads, crackers, pastries (usually eaten in smaller portions)
            "starch": 300.0, # Rice/Pasta
            "meat": 370.0, # Meat/Fish
            "vegetarian": 400.0, # Veg protein like tofu, seitan, tempeh and other vegetarian foods like legumes
            "veg": 400.0, # Vegetables like broccoli, spinach, carrots   
            "supplement": 80.0, # Protein powders and other supplements are usually taken in small amounts 
            "cheese": 120.0, # These include dense, fatty cheeses like halloumi, feta, mozzarella
            "nut": 80.0, # Nuts like almonds, walnuts, cashews
            "sauce": 100.0, # Sauces and dressings are usually used in small amounts due to high calorie density
            "solid_default": 400.0 # This is the default cap for any solid food that doesn't fit the above categories.
        }
        
        self.VEG_KEYWORDS = [
            'salad','lettuce','spinach','arugula','rocket','kale',
            'cucumber','tomato','pepper','bell pepper','chili','radish',
            'carrot','celery',
            'broccoli','cauliflower','cabbage',
            'zucchini','courgette','squash','eggplant','aubergine',
            'onion','shallot','leek','garlic','scallion','spring onion',
            'mushroom','shiitake',
            'beet','beetroot','turnip','parsnip',
            'pea','green bean','snap pea',
            'corn','sweetcorn',
            'asparagus','artichoke','fennel',
            'avocado',
            'collard','radicchio'
        ]
        
        self.BAD_VEG_WORDS = [
            'casserole','pancake','stew','pie','soup','fried',
            'gratin','roast','bake','saute','steam','canned'
        ]
        
        self.BREAKFAST_ONLY_AND_SNACK_WORDS = [
            'porridge', 'oat', 'oatmeal', 'gruel', 'muesli', 'granola', 
            'cereal', 'cornflakes', 'puffs', 'bran', 'wheat'
        ]
        
        self.DAIRY_KEYWORDS = ['milk', 'yogurt', 'yoghurt', 'kefir', 'curd', 'quark']
        
        self.DAIRY_EXCLUSIONS = ['powder', 'condensed', 'evaporated', 'chocolate', 'juice', 'flavored', 'flavoured', 'cafe', 'coffee', 'latte', 'berry', 'fruit', 'soup', 'stew', 'water', 'sauce', 'dressing', 'sweetened']
        
        self.BERRY_KEYWORDS = [
            'berry', 'berries', 'strawberry', 'blueberry', 'raspberry', 
            'blackberry', 'cranberry', 'lingonberry', 'cloudberry', 
            'gooseberry', 'currant'
        ]
        
        self.FRUIT_KEYWORDS = [
            'fruit', 'mango', 'grape', 'apple', 'pear', 'banana', 
            'fig', 'prune', 'date', 'cherry', 'papaya', 'pineapple', 
            'dried', 'raisin', 'plum', 'kiwi', 'peach', 'apricot', 
            'melon', 'orange'
        ]
        
        self.BOOSTER_EXCLUSIONS = [
            'juice', 'drink', 'soup', 'puree', 'powder', 'flour', 
            'nectar', 'syrup', 'smoothie', 'concentrate', 'basil', 
            'herb', 'spice', 'sweetened'
        ]
        
        self.CRUNCH_KEYWORDS = [
            'seed', 'nut', 'granola', 'muesli', 'cacao', 'chia', 
            'flax', 'hemp', 'almond', 'walnut', 'cashew', 'honey',
            'pecan', 'pistachio', 'sunflower', 'sesame'
        ]
        
        self.SALAD_KEYWORDS = [
            'salad', 'lettuce', 'cucumber', 'tomato', 'vegetable', 
            'spinach', 'kale', 'arugula', 'rocket', 'carrot', 'pepper', 
            'broccoli', 'cauliflower', 'cabbage', 'asparagus', 'zucchini','squash'
        ]
        
        self.CHEESE_KEYWORDS = ['halloumi', 'feta', 'mozzarella', 'cheese', 'tofu']
        
        self.MUESLI_KEYWORDS = ['muesli', 'granola', 'cereal', 'oat', 'oatmeal', 'bran', 'flakes', 'puffs']
        
        self.MAIN_CATEGORIES = ['main_dish', 'side_dish', 'soup', 'drink']
        
        self.SWEET_KEYWORDS = ['yogurt', 'yoghurt', 'porridge', 'oat', 'curd', 'cottage', 'quark', 'pancake', 'waffle', 'crepe']
        
        self.COOKED_VEG_KEYWORDS = ['mash', 'boil', 'root', 'swede', 'stew', 'fried', 'wok', 'bake', 'roast', 'saute', 'casserole', 'canned']
        
        self.LIQUID_EXCLUSIONS = ['oil', 'sauce', 'dressing', 'soup', 'broth', 'water', 'coffee', 'tea', 'alcohol', 'sweetened', 'sugar', 'gravy', 'wine', 'sweetened']
        
        self.PROTEIN_SUPPLEMENT_KEYWORDS = ['whey', 'casein', 'protein powder', 'isolate', 'soy protein', 'pea protein']
        
        self.ALLOWED_PROCESSING_LEVELS = ['unprocessed', 'processed']
        
        self.ALCOHOL_KEYWORDS = [
                'wine', 'beer', 'cider', 'alcohol', 'liqueur', 
                'vodka', 'gin', 'rum', 'whisky', 'brandy', 
                'champagne', 'cocktail', 'spirit', 'schnapps'
        ]
        
        self.MILK_SUBSTITUTES = ['soy', 'almond', 'oat', 'rice', 'coconut', 'cashew', 'pea']
        
        self.NON_MEAL_DRINKS = [
            'coffee', 'tea', 'water', 'espresso', 'americano', 'infusion', 
            'beverage'
        ]
        
        # Foods that are strong/salty and need a base (Bread/Cracker)
        self.INTENSE_TOPPINGS = [
            'anchovy', 'anchovies', 'sardine', 'sprat', 'herring', 
            'smoked salmon', 'gravlax', 'cold smoked', 
            'salami', 'prosciutto', 'ham', 'cured', 
            'blue cheese', 'brie', 'camembert', 'feta', 'goat cheese',
            'hummus', 'houmous', 'tzatziki', 'pesto', 'guacamole', 
        ]
        
        # Neutral bases to pair with intense foods
        self.NEUTRAL_BASES = [
            'bread', 'rye bread', 'toast', 'cracker', 'crispbread', 
            'baguette', 'roll', 'bun', 'rice cake', 'pita', 'flatbread'
        ]
        
        self.DIP_BASES = [
            'carrot', 'celery', 'cucumber', 'bell pepper', 'pepper', 'tomato', 'radish', 'snap pea', 'broccoli'
        ]
        
        self.BREAD_KEYWORDS = [
            'bread', 'rye', 'wheat', 'sourdough', 'baguette', 
            'toast', 'bun', 'roll', 'cracker', 'flatbread', 
            'pita', 'ciabatta', 'focaccia', 'brioche'
        ]
        
        self.CARB_BOOST_KEYWORDS = [
            # Grains & starches
            'bread', 'pasta', 'rice', 'potato', 'quinoa', 
            'couscous', 'noodle', 'tortilla', 'wrap', 'oat', 'oatmeal',
            'barley', 'farro', 'buckwheat', 'bulgur', 'millet', 'rye',
            'toast', 'sandwich', 'flatbread'

            # Legumes (complex carbs + protein)
            'lentils', 'chickpeas', 'beans', 'black beans', 'kidney beans', 'navy beans', 'pinto beans', 'edamame', 'peas', 'couscous',
            'quinoa', 'hummus'

            # Fruits & berries
            'apple', 'banana', 'orange', 'pear', 'peach', 'plum', 'grape', 'mango', 'pineapple', 'kiwi', 'apricot',
            'strawberry', 'blueberry', 'raspberry', 'blackberry', 'cranberry', 'gooseberry', 'mulberry', 'date', 'fig',
            'mandarin', 'watermelon', 'cantaloupe', 'honeydew'

            # Other complex carbs
            'sweet potato', 'corn', 'pumpkin', 'squash'
        ]
        
        self.HEALTHY_CREAMY_KEYWORDS = [
            'avocado', 'butter', 'cream', 'yogurt', 'yoghurt', 'curd', 'cottage', 'quark', 'sour cream','hummus', 'guacamole', 'tzatziki', 'ghee', 'paste' 
        ]
        
        self.DIP_KEYWORDS = ['hummus', 'tzatziki', 'guacamole', 'pesto', 'salsa', 'bean dip', 'miso paste', 'sour cream', 'yogurt dip', 'sour cream']
        
        self.SAVORY_EXCLUDE_FOR_BREAKFAST = [
                'noodle', 'rice', 'pasta', 'potato', 'spaghetti', 'macaroni', 
                'couscous', 'soup', 'stew', 'sauce', 'curry'
        ]
    
        # Allergy filtering logic
        # The dataframes are filtered immediately so the AI never sees unsafe food.
        if user_allergies:
            # 1. Filtering Main Foods
            # Using lambda to apply rules engine function to every row because it allows for complex logic that can consider multiple columns (e.g. name, category, sub_category) when determining if a food is safe for the user.
            if not self.df.empty:
                # axis=1 ensures the function is applied to each row, not column. The function returns True/False for each row, creating a boolean mask that filters the DataFrame to only include safe foods.
                mask = self.df.apply(lambda row: is_safe_to_eat(user_allergies, row), axis=1)
                # Boolean indexing to filter the DataFrame based on the mask. Only rows where the mask is True (safe to eat) are kept. 
                # reset_index(drop=True) is used to reset the index of the resulting DataFrame after filtering, which is important for maintaining a clean and consistent index.
                self.df = self.df[mask].reset_index(drop=True)
            
            # 2. Filtering Boosters (Same logic as in Main Foods)
            if not self.boosters_df.empty:
                mask_boosters = self.boosters_df.apply(lambda row: is_safe_to_eat(user_allergies, row), axis=1)
                self.boosters_df = self.boosters_df[mask_boosters].reset_index(drop=True)
        
                       
        # Data Cleaning for Main Foods
        if not self.df.empty:
            # 1. Fixing Numbers. This ensures protein/carb/fat are numbers (float), not text.
            # If a value is missing or broken, it is turned into 0.0.
            for col in self.features:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0.0)
            # If energy_kcal is missing, we calculate it using the formula.
            if 'energy_kcal' not in self.df.columns:
                self.df['energy_kcal'] = (self.df[self.features[0]] * 4) + (self.df[self.features[1]] * 4) + (self.df[self.features[2]] * 9)
            
            # 2. Fixing Text Tags. Ensuring that categories exist.
            text_cols = ['category', 'sub_category', 'processing_level', 'pairing_tag']
            for col in text_cols:
                # If column is missing in DB, it is created with a default value
                if col not in self.df.columns:
                    default = 'none' if col == 'pairing_tag' else 'generic'
                    if col == 'processing_level': 
                        default = 'processed'
                    self.df[col] = default # Creates the column and fills all rows with the chosen default value.
                # Replaces missing values with default and makes all text lowercase for consistency
                self.df[col] = self.df[col].fillna('none' if col == 'pairing_tag' else 'generic').astype(str).str.lower()
            
            # 3. Checks if the column is missing from the DataFrame. If missing, it creates it and fills with False.
            # Ensures 'is_liquid' is True/False, not Null.
            if 'is_liquid' not in self.df.columns: self.df['is_liquid'] = False
            self.df['is_liquid'] = self.df['is_liquid'].fillna(False)
            # 4. Checks if the column is missing from the DataFrame. If missing, it creates it and fills with False.
            if 'is_breakfast' not in self.df.columns: self.df['is_breakfast'] = False
            self.df['is_breakfast'] = self.df['is_breakfast'].fillna(False)
        # If the DataFrame is empty, we still want to have the expected columns for consistency, even if they are filled with default values. 
        # This prevents errors later when the AI tries to access these columns.
        else:
            self.df = pd.DataFrame()
         
        # Data Cleaning for Boosters   
        if not self.boosters_df.empty:
            # Loops over the feature columns and ensures they are numeric
            for col in self.features:
                if col in self.boosters_df.columns: # Ensures the column exists in boosters_df before modifying it 
                    # Converts values to numbers (float). Invalid entries like NaN become NaN and are then filled with 0.0
                    self.boosters_df[col] = pd.to_numeric(self.boosters_df[col], errors='coerce').fillna(0.0)
    
    # This function is used to filter a DataFrame based on a list of keywords that should be excluded. It checks if any of the exclude_keywords are present in the 'name' column of the DataFrame and filters out those rows.
    def _filter_by_keywords(self, df, exclude_keywords):
        if not exclude_keywords:
            return df
        # Converts exclude_keywords to lowercase for case-insensitive matching.
        exclude_keywords = [k.lower() for k in exclude_keywords]
        # Creates a boolean mask where True means the row does NOT contain any of the exclude_keywords in its 'name' column. The lambda function checks each name against all exclude_keywords and returns True if none of them are found.
        # The tilde (~) operator is used to invert the boolean values, so True becomes False and vice versa.
        mask = ~df['name'].str.lower().apply(
            lambda name: any(ex_kw in name for ex_kw in exclude_keywords)
        )
        # Returns a filtered DataFrame containing only rows where the mask is True, meaning they do not contain any of the exclude_keywords in their 'name'.
        return df[mask]
    
    # Helper function to determine if a food is in a sweet context that would benefit from berries/fruits. It checks if the main dish or side dish contains keywords associated with sweet foods like yogurt, porridge, oats, etc. 
    # If either the main dish or side dish contains any of these sweet keywords, it returns True, indicating that adding berries or fruits would be a good idea to enhance the flavor and nutritional profile of the meal.   
    def _is_sweet_context(self, main_name: str, side_name: str = "") -> bool:
        sweet_keywords = self.SWEET_KEYWORDS
        
        return any(kw in main_name for kw in sweet_keywords) or \
            any(kw in side_name for kw in sweet_keywords) 
    
    # Helper function to find a dairy or milk substitute to pair with cereals. 
    # It looks for items that contain keywords like "milk", "yogurt", "kefir", etc., and are liquids with allowed processing levels. 
    # It also applies exclusions to avoid items that are not suitable (e.g. flavored, sweetened, powdered). 
    # If multiple candidates are found, it randomly samples one to add variety.
    def _find_dairy_for_cereal(self, ignore_keywords = None) -> dict | None:
        all_keywords = self.DAIRY_KEYWORDS + self.MILK_SUBSTITUTES
        current_exclusions = self.DAIRY_EXCLUSIONS.copy()

        # If user has specified additional keywords to ignore (e.g. "milk"), we add those to the current exclusions list. 
        # This allows for dynamic filtering based on user preferences or dietary restrictions.
        if ignore_keywords:
            current_exclusions.extend([k.lower() for k in ignore_keywords])

        # Create base mask without exclusions
        mask = (
            (self.df['name'].str.contains('|'.join(all_keywords), case=False, regex=True)) &
            (self.df['is_liquid'] == True) & 
            (self.df['processing_level'].isin(self.ALLOWED_PROCESSING_LEVELS))
        )
        # Apply keyword exclusions to filter out unwanted items. 
        candidates = self.df[mask]
        # This function call further filters the candidates DataFrame by removing any items that contain keywords in the current_exclusions list. 
        candidates = self._filter_by_keywords(candidates, current_exclusions)
        
        # If no candidates remain after filtering, we return None, indicating that there are no suitable dairy or milk substitutes available for pairing with cereals.
        if candidates.empty:
            return None
            
        # Random sample to give variety
        # iloc[0] is used to get the first row of the sampled DataFrame, which is then converted to a dictionary. 
        # This allows us to return a single food item as a dictionary containing all its attributes, which can be easily used for further processing or display.
        return candidates.sample(1).iloc[0].to_dict()
    
    # This helper function is used to add a booster food item to the list of boosters being added to the meal. 
    # It takes care of calculating the correct portion size (in grams) based on the target macros and the nutritional profile of the booster food.
    def _add_booster(self, boosters_added: list, booster_food: dict, grams: float, reason: str) -> None:
        # The scalar is calculated to determine how much of the booster food to add based on the target grams because the nutritional information is typically given per 100 grams. 
        # By dividing the desired grams by 100, we get a scaling factor that can be applied to the protein, carbs, and fat values of the booster food to calculate the actual macros contributed by the portion being added to the meal. 
        scalar = grams / 100.0
        
        # Appends a dictionary representing the booster food to the boosters_added list. 
        boosters_added.append({
            "name": booster_food['name'],
            "grams": grams,
            "reason": reason,
            "macros": {
                "p": round(booster_food.get(self.COL_PROTEIN, 0) * scalar, 1),
                "c": round(booster_food.get(self.COL_CARBS, 0) * scalar, 1),
                "f": round(booster_food.get(self.COL_FAT, 0) * scalar, 1)
            },
            "full_profile": booster_food
        })
    
    # Helper function to determine if two foods are similar enough that they shouldn't be paired together for variety.    
    def _foods_are_similar(self, food1_name: str, food2_name: str) -> bool:
        name1 = food1_name.lower()
        name2 = food2_name.lower()
        
        # Exact match
        if name1 == name2:
            return True
        
        # Direct substring match (e.g. "chicken breast" vs "chicken")
        food_families = [
            # Dairy family
            ['curd milk', 'curd', 'quark'],
            ['yogurt', 'yoghurt', 'skyr'],
            ['cottage cheese', 'ricotta'],
            ['greek yogurt', 'greek yoghurt'],
            
            # Meat family
            ['chicken breast', 'chicken'],
            ['chicken thigh', 'chicken'],
            ['beef mince', 'ground beef', 'beef'],
            ['pork chop', 'pork'],
            ['ham', 'cooked ham'],
            
            # Fish family
            ['salmon', 'smoked salmon'],
            ['tuna', 'canned tuna'],
            ['cod', 'white fish'],
            
            # Grain family
            ['oat porridge', 'oatmeal', 'oat flakes'],
            ['rice porridge', 'rice gruel'],
            ['rice', 'brown rice', 'white rice', 'basmati rice', 'jasmine rice'],
            ['pasta', 'spaghetti', 'penne', 'macaroni'],
            ['bread', 'rye bread', 'wheat bread', 'sourdough bread'],
            ['cracker', 'crispbread'],
            ['tortilla', 'wrap', 'flatbread'],
            
            # Veg family
            ['potato', 'sweet potato', 'yam'],
            ['lettuce', 'iceberg lettuce', 'romaine'],
            ['cabbage', 'red cabbage', 'white cabbage'],
            ['spinach', 'baby spinach'],
            ['kale', 'curly kale'],
            ['broccoli', 'broccolini'],
            
            # Nut family
            ['almond', 'almonds'],
            ['walnut', 'walnuts'],
            ['peanut', 'peanuts'],
            ['cashew', 'cashews'],
            ['pecan', 'pecans'],
            
            #Coffee/Tee family
            ['coffee', 'espresso', 'latte', 'cappuccino'],
            ['tea', 'green tea', 'black tea', 'herbal tea'],    
        ]
         # Check if both foods belong to the same family
        for family in food_families:
            found1 = any(keyword in name1 for keyword in family)
            found2 = any(keyword in name2 for keyword in family)
            
            if found1 and found2:
                return True  # Both are in the same family
        
        return False  # Different foods
    
    # This function is designed to find a neutral base food item (like bread, crackers, or veggies) that can be paired with intense toppings such as salty fish, cured meats, strong cheeses, or flavorful dips. 
    def _find_neutral_base_for_topping(self, topping_name: str, target_grams: float = 100) -> dict | None:
        # Topping name is converted to lowercase for case-insensitive matching when searching for keywords in the food database
        topping_lower = topping_name.lower()
        
        # Dips and spreads pair well with vegetables
        dip_keywords = self.DIP_KEYWORDS
        is_dip = any(k in topping_lower for k in dip_keywords)
        
        if is_dip:
            # Prefer veggies for dips
            base_keywords = self.DIP_BASES
        else:
            # Prefer bread for salty fish/meat
            base_keywords = self.NEUTRAL_BASES
        
        mask = (
            self.df['name'].str.contains('|'.join(base_keywords), case=False, regex=True) &
            self.df['processing_level'].isin(self.ALLOWED_PROCESSING_LEVELS) &
            (self.df['category'] == 'side')
        )
        
        candidates = self.df[mask]
        
        # Fallback: if no matches, try the other category
        if candidates.empty:
            fallback_keywords = self.NEUTRAL_BASES if is_dip else self.DIP_BASES
            mask = (
                self.df['name'].str.contains('|'.join(fallback_keywords), case=False, regex=True) &
                self.df['processing_level'].isin(self.ALLOWED_PROCESSING_LEVELS) &
                (self.df['category'] == 'side')
            )
            candidates = self.df[mask]
        
        if candidates.empty:
            return None
        
        base = candidates.sample(1).iloc[0].to_dict()
        
        scalar = target_grams / 100.0
        return {
            "name": base['name'],
            "grams": target_grams,
            "macros": {
                "p": round(base.get(self.COL_PROTEIN, 0) * scalar, 1),
                "c": round(base.get(self.COL_CARBS, 0) * scalar, 1),
                "f": round(base.get(self.COL_FAT, 0) * scalar, 1)
            },
            "full_profile": base
        }
        
    # Helper function to determine the maximum portion size for a given food item based on its name, category, and sub-category.
    def _get_max_portion(self, row):
        # name is used for keyword checks
        name = row.get('name', '').lower()
        # Sub-category and category are used for broader classification when keywords are not definitive. 
        sub = row.get('sub_category', 'generic')
        cat = row.get('category', 'generic')

        # Soups
        if 'soup' in name or 'broth' in name or 'bouillon' in name or 'stew' in name:
            return self.PORTION_CAPS['soup']

        # Liquids
        if row.get('is_liquid'): 
            return self.PORTION_CAPS['liquid']
        
        # Dense Foods (Cheese & Nuts) - Check Name or Sub-category
        if cat == 'snack' and sub == 'dairy':
            return self.PORTION_CAPS['cheese']
            
        if 'nut' in name or 'seed' in name or sub == 'nut':
            return self.PORTION_CAPS['nut']

        # Check Sub-Category Matches (Starch, Bakery)
        # This automatically maps sub_category='starch' to 300.0 and 'bakery' to 100.0
        if sub in self.PORTION_CAPS: 
            return self.PORTION_CAPS[sub]
        
        # Check Main Category
        if cat == 'supplement': 
            return self.PORTION_CAPS['supplement']
        if cat == 'main': 
            return self.PORTION_CAPS['meat']
        
        # Fallback
        return self.PORTION_CAPS['solid_default']
    
    # Function that finds a soup item based on target macros to fill gaps
    def _find_soup(self, gap_macros, allowed_processing, ignore_names, is_breakfast=False, ignore_keywords=None):
        
        # Filter for soups
        mask = (
            self.df['name'].str.contains('soup|broth|bouillon', case=False, regex=True) &
            ~self.df['name'].str.contains('gravy|sauce', case=False, regex=True) &
            self.df['processing_level'].isin(allowed_processing) &
            self.df['sub_category'].isin(['meat', 'fish', 'vegetarian', 'veg'])
        )
        
        # If it's breakfast, only allow soups tagged as breakfast
        # This effectively stops soups from appearing at breakfast if none are tagged
        if is_breakfast:
            mask = mask & (self.df['is_breakfast'] == True)
        
        soup_df = self.df[mask]
        
        # Apply keyword exclusions to filter out unwanted soups
        soup_df = self._filter_by_keywords(soup_df, ignore_keywords)
        
        # If no soups remain after filtering, we return None, indicating that there are no suitable soup options available to fill the macro gaps
        if soup_df.empty: 
            return None

        # Setup KNN for the soup
        # Creates a KNN model looking for up to 20 nearest neighbors
        # Measures similarity using cosine distance (angles between vectors), not straight-line distance because nutritional data because it cares about proportions, not absolute values
        # Algorithm='brute' = compares against all soups. It is slower but more accurate with small datasets.
        model = NearestNeighbors(n_neighbors=min(20, len(soup_df)), metric='cosine', algorithm='brute')
        # Learning the nutritional profiles of all filtered soups
        # .fit() = memorizes all the macro profile
        model.fit(soup_df[self.features])
        
        # Target
        t_p = gap_macros.get(self.COL_PROTEIN, 0)
        t_c = gap_macros.get(self.COL_CARBS, 0)
        t_f = gap_macros.get(self.COL_FAT, 0)
        
        # Taget vector is the macro gap we want to fill. The KNN model will use this vector to find the closest soups in terms of nutritional profile.
        target_vector = pd.DataFrame([[t_p, t_c, t_f]], columns=self.features)
        
        # Find closest soups to the target macros using KNN. This returns the distances and indices of the nearest neighbors in the soup_df DataFrame.
        # model.kneighbors(target_vector) finds the 20 soups closest to that target in "macro space"
        # Returns:
        # distances = how far each neighbor is (lower = better match)
        # indices = their positions in soup_df
        # .kneighbors() = uses that memory to find closest matches
        distances, indices = model.kneighbors(target_vector)
        
        # Picking unique soup, sarting from the closest one (the best match)
        # Loops through the 20 closest soups (sorted by distance, closest first)
        # Skips any already used soups (ignore_names)
        # Returns the first valid soup found (= best match that hasn't been used)
        for idx in indices[0]:
            # soup_df.iloc[idx] tells Pandas to go into the soup database and pull out the exact row at position idx
            # .to_dict() converts that row of data into a standard Python dictionary so the code can easily read it
            item = soup_df.iloc[idx].to_dict()
            if item['name'] in ignore_names or item['name'].strip().lower() in ignore_names: 
                continue
                
            # Calculating portion
            # We assume soup is mostly for volume/carbs/fat, less for protein.
            gap_c = gap_macros.get(self.COL_CARBS, 0)
            grams = self._calculate_portion(item, t_c, self.COL_CARBS, is_main_dish=True)
            
            # Creating the dictionary to represent the chosen soup
            return {
                "name": item['name'],
                "grams": grams,
                "processing_level": item.get('processing_level', 'unknown'),
                "pairing_tag": item.get('pairing_tag', 'none'),
                "sub_category": "soup",
                "macros": {
                    "p": (item[self.features[0]] * grams) / 100,
                    "c": (item[self.features[1]] * grams) / 100,
                    "f": (item[self.features[2]] * grams) / 100
                },
                "full_profile": item
            }
        return None
    
    # Function for finding a drink to fill macro gaps
    def _find_drink(self, gap_macros, allowed_processing, ignore_names, ignore_keywords=None):
        keywords = '|'.join(['kefir', 'smoothie', 'drinkable', 'juice', 'milk', 'beverage', 'shake', 'tea', 'coffee'])
        
        all_exclusions = self.LIQUID_EXCLUSIONS + self.ALCOHOL_KEYWORDS

        # Merge user exclusions (e.g. "milk")
        if ignore_keywords:
            all_exclusions.extend([k.lower() for k in ignore_keywords])

        # Create base mask without exclusions first
        mask = (
            (self.df['is_liquid'] == True) & 
            (self.df['name'].str.contains(keywords, case=False, regex=True)) & 
            (self.df['processing_level'].isin(allowed_processing))
        )

        drink_df = self.df[mask]
        drink_df = self._filter_by_keywords(drink_df, all_exclusions)
        
        if drink_df.empty: 
            return None

        model = NearestNeighbors(n_neighbors=min(20, len(drink_df)), metric='cosine', algorithm='brute')
        model.fit(drink_df[self.features])
        
        t_p = gap_macros.get(self.COL_PROTEIN, 0)
        t_c = gap_macros.get(self.COL_CARBS, 0)
        t_f = gap_macros.get(self.COL_FAT, 0)

        # Drinks should contribute protein/carbs, NOT fat (which comes from oils/nuts)
        if t_f < 20:  # If low fat budget remaining
            search_f = 0.0
        elif t_c > 15:  # If we need carbs
            search_f = min(t_f * 0.3, 5.0)  # Max 5g fat from drink
        else:
            search_f = min(t_f * 0.5, 8.0)  # Max 8g fat from drink

        target_vector = pd.DataFrame([[t_p, t_c, search_f]], columns=self.features)
        
        distances, indices = model.kneighbors(target_vector)
        
        for idx in indices[0]:
            item = drink_df.iloc[idx].to_dict()
            if item['name'] in ignore_names or item['name'].strip().lower() in ignore_names: continue
            
            # Scale logic. If we need more protein than carbs, we prioritize protein in the portion calculation, otherwise carbs. 
            # This ensures the drink is contributing to the most needed macro.
            if t_p > t_c: 
                grams = self._calculate_portion(item, t_p, self.COL_PROTEIN, is_main_dish=True)
            else: 
                grams = self._calculate_portion(item, t_c, self.COL_CARBS, is_main_dish=True)

            # Drinks can be very calorie-dense, so we cap the portion size to prevent it from taking over the meal.
            if grams > 500: 
                grams = 500.0
            scalar = grams / 100.0
            
            return {
                "name": item['name'], 
                "grams": grams, "category": "drink", 
                "sub_category": item.get('sub_category', 'generic'),
                "processing_level": item.get('processing_level', 'unknown'), 
                "pairing_tag": item.get('pairing_tag', 'none'),
                "macros": {"p": round(item[self.COL_PROTEIN]*scalar,1), "c": round(item[self.COL_CARBS]*scalar,1), "f": round(item[self.COL_FAT]*scalar,1)},
                "full_profile": item
            }
        return None
    
    # Helper function to get fresh/raw vegetable candidates from the main food database. 
    # This function is importnat for ensuring that the meal plan includes healthy vegetable options that fit the user's preferences and dietary needs.
    def _get_fresh_veg_candidates(self, df=None):
        # Safety checks to ensure we have a valid DataFrame to work with and that it is not empty before applying the filtering logic. 
        if df is None:
            df = self.df
        if df.empty:
            return pd.DataFrame()

        mask = (
            (df['category'] == 'side') &
            (df['sub_category'] == 'veg') &
            (df['processing_level'].isin(self.ALLOWED_PROCESSING_LEVELS)) &
            (df['name'].str.contains('|'.join(self.VEG_KEYWORDS), case=False, na=False)) &
            (~df['name'].str.contains('|'.join(self.BAD_VEG_WORDS), case=False, na=False))
        )

        return df[mask]

    # This function is responsible for applying the various filters (hard filters, keyword exclusions, and focus keywords) to the main food database to create a tailored pool of food options that the KNN model will use to generate meal plans.
    def _get_model_for_filter(self, filters: dict, ignore_keywords = None, include_keywords: list = None, craving_keywords: list = None):
        # Creating a temporary DataFrame to apply filters
        # We never want to modify the original database
        temp_df = self.df.copy()
        
        # 1. Applying hard filters
        for col, value in filters.items():
            if isinstance(value, list): 
                temp_df = temp_df[temp_df[col].isin(value)]
            elif isinstance(value, str) and value.startswith("NOT_"): 
                temp_df = temp_df[temp_df[col] != value.replace("NOT_", "")]
            else: 
                temp_df = temp_df[temp_df[col] == value]
            
        # 2. Apply Exclusions
        temp_df = self._filter_by_keywords(temp_df, ignore_keywords)
            
        final_df = temp_df
        
        # PRIORITY 1: Craving Keywords (User explicitly asked for these)
        # These MUST appear in the plan if possible
        has_cravings = False
        if craving_keywords:
            craving_pattern = '|'.join([k.lower() for k in craving_keywords])
            if craving_pattern:
                craving_df = temp_df[temp_df['name'].str.contains(craving_pattern, case=False, na=False)]
                
                if not craving_df.empty:
                    # Found explicit cravings - use them
                    final_df = craving_df
                    has_cravings = True
                    # print(f"Craving match found: {len(craving_df)} items matching {craving_keywords}")
                    
                    # If we have enough craving matches (>=3), we stop here and ignore AI suggestions
                    # This prevents "Broccoli" from being drowned out by 50 other AI suggestions.
                    if len(craving_df) >= 3:
                        model = NearestNeighbors(n_neighbors=min(self.k, len(final_df)), metric='cosine', algorithm='brute')
                        model.fit(final_df[self.features])
                        return model, final_df
        
        # PRIORITY 2: Focus/Include Keywords (AI-suggested foods)
        if include_keywords:
            pattern = '|'.join([k.lower() for k in include_keywords])
            if pattern:
                focused_df = temp_df[temp_df['name'].str.contains(pattern, case=False, na=False)]
                
                # If we already have craving results, MERGE them
                if has_cravings:
                    if not focused_df.empty:
                        # Using 'id' to deduplicate if available, otherwise 'name'
                        # This avoids the "unhashable list" error and keeps distinct items with same names
                        dedup_col = 'id' if 'id' in final_df.columns else 'name'
                        
                        final_df = pd.concat([final_df, focused_df]).drop_duplicates(subset=[dedup_col])
                else:
                    # No cravings, rely on AI focus
                    if len(focused_df) >= 5:
                        final_df = focused_df

        # POOL SIZE SAFETY CHECK
        # If the resulting list is too small (e.g. < 5 items), the KNN won't have enough neighbors
        # to generate 4-5 distinct meals. We must add back the general items (temp_df).
        min_pool_size = 10 
        if len(final_df) < min_pool_size:
            print(f"Focused pool too small ({len(final_df)}), merging with general options...")
            dedup_col = 'id' if 'id' in final_df.columns else 'name'
            
            # Prioritize our focus items, but fill the rest with general items
            final_df = pd.concat([final_df, temp_df]).drop_duplicates(subset=[dedup_col])

        if final_df.empty: return None, pd.DataFrame()
        
        # Building the KNN model on the final filtered DataFrame. 
        model = NearestNeighbors(n_neighbors=min(self.k, len(final_df)), metric='cosine', algorithm='brute')
        model.fit(final_df[self.features])
        return model, final_df
    
    
    # Calculates portion size based on target nutrient amount
    def _calculate_portion(self, food_item: dict, target_amount: float, macro_key: str, is_main_dish: bool = False):
        # Extracts the amount of the specified macronutrient (protein, carbs, or fat) per 100 grams from the food item. If the macro_key is not found in the food item, it defaults to 0. 
        # This value is crucial for determining how much of the food item is needed to meet the target macro amount.
        val_per_100g = food_item.get(macro_key, 0)
        
        # Base Minimums
        min_limit = 100.0 if is_main_dish else 50.0
        
        if val_per_100g <= 0: return min_limit
        
        # If High Calorie Goal (>3000), act aggressive (1.2x)
        # Otherwise standard (1.0x) or conservative for carbs (0.85x)
        is_bulking = target_amount > 80 # Heuristic: if single meal target > 80g
        
        if is_bulking:
             aggressiveness = 1.2
        elif macro_key == self.COL_CARBS:
             aggressiveness = 0.85 
        else:
             aggressiveness = 1.0
        
        grams_needed = ((target_amount * aggressiveness) / val_per_100g) * 100 

        # Allow smaller portions for dense foods
        if macro_key == self.COL_CARBS and val_per_100g > 20 and not is_bulking:
            min_limit = 30.0

        # Dynamic cap scaling
        # If the requested amount is big, allow the cap to stretch
        base_cap = self._get_max_portion(food_item)
        
        # If we need more than the cap, allow up to 1.5x cap for Bulking
        if grams_needed > base_cap and is_bulking:
            max_limit = base_cap * 1.5
        else:
            max_limit = base_cap
        
        # The final portion size is calculated by taking the grams needed to meet the target macro, but it is constrained within a minimum limit (to ensure a reasonable portion size) and a maximum limit (to prevent excessively large portions). 
        # The result is rounded to the nearest whole number for practicality.   
        return round(max(min_limit, min(grams_needed, max_limit)), 0)
    
    # Optimizes meal by adding boosters based on pairing tags and macro gaps
    def _optimize_with_boosters(self, meal_dict, target_macros, ignore_keywords=None):
        # For loop for ensuring total_macros keys exist
        for key in ['protein', 'carbs', 'fat']:
            meal_dict['total_macros'][key] = meal_dict['total_macros'].get(key, 0)
            
        # If no boosters are available, returns the meal as is
        if self.boosters_df.empty: 
            return meal_dict
        
        # Filter the entire boosters dataframe at the start
        valid_boosters = self.boosters_df.copy()
        valid_boosters = self._filter_by_keywords(valid_boosters, ignore_keywords)

        # Extracts the total fat (in grams) already present in the meal
        current_f = meal_dict['total_macros']['fat']
        # Extracts the target fat (in grams) from the desired macros
        target_f = target_macros.get("fat, total (g)", 0)
        
        # List to hold added boosters
        boosters_added = []
        # Flag to track if fat was added due to pairing tag
        fat_added_by_pairing_tag = False
        
        # Extracts main and side dishes from the meal
        main_dish = meal_dict.get('main_dish', {})
        side_dish = meal_dict.get('side_dish', {}) 
        
        # Gets pairing tag and name of the main dish for decision making
        pairing_tag = main_dish.get('pairing_tag', 'none')
        main_name = main_dish.get('name', '').lower()

        # RULE 1: Needs Fiber (e.g., Yogurt, Porridge)
        if pairing_tag == 'needs_fiber':
            # Check if it is a Sweet Context (Yogurt, Porridge)
            side_name = side_dish.get('name', '').lower()
            main_name = main_dish.get('name', '').lower()
            is_sweet = self._is_sweet_context(main_name, side_name)
            
            is_pancake = 'pancake' in main_name or 'crepe' in main_name or 'waffle' in main_name
            
            if is_sweet or is_pancake:
                # Gets all valid boosters (Fiber + Antioxidant)
                options = valid_boosters[valid_boosters['booster_type'].isin(['antioxidant', 'fiber'])]
                # Filters out any boosters that contain bad words
                if 'name' in options.columns:
                    options = options[~options['name'].str.contains('|'.join(self.BOOSTER_EXCLUSIONS), case=False, na=False)]
               
                if not options.empty:
                    # STEP 1: Try to find berries first
                    berries = options[options['name'].str.contains('|'.join(self.BERRY_KEYWORDS), case=False, na=False)]
                    
                    # STEP 2: If no berries, fall back to other fruits
                    if berries.empty:
                        fruits = options[options['name'].str.contains('|'.join(self.FRUIT_KEYWORDS), case=False, na=False)]
                    else:
                        # Berries found - use them
                        fruits = berries
                    
                    # STEP 3: Pick one if available
                    if not fruits.empty:
                        b = fruits.sample(1).iloc[0].to_dict()
                        grams = b['recommended_grams']
                        
                        # Reduce portion if it's high-sugar (like honey, dates)
                        carb_density = b.get(self.COL_CARBS, 0)
                        if carb_density > 60:  # Very high sugar (honey, dried fruit)
                            grams = min(grams, 15)  # Cap at 15g
                            
                        raw_type = b.get('booster_type', 'Antioxidant')
                        formatted_reason = raw_type.replace('_', ' ').title()
                        self._add_booster(
                            boosters_added, b, grams, f"Source of {formatted_reason}"
                        )

                    # Pick one crunchy option
                    crunchies = options[options['name'].str.contains('|'.join(self.CRUNCH_KEYWORDS), case=False, na=False)]
                    
                    # Filter out fruits from crunchies to avoid overlap
                    crunchies = crunchies[~crunchies['name'].str.contains('|'.join(self.FRUIT_KEYWORDS), case=False, na=False)]
                    
                    # Picks one crunchy if not empty
                    if current_f < target_f * 0.8:
                        if not crunchies.empty:
                            b = crunchies.sample(1).iloc[0].to_dict()
                            grams = b['recommended_grams']
                            
                            raw_type = b.get('booster_type', 'Fiber')
                            formatted_reason = raw_type.replace('_', ' ').title()

                            self._add_booster(
                                boosters_added, b, grams, f"Source of {formatted_reason}")
                
        # RULE 2: Needs Fat
        # If the meal's pairing tag indicates it needs fat, and there's a significant fat gap, it adds a healthy fat booster
        fat_gap = target_f - current_f
        # Check % of fat filled. 
        # If we are already 80% of the way to the fat target, don't add fat even if the tag asks for it.
        percent_fat_filled = current_f / target_f if target_f > 0 else 1.0
        # This prevents over-fatty meals when scaling happens later.
        # Sets a threshold of 3g fat gap to consider adding fat boosters
        if pairing_tag == 'needs_fat' and fat_gap > 10.0 and percent_fat_filled < 0.75:
            options = valid_boosters[valid_boosters['booster_type'] == 'healthy_fat']
            if not options.empty:
                b = options.sample(1).iloc[0].to_dict()  
                # More conservative fat portions
                needed_grams = (fat_gap / b.get("fat, total (g)", 1)) * 100
                grams = min(15, needed_grams)
                self._add_booster(boosters_added, b, grams, "Healthy Fat Booster")
                fat_added_by_pairing_tag = True

        # RULE 3: Veggie Filler (For Composite Meals)
        side_sub = side_dish.get('sub_category', '')
        side_name = side_dish.get('name', '').lower()
        
        # Determines if the meal already has fresh veggies
        veggie_keywords = self.VEG_KEYWORDS
        has_fresh_veggies = any(
            kw in main_name or kw in side_name
            for kw in veggie_keywords
        )
        # Checks if the side dish is a heavy starch or bakery item
        is_heavy_side = side_sub in ['starch', 'bakery', 'generic']
        # Checks if the side dish is a cooked vegetable
        is_cooked_veg = any(k in side_name for k in self.COOKED_VEG_KEYWORDS)
        
        is_sweet = self._is_sweet_context(main_name, side_name)
        
        # Only run if we actually have a side dish (Composite Meal)
        if side_dish and not has_fresh_veggies and (is_heavy_side or is_cooked_veg) and not is_sweet:
            
            candidates = self._get_fresh_veg_candidates()

            if not candidates.empty:
                b = candidates.sample(1).iloc[0].to_dict()
                grams = 100 
                self._add_booster(
                    boosters_added, b, grams, "Fresh Veggies"
                )

        # RULE 4: Salad Dressing
        veggie_keywords = self.VEG_KEYWORDS
        added_raw_veggies = any(
            any(kw in b['name'].lower() for kw in veggie_keywords)
            for b in boosters_added
        )
        is_side_salad = any(kw in side_name for kw in self.SALAD_KEYWORDS)
        fat_booster_exists = any('healthy_fat' in b['reason'].lower() or 'healthy fats' in b['reason'].lower() for b in boosters_added)
        
        # If raw veggies were added or the side is a salad, and no fat booster exists, add a healthy fat booster
        if (added_raw_veggies or is_side_salad) and not fat_booster_exists and not fat_added_by_pairing_tag:
            meal_total_fat = current_f 
            # If the current fat is less than 20g, add a healthy fat booster (like olive oil)
            if meal_total_fat < 20.0:
                options = valid_boosters[valid_boosters['booster_type'] == 'healthy_fat']
                oils = options[options['name'].str.contains('oil', case=False)]
                # Choose oil if available, otherwise any healthy fat booster
                choice_df = oils if not oils.empty else options
                # If we have options, pick one randomly
                if not choice_df.empty:
                    b = choice_df.sample(1).iloc[0].to_dict()
                    
                    # Checking current fat status - reducing oil if already high
                    current_fat_percent = current_f / target_f if target_f > 0 else 0
                    
                    if current_fat_percent > 0.70:
                        grams = 8.0  # Reduce to 8g if already high in fat
                    else:
                        grams = b['recommended_grams']
                    
                    self._add_booster(
                        boosters_added, b, grams, "Salad Dressing"
                    )
  
        # RULE 5: CEREAL FIX (Muesli needs Milk/Yogurt)
        
        # 1. Detecting cereal
        is_cereal_main = any(k in main_name for k in self.MUESLI_KEYWORDS) and 'bar' not in main_name
        is_cereal_side = any(k in side_name for k in self.MUESLI_KEYWORDS) and 'bar' not in side_name

        if is_cereal_main or is_cereal_side:
            
            # 2. Checking if dairy is explicitly named in the visible meal components
            active_food_names = [main_name]
            
            if side_dish: 
                active_food_names.append(side_dish.get('name', '').lower())
            if meal_dict.get('drink'): 
                active_food_names.append(meal_dict['drink'].get('name', '').lower())
            if meal_dict.get('soup'): 
                active_food_names.append(meal_dict['soup'].get('name', '').lower())
            
            # Check existing boosters too
            for b in boosters_added:
                active_food_names.append(b.get('name', '').lower())

            # Check for dairy keywords in those specific names
            all_dairy_keys = self.DAIRY_KEYWORDS + self.MILK_SUBSTITUTES
            has_dairy = any(
                any(k in name for k in all_dairy_keys) 
                for name in active_food_names
            )
            
            # 3. If no dairy found, add it.
            if not has_dairy:
                dairy_item = self._find_dairy_for_cereal(ignore_keywords=ignore_keywords)
                
                if dairy_item:
                    grams = 150.0
                    self._add_booster(
                        boosters_added, dairy_item, grams, "Milk/Yogurt Base for Cereal"
                    )
                else:
                    # Debug query
                    all_keywords = self.DAIRY_KEYWORDS + self.MILK_SUBSTITUTES
                    test_mask = (
                        (self.df['name'].str.contains('|'.join(all_keywords), case=False, regex=True)) &
                        (self.df['is_liquid'] == True) 
                    )
                    available_dairy = self.df[test_mask]

        # RULE 6: Cheese Needs Veggies
        is_cheese_main = any(k in main_name for k in self.CHEESE_KEYWORDS)

        if is_cheese_main:
            # Try veggie_side boosters first
            candidates = self._get_fresh_veg_candidates()

            if not candidates.empty:
                b = candidates.sample(1).iloc[0].to_dict()
                grams = 100.0

                self._add_booster(
                    boosters_added, b, grams, "Fresh Veggies with Cheese"
                )
        
        # RULE 7: PROTEIN POWDER (Needs Liquid + Fruit)
        # Check if main dish is a powder/supplement
        is_powder = (
            main_dish.get('category') == 'supplement' or 
            any(k in main_name for k in self.PROTEIN_SUPPLEMENT_KEYWORDS) or
            'powder' in main_name 
        )

        if is_powder:
            # 1. Add Liquid Base
            mask = (
                (self.df['is_liquid'] == True) &
                (self.df['name'].str.contains('milk|oat drink|almond drink|soy', case=False, regex=True)) &
                (self.df['processing_level'].isin(self.ALLOWED_PROCESSING_LEVELS)) &
                (~self.df['name'].str.contains('chocolate|strawberry|vanilla|sugar|cream|condensed|flavored', case=False, regex=True))
            )
            
            liquid_candidates = self.df[mask]

            if not liquid_candidates.empty:
                liq = liquid_candidates.sample(1).iloc[0].to_dict()
                self._add_booster(
                    boosters_added, liq, 300.0, "Liquid Base for Shake"
                )

            # 2. Add Flavor/Fruit
            if not self.boosters_df.empty:
                # Filter for antioxidants/fiber
                fruit_options = self.boosters_df[self.boosters_df['booster_type'].isin(['antioxidant', 'fiber'])]
                
                shake_fruits = self.BERRY_KEYWORDS + self.FRUIT_KEYWORDS
                
                if 'name' in fruit_options.columns:
                    fruit_options = fruit_options[fruit_options['name'].str.contains('|'.join(shake_fruits), case=False, na=False)]

                if not fruit_options.empty:
                    frt = fruit_options.sample(1).iloc[0].to_dict()
                    self._add_booster(
                        boosters_added, frt, 100.0, "Fruit for Shake Flavor"
                    )

                
        # RULE 8: MUESLI/GRANOLA AS BOOSTER NEEDS DAIRY
        # If muesli/granola was added as a booster (for fiber), ensure dairy exists
        muesli_booster_added = any(
            any(k in b['name'].lower() for k in self.MUESLI_KEYWORDS)
            for b in boosters_added
        )

        if muesli_booster_added:
            # Check if meal has dairy anywhere
            has_dairy = any(k in str(meal_dict).lower() for k in self.DAIRY_KEYWORDS)
            
            if not has_dairy:
                # Add dairy
                dairy_item = self._find_dairy_for_cereal()
                if dairy_item:
                    b = dairy_item
                    grams = 150.0
                    self._add_booster(
                        boosters_added, b, grams, "Dairy for Muesli (Protein)"
                    )

        # RULE 9: PORRIDGE/OATMEAL SIDE NEEDS BERRIES
        # If side dish is porridge/oatmeal, add berries
        side_name = side_dish.get('name', '').lower() if side_dish else ''
        is_porridge_side = any(k in side_name for k in self.BREAKFAST_ONLY_AND_SNACK_WORDS)

        if is_porridge_side and self.boosters_df is not None and not self.boosters_df.empty:
            # Check if we already added berries
            has_berry = any('berry' in b.get('name', '').lower() for b in boosters_added)
            
            if not has_berry:
                # Get berries
                options = valid_boosters[valid_boosters['booster_type'] == 'antioxidant']
                
                if not options.empty:
                    berries = options[options['name'].str.contains('|'.join(self.BERRY_KEYWORDS), case=False, na=False)]
                    # Exclude boosters with exclusion keywords in their name
                    if not berries.empty:
                        berries = berries[~berries['name'].str.contains('|'.join(self.BOOSTER_EXCLUSIONS), case=False, na=False)]
                    if not berries.empty:
                        b = berries.sample(1).iloc[0].to_dict()
                        grams = b['recommended_grams']
                        self._add_booster(boosters_added, b, grams, "Berries for Porridge")
                        
        # RULE 10: INTENSE TOPPINGS NEED NEUTRAL BASES
        main_name = main_dish.get('name', '').lower()
        is_intense_topping = any(k in main_name for k in self.INTENSE_TOPPINGS)

        if is_intense_topping and meal_dict.get('type') == 'single_food':
            # Check if we already have a base
            has_base = any(
                any(k in b.get('name', '').lower() for k in self.NEUTRAL_BASES)
                for b in boosters_added
            )
            
            if not has_base:
                base_item = self._find_neutral_base_for_topping(main_name, target_grams=80.0)
                
                if base_item:
                    self._add_booster(
                        boosters_added, base_item, base_item['grams'], "Neutral Base for Topping"
                    )  

        # Update Totals
        # Adds the boosters to the meal dictionary and updates total macros
        meal_dict['boosters'] = boosters_added
        for b in boosters_added:
            meal_dict['total_macros']['protein'] += b['macros']['p']
            meal_dict['total_macros']['carbs']   += b['macros']['c']
            meal_dict['total_macros']['fat']     += b['macros']['f']
        
        meal_dict['boosters'] = boosters_added
        
        # Recalculate totals from scratch to be safe
        new_p = meal_dict['main_dish'].get('macros', {}).get('p', 0)
        new_c = meal_dict['main_dish'].get('macros', {}).get('c', 0)
        new_f = meal_dict['main_dish'].get('macros', {}).get('f', 0)
        
        if 'side_dish' in meal_dict and meal_dict['side_dish']:
             new_p += meal_dict['side_dish']['macros'].get('p', 0)
             new_c += meal_dict['side_dish']['macros'].get('c', 0)
             new_f += meal_dict['side_dish']['macros'].get('f', 0)
             
        for b in boosters_added:
            new_p += b['macros']['p']
            new_c += b['macros']['c']
            new_f += b['macros']['f']
            
        meal_dict['total_macros']['protein'] = round(new_p, 1)
        meal_dict['total_macros']['carbs'] = round(new_c, 1)
        meal_dict['total_macros']['fat'] = round(new_f, 1)
            
        return meal_dict
    
    # Function for scaling meal components to better hit target macros
    def _scale_meal_to_target(self, meal_dict, target_macros):
        # 1. Get Current Totals
        curr_p = meal_dict['total_macros']['protein']
        curr_c = meal_dict['total_macros']['carbs']
        curr_f = meal_dict['total_macros']['fat']
        
        # Recalculate calories strictly based on macros to ensure math aligns with UI
        current_cal = (curr_p * 4) + (curr_c * 4) + (curr_f * 9)
        
        if current_cal < 50: 
            return meal_dict
        
        # 2. Get Targets
        t_p = target_macros.get(self.COL_PROTEIN, 0)
        t_c = target_macros.get(self.COL_CARBS, 0)
        t_f = target_macros.get(self.COL_FAT, 0)
        t_cal = target_macros.get("calories") or (t_p*4 + t_c*4 + t_f*9)

        # 3. Calculate Scaling Ratios
        r_p = t_p / curr_p if curr_p > 0 else 1.0
        r_c = t_c / curr_c if curr_c > 0 else 1.0
        
        # 4. Determine Scale Factor
        scale_factor = 1.0

        # PRIORITY 1: Don't overshoot Calories or Carbs significantly
        # If we are > 10% over calories or > 5% over carbs, shrink it.
        r_cal = t_cal / current_cal if current_cal > 0 else 1.0
        
        if r_cal < 0.90 or r_c < 0.95:
             # Shrink by the limiting factor
             scale_factor = min(r_cal, r_c)
        
        # PRIORITY 2: Hit Protein Target
        # If we are undershooting protein, grow, even if calories go slightly up.
        elif r_p > 1.02:
            scale_factor = r_p 
            # Cap growth to prevent massive calorie overshoot
            # If growing protein makes calories > 115% of target, cap it.
            max_cal_growth = (t_cal * 1.15) / current_cal
            scale_factor = min(scale_factor, max_cal_growth)

        # Safety Clamps (0.5x to 3.0x)
        scale_factor = max(0.5, min(scale_factor, 3.0))
        
        if 0.98 <= scale_factor <= 1.02: return meal_dict

        # Applying Scaling
        def scale_component(comp):
            if not comp or 'grams' not in comp: 
                return
            old_grams = comp.get('grams', 0)
            if old_grams <= 0: 
                return

            # Apply scale
            new_grams = round(old_grams * scale_factor, 0)
            
            # Enforce Minimums/Maximums
            is_main = (comp == meal_dict.get('main_dish'))
            min_lim = 80.0 if is_main else 30.0
            max_lim = self._get_max_portion(comp)
            
            new_grams = max(min_lim, min(new_grams, max_lim))
            
            # Apply changes
            comp['grams'] = round(new_grams, 0)
            real_scale = new_grams / old_grams
            
            for k in comp['macros']:
                comp['macros'][k] = round(comp['macros'][k] * real_scale, 1)

        scale_component(meal_dict.get('main_dish'))
        if 'side_dish' in meal_dict: 
            scale_component(meal_dict.get('side_dish'))
        if 'soup' in meal_dict: 
            scale_component(meal_dict.get('soup'))
        if 'drink' in meal_dict: 
            scale_component(meal_dict.get('drink'))
        
        # Recalculate Totals
        new_p = new_c = new_f = 0
        all_comps = [meal_dict.get(k) for k in self.MAIN_CATEGORIES if meal_dict.get(k)]
        all_comps += meal_dict.get('boosters', [])
        
        for c in all_comps:
            new_p += c['macros'].get('p', 0)
            new_c += c['macros'].get('c', 0)
            new_f += c['macros'].get('f', 0)
        
        meal_dict['total_macros'] = {
            "protein": round(new_p, 1), 
            "carbs": round(new_c, 1), 
            "fat": round(new_f, 1)
        }
        return meal_dict

    # Function to scale all meals together if we are overshooting targets significantly. 
    # This is a global adjustment that can help bring the entire plan back in line with calorie and carb goals without sacrificing protein as much.
    def scale_meals_globally(self, meals: list, target_macros: dict):
        if not meals:
            return meals

        # Sum totals across meals
        total_p = sum(m['total_macros']['protein'] for m in meals)
        total_c = sum(m['total_macros']['carbs'] for m in meals)
        total_f = sum(m['total_macros']['fat'] for m in meals)

        total_cal = (total_p * 4) + (total_c * 4) + (total_f * 9)

        target_p = target_macros.get(self.COL_PROTEIN, 0)
        target_c = target_macros.get(self.COL_CARBS, 0)
        target_f = target_macros.get(self.COL_FAT, 0)
        target_cal = target_macros.get("calories") or (
            target_p * 4 + target_c * 4 + target_f * 9
        )

        # Only scale down if we are overshooting
        # Check if we are over on ANY macro or calories
        cal_ratio = total_cal / target_cal if target_cal > 0 else 1.0
        carb_ratio = total_c / target_c if target_c > 0 else 1.0
        fat_ratio = total_f / target_f if target_f > 0 else 1.0
        protein_ratio = total_p / target_p if target_p > 0 else 1.0
        
        # SAFETY CHECK: Never shrink if Calories are significantly under target (<90%)
        if cal_ratio < 0.90:
             return meals

        # Normal shrinking logic
        needs_shrinking = (cal_ratio > 1.05) or (carb_ratio > 1.10) or (fat_ratio > 1.10)
        
        if protein_ratio < 0.95:  # If protein below 95%, don't scale down
            print(f"Skipping global scaling: Protein already low ({protein_ratio:.0%})")
            return meals
        
            
        if carb_ratio < 0.92:  # If carbs below 92%, don't shrink
            return meals
        
        if not needs_shrinking:
            return meals  # Don't touch meals if we're at or below target

        print(f"Global Scaling: Overshooting detected (Cal: {cal_ratio:.0%}, C: {carb_ratio:.0%}, F: {fat_ratio:.0%})")
        
        is_carb_crisis = (total_c / target_c) > 1.05 if target_c > 0 else False
        
        min_scale_floor = 0.50 if is_carb_crisis else 0.70
        # Calculate scale factor based on worst overshoot
        scale = min(1.0 / cal_ratio, 1.0 / carb_ratio, 1.0 / fat_ratio)
        scale = max(min_scale_floor, scale)  # Don't shrink more than 15%
        
        # If scaling would drop protein below 90%, limit the scaling
        protein_after_scale = total_p * scale
        
        # Exception for Overshooting Carbs
        # If we are massively overshooting carbs (>105%), ignore the protein safety clamp.
        if protein_after_scale < target_p * 0.88:  
            min_scale = (target_p * 0.88) / total_p  
            scale = max(scale, min_scale)
            print(f"Limiting scale to {scale:.2f} to preserve protein")

        def scale_component(comp):
            if not comp or 'grams' not in comp:
                return
            old = comp['grams']
            if old <= 0:
                return

            comp['grams'] = round(old * scale, 0)

            for k in comp['macros']:
                comp['macros'][k] = round(comp['macros'][k] * scale, 1)
        
        # Applying scaling
        for meal in meals:
            for k in self.MAIN_CATEGORIES:
                if k in meal and meal[k]:
                    scale_component(meal[k])

            for b in meal.get('boosters', []):
                scale_component(b)

            # Recalculate totals
            p = c = f = 0
            for k in self.MAIN_CATEGORIES:
                if k in meal and meal[k]:
                    p += meal[k]['macros'].get('p', 0)
                    c += meal[k]['macros'].get('c', 0)
                    f += meal[k]['macros'].get('f', 0)

            for b in meal.get('boosters', []):
                p += b['macros'].get('p', 0)
                c += b['macros'].get('c', 0)
                f += b['macros'].get('f', 0)

            meal['total_macros'] = {
                "protein": round(p, 1),
                "carbs": round(c, 1),
                "fat": round(f, 1)
            }

        return meals
    
    # Function to boost protein in meals that are significantly under target
    def _apply_protein_boost(self, meal_dict, component, current_deficit, min_density=12, ignore_keywords=None):
        if ignore_keywords:
            food_name = component.get('name', '').lower()
            if any(keyword.lower() in food_name for keyword in ignore_keywords):
                return False  
            
        p = component['macros'].get('p', 0)
        c = component['macros'].get('c', 0)
        f = component['macros'].get('f', 0)
        grams = component['grams']
        
        if grams <= 0: return

        # 1. DENSITY CHECK
        p_per_100g = (p / grams) * 100
        
        # 2. Bulking Mode: If we are missing A LOT of protein (>40g), relax the rules
        is_bulking_mode = current_deficit > 40
        
        # If bulking, accept slightly lower quality protein sources (e.g. 10g/100g)
        effective_min_density = min_density - 2 if is_bulking_mode else min_density
        
        # If the protein density is too low, skip this component. But if bulking, allow slightly less dense sources
        if p_per_100g < effective_min_density: 
            return 
        
        # This prevents adding a lot of carbs in the name of protein. If carbs are more than 1.5x protein, skip. But if bulking, allow up to 2.5x carbs.
        carb_limit_ratio = 2.5 if is_bulking_mode else 1.5
        if c > (p * carb_limit_ratio): 
            return 
        
        # 
        max_boost_percent = 0.80 if is_bulking_mode else 0.40
        if f > p and not is_bulking_mode: max_boost_percent = 0.10

        # 2. Calculate Boost
        grams_needed = (current_deficit / p_per_100g) * 100
        allowed_grams = grams * max_boost_percent
        
        boost_grams = min(grams_needed, allowed_grams)
        
        # 3. Applying Boost
        new_grams = grams + boost_grams
        
        # Dynamic Cap: If bulking, allow portions 1.5x larger than normal cap
        base_cap = self._get_max_portion(component)
        max_cap = base_cap * 1.5 if is_bulking_mode else base_cap
        
        new_grams = min(new_grams, max_cap)
        
        if new_grams > grams:
            scale = new_grams / grams
            component['grams'] = round(new_grams, 0)
            
            # Save old macros for difference calculation
            old_p, old_c, old_f = p, c, f
            
            # Update macros
            for k in component['macros']:
                component['macros'][k] = round(component['macros'][k] * scale, 1)
            
            # Update Meal Totals
            meal_dict['total_macros']['protein'] += (component['macros']['p'] - old_p)
            meal_dict['total_macros']['carbs'] += (component['macros']['c'] - old_c)
            meal_dict['total_macros']['fat'] += (component['macros']['f'] - old_f)
            
            print(f"Boosted {component['name']} (+{new_grams - grams:.0f}g) for Protein")
            return True # Signal that we boosted
        return False
    
    # Final pass function to rescue protein if we are significantly under target after all other adjustments
    def rescue_protein_deficit(self, meals: list, target_macros: dict, ignore_keywords=None):
        if not meals: 
            return meals
        
        # BOOSTERS DF for protein boosters (powders)
        valid_boosters = self.boosters_df.copy()
        valid_boosters = self._filter_by_keywords(valid_boosters, ignore_keywords)

        # Calculate total protein
        total_p = sum(m['total_macros']['protein'] for m in meals)
        target_p = target_macros.get(self.COL_PROTEIN, 0)
        
        protein_deficit = target_p - total_p
        protein_percent = (total_p / target_p) if target_p > 0 else 1.0

        if protein_deficit < 5 and protein_percent > 0.95:
            return meals

        print(f"Protein Rescue: Need {protein_deficit:.1f}g more protein")
        
        # STRATEGY 1: Boost Main Dishes
        # Using _apply_protein_boost helper to handle "Bulking Mode"
        for meal in meals:
            if protein_deficit <= 2: 
                break
            main = meal.get('main_dish')
            if main:
                if self._apply_protein_boost(meal, main, protein_deficit, min_density=15, ignore_keywords=ignore_keywords):
                     # Recalculate deficit
                     new_total = sum(m['total_macros']['protein'] for m in meals)
                     protein_deficit = target_p - new_total
        
        # STRATEGY 2: Boost Protein-Rich Sides
        for meal in meals:
            if protein_deficit <= 2: 
                break
            side = meal.get('side_dish')
            if side:
                if self._apply_protein_boost(meal, side, protein_deficit, min_density=10, ignore_keywords=ignore_keywords):
                     new_total = sum(m['total_macros']['protein'] for m in meals)
                     protein_deficit = target_p - new_total

        # STRATEGY 3: Boost Snacks
        for meal in meals:
            if protein_deficit <= 2: 
                break
            if meal.get('type') == 'single_food':
                main = meal.get('main_dish')
                if main:
                    if self._apply_protein_boost(meal, main, protein_deficit, min_density=8, ignore_keywords=ignore_keywords):
                         new_total = sum(m['total_macros']['protein'] for m in meals)
                         protein_deficit = target_p - new_total

        # STRATEGY 4: Add Protein Boosters
        if protein_deficit > 10 and not valid_boosters.empty and 'booster_type' in valid_boosters.columns:
            protein_boosters = valid_boosters[valid_boosters['booster_type'] == 'protein']
            
            if not protein_boosters.empty:
                for meal in meals:
                    if protein_deficit <= 5: 
                        break
                    
                    has_protein_booster = any(
                        'protein' in b.get('reason', '').lower() 
                        for b in meal.get('boosters', [])
                    )
                    
                    if not has_protein_booster:
                        booster = protein_boosters.sample(1).iloc[0].to_dict()
                        grams = min(30, protein_deficit * 3)
                        
                        self._add_booster(
                            meal.get('boosters', []), 
                            booster, 
                            grams, 
                            "Protein Boost"
                        )
                        
                        p_val = booster.get(self.COL_PROTEIN, 0)
                        added_p = (p_val * grams) / 100
                        
                        # Update Meal Totals Manually
                        meal['total_macros']['protein'] += added_p
                        meal['total_macros']['carbs'] += (booster.get(self.COL_CARBS, 0) * grams) / 100
                        meal['total_macros']['fat'] += (booster.get(self.COL_FAT, 0) * grams) / 100
                        
                        protein_deficit -= added_p
                        print(f"Added Protein Booster: {booster['name']} -> +{added_p:.1f}g protein")
            
        # FINAL CHECK
        if protein_deficit > 5:
            print(f"Final protein boost needed: {protein_deficit:.1f}g")
            
            best_meal = None
            best_density = 0
            for meal in meals:
                main = meal.get('main_dish')
                if not main or 'grams' not in main: continue
                
                p_per_100g = (main['macros'].get('p', 0) / main['grams']) * 100
                if p_per_100g > best_density:
                    best_density = p_per_100g
                    best_meal = meal
            
            if best_meal and best_density > 15:
                # Force boost the best meal found
                self._apply_protein_boost(best_meal, best_meal['main_dish'], protein_deficit, min_density=0, ignore_keywords=ignore_keywords)
                    
        return meals

    # Function to add healthy fats if we are significantly under target after all other adjustments
    def rescue_fat_deficit(self, meals: list, target_macros: dict, ignore_keywords=None):
        if not meals: 
            return meals
        
        valid_boosters = self.boosters_df.copy()
        valid_boosters = self._filter_by_keywords(valid_boosters, ignore_keywords)

        if valid_boosters.empty: 
            return meals
        
        total_f = sum(m['total_macros']['fat'] for m in meals)
        target_f = target_macros.get(self.COL_FAT, 0)
        fat_deficit = target_f - total_f
        
        # If we are close enough, stop
        if fat_deficit < 10: 
            return meals
        
        print(f"Fat Rescue: Need {fat_deficit:.1f}g more fat")
        
        if 'booster_type' not in valid_boosters.columns: 
            return meals
        
        # Categorize fat boosters into Oils, Crunchy (Nuts/Seeds), and Creamy (Avocado/Butter/Coconut milk)
        fat_options = valid_boosters[valid_boosters['booster_type'] == 'healthy_fat']
        
        nuts_seeds = fat_options[fat_options['name'].str.contains('nut|seed', case=False, na=False)]
        oils = fat_options[fat_options['name'].str.contains('oil', case=False, na=False)]
        # Add a category for "Creamy/Fleshy" fats (Avocado, Butter, Coconut milk) if available
        creamy_fats = fat_options[fat_options['name'].str.contains('|'.join(self.HEALTHY_CREAMY_KEYWORDS), case=False, na=False)]
        
        if fat_options.empty: 
            return meals
        
        # Loop twice: First pass adds primary fat. Second pass adds secondary fat if still short.
        for pass_num in [1, 2]: 
            if fat_deficit <= 5: 
                break
            
            for meal in meals:
                if fat_deficit <= 5: 
                    break
                
                # Validation checks
                main = meal.get('main_dish', {})
                if main.get('full_profile', {}).get('is_liquid', False): 
                    continue
                main_name = main.get('name', '').lower()
                if any(k in main_name for k in self.SWEET_KEYWORDS + self.MUESLI_KEYWORDS): 
                    continue
                
                existing_boosters = meal.get('boosters', [])
                
                # Check what we already have
                has_oil = any('oil' in b['name'].lower() for b in existing_boosters)
                has_crunch = any('nut' in b['name'].lower() or 'seed' in b['name'].lower() for b in existing_boosters)
                has_creamy = any(any(keyword in b['name'].lower() for keyword in self.HEALTHY_CREAMY_KEYWORDS) for b in existing_boosters)
                
                candidate = None
                reason = "Healthy Fats"
                
                # LOGIC: Try to fill a missing "Fat Slot" (Oil, Crunch, or Creamy)
                if not has_oil and not oils.empty:
                    candidate = oils.sample(1).iloc[0].to_dict()
                    reason = "Healthy Fats (Oil)"
                elif not has_crunch and not nuts_seeds.empty:
                    candidate = nuts_seeds.sample(1).iloc[0].to_dict()
                    reason = "Healthy Fats (Crunch)"
                elif not has_creamy and not creamy_fats.empty:
                    candidate = creamy_fats.sample(1).iloc[0].to_dict()
                    reason = "Healthy Fats (Rich)"
                
                if not candidate: 
                    continue
                
                # Calculate Portion
                # For Keto, we allow large fat portions (up to 30g oil/nuts)
                max_cap = 30.0 
                needed_grams = (fat_deficit / candidate.get(self.COL_FAT, 1)) * 100
                grams = max(10, min(max_cap, needed_grams))
                
                scalar = grams / 100.0
                
                new_booster = {
                    "name": candidate['name'], "grams": round(grams, 1), "reason": reason,
                    "macros": {
                        "p": round(candidate.get(self.COL_PROTEIN, 0) * scalar, 1),
                        "c": round(candidate.get(self.COL_CARBS, 0) * scalar, 1),
                        "f": round(candidate.get(self.COL_FAT, 0) * scalar, 1)
                    }, "full_profile": candidate
                }
                
                if 'boosters' not in meal: meal['boosters'] = []
                meal['boosters'].append(new_booster)
                
                # Update totals
                meal['total_macros']['protein'] += new_booster['macros']['p']
                meal['total_macros']['carbs'] += new_booster['macros']['c']
                meal['total_macros']['fat'] += new_booster['macros']['f']
                
                fat_deficit -= new_booster['macros']['f']
                print(f"   Added {candidate['name']} ({grams:.1f}g) to meal → +{new_booster['macros']['f']:.1f}g fat")
        
        return meals

    # Function to boost carbs in meals that are significantly under target after all other adjustments
    def rescue_carb_deficit(self, meals: list, target_macros: dict, ignore_keywords = None):
        # This set will remember which meals we modify in Strategy 1, so we don't accidentally double-stuff them in Strategy 2.
        boosted_meal_indices = set()

        # Creating a clean list of candidate foods, removing any forbidden items (allergies).
        valid_boosters = self.df.copy()
        valid_boosters = self._filter_by_keywords(valid_boosters, ignore_keywords)

        if valid_boosters.empty: 
            return meals
        
        # Calculate the gap: how many carbs we are missing
        total_c = sum(m['total_macros']['carbs'] for m in meals)
        target_c = target_macros.get(self.COL_CARBS, 0)
        carb_deficit = target_c - total_c
        carb_percent = (total_c / target_c) if target_c > 0 else 1.0
        
        # Skipping carb rescue if we are close enough or if carbs are already very high (to avoid over-boosting)
        if carb_deficit < 5 and carb_percent > 0.98: 
            return meals
        
        print(f"Carb Rescue: Need {carb_deficit:.1f}g more carbs")
        
        # Strategy 1: Boost existing Starches
        # Loop 1: Expanding the foods
        for i, meal in enumerate(meals): 
            # Loop checks: Stop if gap is filled, skip if it's a snack (single_food).
            if carb_deficit <= 5: 
                break
            if meal.get('type') != 'composite_meal': 
                continue
            
            side = meal.get('side_dish')
            if not side or 'grams' not in side: 
                continue
            
            # This acts as quality check: Is the side dish actually a carb source?
            # We check density: (Carbs / Total Grams) * 100.
            # If it's < 10g carbs per 100g (like Broccoli), we skip it because We cannot consume 1kg of broccoli.
            c_per_100g = (side['macros'].get('c', 0) / side['grams']) * 100 if side['grams'] > 0 else 0
            if c_per_100g < 10: 
                continue
            
            # Calculating boost
            old_grams = side['grams']
            # We allow the portion to grow up to 130% of its normal maximum.
            max_allowed = self._get_max_portion(side) * 1.30
            
            # Computing required boost to fill the carb deficit
            grams_needed = (carb_deficit / c_per_100g) * 100
            # Safety cap: We limit the growth to +60% of the original size.
            boost = min(old_grams * 0.60, grams_needed)
            
            # This ensures we don't add an excessive amount of carbs from one component, which could throw off the meal balance and lead to unrealistic portion sizes.
            new_grams = min(old_grams + boost, max_allowed)
            # Skip if no meaningful change
            if new_grams <= old_grams: 
                continue
            # Marking this meal as boosted, if the math worked out to add food
            boosted_meal_indices.add(i)
        
            # Scale factors for macro update
            actual_boost = new_grams - old_grams
            scale = new_grams / old_grams
            
            # Updating the side dish portion and macros
            side['grams'] = round(new_grams, 0)
            for k in side['macros']: 
                side['macros'][k] = round(side['macros'][k] * scale, 1)
            
            # Update totals in meal dictionary
            for macro_key in ['p', 'c', 'f']:
                # This dynamic mapping allows us to update the correct macro in the meal totals without hardcoding each one.
                macro_name = {'p': 'protein', 'c': 'carbs', 'f': 'fat'}[macro_key]
                # This line updates the meal's total macros by adding the difference caused by the boost. 
                # It calculates the added macros based on the original macro value for the side dish, scaled by the actual boost in grams.
                meal['total_macros'][macro_name] += (side['macros'][macro_key] * (scale - 1))
            
            # Calculating the actual carbs added for logging purposes, which provides insight into how much the carb content of the meal was increased by this boost.
            carbs_added = (c_per_100g * actual_boost) / 100 # Shrinking the carb gap
            carb_deficit -= carbs_added
            print(f"Boosted {side['name']}: +{actual_boost:.0f}g -> +{carbs_added:.1f}g carbs")

        # Strategy 2: Add high-density carb boosters
        # Only proceed if still meaningfully low. We don't want to add carb boosters if we are already close to target after boosting sides.
        if carb_deficit > 10:
            # 1. Merging carb-related keywords.
            all_keywords = list(set(self.CARB_BOOST_KEYWORDS + self.BREAD_KEYWORDS))
            
            # 2. Get Candidates
            all_boosters = valid_boosters[
                (valid_boosters['name'].str.contains('|'.join(all_keywords), case=False, regex=True)) &
                (valid_boosters['processing_level'].isin(self.ALLOWED_PROCESSING_LEVELS)) &
                (valid_boosters['category'].isin(['side', 'snack'])) & 
                (valid_boosters[self.COL_CARBS] >= 15)                 
            ].copy()
            
            savory_exclude_for_breakfast = self.SAVORY_EXCLUDE_FOR_BREAKFAST
            
            # Sorting by carb content to prioritize the most efficient boosters. 
            if not all_boosters.empty:
                all_boosters = all_boosters.sort_values(self.COL_CARBS, ascending=False)
                
                # value set to track if we've used any bread-based boosters, since we want to limit it to 1 per day across all meals. 
                bread_used_globally = False
                used_booster_names = set() 
                
                # Count eligible meals
                eligible_meals_count = 0
                # For loop to count how many meals are eligible for carb boosters based on criteria (composite meals with <3 boosters and not breakfast-only)
                for meal in meals:
                    # Skipping single foods since we do not want to add, for isntance, side of rice to snacks. 
                    # Making sure that meal is not too complex (already has 3 boosters)
                    if meal.get('type') == 'composite_meal' and len(meal.get('boosters', [])) < 3:
                        main_name = meal.get('main_dish', {}).get('name', '').lower()
                        # This logic assumes that "Carb Rescue" usually adds things like Bread, Rice, or Pasta. 
                        # We do not want to add a slice of Rye Bread to a bowl of Oatmeal. 
                        # This filter ensures we only target savory meals (like Chicken or Tofu) where extra carbs make culinary sense.
                        if not any(k in main_name for k in self.BREAKFAST_ONLY_AND_SNACK_WORDS):
                            #  If a meal passes all the tests above, we increment the counter.
                             eligible_meals_count += 1
                
                if eligible_meals_count == 0: 
                    # If no meals qualify (maybe you only have snacks and porridge today), we set the count to 1 because later in the code division is done carb_deficit / eligible_meals_count.
                    eligible_meals_count = 1

                # Loop 2: Adding new items if we are still short.
                for i, meal in enumerate(meals):
                    # Loop checks: Stop if gap is filled, skip if not a composite meal (we don't want to add carb boosters to snacks or single foods).
                    if carb_deficit <= 5: 
                        break
                    if meal.get('type') != 'composite_meal': 
                        continue
                    # Skip meals we already boosted in Strategy 1
                    if i in boosted_meal_indices: 
                        continue
                    
                    # Identifies if we are currently looking at Breakfast.
                    # This is important because we want to avoid adding savory carb boosters (like bread or pasta) to breakfast meals that are primarily sweet (like oatmeal).
                    slot_name = meal.get('slot_name', '').lower()
                    # i==0 means breakfast because breakfast is always the first meal in the list. This is a fallback in case slot_name is missing or not standardized.
                    is_breakfast = 'breakfast' in slot_name or i == 0
                    
                    main_name = meal.get('main_dish', {}).get('name', '').lower()
                    side_name = meal.get('side_dish', {}).get('name', '').lower()
                    
                    # Skip "Sweet" breakfasts (Oatmeal) to avoid adding savory sides.
                    if any(k in main_name for k in self.BREAKFAST_ONLY_AND_SNACK_WORDS): 
                        continue
                    # If the meal already has 3 extra items - stop
                    if len(meal.get('boosters', [])) >= 3: 
                        continue
                    
                    # Filter options
                    current_options = all_boosters.copy()
                    
                    # Removing duplicates: If we have already used "Whole Wheat Bread" as a booster in Meal 1, we don't want to add it again in Meal 3. 
                    # This ensures variety across meals and prevents the same carb source from being added multiple times in the same day.
                    if used_booster_names:
                        current_options = current_options[~current_options['name'].isin(used_booster_names)]
                        
                    # Remove items that are already in this meal that are similar like "White Rice" and "Brown Rice". We don't want to add "Brown Rice" booster to a meal that already has "White Rice" as a main or side dish.
                    current_options = current_options[
                        ~current_options['name'].apply(lambda x: self._foods_are_similar(x, main_name) or self._foods_are_similar(x, side_name))
                    ]
                    
                    
                    if is_breakfast:
                        #  It removes "Savory" items like Pasta, Rice, Noodles, Beans, Soup.
                        current_options = current_options[
                            ~current_options['name'].str.contains('|'.join(savory_exclude_for_breakfast), case=False, regex=True)
                        ]
                        # Throwing away everything else and only keeps breakfast foods
                        if 'is_breakfast' in current_options.columns:
                            tagged = current_options[current_options['is_breakfast'] == True]
                            if not tagged.empty: 
                                current_options = tagged
                    else:
                        if 'is_breakfast' in current_options.columns:
                            # Remove foods strictly marked as breakfast-only
                            current_options = current_options[current_options['is_breakfast'] == False]
                        # Removing items with names like "Cereal", "Porridge"
                        current_options = current_options[
                            ~current_options['name'].str.contains(
                                '|'.join(self.BREAKFAST_ONLY_AND_SNACK_WORDS), case=False, regex=True
                            )
                        ]
                    
                    # Does the main dish already involve bread?
                    meal_has_bread = any(k in str(meal).lower() for k in self.BREAD_KEYWORDS)
                    # Did we add bread to a previous meal today?
                    if bread_used_globally or meal_has_bread:
                        current_options = current_options[
                            ~current_options['name'].str.contains('|'.join(self.BREAD_KEYWORDS), case=False, regex=True)
                        ]
                    
                    if current_options.empty: 
                        continue
                    
                    # Picking randomly from top 3 to ensure variety
                    top_candidates = current_options.head(3)
                    booster = top_candidates.sample(1).iloc[0].to_dict()
                    
                    # Tracking usage
                    used_booster_names.add(booster['name'])
                    booster_name = booster['name'].lower()
                    
                    # If the booster we are adding is bread-based, we set the flag to True so that no other meal can add a bread-based booster. 
                    # This ensures that we don't end up with multiple bread items across meals, which could lead to an unbalanced and carb-heavy day.
                    if any(k in booster_name for k in self.BREAD_KEYWORDS):
                        bread_used_globally = True
                    
                    # Calculate Grams
                    carb_per_100g = booster.get(self.COL_CARBS, 0)
                    target_for_this_meal = carb_deficit / eligible_meals_count
                    
                    
                    if carb_per_100g > 0:
                        #  We aim for 90% of the gap, not 100%, to avoid over-boosting
                        ideal_grams = (target_for_this_meal * 0.90 / carb_per_100g) * 100
                        # 
                        grams = max(ideal_grams, 50) # Floor: Minimum 50g
                        grams = min(grams, 180)  # Ceiling: Maximum 180g
                    else:
                        grams = 60.0 # Fallback portion size when carb data is missing, set to a reasonable default for carb boosters.
                    
                    grams = round(grams, 0) # Removes decimals
                    scalar = grams / 100.0 # Convert grams to a math multiplier, so we get the correct macros based on the db values which are per 100g.
                    
                    new_booster = {
                        "name": booster['name'], "grams": grams, "reason": "Carb Boost",
                        "macros": {
                            "p": round(booster.get(self.COL_PROTEIN, 0) * scalar, 1),
                            "c": round(booster.get(self.COL_CARBS, 0) * scalar, 1),
                            "f": round(booster.get(self.COL_FAT, 0) * scalar, 1)
                        }, "full_profile": booster
                    }
                    
                    # It checks if the list exists (create it if not).
                    if 'boosters' not in meal: meal['boosters'] = []
                    # Adding the new booster to the meal's boosters list. 
                    # This is where the new carb source gets officially added to the meal plan.
                    meal['boosters'].append(new_booster)
                    
                    #  Manually add the new macros to the meal's running totals
                    added_c = new_booster['macros']['c']
                    meal['total_macros']['protein'] += new_booster['macros']['p']
                    meal['total_macros']['carbs'] += added_c
                    meal['total_macros']['fat'] += new_booster['macros']['f']
                    
                    # After adding the booster, we reduce the carb_deficit by the amount of carbs we just added. 
                    # We also decrement the eligible_meals_count because we've just boosted one meal, so there are now fewer meals left to distribute the remaining carb deficit across. 
                    carb_deficit -= added_c
                    eligible_meals_count -= 1 
                    if eligible_meals_count < 1: 
                        eligible_meals_count = 1 # Safety check: Ensures we never divide by zero in the next iteration.
                    
                    print(f"Added Carb Booster ({'Breakfast' if is_breakfast else 'Main'}): {booster['name']} ({grams}g) -> +{added_c:.1f}g carbs")

        return meals
    
    # Main function to find a single food recommendation based on target macros and filters. This is used for snack recommendations and also as a fallback when we cannot find good composite meals.
    def find_single_food(self, target_macros: dict, meal_type: str = "snack", only_healthy: bool = True, ignore_names: list = None, ignore_keywords = None, include_keywords = None, craving_keywords = None):
        if ignore_names is None: 
            ignore_names = []
        
        # 1. Filters
        allowed_processing = self.ALLOWED_PROCESSING_LEVELS if only_healthy else ['unprocessed', 'processed', 'ultra_processed']
        filters = {'processing_level': allowed_processing}
        
        if meal_type == "snack": 
            filters['category'] = ['snack', 'supplement']
        elif meal_type == "breakfast": 
            filters['category'] = ['main', 'snack']
            filters['is_breakfast'] = True 
        else:
            filters['category'] = 'main'
            
        exclude_list = (ignore_keywords or []) + self.ALCOHOL_KEYWORDS
        
        # 2. Model creation 
        model, filtered_df = self._get_model_for_filter(filters, ignore_keywords=exclude_list, include_keywords=include_keywords, craving_keywords=craving_keywords)
        
        # Breakfast Fallback: If strict search fails, try generic
        if model is None and meal_type == "breakfast":
            if 'is_breakfast' in filters: del filters['is_breakfast']
            model, filtered_df = self._get_model_for_filter(filters, ignore_keywords=ignore_keywords, include_keywords=include_keywords, craving_keywords=craving_keywords)
            
        if model is None: 
            return []
        
        # 3. Search
        # Uses explicit columns if defined, otherwise strings
        p_col = getattr(self, 'COL_PROTEIN', "protein, total (g)")
        c_col = getattr(self, 'COL_CARBS', "carbohydrate, available (g)")
        f_col = getattr(self, 'COL_FAT', "fat, total (g)")

        # Creating a DataFrame for the target macros to feed into the KNN model. This DataFrame has the same structure as the one used to train the model, ensuring that the KNN algorithm can compute distances correctly.
        target_vector = pd.DataFrame([[
            target_macros.get(p_col, 0), 
            target_macros.get(c_col, 0), 
            target_macros.get(f_col, 0)
        ]], columns=self.features)
        
        distances, indices = model.kneighbors(target_vector, n_neighbors=min(self.k, len(filtered_df)))
        
        # List to hold the final recommendations that will be returned to the user after processing and optimization.
        recommendations = []
        # Looping through the nearest neighbors returned by the KNN model. For each neighbor, we perform a series of checks and calculations to determine if it should be included in the recommendations, and if so, how it should be portioned and optimized based on the target macros and user preferences.
        for i, idx in enumerate(indices[0]):
            item = filtered_df.iloc[idx].to_dict()
            name_lower = item['name'].lower()
            
            # Check exact match exclusion, ignoring foods that are in the ignore_names list.
            if item['name'] in ignore_names:
                continue
            
            # Avoiding coffee/tea as snacks since they are not filling and can throw off the meal balance.
            # We allow them only if explicitly asked for, otherwise block them.
            if any(k in name_lower for k in self.NON_MEAL_DRINKS):
                # But allow if it's a "Latte" or "Cappuccino" with milk (calories > 50)
                if item.get('energy_kcal', 0) < 50:
                    continue
                
            # 2. Min kcal threshold for snacks: We want to ensure that snack recommendations are substantial enough to be satisfying and worth consuming.
            # A "Main Snack" needs at least 50 calories to be worth listing.
            if item.get('energy_kcal', 0) < 50 and target_macros.get('calories', 100) > 50:
                continue
            
            # Relaxing similarity restrictions
            # If user asked for "Avocado", allow Avocado snack even if used in lunch
            is_requested = False
            if include_keywords:
                is_requested = any(req.lower() in name_lower for req in include_keywords)
            
            # Ebters only if there are no requested foods, so  to ensure that there is no repitiotion of the same food across meals, but allows it if the user explicitly asked for it.
            if not is_requested:
                if any(self._foods_are_similar(item['name'], ignored) for ignored in ignore_names): 
                    continue
                    
            # 4. Calculating portion
            t_p = target_macros.get(p_col, 0)
            t_c = target_macros.get(c_col, 0)
            
            # This check is used to determine if we should allow a larger portion size for this item.
            # The food cannot be supplement or snack category
            is_large_portion = (item.get('category') != 'supplement') and (meal_type != 'snack')
            
            # Ensures that the powdered supplements are portioned correctly based on the more limiting macro (protein or carbs), since they often have very different densities and we want to avoid recommending an unrealistic portion size that would be required to meet the target macros.
            if item.get('category') == 'supplement': 
                grams = self._calculate_portion(item, t_p, p_col, is_main_dish=False)
            # Decoding which macro dictae the size
            # High protein needed
            elif t_p > t_c: 
                grams = self._calculate_portion(item, t_p, p_col, is_main_dish=is_large_portion)
            # High carb needed
            else: 
                grams = self._calculate_portion(item, t_c, c_col, is_main_dish=is_large_portion)
             
            # 5. Building object
            # Calculate raw macros for the main item
            p_val = (item[self.features[0]] * grams) / 100
            c_val = (item[self.features[1]] * grams) / 100
            f_val = (item[self.features[2]] * grams) / 100

            meal_obj = {
                "type": "single_food",
                "main_dish": {
                    "name": item['name'],
                    "sub_category": item.get('sub_category', 'generic'),
                    "grams": grams,
                    "processing_level": item.get('processing_level', 'unknown'),
                    "pairing_tag": item.get('pairing_tag', 'none'),
                    # Add macros to main_dish so scaler can read them
                    "macros": {"p": p_val, "c": c_val, "f": f_val}
                },
                "total_macros": {
                    "protein": p_val,
                    "carbs": c_val,
                    "fat": f_val
                },
                "knn_distance": float(distances[0][i])
            }   
            
            # 6. Optimize with boosters and scale to target macros. This step takes the initial recommendation from the KNN model and applies any necessary adjustments (like adding protein or carb boosters) to better align with the user's target macros, and then scales the portion size to ensure that the final recommendation is as close as possible to the desired nutritional profile.
            meal_with_boosters = self._optimize_with_boosters(meal_obj, target_macros, ignore_keywords=ignore_keywords)
            final_meal = self._scale_meal_to_target(meal_with_boosters, target_macros)
            
            recommendations.append(final_meal)
            if len(recommendations) >= 3:
                break 
            
        return recommendations
    
    # Main function to find a composite meal (main + side) recommendation based on target macros and filters. This is the core function for generating lunch and dinner recommendations, where we want to create a balanced meal that meets the user's nutritional goals while also adhering to their preferences and restrictions.
    def find_composite_meal(self, target_macros: dict, meal_type: str = "lunch", only_healthy: bool = True, ignore_names: list = None, ignore_keywords = None, include_keywords = None, craving_keywords = None):
        
        if ignore_names is None:
            ignore_names = []
        
        # Extracting the numerical goals for this specific meal
        total_p = target_macros.get(self.COL_PROTEIN, 0)
        total_c = target_macros.get(self.COL_CARBS, 0)
        total_f = target_macros.get(self.COL_FAT, 0)
        
        # Allowed processing levels depend on the "only_healthy" flag. If only_healthy is True, we restrict to cleaner options; if False, we expand the pool to include more processed foods.
        allowed_processing = self.ALLOWED_PROCESSING_LEVELS if only_healthy else ['unprocessed', 'processed', 'ultra_processed']
        
        # Main dish filters
        # 1. Setup Filters
        # Base Rule: Must be a solid food (not milk/soup), must be processed correctly, and MUST be categorized as 'main' in the db.
        main_filters = {'processing_level': allowed_processing, "is_liquid": False, "category": "main"}

        if meal_type == "breakfast": 
            main_filters['is_breakfast'] = True
            # For breakfast, we allow both "main" and "snack" categories to be considered for the main dish, since many breakfast items like yogurt might be categorized as snacks but can serve as a main meal.
            main_filters['category'] = ['main', 'snack']
        
        # Filters the whole database down to just the eligible Main Dishes.
        # It applies exclusions (allergies) and inclusions (cravings).
        main_model, main_df = self._get_model_for_filter(main_filters, ignore_keywords=ignore_keywords, include_keywords=include_keywords, craving_keywords=craving_keywords )
        
        # Fallback 
        if main_model is None and meal_type == "breakfast":
            if 'is_breakfast' in main_filters:
                del main_filters['is_breakfast']
            main_model, main_df = self._get_model_for_filter(main_filters, ignore_keywords=ignore_keywords, include_keywords=include_keywords, craving_keywords=craving_keywords)
        
        if main_model is None:
            return []
        
    
        # We expect the main dish to provide 70% of the protein.
        main_target_p = total_p * 0.70 
        # We expect the main dish to provide only 20% of the carbs (Carbs usually come from sides).
        main_target_c = total_c * 0.20 
        # Fat target depends on carb goal - if very low carb, we want more fat in the main dish to keep it satisfying and avoid a tiny 50g salad with 5g of fat. If higher carb, we can allow a lighter main and more filling sides.
        main_target_f = total_f * 0.20 if total_c > 120 else total_f * 0.12
        
        # Fat target depends on carb goal
        if total_c > 120:
            main_target_f = total_f * 0.25  # More conservative
        else:
            main_target_f = total_f * 0.40
        
        # Creating the math vector to search for
        main_target = pd.DataFrame(
            [[main_target_p, main_target_c, main_target_f]], 
            columns=[self.COL_PROTEIN, self.COL_CARBS, self.COL_FAT]
        )
        
        # Asking KNN for the closest matches in the database
        dists_m, indices_m = main_model.kneighbors(main_target, n_neighbors=min(self.k, len(main_df)))
        
        recommendations = []
        seen_names = set(ignore_names) if ignore_names else set()
        
        # Looping through the candidates
        for i, main_idx in enumerate(indices_m[0]):
            if len(recommendations) >= 3:
                break
            
            # iloc accesses the row of the DataFrame at the position main_idx, which corresponds to one of the nearest neighbors found by the KNN model. This row contains all the information about that particular food item (like its name, macros, category, etc.).
            # .to_dict() converts the row of the DataFrame corresponding to the current index into a dictionary, which allows for easier access to the food's attributes like name, macros, category.
            main_food = main_df.iloc[main_idx].to_dict()

            # Check exact match to avid repitions of the same food across meals, but allows it if the user explicitly asked for it in include_keywords.
            if main_food['name'].strip().lower() in seen_names:
                continue

            # Checking siilarity
            # This logic allows foods that are similar to be included if they were explicitly requested by the user, even if they have similar names to other items in the meal plan. 
            is_requested = False
            if include_keywords:
                is_requested = any(req.lower() in main_food['name'].lower() for req in include_keywords)
            
            # Only block similar foods if they were not explicitly requested
            if not is_requested:
                if any(self._foods_are_similar(main_food['name'], name) for name in seen_names): 
                    continue
    
            # Blocking breakfast items in lunch/dinner
            if meal_type != "breakfast":
                name_lower = main_food['name'].lower()
                if any(k in name_lower for k in self.BREAKFAST_ONLY_AND_SNACK_WORDS):
                    continue
            
            # Calculating grams needed to hit the target protein.
            grams_main = self._calculate_portion(main_food, main_target_p, self.COL_PROTEIN, is_main_dish=True)
            
            # Forcing the portion to be at least 200g (for a main meal) but not huge
            grams_main = max(200.0, min(grams_main, self._get_max_portion(main_food)))
            
            # Calculating exactly how much P/C/F this portion provides.
            scalar_main = grams_main / 100.0
            p_p = main_food[self.COL_PROTEIN] * scalar_main
            p_c = main_food[self.COL_CARBS] * scalar_main
            p_f = main_food[self.COL_FAT] * scalar_main
            
            # Calculating the gap. This is what the side dish must fill.
            rem_p = max(0, total_p - p_p)
            rem_c = max(0, total_c - p_c)
            rem_f = max(0, total_f - p_f)
            
            # Side should fill the carb gap
            side_filters = {'category': 'side', 'processing_level': allowed_processing}
            
            if meal_type == "breakfast":
                side_filters['is_breakfast'] = True
                # For breakfast, we allow both "main" and "snack" categories to be considered for the main dish, since many breakfast items like yogurt might be categorized as snacks but can serve as a main meal.
                side_filters['category'] = ['side', 'snack']
            
            # Keto Logic: If Carbs are low (<100g), force veggies.
            is_strict_low_carb = total_c < 100
            
            if is_strict_low_carb:
                side_filters['sub_category'] = ['veg']
            else:
                # Normal logic for balanced diets
                if rem_c > 35:
                    side_filters['sub_category'] = ['starch']
                elif rem_c > 15:
                    side_filters['sub_category'] = ['veg', 'vegetarian'] 
                else:
                    side_filters['sub_category'] = ['veg']
            # This function applies the filters defined in side_filters to the food database, and then trains a KNN model on the resulting subset of foods. 
            # Applying the ignore_keywords, include_keywords, and craving_keywords to further refine the selection of foods that will be considered as potential side dishes for the meal recommendation.
            side_model, side_df = self._get_model_for_filter(
                side_filters, 
                ignore_keywords=ignore_keywords, 
                include_keywords=include_keywords,
                craving_keywords=craving_keywords
            )
            
            # Fallback logic
            # Fallback 1: If 'starch' failed, try 'starch' + 'generic' + 'bakery'
            if side_model is None and side_filters.get('sub_category') == ['starch']:
                side_filters['sub_category'] = ['starch', 'generic', 'bakery']
                side_model, side_df = self._get_model_for_filter(
                side_filters, 
                ignore_keywords=ignore_keywords, 
                include_keywords=include_keywords,
                craving_keywords=craving_keywords
            )
            # Fallback 2: If sub_category filter is too strict and yields no results, remove it and try again to get any side dish that can fill the carb gap, even if it's not the perfect match.
            if side_model is None and 'sub_category' in side_filters:
                del side_filters['sub_category']
                side_model, side_df = self._get_model_for_filter(
                side_filters, 
                ignore_keywords=ignore_keywords, 
                include_keywords=include_keywords,
                craving_keywords=craving_keywords
            )
            
            # Final Fallback for Breakfast: If we are doing breakfast and still have no sides, we can relax the filters to include any breakfast-appropriate sides/snacks, since breakfast can be more flexible and we want to ensure we can find something to fill the carb gap.
            if side_model is None and meal_type == "breakfast":
                if 'is_breakfast' in side_filters:
                    del side_filters['is_breakfast']
                side_filters['category'] = ['side', 'snack']
                side_model, side_df = self._get_model_for_filter(
                    side_filters, 
                    ignore_keywords=ignore_keywords, 
                    include_keywords=include_keywords,
                    craving_keywords=craving_keywords
                )
            
            # If we still can't find any sides, we skip adding a side dish and move on to the next main dish candidate.
            if side_model is None:
                continue
            
            # Smart Targeting
            # If we need Carbs, we ignore Fat limits for the side dish search.
            # This helps matches like Oats/Rice (which might have 3g fat) even if we strictly have 0g fat left.
            search_f = 0.5 if rem_c > 20 else rem_f
            
            side_target_p = rem_p * 0.5
            # Allowing sides to contribute more carbs
            side_target_c = min(rem_c * 0.80, 100.0)  # Aim to fill 80% of carb gap
            side_target_f = min(rem_f * 0.25, 4.0)  
            
            side_target = pd.DataFrame([[side_target_p, side_target_c, side_target_f]], columns=self.features)
            # Running KNN for search
            dists_s, indices_s = side_model.kneighbors(side_target, n_neighbors=min(self.k, len(side_df)))
            
            selected_side = None
            for s_idx in indices_s[0]:
                candidate = side_df.iloc[s_idx].to_dict()
                cand_name = candidate['name'].strip().lower()
                
                # BLOCK BREAKFAST SIDES IN LUNCH/DINNER
                if meal_type != "breakfast":
                    if any(k in cand_name for k in self.BREAKFAST_ONLY_AND_SNACK_WORDS):
                        continue
                
                # Check exact match
                if cand_name in seen_names:
                    continue
                
                # Check similarity
                is_similar = any(self._foods_are_similar(candidate['name'], name) for name in seen_names)
                if is_similar:
                    continue
                
                # Check if side is too similar to main dish
                if self._foods_are_similar(candidate['name'], main_food['name']):
                    continue
                
                selected_side = candidate
                break
                        
            if not selected_side:
                continue
            
            # Tracking visited names to avoid repetition across meals
            seen_names.add(main_food['name'].strip().lower())
            seen_names.add(selected_side['name'].strip().lower())
            
            # Size side to fill carb gap - SMART SIZING based on density
            grams_side = self._calculate_portion(selected_side, side_target_c, self.COL_CARBS, is_main_dish=False)

            # Dynamic minimum based on carb density
            side_carb_density = selected_side.get(self.COL_CARBS, 0)
            if side_carb_density > 20:  # High carb density (pasta, rice)
                min_portion = 80.0
            elif side_carb_density > 10:  # Medium density
                min_portion = 120.0
            else:  # Low density vegetables
                min_portion = 150.0

            # Ensuring the side dish is not too small (for low-carb sides) or too large (for high-carb sides)
            grams_side = max(min_portion, min(grams_side, self._get_max_portion(selected_side)))
            scalar_side = grams_side / 100.0
            
            # Calculating the macros for the side dish based on the portion size.
            s_p = selected_side[self.COL_PROTEIN] * scalar_side
            s_c = selected_side[self.COL_CARBS] * scalar_side
            s_f = selected_side[self.COL_FAT] * scalar_side
            
            # Calculating the combined macros of the main and side dishes to see how much of the target macros are still remaining and to determine if we need to add a soup or drink to fill any significant gaps, especially in protein.
            current_p = p_p + s_p
            current_c = p_c + s_c
            current_f = p_f + s_f
            
            # Calculate remaining gaps for soup/drink
            soup_item = None
            drink_item = None
            
            # Gaps are calculated to determine how much more protein, carbs, and fat we need to reach the target macros after accounting for the main and side dishes. 
            # This helps us decide if we need to add a soup or drink to fill those gaps, and if so, how much of each macro we should be targeting with those additions.
            gap_p = max(0, total_p - current_p)
            gap_c = max(0, total_c - current_c)
            gap_f = max(0, total_f - current_f)
            
            # Calculating calorie gap to inform soup/drink addition. If we are significantly under the calorie target, we might want to be more aggressive in adding a soup or drink
            target_cal = target_macros.get('calories') or (total_p * 4) + (total_c * 4) + (total_f * 9)
            current_cal = (current_p * 4) + (current_c * 4) + (current_f * 9)
            cal_gap = target_cal - current_cal
            # Checking current carb status before adding
            current_carb_percent = (current_c / total_c) if total_c > 0 else 0

            # Only add soup if we need protein/calories AND carbs aren't already high
            carb_safe = current_carb_percent < 0.85  # Only if under 85% carb target

            # The logic for adding a soup is designed to be conservative and only trigger if there is a significant protein gap (greater than 15g) or a significant calorie gap (greater than 350 calories), and if the current carb percentage is below 85% of the target. 
            if (gap_p > 15 or cal_gap > 350) and carb_safe:
                soup_target = {
                    self.COL_PROTEIN: gap_p,
                    self.COL_CARBS: min(gap_c, 10),  # Capping carb contribution from soup
                    self.COL_FAT: gap_f
                }
                # The function _find_soup is responsible for searching the database for a soup that matches the specified macro targets (soup_target) while also adhering to the allowed processing levels and avoiding any foods that are in the seen_names list or contain any of the ignore_keywords.
                soup_item = self._find_soup(soup_target, allowed_processing, list(seen_names), is_breakfast=(meal_type == "breakfast"), ignore_keywords=ignore_keywords)
                 
                # If we find a soup, we add its macros to the current totals and recalculate the gaps. 
                if soup_item:
                    seen_names.add(soup_item['name'].strip().lower())
                    current_p += soup_item['macros']['p']
                    current_c += soup_item['macros']['c']
                    current_f += soup_item['macros']['f']
                    current_cal = (current_p * 4) + (current_c * 4) + (current_f * 9)
                    
                    # Recalculates gaps
                    gap_p = max(0, total_p - current_p)
                    gap_c = max(0, total_c - current_c)
                    gap_f = max(0, total_f - current_f)
                    cal_gap = target_cal - current_cal
            
            # Recalculates carb safety after potential soup addition
            current_carb_percent = (current_c / total_c) if total_c > 0 else 0
            carb_safe_for_drink = current_carb_percent < 0.80  # Stricter threshold

            # Add drink ONLY if significant protein gap remains AND carbs are safe
            if gap_p > 15 and carb_safe_for_drink and cal_gap > 250:
                # Prioritize protein, minimize carbs if already high
                carb_percent = current_c / total_c if total_c > 0 else 0

                if carb_percent > 0.75:
                    # Already have lots of carbs - search for high-protein, low-carb drink
                    drink_target = {
                        self.COL_PROTEIN: gap_p,
                        self.COL_CARBS: min(10, gap_c),  # Force low-carb search
                        self.COL_FAT: max(3, gap_f) if current_f < total_f * 0.9 else 0
                    }
                else:
                    drink_target = {
                        self.COL_PROTEIN: gap_p,
                        self.COL_CARBS: min(15, gap_c) if gap_c > 0 else 0,
                        self.COL_FAT: max(3, gap_f) if current_f < total_f * 0.9 else 0
                    }
                drink_item = self._find_drink(drink_target, allowed_processing, list(seen_names), ignore_keywords=ignore_keywords)
                
                if drink_item:
                    seen_names.add(drink_item['name'].strip().lower())
                    current_p += drink_item['macros']['p']
                    current_c += drink_item['macros']['c']
                    current_f += drink_item['macros']['f']
            
            
            # Compile meal
            combo = {
                "type": "composite_meal",
                "main_dish": {
                    "name": main_food['name'],
                    "grams": grams_main,
                    "processing_level": main_food.get('processing_level', 'unknown'),
                    "pairing_tag": main_food.get('pairing_tag', 'none'),
                    "sub_category": main_food.get('sub_category', 'generic'),
                    "macros": {"p": round(p_p, 1), "c": round(p_c, 1), "f": round(p_f, 1)}
                },
                "side_dish": {
                    "name": selected_side['name'],
                    "grams": grams_side,
                    "processing_level": selected_side.get('processing_level', 'unknown'),
                    "pairing_tag": selected_side.get('pairing_tag', 'none'),
                    "sub_category": selected_side.get('sub_category', 'generic'),
                    "macros": {"p": round(s_p, 1), "c": round(s_c, 1), "f": round(s_f, 1)}
                },
                "total_macros": {
                    "protein": round(current_p, 1),
                    "carbs": round(current_c, 1),
                    "fat": round(current_f, 1)
                },
                "knn_distance": (dists_m[0][i] + dists_s[0][0]) / 2
            }
            
            if soup_item: 
                combo["soup"] = soup_item
            if drink_item: 
                combo["drink"] = drink_item

            # After compiling the initial meal recommendation with the main dish, side dish, and optional soup and drink, we then pass this combo through the _optimize_with_boosters function to see if we can add any additional items (like a small carb booster or protein booster) to better align the meal with the target macros.
            final_combo = self._optimize_with_boosters(combo, target_macros, ignore_keywords=ignore_keywords)
            # Finally, we scale the entire meal (main + side + soup + drink + boosters) to ensure that the portion sizes are adjusted so that the final macros of the meal are as close as possible to the user's target macros, while still maintaining the balance and composition of the meal.
            final_combo = self._scale_meal_to_target(final_combo, target_macros)
            recommendations.append(final_combo)
            
            # Retry
            # If we failed to find anything because the user's keywords were too specific,try again without the keywords.
            if not recommendations and include_keywords:
                print("Focused search returned 0 results. Retrying with general database...")
                return self.find_composite_meal(
                    target_macros, meal_type, only_healthy, ignore_names, 
                    ignore_keywords, include_keywords=None # Remove restrictions
                )
            
        return recommendations