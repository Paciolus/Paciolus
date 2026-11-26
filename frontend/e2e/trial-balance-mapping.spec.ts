/**
 * Sprint 734: Playwright E2E coverage for the mapping-required handoff in the Trial Balance
 * upload flow. Sprint 900: runs against the real backend.
 *
 * Why this spec exists:
 * - When the backend cannot identify the Debit and Credit columns it answers with
 *   `column_detection.requires_mapping`; the page asks the user to map the columns and re-runs
 *   the audit with that mapping.
 * - The handoff is the most fragile path in the upload pipeline: a regression in the debounce
 *   dedup logic produces "recalc fires twice" symptoms that are invisible in unit tests but waste
 *   a real upload round-trip per user.
 *
 * What this spec asserts:
 *   1. Pre-flight runs and the user proceeds from its summary
 *   2. The mapping modal opens when the backend cannot identify the columns
 *   3. The user picks all three columns and submits
 *   4. After submission the upload runs exactly once more (no debounce duplicates)
 *   5. The modal closes and the page shows results, not an error
 *
 * Network strategy (Sprint 900):
 * - Every request reaches the real backend. POST /audit/trial-balance is only counted and
 *   inspected. The 2026-04 version mocked it with responses that had drifted from the real
 *   contract; it skipped in CI until Sprint 889 seeded an account, and the real responses
 *   then showed that the modal had not opened since Sprint 519 and that pre-flight and
 *   out-of-balance trial balances answered 500.
 * - A third upload would be a regression: it is answered 500 so the test fails clearly.
 */
import { test as base, expect, type Page, type Route } from '@playwright/test'

const SMOKE_USER = process.env.SMOKE_USER ?? ''
const SMOKE_PASS = process.env.SMOKE_PASS ?? ''

/**
 * Generic headers the backend cannot match, so it asks for a mapping. The unique account name
 * keeps a retry from being refused as an identical upload within 5 minutes (Sprint 872).
 */
function genericHeaderCsv(rows: string[]): Buffer {
  const unique = `Suspense ${Date.now()}-${Math.random().toString(36).slice(2, 8)},0,0`
  return Buffer.from(['Col A,Col B,Col C', ...rows, unique].join('\n'), 'utf-8')
}

async function login(page: Page) {
  await page.goto('/login')
  await page.fill('input[name="email"], input[type="email"]', SMOKE_USER)
  await page.fill('input[name="password"], input[type="password"]', SMOKE_PASS)
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard**', { timeout: 15000 })
}

/**
 * Log in once per worker and run every test in that one signed-in page. Login is limited to
 * 5 a minute per IP and the smoke spec logs in too, so one login per test (plus retries) went
 * over the limit in CI. Saved cookies cannot be shared between pages instead: the refresh
 * token rotates on use, so a second page starts with a revoked one (2026-11-25).
 */
const test = base.extend<{ page: Page }, { signedInPage: Page }>({
  signedInPage: [
    async ({ browser }, provide, workerInfo) => {
      const context = await browser.newContext({ baseURL: workerInfo.project.use.baseURL })
      const page = await context.newPage()
      await login(page)
      await provide(page)
      await context.close()
    },
    { scope: 'worker' },
  ],
  page: async ({ signedInPage }, provide) => {
    await provide(signedInPage)
    await signedInPage.unrouteAll({ behavior: 'ignoreErrors' })
  },
})

/**
 * Every upload runs the pre-flight check first (Sprint 283); the audit upload starts when
 * the user proceeds from the pre-flight summary.
 */
async function proceedPastPreflight(page: Page) {
  const proceed = page.getByRole('button', { name: /proceed to full analysis/i })
  await expect(proceed).toBeVisible({ timeout: 15000 })
  await proceed.click()
}

/** Count audit uploads, record whether each sent a column mapping, and pass them through. */
async function countUploads(page: Page, maxAllowed: number) {
  const uploads: { hadMapping: boolean }[] = []
  await page.route('**/audit/trial-balance', async (route: Route) => {
    // Form bodies are multipart/form-data; check whether the column_mapping field was sent.
    const hadMapping = (route.request().postData() ?? '').includes('column_mapping')
    uploads.push({ hadMapping })
    if (uploads.length > maxAllowed) {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: `regression: upload ${uploads.length}, expected at most ${maxAllowed}` }),
      })
      return
    }
    await route.continue()
  })
  return uploads
}

test.describe('Sprint 734 — Trial Balance mapping-required handoff', () => {
  test.skip(!SMOKE_USER || !SMOKE_PASS, 'SMOKE_USER and SMOKE_PASS env vars required')

  test('mapping modal renders, user submits mapping, second upload completes without debounce dupes', async ({
    page,
  }) => {
    const uploads = await countUploads(page, 2)

    await page.goto('/tools/trial-balance')
    await page.waitForLoadState('networkidle')

    const fileInput = page.locator('input[type="file"]')
    await expect(fileInput).toBeAttached({ timeout: 10000 })
    await fileInput.setInputFiles({
      name: 'mapping-required.csv',
      mimeType: 'text/csv',
      buffer: genericHeaderCsv(['Cash,50000,0', 'Revenue,0,51000', 'Expense,1000,0']),
    })

    await proceedPastPreflight(page)

    // Mapping modal must appear after the first upload says requires_mapping.
    // Identified by its unique aria-labelledby.
    const modal = page.locator('[role="dialog"][aria-labelledby="column-mapping-title"]')
    await expect(modal).toBeVisible({ timeout: 15000 })

    await expect(page.locator('#account-column')).toBeVisible()
    await expect(page.locator('#debit-column')).toBeVisible()
    await expect(page.locator('#credit-column')).toBeVisible()

    // Pick a valid (all-distinct) mapping
    await page.selectOption('#account-column', 'Col A')
    await page.selectOption('#debit-column', 'Col B')
    await page.selectOption('#credit-column', 'Col C')

    const confirmButton = page.getByRole('button', { name: /confirm mapping/i })
    await expect(confirmButton).toBeEnabled()
    await confirmButton.click()

    // Modal must close after a successful mapping submission
    await expect(modal).not.toBeVisible({ timeout: 10000 })

    // Wait for the second upload, then past the 300ms debounce window so a
    // regression-induced third call has a chance to fire.
    await expect.poll(() => uploads.length, { timeout: 15000 }).toBeGreaterThanOrEqual(2)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(800)

    // 1 = initial upload (requires mapping), 2 = with the mapping, 3+ = debounce regression
    expect(uploads.length, 'exactly 2 uploads expected — initial + post-mapping').toBe(2)
    expect(uploads.map(u => u.hadMapping), 'only the second upload carries column_mapping').toEqual([false, true])

    // The page shows the results, not an error.
    await expect(page.getByRole('heading', { name: 'Tool Error' })).toHaveCount(0)
    await expect(page.getByText(/could not be completed|failed to analyze/i)).toHaveCount(0)
  })

  test('mapping modal cancel does not trigger a second upload', async ({ page }) => {
    const uploads = await countUploads(page, 1)

    await page.goto('/tools/trial-balance')
    await page.waitForLoadState('networkidle')

    const fileInput = page.locator('input[type="file"]')
    await expect(fileInput).toBeAttached({ timeout: 10000 })
    await fileInput.setInputFiles({
      name: 'cancel-mapping.csv',
      mimeType: 'text/csv',
      buffer: genericHeaderCsv(['Cash,50000,0', 'Revenue,0,50000']),
    })

    await proceedPastPreflight(page)

    const modal = page.locator('[role="dialog"][aria-labelledby="column-mapping-title"]')
    await expect(modal).toBeVisible({ timeout: 15000 })

    // Cancel rather than confirm
    await page.getByRole('button', { name: /^cancel$/i }).click()
    await expect(modal).not.toBeVisible({ timeout: 5000 })

    // Wait past the debounce window in case a stale state would trigger one
    await page.waitForTimeout(800)

    // Cancelling must NOT trigger a second upload — only the initial one that asked for a mapping.
    expect(uploads.length, 'cancel must not trigger a second upload').toBe(1)
  })
})
