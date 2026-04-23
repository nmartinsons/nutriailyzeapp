import argparse
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_POSITIVE = BASE_DIR / "stats_and_users" / "generated_plans.json"
DEFAULT_NEGATIVE = BASE_DIR / "stats_and_users" / "do_not_want_exclusion_report.json"
DEFAULT_OUTPUT = BASE_DIR / "stats_and_users" / "preference_confusion_metrics_48.json"


def safe_div(num: float, den: float):
    return num / den if den else None


def fmt_pct(value):
    return f"{value * 100:.2f}%" if value is not None else "N/A"


def load_positive_cases(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing positive source file: {path}")

    rows = json.loads(path.read_text())
    cases = []

    for row in rows:
        kw = row.get("keyword_success")
        if kw is None:
            continue

        try:
            y_pred = int(kw)
        except Exception as exc:
            raise ValueError(f"Invalid keyword_success for id={row.get('id')}: {kw}") from exc

        if y_pred not in (0, 1):
            raise ValueError(f"keyword_success must be 0 or 1 for id={row.get('id')}, got {y_pred}")

        cases.append(
            {
                "id": row.get("id"),
                "segment": "positive_i_want",
                "y_true": 1,
                "y_pred": y_pred,
                "source": "keyword_success",
            }
        )

    return cases


def load_negative_cases(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing negative source file: {path}")

    report = json.loads(path.read_text())
    details = report.get("details", [])

    cases = []
    for row in details:
        status = row.get("status")
        if status == "skipped_no_negation":
            continue

        if status == "violation_present":
            y_pred = 1
        elif status == "success_excluded":
            y_pred = 0
        else:
            continue

        cases.append(
            {
                "id": row.get("id"),
                "segment": "negative_do_not_want",
                "y_true": 0,
                "y_pred": y_pred,
                "source": "do_not_want_exclusion_report",
            }
        )

    return cases


def compute_confusion(cases):
    tp = tn = fp = fn = 0

    for c in cases:
        y_true = c["y_true"]
        y_pred = c["y_pred"]

        if y_true == 1 and y_pred == 1:
            tp += 1
        elif y_true == 0 and y_pred == 0:
            tn += 1
        elif y_true == 0 and y_pred == 1:
            fp += 1
        elif y_true == 1 and y_pred == 0:
            fn += 1

    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    accuracy = safe_div(tp + tn, tp + tn + fp + fn)
    f1 = safe_div(2 * tp, 2 * tp + fp + fn)

    return {
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
        "f1": f1,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute combined preference confusion metrics from positive and negative cohorts"
    )
    parser.add_argument("--positive", type=Path, default=DEFAULT_POSITIVE)
    parser.add_argument("--negative", type=Path, default=DEFAULT_NEGATIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    pos_cases = load_positive_cases(args.positive)
    neg_cases = load_negative_cases(args.negative)
    all_cases = pos_cases + neg_cases

    confusion = compute_confusion(all_cases)

    report = {
        "positive_cases": len(pos_cases),
        "negative_cases": len(neg_cases),
        "total_cases": len(all_cases),
        **confusion,
    }

    args.output.write_text(json.dumps(report, indent=2))

    print("=" * 62)
    print("COMBINED PREFERENCE CONFUSION REPORT")
    print("=" * 62)
    print(f"Positive cases (I want):      {len(pos_cases)}")
    print(f"Negative cases (do not want): {len(neg_cases)}")
    print(f"Total cases:                  {len(all_cases)}")
    print("-" * 62)
    print(f"TP: {confusion['tp']}")
    print(f"TN: {confusion['tn']}")
    print(f"FP: {confusion['fp']}")
    print(f"FN: {confusion['fn']}")
    print("-" * 62)
    print(f"Precision:         {fmt_pct(confusion['precision'])}")
    print(f"Recall:            {fmt_pct(confusion['recall'])}")
    print(f"Accuracy:          {fmt_pct(confusion['accuracy'])}")
    print(f"F1 score:          {fmt_pct(confusion['f1'])}")
    print("=" * 62)
    print(f"Saved metrics to: {args.output}")


if __name__ == "__main__":
    main()
