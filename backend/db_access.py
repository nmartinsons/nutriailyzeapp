import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    raise ValueError("Supabase credentials not found in .env")

# The connection object
supabase: Client = create_client(url, key)

def fetch_all_data():
    # Fetches foods
    f_res = supabase.table('foods').select("*").limit(10000).execute()
    
    # Fetches boosters
    b_res = supabase.table('health_boosters').select("booster_type, recommended_grams, foods(*)").limit(10000).execute()
    
    # Cleaning boosters because of nested structure because of foreign key relationship
    b_clean = [] # List to hold cleaned booster data
    # For loop which gives that one item equals one booster with its food data flattened
    for item in b_res.data:
        # If there are foods associated with the booster
        if item.get('foods'):
            # This flattens the food object into dictionary and adds booster info
            flat = item['foods'].copy()
            flat['booster_type'] = item['booster_type']
            flat['recommended_grams'] = item['recommended_grams']
            b_clean.append(flat)

    return f_res.data, b_clean