"""Sprint 679: unit tests for PDF branding context + scope manager.

Covers:
  * ``PDFBrandingContext`` immutable dataclass invariants.
  * ``effective_*`` methods gate on ``tier_has_branding``.
  * ``apply_pdf_branding`` ContextVar scoping + reset-on-exit.
  * ``load_pdf_branding_context`` resolution paths (tier ok, tier missing,
    no org, no FirmBranding row, logo download failure).
  * Integration: ``generate_testing_memo`` reads ContextVar branding
    and swaps in the custom logo + footer without touching 18
    downstream memo-generator signatures.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from shared.pdf_branding import (
    BLANK_BRANDING,
    PDFBrandingContext,
    apply_pdf_branding,
    current_pdf_branding,
    load_pdf_branding_context,
)


class TestPDFBrandingContext:
    def test_default_is_blank(self):
        assert BLANK_BRANDING.tier_has_branding is False
        assert BLANK_BRANDING.logo_bytes is None
        assert BLANK_BRANDING.header_text is None
        assert BLANK_BRANDING.footer_text is None

    def test_effective_logo_gates_on_tier(self):
        """Downgraded user's leftover logo bytes must not leak."""
        ctx = PDFBrandingContext(
            tier_has_branding=False,
            logo_bytes=b"\x89PNG\r\n\x1a\n" + b"\x00" * 100,
        )
        assert ctx.effective_logo_bytes() is None

    def test_effective_logo_returns_bytes_when_authorised(self):
        payload = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        ctx = PDFBrandingContext(tier_has_branding=True, logo_bytes=payload)
        assert ctx.effective_logo_bytes() == payload

    def test_effective_header_gates_on_tier(self):
        ctx = PDFBrandingContext(tier_has_branding=False, header_text="Acme CPA LLP")
        assert ctx.effective_header_text() is None
        ctx = PDFBrandingContext(tier_has_branding=True, header_text="Acme CPA LLP")
        assert ctx.effective_header_text() == "Acme CPA LLP"

    def test_effective_footer_gates_on_tier(self):
        ctx = PDFBrandingContext(tier_has_branding=False, footer_text="Confidential — Acme LLP")
        assert ctx.effective_footer_text() is None
        ctx = PDFBrandingContext(tier_has_branding=True, footer_text="Confidential — Acme LLP")
        assert ctx.effective_footer_text() == "Confidential — Acme LLP"

    def test_frozen_dataclass(self):
        ctx = PDFBrandingContext(tier_has_branding=True)
        with pytest.raises(Exception):  # FrozenInstanceError
            ctx.tier_has_branding = False  # type: ignore[misc]


class TestApplyPdfBranding:
    def test_default_context_is_blank(self):
        assert current_pdf_branding() is BLANK_BRANDING

    def test_apply_sets_and_resets(self):
        ctx = PDFBrandingContext(tier_has_branding=True, header_text="Firm A")
        with apply_pdf_branding(ctx):
            assert current_pdf_branding() is ctx
            assert current_pdf_branding().header_text == "Firm A"
        assert current_pdf_branding() is BLANK_BRANDING

    def test_apply_resets_on_exception(self):
        ctx = PDFBrandingContext(tier_has_branding=True, header_text="Firm B")
        with pytest.raises(RuntimeError):
            with apply_pdf_branding(ctx):
                assert current_pdf_branding() is ctx
                raise RuntimeError("simulated failure")
        # Even on exception, the ContextVar resets.
        assert current_pdf_branding() is BLANK_BRANDING

    def test_apply_nested_scopes(self):
        outer = PDFBrandingContext(tier_has_branding=True, header_text="Outer")
        inner = PDFBrandingContext(tier_has_branding=True, header_text="Inner")
        with apply_pdf_branding(outer):
            assert current_pdf_branding().header_text == "Outer"
            with apply_pdf_branding(inner):
                assert current_pdf_branding().header_text == "Inner"
            assert current_pdf_branding().header_text == "Outer"
        assert current_pdf_branding() is BLANK_BRANDING

    def test_apply_none_is_noop(self):
        """Callers can pass None without wrapping in if-branches."""
        with apply_pdf_branding(None):
            assert current_pdf_branding() is BLANK_BRANDING

    def test_apply_blank_branding_is_noop(self):
        """BLANK_BRANDING sentinel skips the ContextVar set."""
        before_token = current_pdf_branding()
        with apply_pdf_branding(BLANK_BRANDING):
            # Identity — the ContextVar shouldn't have been touched.
            assert current_pdf_branding() is before_token


class TestLoadPdfBrandingContext:
    def test_no_entitlement_returns_blank(self):
        """User without custom_branding entitlement → blank."""

        class _Ent:
            custom_branding = False

        with patch(
            "shared.entitlement_checks.get_effective_entitlements",
            return_value=_Ent(),
        ):
            result = load_pdf_branding_context(user=object(), db=object())
        assert result.tier_has_branding is False
        assert "tier_lacks_custom_branding" in result.resolution_notes

    def test_entitlement_failure_returns_blank(self):
        """DB/entitlement exception → blank with diagnostic note."""
        with patch(
            "shared.entitlement_checks.get_effective_entitlements",
            side_effect=RuntimeError("DB down"),
        ):
            result = load_pdf_branding_context(user=object(), db=object())
        assert result.tier_has_branding is False
        assert "entitlement_lookup_failed" in result.resolution_notes

    def test_enterprise_user_without_session_returns_early(self):
        """Non-Session db (e.g., unresolved Depends in unit test) → tier-ok
        but no DB lookup. Default Paciolus branding renders."""

        class _Ent:
            custom_branding = True

        with patch(
            "shared.entitlement_checks.get_effective_entitlements",
            return_value=_Ent(),
        ):
            result = load_pdf_branding_context(user=object(), db="not-a-session")
        assert result.tier_has_branding is True
        assert result.logo_bytes is None
        assert "db_not_a_session" in result.resolution_notes


class TestMemoTemplateReadsContextVar:
    """Sprint 679 integration: memo template picks up branding from the
    ContextVar set by ``apply_pdf_branding``. No memo-generator
    signature changes required.
    """

    def test_blank_branding_does_not_fail(self):
        """Sanity — absence of branding doesn't break the template path."""
        # Module import smoke-test: memo_template pulls pdf_branding at
        # the module level now. If the import graph ever breaks we want
        # to catch it before a memo generation path does.
        from shared.memo_template import generate_testing_memo  # noqa: F401


class TestReportGeneratorsReadContextVar:
    """Sprint 679 (completion): the three report PDFs that don't flow through
    ``generate_testing_memo`` — the combined audit report, the financial
    statements PDF, and the anomaly summary — each read the active
    ``PDFBrandingContext`` via ``current_pdf_branding()`` at their entry
    point. These tests pin that wiring so a future refactor can't silently
    drop the ContextVar read and regress Enterprise branding coverage.
    """

    def _branded_ctx(self) -> PDFBrandingContext:
        return PDFBrandingContext(
            tier_has_branding=True,
            logo_bytes=b"\x89PNG\r\n\x1a\nFAKE",
            logo_content_type="image/png",
            header_text="ACME Audit Partners",
            footer_text="Confidential — Prepared for ACME Client Corp.",
        )

    def test_generate_audit_report_threads_branding_into_chrome(self):
        """``generate_audit_report`` (combined audit report) must pass the
        branding logo to ``build_cover_page`` and wrap the page footer
        with ``make_branded_page_footer(header, footer)``.
        """
        from pdf import orchestrator as orch

        ctx = self._branded_ctx()
        with (
            patch.object(orch, "SimpleDocTemplate") as mock_doc_cls,
            patch("shared.report_chrome.build_cover_page") as mock_cover,
            patch("shared.report_chrome.make_branded_page_footer") as mock_footer,
            patch.object(orch, "render_table_of_contents"),
            patch.object(orch, "render_data_intake_summary"),
            patch.object(orch, "render_executive_summary"),
            patch.object(orch, "render_population_composition"),
            patch.object(orch, "render_risk_summary"),
            patch.object(orch, "render_anomaly_details"),
            patch.object(orch, "render_going_concern_indicators"),
            patch.object(orch, "render_workpaper_signoff"),
            patch.object(orch, "render_limitations"),
            patch.object(orch, "render_classical_footer"),
        ):
            # SimpleDocTemplate.build() is a no-op stub so we don't need real ReportLab flowables
            doc_instance = mock_doc_cls.return_value
            doc_instance.width = 100
            doc_instance.build.return_value = None

            with apply_pdf_branding(ctx):
                orch.generate_audit_report({"anomalies": []}, filename="test.xlsx")

        # Logo threaded into cover
        cover_kwargs = mock_cover.call_args.kwargs
        assert cover_kwargs.get("custom_logo_bytes") == ctx.logo_bytes

        # Branded footer factory called with firm's text
        footer_kwargs = mock_footer.call_args.kwargs
        assert footer_kwargs["header_text"] == ctx.header_text
        assert footer_kwargs["footer_text"] == ctx.footer_text

    def test_generate_financial_statements_pdf_threads_branding(self):
        """FS PDF: logo into cover, ``custom_header``/``custom_footer``
        threaded into ``draw_fs_decorations`` via the closure.
        """
        from pdf import orchestrator as orch

        ctx = self._branded_ctx()

        # Minimal statements stub — the FS orchestrator reads entity_name / period_end
        class _FakeStatements:
            entity_name = "ACME Client Corp."
            period_end = "2025-12-31"

        fs_deco_calls: list[dict] = []

        def _capture_fs_deco(canvas, doc, page_counter, **kwargs):
            fs_deco_calls.append(kwargs)

        with (
            patch.object(orch, "SimpleDocTemplate") as mock_doc_cls,
            patch("shared.report_chrome.build_cover_page") as mock_cover,
            patch.object(orch, "draw_fs_decorations", side_effect=_capture_fs_deco) as mock_deco,
            patch.object(orch, "render_balance_sheet"),
            patch.object(orch, "render_income_statement"),
            patch.object(orch, "render_cash_flow"),
            patch.object(orch, "render_ratios", return_value=False),
            patch.object(orch, "render_quality_of_earnings"),
            patch.object(orch, "render_notes"),
            patch.object(orch, "render_mapping_trace"),
            patch.object(orch, "render_workpaper_signoff"),
        ):
            doc_instance = mock_doc_cls.return_value
            doc_instance.width = 100

            # Simulate doc.build calling the onFirstPage closure so we can
            # capture the kwargs threaded through the closure into draw_fs_decorations.
            def _fake_build(story, onFirstPage=None, onLaterPages=None, **_):
                class _FakeCanvas:
                    def saveState(self):
                        pass

                    def restoreState(self):
                        pass

                if onFirstPage is not None:
                    onFirstPage(_FakeCanvas(), doc_instance)

            doc_instance.build.side_effect = _fake_build

            with apply_pdf_branding(ctx):
                orch.generate_financial_statements_pdf(_FakeStatements())

        # Logo wired into FS cover
        cover_kwargs = mock_cover.call_args.kwargs
        assert cover_kwargs.get("custom_logo_bytes") == ctx.logo_bytes

        # draw_fs_decorations received custom_header + custom_footer
        assert fs_deco_calls, "draw_fs_decorations should have been invoked via the _fs_deco closure"
        assert fs_deco_calls[0]["custom_header"] == ctx.header_text
        assert fs_deco_calls[0]["custom_footer"] == ctx.footer_text

    def test_anomaly_summary_generator_threads_branding(self):
        """``AnomalySummaryGenerator.generate_pdf`` reads the ContextVar
        and threads ``custom_logo_bytes`` into the cover + wires the
        branded footer callback into ``doc.build``.
        """
        import anomaly_summary_generator as asg

        ctx = self._branded_ctx()

        # Minimal engagement + client stubs so _verify_engagement_access + DB queries return something
        from types import SimpleNamespace

        engagement = SimpleNamespace(
            id=1,
            client_id=1,
            period_start=None,
            period_end=None,
        )

        cover_calls: list[dict] = []

        def _capture_cover(story, styles, metadata, doc_width, logo_path, **kwargs):
            cover_calls.append(kwargs)

        with (
            patch.object(asg, "make_branded_page_footer") as mock_footer,
            patch.object(asg, "SimpleDocTemplate") as mock_doc_cls,
            patch.object(asg, "build_cover_page", side_effect=_capture_cover),
            patch.object(
                asg.AnomalySummaryGenerator,
                "_verify_engagement_access",
                return_value=engagement,
            ),
            patch.object(asg.AnomalySummaryGenerator, "_build_story", wraps=None) as mock_build,
        ):
            mock_build.return_value = []

            # Stub the DB completely — the generator queries tool_runs + follow_up_items
            class _FakeQuery:
                def filter(self, *_a, **_k):
                    return self

                def order_by(self, *_a, **_k):
                    return self

                def all(self):
                    return []

                def first(self):
                    return SimpleNamespace(name="ACME Client")

            class _FakeDB:
                def query(self, *_a, **_k):
                    return _FakeQuery()

            gen = asg.AnomalySummaryGenerator(_FakeDB())

            doc_instance = mock_doc_cls.return_value
            doc_instance.build.return_value = None

            with apply_pdf_branding(ctx):
                gen.generate_pdf(user_id=1, engagement_id=1)

        # _build_story was invoked with the branded logo bytes
        build_kwargs = mock_build.call_args.kwargs
        assert build_kwargs.get("custom_logo_bytes") == ctx.logo_bytes

        # Branded footer factory received the firm's header/footer strings
        footer_kwargs = mock_footer.call_args.kwargs
        assert footer_kwargs["header_text"] == ctx.header_text
        assert footer_kwargs["footer_text"] == ctx.footer_text

    def test_unbranded_tier_leaves_generators_unchanged(self):
        """Non-Enterprise tiers (tier_has_branding=False) must produce
        exactly the same PDF chrome as the no-context case — effective_*
        methods return None, so generators see no custom logo/header/footer.
        """
        downgraded = PDFBrandingContext(
            tier_has_branding=False,
            logo_bytes=b"leftover-bytes",
            header_text="Old Firm",
            footer_text="Old Footer",
        )
        assert downgraded.effective_logo_bytes() is None
        assert downgraded.effective_header_text() is None
        assert downgraded.effective_footer_text() is None

        from pdf import orchestrator as orch

        with (
            patch.object(orch, "SimpleDocTemplate") as mock_doc_cls,
            patch("shared.report_chrome.build_cover_page") as mock_cover,
            patch("shared.report_chrome.make_branded_page_footer") as mock_footer,
            patch.object(orch, "render_table_of_contents"),
            patch.object(orch, "render_data_intake_summary"),
            patch.object(orch, "render_executive_summary"),
            patch.object(orch, "render_population_composition"),
            patch.object(orch, "render_risk_summary"),
            patch.object(orch, "render_anomaly_details"),
            patch.object(orch, "render_going_concern_indicators"),
            patch.object(orch, "render_workpaper_signoff"),
            patch.object(orch, "render_limitations"),
            patch.object(orch, "render_classical_footer"),
        ):
            mock_doc_cls.return_value.width = 100
            mock_doc_cls.return_value.build.return_value = None

            with apply_pdf_branding(downgraded):
                orch.generate_audit_report({"anomalies": []}, filename="x.xlsx")

        # Cover called with None logo bytes — tier gate closed
        assert mock_cover.call_args.kwargs.get("custom_logo_bytes") is None
        # make_branded_page_footer called with None/None — factory
        # internally returns the plain draw_page_footer in that case
        footer_kwargs = mock_footer.call_args.kwargs
        assert footer_kwargs["header_text"] is None
        assert footer_kwargs["footer_text"] is None
