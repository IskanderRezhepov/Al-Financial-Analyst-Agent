"""Real Yahoo + local model check; saves dated, unmodified evidence locally."""
import json
from pathlib import Path
import sys

import httpx


def main():
    target = Path("outputs")
    target.mkdir(exist_ok=True)
    with httpx.Client(base_url="http://127.0.0.1:8888", timeout=600) as client:
        print("Health:", client.get("/api/health").json(), flush=True)
        for ticker in sys.argv[1:] or ["AAPL", "MSFT"]:
            response = client.post("/api/analyze", json={"ticker": ticker,
                "request": "Summarize financial health from retrieved evidence. Do not invent information."})
            result = response.json()
            (target / f"{ticker}-analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
            assert response.status_code == 200, result
            assert result["snapshot"]["price"]["data"]["close"] > 0
            assert result["analysis_status"] == "complete", result.get("model_error")
            assert result["analysis"].strip()
            print(ticker, "SUCCESS", result["snapshot"]["price"]["data"], flush=True)
            print("Tools:", [(t["tool"], t["status"]) for t in result["tool_execution"]], flush=True)
            print("Warnings:", result["warnings"], flush=True)
        invalid = client.post("/api/analyze", json={"ticker": "NOT A TICKER!"})
        assert invalid.status_code == 422
        nonexistent = client.post("/api/analyze", json={"ticker": "ZZZZZZZZZZ"})
        assert nonexistent.status_code == 502
        assert "Traceback" not in nonexistent.text
        print("Invalid and nonexistent tickers: safe errors PASS", flush=True)
        names = client.get("/api/companies", params={"q": "Microsoft"})
        print("Company name lookup:", names.status_code, names.json(), flush=True)


if __name__ == "__main__":
    main()
