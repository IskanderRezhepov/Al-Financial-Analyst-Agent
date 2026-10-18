import { useEffect, useState } from 'react'
import { C1Chat, ThemeProvider } from '@thesysai/genui-sdk'
import '@crayonai/react-ui/styles/index.css'
import './App.css'

type Datum = Record<string, unknown>
type Evidence = { source: string; retrieved_at_utc: string; data: Datum }
type Report = {
  ticker: string; generated_at_utc: string; provider: string; analysis: string;
  analysis_status: string; model_error: string | null; warnings: string[];
  snapshot: Record<string, Evidence>;
  tool_execution: { tool: string; status: string; source?: string }[];
  underwriting: { label: string; risk_indicators: string[]; positive_signals: string[];
    missing_data: string[]; suggested_human_review: boolean; review_reason: string;
    scope: string; thresholds: string } | null;
}
type Company = { symbol: string; shortname?: string; longname?: string; exchange: string }

const money = (value: unknown, currency: unknown) => {
  if (typeof value !== 'number') return 'Unavailable'
  return `${value.toLocaleString(undefined, { maximumFractionDigits: 2 })} ${typeof currency === 'string' ? currency : '(currency unavailable)'}`
}
const metric = (value: unknown, percent = false) => typeof value === 'number'
  ? percent ? `${(value * 100).toFixed(2)}%` : value.toLocaleString(undefined, { maximumFractionDigits: 2 })
  : 'Unavailable'

function AnalysisText({ text }: { text: string }) {
  // Render model output as text, never injected HTML or executable markup.
  return <div className="analysis-text">{text.split('\n').map((line, i) =>
    /^#{1,4}\s/.test(line) || /^\d\.\s/.test(line)
      ? <h3 key={i}>{line.replace(/^#+\s*/, '').replaceAll('**', '')}</h3>
      : <p key={i}>{line.replaceAll('**', '') || '\u00a0'}</p>)}</div>
}

async function responseJSON(response: Response) {
  const data = await response.json()
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Request rejected. Check the input and retry.')
  return data
}

function App() {
  const [health, setHealth] = useState<{ provider: string; model: string } | null>(null)
  const [ticker, setTicker] = useState('AAPL')
  const [focus, setFocus] = useState('Explain financial health and key business risks.')
  const [underwriting, setUnderwriting] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [report, setReport] = useState<Report | null>(null)
  const [matches, setMatches] = useState<Company[]>([])
  const [tab, setTab] = useState('report')
  useEffect(() => {
    fetch('/api/health').then(responseJSON).then(setHealth)
      .catch(() => setError('Backend is unavailable. Start it on port 8888, then refresh this page.'))
  }, [])

  async function search() {
    setError(''); setMatches([]); setBusy(true)
    try {
      const data = await responseJSON(await fetch(`/api/companies?q=${encodeURIComponent(ticker)}`))
      setMatches(data.matches)
      if (!data.matches.length) setError('No listed companies found. Enter an exact ticker or another company name.')
    } catch (err) { setError(err instanceof Error ? err.message : 'Company lookup failed.') }
    finally { setBusy(false) }
  }

  async function run() {
    setError(''); setReport(null); setBusy(true)
    try {
      const data = await responseJSON(await fetch('/api/analyze', { method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker, request: focus, include_underwriting: underwriting }) }))
      setReport(data)
    } catch (err) { setError(err instanceof Error ? err.message : 'Analysis failed. Check the backend and retry.') }
    finally { setBusy(false) }
  }

  function download() {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `${report?.ticker}-analysis.json`; a.click()
    URL.revokeObjectURL(url)
  }

  const overview = report?.snapshot.overview?.data || {}
  const price = report?.snapshot.price?.data || {}
  const periods = report?.snapshot.balance_sheet?.data.annual_periods as Record<string, Datum> | undefined
  const news = report?.snapshot.news?.data as unknown as { title: string; url?: string; published?: string }[] | undefined
  const safeLink = (url: string) => /^https:\/\//i.test(url)

  return <div className="shell">
    <header><div className="brand-icon">FA</div><div><span className="eyebrow">AGENTIC FINANCE · COURSE PROJECT</span>
      <h1>AI Financial Analyst Agent</h1></div><span className="provider">{health ? `${health.provider} · ${health.model}` : 'Connecting…'}</span></header>
    <nav><button className={tab === 'report' ? 'selected' : ''} onClick={() => setTab('report')}>Financial analysis</button>
      {health?.provider === 'thesys' && <button className={tab === 'chat' ? 'selected' : ''} onClick={() => setTab('chat')}>Tutorial · C1 dynamic chat</button>}</nav>
    {tab === 'chat' ? <div className="chat"><ThemeProvider mode="dark"><C1Chat apiUrl="/api/chat" /></ThemeProvider></div> : <>
      <div className="intro"><h2>From company data to a clear financial view.</h2>
        <p>Yahoo Finance evidence, an AI interpretation, and transparent risk flags for human review.</p></div>
      <div className="layout"><aside className="panel input-panel"><h2>New analysis</h2>
        <form onSubmit={event => { event.preventDefault(); void run() }}>
          <label htmlFor="ticker">Company / ticker</label><input id="ticker" value={ticker} maxLength={100}
            onChange={e => { setTicker(e.target.value); setMatches([]) }} placeholder="AAPL, MSFT or a company name" required />
          <button type="button" className="secondary" onClick={() => void search()} disabled={busy || !ticker.trim()}>Find company ticker</button>
          {matches.length > 0 && <div className="matches">{matches.map(company => <button type="button" key={company.symbol}
            onClick={() => { setTicker(company.symbol); setMatches([]) }}><strong>{company.symbol}</strong> · {company.longname || company.shortname} ({company.exchange})</button>)}</div>}
          <p className="hint">For a company name, find and select its ticker first.</p>
          <label htmlFor="focus">Analysis focus</label><textarea id="focus" value={focus} onChange={e => setFocus(e.target.value)} maxLength={1000} rows={4} />
          <label className="check"><input type="checkbox" checked={underwriting} onChange={e => setUnderwriting(e.target.checked)} /> Include demo underwriting support</label>
          <button className="primary" disabled={busy || !ticker.trim()} type="submit">{busy ? 'Working…' : 'Run Analysis'}</button>
        </form>
        <div className="workflow"><span>WORKFLOW</span><ol><li>Retrieve Yahoo Finance data</li><li>Run the financial analyst agent</li><li>Produce a structured report</li><li>Flag items for human review</li></ol></div>
        <p className="hint">Educational use only. Not financial advice or production underwriting.</p>
      </aside><main aria-live="polite" aria-busy={busy}>
        {error && <div className="error" role="alert">{error}</div>}
        {busy && <div className="panel loading"><div className="spinner" /><h2>Collecting evidence and preparing analysis</h2><p>Yahoo tools run first; local model generation may take several minutes.</p></div>}
        {!report && !busy && <div className="panel empty"><span className="empty-icon">↗</span><h2>Your company research starts here</h2>
          <p>Enter a ticker and run an analysis. The report includes dated financial metrics, source records, and an AI interpretation.</p>
          <div className="tags"><span>Company overview</span><span>Financial metrics</span><span>Risk indicators</span></div></div>}
        {report && <>
          <section className="panel report-header"><div><span className="eyebrow">FINANCIAL RESEARCH REPORT</span><h2>{String(overview.longName || overview.shortName || report.ticker)} <small>{report.ticker}</small></h2>
            <p>Retrieved {new Date(report.generated_at_utc).toLocaleString()} · {report.provider} · AI report {report.analysis_status}</p></div>
            <button className="secondary" onClick={download}>Download evidence + report</button></section>
          {report.model_error && <div className="error" role="alert">{report.model_error}</div>}
          {report.warnings.length > 0 && <div className="notice">{report.warnings.map(w => <p key={w}>{w}</p>)}</div>}
          <section className="metrics">
            <div><span>Latest daily close</span><strong>{money(price.close, price.currency)}</strong><small>{typeof price.price_date === 'string' ? price.price_date.slice(0, 10) : 'Date unavailable'}</small></div>
            <div><span>Revenue · trailing</span><strong>{money(overview.totalRevenue, overview.financialCurrency)}</strong><small>Yahoo reported totalRevenue</small></div>
            <div><span>Profit margin</span><strong>{metric(overview.profitMargins, true)}</strong><small>Reported ratio</small></div>
            <div><span>Current ratio</span><strong>{metric(overview.currentRatio)}</strong><small>Reported ratio</small></div>
          </section>
          <section className="panel"><h2>Verified source metrics</h2><p className="hint">Latest available close, not a live executable quote. Financial statement and market currencies can differ. Ratios and periods may be unavailable or lag filings.</p>
            <dl className="facts"><dt>Sector / industry</dt><dd>{String(overview.sector || 'Unavailable')} / {String(overview.industry || 'Unavailable')}</dd>
              <dt>Revenue growth</dt><dd>{metric(overview.revenueGrowth, true)} (Yahoo growth field)</dd>
              <dt>Operating margin</dt><dd>{metric(overview.operatingMargins, true)}</dd>
              <dt>Cash / debt</dt><dd>{money(overview.totalCash, overview.financialCurrency)} / {money(overview.totalDebt, overview.financialCurrency)}</dd>
              <dt>Market capitalization</dt><dd>{money(overview.marketCap, overview.currency)}</dd>
              <dt>Trailing P/E / beta</dt><dd>{metric(overview.trailingPE)} / {metric(overview.beta)}</dd>
              <dt>Most recent quarter / fiscal year end</dt><dd>{String(overview.mostRecentQuarter || 'Unavailable')} / {String(overview.lastFiscalYearEnd || 'Unavailable')}</dd>
              <dt>90-day annualized return volatility</dt><dd>{metric(report.snapshot.history?.data.annualized_daily_return_volatility, true)}</dd></dl>
            {periods && <details><summary>Annual balance sheets · fiscal dates and reported line items</summary><pre>{JSON.stringify({ currency: report.snapshot.balance_sheet?.data.financial_currency, periods }, null, 2)}</pre></details>}
          </section>
          <section className="panel"><h2>Financial analyst interpretation</h2><p className="hint">Financial facts come directly from tool results. The AI prioritizes validated source-backed signals for the final summary.</p>
            {report.analysis ? <AnalysisText text={report.analysis} /> : <p>AI interpretation unavailable. Verified source data remains available above.</p>}</section>
          {report.underwriting && <section className="panel"><span className="eyebrow">OPTIONAL ACADEMIC EXTENSION</span><h2>Demo underwriting support</h2>
            <p>{report.underwriting.label}</p><strong className="review">{report.underwriting.suggested_human_review ? 'Suggested human review: Yes' : 'No demo threshold triggered; human decision still required'}</strong>
            <h3>Risk indicators</h3>{report.underwriting.risk_indicators.length ? <ul>{report.underwriting.risk_indicators.map(v => <li key={v}>{v}</li>)}</ul> : <p>No demo threshold triggered in available data.</p>}
            <h3>Positive signals</h3>{report.underwriting.positive_signals.length ? <ul>{report.underwriting.positive_signals.map(v => <li key={v}>{v}</li>)}</ul> : <p>No signal established from available fields.</p>}
            {report.underwriting.missing_data.length > 0 && <p>Unavailable: {report.underwriting.missing_data.join(', ')}</p>}
            <p className="hint">{report.underwriting.thresholds}</p><p className="hint">{report.underwriting.scope}</p></section>}
          <section className="panel"><h2>Sources & tool execution</h2><ul className="tool-list">{report.tool_execution.map((call, i) => <li key={i}><code>{call.tool}</code><span>{call.status}</span>{call.source && <a href={call.source} target="_blank" rel="noreferrer">Yahoo source ↗</a>}</li>)}</ul>
            <p className="hint">Retrieval timestamps and complete tool responses are included in the downloadable JSON. Source data is not independently audited.</p>
            <h3>Recent source news</h3>{news?.length ? <ul>{news.map((item, i) => <li key={i}>{item.url && safeLink(item.url) ? <a href={item.url} target="_blank" rel="noreferrer">{item.title}</a> : item.title}<small> {item.published}</small></li>)}</ul> : <p>News unavailable from Yahoo Finance.</p>}
          </section>
        </>}
      </main></div>
    </>}
    <footer>Based on NeuralNine’s assigned tutorial · Yahoo Finance via yfinance · Academic decision support</footer>
  </div>
}

export default App
