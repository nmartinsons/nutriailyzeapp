import os
import json
import time
import requests
from dotenv import load_dotenv
from db_access import supabase

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def identify_boosters_batch(foods, max_retries=3):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    food_names = [f['name'] for f in foods]
    
    prompt_text = f"""
    You are an expert nutritionist building a database of "Health Boosters".
    Analyze the following list of foods. Identify ONLY the items that are commonly added to meals in small quantities to boost health (healthy fats, fiber, seeds, nuts, oils, superfoods).
    
    Ignore main dishes (Chicken, Rice, Bread) and Junk Food.
    
    Classify the valid boosters into one of these types:
    1. "healthy_fat" (healthy/unsaturated fats, omega-rich foods):
    Olive oil, avocado oil, walnuts, almonds, nut butters.

    2. "fiber" (dietary and prebiotic fiber sources):
    Chia seeds, flax seeds, psyllium husk, bran.

    3. "antioxidant" (polyphenol- and phytonutrient-rich foods):
    Blueberries, raspberries, goji berries, cacao nibs.

    
    Return a JSON object where the key is the exact "Food Name" and the value is the category ("healthy_fat", "fiber", or "antioxidant").
    If the food is NOT a booster, do not include it in the JSON.

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
            time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")
            
    return {}

def main():
    print("Extracting Health Boosters (All Rows)...")
    
    current_offset = 0
    batch_size = 1000 # Fetch 1000 at a time from DB
    
    while True:
        print(f"\n--- Fetching DB rows {current_offset} to {current_offset + batch_size} ---")
        
        # Fetch using .range() instead
        response = supabase.table('foods').select("id, name") \
            .in_("processing_level", ["unprocessed", "processed"]) \
            .range(current_offset, current_offset + batch_size - 1) \
            .execute()
        
        all_foods_in_chunk = response.data
        
        # Stop if no more data returned
        if not all_foods_in_chunk:
            print("Finished processing all foods.")
            break
            
        # 2. Process this chunk in smaller sub-batches for Gemini (50 at a time)
        gemini_batch_size = 50
        for i in range(0, len(all_foods_in_chunk), gemini_batch_size):
            batch = all_foods_in_chunk[i:i+gemini_batch_size]
            print(f"  Sending {len(batch)} items to Gemini...")
            
            # Ask Gemini
            boosters_found = identify_boosters_batch(batch)
            
            if boosters_found:
                db_inserts = []
                for food in batch:
                    name = food['name']
                    if name in boosters_found:
                        b_type = boosters_found[name]
                        
                        # Set grams
                        grams = 10
                        if b_type == 'antioxidant': grams = 80
                        elif b_type == 'healthy_fat' and 'oil' in name.lower(): grams = 10
                        elif b_type == 'healthy_fat': grams = 20
                        
                        db_inserts.append({
                            "food_id": food['id'],
                            "booster_type": b_type,
                            "recommended_grams": grams
                        })
                        print(f"    -> Found: {name}")
                
                # Insert
                if db_inserts:
                    try:
                        supabase.table('health_boosters').upsert(db_inserts, on_conflict="food_id").execute()
                        print(f"    Saved {len(db_inserts)} boosters.")
                    except Exception as e:
                        print(f"    DB Error: {e}")
            
            # Small sleep
            time.sleep(1)

        # Move the cursor forward for the next DB fetch
        current_offset += batch_size

if __name__ == "__main__":
    main()