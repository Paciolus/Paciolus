# Phase X Guardrail Checks — CI/CD Reference

> These grep checks enforce the AccountingExpertAuditor's 8 non-negotiable conditions.
> Add to CI pipeline to prevent guardrail regressions.

## Guardrail 4: No Audit Terminology in Engagement UI

**Rule:** Engagement components and pages must not use audit opinion, risk assessment, or control testing language.

```bash
# Must return zero matches
rg -i "audit opinion|risk assessment|control testing" \
  frontend/src/components/engagement/ \
  frontend/src/app/engagements/
```

**Last verified:** Sprint 102 (2026-02-08) — PASS (zero matches)

## Guardrail 6: No Composite Engagement Scoring

**Rule:** Engagement routes must not aggregate per-tool scores into an engagement-level composite risk score.

```bash
# Must return zero matches (excluding per-tool-run field definitions)
rg -i "engagement.*risk.*score" backend/routes/engagements.py
```

**Note:** `composite_score` on `ToolRunResponse` is a per-tool-run field (individual tool's native composite score, e.g., AP testing composite). This is NOT an engagement-level aggregate and is compliant with the guardrail. The guardrail prohibits `engagement_risk_score` or similar aggregation across tools.

**Last verified:** Sprint 102 (2026-02-08) — PASS

## Guardrail 1: No ISA 265 Structure

**Rule:** Anomaly summary and engagement exports must not contain ISA 265 classification terms.

```bash
# Must return zero matches
rg -i "Material Weakness|Significant Deficiency|Control Environment Assessment|Management Letter" \
  backend/anomaly_summary_generator.py \
  backend/engagement_export.py
```

**Last verified:** Sprint 101/102 — PASS

## Guardrail 5: Non-Dismissible Disclaimers

**Rule:** All engagement-related pages and exports must include non-dismissible disclaimer banners.

**Manual check locations:**
- `frontend/src/app/engagements/page.tsx` — Page-level disclaimer banner
- `frontend/src/components/engagement/FollowUpItemsTable.tsx` — Follow-up tab disclaimer
- `backend/anomaly_summary_generator.py` — PDF disclaimer (DISCLAIMER_TEXT constant)
- `backend/shared/memo_base.py` — Memo disclaimer (build_disclaimer function)

## Guardrail 2: Narratives Only in Follow-Up Items

**Rule:** Follow-up items table must not have columns for account numbers, monetary amounts, or PII.

```bash
# Must return zero matches in follow-up model
rg -i "account_number|amount|balance|debit|credit" \
  backend/follow_up_items_model.py
```

**Last verified:** Sprint 99/102 — PASS
