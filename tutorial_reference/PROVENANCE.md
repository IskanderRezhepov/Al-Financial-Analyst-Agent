# Tutorial provenance

Assigned video: [Advanced AI Stock Analysis Assistant in Python — NeuralNine](https://youtu.be/AE_6F8cuXsA).

The YouTube HTML metadata and description were retrieved on 19 October 2026 (Europe/Berlin).
The description explicitly links to [this source folder](https://github.com/NeuralNine/youtube-tutorials/tree/main/AI%20Stock%20Analysis%20Assistant).
The implementation is based on that linked repository, not an unrelated financial-agent tutorial.
No full video transcript was used or claimed. The video metadata lists environment setup,
backend/agent, frontend, and agent finance tools as its chapters.

`backend/` and `frontend/` in this reference directory contain the original downloaded source,
configuration and dependency locks. Starter logo assets and empty README files were omitted.
These files are reference material; run the adapted root `backend/` and `frontend/` instead.
`SHA256SUMS.txt` records the downloaded reference bytes.

## Directly reproduced

- Python >=3.12 (tutorial `.python-version`: 3.12; local verification: 3.13.2).
- FastAPI/Uvicorn backend on 8888, React/TypeScript/Vite frontend on 3000, `/api` proxy.
- `langchain.agents.create_agent`, LangChain tool decorators, `ChatOpenAI` and
  `langgraph.checkpoint.memory.InMemorySaver` keyed by `threadId`.
- Thesys endpoint `https://api.thesys.dev/v1/embed/` and model `c1/openai/gpt-5/v-20250930`.
- `get_stock_price`, `get_historical_stock_price`, `get_balance_sheet`, `get_stock_news`, all using yfinance/Yahoo.
- `/api/chat` request fields `prompt`, `threadId`, `responseId`; raw model token streaming.
- `C1Chat`, `ThemeProvider`, `@thesysai/genui-sdk`, `@crayonai/react-ui` and its styles.

## Assignment additions / adaptations (not claimed to be in the video)

- Local Ollama uses the same ChatOpenAI integration through Ollama's compatible local API.
  Its plain-text report screen replaces C1 only in local mode; C1 requires the proprietary service.
- Company search and overview metrics, mandatory evidence prefetch, eight-section report instructions,
  dated/currency-labeled records, optional demo underwriting flags, downloads and safe errors.
  Model summary selections are validated against an evidence-derived signal catalogue rather than
  displaying unverified numeric or qualitative financial claims from the local model.
- JSON-safe/bounded tool results, historical date-range validation, loopback binding, lazy model creation,
  and a public-certificate temporary-copy workaround for libcurl's Windows Unicode-path error.
- Python dependencies are pinned to the linked tutorial's lockfile. The frontend starts from the
  original lockfile, with Playwright added for validation and compatible npm security updates applied.
- Tests, screenshots, submission packaging and documentation.

The Thesys model identifier and route are preserved from source. Their current availability and
successful authenticated generation have not been verified without a user-provided Thesys key.
