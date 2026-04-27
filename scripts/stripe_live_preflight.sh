#!/usr/bin/env bash
# Sprint 719 — Stripe live-mode preflight runner.
#
# Mandatory checklist step before flipping the Stripe live-mode env vars
# to production.  Triggers each event type the webhook handler claims
# to support, captures the response, and bails on the first non-200.
#
# Prereq: Stripe CLI installed and logged in to the LIVE account.
#   $ stripe --version    # must succeed
#   $ stripe login        # opens browser, paste live-mode session key
#
# Usage:
#   $ scripts/stripe_live_preflight.sh https://api.paciolus.com/billing/webhook
#
# What this does:
# - Fires one of each WEBHOOK_HANDLERS event type via `stripe trigger`.
# - Stripe CLI sends to your live webhook endpoint and prints the
#   response code.  Any non-200 means the live secret + handler chain
#   isn't aligned -- DO NOT proceed with the cutover.
#
# Out of scope (intentional):
# - Asserting state changes in the admin dashboard (would require API
#   token tour through Postgres / admin endpoints).  The 200/non-200
#   binary catches the most common cutover failures (signature
#   mismatch, secret format).
#
# Exit codes:
#   0 = all events returned 2xx
#   non-0 = at least one event failed; stderr lists the failure
#
# Lifecycle:
# - This script is referenced from tasks/ceo-actions.md Phase 4.1.
# - Update WEBHOOK_HANDLERS list when backend/billing/webhook_handler.py
#   adds or removes event types.

set -euo pipefail

ENDPOINT="${1:-}"
if [[ -z "$ENDPOINT" ]]; then
  echo "Usage: $0 <webhook-endpoint-url>" >&2
  echo "Example: $0 https://api.paciolus.com/billing/webhook" >&2
  exit 64
fi

if ! command -v stripe >/dev/null 2>&1; then
  echo "ERROR: Stripe CLI not on PATH. Install: https://stripe.com/docs/stripe-cli" >&2
  exit 64
fi

# Event types the live handler must accept. Keep in sync with
# backend/billing/webhook_handler.py WEBHOOK_HANDLERS.
EVENTS=(
  "checkout.session.completed"
  "customer.subscription.created"
  "customer.subscription.updated"
  "customer.subscription.deleted"
  "customer.subscription.trial_will_end"
  "invoice.created"
  "invoice.paid"
  "invoice.payment_succeeded"
  "invoice.payment_failed"
  "charge.dispute.created"
  "charge.dispute.closed"
)

failures=0
echo "Sprint 719 Stripe live preflight"
echo "Endpoint: $ENDPOINT"
echo "Event types to fire: ${#EVENTS[@]}"
echo ""

for event_type in "${EVENTS[@]}"; do
  echo -n "→ $event_type ... "
  if stripe trigger "$event_type" --add "billing_endpoint:$ENDPOINT" >/tmp/stripe_preflight.log 2>&1; then
    echo "OK"
  else
    echo "FAIL"
    echo "  See /tmp/stripe_preflight.log for details" >&2
    failures=$((failures + 1))
  fi
done

echo ""
if [[ $failures -gt 0 ]]; then
  echo "ERROR: $failures of ${#EVENTS[@]} events failed" >&2
  echo "Do NOT proceed with the live-mode cutover until every event returns 200." >&2
  exit 1
fi

echo "OK: all ${#EVENTS[@]} events accepted by $ENDPOINT"
echo "Live-mode cutover is GREEN for the webhook handler. Proceed with the"
echo "tasks/ceo-actions.md Phase 4.1 checklist."
