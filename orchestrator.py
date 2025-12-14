from agents.sales_agent import SalesAgent
from agents.technical_agent import TechnicalAgent
from agents.pricing_agent import PricingAgent
from main_agent import MainAgent

def main():

    print("Initializing Agents...\n")

    # Load paths for the agent data
    sales = SalesAgent(data_folder="data/rfps/")
    technical = TechnicalAgent(products_csv="data/products.csv")
    pricing = PricingAgent(
        product_pricing_csv="data/product_pricing.csv",
        test_pricing_csv="data/test_pricing.csv"
    )

    print("Running Main Agent...\n")
    orchestrator = MainAgent(sales, technical, pricing)
    orchestrator.run()

if __name__ == "__main__":
    main()
