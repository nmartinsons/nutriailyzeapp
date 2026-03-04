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

            3. avoid_keywords (ARRAY of strings):
            Foods to avoid due to medical conditions OR explicit dislikes.
            Combine specific ingredients and broad categories.
            Examples:
            - "I have diabetes" → ["sugar", "syrup", "juice", "white bread", "white rice", "jam", "honey", "dried fruit"]
            - "I hate broccoli" → ["broccoli"]
            - "No nuts" → ["nuts", "peanut", "almond", "walnut"]
            - "Gluten free" → ["wheat", "barley", "rye", "bread", "pasta"]

            4. include_keywords (ARRAY of strings):
            Foods the user EXPLICITLY asks for.
            Example: "I really want some chicken today" → ["chicken"]
            Example: "Use up my eggs" → ["egg"]

            5. focus_ingredients (ARRAY of strings):
            List 5-15 specific, high-density ingredients that are BEST for the user's specific request or condition.
            Think: "What should this person eat to succeed?"
            - If a medical condition/diet is given, list foods for that diet.
            - If "Diabetes": ["oats", "barley", "lentils", "beans", "salmon", "chicken", "broccoli", "spinach", "berries", "avocado", "yogurt"]
            - If "Keto": ["avocado", "pork", "beef", "egg", "cheese", "salmon", "olive oil", "butter"]
            - If "High Protein": ["chicken breast", "tuna", "turkey", "cottage cheese", "egg white", "lean beef"]
            - If "Mediterranean": ["olive oil", "fish", "tomato", "cucumber", "feta", "chickpeas"]

            6. preferred_style (ENUM or null):
            ["simple", "quick", "spicy", "comfort", "cold", "raw"]
            - "I want something light" -> "cold" (Salads/Yogurt) or "simple"
            - "I want something heavy/hearty" -> "comfort" (Stews/Porridge)


            OUTPUT:
            Return ONLY valid JSON.
            """

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "OBJECT",
                    "properties": {
                        "macro_style": {
                            "type": "STRING",
                            "enum": [
                                "balanced", "low_carb", "keto", "high_protein",
                                "vegan", "vegetarian",
                                "diabetic_friendly", "heart_healthy"
                            ],
                            "nullable": True
                        },
                        "goal_override": {
                            "type": "STRING",
                            "enum": ["lose", "maintain", "gain"],
                            "nullable": True
                        },
                        "avoid_keywords": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"}
                        },
                        "include_keywords": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"}
                        },
                        "focus_ingredients": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"}
                        },
                        "preferred_style": {
                            "type": "STRING",
                            "enum": ["simple", "quick", "spicy", "comfort", "cold", "raw"],
                            "nullable": True
                        },
                    },
                    "required": ["avoid_keywords", "include_keywords", "focus_ingredients"]
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