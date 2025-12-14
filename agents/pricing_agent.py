import json
import csv
from typing import Dict, Any, List

class PricingAgent:
    def __init__(self, product_pricing_csv: str, test_pricing_csv: str):
        self.product_prices = self.load_prices(product_pricing_csv)
        self.test_prices = self.load_prices(test_pricing_csv)

    def load_prices(self, path: str) -> Dict[str, float]:
        prices = {}
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = row.get("sku") or row.get("test") or row.get("name")
                val = row.get("price") or row.get("cost") or row.get("unit_price")
                try:
                    prices[str(key)] = float(val)
                except Exception:
                    try:
                        prices[str(key)] = float(val.replace(",",""))
                    except Exception:
                        prices[str(key)] = 0.0
        return prices

    def _match_test_price(self, test_name: str) -> float:
        # naive case-insensitive substring match
        for k, v in self.test_prices.items():
            if not k:
                continue
            if test_name.lower() in k.lower() or k.lower() in test_name.lower():
                return v
        return 0.0

    def calculate_price(
    self,
    technical_output: Dict[str, Any],
    tests: List[str] = None,
    quantities: List[Dict[str, Any]] = None,
    logs: list = None
    ) -> Dict[str, Any]:

        if logs is None:
            logs = []

        logs.append("✔ Loaded product pricing CSV")
        logs.append("✔ Loaded test pricing CSV")

        pricing_table = []
        qty_map = {}

        if quantities:
            for q in quantities:
                qty_map[str(q.get("item_id"))] = float(
                    q.get("quantity_km", q.get("quantity", 1)) or 1
                )

        for item in technical_output.get("items", []):
            item_id = item.get("item_id")
            logs.append(f"✔ Calculating pricing for item {item_id}")

            top3 = item.get("top3", [])
            sku = top3[0]["sku"] if top3 else None

            unit_price = self.product_prices.get(sku, 0.0)
            qty = qty_map.get(str(item_id), 1.0)
            material_cost = unit_price * qty

            test_cost = 0.0
            test_details = []

            if tests:
                for t in tests:
                    price_for_t = self._match_test_price(t)
                    test_details.append({"test": t, "price": price_for_t})
                    test_cost += price_for_t

            pricing_table.append({
                "item_id": item_id,
                "rfp_item": item.get("rfp_item"),
                "sku_selected": sku,
                "unit_price": unit_price,
                "qty": qty,
                "material_cost": material_cost,
                "test_cost": test_cost,
                "test_details": "; ".join(
                    [f"{t['test']}: {t['price']}" for t in test_details]
                ),
                "total_cost": material_cost + test_cost
            })

        logs.append(f"✔ Calculated pricing for {len(pricing_table)} items")

        return {"pricing_table": pricing_table}

