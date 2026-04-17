# Sprints 604–607 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-14.

---

### Sprint 604: Remove ISA/PCAOB "Compliant" Marketing Overclaim
**Status:** COMPLETE
**Source:** Scout + Accounting Auditor — legal-risk marketing copy
**File:** `frontend/src/app/(marketing)/demo/page.tsx`, `frontend/src/components/marketing/ToolShowcase.tsx`, `frontend/src/components/marketing/ToolSlideshow.tsx`, `frontend/src/components/jeTesting/SamplingPanel.tsx`, `frontend/src/__tests__/SamplingPanel.test.tsx`
**Problem:** Three marketing surfaces + one in-product header asserted "ISA 530 / PCAOB AS 2315 compliant MUS and random sampling". AICPA/PCAOB do not certify software — "compliant" implies third-party assessment, or that using the tool satisfies the standard. Malpractice exposure.

**Changes:**
- [x] `demo/page.tsx`, `ToolShowcase.tsx`, `ToolSlideshow.tsx` — replaced "ISA 530 / PCAOB AS 2315 compliant MUS…" with "MUS and random sampling with Stringer bounds — designed to support ISA 530 / PCAOB AS 2315 procedures"
- [x] `ToolSlideshow.tsx` — `valueProposition` swapped "ISA 530-compliant parameters" for "ISA 530 methodology parameters"
- [x] `SamplingPanel.tsx` (in-product panel header) — "PCAOB AS 2315 / ISA 530 compliant" → "Per PCAOB AS 2315 / ISA 530 methodology"
- [x] `SamplingPanel.test.tsx` — assertion updated to the new string

**Review:**
- Grep for `(ISA|PCAOB|AS) \\d+ compliant` patterns in `frontend/src` now returns zero matches
- `npm run build` clean; `npx jest SamplingPanel` passes with the new assertion

---

### Sprint 605: Remove ISA 265 Deficiency Classification From Anomaly PDF
**Status:** COMPLETE
**Source:** Accounting Auditor — assurance-adjacent guardrail violation
**File:** `backend/anomaly_summary_generator.py`
**Problem:** The generator emitted a "Deficiency Classification" checkbox block (Control Deficiency / Significant Deficiency / Material Weakness / Inconclusive) and an aggregate summary table on every anomaly response — directly contradicting the file's own GUARDRAIL 3 at line 17. ISA 265 deficiency classification is auditor-judgment-only; the platform must not imply it delivers this output.

**Changes:**
- [x] `anomaly_summary_generator.py` — deleted the deficiency classification checkbox row from the per-anomaly response table
- [x] `anomaly_summary_generator.py` — deleted the "Aggregate Deficiency Classification Summary (DRAFT)" section and the 5-row classification table
- [x] Replaced the row with a free-text "Practitioner Classification Notes" field that explicitly reminds the reader that classification is auditor judgment
- [x] Removed the now-meaningless "Deficiency Classifications Made: 0" line from Section III header
- [x] Rephrased `DISCLAIMER_TEXT` — no longer promises "all deficiency classifications" from the practitioner in the assessment section; states classification is outside report scope

**Review:**
- `pytest tests/test_anomaly_summary.py` — 17 passed (no snapshots to update; existing `test_no_isa_265_sections` guardrail still passes because forbidden terms never appear in updated `DISCLAIMER_TEXT` with the casing the test checks)
- Guardrail 3 is now enforced by the code, not just the docstring

---

### Sprint 606: Rename "Assurance Center" → Trust Center
**Status:** COMPLETE
**Source:** Accounting Auditor — regulated-term drift
**File:** `frontend/src/app/(marketing)/trust/page.tsx`
**Problem:** The trust page `<h1>` was "Assurance Center". In professional-services context this is a regulated term; a regulator or peer could read it as the platform claiming to deliver assurance services. The subtitle mitigation further down the page did not appear on the same visual element as the heading, so the initial read was the overclaim.

**Changes:**
- [x] `trust/page.tsx` — `<h1>Assurance Center</h1>` → `<h1>Trust Center</h1>`

**Review:**
- Grep across `frontend/src` confirms zero remaining "Assurance Center" strings (matches only appear in `.next/` build output and `coverage/`, both regenerated)
- `npm run build` clean

---

### Sprint 607: Internal Admin Canonical IP Helper
**Status:** COMPLETE
**Source:** Critic — audit log forgery risk
**File:** `backend/routes/internal_admin.py`, `backend/tests/test_internal_admin.py`
**Problem:** `internal_admin.py` defined its own `_get_client_ip` that blindly trusted `X-Forwarded-For`, bypassing the `TRUSTED_PROXY_IPS` check in `security_middleware.get_client_ip`. Every admin audit log entry (plan_override, refund, impersonation, force-cancel, session revoke, dunning resolve, impersonation start) therefore carried a forgeable IP — an attacker with superadmin credentials could spoof the source IP on every audit entry.

**Changes:**
- [x] `routes/internal_admin.py` — deleted the local `_get_client_ip` helper, imported the canonical `get_client_ip` from `security_middleware`, rewrote all 8 audit-log call-sites to use it
- [x] `tests/test_internal_admin.py` — new `test_sprint_607_uses_proxy_aware_ip_helper` regression asserts `internal_admin.get_client_ip is security_middleware.get_client_ip` and that the old `_get_client_ip` no longer exists on the module

**Review:**
- `pytest tests/test_internal_admin.py` — 35 passed (regression included)
- `security_middleware.get_client_ip` already has its own proxy-trust tests in `test_transport_hardening.py` — no need to duplicate IP-spoofing-through-middleware coverage here
- Admin audit log IP entries are now tamper-resistant end-to-end: only requests arriving from `TRUSTED_PROXY_IPS` can set the forwarded-for chain

---


---
