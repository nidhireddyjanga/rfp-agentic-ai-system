# Agentic AI System for B2B RFP Processing

## Overview
This project demonstrates an end-to-end Agentic AI system designed to automate and accelerate the B2B RFP response process for an industrial wires and cables manufacturer.

The solution simulates how Sales, Technical, and Pricing teams collaborate using AI agents to identify RFPs, match product specifications, estimate pricing, and generate a consolidated response.

---

## Problem Statement
Manual RFP processing causes delays in identification, technical evaluation, and pricing, reducing the chances of winning large B2B tenders.

---

## Solution Approach
We implemented a multi-agent architecture where each agent performs a specialized role, coordinated by a Main Orchestrator.

### Agents Involved

Sales Agent
- Identifies RFPs and extracts scope, due dates, quantities, and test requirements
- Prepares role-specific summaries for downstream agents

Technical Agent
- Matches RFP product specifications with OEM product SKUs
- Recommends Top-3 SKUs per item
- Calculates a Spec Match percentage
- Generates a comparison table for each RFP item

Pricing Agent
- Assigns unit prices using synthetic pricing data
- Adds testing and acceptance test costs
- Produces a consolidated pricing table

Main Agent (Orchestrator)
- Coordinates all agents
- Consolidates technical, pricing, and summary outputs
- Generates the final structured RFP response

---

## Key Features
- Multi-agent orchestration using Agentic AI principles
- Context-aware summaries for Technical and Pricing agents
- Top-3 product recommendation with spec match scoring
- Automated pricing estimation (products and tests)
- End-to-end pipeline execution
- Interactive Streamlit-based UI
- Agent execution logs for traceability

---

## Tech Stack
- Python
- Streamlit
- Pandas
- CSV-based synthetic datasets
- GitHub

---

## Project Structure

```text
rfp-ai-system-main/
├── agents/
│   ├── sales_agent.py
│   ├── technical_agent.py
│   └── pricing_agent.py
├── data/
│   ├── rfps/
│   ├── products.csv
│   ├── product_pricing.csv
│   └── test_pricing.csv
├── main_agent.py
├── orchestrator.py
├── ui_full.py
├── README.md
└── .gitignore
```

---

## How to Run the Project

Activate virtual environment  
.venv\Scripts\activate

Launch Streamlit UI  
streamlit run ui_full.py

---

## Demo Flow
1. Upload or select an RFP (Scan URL or local repository)
2. Run the pipeline
3. View:
   - Top-3 SKU recommendations
   - Pricing breakdown
   - Detailed item-level JSON
   - Agent execution logs
4. Download final response JSON

---

## Output
- Structured technical matching results
- Spec comparison tables
- Consolidated pricing estimates
- Final RFP response JSON
- Agent execution logs

---

## Team Contributions

- **Sales Agent Development**
  - RFP discovery, URL scanning, and RFP summarization logic

- **Technical Agent Development**
  - SKU–RFP specification matching
  - Spec match scoring logic
  - Top-3 product recommendations and comparison tables

- **Pricing Agent Development**
  - Product pricing estimation
  - Test and acceptance cost calculation
  - Consolidated pricing tables

- **Agent Orchestration & Integration**
  - Main agent workflow coordination
  - Inter-agent data flow and validation
  - End-to-end pipeline execution

- **Frontend & UX (Streamlit UI)**
  - RFP upload/selection interface
  - Pipeline execution controls
  - Results visualization (tables, expanders, logs)

- **System Design & Architecture**
  - Multi-agent architecture design
  - Data schema definition and assumptions


---

## Demo Video
Demo video attached separately as part of the submission.

---

## Disclaimer
All pricing data, product data, and RFPs used in this project are synthetic and created solely for demonstration purposes.
