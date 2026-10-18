# Verification results

Verified on **19 October 2026, Europe/Berlin**, on this Windows project. The selected example JSON
files include their exact UTC retrieval timestamps and source URLs. These are dated captures, not promises
about future prices. No financial API responses were mocked in the live or browser checks.

| Check | Result |
| --- | --- |
| Python / Node | Python 3.13.2; Node 24.13.0 |
| `pip check` | No broken requirements |
| Offline tests | 8 passed: ticker validation, missing-data review flags, rule flags, JSON missing values, safe source/model errors, evidence preservation, local C1 route separation |
| Frontend production build | Passed; tutorial C1 stack produces a large bundle |
| Frontend ESLint | Passed |
| AAPL live analysis | Passed: actual daily close, overview, annual statements, history, validated AI summary and eight-section report |
| MSFT live analysis | Passed with the same workflow |
| Company lookup | Yahoo search for Microsoft returned MSFT and other listed share classes/markets |
| Invalid input | `NOT A TICKER!` returned HTTP 422 |
| Nonexistent ticker | `ZZZZZZZZZZ` returned a safe HTTP 502; no normal-flow traceback |
| Real Edge browser | Passed: actual AAPL submission, loading state, complete report, JSON download, safe invalid-input screen |
| Browser runtime errors | None observed |
| Mobile layout | 390px viewport; no horizontal page overflow |
| Proof screenshots | Eight PNG files in `screenshots/`; visually inspected input, report, source/tool and mobile captures |
| Git / secret exclusions | `.env`, virtual environment, node_modules, logs, caches, runtime outputs and submission ZIP are ignored |

## Actual tool outcomes

Both live examples successfully executed `get_stock_price`, `get_company_overview`,
`get_balance_sheet` and `get_historical_stock_price`. `get_stock_news` executed but Yahoo returned
no news records. The report explicitly marks that unavailable and draws no conclusion about absent events.

The model selects evidence-supported qualitative signal IDs, which the backend validates before rendering.
All reported numbers, periods and currencies are formatted directly from tool data.
Offline fixtures are synthetic only for failure-path tests; they are not used in example evidence or screenshots.

## Resolved local issues

- The project's Cyrillic directory path caused curl error 77 when opening its public CA bundle.
  The app now copies that bundle to a process-specific temporary ASCII path and keeps TLS verification enabled.
- Ollama was installed but its server was stopped. The existing installed server was started locally;
  no model download, system installation or payment was required.
- Python was installed but not on this shell's PATH. Setup commands use its actual executable and project venv.
- Dependency resolution was aligned with the tutorial's Python lockfile. Unused packages from the initial
  install were removed from this project's environment; `pip check` passes.
- `SSLKEYLOGFILE` was absent; no environment or system changes were needed for it.

## Remaining scope and limitations

- **Thesys C1 authenticated generation is untested.** The original route, packages, endpoint and model ID
  are preserved. No Thesys key was supplied and no paid request was made. Its current availability is unverified.
- Yahoo news was unavailable for both tested tickers. Yahoo data remains unofficial, potentially delayed,
  incomplete and subject to rate limits. Example values must be read with their timestamps.
- `npm audit`: **10 remaining findings: 6 low, 4 moderate; 0 high, 0 critical** after compatible fixes.
  Remaining findings are in the preserved tutorial UI dependency chain; no forced major/downgrade fix was applied.
  The original tutorial frontend lockfile is preserved separately for comparison.
- Academic decision support only. No underwriting eligibility, pricing, bind, fraud, or regulated advice is produced.
- Screenshots and example reports demonstrate the completed local adaptation. If the class requires the exact
  paid C1-generated UI, a separate manually configured Thesys demonstration is still required.

The local project and `submission.zip` are prepared for review/submission. Moodle upload, rubric acceptance,
student identity details and deadlines have not been verified or submitted automatically.
