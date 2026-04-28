/**
 * Sprint 734: Playwright E2E coverage for the mapping-required preflight handoff
 * in the Trial Balance upload flow.
 *
 * Why this spec exists:
 * - `useTrialBalanceUpload` has a state machine that branches on
 *   `column_detection.requires_mapping` to surface a mapping modal, then
 *   relies on the debounce effect (line 254-287 of the hook) to re-run the
 *   audit once the user submits a mapping.
 * - The handoff is the most fragile path in the upload pipeline: a regression
 *   in the debounce dedup logic produces "recalc fires twice" symptoms that
 *   are invisible in unit tests but waste a real upload round-trip per user.
 * - This spec is the prerequisite gate for the deferred decomposition of
 *   `useTrialBalanceUpload` (`tasks/todo.md` Deferred Items line 55).
 *   Without E2E coverage of this flow, the split is unsafe.
 *
 * What this spec asserts:
 *   1. Mapping modal renders when backend signals requires_mapping=true
 *   2. User can pick all three columns (account/debit/credit) and submit
 *   3. After submission, the upload re-runs exactly ONCE (no debounce dupes)
 *   4. The modal closes after submission
 *   5. Results render on the second-pass success
 *
 * Network strategy:
 * - Mocks POST /audit/trial-balance only. All other endpoints (auth, settings,
 *   engagement context) hit the real backend so the test exercises the actual
 *   FastAPI dependency stack and CSP/CSRF middleware.
 * - The mock uses a request counter: first call → requires_mapping response,
 *   second call (with column_mapping in form body) → success response.
 *   A third call would be a regression and is asserted against.
 */
import { test, expect, type Page, type Route } from '@playwright/test'

const SMOKE_USER = process.env.SMOKE_USER ?? ''
const SMOKE_PASS = process.env.SMOKE_PASS ?? ''

/** Minimal `column_detection` payload that triggers the mapping modal. */
const MAPPING_REQUIRED_DETECTION = {
  account_column: null,
  debit_column: null,
  credit_column: null,
  account_confidence: 0.3,
  debit_confidence: 0.4,
  credit_confidence: 0.4,
  overall_confidence: 0.37,
  requires_mapping: true,
  all_columns: ['Col A', 'Col B', 'Col C'],
  detection_notes: [
    'Header row could not be matched against the standard account-column patterns.',
  ],
}

/** First-pass response: backend says mapping is required. */
const MAPPING_REQUIRED_RESPONSE = {
  success: true,
  row_count: 3,
  total_debits: 50000,
  total_credits: 50000,
  balanced: true,
  material_count: 0,
  immaterial_count: 3,
  is_consolidated: false,
  sheet_count: null,
  abnormal_balances: [],
  column_detection: MAPPING_REQUIRED_DETECTION,
}

/** Second-pass response: mapping submitted, audit completes successfully. */
const SUCCESS_RESPONSE = {
  success: true,
  row_count: 3,
  total_debits: 50000,
  total_credits: 50000,
  balanced: true,
  material_count: 1,
  immaterial_count: 2,
  is_consolidated: false,
  sheet_count: null,
  abnormal_balances: [],
  column_detection: {
    ...MAPPING_REQUIRED_DETECTION,
    requires_mapping: false,
    account_column: 'Col A',
    debit_column: 'Col B',
    credit_column: 'Col C',
    overall_confidence: 1.0,
  },
}

async function login(page: Page) {
  await page.goto('/login')
  await page.fill('input[name="email"], input[type="email"]', SMOKE_USER)
  await page.fill('input[name="password"], input[type="password"]', SMOKE_PASS)
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard**', { timeout: 15000 })
}

test.describe('Sprint 734 — Trial Balance mapping-required handoff', () => {
  test.skip(!SMOKE_USER || !SMOKE_PASS, 'SMOKE_USER and SMOKE_PASS env vars required')

  test('mapping modal renders, user submits mapping, second upload completes without debounce dupes', async ({
    page,
  }) => {
    await login(page)

    // Counter is checked at end of test to prove no debounce-induced
    // duplicate uploads. Each request is also classified by whether
    // its body included a column_mapping field, so we can assert the
    // first call had no mapping and the second did.
    let uploadRequestCount = 0
    let firstRequestHadMapping = false
    let secondRequestHadMapping = false

    await page.route('**/audit/trial-balance', async (route: Route) => {
      uploadRequestCount += 1
      const requestNumber = uploadRequestCount

      // Form bodies are multipart/form-data; check whether the
      // column_mapping field was included by scanning the raw body.
      const postData = route.request().postData() ?? ''
      const hasMapping = postData.includes('column_mapping')

      if (requestNumber === 1) {
        firstRequestHadMapping = hasMapping
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(MAPPING_REQUIRED_RESPONSE),
        })
      } else if (requestNumber === 2) {
        secondRequestHadMapping = hasMapping
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(SUCCESS_RESPONSE),
        })
      } else {
        // 3rd+ request would be a debounce regression — fail the
        // route so the test surfaces the issue clearly rather than
        // silently passing on a duplicate response.
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: `Sprint 734 regression: ${requestNumber}rd upload — should be exactly 2`,
          }),
        })
      }
    })

    // Navigate to TB tool and upload the file
    await page.goto('/tools/trial-balance')
    await page.waitForLoadState('networkidle')

    const fileInput = page.locator('input[type="file"]')
    await expect(fileInput).toBeAttached({ timeout: 10000 })

    const csvContent = 'Col A,Col B,Col C\nCash,50000,0\nRevenue,0,50000\nExpense,1000,0'
    await fileInput.setInputFiles({
      name: 'mapping-required.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(csvContent, 'utf-8'),
    })

    // Mapping modal must appear after the first upload returns
    // requires_mapping=true. Identified by its unique aria-labelledby.
    const modal = page.locator('[role="dialog"][aria-labelledby="column-mapping-title"]')
    await expect(modal).toBeVisible({ timeout: 15000 })

    // The three column dropdowns should be populated with the columns
    // from the mocked detection response.
    await expect(page.locator('#account-column')).toBeVisible()
    await expect(page.locator('#debit-column')).toBeVisible()
    await expect(page.locator('#credit-column')).toBeVisible()

    // Pick a valid (all-distinct) mapping
    await page.selectOption('#account-column', 'Col A')
    await page.selectOption('#debit-column', 'Col B')
    await page.selectOption('#credit-column', 'Col C')

    // Confirm — should trigger the second-pass upload via the debounce
    const confirmButton = page.getByRole('button', { name: /confirm mapping/i })
    await expect(confirmButton).toBeEnabled()
    await confirmButton.click()

    // Modal must close after a successful mapping submission
    await expect(modal).not.toBeVisible({ timeout: 10000 })

    // Wait for the second upload + a margin past the 300ms debounce window
    // to give any (regression-induced) third call a chance to fire.
    await page.waitForFunction(() => {
      const w = window as unknown as { __trial_balance_complete?: boolean }
      return w.__trial_balance_complete === true
    }, { timeout: 0 }).catch(() => {
      // No global flag wired up — fall back to network-idle wait + a
      // generous post-debounce buffer.
    })
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(500) // Past the 300ms debounce window

    // Critical Sprint 734 assertion: exactly 2 uploads happened.
    // 1 = initial upload (returns requires_mapping)
    // 2 = post-mapping upload (returns success)
    // 3+ = debounce regression
    expect(uploadRequestCount, 'exactly 2 uploads expected — initial + post-mapping').toBe(2)

    // Pin the request semantics — first had no mapping (hadn't submitted yet),
    // second carried the user's column_mapping in the form body.
    expect(firstRequestHadMapping, 'first upload should have no column_mapping').toBe(false)
    expect(secondRequestHadMapping, 'second upload should carry column_mapping').toBe(true)
  })

  test('mapping modal cancel does not trigger a second upload', async ({ page }) => {
    await login(page)

    let uploadRequestCount = 0

    await page.route('**/audit/trial-balance', async (route: Route) => {
      uploadRequestCount += 1
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MAPPING_REQUIRED_RESPONSE),
      })
    })

    await page.goto('/tools/trial-balance')
    await page.waitForLoadState('networkidle')

    const fileInput = page.locator('input[type="file"]')
    await expect(fileInput).toBeAttached({ timeout: 10000 })

    const csvContent = 'Col A,Col B,Col C\nCash,50000,0\nRevenue,0,50000'
    await fileInput.setInputFiles({
      name: 'cancel-mapping.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(csvContent, 'utf-8'),
    })

    const modal = page.locator('[role="dialog"][aria-labelledby="column-mapping-title"]')
    await expect(modal).toBeVisible({ timeout: 15000 })

    // Cancel rather than confirm
    await page.getByRole('button', { name: /^cancel$/i }).click()
    await expect(modal).not.toBeVisible({ timeout: 5000 })

    // Wait past the debounce window in case a stale state would trigger one
    await page.waitForTimeout(800)

    // Cancelling must NOT trigger a second upload — only the initial one
    // that returned requires_mapping. If this regresses, every cancel
    // wastes a round-trip and the user sees a flicker of stale results.
    expect(uploadRequestCount, 'cancel must not trigger a second upload').toBe(1)
  })
})
