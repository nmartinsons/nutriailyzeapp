import os
import json
import time
import requests
from dotenv import load_dotenv
from db_access import supabase

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Define valid sub-categories for validation
VALID_SUB_CATEGORIES = [
    "meat",       # Beef, Chicken, Pork, Lamb
    "fish",       # Fish, Seafood
    "vegetarian", # Tofu, Seitan, Meat substitutes
    "dairy",      # Milk, Cheese, Yogurt, Cream
    "starch",     # Rice, Pasta, Potato, Couscous, Quinoa (Good for heavy meals)
    "bakery",     # Bread, Rolls, Toast, Bagels (Good for sides, bad for heavy meal sides)
    "veg",        # Broccoli, Salad, Carrots, Spinach
    "fruit",      # Apple, Banana, Berries
    "nut",        # Almonds, Peanuts, Seeds
    "sweet",      # Chocolate, Candy, Ice cream
    "generic"     # Oils, Flour, Spices, or unknown
]

def classify_details_batch(food_names, max_retries=3):
    """
    Uses direct HTTP Request to Gemini to classify sub-category and liquid status.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    
    # PROMPT FOR SUB_CATEGORIES AND LIQUID STATUS
    prompt_text = f"""
    You are an expert nutritionist. Analyze these foods. 
    Return a JSON object where the key is the exact "Food Name" provided, and the value is an object with two keys: "sub_category" and "is_liquid".

    1. "sub_category" (Choose exactly one):
       - "meat", "fish", "vegetarian", "dairy"
       - "starch" (Rice, Pasta, Potato, Couscous, Grains)
       - "bakery" (Bread, Rolls, Toast, Buns, Pastry)
       - "veg" (Vegetables, Salad)
       - "fruit", "nut", "sweet"
       - "generic" (Oils, Spices, Flour, or if unsure)

    2. "is_liquid":
       - true (Milk, Soup, Smoothie, Oil, Sauce, Juices, Coffee)
       - false (Solid foods, purees, thick stews)

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
                # Don't return empty immediately on 500s, try again
                time.sleep(1)
        except Exception as e:
            print(f"Exception: {e}")
            time.sleep(1)
            
    return {}

def main():
    print("Starting Sub-Category & Liquid Tagging...")
    
    while True:
        # Look for NULL 'sub_category'
        # This prevents processing the same rows over and over
        response = supabase.table('foods').select("id, name").is_("sub_category", "null").limit(50).execute()
        if not response.data:
            response = supabase.table('foods').select("id, name").eq("sub_category", "{}").limit(50).execute()
        
        foods = response.data
        if not foods:
            print("\nAll foods sub-categorized! Exiting.")
            break

        print(f"\nProcessing batch of {len(foods)} foods...")
        
        food_names = [f['name'] for f in foods]
        
        # Call AI
        details_map = classify_details_batch(food_names)
        
        # Prepare updates
        batch_updates = []
        
        for food in foods:
            name = food['name']
            
            # Extract result from AI
            result = details_map.get(name)
            
            if result:
                # Get values
                sub = result.get("sub_category", "generic").lower()
                liq = result.get("is_liquid", False)
                
                # Validation: If AI returns a hallucinated category, force generic
                if sub not in VALID_SUB_CATEGORIES:
                    sub = "generic"
            else:
                # FAIL-SAFE: If AI ignored this item, mark it generic so we don't loop forever
                print(f"AI missed '{name}', marking generic.")
                sub = "generic"
                liq = False

            batch_updates.append({
                "id": food['id'],
                "sub_category": sub,
                "is_liquid": liq
            })
            print(f"Prepared: {name[:20]}... -> [{sub}] Liquid:{liq}")

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