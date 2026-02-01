import os
import json
import time
import requests
from dotenv import load_dotenv
from db_access import supabase

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Valid NOVA categories
VALID_LEVELS = [
    "unprocessed", # NOVA Group 1: Whole foods (Fresh meat, veg, eggs, milk, grains)
    "culinary_ingredient", # NOVA Group 2: Culinary ingredients (Oils, Salt, Sugar)
    "processed",        # NOVA Group 3: Simple changes (Cheese, fresh bread, canned veg, salted nuts)
    "ultra_processed"   # NOVA Group 4: Industrial (Soda, nuggets, chips, flavored yogurt, instant meals)
]

def classify_processing_batch(food_names, max_retries=3):
    # Uses Gemini to determine the NOVA processing level of foods.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    # PROMPT BASED ON NOVA CLASSIFICATION
    prompt_text = f"""
    You are an expert nutritionist using the NOVA Food Classification system.
    Classify the following food items into exactly ONE of these categories:

    1. "unprocessed": Whole foods (Meat, Veg, Fruit, Milk, Eggs, Grains).
    
    2. "culinary_ingredient": (NOVA Group 2) substances extracted from Group 1 used for cooking.
       - Examples: Butter, Lard, Vegetable Oils, Sugar, Salt, Vinegar, Honey.
       
    3. "processed": (NOVA Group 3) Group 1 foods modified with Group 2.
       - Examples: Cheese, Canned Veg, Salted Nuts, Smoked Meats, Fresh Bread.
       
    4. "ultra_processed": (NOVA Group 4) Industrial formulations.
       - Examples: Soda, Chips, Nuggets, Margarine, Instant Noodles. This will not include, for instance, unflavored yogurt or bread with good ingredients.

    Return a JSON object where the key is the exact "Food Name" provided, and the value is the category string.

    Input Foods:
    {json.dumps(food_names)}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                text_content = result['candidates'][0]['content']['parts'][0]['text']
                return json.loads(text_content)
            else:
                print(f"Error {response.status_code}")
                time.sleep(1)
        except Exception as e:
            print(f"Exception: {e}")
            time.sleep(1)
            
    return {}

def main():
    print("Starting Processing Tagging...")
    
    while True:
        # Fetch foods where 'processing_level' is NULL
        response = supabase.table('foods').select("id, name").is_("processing_level", "null").limit(50).execute()
        if not response.data:
            response = supabase.table('foods').select("id, name").eq("processing_level", "{}").limit(50).execute()
        
        foods = response.data
        if not foods:
            print("\nAll foods tagged for processing level! Exiting.")
            break

        print(f"\nProcessing batch of {len(foods)} foods...")
        
        food_names = [f['name'] for f in foods]
        
        # Call AI
        health_map = classify_processing_batch(food_names)
        
        batch_updates = []
        
        for food in foods:
            name = food['name']
            
            # Get result from AI
            level = health_map.get(name)
            
            if level:
                level = level.lower()
                # Validation: Force strict categories
                if level not in VALID_LEVELS:
                    # Fallback logic: If AI is unsure, usually it's at least processed
                    level = "processed" 
            else:
                # Fail-safe: AI missed it, mark as processed to stop infinite loop
                print(f"AI missed '{name}', marking as 'processed'.")
                level = "processed"

            batch_updates.append({
                "id": food['id'],
                "processing_level": level
            })
            print(f"Prepared: {name[:25]}... -> {level}")

        # Send Update
        try:
            if batch_updates:
                supabase.table('foods').upsert(batch_updates).execute()
                print(f"Successfully updated {len(batch_updates)} rows.")
        except Exception as e:
            print(f"Database Update Error: {e}")

        print("Sleeping 5s...")
        time.sleep(5)

if __name__ == "__main__":
    main()