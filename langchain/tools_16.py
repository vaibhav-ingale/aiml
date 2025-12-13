"""Financial tools for stock analysis and market data."""

import json
from langchain_core.tools import tool


@tool
def get_nse_stock_price(symbol: str) -> str:
    """Get detailed stock information for Indian stocks (NSE) including price, company name, market cap, PE ratio, and 52-week range.
    Use stock symbols like 'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', etc."""
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


@tool
def calculate_market_cap_change(ticker: str, days: int = 30) -> str:
    """Calculate the change in market capitalization over a specified number of days for US stocks.
    Args:
        ticker: Stock ticker symbol (e.g., AAPL, TSLA, MSFT)
        days: Number of days to look back (default: 30)
    """
    import yfinance as yf

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=f"{days}d")

        if hist.empty or len(hist) < 2:
            return json.dumps({"error": f"Insufficient data for {ticker}"}, indent=2)

        # Get shares outstanding
        info = stock.info
        shares = info.get("sharesOutstanding")

        if not shares:
            return json.dumps({"error": "Shares outstanding data not available"}, indent=2)

        # Calculate market cap at first and last available dates
        first_date = hist.index[0]
        last_date = hist.index[-1]

        first_price = hist.iloc[0]["Close"]
        last_price = hist.iloc[-1]["Close"]

        first_market_cap = first_price * shares
        last_market_cap = last_price * shares

        change = last_market_cap - first_market_cap
        change_percent = (change / first_market_cap) * 100

        result = {
            "symbol": ticker.upper(),
            "start_date": str(first_date.date()),
            "end_date": str(last_date.date()),
            "initial_market_cap": first_market_cap,
            "current_market_cap": last_market_cap,
            "change": change,
            "change_percent": round(change_percent, 2),
        }

        # Format values
        if result["initial_market_cap"] >= 1_000_000_000:
            result["initial_market_cap_formatted"] = f"${first_market_cap / 1_000_000_000:.2f}B"
            result["current_market_cap_formatted"] = f"${last_market_cap / 1_000_000_000:.2f}B"
            result["change_formatted"] = f"${abs(change) / 1_000_000_000:.2f}B"

        return json.dumps(result, indent=2, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@tool
def compare_stocks(ticker1: str, ticker2: str) -> str:
    """Compare two stocks side by side with key metrics like price, market cap, PE ratio, and 52-week performance.
    Works for US stocks (e.g., AAPL vs MSFT)."""
    import yfinance as yf

    try:
        stocks_data = {}

        for ticker in [ticker1, ticker2]:
            stock = yf.Ticker(ticker)
            info = stock.info

            stocks_data[ticker.upper()] = {
                "company_name": info.get("longName") or info.get("shortName"),
                "current_price": info.get("regularMarketPrice") or info.get("currentPrice"),
                "market_cap": info.get("marketCap"),
                "market_cap_formatted": None,
                "pe_ratio": info.get("trailingPE") or info.get("forwardPE"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "52_week_change_percent": info.get("52WeekChange"),
            }

            # Format market cap
            mc = stocks_data[ticker.upper()]["market_cap"]
            if mc:
                if mc >= 1_000_000_000_000:
                    stocks_data[ticker.upper()]["market_cap_formatted"] = f"${mc / 1_000_000_000_000:.2f}T"
                elif mc >= 1_000_000_000:
                    stocks_data[ticker.upper()]["market_cap_formatted"] = f"${mc / 1_000_000_000:.2f}B"

        return json.dumps(stocks_data, indent=2, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)
