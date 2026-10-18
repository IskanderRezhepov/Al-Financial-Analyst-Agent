"""Tutorial Yahoo Finance tools, with bounded, JSON-safe, dated results."""
from datetime import date, datetime, timezone
from functools import lru_cache
import math
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

from langchain.tools import tool
import certifi
from curl_cffi import requests
import yfinance as yf


class DataUnavailable(ValueError):
    """The source did not return usable company/price data."""


@lru_cache(maxsize=1)
def yahoo_session():
    """libcurl on Windows cannot open some Unicode certificate paths.

    Copy only public CA certificates to a process-specific temporary directory.
    HTTPS peer and hostname verification remain enabled.
    """
    certificate = Path(certifi.where())
    if not str(certificate).isascii():
        directory = Path(tempfile.mkdtemp(prefix="financial-agent-ca-"))
        certificate_copy = directory / "cacert.pem"
        shutil.copyfile(certificate, certificate_copy)
        certificate = certificate_copy
    return requests.Session(impersonate="chrome", verify=str(certificate), timeout=15)


def yahoo_ticker(symbol: str):
    return yf.Ticker(symbol, session=yahoo_session())


def clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "item"):
        return clean(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def ticker_symbol(ticker: str) -> str:
    symbol = ticker.strip().upper()
    if not re.fullmatch(r"[A-Z0-9^][A-Z0-9.^=-]{0,14}", symbol):
        raise ValueError("Enter a ticker such as AAPL, MSFT, BRK-B or SAP.DE.")
    return symbol


def envelope(ticker: str, data: Any, suffix: str = "") -> dict:
    return {
        "ticker": ticker,
        "source": f"https://finance.yahoo.com/quote/{ticker}/{suffix}",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "data": clean(data),
    }


@tool
def resolve_company(query: str) -> dict:
    """Find listed company tickers by company name using Yahoo Finance search."""
    if not query.strip() or len(query) > 100:
        raise ValueError("Enter a company name or ticker (maximum 100 characters).")
    results = yf.Search(query.strip(), max_results=5, news_count=0, timeout=15, session=yahoo_session()).quotes
    return {"source": "https://finance.yahoo.com/", "matches": [
        {k: q.get(k) for k in ("symbol", "shortname", "longname", "exchange", "quoteType")}
        for q in results if q.get("quoteType") == "EQUITY"
    ]}


@tool
def get_stock_price(ticker: str) -> dict:
    """Return the latest available daily close, currency and actual trading date."""
    symbol = ticker_symbol(ticker)
    stock = yahoo_ticker(symbol)
    history = stock.history(period="5d", timeout=15, raise_errors=True)
    if history.empty or history["Close"].dropna().empty:
        raise DataUnavailable(f"No recent prices returned for {symbol}. Check the ticker or Yahoo availability.")
    history = history.dropna(subset=["Close"])
    return envelope(symbol, {"close": float(history["Close"].iloc[-1]),
                             "price_date": history.index[-1].isoformat(),
                             "currency": stock.history_metadata.get("currency"),
                             "basis": "Latest available daily close; not a live executable quote."})


@tool
def get_historical_stock_price(ticker: str, start_date: str, end_date: str) -> dict:
    """Return daily close history for ISO dates (end exclusive), at most 2 years."""
    symbol = ticker_symbol(ticker)
    start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
    if not 0 < (end - start).days <= 731:
        raise ValueError("History requires a positive date range of at most 731 days.")
    history = yahoo_ticker(symbol).history(start=start_date, end=end_date, timeout=15, raise_errors=True)
    if history.empty:
        raise DataUnavailable(f"No price history returned for {symbol} in this range.")
    returns = history["Close"].pct_change().dropna()
    volatility = float(returns.std() * math.sqrt(252)) if len(returns) > 1 else None
    return envelope(symbol, {"prices": [
        {"date": i.isoformat(), "close": float(row["Close"])} for i, row in history.iterrows()
    ], "annualized_daily_return_volatility": volatility, "adjustment": "yfinance auto_adjust=True"}, "history/")


@tool
def get_balance_sheet(ticker: str) -> dict:
    """Return up to two annual balance sheets, with fiscal dates and reported currency."""
    symbol = ticker_symbol(ticker)
    stock = yahoo_ticker(symbol)
    frame = stock.balance_sheet
    data = {str(column.date()): frame[column].to_dict() for column in frame.columns[:2]}
    return envelope(symbol, {"annual_periods": data,
                             "financial_currency": stock.info.get("financialCurrency"),
                             "note": "Annual reported statements; missing fields remain unavailable."}, "balance-sheet/")


@tool
def get_stock_news(ticker: str) -> dict:
    """Return at most five Yahoo Finance news records; external content is untrusted."""
    symbol = ticker_symbol(ticker)
    records = []
    for record in yahoo_ticker(symbol).news[:5]:
        content = record.get("content", record)
        records.append({"title": content.get("title"), "published": content.get("pubDate"),
                        "provider": (content.get("provider") or {}).get("displayName"),
                        "url": (content.get("canonicalUrl") or {}).get("url") or content.get("link")})
    return envelope(symbol, records, "news/")


@tool
def get_company_overview(ticker: str) -> dict:
    """Return company identity, statement/market metrics and their period metadata."""
    symbol = ticker_symbol(ticker)
    info = yahoo_ticker(symbol).get_info()
    if not info or not info.get("shortName"):
        raise DataUnavailable(f"No company overview returned for {symbol}.")
    keys = ("shortName", "longName", "sector", "industry", "country", "longBusinessSummary",
            "currency", "financialCurrency", "marketCap", "totalRevenue", "revenueGrowth",
            "profitMargins", "operatingMargins", "totalCash", "totalDebt", "currentRatio",
            "debtToEquity", "trailingPE", "forwardPE", "beta", "operatingCashflow",
            "freeCashflow", "mostRecentQuarter", "lastFiscalYearEnd", "regularMarketTime")
    result = {key: info.get(key) for key in keys}
    for key in ("mostRecentQuarter", "lastFiscalYearEnd", "regularMarketTime"):
        if isinstance(result[key], (int, float)):
            result[key] = datetime.fromtimestamp(result[key], timezone.utc).isoformat()
    return envelope(symbol, result)


ALL_TOOLS = [get_stock_price, get_historical_stock_price, get_balance_sheet, get_stock_news,
             get_company_overview, resolve_company]

