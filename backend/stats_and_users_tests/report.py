import json
from pathlib import Path

OUTPUT_JSON = Path(__file__).parent / "generated_plans.json"

if not OUTPUT_JSON.exists():
    print(f"Error: '{OUTPUT_JSON}' not found. Run solution_eval.py first to generate plans.")
    raise SystemExit(1)

results = json.loads(OUTPUT_JSON.read_text())
count = len(results)

if count == 0:
    print("No results found in generated_plans.json.")
    raise SystemExit(0)


def _binary_rate(cases, score_key):
    if not cases:
        return None
    return sum(r[score_key] for r in cases) / len(cases) * 100


def _fmt_rate(value):
    return f"{value:.2f}%" if value is not None else "N/A"


# 1. Nutritional Adherence (MAPE)
mape_cal = sum(r['ape_cal'] for r in results) / count
mape_p   = sum(r['ape_p']   for r in results) / count
mape_c   = sum(r['ape_c']   for r in results) / count
mape_f   = sum(r['ape_f']   for r in results) / count

# 2. Constraint Adherence Rate (CAR)
safety_cases   = [r for r in results if r.get('constraint_score')          is not None]
allergy_cases  = [r for r in results if r.get('allergy_constraint_score')  is not None]
dietary_cases  = [r for r in results if r.get('dietary_constraint_score')  is not None]

car_score          = _binary_rate(safety_cases,  'constraint_score')
allergy_adherence  = _binary_rate(allergy_cases, 'allergy_constraint_score')
dietary_adherence  = _binary_rate(dietary_cases, 'dietary_constraint_score')

# 3. Free-Text Preference Success
pref_cases   = [r for r in results if r.get('keyword_success') is not None]
success_rate = _binary_rate(pref_cases, 'keyword_success')

# REPORT
print("\n" + "=" * 50)
print(f"FINAL THESIS RESULTS (N={count})")
print("=" * 50)
print(f"1. Nutritional Adherence (MAPE):")
print(f"   - Calories:      {mape_cal:.2f}%  (Target: ≤5%)")
print(f"   - Protein:       {mape_p:.2f}%")
print(f"   - Carbs:         {mape_c:.2f}%")
print(f"   - Fat:           {mape_f:.2f}%")
print("-" * 50)
print(f"2. Constraint Adherence Rate (CAR): {_fmt_rate(car_score)}")
print(f"   (Based on {len(safety_cases)} profiles with any restrictions)")
print(f"   - Allergen Adherence Rate:        {_fmt_rate(allergy_adherence)}")
print(f"     (Based on {len(allergy_cases)} profiles with allergies)")
print(f"   - Dietary Restriction Adherence:  {_fmt_rate(dietary_adherence)}")
print(f"     (Based on {len(dietary_cases)} profiles with dietary restrictions)")
print("-" * 50)
print(f"3. Free-Text Preference Success:    {_fmt_rate(success_rate)}")
print(f"   (Based on {len(pref_cases)} profiles with cravings)")
print("=" * 50)

# FAILING PROFILES
failing_dietary  = [r for r in dietary_cases  if r['dietary_constraint_score']  == 0]
failing_allergy  = [r for r in allergy_cases  if r['allergy_constraint_score']  == 0]
failing_pref     = [r for r in pref_cases     if r['keyword_success']           == 0]

if failing_dietary or failing_allergy or failing_pref:
    print("\n--- Failing Profiles ---")
    for r in failing_dietary:
        print(f"  [DIETARY]  ID {r['id']} | style={r.get('macro_style','?')}")
    for r in failing_allergy:
        print(f"  [ALLERGY]  ID {r['id']} | allergies={r.get('allergies','?')}")
    for r in failing_pref:
        print(f"  [PREF]     ID {r['id']} | text=\"{r.get('text_input','?')}\"")
else:
    print("\nNo failing profiles.")
