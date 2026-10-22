#!/usr/bin/env bash
#
# npm audit gate — Sprint 794.
#
# WHY THIS EXISTS
# `npm audit` exits 1 when it finds a vulnerability AND when it cannot reach
# the advisory endpoint. On 2026-10-22 PR #189's "Node CVE & License Audit"
# went red on a 503 from registry.npmjs.org; no vulnerability existed, but the
# failure was indistinguishable from a genuine CRITICAL. Three call sites ran
# the bare command, so all three had it.
#
# WHAT THIS CHANGES
#   1. Retries. A 503 is usually seconds long, so most of the problem is gone
#      before any policy question is reached.
#   2. Separates the outcomes. `--json` is classified by payload
#      (scripts/classify_npm_audit.py) rather than by exit code — the exit
#      code being precisely what cannot tell them apart.
#   3. Says which happened. An unreachable registry still fails a blocking
#      gate (unchanged policy — a security gate that opens when it cannot see
#      is worse), but it now says so in words, so the reader re-runs the job
#      instead of hunting a CVE that was never there.
#
# Whether "unverified" SHOULD block is a real judgement call and is NOT
# settled here: failing closed matches the Sprint 778a precedent, but 778a
# gates a monthly report while this gates every PR, so a long npm incident
# stops all work. Tracked as Sprint 794 step 3. This script preserves the
# existing behaviour and only makes the signal honest.
#
# Usage: npm_audit_gate.sh [--audit-level LEVEL] [--mode blocking|advisory]
#   --audit-level  lowest severity that counts as a finding (default: high)
#   --mode         blocking → non-zero exit on VULNERABLE or UNVERIFIED
#                  advisory → always exits 0; reports only (default: blocking)
# Run from the directory containing package.json.

set -uo pipefail

AUDIT_LEVEL="high"
MODE="blocking"
ATTEMPTS="${NPM_AUDIT_ATTEMPTS:-3}"
# Overridable so the tests do not sleep.
BACKOFF="${NPM_AUDIT_BACKOFF_SECONDS:-10}"

while [ $# -gt 0 ]; do
  case "$1" in
    --audit-level) AUDIT_LEVEL="${2:?--audit-level needs a value}"; shift 2 ;;
    --mode)        MODE="${2:?--mode needs a value}"; shift 2 ;;
    *) echo "npm_audit_gate: unknown argument '$1'" >&2; exit 2 ;;
  esac
done

case "$MODE" in
  blocking|advisory) ;;
  *) echo "npm_audit_gate: --mode must be 'blocking' or 'advisory', got '$MODE'" >&2; exit 2 ;;
esac

# `python3` on CI runners, `python` on a Windows dev box.
PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "npm_audit_gate: no python interpreter found — cannot classify the audit result." >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLASSIFIER="$SCRIPT_DIR/classify_npm_audit.py"
if [ ! -f "$CLASSIFIER" ]; then
  echo "npm_audit_gate: classifier not found at $CLASSIFIER" >&2
  exit 2
fi

RAW=""
VERDICT=""
REASON=""

attempt=1
while [ "$attempt" -le "$ATTEMPTS" ]; do
  RAW="$(npm audit --json --omit=dev --audit-level="$AUDIT_LEVEL" 2>/dev/null)"
  NPM_EXIT=$?

  CLASSIFIED="$(printf '%s' "$RAW" | "$PY" "$CLASSIFIER" --npm-exit "$NPM_EXIT" --audit-level "$AUDIT_LEVEL")"
  VERDICT="$(printf '%s\n' "$CLASSIFIED" | sed -n '1p')"
  REASON="$(printf '%s\n' "$CLASSIFIED" | sed -n '2,$p')"

  if [ "$VERDICT" != "UNVERIFIED" ]; then
    break
  fi

  if [ "$attempt" -lt "$ATTEMPTS" ]; then
    echo "npm audit attempt $attempt/$ATTEMPTS could not verify: $REASON"
    echo "Retrying in ${BACKOFF}s — this is a transport problem, not a finding."
    sleep "$BACKOFF"
    BACKOFF=$(( BACKOFF * 2 ))
  fi
  attempt=$(( attempt + 1 ))
done

echo ""
echo "npm audit verdict: $VERDICT"
echo "$REASON"
echo ""

case "$VERDICT" in
  CLEAN)
    exit 0
    ;;
  VULNERABLE)
    echo "A dependency vulnerability at or above '$AUDIT_LEVEL' is present."
    echo "Run 'npm audit --omit=dev' in frontend/ for the advisory detail."
    [ "$MODE" = "blocking" ] && exit 1
    exit 0
    ;;
  UNVERIFIED)
    echo "THIS IS NOT A VULNERABILITY FINDING."
    echo "The audit could not be completed after $ATTEMPTS attempts, so the dependency"
    echo "tree is neither proven clean nor proven vulnerable. The usual cause is an"
    echo "outage at registry.npmjs.org; re-running this job is the normal response."
    [ "$MODE" = "blocking" ] && exit 1
    exit 0
    ;;
  *)
    echo "npm_audit_gate: classifier returned an unrecognised verdict '$VERDICT'." >&2
    [ "$MODE" = "blocking" ] && exit 1
    exit 0
    ;;
esac
