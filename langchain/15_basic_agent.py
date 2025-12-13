from langchain_core.tools import tool
from mlutils import print_model_info
from model_switcher import MODEL_NAME, MODEL_PARAMS, PROVIDER, get_configured_model

import langchain
from langchain.agents import create_agent

print(f"Lancghain version: {langchain.__version__}  ")


@tool
def add(a: int, b: int) -> int:
    """Adds a and b."""
    return a + b


@tool
def multiply(a: int, b: int) -> int:
    """Multiplies a and b."""
    return a * b


@tool
def subtract(a: int, b: int) -> int:
    """Subtracts b from a."""
    return a - b


@tool
def divide(a: int, b: int) -> float:
    """Divides a by b."""
    if b == 0:
        return "Error: Division by zero"
    return a / b


@tool
def get_current_time() -> str:
    """Get the current time as a string."""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def get_local_timezone() -> str:
    """Get the local timezone as a string."""
    import time

    return time.tzname[time.localtime().tm_isdst]


@tool
def get_current_date() -> str:
    """Get the current date as a string."""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d")


# Separate tools that the agent can chain automatically for finding the time in a city
@tool
def identify_timezone(city: str) -> str:
    """Identify the IANA timezone for a given city using LLM reasoning.
    Returns the timezone identifier (e.g., 'America/New_York', 'Asia/Tokyo', 'Europe/London').
    Use this first before calculating time in a city."""
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a geography expert. Given a city name, identify its IANA timezone identifier. "
                "Return ONLY the timezone string (e.g., 'America/New_York', 'Asia/Tokyo', 'Europe/London', 'Asia/Kolkata'). "
                "Do not include any explanation, just the timezone identifier.",
            ),
            ("human", "What is the IANA timezone for {city}?"),
        ]
    )

    model = get_configured_model(temperature=0)
    chain = prompt | model | StrOutputParser()

    try:
        timezone = chain.invoke({"city": city}).strip()
        # Clean up any extra text the LLM might add
        timezone = timezone.replace("'", "").replace('"', "").strip()
        return timezone
    except Exception as e:
        return f"Error identifying timezone: {e}"


@tool
def calculate_time_in_timezone(timezone: str) -> str:
    """Calculate the current time in a given IANA timezone.
    Args:
        timezone: IANA timezone identifier like 'America/New_York', 'Asia/Tokyo', 'Asia/Kolkata', 'Europe/London'
    Returns the current time, timezone name, and time difference from local time."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    try:
        # Get current time in local timezone
        local_time = datetime.now().astimezone()

        # Get time in target timezone
        target_tz = ZoneInfo(timezone)
        target_time = datetime.now(target_tz)

        # Calculate time difference
        time_diff = target_time.utcoffset() - local_time.utcoffset()
        hours_diff = time_diff.total_seconds() / 3600

        return (
            f"\nCurrent time: {target_time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n" f"Timezone: {timezone}\n" f"Time difference from local: {hours_diff:+.1f} hours"
        )
    except Exception as e:
        return f"Error calculating time for timezone '{timezone}': {e}. Please verify the IANA timezone format."


@tool
def get_current_weather(location: str) -> str:
    """Get the current weather for a given location. Use city name like 'New York', 'London', 'Tokyo'."""
    import asyncio

    import python_weather

    async def get_weather():
        async with python_weather.Client(unit=python_weather.METRIC) as client:
            weather = await client.get(location)
            current = weather.temperature
            description = weather.description if hasattr(weather, "description") else "N/A"
            return f"Weather in {location}: {current}°C, {description}"

    try:
        return asyncio.run(get_weather())
    except Exception as e:
        return f"Weather error: Could not fetch weather for {location}. Error: {e}"


@tool
def search(query: str) -> str:
    """Search the web using DuckDuckGo."""
    from ddgs import DDGS

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if not results:
                return "No results found."

            # Format the results
            formatted_results = []
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                body = result.get("body", "No description")
                url = result.get("href", "")
                formatted_results.append(f"{i}. {title}\n   {body}\n   {url}")

            return "\n\n".join(formatted_results)
    except Exception as e:
        return f"Search error: {e}"


@tool
def wikipedia_search(query: str) -> str:
    """Search Wikipedia for a given query and return a summary from the results."""
    import wikipedia

    try:
        # First, search for the query to find matching pages
        search_results = wikipedia.search(query, results=5)

        if not search_results:
            return f"No Wikipedia articles found for '{query}'."

        # Try to get summary for the first result
        try:
            page_title = search_results[0]
            summary = wikipedia.summary(page_title, sentences=5, auto_suggest=False)
            return f"Article: {page_title}\n\n{summary}"
        except wikipedia.DisambiguationError as e:
            # If there's a disambiguation page, list the options
            options = e.options[:5]  # Get first 5 options
            return f"'{query}' is ambiguous. Did you mean one of these?\n" + "\n".join(f"- {opt}" for opt in options)
        except wikipedia.PageError:
            # If the page doesn't exist, try the next result
            if len(search_results) > 1:
                try:
                    page_title = search_results[1]
                    summary = wikipedia.summary(page_title, sentences=5, auto_suggest=False)
                    return f"Article: {page_title}\n\n{summary}"
                except Exception:
                    return f"Found these articles but couldn't retrieve summary: {', '.join(search_results[:3])}"
            else:
                return f"Page not found for '{query}'."
    except Exception as e:
        return f"Wikipedia error: {e}"


@tool
def get_nse_stock_price(symbol: str) -> str:
    """Get detailed stock information for Indian stocks (NSE) including price, company name, market cap, PE ratio, and 52-week range.
    Use stock symbols like 'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', etc."""
    import json

    from nsepython import nse_eq

    try:
        # Get stock quote data
        stock_data_raw = nse_eq(symbol.upper())

        if not stock_data_raw:
            return f"Could not retrieve stock data for symbol '{symbol}'. Please verify the NSE symbol."

        # Extract required information
        stock_data = {
            "symbol": symbol.upper(),
            "current_price": stock_data_raw.get("priceInfo", {}).get("lastPrice"),
            "company_name": stock_data_raw.get("info", {}).get("companyName"),
            "market_cap": stock_data_raw.get("metadata", {}).get("marketCap"),
            "pe_ratio": stock_data_raw.get("metadata", {}).get("pdSymbolPe"),
            "52_week_high": stock_data_raw.get("priceInfo", {}).get("weekHighLow", {}).get("max"),
            "52_week_low": stock_data_raw.get("priceInfo", {}).get("weekHighLow", {}).get("min"),
            "change": stock_data_raw.get("priceInfo", {}).get("change"),
            "percent_change": stock_data_raw.get("priceInfo", {}).get("pChange"),
        }

        # Check if we got valid data
        if stock_data["current_price"] is None:
            return f"Could not retrieve stock data for symbol '{symbol}'. Please verify the NSE symbol."

        # Format market cap for readability
        if stock_data["market_cap"]:
            market_cap_value = float(stock_data["market_cap"])
            if market_cap_value >= 1_00_000:  # 1 Lakh Crore
                stock_data["market_cap_formatted"] = f"₹{market_cap_value / 1_00_000:.2f} Lakh Cr"
            elif market_cap_value >= 1_000:  # 1000 Crore
                stock_data["market_cap_formatted"] = f"₹{market_cap_value / 1_000:.2f} Thousand Cr"
            else:
                stock_data["market_cap_formatted"] = f"₹{market_cap_value:.2f} Cr"

        # Return formatted JSON
        return json.dumps(stock_data, indent=2, ensure_ascii=False)

    except Exception as e:
        return f"NSE stock error: {e}"


@tool
def get_us_stock_price(ticker: str) -> str:
    """Get detailed stock information for a given ticker symbol including price, company name, market cap, PE ratio, and 52-week range."""
    import json

    import yfinance as yf

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Extract required information
        stock_data = {
            "symbol": ticker.upper(),
            "current_price": info.get("regularMarketPrice") or info.get("currentPrice"),
            "company_name": info.get("longName") or info.get("shortName"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE") or info.get("forwardPE"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
        }

        # Check if we got valid data
        if stock_data["current_price"] is None:
            return f"Could not retrieve stock data for ticker '{ticker}'. Please verify the ticker symbol."

        # Format market cap for readability
        if stock_data["market_cap"]:
            if stock_data["market_cap"] >= 1_000_000_000_000:
                stock_data["market_cap_formatted"] = f"${stock_data['market_cap'] / 1_000_000_000_000:.2f}T"
            elif stock_data["market_cap"] >= 1_000_000_000:
                stock_data["market_cap_formatted"] = f"${stock_data['market_cap'] / 1_000_000_000:.2f}B"
            elif stock_data["market_cap"] >= 1_000_000:
                stock_data["market_cap_formatted"] = f"${stock_data['market_cap'] / 1_000_000:.2f}M"
            else:
                stock_data["market_cap_formatted"] = f"${stock_data['market_cap']:,.0f}"

        # Return formatted JSON
        return json.dumps(stock_data, indent=2, ensure_ascii=False)

    except Exception as e:
        return f"Stock price error: {e}"


@tool
def get_us_financial_statements(ticker: str) -> str:
    """Retrieve key financial statement data for US/international stocks using ticker symbols like AAPL, TSLA, MSFT.
    Returns revenue, net income, total assets, and total debt for the latest available period."""
    import json

    import yfinance as yf

    try:
        stock = yf.Ticker(ticker)
        financials = stock.financials
        balance_sheet = stock.balance_sheet

        if financials.empty or balance_sheet.empty:
            return json.dumps({"error": f"No financial data available for {ticker}"}, indent=2)

        latest_period = financials.columns[0]

        # Extract period string
        period_str = str(latest_period.date()) if hasattr(latest_period, "date") else str(latest_period)

        # Build result dictionary
        result = {
            "symbol": ticker.upper(),
            "period": period_str,
            "currency": "USD",
            "revenue": None,
            "net_income": None,
            "total_assets": None,
            "total_debt": None,
        }

        # Safely extract financial data
        if "Total Revenue" in financials.index:
            result["revenue"] = float(financials.loc["Total Revenue", latest_period])
        if "Net Income" in financials.index:
            result["net_income"] = float(financials.loc["Net Income", latest_period])
        if "Total Assets" in balance_sheet.index:
            result["total_assets"] = float(balance_sheet.loc["Total Assets", latest_period])
        if "Total Debt" in balance_sheet.index:
            result["total_debt"] = float(balance_sheet.loc["Total Debt", latest_period])

        # Format numbers for readability
        for key in ["revenue", "net_income", "total_assets", "total_debt"]:
            if result.get(key) is not None:
                value = result[key]
                if abs(value) >= 1_000_000_000:
                    result[f"{key}_formatted"] = f"${value / 1_000_000_000:.2f}B"
                elif abs(value) >= 1_000_000:
                    result[f"{key}_formatted"] = f"${value / 1_000_000:.2f}M"
                else:
                    result[f"{key}_formatted"] = f"${value:,.0f}"

        return json.dumps(result, indent=2, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@tool
def get_nse_financial_statements(symbol: str) -> str:
    """Retrieve key financial statement data for Indian NSE stocks like RELIANCE, TCS, INFY, HDFCBANK.
    Returns revenue, net income, total assets, and total debt for the latest available period."""
    import json

    import yfinance as yf

    try:
        # Clean symbol and add .NS suffix
        clean_symbol = symbol.replace(".NS", "").replace(".BO", "").upper()

        stock = yf.Ticker(f"{clean_symbol}.NS")
        financials = stock.financials
        balance_sheet = stock.balance_sheet

        if financials.empty or balance_sheet.empty:
            return json.dumps({"error": f"No financial data available for {clean_symbol}"}, indent=2)

        latest_period = financials.columns[0]

        # Extract period string
        period_str = str(latest_period.date()) if hasattr(latest_period, "date") else str(latest_period)

        # Build result dictionary
        result = {
            "symbol": clean_symbol,
            "period": period_str,
            "currency": "INR",
            "revenue": None,
            "net_income": None,
            "total_assets": None,
            "total_debt": None,
        }

        # Safely extract financial data
        if "Total Revenue" in financials.index:
            result["revenue"] = float(financials.loc["Total Revenue", latest_period])
        if "Net Income" in financials.index:
            result["net_income"] = float(financials.loc["Net Income", latest_period])
        if "Total Assets" in balance_sheet.index:
            result["total_assets"] = float(balance_sheet.loc["Total Assets", latest_period])
        if "Total Debt" in balance_sheet.index:
            result["total_debt"] = float(balance_sheet.loc["Total Debt", latest_period])

        # Format numbers in Crores
        for key in ["revenue", "net_income", "total_assets", "total_debt"]:
            if result.get(key) is not None:
                value = result[key]
                if abs(value) >= 10_000_000:
                    result[f"{key}_formatted"] = f"₹{value / 10_000_000:.2f} Cr"
                else:
                    result[f"{key}_formatted"] = f"₹{value:,.0f}"

        return json.dumps(result, indent=2, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


tools = [
    add,
    multiply,
    subtract,
    divide,
    get_current_weather,
    get_current_time,
    get_current_date,
    identify_timezone,  # NEW: Step 1 - Identify timezone for a city
    calculate_time_in_timezone,  # NEW: Step 2 - Calculate time in that timezone
    search,
    get_local_timezone,
    wikipedia_search,
    get_us_stock_price,
    get_nse_stock_price,
    get_us_financial_statements,
    get_nse_financial_statements,
]

# Create system prompt for the agent
system_prompt = (
    "You are a helpful assistant. Use the available tools to answer questions. "
    "When asked about time in different cities, first use identify_timezone to get the timezone for the city, "
    "then use calculate_time_in_timezone with that timezone to get the current time. "
    "For any date, time, calendar related things use tools to get the current time first. "
    "For Indian stocks (NSE), use get_nse_stock_price with symbols like RELIANCE, TCS, INFY. "
    "For US/international stocks, use get_us_stock_price with tickers like AAPL, TSLA, MSFT. "
    "For US stock financials (revenue, net income, assets, debt), use get_us_financial_statements with tickers like AAPL, TSLA. "
    "For Indian stock financials, use get_nse_financial_statements with symbols like RELIANCE, TCS, INFY. "
    "Do not add any extra formatting."
)

model = get_configured_model(temperature=0)
print_model_info(PROVIDER, MODEL_NAME, MODEL_PARAMS)

if model is None:
    print("\nERROR: Failed to initialize model. Please check:")
    print("1. For Ollama: Install langchain-ollama (pip install langchain-ollama)")
    print("2. For llama.cpp: Install langchain-openai (pip install langchain-openai)")
    print("3. Ensure your model provider is properly configured")
    exit(1)

# Create the agent using the new langchain 1.0 API
agent = create_agent(model, tools, system_prompt=system_prompt, debug=False)


def run_query(query: str):
    """Run a query and show the tool usage and output."""
    print(f"\n{'=' * 60}")
    print(f"Query: {query}")
    print(f"{'=' * 60}")
    try:
        # Invoke the agent with the query
        result = agent.invoke({"messages": [{"role": "user", "content": query}]})

        # Extract the final response from messages
        messages = result.get("messages", [])

        # Track and display tool usage
        tool_calls_made = []
        for msg in messages:
            # Check for AI messages with tool calls
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get("name", "unknown")
                    tool_args = tool_call.get("args", {})
                    tool_calls_made.append({"name": tool_name, "args": tool_args})
                    print(f"\n Tool Used: {tool_name}")
                    print(f"   Arguments: {tool_args}")

            # Check for tool messages (results)
            if hasattr(msg, "name") and msg.name:
                tool_result = msg.content if hasattr(msg, "content") else str(msg)
                print(f"   Result: {tool_result}")

        # Extract final answer
        if messages:
            final_message = messages[-1]
            final_answer = final_message.content if hasattr(final_message, "content") else str(final_message)
        else:
            final_answer = "No response generated"

        print(f"\n{'─' * 60}")
        print(f"Final Answer: {final_answer}")
        print(f"{'─' * 60}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


# Test the tools
# run_query("search who is albert einstein?")

# run_query("what is 2 + 4")
# run_query("what is 2 * 4")
# run_query("what is 10 / 2")
# run_query("what is 8 - 3?")

# run_query("what is the current weather in London?")
# run_query("what is the current weather in Mumbai?")
# run_query("what is the current weather in San Jose, California?")
# run_query("what is the current date and time?")

# run_query("what is current timezone?")
# run_query("what is current time in New York?")
# run_query("what is the current time in Tokyo?")
# run_query("what is the current time in Mumbai?")
# run_query("what is the current time in Dubai?")
# run_query("what is the current time in Chennai?")
# run_query("what is the current time in Pune?")
# run_query("what is the current time in Satara?")
# run_query("what is the current time in Kolhapur?")

# run_query("wikipedia search on Golden Gate Bridge")
# run_query("how much 6!")
# run_query("what is the date on next sunday?")
# run_query("my dob is 13 jun 1986 what is my age as of today in month,days,hours?")

run_query("what is the stock price of AAPL?")
run_query("get me stock info for TSLA")
run_query("get me stock info for MCX.NS")
run_query("get me stock info for RELIANCE.NS")
run_query("what is the stock price of TCS.NS?")
run_query("show me INFY.NS stock details")

# US stocks
run_query("show me financial statements for AAPL")
run_query("what is TSLA revenue and profit?")

# Indian stocks
run_query("get financial data for RELIANCE")
run_query("what is TCS revenue and profit?")
