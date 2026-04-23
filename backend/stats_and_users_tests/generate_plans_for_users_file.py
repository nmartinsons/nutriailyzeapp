import argparse
import json
import random
import traceback
from pathlib import Path

import numpy as np

import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from plan_generator import MealPlanGenerator
from models import UserProfile, UserActivity, Intensity, Gender, Goal, ActivityLevel

THESIS_BASE_SEED = 2026
DEFAULT_INPUT = BASE_DIR / "test_users_do_not_want_24.json"
DEFAULT_OUTPUT = BASE_DIR / "stats_and_users" / "generated_plans_do_not_want_24.json"
DEFAULT_FAILURES = BASE_DIR / "stats_and_users" / "failed_profiles_do_not_want_24.json"


def _build_user_profile(data: dict) -> UserProfile:
    activity_objects = []
    for act in data.get("activities", []):
        activity_objects.append(
            UserActivity(
                hours=act["hours"],
                intensity=Intensity(act["intensity"]),
            )
        )

    return UserProfile(
        id=data["id"],
        age=data["age"],
        height=data["height"],
        weight=data["weight"],
        gender=Gender(data["gender"]),
        daily_activity=ActivityLevel(data["daily_activity"]),
        goal=Goal(data["goal"]),
        activities=activity_objects,
        meal_amount=data.get("meal_amount", 3),
        allergies=data.get("allergies", []),
        text_input=data.get("text_input", ""),
    )


def _seed_for_user(user_id) -> int:
    user_id_str = str(user_id)
    if user_id_str.isdigit():
        return THESIS_BASE_SEED + int(user_id_str)
    return THESIS_BASE_SEED + sum(ord(ch) for ch in user_id_str)


def generate_plans(input_json: Path, output_json: Path, failures_json: Path) -> None:
    users_data = json.loads(input_json.read_text())
    print(f"Loaded {len(users_data)} profiles from '{input_json}'")

    results = []
    failures = []

    for data in users_data:
        try:
            run_seed = _seed_for_user(data.get("id"))
            random.seed(run_seed)
            np.random.seed(run_seed)

            user_obj = _build_user_profile(data)
            generator = MealPlanGenerator(user_obj)
            plan_output = generator.generate_raw_plan()

            results.append(
                {
                    "id": data["id"],
                    "text_input": data.get("text_input", ""),
                    "allergies": data.get("allergies", []),
                    "macro_style": data.get("macro_style"),
                    "meal_amount": data.get("meal_amount", 3),
                    "daily_targets": plan_output.get("daily_targets", {}),
                    "meals": plan_output.get("meals", []),
                }
            )
        except Exception as exc:
            error_message = f"{type(exc).__name__}: {exc}"
            print(f"Error with User {data.get('id')}: {error_message}")
            failures.append(
                {
                    "id": data.get("id"),
                    "text_input": data.get("text_input"),
                    "error": error_message,
                    "traceback": traceback.format_exc(),
                }
            )

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(results, indent=2))
    print(f"Saved {len(results)} generated plans to '{output_json}'")

    if failures:
        failures_json.parent.mkdir(parents=True, exist_ok=True)
        failures_json.write_text(json.dumps(failures, indent=2))
        print(f"Saved {len(failures)} failed profiles to '{failures_json}'")
    elif failures_json.exists():
        failures_json.unlink()
        print(f"No failures. Removed existing failures file '{failures_json}'")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate meal plans from a user JSON file without modifying existing evaluation scripts"
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--failures", type=Path, default=DEFAULT_FAILURES)
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    generate_plans(args.input, args.output, args.failures)


if __name__ == "__main__":
    main()
