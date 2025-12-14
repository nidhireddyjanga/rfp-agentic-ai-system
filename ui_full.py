# ui_full.py
import streamlit as st
import json
import pandas as pd
import os
import tempfile

from agents.sales_agent import SalesAgent
from agents.technical_agent import TechnicalAgent
from agents.pricing_agent import PricingAgent
from main_agent import MainAgent

st.set_page_config(page_title="RFP AI System", layout="wide")

# -------------------
# Global CSS (tabs fix + basic styling)
# -------------------
st.markdown("""
<style>
/* Title */
.big-title { font-size:50px !important; font-weight:900; text-align:center; margin-bottom:6px; }
.sub-title { font-size:18px !important; text-align:center; color:#666; margin-bottom:20px; }

/* Remove baseweb tab underline and force blue highlight */
div[data-baseweb="tab"] {
    border-bottom: 0 !important;
    box-shadow: none !important;
}
div[data-baseweb="tab-highlight"] {
    background: #4a90e2 !important;
    height: 3px !important;
}
.stTabs [aria-selected="true"] {
    color: #1f6feb !important;
    font-weight: 700 !important;
}
.stTabs [aria-selected="false"] {
    color: #888 !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------
# Header
# -------------------
st.markdown("<p class='big-title'>AI-Powered RFP Automation System</p>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Sales → Technical (Top-3 SKU matching) → Pricing — end-to-end demo</p>", unsafe_allow_html=True)
st.markdown("---")

# -------------------
# Step 1: Input selection
# -------------------
st.markdown("## Step 1 — Select RFP Input Source")

choice = st.radio(
    "Choose how you want to provide the RFP:",
    ["Scan URLs for RFPs", "Choose from Sample RFPs", "Upload an RFP"],
    horizontal=True
)

rfp_json = None
selected_file_path = None

if choice == "Scan URLs for RFPs":
    st.markdown("### Scan URLs (demo: maps to local sample RFPs)")
    urls = st.text_area("Enter RFP listing URLs (one per line) or leave blank to auto-discover local RFPs", height=100)
    if st.button("Scan URLs"):
        sales = SalesAgent(data_folder="data/rfps/")
        urls_list = [u.strip() for u in urls.splitlines() if u.strip()]
        try:
            rfp_json = sales.scan_urls_for_rfps(urls_list)
        except Exception:
            rfp_json = None
        if rfp_json:
            st.success("RFP identified (demo).")
            st.json(rfp_json)
        else:
            st.warning("No RFP found (make sure there are JSON files under data/rfps/).")

elif choice == "Choose from Sample RFPs":
    st.markdown("### Choose an RFP from data/rfps/")
    try:
        sample_files = sorted([f for f in os.listdir("data/rfps/") if f.endswith(".json")])
    except Exception:
        sample_files = []
    if not sample_files:
        st.info("No sample RFPs found in data/rfps/. Upload one or use scan option.")
    else:
        selected = st.selectbox("Choose RFP file", sample_files)
        if selected:
            selected_file_path = os.path.join("data/rfps", selected)
            try:
                with open(selected_file_path, "r", encoding="utf-8") as fh:
                    rfp_json = json.load(fh)
                st.success(f"Loaded: {selected}")
                st.json(rfp_json)
            except Exception as e:
                st.error(f"Could not load selected file: {e}")
                rfp_json = None

elif choice == "Upload an RFP":
    st.markdown("### Upload a JSON RFP file")
    uploaded = st.file_uploader("Upload RFP JSON", type=["json"])
    if uploaded:
        try:
            rfp_json = json.load(uploaded)
            st.success("RFP uploaded and parsed.")
            st.json(rfp_json)
        except Exception as e:
            st.error("Uploaded file could not be parsed as JSON.")
            rfp_json = None

# -------------------
# Step 2: Run pipeline
# -------------------
st.markdown("---")
st.markdown("## Step 2 — Run RFP Processing Pipeline")

if st.button("Run Pipeline", use_container_width=True):
    if not rfp_json:
        st.error("No RFP provided. Upload or select an RFP before running the pipeline.")
        st.stop()

    # Initialize agents
    sales = SalesAgent(data_folder="data/rfps/")
    technical = TechnicalAgent(products_csv="data/products.csv")
    pricing = PricingAgent(
        product_pricing_csv="data/product_pricing.csv",
        test_pricing_csv="data/test_pricing.csv"
    )

    main_agent = MainAgent(sales, technical, pricing)

    with st.spinner("Running multi-agent pipeline..."):
        try:
            final_output = main_agent.process_rfp(rfp_json)
            st.session_state["final_output"] = final_output
            st.success("Pipeline completed — see tabs below.")
        except Exception as e:
            st.error(f"Pipeline failed: {e}")
            st.session_state["final_output"] = None

# -------------------
# Results area (if pipeline run)
# -------------------
if "final_output" in st.session_state and st.session_state["final_output"]:
    final_output = st.session_state["final_output"]

    # 👇 ADD LOGS TAB HERE
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Technical Match", "Pricing", "Pipeline Logs", "Final JSON Output"]
    )

    # -------------------
    # Technical Match tab
    # -------------------
    with tab1:
        st.subheader("Top-3 SKU Recommendations (per item)")
        items = final_output.get("technical_match", {}).get("items", [])
        if not items:
            st.info("No technical match results found.")
        else:
            rows = []
            for it in items:
                top3 = it.get("top3", [])
                rows.append({
                    "Item": it.get("rfp_item") or it.get("description") or it.get("item_id"),
                    "Top1 SKU": top3[0]["sku"] if len(top3) > 0 else "",
                    "Top1 %": top3[0]["spec_match_pct"] if len(top3) > 0 else "",
                    "Top2 SKU": top3[1]["sku"] if len(top3) > 1 else "",
                    "Top2 %": top3[1]["spec_match_pct"] if len(top3) > 1 else "",
                    "Top3 SKU": top3[2]["sku"] if len(top3) > 2 else "",
                    "Top3 %": top3[2]["spec_match_pct"] if len(top3) > 2 else ""
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

            for it in items:
                label = it.get("rfp_item") or it.get("item_id")
                with st.expander(f"Details — {label}"):
                    st.markdown("**RFP item**")
                    st.json({"item_id": it.get("item_id"), "description": it.get("rfp_item")})
                    st.markdown("**Top-3 candidates**")
                    st.json(it.get("top3", []))

    # -------------------
    # Pricing tab
    # -------------------
    with tab2:
        st.subheader("Pricing")
        pricing_table = final_output.get("pricing", {}).get("pricing_table", [])
        if pricing_table:
            st.dataframe(pd.DataFrame(pricing_table), use_container_width=True)
        else:
            st.info("No pricing entries found.")

    # -------------------
    # Logs tab (NEW)
    # -------------------
    with tab3:
        st.subheader("Pipeline Execution Logs")

        logs = final_output.get("logs", [])
        if not logs:
            st.info("No logs available.")
        else:
            for line in logs:
                line = line.strip()
                if not line:
                    continue  # 🚫 skip blank lines

                # Agent headers
                if line.startswith("[") and line.endswith("]"):
                    agent_name = line.replace("[", "").replace("]", "")
                    st.markdown(
                        f"""
                        <div style="
                            font-size:20px;
                            font-weight:700;
                            margin-top:18px;
                            margin-bottom:8px;
                        ">
                            {agent_name}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"- {line}")

    # -------------------
    # Final JSON tab
    # -------------------
    with tab4:
        st.subheader("Final response JSON")
        st.json(final_output)
        st.download_button(
            "Download final_response.json",
            data=json.dumps(final_output, indent=2),
            file_name="final_response.json",
            mime="application/json",
            use_container_width=True
        )

else:
    st.info("No pipeline output yet. Run the pipeline after selecting or uploading an RFP.")

