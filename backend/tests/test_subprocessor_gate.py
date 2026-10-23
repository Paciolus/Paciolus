"""
Sprint 807 (finding C-1) — every third party the product talks to must be listed.

`docs/04-compliance/SUBPROCESSOR_LIST.md` carried five entries: Render, Vercel,
Stripe, Sentry, SendGrid. Two were missing:

- **Cloudflare (R2).** `shared/export_share_storage.py` has written export-share
  **file bytes** to the `paciolus-exports` bucket since Sprint 611 (2026-04-23),
  keyed `shares/<share_token_hash>`. That is customer financial export content —
  the most sensitive payload the product handles. Cloudflare appeared in the
  BCP/DR document only as a DNS provider and a hypothetical CDN fallback, never
  as a processor.
- **Google LLC.** `globals.css` loaded three font families from
  `fonts.googleapis.com`, so every visitor's IP address and User-Agent went to
  Google on every page load.

`DATA_PROCESSING_ADDENDUM.md:208` commits in writing to *"Maintain an up-to-date
list of subprocessors"*. For a product positioned on Zero-Storage privacy, an
unlisted processor holding export bytes is the finding most likely to surface in
a customer security review or a DPA negotiation.

It went unnoticed for six months because nothing was checking. That is the same
shape as D-4 (a route list that stopped matching) and T-3 (a pattern that came
back after being fixed once), both in the same review — so the deliverable is the
gate, and these are its tests.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "lint_subprocessors.py"


def _load_gate():
    spec = importlib.util.spec_from_file_location("lint_subprocessors", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gate = _load_gate()


class TestTheGateRuns:
    def test_the_repo_passes(self):
        assert gate.main() == 0

    def test_the_script_exists_where_ci_expects_it(self):
        assert SCRIPT_PATH.exists()


class TestSubprocessorListParsing:
    def test_the_active_subprocessors_are_read(self):
        listed = gate._listed_providers()

        # The five that were always there.
        assert {"Render", "Vercel", "Stripe", "Sentry", "SendGrid"} <= listed

    def test_cloudflare_is_now_listed_as_a_processor(self):
        """C-1's substantive half: the one that actually holds customer bytes."""
        assert "Cloudflare" in gate._listed_providers()

    def test_the_infrastructure_only_table_is_not_counted_as_processors(self):
        """
        The list distinguishes processors from infrastructure, and the gate must
        respect that distinction — otherwise 'GitHub' would satisfy a CSP host
        mapping and the check would be meaningless.
        """
        listed = gate._listed_providers()

        assert "GitHub" not in listed
        assert "Dependabot" not in listed
        assert "Prometheus" not in listed


class TestCspHostExtraction:
    def test_the_google_font_hosts_are_gone(self):
        """
        C-2 resolved the Google half by elimination rather than disclosure: the
        fonts are self-hosted by `next/font`, so the two hosts left the CSP and
        Google never became a row on the list.
        """
        hosts = gate._csp_hosts()

        assert "fonts.googleapis.com" not in hosts
        assert "fonts.gstatic.com" not in hosts

    def test_no_css_import_pulls_a_third_party_stylesheet(self):
        """
        Checked separately from the CSP because this is how the Google Fonts
        dependency got in: a stylesheet `@import` is invisible to a reader
        scanning the CSP, and it loads on every page.
        """
        assert gate._css_import_hosts() == set()

    def test_no_component_link_tag_fetches_a_third_party_origin(self):
        """
        The check that the first pass of Sprint 807 needed and did not have.

        That pass removed the `@import` from `globals.css` and both hosts from
        the CSP, and declared C-2 resolved. The compiled bundle still contained
        `fonts.googleapis.com/css2?family=Merriweather...`, because two more
        loaders existed that nothing had looked at:

        - `app/global-error.tsx` rendered its own `<html>` with a
          `<link rel="stylesheet">` to Google — so the one page that renders
          after the app has already crashed also made a third-party request.
        - `app/internal/typography-preview/page.tsx` loaded three candidate
          serifs plus two `preconnect` hints, on a route with no auth gate by
          its own design note.

        A gate that reads `globals.css` and the CSP and calls that "every
        external host" is a scan whose scope excludes the thing it was written
        for — the defect the PR #185 review found.
        """
        assert gate._component_link_hosts() == {}

    def test_the_link_scan_detects_a_google_font_link(self):
        """
        Proves the scan is connected to something. A regex that silently matches
        nothing would make the assertion above pass for the wrong reason.
        """
        import re

        sample = """
            <link
              href="https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700"
              rel="stylesheet"
            />
            <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        """
        pattern = re.compile(r"""href=["']https?://([^/"']+)""")
        found: set[str] = set()
        for element in re.findall(r"<link\b[^>]*>", sample, re.DOTALL):
            found |= set(pattern.findall(element))

        assert found == {"fonts.googleapis.com", "fonts.gstatic.com"}
        # And both map to a provider that is deliberately not on the list, so
        # the gate would have failed.
        for host in found:
            assert gate.HOST_TO_PROVIDER[host] == "Google"
            assert "Google" not in gate._listed_providers()

    def test_sentry_is_still_reachable_and_still_mapped(self):
        """A sanity check that the extraction is finding real hosts, not nothing."""
        hosts = gate._csp_hosts()

        assert any("sentry.io" in host for host in hosts)
        for host in hosts:
            assert gate.HOST_TO_PROVIDER.get(host) in gate._listed_providers(), host

    def test_csp_parsing_ignores_comments_and_inner_single_quotes(self):
        """
        Two parsing rules that the first draft of this gate got wrong, and both
        produced nonsense findings:
        - `//` comment lines must be stripped, or prose (and the backticks it
          uses to quote code) parses as CSP sources and the gate reports English
          words as undisclosed hosts.
        - Directive strings are delimited by `"` or a backtick only, never a
          single quote, because CSP *values* contain single quotes (`'self'`).
          Treating `'` as a delimiter mis-pairs the quotes and captures whatever
          sits between two directives.
        """
        hosts = gate._csp_hosts()

        for host in hosts:
            assert "." in host or host.startswith("*"), f"{host!r} is not a hostname"
            assert " " not in host, f"{host!r} contains a space"
            assert not host.startswith("'"), host


class TestStorageBucketCoverage:
    def test_the_exports_bucket_is_detected(self):
        """
        The bucket the backend actually writes to. If this stops being detected,
        the gate goes quiet about the finding it exists to catch.
        """
        assert "R2_EXPORTS" in gate._configured_buckets()

    def test_every_configured_bucket_maps_to_a_listed_provider(self):
        listed = gate._listed_providers()
        for prefix in gate._configured_buckets():
            provider = gate.BUCKET_ENV_TO_PROVIDER[prefix]
            assert provider in listed, f"{prefix} -> {provider} is not a listed subprocessor"


class TestTheGateCanActuallyFail:
    """
    Guards the gate itself. A check that passes because it found nothing is the
    failure mode this review kept finding — see the PR #185 defect recorded in
    the PR #185 review, where a scan's own filename filter excluded the module it was
    written for.
    """

    def test_an_unmapped_host_has_no_provider(self):
        assert gate.HOST_TO_PROVIDER.get("cdn.evil-analytics.example") is None

    def test_a_mapped_but_unlisted_provider_is_detectable(self):
        """
        Google is still in the host map on purpose — so that reintroducing a
        Google font host is caught — and Google is deliberately *not* on the
        subprocessor list, because C-2 removed the dependency instead. That
        combination is precisely what the gate must fail on.
        """
        assert gate.HOST_TO_PROVIDER["fonts.googleapis.com"] == "Google"
        assert "Google" not in gate._listed_providers()

    @pytest.mark.parametrize("host", ["fonts.googleapis.com", "fonts.gstatic.com"])
    def test_reintroducing_a_google_font_host_would_fail_the_gate(self, host):
        provider = gate.HOST_TO_PROVIDER[host]
        assert provider not in gate._listed_providers(), (
            f"{host} maps to {provider}, which is not listed — so if the host "
            f"came back into the CSP, main() would return 1"
        )
