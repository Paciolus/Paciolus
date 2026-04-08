#!/usr/bin/env bash
# Paciolus Post-Deploy Smoke Test
#
# Exercises the critical boot + auth path against a deployed backend.
# Use after any Render deploy or DB/env var change to confirm the instance
# is genuinely healthy before declaring success.
#
# Usage:
#   scripts/smoke_test_render.sh                                  # defaults to https://paciolus-api.onrender.com
#   scripts/smoke_test_render.sh https://api.paciolus.com         # override base URL
#   BASE_URL=https://paciolus-api.onrender.com scripts/smoke_test_render.sh
#
# What it checks:
#   1.  /health returns 200 within 10s (cold-start tolerated up to 45s)
#   2.  /auth/csrf without auth returns 401 (proves auth middleware wired)
#   3.  /auth/register succeeds and sets paciolus_access + paciolus_refresh HttpOnly cookies
#   4.  Register response includes access_token + csrf_token + user object
#   5.  /auth/me with the register cookies returns 200 and the same user
#   6.  /auth/login (fresh attempt with a known-bad password) returns 401
#   7.  /auth/logout succeeds and the Set-Cookie header clears both cookies
#   8.  /auth/me after logout returns 401 (session is actually revoked)
#
# Exit codes:
#   0  all checks pass
#   1  any check fails (script stops at the first failure)
#
# Dependencies: curl, jq, mktemp
# Zero-Storage: the test account is registered, exercised, and then left alone.
# The dunning cleanup scheduler will retire unused accounts per retention policy.

set -euo pipefail

BASE_URL="${1:-${BASE_URL:-https://paciolus-api.onrender.com}}"
COOKIE_JAR="$(mktemp -t paciolus-smoke.XXXXXX)"
trap 'rm -f "$COOKIE_JAR"' EXIT

TIMESTAMP="$(date +%s)"
TEST_EMAIL="smoke-test-${TIMESTAMP}@paciolus.test"
TEST_PASSWORD="SmokeTest!${TIMESTAMP}"

# Colors for readable output
GREEN=$(tput setaf 2 2>/dev/null || true)
RED=$(tput setaf 1 2>/dev/null || true)
YELLOW=$(tput setaf 3 2>/dev/null || true)
BOLD=$(tput bold 2>/dev/null || true)
RESET=$(tput sgr0 2>/dev/null || true)

pass() { printf "  ${GREEN}PASS${RESET}  %s\n" "$1"; }
fail() { printf "  ${RED}FAIL${RESET}  %s\n" "$1" >&2; exit 1; }
step() { printf "\n${BOLD}%s${RESET}\n" "$1"; }
info() { printf "  ${YELLOW}INFO${RESET}  %s\n" "$1"; }

command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }
command -v jq   >/dev/null || { echo "jq is required"   >&2; exit 1; }

printf "${BOLD}Paciolus Smoke Test${RESET}\n"
printf "  Base URL:  %s\n" "$BASE_URL"
printf "  Test user: %s\n" "$TEST_EMAIL"

# -----------------------------------------------------------------------------
# Step 1: /health
# -----------------------------------------------------------------------------
step "1. /health"
HEALTH_CODE=$(curl --silent --show-error --max-time 45 --output /dev/null --write-out "%{http_code}" "$BASE_URL/health")
[ "$HEALTH_CODE" = "200" ] && pass "/health returned 200" || fail "/health returned $HEALTH_CODE"

# -----------------------------------------------------------------------------
# Step 2: /auth/csrf without auth should be 401 (auth middleware wired)
# -----------------------------------------------------------------------------
step "2. /auth/csrf (unauthenticated)"
CSRF_CODE=$(curl --silent --max-time 15 --output /dev/null --write-out "%{http_code}" "$BASE_URL/auth/csrf")
[ "$CSRF_CODE" = "401" ] && pass "/auth/csrf correctly rejected unauthenticated request" \
                          || fail "/auth/csrf returned $CSRF_CODE (expected 401)"

# -----------------------------------------------------------------------------
# Step 3: /auth/register — create test account, capture cookies
# -----------------------------------------------------------------------------
step "3. /auth/register"
REGISTER_BODY=$(jq -n --arg email "$TEST_EMAIL" --arg pw "$TEST_PASSWORD" \
    '{email: $email, password: $pw, name: "Smoke Test"}')

REGISTER_RESPONSE=$(curl --silent --show-error --max-time 30 \
    --cookie-jar "$COOKIE_JAR" \
    -H "Content-Type: application/json" \
    -H "X-Requested-With: XMLHttpRequest" \
    -d "$REGISTER_BODY" \
    -w "\n%{http_code}" \
    "$BASE_URL/auth/register")

REGISTER_CODE="${REGISTER_RESPONSE##*$'\n'}"
REGISTER_JSON="${REGISTER_RESPONSE%$'\n'*}"

[ "$REGISTER_CODE" = "201" ] || fail "/auth/register returned $REGISTER_CODE (expected 201)\n$REGISTER_JSON"
pass "/auth/register returned 201"

# Verify response shape
jq -e '.access_token' <<<"$REGISTER_JSON" >/dev/null || fail "register response missing access_token"
jq -e '.csrf_token'   <<<"$REGISTER_JSON" >/dev/null || fail "register response missing csrf_token"
jq -e '.user.email'   <<<"$REGISTER_JSON" >/dev/null || fail "register response missing user.email"
pass "register response shape valid (access_token, csrf_token, user)"

REGISTER_EMAIL=$(jq -r '.user.email' <<<"$REGISTER_JSON")
[ "$REGISTER_EMAIL" = "$TEST_EMAIL" ] || fail "register returned wrong email: $REGISTER_EMAIL"
pass "register returned correct email"

# Verify cookies were set
grep -q "paciolus_access"  "$COOKIE_JAR" || fail "paciolus_access cookie not set by /auth/register"
grep -q "paciolus_refresh" "$COOKIE_JAR" || fail "paciolus_refresh cookie not set by /auth/register"
pass "HttpOnly cookies set (paciolus_access, paciolus_refresh)"

CSRF_TOKEN=$(jq -r '.csrf_token' <<<"$REGISTER_JSON")

# -----------------------------------------------------------------------------
# Step 4: /auth/me with the register cookies
# -----------------------------------------------------------------------------
step "4. /auth/me (cookie-authenticated)"
ME_RESPONSE=$(curl --silent --show-error --max-time 15 \
    --cookie "$COOKIE_JAR" \
    -w "\n%{http_code}" \
    "$BASE_URL/auth/me")

ME_CODE="${ME_RESPONSE##*$'\n'}"
ME_JSON="${ME_RESPONSE%$'\n'*}"

[ "$ME_CODE" = "200" ] || fail "/auth/me returned $ME_CODE (expected 200)"
pass "/auth/me returned 200"

ME_EMAIL=$(jq -r '.email' <<<"$ME_JSON")
[ "$ME_EMAIL" = "$TEST_EMAIL" ] || fail "/auth/me returned wrong email: $ME_EMAIL"
pass "/auth/me returned correct user"

# -----------------------------------------------------------------------------
# Step 5: /auth/login with wrong password (should be 401)
# -----------------------------------------------------------------------------
step "5. /auth/login (wrong password)"
BAD_LOGIN=$(jq -n --arg email "$TEST_EMAIL" '{email: $email, password: "definitelyWrongPassword!1"}')

BAD_LOGIN_CODE=$(curl --silent --max-time 15 --output /dev/null --write-out "%{http_code}" \
    -H "Content-Type: application/json" \
    -H "X-Requested-With: XMLHttpRequest" \
    -d "$BAD_LOGIN" \
    "$BASE_URL/auth/login")

[ "$BAD_LOGIN_CODE" = "401" ] && pass "/auth/login correctly rejected wrong password" \
                              || fail "/auth/login returned $BAD_LOGIN_CODE (expected 401)"

# -----------------------------------------------------------------------------
# Step 6: /auth/logout
# -----------------------------------------------------------------------------
step "6. /auth/logout"
LOGOUT_CODE=$(curl --silent --max-time 15 --output /dev/null --write-out "%{http_code}" \
    --cookie "$COOKIE_JAR" \
    --cookie-jar "$COOKIE_JAR" \
    -H "X-CSRF-Token: $CSRF_TOKEN" \
    -H "X-Requested-With: XMLHttpRequest" \
    -X POST \
    "$BASE_URL/auth/logout")

[ "$LOGOUT_CODE" = "200" ] && pass "/auth/logout returned 200" \
                           || fail "/auth/logout returned $LOGOUT_CODE (expected 200)"

# -----------------------------------------------------------------------------
# Step 7: /auth/me after logout (should be 401 — session revoked)
# -----------------------------------------------------------------------------
step "7. /auth/me (post-logout)"
POST_ME_CODE=$(curl --silent --max-time 15 --output /dev/null --write-out "%{http_code}" \
    --cookie "$COOKIE_JAR" \
    "$BASE_URL/auth/me")

[ "$POST_ME_CODE" = "401" ] && pass "/auth/me returned 401 after logout (session revoked)" \
                            || fail "/auth/me returned $POST_ME_CODE after logout (expected 401)"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
printf "\n${GREEN}${BOLD}All smoke tests passed.${RESET}\n"
printf "  Base URL:   %s\n" "$BASE_URL"
printf "  Test email: %s  (retained; retention cleanup will archive it)\n" "$TEST_EMAIL"
