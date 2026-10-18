"""Build factual report sections directly from tool values, never model arithmetic."""


def number(value, suffix=""):
    return f"{value:,.2f}{suffix}" if isinstance(value, (int, float)) else "Unavailable"


def percent(value):
    return number(value * 100, "%") if isinstance(value, (int, float)) else "Unavailable"


def summary_signals(snapshot: dict) -> dict[str, str]:
    """Only source-supported statements may appear in the AI-prioritized summary."""
    info = snapshot.get("overview", {}).get("data", {})
    signals = {
        "period_caution": "Reported overview fields and annual statements can refer to different periods; verify alignment against filings.",
        "valuation_context": "No peer benchmark was retrieved, so valuation cannot be judged cheap or expensive from these metrics alone.",
        "human_review": "An authorized human must review the source evidence and business context before any financial or underwriting decision.",
    }
    margin, ratio = info.get("profitMargins"), info.get("currentRatio")
    if isinstance(margin, (int, float)):
        signals["profitability"] = "Reported net profitability is positive." if margin > 0 else "Reported net profitability is nonpositive; investigate its causes and sustainability."
    if isinstance(ratio, (int, float)):
        signals["liquidity"] = "The reported current ratio is at least one; sector context and liability maturities still require review." if ratio >= 1 else "The reported current ratio is below one, suggesting a need to investigate short-term liquidity."
    cash, debt = info.get("totalCash"), info.get("totalDebt")
    if isinstance(cash, (int, float)) and isinstance(debt, (int, float)):
        signals["cash_debt"] = "Reported debt exceeds reported cash; review cash generation and maturity schedules rather than inferring distress." if debt > cash else "Reported cash covers reported debt at this snapshot; this alone does not establish creditworthiness."
    if not snapshot.get("news", {}).get("data"):
        signals["news_gap"] = "Recent news data was unavailable, so no conclusion about adverse events can be drawn."
    return signals


def factual_report(snapshot: dict, warnings: list[str], synthesis: str = "") -> str:
    info = snapshot.get("overview", {}).get("data", {})
    price = snapshot.get("price", {}).get("data", {})
    history = snapshot.get("history", {}).get("data", {})
    financial_currency = info.get("financialCurrency") or "currency unavailable"
    market_currency = info.get("currency") or "currency unavailable"
    cash, debt = info.get("totalCash"), info.get("totalDebt")
    risks = ["Yahoo Finance is a secondary source; confirm material facts against original filings."]
    positives = []
    if isinstance(info.get("currentRatio"), (int, float)) and info["currentRatio"] < 1:
        risks.append("Reported current ratio is below one; investigate liquidity in sector context.")
    if cash is not None and debt is not None and debt > cash:
        risks.append("Reported debt exceeds cash; inspect maturity schedules and cash generation.")
    if isinstance(info.get("profitMargins"), (int, float)):
        if info["profitMargins"] < 0:
            risks.append("Reported profit margin is negative.")
        elif info["profitMargins"] > 0:
            positives.append("Reported net profit margin is positive.")
    if isinstance(info.get("revenueGrowth"), (int, float)):
        if info["revenueGrowth"] > 0:
            positives.append("Yahoo's reported revenue-growth field is positive; its comparison period is not supplied here.")
        elif info["revenueGrowth"] < 0:
            risks.append("Yahoo's reported revenue-growth field is negative; verify its comparison period.")
    if isinstance(info.get("operatingCashflow"), (int, float)) and info["operatingCashflow"] > 0:
        positives.append("Reported operating cash flow is positive.")
    news = snapshot.get("news", {}).get("data", [])
    if not news:
        risks.append("Recent news is unavailable. No conclusion about the presence or absence of adverse events can be drawn.")
    risks.extend(warnings)
    periods = snapshot.get("balance_sheet", {}).get("data", {}).get("annual_periods", {})
    statements = ", ".join(periods) or "Unavailable"
    return "\n\n".join([
        "## 1. Company Overview\n" + str(info.get("longName") or info.get("shortName") or "Company name unavailable")
        + f". Sector: {info.get('sector') or 'Unavailable'}. Industry: {info.get('industry') or 'Unavailable'}.",
        "## 2. Revenue / Growth\n"
        + f"Reported total revenue (Yahoo totalRevenue): {number(info.get('totalRevenue'))} {financial_currency}. "
        + f"Reported revenue growth: {percent(info.get('revenueGrowth'))}. "
        + "The growth comparison period is not supplied by this tool; do not treat it as full-year revenue growth. "
        + f"Most recent quarter metadata: {info.get('mostRecentQuarter') or 'Unavailable'}.",
        "## 3. Profitability\n"
        + f"Net profit margin: {percent(info.get('profitMargins'))}. Operating margin: {percent(info.get('operatingMargins'))}. "
        + f"Operating cash flow: {number(info.get('operatingCashflow'))} {financial_currency}. "
        + f"Free cash flow: {number(info.get('freeCashflow'))} {financial_currency}. "
        + "These Yahoo overview fields can have different reporting bases; consult filings for period alignment.",
        "## 4. Balance Sheet / Liquidity\n"
        + f"Reported cash: {number(cash)} {financial_currency}. Reported debt: {number(debt)} {financial_currency}. "
        + f"Current ratio: {number(info.get('currentRatio'))}. "
        + f"Annual balance sheet fiscal dates: {statements}. "
        + "Annual statement values and overview metrics may refer to different periods; they are not combined into new ratios.",
        "## 5. Valuation or Market Context\n"
        + f"Latest available daily close: {number(price.get('close'))} {price.get('currency') or 'currency unavailable'}, "
        + f"dated {price.get('price_date') or 'Unavailable'}; not a live executable quote. "
        + f"Market capitalization: {number(info.get('marketCap'))} {market_currency}. "
        + f"Trailing P/E: {number(info.get('trailingPE'))}; forward P/E: {number(info.get('forwardPE'))}. "
        + f"Annualized daily-return volatility over the retrieved history: {percent(history.get('annualized_daily_return_volatility'))}. "
        + "P/E alone does not establish whether a stock is cheap or expensive; no peer benchmark is provided.",
        "## 6. Key Risks\n" + "\n".join("- " + value for value in risks),
        "## 7. Positive Signals\n" + "\n".join("- " + value for value in positives or ["No positive signal established from available fields."]),
        "## 8. Final Analyst Summary\n" + (synthesis or "AI synthesis unavailable. Use the source-backed facts above and verify with original filings.")
        + "\nEducational decision support only; not investment advice or an underwriting decision.",
    ])
