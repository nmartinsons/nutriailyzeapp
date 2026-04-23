import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_JSON = BASE_DIR / "generated_plans.json"
OUTPUT_CSV = BASE_DIR / "ape_solution_eval.csv"


def main():
    if not INPUT_JSON.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_JSON}")

    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for user in data:
        row = {
            "id": user.get("id"),
            "ape_cal": user.get("ape_cal"),
            "ape_p": user.get("ape_p"),
            "ape_c": user.get("ape_c"),
            "ape_f": user.get("ape_f"),
        }
        rows.append(row)

    fieldnames = [
        "id",
        "ape_cal",
        "ape_p",
        "ape_c",
        "ape_f",
    ]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved APE solution-eval CSV: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
