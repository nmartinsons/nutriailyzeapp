import os
import json
import time
import requests
from dotenv import load_dotenv
from db_access import supabase

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def classify_breakfast_batch(food_names, max_retries=3):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    prompt_text = f"""
    Analyze these foods and determine if they are common BREAKFAST items.
    
    Return a JSON object where the key is the exact "Food Name" and the value is true or false.
    
    Rules for TRUE:
    - Eggs, Porridge, Oatmeal, Cereal, Pancakes, Waffles, Toast.
    - Yogurt, Curd, Kefir, Milk, Cheese slices, Cottage cheese.
    - Fruits, Berries, Smoothies.
    - Bacon, Ham, Breakfast Sausages, Breakfast Burritos, Breakfast Sandwiches, Breakfast Wraps, Omelettes, Stewed Bean dishes.
    - Smoked salmon, Avocado toasts.
    
    Rules for FALSE:
    - Dinner meals (Stew, Soup, Roast, Pasta, Rice dishes, Wok).
    - Raw ingredients (Flour, Oil, Salt).
    - Desserts (Cake, Cookies) unless it is a pastry.
    
    Input Foods:
    {json.dumps(food_names)}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"response_mime_type": "application/json"}
    }
    
    for _ in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                return json.loads(response.json()['candidates'][0]['content']['parts'][0]['text'])
            elif response.status_code == 429:
                print("Quota limit. Waiting 10s...")
                time.sleep(10)
            else:
                print(f"API Error {response.status_code}")
                time.sleep(1)
        except Exception as e:
            print(f"Exception: {e}")
            time.sleep(1)
            
    return {}

def main():
    print("Tagging Breakfast Foods (Batch 50)...")
    
    while True:
        response = supabase.table('foods').select("id, name") \
            .in_("category", ["main", "side", "snack"]) \
            .is_("is_breakfast", "null") \
            .limit(50) \
            .execute()
            
        foods = response.data
        if not foods:
            print("All foods tagged.")
            break

        print(f"Processing batch of {len(foods)} items...")
        
        # Call AI
        food_names = [f['name'] for f in foods]
        tags_map = classify_breakfast_batch(food_names)
        
        updates = []
        for food in foods:
            is_break = tags_map.get(food['name'], False)
            
            updates.append({
                "id": food['id'], 
                "is_breakfast": is_break
            })
            
            if is_break:
                print(f"{food['name']}")
            
        if updates:
            try:
                supabase.table('foods').upsert(updates).execute()
                print(f"Saved {len(updates)} updates.")
            except Exception as e:
                print(f"DB Error: {e}")
        
        time.sleep(2)

if __name__ == "__main__":
    main()