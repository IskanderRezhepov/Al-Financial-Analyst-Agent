// Real UI -> real backend -> Yahoo + Ollama. No mocked financial responses.
import { chromium } from '../frontend/node_modules/playwright/index.mjs'
import { mkdir, writeFile } from 'node:fs/promises'
import assert from 'node:assert/strict'

await mkdir('screenshots', { recursive: true })
await mkdir('outputs', { recursive: true })
const browser = await chromium.launch({ channel: 'msedge', headless: true })
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
const errors = []
page.on('pageerror', error => errors.push(error.message))
try {
  await page.goto('http://127.0.0.1:3000', { waitUntil: 'networkidle' })
  await page.getByText(/ollama ·/).waitFor()
  await page.screenshot({ path: 'screenshots/01-input.png', fullPage: true })
  await page.getByLabel('Company / ticker').fill('AAPL')
  const pending = page.waitForResponse(response => response.url().endsWith('/api/analyze'), { timeout: 600000 })
  await page.getByRole('button', { name: 'Run Analysis', exact: true }).click()
  await page.getByText('Collecting evidence and preparing analysis').waitFor()
  await page.screenshot({ path: 'screenshots/02-running.png', fullPage: true })
  const response = await pending
  assert.equal(response.status(), 200)
  const result = await response.json()
  await writeFile('outputs/AAPL-browser-analysis.json', JSON.stringify(result, null, 2))
  assert.equal(result.analysis_status, 'complete', result.model_error)
  await page.getByRole('heading', { name: 'Verified source metrics' }).waitFor()
  await page.screenshot({ path: 'screenshots/03-analysis.png', fullPage: true })
  await page.getByRole('heading', { name: 'Financial analyst interpretation' }).scrollIntoViewIfNeeded()
  await page.screenshot({ path: 'screenshots/04-structured-report.png' })
  await page.getByRole('heading', { name: 'Sources & tool execution' }).scrollIntoViewIfNeeded()
  await page.screenshot({ path: 'screenshots/05-tools-and-sources.png' })
  await page.getByRole('heading', { name: 'Demo underwriting support' }).scrollIntoViewIfNeeded()
  await page.screenshot({ path: 'screenshots/06-underwriting.png' })
  const downloadPending = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Download evidence + report' }).click()
  const download = await downloadPending
  assert.equal(download.suggestedFilename(), 'AAPL-analysis.json')
  await page.getByLabel('Company / ticker').fill('BAD INPUT!')
  await page.getByRole('button', { name: 'Run Analysis', exact: true }).click()
  await page.getByRole('alert').waitFor()
  await page.screenshot({ path: 'screenshots/07-invalid-input.png', fullPage: true })
  await page.setViewportSize({ width: 390, height: 844 })
  await page.screenshot({ path: 'screenshots/08-mobile.png', fullPage: true })
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth), false, 'Mobile overflows horizontally')
  assert.deepEqual(errors, [], 'Browser runtime errors')
  console.log(JSON.stringify({ status: 'PASS', ticker: result.ticker, analysis: result.analysis_status,
    tools: result.tool_execution, warnings: result.warnings, browserErrors: errors }, null, 2))
} finally {
  await browser.close()
}
