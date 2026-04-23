import argparse
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = BASE_DIR / "stats_and_users" / "generated_plans_do_not_want_24.json"
DEFAULT_OUTPUT = BASE_DIR / "stats_and_users" / "do_not_want_exclusion_report.json"


def _normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())


def _extract_negated_food(text_input: str) -> str | None:
    if not text_input:
        return None

    patterns = [
        r"\bi\s+do\s+not\s+want\s+(.+)$",
        r"\bi\s+don\'t\s+want\s+(.+)$",
        r"\bwithout\s+(.+)$",
    ]

    raw = text_input.strip()
    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.IGNORECASE)
        if match:
            value = match.group(1).strip().strip(". !?")
            return value if value else None
    return None


def _collect_meal_names(plan_row: dict) -> list[str]:
    names: list[str] = []

    for meal in plan_row.get("meals", []):
        food_data = meal.get("food_data") or {}

        for key in ("main_dish", "side_dish", "soup", "drink", "booster"):
            item = food_data.get(key)
            if isinstance(item, dict):
                name = item.get("name")
                if isinstance(name, str) and name.strip():
                    names.append(name.strip())

                full_profile = item.get("full_profile")
                if isinstance(full_profile, dict):
                    nested_name = full_profile.get("name")
                    if isinstance(nested_name, str) and nested_name.strip():
                        names.append(nested_name.strip())

        boosters = food_data.get("boosters")
        if isinstance(boosters, list):
            for item in boosters:
                if isinstance(item, dict):
                    name = item.get("name")
                    if isinstance(name, str) and name.strip():
                        names.append(name.strip())

                    full_profile = item.get("full_profile")
                    if isinstance(full_profile, dict):
                        nested_name = full_profile.get("name")
                        if isinstance(nested_name, str) and nested_name.strip():
                            names.append(nested_name.strip())

    return names


def _is_present(negated_food: str, meal_names: list[str]) -> tuple[bool, str | None]:
    neg_norm = _normalize_text(negated_food)
    if not neg_norm:
        return False, None

    neg_tokens = set(neg_norm.split())

    for meal_name in meal_names:
        meal_norm = _normalize_text(meal_name)
        if not meal_norm:
            continue

        # Strict phrase check
        if neg_norm in meal_norm:
            return True, meal_name

        # Token-overlap fallback for names with punctuation/order differences
        meal_tokens = set(meal_norm.split())
        if neg_tokens and neg_tokens.issubset(meal_tokens):
            return True, meal_name

    return False, None


def evaluate(input_path: Path, output_path: Path) -> dict:
    rows = json.loads(input_path.read_text())

    evaluated = 0
    success = 0
    violations = 0
    skipped_no_negation = 0

    details = []

    for row in rows:
        profile_id = row.get("id")
        text_input = row.get("text_input", "")

        negated_food = _extract_negated_food(text_input)
        if not negated_food:
            skipped_no_negation += 1
            details.append(
                {
                    "id": profile_id,
                    "text_input": text_input,
                    "status": "skipped_no_negation",
                    "negated_food": None,
                    "matched_food": None,
                }
            )
            continue

        evaluated += 1
        meal_names = _collect_meal_names(row)
        present, matched_food = _is_present(negated_food, meal_names)

        if present:
            violations += 1
            status = "violation_present"
        else:
            success += 1
            status = "success_excluded"

        details.append(
            {
                "id": profile_id,
                "text_input": text_input,
                "status": status,
                "negated_food": negated_food,
                "matched_food": matched_food,
            }
        )

    exclusion_success_rate = (success / evaluated * 100) if evaluated else None

    report = {
        "total_rows": len(rows),
        "evaluated_rows": evaluated,
        "skipped_no_negation": skipped_no_negation,
        "success_excluded": success,
        "violations_present": violations,
        "exclusion_success_rate": exclusion_success_rate,
        "details": details,
    }

    output_path.write_text(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate exclusion success for do-not-want prompts"
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Input file not found: {args.input}")

    report = evaluate(args.input, args.output)

    rate = report["exclusion_success_rate"]
    rate_str = f"{rate:.2f}%" if rate is not None else "N/A"

    print("=" * 58)
    print("DO-NOT-WANT EXCLUSION REPORT")
    print("=" * 58)
    print(f"Total rows:         {report['total_rows']}")
    print(f"Evaluated rows:     {report['evaluated_rows']}")
    print(f"Skipped (no phrase):{report['skipped_no_negation']}")
    print(f"Excluded success:   {report['success_excluded']}")
    print(f"Violations present: {report['violations_present']}")
    print(f"Success rate:       {rate_str}")
    print("=" * 58)
    print(f"Saved report to: {args.output}")


if __name__ == "__main__":
    main()
