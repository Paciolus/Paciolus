#!/usr/bin/env bash
#
# pip-audit gate — Sprint 794b. The Python counterpart to npm_audit_gate.sh.
#
# WHY THIS EXISTS
# `pip-audit` exits 1 when it finds a vulnerability AND when it cannot reach
# the service it needs. Captured from pip-audit 2.10.1 against an unreachable
# index: exit 1, nothing on stdout — indistinguishable by exit code from a
# genuine finding. Sprint 794a fixed the same defect on the npm side after a
# 503 from registry.npmjs.org failed PR #189's CVE gate with no vulnerability
# present. Three pip-audit call sites had it too.
#
# WHAT THIS CHANGES
#   1. Retries, so a transient outage does not reach a verdict at all.
#   2. Separates the outcomes. `--format json` is classified by payload
#      (scripts/classify_pip_audit.py) rather than by exit code — the exit
#      code being precisely what cannot tell them apart.
#   3. Says which happened. An unreachable service still fails a blocking
#      gate (unchanged policy), but now says so in words.
#
# Whether "unverified" SHOULD block is Sprint 794 step 3 and is NOT settled
# here. This script preserves the existing behaviour and only makes the signal
# honest.
#
# Usage: pip_audit_gate.sh [--mode blocking|advisory] [-- <pip-audit args>...]
#   --mode   blocking → non-zero exit on VULNERABLE or UNVERIFIED (default)
#            advisory → always exits 0; reports only
#   Everything after `--` is passed through to pip-audit, so callers keep
#   their own `-r requirements.txt` and `--ignore-vuln ...` flags.
#
# `--format json` is added by this script. Callers must not pass `--desc`:
# it is meaningless with JSON output, and the JSON already carries the
# descriptions the readable summary needs.

set -uo pipefail

MODE="blocking"
ATTEMPTS="${PIP_AUDIT_ATTEMPTS:-3}"
# Overridable so the tests do not sleep.
BACKOFF="${PIP_AUDIT_BACKOFF_SECONDS:-10}"
PASSTHROUGH=()

while [ $# -gt 0 ]; do
  case "$1" in
    --mode) MODE="${2:?--mode needs a value}"; shift 2 ;;
    --) shift; PASSTHROUGH=("$@"); break ;;
    *) echo "pip_audit_gate: unknown argument '$1' (pip-audit args go after '--')" >&2; exit 2 ;;
  esac
done

case "$MODE" in
  blocking|advisory) ;;
  *) echo "pip_audit_gate: --mode must be 'blocking' or 'advisory', got '$MODE'" >&2; exit 2 ;;
esac

for arg in ${PASSTHROUGH+"${PASSTHROUGH[@]}"}; do
  if [ "$arg" = "--desc" ]; then
    echo "pip_audit_gate: drop '--desc' — it does nothing alongside --format json, and the" >&2
    echo "                readable summary is built from the JSON instead." >&2
    exit 2
  fi
  if [ "$arg" = "--format" ]; then
    echo "pip_audit_gate: do not pass '--format'; this gate requires JSON to tell a finding" >&2
    echo "                apart from an outage." >&2
    exit 2
  fi
done

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "pip_audit_gate: no python interpreter found — cannot classify the audit result." >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLASSIFIER="$SCRIPT_DIR/classify_pip_audit.py"
if [ ! -f "$CLASSIFIER" ]; then
  echo "pip_audit_gate: classifier not found at $CLASSIFIER" >&2
  exit 2
fi

VERDICT=""
REASON=""

attempt=1
while [ "$attempt" -le "$ATTEMPTS" ]; do
  RAW="$(pip-audit --format json ${PASSTHROUGH+"${PASSTHROUGH[@]}"} 2>/dev/null)"
  PIP_EXIT=$?

  CLASSIFIED="$(printf '%s' "$RAW" | "$PY" "$CLASSIFIER" --pip-exit "$PIP_EXIT")"
  VERDICT="$(printf '%s\n' "$CLASSIFIED" | sed -n '1p')"
  REASON="$(printf '%s\n' "$CLASSIFIED" | sed -n '2,$p')"

  if [ "$VERDICT" != "UNVERIFIED" ]; then
    break
  fi

  if [ "$attempt" -lt "$ATTEMPTS" ]; then
    echo "pip-audit attempt $attempt/$ATTEMPTS could not verify: $REASON"
    echo "Retrying in ${BACKOFF}s — this is a transport problem, not a finding."
    sleep "$BACKOFF"
    BACKOFF=$(( BACKOFF * 2 ))
  fi
  attempt=$(( attempt + 1 ))
done

echo ""
echo "pip-audit verdict: $VERDICT"
echo "$REASON"
echo ""

case "$VERDICT" in
  CLEAN)
    exit 0
    ;;
  VULNERABLE)
    echo "Run 'pip-audit --desc' in backend/ for the full advisory text."
    [ "$MODE" = "blocking" ] && exit 1
    exit 0
    ;;
  UNVERIFIED)
    echo "THIS IS NOT A VULNERABILITY FINDING."
    echo "The audit could not be completed after $ATTEMPTS attempts, so the dependency"
    echo "tree is neither proven clean nor proven vulnerable. The usual cause is an"
    echo "outage at the package index or the advisory service; re-running this job is"
    echo "the normal response."
    [ "$MODE" = "blocking" ] && exit 1
    exit 0
    ;;
  *)
    echo "pip_audit_gate: classifier returned an unrecognised verdict '$VERDICT'." >&2
    [ "$MODE" = "blocking" ] && exit 1
    exit 0
    ;;
esac
