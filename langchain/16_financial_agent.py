"""Financial Agent - Specialized agent for stock market analysis and financial data."""

from mlutils import print_model_info
from model_switcher import MODEL_NAME, MODEL_PARAMS, PROVIDER, get_configured_model

import langchain
from langchain.agents import create_agent

# Import financial tools from the separate tools file
import sys
from pathlib import Path

# Add current directory to path to import the tools module
sys.path.insert(0, str(Path(__file__).parent))

from tools_16 import (
    calculate_market_cap_change,
    compare_stocks,
    get_nse_financial_statements,
    get_nse_stock_price,
    get_us_financial_statements,
    get_us_stock_price,
)

print(f"Langchain version: {langchain.__version__}")

# Define the tools available to the financial agent
tools = [
    get_us_stock_price,
    get_nse_stock_price,
    get_us_financial_statements,
    get_nse_financial_statements,
    calculate_market_cap_change,
    compare_stocks,
]

# Create system prompt for the financial agent
system_prompt = """You are a specialized financial analysis agent with expertise in stock markets and financial data.

Your capabilities include:
- Retrieving real-time stock prices and key metrics for US and Indian (NSE) stocks
- Analyzing financial statements including revenue, net income, assets, and debt
- Comparing multiple stocks side by side
- Calculating market capitalization changes over time
- Providing insights on PE ratios, 52-week ranges, and market trends

Guidelines:
- For Indian stocks (NSE), use symbols like RELIANCE, TCS, INFY, HDFCBANK
- For US/international stocks, use ticker symbols like AAPL, TSLA, MSFT, GOOGL
- When comparing stocks, consider market cap, PE ratio, and price performance
- Always provide context and analysis with the raw data
- Format numbers clearly with appropriate currency symbols ($ for USD, ₹ for INR)
- Be precise and professional in your financial analysis
"""

# Initialize the model
model = get_configured_model(temperature=0)
print_model_info(PROVIDER, MODEL_NAME, MODEL_PARAMS)

if model is None:
    print("\nERROR: Failed to initialize model. Please check:")
    print("1. For Ollama: Install langchain-ollama (pip install langchain-ollama)")
    print("2. For llama.cpp: Install langchain-openai (pip install langchain-openai)")
    print("3. Ensure your model provider is properly configured")
    exit(1)

# Create the financial agent
agent = create_agent(model, tools, system_prompt=system_prompt, debug=False)


def run_query(query: str):
    """Run a financial query and display the results with tool usage."""
    print(f"\n{'=' * 80}")
    print(f"Query: {query}")
    print(f"{'=' * 80}")

    try:
        # Invoke the agent with the query
        result = agent.invoke({"messages": [{"role": "user", "content": query}]})

        # Extract the messages
        messages = result.get("messages", [])

        # Track and display tool usage
        print("\nTool Usage:")
        print("-" * 80)
        for msg in messages:
            # Check for AI messages with tool calls
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get("name", "unknown")
                    tool_args = tool_call.get("args", {})
                    print(f"  Tool: {tool_name}")
                    print(f"  Arguments: {tool_args}")

            # Check for tool messages (results)
            if hasattr(msg, "name") and msg.name:
                tool_result = msg.content if hasattr(msg, "content") else str(msg)
                print(f"  Result Preview: {tool_result[:200]}{'...' if len(tool_result) > 200 else ''}")

        # Extract final answer
        if messages:
            final_message = messages[-1]
            final_answer = final_message.content if hasattr(final_message, "content") else str(final_message)
        else:
            final_answer = "No response generated"

        print(f"\n{'─' * 80}")
        print("Final Answer:")
        print(f"{'─' * 80}")
        print(final_answer)
        print(f"{'─' * 80}\n")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


# Example queries for the financial agent
if __name__ == "__main__":
    # US Stock queries
    run_query("What is the current stock price of Apple (AAPL)?")
    run_query("Show me the financial statements for Tesla (TSLA)")
    run_query("Compare Apple (AAPL) and Microsoft (MSFT) stocks")

    # Indian Stock queries
    run_query("What is the stock price of Reliance Industries?")
    run_query("Get financial data for TCS")

    # Advanced analysis
    run_query("How much has Tesla's market cap changed in the last 30 days?")
    run_query("Compare the PE ratios of AAPL and TSLA. Which is a better value?")
