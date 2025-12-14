import json
import os
import re
import tempfile
from typing import List, Dict, Any

try:
    import requests
    from io import BytesIO
    from PyPDF2 import PdfReader
    HAS_NETWORK = True
except Exception:
    requests = None
    BytesIO = None
    PdfReader = None
    HAS_NETWORK = False


class SalesAgent:
    def __init__(self, data_folder: str = "data/rfps/"):
        self.data_folder = data_folder

    # ---- simple default identify (loads first local rfp) ----
    def identify_rfp(self) -> Dict[str, Any]:
        files = [f for f in os.listdir(self.data_folder) if f.endswith(".json")]
        if not files:
            raise FileNotFoundError("No RFP files found inside data/rfps/")
        first_rfp_path = os.path.join(self.data_folder, files[0])
        with open(first_rfp_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ---- scan a list of URLs (tries local mapping, JSON fetch, PDF text extraction) ----
    def scan_urls_for_rfps(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        For each URL:
         - if it matches a filename in data/rfps/ return that local RFP
         - else attempt to GET the URL (if requests available). If Content-Type JSON -> parse
         - if PDF -> download and attempt to extract plain text and build a simple RFP object
        Returns list of dicts with keys: title, due_date, source, rfp (object or None)
        """
        found = []
        # preload local rfps
        local_rfps = {}
        try:
            for fn in os.listdir(self.data_folder):
                if fn.lower().endswith(".json"):
                    path = os.path.join(self.data_folder, fn)
                    try:
                        with open(path, "r", encoding="utf-8") as fh:
                            j = json.load(fh)
                        local_rfps[fn.lower()] = j
                        # also map id/title keys for fuzzy matching
                        local_rfps[str(j.get("id","")).lower()] = j
                        local_rfps[str(j.get("title","")).lower()] = j
                    except Exception:
                        continue
        except Exception:
            pass

        for url in urls:
            url_norm = url.strip()
            base = os.path.basename(url_norm).lower()
            matched = False
            # 1) try local filename match
            for key, rfp in local_rfps.items():
                if base and base in key:
                    found.append({"title": rfp.get("title"), "due_date": rfp.get("due_date"),
                                  "source": "local:" + key, "rfp": rfp})
                    matched = True
                    break
            if matched:
                continue

            # 2) try to use ID match
            for key, rfp in local_rfps.items():
                if key and key in url_norm.lower():
                    found.append({"title": rfp.get("title"), "due_date": rfp.get("due_date"),
                                  "source": "local:" + key, "rfp": rfp})
                    matched = True
                    break
            if matched:
                continue

            # 3) attempt to fetch remote URL if requests available
            if HAS_NETWORK and requests:
                try:
                    resp = requests.get(url_norm, timeout=10)
                    ctype = resp.headers.get("content-type","").lower()
                    if "application/json" in ctype or url_norm.lower().endswith(".json"):
                        try:
                            j = resp.json()
                            found.append({"title": j.get("title", "remote JSON RFP"), "due_date": j.get("due_date", "unknown"),
                                          "source": url_norm, "rfp": j})
                            continue
                        except Exception:
                            pass
                    if "application/pdf" in ctype or url_norm.lower().endswith(".pdf"):
                        # save temp and try to extract text to find a title/due_date/scope
                        if PdfReader:
                            try:
                                bio = BytesIO(resp.content)
                                reader = PdfReader(bio)
                                text = []
                                for p in reader.pages[:5]:
                                    try:
                                        text.append(p.extract_text() or "")
                                    except Exception:
                                        pass
                                txt = "\n".join(text)
                                # try to parse simple fields from text
                                title = self._extract_field_from_text(txt, ["title:", "rfp title:", "request for proposal"])
                                due = self._extract_field_from_text(txt, ["due date:", "submission date:", "due:"])
                                # Attempt to synthesize a small RFP object using very simple heuristics:
                                scope = self._extract_scope_from_text(txt)
                                rfp_obj = {"title": title or f"Remote PDF: {base}", "due_date": due or "unknown", "scope": scope, "tests": []}
                                found.append({"title": rfp_obj["title"], "due_date": rfp_obj["due_date"], "source": url_norm, "rfp": rfp_obj})
                                continue
                            except Exception:
                                # fallback create placeholder entry
                                found.append({"title": f"Remote PDF (couldn't parse): {base}", "due_date": "unknown", "source": url_norm, "rfp": None})
                                continue
                        else:
                            # no PDF reader installed: return placeholder
                            found.append({"title": f"Remote PDF (no PDF lib): {base}", "due_date": "unknown", "source": url_norm, "rfp": None})
                            continue
                    # fallback: unknown content type -> placeholder
                    found.append({"title": f"Remote resource: {base}", "due_date": "unknown", "source": url_norm, "rfp": None})
                except Exception:
                    found.append({"title": f"Remote resource (fetch failed): {base}", "due_date": "unknown", "source": url_norm, "rfp": None})
            else:
                # no network available: return placeholder so user knows nothing matched
                found.append({"title": f"Remote resource (no-network): {base}", "due_date": "unknown", "source": url_norm, "rfp": None})

        return found

    # ---- very small heuristics helper functions ----
    def _extract_field_from_text(self, text: str, keys: List[str]) -> str:
        t = text.lower()
        for k in keys:
            if k in t:
                idx = t.find(k)
                snippet = t[idx: idx + 200].splitlines()[0]
                # return characters after the key
                after = snippet.replace(k, "").strip(" :\n")
                if after:
                    return after.strip()
        return ""

    def _extract_scope_from_text(self, text: str) -> List[Dict[str, Any]]:
        # very small heuristic: look for lines containing "voltage" and treat as one scope item cluster
        lines = text.splitlines()
        items = []
        cur = {}
        for ln in lines:
            low = ln.lower()
            if "voltage" in low or "conductor" in low or "insulation" in low:
                # try to parse a name from nearby lines
                # if cur empty, try to set description from previous non-empty line
                if not cur.get("description"):
                    # pick previous non-empty line
                    for back in reversed(lines[max(0, lines.index(ln)-3):lines.index(ln)]):
                        if back.strip():
                            cur["description"] = back.strip()
                            break
                # set specs found
                if "voltage" in low:
                    m = re.search(r"([\d\.]+k?v)", low)
                    cur.setdefault("specs", {})["voltage"] = m.group(1) if m else ""
                if "conductor" in low:
                    m = re.search(r"(aluminium|aluminum|copper|steel|copper)", low)
                    cur.setdefault("specs", {})["conductor"] = m.group(1) if m else ""
                if "insulation" in low:
                    m = re.search(r"([\d\.]+)\s?mm", low)
                    cur.setdefault("specs", {})["insulation_thickness_mm"] = float(m.group(1)) if m else 0.0
                # if specs appear complete-ish, append
                s = cur.get("specs", {})
                if s.get("voltage") or s.get("conductor"):
                    # ensure item_id / description
                    cur.setdefault("item_id", len(items)+1)
                    cur.setdefault("quantity_km", 1)
                    if "rfp_item" not in cur:
                        cur.setdefault("description", cur.get("description", f"Item {len(items)+1}"))
                    items.append(cur)
                    cur = {}
        return items

    def summarize_for_technical(self, rfp_data):
        """Short, structured summary for Technical Agent."""
        scope = rfp_data.get("scope", [])

        tech_summary = {
            "id": rfp_data.get("id"),
            "title": rfp_data.get("title"),
            "due_date": rfp_data.get("due_date"),
            "scope": [],  # remapped to ONLY what tech agent needs
        }

        for item in scope:
            tech_summary["scope"].append({
                "item_id": item.get("item_id"),
                "description": item.get("description"),
                "specs": item.get("specs", {})
            })

        return tech_summary


    def summarize_for_pricing(self, rfp_data):
        """Short summary for Pricing Agent (quantities + tests)."""
        scope = rfp_data.get("scope", [])

        pricing_summary = {
            "id": rfp_data.get("id"),
            "title": rfp_data.get("title"),
            "tests": rfp_data.get("tests", []),
            "quantities": []
        }

        for item in scope:
            pricing_summary["quantities"].append({
                "item_id": item.get("item_id"),
                "quantity_km": item.get("quantity_km", 1)
            })

        return pricing_summary

    # ---- small helper: compute simple sales-fit score if needed externally ----
    def compute_sales_fit_score(self, rfp_data: Dict[str, Any]) -> int:
        # reuse earlier logic adapted
        score = 0
        if self.extract_budget(rfp_data) != "Budget not mentioned":
            score += 30
        if self.extract_timeline(rfp_data) != "Timeline not mentioned":
            score += 20
        if len(self.extract_business_requirements(rfp_data)) > 1:
            score += 50
        return min(score, 100)

    # existing extraction helpers (budget, timeline, requirements) kept
    def extract_business_requirements(self, rfp_data):
        text = json.dumps(rfp_data).lower()
        keywords = ["business need", "goal", "objective", "problem", "requirement", "use case", "scope"]
        requirements = []
        for k in keywords:
            if k in text:
                pattern = rf"{k}[^\.]*\."
                matches = re.findall(pattern, text)
                requirements.extend(matches)
        return list(set(requirements)) or ["No clear business requirements found."]

    def extract_budget(self, rfp_data):
        text = json.dumps(rfp_data)
        budget_patterns = [r"\₹[\d,]+", r"\$[\d,]+", r"\d+\s?(crore|lakh|million|billion)", r"budget[^0-9]*([\d,.]+)"]
        for p in budget_patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return "Budget not mentioned"

    def extract_timeline(self, rfp_data):
        text = json.dumps(rfp_data)
        timeline_patterns = [r"\d+\s?(days|weeks|months|quarters|years)", r"timeline[^0-9]*([\d,.]+\s?(days|weeks|months))"]
        for p in timeline_patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return "Timeline not mentioned"

    # old shorthand process kept
    def process(self, rfp_data):
        return {
            "business_requirements": self.extract_business_requirements(rfp_data),
            "budget": self.extract_budget(rfp_data),
            "timeline": self.extract_timeline(rfp_data),
            "sales_fit_score": self.compute_sales_fit_score(rfp_data)
        }
