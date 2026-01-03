import os
import json
import time
import requests
from dotenv import load_dotenv
from db_access import supabase

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def categorize_batch_with_retry(food_names, max_retries=3):
    """
    Uses direct HTTP Request to Gemini to bypass SDK Auth conflicts.
    """
    # 1. The Endpoint URL (We use Gemini 2.0 Flash)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={GEMINI_API_KEY}"
    
    # 2. The Header
    headers = {"Content-Type": "application/json"}
    
    # 3. The Prompt & Body
    prompt_text = f"""
    You are an expert nutritionist and food safety officer. 
    Analyze the following food items from the Fineli database.
    Identify if they contain any of the **14 EU Major Allergens** listed by EFSA.
    
    Use strictly these tag names:
    1. "gluten" (Wheat, Rye, Barley, Oats)
    2. "crustaceans" (Crab, Lobster, Prawns, Shrimp)
    3. "eggs"
    4. "fish"
    5. "peanuts"
    6. "soy" (Soybeans)
    7. "milk" (Dairy, Lactose, Butter, Cheese, Yogurt)
    8. "nuts" (Tree nuts: Almonds, Hazelnuts, Walnuts, Cashews, Pecans, Brazil, Pistachio, Macadamia)
    9. "celery"
    10. "mustard"
    11. "sesame"
    12. "sulphites" (Sulphur dioxide, often in dried fruits, processed meat, wine)
    13. "lupin"
    14. "molluscs" (Mussels, Oysters, Squid, Snails)
    
    Return a JSON object where the key is the exact "Food Name" provided, and the value is a list of applicable tags.
    If no allergens are found, use an empty list [].
    
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
                # Gives the text from the first part of the first response candidate returned by Gemini
                text_content = result['candidates'][0]['content']['parts'][0]['text']
                return json.loads(text_content)
            elif response.status_code == 429:
                print(f"Quota Exceeded. Waiting 30s...")
                time.sleep(30) 
                continue 
            else:
                print(f"Error {response.status_code}")
                return {}
        except Exception:
            return {}
            
    return {}

def main():
    print("Starting Optimized Tagging...")
    
    # Loop until done
    while True:
        # Fetch batch
        response = supabase.table('foods').select("id, name").is_("allergens", "null").limit(50).execute()
        if not response.data:
            response = supabase.table('foods').select("id, name").eq("allergens", "{}").limit(50).execute()

        foods = response.data
        if not foods:
            print("\nAll foods tagged! Exiting.")
            break

        print(f"\nProcessing batch of {len(foods)} foods...")
        
        # Extract names for AI
        food_names = [f['name'] for f in foods]
        
        # Call AI
        tags_map = categorize_batch_with_retry(food_names)
        
        if tags_map:
            # Prepare a list of all updates
            batch_updates = []
            
            for food in foods:
                name = food['name']
                found_tags = tags_map.get(name, [])
                clean_tags = [t.lower() for t in found_tags]
                
                #  If the list is empty, 'none' is added so it is not picked up again
                if not clean_tags:
                    clean_tags = ["none"]
                
                # Add to the list. Including the id so Supabase knows which row to update
                batch_updates.append({
                    "id": food['id'],
                    "allergens": clean_tags
                })
                print(f"Prepared: {name[:20]}... -> {clean_tags}")

            # Sends one big update request
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