# AI Financial Analyst Agent

## Assignment

This homework follows NeuralNine's [Advanced AI Stock Analysis Assistant in Python](https://youtu.be/AE_6F8cuXsA).
The video description links to the [original backend/frontend source](https://github.com/NeuralNine/youtube-tutorials/tree/main/AI%20Stock%20Analysis%20Assistant).
The implementation was reproduced from that linked code and the video's metadata; a full transcript was not used.
Original downloaded files and a precise comparison are in [tutorial_reference/PROVENANCE.md](tutorial_reference/PROVENANCE.md).

The repo originally contained only a one-line README, so the tutorial's `backend/` and `frontend/` layout is used directly.

## Features

- Exact ticker input, or company-name search with explicit ticker selection.
- Yahoo Finance daily close, historical prices, annual balance sheets and company news tools.
- Additional company overview, revenue, profitability, liquidity, valuation and volatility metrics.
- Eight-section report with facts formatted directly from returned data and an AI-prioritized, validated qualitative summary.
- Dated source evidence, currency labels, visible tool outcomes and JSON report download.
- Optional academic underwriting support with transparent liquidity, debt, profitability and volatility flags.
- Local/free Ollama mode, plus the tutorial-compatible Thesys C1 dynamic chat mode.
- Loading states and safe invalid-input, missing-data and model-unavailable handling.

## Architecture

```text
User request (React / TypeScript / Vite, port 3000)
  → FastAPI backend (port 8888)
  → Yahoo Finance tools (yfinance)
  → LangChain create_agent + ChatOpenAI + LangGraph InMemorySaver
  → Source-backed structured report + qualitative model summary
  → Optional academic underwriting flags / human review
```

The original C1 path remains `C1Chat → /api/chat → agent.stream → Thesys C1 → generated UI`.
Vite proxies `/api` to the backend. Local mode uses `/api/analyze` and a simple React report screen;
Ollama does not reproduce the proprietary C1 UI format.
The analyst explicitly collects the tutorial tools before synthesis, with actual tool-call messages
passed into the agent. The model can request further tool calls. C1 chat uses model-selected tools.
The report's financial quantities and dates come from tool values, not model arithmetic.
For the summary, the agent chooses supported signal IDs in priority order. Its choices are validated
against the available evidence; only the corresponding source-backed sentences are rendered.
Unsupported model claims are never used as financial facts.
Memory is process-local and disappears when the backend restarts; independent reports use separate threads.

```text
backend/                 main.py, agent.py, tools.py, config.py, reporting.py, underwriting.py
frontend/                tutorial React/Vite stack + local report screen
tutorial_reference/      original downloaded code and locks; provenance/checksums
tests/                   offline, real API and real browser checks
screenshots/             captured proof from the running local application
evidence/                dated public-source example reports and verification results
.env.example             placeholders only
requirements.txt         tutorial direct package pins + tutorial constraints
requirements-lock.txt    full tested Python environment
start.ps1                starts the two local servers in the background
SUBMISSION_CHECKLIST.md  Moodle packaging and screenshot instructions
```

## Setup

Prerequisites: Windows PowerShell, Python 3.12 or 3.13, Node.js 22.12+ (tested with 24.13.0),
and Ollama with a tool-capable model. Tested here with Python 3.13.2 and the already installed `qwen3:4b-instruct`.
No paid API or API key is required for local mode. Yahoo access still needs internet.

From the project root:

```powershell
# Python is not on PATH on the tested machine, so use its installed path:
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
npm.cmd ci --prefix frontend
Copy-Item .env.example .env
```

If your Python is elsewhere, use its path or `py -3.13 -m venv .venv` instead of the first command.
The existing `.venv` is already installed on this machine; do not recreate it just to run the app.
To reproduce the original dependency selection rather than the tested freeze, use
`python -m pip install -r requirements.txt` inside the venv. Its constraints come from the tutorial's `uv.lock`.
The frontend original lock is preserved under `tutorial_reference/`; the active lock includes compatible
security updates and Playwright for testing.

Start Ollama from its installed application, or in a separate PowerShell terminal:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve
```

If already running, use the existing server. In another terminal you can check installed models:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" list
```

Set `OLLAMA_MODEL` to an installed tool-capable model. Downloading another model is optional and was not required here.

## Environment Variables

Copy `.env.example` to `.env` and edit locally. Never commit `.env` or supply a key in chat/browser code.

| Variable | Default / meaning |
| --- | --- |
| `LLM_PROVIDER` | `ollama`; select `thesys` for the original paid service path |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434/v1` |
| `OLLAMA_MODEL` | `qwen3:4b-instruct`; must already be installed |
| `OPENAI_API_KEY` | Empty locally. In Thesys mode, enter **your Thesys key** here; the tutorial uses this variable through ChatOpenAI. A normal OpenAI key is not a Thesys key. |
| `THESYS_BASE_URL` | `https://api.thesys.dev/v1/embed/` from the tutorial |
| `THESYS_MODEL` | `c1/openai/gpt-5/v-20250930` from the tutorial; provider availability may change |
| `LLM_TIMEOUT_SECONDS` | `240`; per model request, local hardware dependent |

Yahoo Finance requires no API key. The tutorial uses no DuckDuckGo, Tavily, SEC, Alpha Vantage or other separate search/data service.
Restart the backend after editing `.env`. Thesys mode reveals the **Tutorial · C1 dynamic chat** tab.
That authenticated cloud path has not been tested because no Thesys key was supplied. Do not purchase
anything to use the local fallback.

## Run

With Ollama running, execute from the repo root:

```powershell
.\start.ps1
```

Open **http://127.0.0.1:3000**. If the two servers are already running, just open that address.
The start script refuses to start duplicate servers on occupied ports. It prints process IDs and logs locally.
For foreground terminals with straightforward Ctrl+C stopping, run these in two terminals instead:

```powershell
# Terminal 1, project root
.\.venv\Scripts\python.exe -m backend.main
```

```powershell
# Terminal 2, project root
npm.cmd run dev --prefix frontend
```

If PowerShell blocks local scripts, use those foreground commands; no system execution-policy change is required.
Backend health: `http://127.0.0.1:8888/api/health`; API documentation: `http://127.0.0.1:8888/docs`.

## Example

Enter `AAPL` and click **Run Analysis**. The five evidence calls retrieve the latest available daily close,
company metrics, annual statements, news, and a ninety-day history window. The analyst creates:

1. Company Overview
2. Revenue / Growth
3. Profitability
4. Balance Sheet / Liquidity
5. Valuation or Market Context
6. Key Risks
7. Positive Signals
8. Final Analyst Summary

Use **Find company ticker** for `Microsoft`, select `MSFT`, and run a second report.
The optional underwriting section shows illustrative flags and suggested human review. A current ratio below
one, debt above cash, negative profit margin, or annualized daily-return volatility above forty percent triggers
a flag. Missing required inputs also suggest review. These are uncalibrated classroom rules, not an approval score.
No eligibility, appetite/capacity, premium, terms, fraud, authority or bind decision is made.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
npm.cmd run build --prefix frontend
npm.cmd run lint --prefix frontend
# Requires the running backend, Ollama and Yahoo internet access:
.\.venv\Scripts\python.exe tests/live_smoke.py AAPL MSFT
# Uses an installed Microsoft Edge for real UI interaction and screenshots:
node tests/browser_smoke.mjs
```

See [evidence/TEST_RESULTS.md](evidence/TEST_RESULTS.md) for actual results and limitations.
Live outputs are saved under ignored `outputs/`; selected dated public examples are included under `evidence/`.
Offline tests use synthetic fixtures solely for control-flow assertions; they are never displayed as financial data.

## Limitations

- Educational demonstration; not financial advice, investment recommendations or production underwriting.
- Yahoo is an unofficial secondary data source and may rate-limit, omit news/metrics, or change APIs.
  Missing data remains unavailable. Latest daily close may be delayed or from the preceding trading day.
- Yahoo overview fields can have different period bases. The growth comparison period is not supplied here;
  annual balance sheets are labeled separately and are not combined with overview fields to derive ratios.
- Financial statements, quote currency and fiscal dates can differ. Confirm material claims against filings.
- The language model prioritizes validated qualitative signals and may prioritize them poorly. The rule-based
  signals are deliberately limited and omit sector calibration. Human review is required.
- Thesys C1 requires a manually supplied key and potentially paid usage. Its original model identifier is retained
  but authenticated generation and current availability are unverified. Local mode uses a conventional report UI.
- The preserved tutorial UI stack has remaining low/moderate npm dependency advisories. Compatible fixes were
  applied; no forced major-version changes were made. Use locally for the assignment, not as a production deployment.
- The original C1 SDK creates a large frontend bundle. Both servers bind only to loopback; there is no multi-user
  authentication or production persistence.
- Windows Unicode project paths required a libcurl certificate-path workaround. Only the public CA bundle is
  copied to a process-specific temp directory; TLS verification stays on. No system settings are changed.
- `SSLKEYLOGFILE` was inspected and was absent; no related environment changes were made.

## Tutorial

Video: https://youtu.be/AE_6F8cuXsA

Source: https://github.com/NeuralNine/youtube-tutorials/tree/main/AI%20Stock%20Analysis%20Assistant

See [tutorial_reference/PROVENANCE.md](tutorial_reference/PROVENANCE.md) for what is tutorial-derived and what was added for this assignment.
