import os
import json
import time
import requests
from dotenv import load_dotenv
from db_access import supabase

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def classify_pairings_batch(food_names, max_retries=3):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    prompt_text = f"""
    You are a nutritionist optimizing meals.
    Analyze these foods and assign a "pairing_tag" to determine if they need a nutritional boost.
    
    Categories:
    1. "needs_fiber": Plain Dairy (Yogurt, Skyr, Curd, Kefir, Cottage Cheese) or Plain Grains (Porridge, Oatmeal) or Cheese (Mozzarella). These need Berries/Seeds/Greens(Veggies).
    2. "needs_fat": Lean/Dry foods. Salads (Lettuce/Spinach without dressing), Lean Proteins (Chicken Breast, Turkey, White Fish, Tuna), Clear Soups. These need Healthy Fats.
    3. "none": Fatty meats (Steak, Salmon), Complete meals (Lasagna, Stew), Processed items, or Snacks.

    Return a JSON object: {{ "Food Name": "tag" }}
    
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
                text = response.json()['candidates'][0]['content']['parts'][0]['text']
                return json.loads(text)
            time.sleep(1)
        except:
            time.sleep(1)
    return {}

def main():
    print("Tagging Food Pairings...")
    
    while True:
        # Fetch foods without a tag (or generic default)
        # We look for NULL to start fresh, or you can check for 'none' if re-running
        response = supabase.table('foods').select("id, name").is_("pairing_tag", "null").limit(50).execute()
        foods = response.data
        if not foods: break

        print(f"Processing {len(foods)} items...")
        tags_map = classify_pairings_batch([f['name'] for f in foods])
        
        updates = []
        for food in foods:
            tag = tags_map.get(food['name'], "none").lower()
            if tag not in ["needs_fiber", "needs_fat"]: tag = "none" # Safety
            
            updates.append({"id": food['id'], "pairing_tag": tag})
            print(f"  {food['name'][:20]} -> {tag}")
            
        if updates:
            supabase.table('foods').upsert(updates).execute()
        
        time.sleep(1)

if __name__ == "__main__":
    main()