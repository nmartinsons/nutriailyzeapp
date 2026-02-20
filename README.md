# Nutriailyze App

Nutriailyze is a Flutter + FastAPI meal planning system.

- **Frontend (Flutter):** user auth, profile/stats input, daily meal display, plan generation UI.
- **Backend (Python/FastAPI):** nutrition rules, intent parsing, KNN meal selection, optional Gemini enrichment, and food-data tagging pipelines.

## Demo Videos

- **Full app walkthrough (YouTube):**

  [Watch on YouTube](https://www.youtube.com/watch?v=0jmcyB91FFU)

---

## Project Structure

- App client (entry point): [lib/main.dart](lib/main.dart)
- Main app screens:
  - [lib/home_screen.dart](lib/home_screen.dart)
    - Main dashboard for daily plan overview, macro progress, and meal cards.
  - [lib/profile_screen.dart](lib/profile_screen.dart)
    - User identity/preferences area (basic profile and account-linked settings).
  - [lib/settings_screen.dart](lib/settings_screen.dart)
    - App-level configuration (preferences, behavior toggles, and account options).
  - [lib/physical_stats_screen.dart](lib/physical_stats_screen.dart)
    - Collects and updates biometrics (height, weight, age, activity, goals) used for macro/calorie logic.
  - [lib/login_screen.dart](lib/login_screen.dart)
    - Authentication entry point for sign-in/session start.
  - [lib/generate_plan_input_screen.dart](lib/generate_plan_input_screen.dart)
    - Input form for meal-plan generation prompts/constraints before calling backend.
  - [lib/output_screen.dart](lib/output_screen.dart)
    - Displays generated meal-plan results from backend (meals, portions, and nutrition summary).

- Backend API: [backend/main.py](backend/main.py)
- Domain models: [backend/models.py](backend/models.py)
- Meal generation orchestration: [backend/plan_generator.py](backend/plan_generator.py)
- Recommendation engine: [backend/knn.py](backend/knn.py)
- Rules/biometrics/macros/allergy logic: [backend/rules_engine.py](backend/rules_engine.py)
- Intent extraction from free text: [backend/intent_parser.py](backend/intent_parser.py)
- DB access (Supabase): [backend/db_access.py](backend/db_access.py)
- Rule tests: [backend/tests/test_rules.py](backend/tests/test_rules.py)

---

## How It Works (End-to-End)

1. **App startup + auth**
   - Flutter bootstraps in [`main`](lib/main.dart), initializes Supabase, and routes through `AuthGate`.
2. **User profile + stats**
   - User data is collected/edited through [lib/profile_screen.dart](lib/profile_screen.dart), [lib/settings_screen.dart](lib/settings_screen.dart), and [lib/physical_stats_screen.dart](lib/physical_stats_screen.dart).
3. **Plan request**
   - Frontend calls backend endpoint [`generate_meal_plan`](backend/main.py) in [backend/main.py](backend/main.py).
4. **Raw plan generation**
   - [`MealPlanGenerator.generate_raw_plan`](backend/plan_generator.py) computes calories/macros, applies intent/rules, and builds meals.
   - Uses:
     - [`IntentParser.parse`](backend/intent_parser.py) from [backend/intent_parser.py](backend/intent_parser.py)
     - [`KNN`](backend/knn.py) from [backend/knn.py](backend/knn.py)
     - [`is_safe_to_eat`](backend/rules_engine.py) from [backend/rules_engine.py](backend/rules_engine.py)
5. **Optional AI enrichment**
   - [`MealPlanGenerator.enrich_with_gemini`](backend/plan_generator.py) reformats raw meal output into a polished JSON response.
6. **Frontend rendering**
   - Generated meals are displayed in [lib/output_screen.dart](lib/output_screen.dart) (detailed plan output: meals, portions, nutrition summary).
   - Plan overview, macro progress, and daily meal cards are shown in [lib/home_screen.dart](lib/home_screen.dart).

---

## Backend Components

- **API layer:** [backend/main.py](backend/main.py)
  - Root health endpoint and `/generate-plan`.
- **Data model validation:** [backend/models.py](backend/models.py)
  - Typed `UserProfile`, enums (`Goal`, `ActivityLevel`, `Intensity`, etc.).
- **Rules engine:** [backend/rules_engine.py](backend/rules_engine.py)
  - BMI/BMR/TDEE, macro logic, meal distribution, allergy filtering.
- **KNN engine:** [backend/knn.py](backend/knn.py)
  - Candidate filtering, portion sizing, deficit rescue, global meal scaling.
- **Intent parser:** [backend/intent_parser.py](backend/intent_parser.py)
  - Converts free text into structured config (`macro_style`, avoid/include keywords, preferred style).
- **DB adapter:** [backend/db_access.py](backend/db_access.py)
  - Supabase client + dataset fetching.

---

## Data Tagging Pipelines

These scripts enrich food metadata in Supabase using Gemini:

- Categories: [backend/data_tagging/data_tagging_categories.py](backend/data_tagging/data_tagging_categories.py)
- Sub-category + liquid flags: [backend/data_tagging/data_tagging_subcat.py](backend/data_tagging/data_tagging_subcat.py)
- NOVA processing level: [backend/data_tagging/data_tagging_processinglvl.py](backend/data_tagging/data_tagging_processinglvl.py)
- Pairing tags: [backend/data_tagging/data_tagging_pairing_tag.py](backend/data_tagging/data_tagging_pairing_tag.py)
- Breakfast labeling: [backend/data_tagging/data_tagging_breakfast.py](backend/data_tagging/data_tagging_breakfast.py)
- Booster extraction: [backend/data_tagging/data_tagging_extract_boosters.py](backend/data_tagging/data_tagging_extract_boosters.py)
- Allergen tags: [backend/data_tagging/data_tagging_alllergens.py](backend/data_tagging/data_tagging_alllergens.py)

---

## Environment Variables

### App `.env` (root)

Used by Flutter in [lib/main.dart](lib/main.dart):

- `SUPABASE_URL`
- `SUPABASE_KEY`

### Backend `.env`

Used by [backend/db_access.py](backend/db_access.py) and Gemini callers:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `GEMINI_API_KEY`

---

## Run Locally

### 1) Flutter app

- Install dependencies:
  - `flutter pub get`
- Run:
  - `flutter run`

### 2) Backend API

From `backend/`:

- Install dependencies (your preferred tool/pip env)
- Start API:
  - `uvicorn main:app --reload`

---

## Testing

- Rule engine tests:
  - [backend/tests/test_rules.py](backend/tests/test_rules.py)
  - Run with: `pytest`

---

## Platform Notes

Desktop/web folders are standard Flutter targets:

- Linux: [linux/CMakeLists.txt](linux/CMakeLists.txt)
- Windows: [windows/CMakeLists.txt](windows/CMakeLists.txt)
- iOS pods: [ios/Podfile](ios/Podfile)
- Web entry: [web/index.html](web/index.html)

Generated plugin/build files should generally not be manually edited (for example [windows/flutter/generated_plugins.cmake](windows/flutter/generated_plugins.cmake), [linux/flutter/generated_plugin_registrant.cc](linux/flutter/generated_plugin_registrant.cc)).

---

## Current High-Level Architecture

- **Client:** Flutter UI + Supabase auth/session handling.
- **Server:** FastAPI meal-generation endpoint.
- **Data:** Supabase food tables + enriched metadata.
- **AI usage:**
  - Intent extraction for user text.
  - Optional meal-plan embellishment.
  - Batch food tagging utilities.
- **Core deterministic logic:** rules + KNN + safety filters. Final meal decisions are made by fixed, predictable code, not by generative AI.
