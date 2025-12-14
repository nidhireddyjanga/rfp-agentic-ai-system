import csv
from typing import Dict, Any, List

class TechnicalAgent:
    def __init__(self, products_csv):
        self.products = self.load_products(products_csv)

    def load_products(self, path) -> List[Dict[str, Any]]:
        products = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # safe parse
                try:
                    ins = float(row.get("insulation_thickness_mm", 0) or 0)
                except Exception:
                    ins = 0.0
                products.append({
                    "sku": row.get("sku"),
                    "voltage": row.get("voltage"),
                    "conductor": row.get("conductor"),
                    "insulation_thickness_mm": ins
                })
        return products

    def compute_match_score(self, rfp_specs: Dict[str, Any], product: Dict[str, Any]) -> float:
        score = 0.0
        try:
            if str(rfp_specs.get("voltage","")).strip().lower() == str(product.get("voltage","")).strip().lower():
                score += 40
        except Exception:
            pass
        try:
            if str(rfp_specs.get("conductor","")).strip().lower() == str(product.get("conductor","")).strip().lower():
                score += 40
        except Exception:
            pass
        try:
            r_val = float(rfp_specs.get("insulation_thickness_mm", 0) or 0)
            p_val = float(product.get("insulation_thickness_mm", 0) or 0)
            if abs(r_val - p_val) <= max(0.2, 0.2 * (r_val if r_val>0 else 1.0)):
                score += 20
        except Exception:
            pass
        return score

    def match_item(self, rfp_item: Dict[str, Any]) -> Dict[str, Any]:
        specs = rfp_item.get("specs", {})
        scored = []
        for p in self.products:
            s = self.compute_match_score(specs, p)
            scored.append((s, p))
        scored.sort(key=lambda x: (-x[0], x[1].get("sku","")))
        top3 = []
        for score, p in scored[:3]:
            top3.append({
                "sku": p.get("sku"),
                "product_specs": {
                    "voltage": p.get("voltage"),
                    "conductor": p.get("conductor"),
                    "insulation_thickness_mm": p.get("insulation_thickness_mm")
                },
                "spec_match_pct": score
            })
        return {
            "item_id": rfp_item.get("item_id"),
            "rfp_item": rfp_item.get("description"),
            "top3": top3
        }

    def process_rfp(self, rfp_data: Dict[str, Any], logs: list = None) -> Dict[str, Any]:
        if logs is None:
            logs = []

        results = []

        for item in rfp_data.get("scope", []):
            item_id = item.get("item_id")
            desc = item.get("description")

            logs.append(f"✔ Matching item {item_id} ({desc})")

            matched = self.match_item(item)

            top3 = matched.get("top3", [])
            logs.append(f"✔ Found {len(top3)} matching SKUs")

            results.append(matched)

        return {"items": results}

