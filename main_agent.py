import json
import os
from typing import Dict, Any, List

class MainAgent:
    def __init__(self, sales_agent, technical_agent, pricing_agent):
        self.sales_agent = sales_agent
        self.technical_agent = technical_agent
        self.pricing_agent = pricing_agent
        self.logs = []

    def log(self, msg):
        self.logs.append(msg)

    def run(self):
        rfp_data = self.sales_agent.identify_rfp()
        return self.process_rfp(rfp_data)

    def process_rfp(self, rfp_data: Dict[str, Any]) -> Dict[str, Any]:
        self.logs = []

        # --------------------
        # SALES AGENT
        # --------------------
        self.log("[Sales Agent]")
        self.log("✔ RFP received")

        sales_summary_for_tech = self.sales_agent.summarize_for_technical(rfp_data)
        self.log(f"✔ Extracted {len(sales_summary_for_tech.get('scope', []))} scope items")
        self.log("✔ Prepared summary for TechnicalAgent")

        sales_summary_for_pricing = self.sales_agent.summarize_for_pricing(rfp_data)
        self.log("✔ Prepared summary for PricingAgent")

        # --------------------
        # TECHNICAL AGENT
        # --------------------
        self.log("\n[Technical Agent]")
        technical_output = self.technical_agent.process_rfp(
            sales_summary_for_tech,
            logs=self.logs
        )

        # --------------------
        # SPEC COMPARISON
        # --------------------
        comparison_table = []
        rfp_items = {str(i.get("item_id")): i for i in sales_summary_for_tech.get("scope", [])}

        for itm in technical_output.get("items", []):
            item_id = str(itm.get("item_id"))
            rfp_spec = rfp_items.get(item_id, {}).get("specs", {})
            comparison_table.append({
                "item_id": itm.get("item_id"),
                "rfp_item": itm.get("rfp_item"),
                "rfp_specs": rfp_spec,
                "candidates": itm.get("top3", [])
            })

        # --------------------
        # PRICING AGENT
        # --------------------
        self.log("\n[Pricing Agent]")
        pricing_output = self.pricing_agent.calculate_price(
            technical_output,
            tests=sales_summary_for_pricing.get("tests", []),
            quantities=sales_summary_for_pricing.get("quantities", []),
            logs=self.logs
        )

        self.log("\n[Pipeline]")
        self.log("✔ Pipeline completed successfully")

        final_response = {
            "rfp_id": rfp_data.get("id"),
            "rfp_title": rfp_data.get("title"),
            "due_date": rfp_data.get("due_date"),
            "sales_summary": {
                "for_technical": sales_summary_for_tech,
                "for_pricing": sales_summary_for_pricing
            },
            "technical_match": technical_output,
            "spec_comparison": comparison_table,
            "pricing": pricing_output,
            "logs": self.logs
        }

        return final_response

