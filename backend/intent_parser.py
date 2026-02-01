import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class IntentParser:
    def parse(self, text_input: str):
        if not text_input or len(text_input.strip()) < 3:
            return {}

        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            "models/gemini-2.5-flash:generateContent"
            f"?key={GEMINI_API_KEY}"
        )
        headers = {"Content-Type": "application/json"}

        prompt = f"""
You are an advanced clinical nutritionist AI for a meal-planning app.

Analyze the user's free-text input and extract a structured JSON configuration.
Be conservative. Only infer what is strongly suggested by the text.

USER INPUT:
"{text_input}"

FIELDS TO EXTRACT:

1. macro_style (ENUM or null):
   ["balanced", "low_carb", "keto", "high_protein", "vegan",
    "vegetarian", "diabetic_friendly", "heart_healthy"]

2. goal_override (ENUM or null):
   ["lose", "maintain", "gain"]

3. avoid_medical (ARRAY of strings):
   Foods to avoid due to medical conditions.
   Examples:
   - diabetes → sugar, syrup, juice, white bread
   - hypertension → salt, sodium, bacon, soy sauce
   - upset stomach → spicy, fried, fatty, raw
   - lactose intolerance → milk, cheese, cream
   - vegetarian/vegan → meat, fish, poultry, eggs, dairy
   - gluten intolerance/celiac → wheat, barley, rye, bread, pasta, baked goods
   - seafood allergy → fish, shellfish, shrimp, crab
   - nut allergy → peanuts, almonds, cashews, walnuts
   - heart disease → saturated fat, trans fat, fried foods, processed meats, high-cholesterol foods

4. avoid_preference (ARRAY of strings):
   Explicit dislikes stated by the user.
   Example: "no fish" → ["fish", "seafood"]

5. include_keywords (ARRAY of strings):
   Foods the user explicitly wants or has.
   Example: "I have chicken" → ["chicken"]

6. preferred_style (ENUM or null):
   ["simple", "quick", "spicy", "comfort", "cold", "raw"]

7. caloric_shift (ENUM or null):
   ["light", "heavy"]

8. ambiguities (ARRAY of strings):
   Conflicting or unclear signals in the text.
   Example: "keto conflicts with pasta request"

OUTPUT:
Return ONLY valid JSON. No explanations.
"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "OBJECT",
                    "properties": {
                        "macro_style": {
                            "type": ["STRING", "NULL"],
                            "enum": [
                                "balanced", "low_carb", "keto", "high_protein",
                                "vegan", "vegetarian",
                                "diabetic_friendly", "heart_healthy", None
                            ]
                        },
                        "goal_override": {
                            "type": ["STRING", "NULL"],
                            "enum": ["lose", "maintain", "gain", None]
                        },
                        "avoid_medical": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"}
                        },
                        "avoid_preference": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"}
                        },
                        "include_keywords": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"}
                        },
                        "preferred_style": {
                            "type": ["STRING", "NULL"],
                            "enum": ["simple", "quick", "spicy", "comfort", "cold", "raw", None]
                        },
                        "caloric_shift": {
                            "type": ["STRING", "NULL"],
                            "enum": ["light", "heavy", None]
                        },
                        "ambiguities": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"}
                        }
                    }
                }
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code != 200:
                print("Intent Error:", response.text)
                return {}

            raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)

        except Exception as e:
            print("Intent Exception:", e)
            return {}
