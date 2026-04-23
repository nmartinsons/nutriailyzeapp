import json
from collections import Counter
from pathlib import Path

OUTPUT_JSON = Path(__file__).parent / "generated_plans.json"

if not OUTPUT_JSON.exists():
    print(f"Error: '{OUTPUT_JSON}' not found.")
    raise SystemExit(1)

results = json.loads(OUTPUT_JSON.read_text())


# Helper: extract all dish names from a single plan

def _get_meal_names(record):
    """Return list of main/side dish names for a user's plan."""
    names = []
    for meal in record.get("meals", []):
        fd = meal.get("food_data", {})
        if fd.get("main_dish"):
            names.append(fd["main_dish"]["name"])
        if fd.get("side_dish"):
            names.append(fd["side_dish"]["name"])
    return names


def _get_all_dish_names(record, include_boosters=False):
    """Return list of ALL dish names (main + side + optionally boosters)."""
    names = _get_meal_names(record)
    if include_boosters:
        for meal in record.get("meals", []):
            fd = meal.get("food_data", {})
            for b in fd.get("boosters", []):
                names.append(b["name"])
    return names


# 1. Within-plan repetition

within_duplicate_ids = []
within_dup_details   = []  # (id, repeated_name, count)

for r in results:
    names = _get_meal_names(r)
    if not names:
        continue
    counts = Counter(names)
    dupes = [(n, c) for n, c in counts.items() if c > 1]
    if dupes:
        within_duplicate_ids.append(r["id"])
        for n, c in dupes:
            within_dup_details.append((r["id"], n, c))


# 2. Across-plan frequency

all_main_names = []   # main dishes only
all_dish_names = []   # main + side

for r in results:
    for meal in r.get("meals", []):
        fd = meal.get("food_data", {})
        if fd.get("main_dish"):
            all_main_names.append(fd["main_dish"]["name"])
        if fd.get("main_dish"):
            all_dish_names.append(fd["main_dish"]["name"])
        if fd.get("side_dish"):
            all_dish_names.append(fd["side_dish"]["name"])

main_counter = Counter(all_main_names)
dish_counter = Counter(all_dish_names)

total_plans        = len(results)
plans_with_meals   = sum(1 for r in results if r.get("meals"))
total_main_slots   = len(all_main_names)
total_dish_slots   = len(all_dish_names)
unique_mains       = len(main_counter)
unique_dishes      = len(dish_counter)

# Type-Token Ratio (TTR): unique / total — higher = more diverse
ttr_mains  = unique_mains  / total_main_slots  if total_main_slots  else 0
ttr_dishes = unique_dishes / total_dish_slots  if total_dish_slots  else 0

# Meals used only once (hapax legomena)
hapax_mains  = sum(1 for c in main_counter.values() if c == 1)
hapax_dishes = sum(1 for c in dish_counter.values() if c == 1)


# 3. Per-slot diversity

slot_counters = {}  # slot_name → Counter of main_dish names

for r in results:
    for meal in r.get("meals", []):
        slot = meal.get("slot_name", "Unknown")
        fd   = meal.get("food_data", {})
        if fd.get("main_dish"):
            slot_counters.setdefault(slot, Counter())[fd["main_dish"]["name"]] += 1


# 4. Intra-plan diversity: avg unique ratio per plan ───────────────────────

unique_ratios = []
for r in results:
    names = _get_meal_names(r)
    if names:
        unique_ratios.append(len(set(names)) / len(names))

avg_unique_ratio = sum(unique_ratios) / len(unique_ratios) if unique_ratios else 0


# REPORTING

W = 60

print("\n" + "=" * W)
print("MEAL DIVERSITY REPORT")
print("=" * W)
print(f"Total profiles:          {total_plans}")
print(f"Profiles with meals:     {plans_with_meals}")

print("\nA. Within-Plan Repetition")
print(f"Plans with repeated dishes:  {len(within_duplicate_ids)} / {plans_with_meals}")
if within_dup_details:
    print("  Offending plans:")
    for uid, name, cnt in within_dup_details:
        print(f"    User {uid}: '{name}' appears {cnt}x")
else:
    print("  No within-plan repetition found.")
print(f"Avg within-plan unique ratio: {avg_unique_ratio:.3f}  (1.0 = fully diverse)")

print("\nB. Across-Plan Diversity (Main Dishes)")
print(f"Total main-dish slots:   {total_main_slots}")
print(f"Unique main dishes:      {unique_mains}")
print(f"Type-Token Ratio (TTR):  {ttr_mains:.3f}  (closer to 1.0 = more diverse)")
print(f"Meals used only once:    {hapax_mains}  ({hapax_mains/unique_mains*100:.1f}% of unique)")

print("\nC. Top 20 Most-Repeated Main Dishes (across all plans)")
for i, (name, cnt) in enumerate(main_counter.most_common(20), 1):
    pct = cnt / total_main_slots * 100
    bar = "█" * min(cnt, 40)
    print(f"  {i:2}. {cnt:3}x ({pct:4.1f}%)  {name[:55]}")

print("\nD. Across-Plan Diversity (Main + Side Dishes)")
print(f"Total dish slots:        {total_dish_slots}")
print(f"Unique dishes:           {unique_dishes}")
print(f"Type-Token Ratio (TTR):  {ttr_dishes:.3f}")
print(f"Dishes used only once:   {hapax_dishes}  ({hapax_dishes/unique_dishes*100:.1f}% of unique)")

print("\nE. Per-Slot Diversity")
for slot in sorted(slot_counters):
    sc        = slot_counters[slot]
    total_sc  = sum(sc.values())
    unique_sc = len(sc)
    top1_name, top1_cnt = sc.most_common(1)[0]
    print(f"  {slot:<12}: {unique_sc:3} unique / {total_sc:3} total  (most common: '{top1_name[:40]}' {top1_cnt}x)")

print("\nF. Top 20 Most-Repeated Side Dishes")
side_counter = Counter()
for r in results:
    for meal in r.get("meals", []):
        fd = meal.get("food_data", {})
        if fd.get("side_dish"):
            side_counter[fd["side_dish"]["name"]] += 1

for i, (name, cnt) in enumerate(side_counter.most_common(20), 1):
    total_sides = sum(side_counter.values())
    pct = cnt / total_sides * 100
    print(f"  {i:2}. {cnt:3}x ({pct:4.1f}%)  {name[:55]}")

print("=" * W)
