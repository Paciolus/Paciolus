#!/usr/bin/env python3
"""
Sprint 807 (finding C-1) — every third party the product actually talks to must
appear in the subprocessor list.

The Data Processing Addendum commits in writing to *"Maintain an up-to-date list
of subprocessors at SUBPROCESSOR_LIST.md"*, and to a documented vendor risk
assessment before engagement. Two providers were processing customer data and
appeared on no list:

- **Cloudflare (R2).** `shared/export_share_storage.py` has written export-share
  *file bytes* to the `paciolus-exports` bucket since Sprint 611 — the most
  sensitive payload the product handles.
- **Google LLC.** `globals.css` loaded three font families from
  `fonts.googleapis.com`, sending every visitor's IP and User-Agent to Google on
  every page load.

Neither was caught by anything, because nothing was looking. This is that
something. It is deliberately mechanical: it reads the hosts out of the CSP in
`src/proxy.ts` and the storage buckets out of the backend's R2 configuration, and
asserts that each maps to a row in the subprocessor list — or to an explicit,
commented exemption below.

Run:  python scripts/lint_subprocessors.py
Exit: 0 clean, 1 on any unmapped host or bucket.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

PROXY = REPO_ROOT / "frontend" / "src" / "proxy.ts"
GLOBALS_CSS = REPO_ROOT / "frontend" / "src" / "app" / "globals.css"
SUBPROCESSOR_LIST = REPO_ROOT / "docs" / "04-compliance" / "SUBPROCESSOR_LIST.md"
BACKEND = REPO_ROOT / "backend"

# ---------------------------------------------------------------------------
# Host -> the provider that must appear in the subprocessor list.
#
# A host absent from this map is a *failure*, not a pass: a new third-party
# origin in the CSP is exactly the event this gate exists to catch, and
# defaulting to "allowed" would reproduce the hand-maintained-list failure that
# finding C-1 and the DEC's H3 are both instances of.
# ---------------------------------------------------------------------------
HOST_TO_PROVIDER: dict[str, str] = {
    "*.sentry.io": "Sentry",
    "sentry.io": "Sentry",
    "fonts.googleapis.com": "Google",
    "fonts.gstatic.com": "Google",
    "js.stripe.com": "Stripe",
    "api.stripe.com": "Stripe",
    "checkout.stripe.com": "Stripe",
}

# CSP sources that are not third-party origins.
NON_HOST_SOURCES = {
    "'self'",
    "'none'",
    "'unsafe-inline'",
    "'unsafe-eval'",
    "'strict-dynamic'",
    "data:",
    "blob:",
    "https:",
    "http:",
}

# ---------------------------------------------------------------------------
# Storage buckets -> provider. Keyed by the env-var prefix the backend reads.
# ---------------------------------------------------------------------------
BUCKET_ENV_TO_PROVIDER: dict[str, str] = {
    "R2_EXPORTS": "Cloudflare",
    "R2_BACKUPS": "Cloudflare",
}


def _fail(message: str) -> None:
    print(f"  FAIL  {message}")


def _listed_providers() -> set[str]:
    """
    Provider names from the Active Subprocessors table.

    Rows look like `| **Render** | ... |`, so the bolded first cell is the name.
    Only the Active Subprocessors section counts — the Infrastructure-Only table
    below it is explicitly *not* a list of processors.
    """
    text = SUBPROCESSOR_LIST.read_text(encoding="utf-8")
    try:
        start = text.index("## Active Subprocessors")
    except ValueError:
        print("FAIL: SUBPROCESSOR_LIST.md has no '## Active Subprocessors' section")
        sys.exit(1)
    end = text.index("\n## ", start + 1)
    section = text[start:end]

    providers: set[str] = set()
    for row in section.splitlines():
        if not row.startswith("|"):
            continue
        match = re.match(r"\|\s*\*\*([^*]+)\*\*", row)
        if match:
            providers.add(match.group(1).strip())
    return providers


# CSP directive names whose values can name a third-party origin. A directive
# string is recognised by starting with one of these.
CSP_FETCH_DIRECTIVES = (
    "default-src",
    "script-src",
    "style-src",
    "img-src",
    "font-src",
    "connect-src",
    "frame-src",
    "media-src",
    "worker-src",
    "manifest-src",
    "child-src",
    "object-src",
    "form-action",
    "base-uri",
    "frame-ancestors",
)


def _csp_hosts() -> set[str]:
    """
    Every third-party origin named in the Content-Security-Policy.

    Parsed on two rules that matter:
    - `//` comment lines are stripped first. Prose in a comment, and any
      backticks it uses to quote code, otherwise parse as CSP sources and the
      gate reports English words as undisclosed hosts.
    - Directive strings are delimited by `"` or a backtick only — **never** a
      single quote, because CSP values contain single quotes (`'self'`,
      `'strict-dynamic'`). Treating `'` as a delimiter mis-pairs the quotes and
      silently captures whatever sits between two directives.
    """
    text = PROXY.read_text(encoding="utf-8")
    if "const csp = [" not in text:
        print(f"FAIL: {PROXY.name} has no `const csp = [` block to read")
        sys.exit(1)

    lines = [line for line in text.splitlines() if not line.strip().startswith("//")]

    hosts: set[str] = set()
    for line in lines:
        for raw in re.findall(r'"([^"]*)"|`([^`]*)`', line):
            directive = (raw[0] or raw[1]).strip()
            tokens = directive.split()
            if not tokens or tokens[0] not in CSP_FETCH_DIRECTIVES:
                continue
            for token in tokens[1:]:
                if token in NON_HOST_SOURCES or token.startswith("${") or token.startswith("'"):
                    continue  # keyword source, or our own interpolated API URL
                host = re.sub(r"^https?://", "", token).rstrip("/")
                if host and host not in NON_HOST_SOURCES:
                    hosts.add(host)
    return hosts


def _css_import_hosts() -> set[str]:
    """
    Third-party origins pulled in by a CSS `@import url(...)`.

    Checked separately because this is how the Google Fonts dependency entered:
    a stylesheet import is invisible to a reader scanning the CSP, and it loads
    on every page.
    """
    if not GLOBALS_CSS.exists():
        return set()
    hosts: set[str] = set()
    for url in re.findall(r"@import\s+url\(\s*['\"]?(https?://[^'\")]+)", GLOBALS_CSS.read_text(encoding="utf-8")):
        hosts.add(re.sub(r"^https?://", "", url).split("/")[0])
    return hosts


def _component_link_hosts() -> dict[str, set[str]]:
    """
    Third-party origins fetched by a `<link href="https://...">` in a component,
    mapped host -> set of files naming it.

    **Why this check exists.** The first pass of Sprint 807 removed the
    `@import` from `globals.css` and the two hosts from the CSP, and declared
    C-2 resolved. The compiled bundle still contained
    `fonts.googleapis.com/css2?family=Merriweather...` — because two *more*
    loaders existed that neither the review nor that pass had looked at:

    - `app/global-error.tsx` rendered its own `<html>` with a `<link
      rel="stylesheet">` to Google, so the one page that renders after the app
      has already crashed also made a third-party request.
    - `app/internal/typography-preview/page.tsx` loaded three candidate serifs
      plus two `preconnect` hints — on a route with no auth gate, by its own
      design note.

    A gate that reads `globals.css` and the CSP and calls that "every external
    host" is a scan whose scope silently excludes the thing it was written for.
    That is the exact defect the PR #185 review found against that guard,
    and the reason this function reads *source*, not configuration.
    """
    hosts: dict[str, set[str]] = {}
    src = REPO_ROOT / "frontend" / "src"
    if not src.exists():
        return hosts

    # <link ... href="https://host/..." /> and preconnect/dns-prefetch hints.
    pattern = re.compile(r"""href=["']https?://([^/"']+)""")
    for path in sorted(src.rglob("*.tsx")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "<link" not in text:
            continue
        # Only consider href attributes that sit inside a <link ...> element.
        for element in re.findall(r"<link\b[^>]*>", text, re.DOTALL):
            for host in pattern.findall(element):
                hosts.setdefault(host, set()).add(path.relative_to(src).as_posix())
    return hosts


def _configured_buckets() -> set[str]:
    """Storage bucket env-var prefixes the backend actually reads."""
    found: set[str] = set()
    for path in BACKEND.rglob("*.py"):
        if "venv" in path.parts or "tests" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for prefix in BUCKET_ENV_TO_PROVIDER:
            if f"{prefix}_BUCKET" in text:
                found.add(prefix)
    return found


def main() -> int:
    listed = _listed_providers()
    failures = 0

    print("Subprocessor coverage gate (Sprint 807, finding C-1)")
    print(f"  listed providers: {', '.join(sorted(listed))}\n")

    csp_hosts = _csp_hosts()
    css_hosts = _css_import_hosts()
    link_hosts = _component_link_hosts()
    print(f"  CSP third-party hosts:         {', '.join(sorted(csp_hosts)) or '(none)'}")
    print(f"  CSS @import third-party hosts: {', '.join(sorted(css_hosts)) or '(none)'}")
    print(f"  <link> third-party hosts:      {', '.join(sorted(link_hosts)) or '(none)'}")

    for host in sorted(csp_hosts | css_hosts | set(link_hosts)):
        where = f" (in {', '.join(sorted(link_hosts[host]))})" if host in link_hosts else ""
        provider = HOST_TO_PROVIDER.get(host)
        if provider is None:
            _fail(
                f"host '{host}' is reachable from the app{where} but is not mapped to a "
                f"provider. Add it to HOST_TO_PROVIDER in this script and add the provider "
                f"to SUBPROCESSOR_LIST.md, or remove the host."
            )
            failures += 1
        elif provider not in listed:
            _fail(
                f"host '{host}' is reachable from the app{where}, maps to '{provider}', and "
                f"'{provider}' is not in the Active Subprocessors table. The DPA commits "
                f"to maintaining that list."
            )
            failures += 1

    buckets = _configured_buckets()
    print(f"  configured storage buckets:   {', '.join(sorted(buckets)) or '(none)'}")
    for prefix in sorted(buckets):
        provider = BUCKET_ENV_TO_PROVIDER[prefix]
        if provider not in listed:
            _fail(
                f"bucket '{prefix}' is written by the backend, maps to '{provider}', and "
                f"'{provider}' is not in the Active Subprocessors table. This is how "
                f"export-share file bytes went to an undisclosed processor for six months."
            )
            failures += 1

    print()
    if failures:
        print(f"FAILED: {failures} unmapped third part{'y' if failures == 1 else 'ies'}")
        return 1
    print("PASS: every CSP host and storage bucket maps to a listed subprocessor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
