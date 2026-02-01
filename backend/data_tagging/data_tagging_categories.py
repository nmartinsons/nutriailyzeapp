import os
import json
import time
import requests
from dotenv import load_dotenv
from db_access import supabase

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Define valid categories for validation
VALID_CATEGORIES = [
    "main",       
    "side",    
    "ingredient", 
    "snack",      
    "supplement"  
]

def classify_batch_with_retry(food_names, max_retries=3):
    """
    Uses direct HTTP Request to Gemini to classify foods into categories.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    
    # PROMPT FOR CATEGORIES
    prompt_text = f"""
    You are an expert nutritionist. 
    Classify the following food items into exactly ONE of these categories:
    
    1. "main": High protein or complete meals (Chicken, Steak, Fish, Tofu, Stews, Pasta dishes).
    2. "side": Starchy carbs or vegetables usually eaten with a main (Rice, Potatoes, Bread, Steamed Broccoli).
    3. "ingredient": Items not eaten alone or raw (Flour, Oil, Salt, Spices, Baking Powder, Raw Dough, Vinegar). This can also involve ingredients used for making bigger foods.
    4. "snack": Ready-to-eat small items (Apple, Nuts, Yogurt, Chocolate, Protein Bar).
    5. "supplement": Powders (Whey, Casein) or pills.
    
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
                return {}
        except Exception as e:
            print(f"Exception: {e}")
            return {}
            
    return {}

def main():
    print("Starting Category Tagging...")
    
    while True:
        # Look for NULL 'category'
        response = supabase.table('foods').select("id, name").is_("category", "null").limit(50).execute()
        if not response.data:
            response = supabase.table('foods').select("id, name").eq("category", "{}").limit(50).execute()
        
        foods = response.data
        if not foods:
            print("\nAll foods categorized! Exiting.")
            break

        print(f"\nProcessing batch of {len(foods)} foods...")
        
        food_names = [f['name'] for f in foods]
        
        # Call AI
        category_map = classify_batch_with_retry(food_names)
        
        if category_map:
            batch_updates = []
            
            for food in foods:
                name = food['name']
                # Get category, default to 'ingredient' if AI misses it to be safe
                cat = category_map.get(name, "ingredient").lower()
                
                # Validation: If AI invents a word, force it to 'ingredient'
                if cat not in VALID_CATEGORIES:
                    cat = "ingredient"
                
                batch_updates.append({
                    "id": food['id'],
                    "category": cat
                })
                print(f"Prepared: {name[:20]}... -> {cat}")

            # Send Update
            try:
                if batch_updates:
                    supabase.table('foods').upsert(batch_updates).execute()
                    print(f"Successfully updated {len(batch_updates)} rows.")
            except Exception as e:
                print(f"Database Update Error: {e}")
            
        else:
            print("AI returned no results.")

        print("Sleeping 5s...")
        time.sleep(5)

if __name__ == "__main__":
    main()