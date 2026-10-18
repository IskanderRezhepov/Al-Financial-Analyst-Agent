"""Offline failure-path and decision-support tests; no fabricated demo outputs."""
import os
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from backend import agent
from backend.main import app
from backend.tools import DataUnavailable, clean, ticker_symbol
from backend.underwriting import underwriting_support


class WorkflowTests(unittest.TestCase):
    def test_ticker_validation_blocks_request_text(self):
        self.assertEqual(ticker_symbol(" aapl "), "AAPL")
        self.assertEqual(ticker_symbol("SAP.DE"), "SAP.DE")
        for value in ("", "Apple Inc", "<script>", "../../.env"):
            with self.assertRaises(ValueError):
                ticker_symbol(value)

    def test_missing_data_requires_human_review(self):
        report = underwriting_support({}, None)
        self.assertTrue(report["suggested_human_review"])
        self.assertTrue(report["missing_data"])
        self.assertEqual(report["positive_signals"], [])

    def test_flags_use_only_available_metrics(self):
        report = underwriting_support({"currentRatio": 0.6, "totalCash": 10,
            "totalDebt": 30, "profitMargins": -0.1}, {"annualized_daily_return_volatility": 0.5})
        self.assertEqual(len(report["risk_indicators"]), 4)
        self.assertTrue(report["suggested_human_review"])
        self.assertEqual(report["missing_data"], [])

    def test_nan_never_becomes_a_json_number(self):
        self.assertEqual(clean({"unknown": float("nan"), "infinite": float("inf")}),
                         {"unknown": None, "infinite": None})

    def test_market_data_failure_is_safe_http_error(self):
        with patch("backend.main.run_analysis", side_effect=DataUnavailable("Yahoo data unavailable")):
            response = TestClient(app).post("/api/analyze", json={"ticker": "ZZZZZZZZ"})
        self.assertEqual(response.status_code, 502)
        self.assertIn("unavailable", response.json()["detail"])

    def test_unexpected_errors_do_not_expose_secrets(self):
        with patch("backend.main.run_analysis", side_effect=RuntimeError("secret-key-must-not-leak")):
            response = TestClient(app).post("/api/analyze", json={"ticker": "AAPL"})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret-key", response.text)

    def test_failed_model_keeps_actual_tool_evidence(self):
        # Synthetic fixtures test control flow only; never published as market evidence.
        evidence = {"source": "https://finance.yahoo.com/", "data": {"close": 1}}
        def fake_tool(name, result=None, failure=None):
            value = Mock()
            value.name = name
            value.invoke.return_value = result
            value.invoke.side_effect = failure
            return value
        with patch.object(agent, "get_stock_price", fake_tool("get_stock_price", evidence)), \
             patch.object(agent, "get_company_overview", fake_tool("get_company_overview", {**evidence, "data": {}})), \
             patch.object(agent, "get_balance_sheet", fake_tool("get_balance_sheet", {**evidence, "data": {"annual_periods": {}}})), \
             patch.object(agent, "get_stock_news", fake_tool("get_stock_news", {**evidence, "data": []})), \
             patch.object(agent, "get_historical_stock_price", fake_tool("get_historical_stock_price", failure=RuntimeError())), \
             patch.object(agent, "build_agent", side_effect=RuntimeError("secret-value")), \
             patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}):
            report = agent.run_analysis("AAPL")
        self.assertEqual(report["snapshot"]["price"]["data"]["close"], 1)
        self.assertEqual(report["analysis_status"], "unavailable")
        self.assertNotIn("secret-value", report["model_error"])
        self.assertIn("AI synthesis unavailable", report["analysis"])

    def test_c1_route_is_explicitly_disabled_for_local_mode(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}):
            response = TestClient(app).post("/api/chat", json={"prompt": {
                "content": "Analyze AAPL", "id": "one", "role": "user"},
                "threadId": "test", "responseId": "two"})
        self.assertEqual(response.status_code, 409)


if __name__ == "__main__":
    unittest.main()
