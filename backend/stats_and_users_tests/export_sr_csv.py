import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_JSON = BASE_DIR / "generated_plans.json"
OUTPUT_CSV = BASE_DIR / "sr_solution_eval.csv"


def main():
    if not INPUT_JSON.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_JSON}")

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for user in data:
        row = {
            "id": user.get("id"),
            "keyword_success": user.get("keyword_success")
        }
        rows.append(row)

    fieldnames = [
        "id",
        "keyword_success"
    ]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved SR CSV: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
