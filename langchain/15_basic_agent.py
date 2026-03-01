import calendar
import time as time_module
# Get current context information for the prompt
from datetime import date, datetime, timedelta

from langchain_core.tools import tool
from mlutils import print_model_info
from model_switcher import get_model


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
    """Get the current date as a string in YYYY-MM-DD format."""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d")


@tool
def manipulate_date(
    base_date: str,
    other_date: str | None = None,
    diff_unit: str | None = None,
    add_days: int = 0,
    add_weeks: int = 0,
    add_months: int = 0,
    add_years: int = 0,
) -> dict | int | str:
    """
    Manipulate dates or calculate differences between two dates.

    IMPORTANT: base_date must be an actual date in YYYY-MM-DD format (e.g., "2026-01-06"),
    NOT a tool name. If you need current date, call get_current_date() first and use its result.

    Parameters:
    - base_date: Base date in YYYY-MM-DD format (e.g., "2026-01-06", "1986-06-13")
    - other_date: Optional second date in YYYY-MM-DD format for difference calculation
    - diff_unit: "days" | "weeks" | "months" | "years" | "all" (required when other_date is provided)
    - add_days: Integer number of days to add (positive) or subtract (negative)
    - add_weeks: Integer number of weeks to add (positive) or subtract (negative)
    - add_months: Integer number of months to add (positive) or subtract (negative)
    - add_years: Integer number of years to add (positive) or subtract (negative)

    Returns:
    - int: if single difference unit is requested (e.g., diff_unit="days" returns 45)
    - dict: if diff_unit="all" (returns {"days": 45, "weeks": 6, "months": 1, "years": 0})
    - str: ISO date string if date is modified (e.g., "2026-01-13")

    Examples:
    - Add 7 days to today: base_date="2026-01-06", add_days=7 → "2026-01-13"
    - Get age in all units: base_date="1986-06-13", other_date="2026-01-06", diff_unit="all"
    - Get weeks until birthday: base_date="2026-01-06", other_date="2026-06-13", diff_unit="weeks"
    """

    def to_date(d: str) -> date:
        return datetime.strptime(d, "%Y-%m-%d").date()

    base = to_date(base_date)

    # -----------------------------
    # DATE DIFFERENCE
    # -----------------------------
    if other_date and diff_unit:
        other = to_date(other_date)
        delta_days = (other - base).days

        months_diff = (other.year - base.year) * 12 + (other.month - base.month)
        years_diff = months_diff // 12

        if diff_unit == "days":
            return delta_days
        elif diff_unit == "weeks":
            return delta_days // 7
        elif diff_unit == "months":
            return months_diff
        elif diff_unit == "years":
            return years_diff
        elif diff_unit == "all":
            return {
                "days": delta_days,
                "weeks": delta_days // 7,
                "months": months_diff,
                "years": years_diff,
            }
        else:
            raise ValueError("diff_unit must be days, weeks, months, years, or all")

    # -----------------------------
    # DATE ADD / SUBTRACT
    # -----------------------------
    result = base + timedelta(days=add_days + add_weeks * 7)

    total_months = result.month - 1 + add_months + add_years * 12
    year = result.year + total_months // 12
    month = total_months % 12 + 1
    day = min(result.day, calendar.monthrange(year, month)[1])

    return date(year, month, day).isoformat()


# Separate tools that the agent can chain automatically for finding the time in a city
@tool
def identify_timezone(city: str) -> str:
    """Identify the IANA timezone for a given city.
    Returns the timezone identifier (e.g., 'America/New_York', 'Asia/Tokyo', 'Europe/London').
    Use this first before calculating time in a city."""

    # Static mapping for common cities - much faster than LLM
    CITY_TIMEZONE_MAP = {
        # ======================
        # United States
        # ======================
        "new york": "America/New_York",
        "nyc": "America/New_York",
        "boston": "America/New_York",
        "washington dc": "America/New_York",
        "philadelphia": "America/New_York",
        "miami": "America/New_York",
        "orlando": "America/New_York",
        "atlanta": "America/New_York",
        "detroit": "America/New_York",
        "tampa": "America/New_York",
        "chicago": "America/Chicago",
        "houston": "America/Chicago",
        "dallas": "America/Chicago",
        "austin": "America/Chicago",
        "san antonio": "America/Chicago",
        "minneapolis": "America/Chicago",
        "st louis": "America/Chicago",
        "nashville": "America/Chicago",
        "denver": "America/Denver",
        "boulder": "America/Denver",
        "salt lake city": "America/Denver",
        "albuquerque": "America/Denver",
        "los angeles": "America/Los_Angeles",
        "la": "America/Los_Angeles",
        "san francisco": "America/Los_Angeles",
        "san jose": "America/Los_Angeles",
        "oakland": "America/Los_Angeles",
        "palo alto": "America/Los_Angeles",
        "mountain view": "America/Los_Angeles",
        "sunnyvale": "America/Los_Angeles",
        "seattle": "America/Los_Angeles",
        "portland": "America/Los_Angeles",
        "san diego": "America/Los_Angeles",
        "phoenix": "America/Phoenix",  # no DST
        "scottsdale": "America/Phoenix",
        "las vegas": "America/Los_Angeles",
        # ======================
        # Canada
        # ======================
        "toronto": "America/Toronto",
        "ottawa": "America/Toronto",
        "montreal": "America/Toronto",
        "vancouver": "America/Vancouver",
        "calgary": "America/Edmonton",
        "edmonton": "America/Edmonton",
        "winnipeg": "America/Winnipeg",
        "halifax": "America/Halifax",
        # ======================
        # United Kingdom
        # ======================
        "london": "Europe/London",
        "manchester": "Europe/London",
        "birmingham": "Europe/London",
        "leeds": "Europe/London",
        "edinburgh": "Europe/London",
        "glasgow": "Europe/London",
        # ======================
        # Europe
        # ======================
        "paris": "Europe/Paris",
        "marseille": "Europe/Paris",
        "lyon": "Europe/Paris",
        "berlin": "Europe/Berlin",
        "munich": "Europe/Berlin",
        "hamburg": "Europe/Berlin",
        "frankfurt": "Europe/Berlin",
        "amsterdam": "Europe/Amsterdam",
        "brussels": "Europe/Brussels",
        "rome": "Europe/Rome",
        "milan": "Europe/Rome",
        "naples": "Europe/Rome",
        "madrid": "Europe/Madrid",
        "barcelona": "Europe/Madrid",
        "valencia": "Europe/Madrid",
        "lisbon": "Europe/Lisbon",
        "zurich": "Europe/Zurich",
        "geneva": "Europe/Zurich",
        "vienna": "Europe/Vienna",
        "prague": "Europe/Prague",
        "warsaw": "Europe/Warsaw",
        "budapest": "Europe/Budapest",
        "stockholm": "Europe/Stockholm",
        "oslo": "Europe/Oslo",
        "copenhagen": "Europe/Copenhagen",
        "helsinki": "Europe/Helsinki",
        "athens": "Europe/Athens",
        "istanbul": "Europe/Istanbul",
        "moscow": "Europe/Moscow",
        # ======================
        # India
        # ======================
        "mumbai": "Asia/Kolkata",
        "bombay": "Asia/Kolkata",
        "delhi": "Asia/Kolkata",
        "new delhi": "Asia/Kolkata",
        "bangalore": "Asia/Kolkata",
        "bengaluru": "Asia/Kolkata",
        "chennai": "Asia/Kolkata",
        "kolkata": "Asia/Kolkata",
        "pune": "Asia/Kolkata",
        "hyderabad": "Asia/Kolkata",
        "ahmedabad": "Asia/Kolkata",
        "jaipur": "Asia/Kolkata",
        "chandigarh": "Asia/Kolkata",
        "kochi": "Asia/Kolkata",
        "trivandrum": "Asia/Kolkata",
        # ======================
        # Asia
        # ======================
        "tokyo": "Asia/Tokyo",
        "osaka": "Asia/Tokyo",
        "kyoto": "Asia/Tokyo",
        "seoul": "Asia/Seoul",
        "beijing": "Asia/Shanghai",
        "shanghai": "Asia/Shanghai",
        "shenzhen": "Asia/Shanghai",
        "guangzhou": "Asia/Shanghai",
        "hong kong": "Asia/Hong_Kong",
        "taipei": "Asia/Taipei",
        "singapore": "Asia/Singapore",
        "bangkok": "Asia/Bangkok",
        "kuala lumpur": "Asia/Kuala_Lumpur",
        "jakarta": "Asia/Jakarta",
        "manila": "Asia/Manila",
        "dubai": "Asia/Dubai",
        "abu dhabi": "Asia/Dubai",
        "riyadh": "Asia/Riyadh",
        "jeddah": "Asia/Riyadh",
        "tel aviv": "Asia/Jerusalem",
        # ======================
        # Africa
        # ======================
        "cairo": "Africa/Cairo",
        "lagos": "Africa/Lagos",
        "nairobi": "Africa/Nairobi",
        "johannesburg": "Africa/Johannesburg",
        "cape town": "Africa/Johannesburg",
        "accra": "Africa/Accra",
        # ======================
        # South America
        # ======================
        "sao paulo": "America/Sao_Paulo",
        "rio de janeiro": "America/Sao_Paulo",
        "buenos aires": "America/Argentina/Buenos_Aires",
        "santiago": "America/Santiago",
        "bogota": "America/Bogota",
        "lima": "America/Lima",
        # ======================
        # Australia & NZ
        # ======================
        "sydney": "Australia/Sydney",
        "melbourne": "Australia/Melbourne",
        "brisbane": "Australia/Brisbane",
        "perth": "Australia/Perth",
        "adelaide": "Australia/Adelaide",
        "auckland": "Pacific/Auckland",
        "wellington": "Pacific/Auckland",
    }

    city_lower = city.lower().strip()

    # Check static map first (fast path)
    if city_lower in CITY_TIMEZONE_MAP:
        return CITY_TIMEZONE_MAP[city_lower]

    # Fallback: Use LLM for unknown cities (slow path)
    try:
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a geography expert. Return ONLY the IANA timezone identifier. "
                    "Examples: 'America/New_York', 'Asia/Tokyo', 'Europe/London'. No explanation.",
                ),
                ("human", "IANA timezone for {city}?"),
            ]
        )

        # Reuse global model (don't create new one or print info)
        llm = get_model(temperature=0)
        chain = prompt | llm | StrOutputParser()

        timezone = chain.invoke({"city": city}).strip()
        timezone = timezone.replace("'", "").replace('"', "").strip()
        return timezone
    except Exception as e:
        return f"Error: {e}"


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
    manipulate_date,
    identify_timezone,
    calculate_time_in_timezone,
    search,
    get_local_timezone,
    wikipedia_search,
    get_us_stock_price,
    get_nse_stock_price,
    get_us_financial_statements,
    get_nse_financial_statements,
]


current_datetime = datetime.now()
current_date = current_datetime.strftime("%Y-%m-%d")
current_time = current_datetime.strftime("%H:%M:%S")
current_day = current_datetime.strftime("%A")
current_timezone = time_module.tzname[time_module.localtime().tm_isdst]
hostname = "San Jose, CA"

# Create system prompt for the agent with chain-of-thought reasoning and context
system_prompt = f"""You are a helpful assistant that thinks step-by-step before answering questions.
Use the available tools to get accurate information.

**CURRENT CONTEXT:**
- Current Date: {current_date} ({current_day})
- Current Time: {current_time}
- Timezone: {current_timezone}
- Location/Host: {hostname}

**THINKING PROCESS:**
Before using tools, think through:
1. What information do I need?
2. Which tool(s) should I use?
3. In what order should I use them?
4. What are the correct parameters?

**DATE AND TIME INSTRUCTIONS:**
- First, understand what the user is asking (current date? future date? past date? age?)
- Always use the `manipulate_date` tool when a user asks about dates.
- Do NOT calculate dates manually.
- **CRITICAL**: Dates must ALWAYS be in YYYY-MM-DD format when calling tools.
- **CRITICAL**: You CANNOT nest tool calls. If you need current date, call get_current_date FIRST, wait for result, THEN use that result in manipulate_date.
- Use:
  - diff_unit="days" | "weeks" | "months" | "years" for a single unit
  - diff_unit="all" when the user asks for multiple or all units (age, time difference with multiple units)
- Use positive or negative values for add/subtract operations.
- For current date: use get_current_date tool
- For current time: use get_current_time tool
- For date addition/subtraction:
  1. FIRST call get_current_date to get today's date in YYYY-MM-DD format
  2. THEN call manipulate_date with the actual date (e.g., "2026-01-06") as base_date
- For date difference (age, days until, etc.):
  1. FIRST call get_current_date to get today's date
  2. THEN call manipulate_date with base_date=<today>, other_date=<target_date>, diff_unit="all" or specific unit
- For time in different cities: First identify_timezone, then calculate_time_in_timezone

**EXAMPLES:**
- "What is the date 7 days from now?"
  Step 1: Call get_current_date → Result: "2026-01-06"
  Step 2: Call manipulate_date(base_date="2026-01-06", add_days=7) → Result: "2026-01-13"

- "My DOB is 13 Jun 1986, what is my age?"
  Step 1: Call get_current_date → Result: "2026-01-06"
  Step 2: Call manipulate_date(base_date="1986-06-13", other_date="2026-01-06", diff_unit="all") → Result: age breakdown

- "How many weeks until June 13?"
  Step 1: Call get_current_date → Result: "2026-01-06"
  Step 2: Call manipulate_date(base_date="2026-01-06", other_date="2026-06-13", diff_unit="weeks") → Result: number of weeks

**STOCK INSTRUCTIONS:**
- Indian stocks (NSE): use get_nse_stock_price (symbols: RELIANCE, TCS, INFY, HDFCBANK)
- US/international stocks: use get_us_stock_price (tickers: AAPL, TSLA, MSFT, GOOGL)
- US stock financials: use get_us_financial_statements
- Indian stock financials: use get_nse_financial_statements

**GENERAL RULES:**
- ALWAYS use tools - never guess or make up information
- Show your reasoning before calling tools
- If a tool fails, explain why and try an alternative approach
- Be precise with tool parameters (e.g., days must be integers)
- Keep final answers clear and concise, If possible provide answer in one line do not include emojis or other decorations
** Do not explain your reasoning in the final answer. **
"""
import uuid

SESSION_ID = f"15basic-agent-{str(uuid.uuid4())[-4:]}"

# Get model with settings optimized for reasoning
# Note: For best results, use reasoning models like deepseek-r1, qwen3, or gpt-4 in model_switcher.py
# model = get_model(temperature=0.1, max_tokens=5000)  # Increased tokens for chain-of-thought reasoning
model = get_model(temperature=0.1, max_tokens=5000, session_id=SESSION_ID)

print_model_info(model)

if model is None:
    print("\nERROR: Failed to initialize model. Please check:")
    print("1. For Ollama: Install langchain-ollama (pip install langchain-ollama)")
    print("2. For llama.cpp: Install langchain-openai (pip install langchain-openai)")
    print("3. Ensure your model provider is properly configured")
    exit(1)

# Bind tools to model
model_with_tools = model.bind_tools(tools)


def run_query(query: str, verbose: bool = True):
    """Run a query and show the tool usage and output with full message logging."""
    print(f"\n{'?' * 80}")
    print(f"Query: {query}")
    print(f"{'?' * 80}")

    try:
        from langchain_core.messages import (HumanMessage, SystemMessage,
                                             ToolMessage)

        # Build message history with system prompt
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=query)]

        if verbose:
            print(f"\nSystem Message:")
            print(f"   {system_prompt[:100]}..." if len(system_prompt) > 100 else f"   {system_prompt}")
            print(f"\nHuman Message:")
            print(f"   {query}")

        # Initial invocation
        response = model_with_tools.invoke(messages)
        messages.append(response)

        if verbose:
            print(f"\nAI Response:")
            if hasattr(response, "content") and response.content:
                print(f"   Content: {response.content}")

        # Handle tool calls iteratively
        max_iterations = 10
        iteration = 0

        while hasattr(response, "tool_calls") and response.tool_calls and iteration < max_iterations:
            iteration += 1
            # print(f"\n{'─' * 80}")
            # print(f"Iteration {iteration}")
            # print(f"{'─' * 80}")

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_id = tool_call["id"]

                # print(f"\n🔧 Tool Call: {tool_name}")
                # print(f"   ID: {tool_id}")
                # print(f"   Arguments: {tool_args}")

                # Find and execute the tool
                tool_to_call = None
                for tool in tools:
                    if tool.name == tool_name:
                        tool_to_call = tool
                        break

                if tool_to_call:
                    try:
                        tool_result = tool_to_call.invoke(tool_args)
                        print(f"  Result: {tool_result}")

                        # Add tool message
                        messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_id, name=tool_name))
                    except Exception as e:
                        error_msg = f"Error executing tool: {e}"
                        print(f"  Error: {error_msg}")
                        messages.append(ToolMessage(content=error_msg, tool_call_id=tool_id, name=tool_name))
                else:
                    print(f"  Error: Tool '{tool_name}' not found")

            # Get next response
            response = model_with_tools.invoke(messages)
            messages.append(response)

            if verbose and hasattr(response, "content") and response.content:
                print(f"\nAI Response:")
                print(f"   Content: {response.content}")

        # Extract final answer
        final_answer = response.content if hasattr(response, "content") else str(response)

        print(f"\n{'$' * 80}")
        print(f"FINAL ANSWER: {final_answer}")
        print(f"{'$' * 80}\n")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


# Test the tools
run_query("search who is albert einstein?")

run_query("what is 2 + 4")
run_query("what is 2 * 4")
run_query("what is 10 / 2")
run_query("what is 8 - 3?")

run_query("what is the current weather in London?")
# run_query("what is the current weather in Mumbai?")
# run_query("what is the current weather in San Jose, California?")
run_query("what is the current date and time?")

run_query("what is current timezone?")
# run_query("what is current time in New York?")
run_query("what is the current time in Tokyo?")
# run_query("what is the current time in Mumbai?")
run_query("what is the current time in Dubai?")
# run_query("what is the current time in Chennai?")
# run_query("what is the current time in Pune?")
# run_query("what is the current time in Satara?")
# run_query("what is the current time in Kolhapur?")

# run_query("wikipedia search on Golden Gate Bridge")
# run_query("how much 6!")
# run_query("what is the date after 7 days?")
# run_query("what is the date on next sunday?")
# run_query("how many weeks until my birthday on 13 june")
# run_query("my dob is 13 jun 1986 what is my age as of today in month,days,hours?")

# run_query("what is the stock price of AAPL?")
run_query("get me stock info for TSLA")
# run_query("get me stock info for MCX.NS")
# run_query("get me stock info for RELIANCE.NS")
# run_query("what is the stock price of TCS.NS?")
# run_query("show me INFY.NS stock details")

# # US stocks
# run_query("show me financial statements for AAPL")
# run_query("what is TSLA revenue and profit?")

# # Indian stocks
# run_query("get financial data for RELIANCE")
# run_query("what is TCS revenue and profit?")
