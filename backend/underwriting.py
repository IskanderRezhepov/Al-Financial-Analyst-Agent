"""Transparent academic flags, never eligibility, pricing or bind decisions."""


def underwriting_support(overview: dict, history: dict | None) -> dict:
    flags, positives, missing = [], [], []
    ratio = overview.get("currentRatio")
    if ratio is None:
        missing.append("Current ratio")
    elif ratio < 1:
        flags.append("Current ratio below 1: investigate short-term liquidity in sector context.")
    else:
        positives.append("Reported current ratio is at least 1; this alone does not establish financial strength.")
    cash, debt = overview.get("totalCash"), overview.get("totalDebt")
    if cash is None or debt is None:
        missing.append("Cash/debt comparison")
    elif debt > cash:
        flags.append("Reported debt exceeds cash: review maturities, cash generation and covenants.")
    else:
        positives.append("Reported cash covers reported debt at this snapshot.")
    margin = overview.get("profitMargins")
    if margin is None:
        missing.append("Profit margin")
    elif margin < 0:
        flags.append("Negative reported profit margin: review sustainability and one-off items.")
    volatility = (history or {}).get("annualized_daily_return_volatility")
    if volatility is None:
        missing.append("Historical volatility")
    elif volatility > 0.40:
        flags.append("Annualized daily-return volatility exceeds the demo threshold of 40%.")
    return {
        "label": "Academic/demo decision-support layer — not regulated underwriting advice",
        "risk_indicators": flags, "positive_signals": positives, "missing_data": missing,
        "suggested_human_review": bool(flags or missing),
        "review_reason": "Review the listed flags/missing data; all actual decisions require an authorized human.",
        "scope": "No eligibility, risk score, premium, terms, appetite/capacity or bind decision is calculated. "
                 "Fraud cannot be inferred from market prices or these financial ratios.",
        "thresholds": "Illustrative, uncalibrated rules: current ratio <1; debt >cash; profit margin <0; "
                      "annualized volatility >40%. Sector differences are not modeled.",
    }

