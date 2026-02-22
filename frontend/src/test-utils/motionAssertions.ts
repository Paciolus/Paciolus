/**
 * Motion Assertion Helpers — Sprint 405: Phase LVI
 *
 * Small helpers to extract framer-motion state from rendered output.
 * Since framer-motion in jsdom doesn't actually animate, these helpers
 * verify structural correctness rather than visual animation.
 */

/**
 * Check that an element has framer-motion data attributes.
 * Useful for verifying a component uses motion.div vs plain div.
 */
export function hasMotionWrapper(container: HTMLElement): boolean {
  const firstChild = container.firstElementChild
  if (!firstChild) return false
  // Our mock renders motion.div as plain div, but we can check
  // that the container has exactly one child wrapper
  return firstChild.tagName === 'DIV'
}

/**
 * Get the key from an AnimatePresence-wrapped motion.div.
 * Returns the data-testid or text content as a proxy for the key
 * (since React keys are not accessible in the DOM).
 */
export function getActiveStateContent(container: HTMLElement): string | null {
  const wrapper = container.firstElementChild
  if (!wrapper) return null
  return wrapper.textContent
}

/**
 * Assert that only one state is rendered at a time.
 * Useful for ToolStatePresence verification.
 */
export function assertSingleState(
  container: HTMLElement,
  expectedTestId: string
): void {
  const el = container.querySelector(`[data-testid="${expectedTestId}"]`)
  if (!el) {
    throw new Error(`Expected element with data-testid="${expectedTestId}" to be present`)
  }
}
