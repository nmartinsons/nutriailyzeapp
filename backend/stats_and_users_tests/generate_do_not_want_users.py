import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
PLANS_PATH = BASE_DIR / "stats_and_users" / "generated_plans.json"
USERS_PATH = BASE_DIR / "test_users.json"
OUT_PATH = BASE_DIR / "test_users_do_not_want_24.json"
TARGET_COUNT = 24


def extract_food_name(meal: dict) -> str | None:
    food_data = meal.get("food_data") or {}

    for key in ("main_dish", "side_dish", "soup", "drink", "booster"):
        item = food_data.get(key)
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name.strip():
                return name.strip()

            full_profile = item.get("full_profile")
            if isinstance(full_profile, dict):
                nested_name = full_profile.get("name")
                if isinstance(nested_name, str) and nested_name.strip():
                    return nested_name.strip()

    boosters = food_data.get("boosters")
    if isinstance(boosters, list):
        for item in boosters:
            if isinstance(item, dict):
                name = item.get("name")
                if isinstance(name, str) and name.strip():
                    return name.strip()

                full_profile = item.get("full_profile")
                if isinstance(full_profile, dict):
                    nested_name = full_profile.get("name")
                    if isinstance(nested_name, str) and nested_name.strip():
                        return nested_name.strip()

    return None


def main() -> None:
    plans = json.loads(PLANS_PATH.read_text())
    users = json.loads(USERS_PATH.read_text())
    users_by_id = {int(user["id"]): user for user in users}

    eligible_profiles = [plan for plan in plans if plan.get("keyword_success") is None]

    selected: list[tuple[int, str]] = []

    for plan in eligible_profiles:
        profile_id = int(plan["id"])
        source_user = users_by_id.get(profile_id)
        if source_user is None:
            continue

        text_input = (source_user.get("text_input") or "").lower()
        if "do not want" in text_input or "don't want" in text_input:
            continue

        chosen_food = None
        for meal in plan.get("meals", []):
            chosen_food = extract_food_name(meal)
            if chosen_food:
                break

        if not chosen_food:
            continue

        selected.append((profile_id, chosen_food))
        if len(selected) >= TARGET_COUNT:
            break

    if len(selected) < TARGET_COUNT:
        raise RuntimeError(
            f"Only found {len(selected)} eligible profiles with extractable foods. Needed {TARGET_COUNT}."
        )

    output_users = []
    for profile_id, food_name in selected:
        user_copy = dict(users_by_id[profile_id])
        user_copy["text_input"] = f"I do not want {food_name}."
        output_users.append(user_copy)

    OUT_PATH.write_text(json.dumps(output_users, indent=2))

    print(f"Created: {OUT_PATH}")
    print(f"Total users: {len(output_users)}")
    print("Selected profiles:")
    for profile_id, food_name in selected:
        print(f"  ID {profile_id}: {food_name}")


if __name__ == "__main__":
    main()
