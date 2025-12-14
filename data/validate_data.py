import json, csv, os
from datetime import datetime

DATA_DIR = "data"

# 1. Validate RFP JSONs
for fn in ["rfp1.json","rfp2.json","rfp3.json"]:
    p = os.path.join(DATA_DIR, fn)
    with open(p, "r", encoding="utf-8") as f:
        r = json.load(f)
    assert "id" in r and "scope" in r and "tests" in r
    # check due_date parse
    try:
        datetime.strptime(r["due_date"], "%Y-%m-%d")
    except Exception as e:
        raise SystemExit(f"{fn} has invalid due_date format: {r.get('due_date')}")

print("RFP JSONs OK")

# 2. Validate products.csv
products = []
with open(os.path.join(DATA_DIR,"products.csv"), newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        products.append(row)
assert len(products) >= 10, "Need at least 10 SKUs"
print(f"Products OK: {len(products)} SKUs")

# 3. Validate product_pricing.csv
prices = {}
with open(os.path.join(DATA_DIR,"product_pricing.csv"), newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        prices[row["sku"]] = float(row["unit_price"])
# check every product has price
missing = [p["sku"] for p in products if p["sku"] not in prices]
if missing:
    raise SystemExit(f"Missing prices for SKUs: {missing}")
print("Product pricing OK")

# 4. Validate test_pricing.csv
tests = {}
with open(os.path.join(DATA_DIR,"test_pricing.csv"), newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        tests[row["test_name"]] = float(row["test_price"])
print("Test pricing OK")

print("All data validations passed.")
