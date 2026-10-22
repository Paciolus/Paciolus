#!/usr/bin/env python3
"""Every page route must be server-rendered on demand — Sprint 786b.

WHY THIS EXISTS
Nonce-based CSP requires the HTML to be generated per request: the nonce in
the `Content-Security-Policy` header has to match the one on the `<script>`
tags. A prerendered page carries a nonce baked in at build time, which will
not match the header the proxy emits, so every inline script on it is blocked.

`CLAUDE.md` and the project memory both state the invariant — *"Build output
must show `ƒ (Dynamic)` not `○ (Static)` when CSP is active (CRITICAL for
nonce-based CSP)"* — and **nothing enforced it.** It held because
`await headers()` in the root layout forces dynamic rendering, which is one
line in one file away from being removed by someone who does not know why it
is there.

That is the documented-invariant-with-no-enforcement shape this sprint has hit
repeatedly. It matters most right now because Sprint 786b step 3 bumps four
frontend majors, and "did any route silently become static" is exactly the
kind of regression a human reads past in 60 lines of build output.

WHAT COUNTS AS A PAGE
A route whose last path segment contains a dot is an asset — `/icon.png`,
`/sitemap.xml`, `/robots.txt`. Those are *supposed* to be static: there is no
HTML, no inline script and no nonce. Everything else is a page and must be
dynamic.

Derived from the route path rather than from a hand-maintained allowlist, so
adding an asset does not require editing this file — Sprint 792's ranking,
where an explicit list of paths is the tier that silently stops covering what
it is named after.

Usage:
    npm run build | python ../scripts/check_route_rendering.py
    python scripts/check_route_rendering.py build-output.txt
"""

from __future__ import annotations

import re
import sys

# Next.js route table lines, e.g.
#   ├ ƒ /tools/trial-balance
#   ├ ○ /icon.png
#   └ ƒ /verify-email
# The leading box-drawing characters vary; the marker and path do not.
_ROUTE = re.compile(r"^[├└┌│\s]*(?P<marker>[ƒ○●◐])\s+(?P<path>/\S*)\s*(?:\d|$)")

DYNAMIC = "ƒ"
STATIC = "○"


def is_asset(path: str) -> bool:
    """True when the route is a file rather than a page.

    `/sitemap.xml` and `/icon.png` have no HTML and therefore no nonce, so
    being prerendered is correct for them.
    """
    last = path.rstrip("/").rsplit("/", 1)[-1]
    return "." in last


def parse_routes(text: str) -> list[tuple[str, str]]:
    """[(marker, path)] for every route line in a Next.js build output."""
    routes: list[tuple[str, str]] = []
    for line in text.splitlines():
        # The legend lines ("○  (Static)   prerendered as static content")
        # look like routes until you notice the path is parenthesised prose.
        if "(Static)" in line or "(Dynamic)" in line or "(Partial Prerender)" in line:
            continue
        match = _ROUTE.match(line)
        if not match:
            continue
        routes.append((match.group("marker"), match.group("path")))
    return routes


_MARKER_NAMES = {
    "\u0192": "dynamic",
    "\u25cb": "STATIC - prerendered",
    "\u25cf": "static with props",
    "\u25d0": "partially prerendered",
}


def main() -> int:
    # A diagnostic that cannot be printed is not a diagnostic. Windows
    # consoles default to cp1252, which cannot encode the box-drawing and
    #
    # STDIN is the half that actually broke. The first version
    # reconfigured only the output streams, so piping a build into this
    # script read the box-drawing characters as cp1252, mangled them, and
    # matched no routes — reporting 'no route table found' for an encoding
    # reason rather than a real one. It failed closed, which was right, but
    # for the wrong cause. Found only by running the pipe form end to end.
    # marker characters Next.js emits.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass

    text = (
        open(sys.argv[1], encoding="utf-8").read()
        if len(sys.argv) > 1
        else sys.stdin.read()
    )

    routes = parse_routes(text)
    if not routes:
        print("ERROR: no route table found in the build output.")
        print(
            "Either the build failed, or Next.js changed its output format and this check now"
        )
        print("verifies nothing — which is worse than failing, so it fails.")
        return 1

    pages = [(m, p) for m, p in routes if not is_asset(p)]
    assets = [(m, p) for m, p in routes if is_asset(p)]
    offenders = [(m, p) for m, p in pages if m != DYNAMIC]

    print("Route Rendering Check (Sprint 786b)")
    print(f"  routes parsed : {len(routes)}")
    print(f"  pages         : {len(pages)}")
    print(
        f"  assets        : {len(assets)} ({', '.join(p for _m, p in assets) or 'none'})"
    )

    if not pages:
        print(
            "\nERROR: routes were parsed but none of them is a page. The asset heuristic has"
        )
        print(
            "swallowed the whole table, so this check is no longer looking at anything."
        )
        return 1

    if offenders:
        print(
            f"\nERROR: {len(offenders)} page route(s) are not server-rendered on demand:"
        )
        for marker, path in offenders:
            # The marker is named, not echoed. Printing the raw glyph
            # crashed this branch with UnicodeEncodeError on a cp1252
            # console, so the failure path died mid-output and the
            # operator never learned which route was wrong — while the
            # non-zero exit made it look as though the check had worked.
            print(f"  {path}   [{_MARKER_NAMES.get(marker, chr(63))}]")
        print(
            "\nNonce-based CSP needs HTML generated per request — a prerendered page carries a"
        )
        print(
            "build-time nonce that will not match the header the proxy sends, so every inline"
        )
        print(
            "script on it is blocked. `await headers()` in the root layout is what forces"
        )
        print("dynamic rendering; check whether it was removed or short-circuited.")
        return 1

    print(f"\nAll {len(pages)} page routes are dynamic.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
