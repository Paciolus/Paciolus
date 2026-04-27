# Auditing Lexicon — Permitted vs. Forbidden Phrasing

**Owner:** Sprint 721, generated from the 2026-04-24 Accounting Methodology
Audit (Rank-2 boundary-language finding).

**Purpose:** Memo generators (`backend/*_memo_generator.py`) produce
workpaper-style PDFs that CPAs may include in their engagement files.
Language drift toward auditor-judgment territory exposes Paciolus to
ISA 265 boundary risk: the platform does *not* classify deficiencies,
quantify misstatements, or render attest opinions. It surfaces
quantitative signals; the auditor draws conclusions.

This lexicon is the canonical phrase allowlist / denylist for memo
language. It is enforced by CI test
`backend/tests/test_memo_boundary_phrasing.py`, which renders each
memo generator against synthetic engagement fixtures and fails on any
hit against the deny patterns.

---

## Allow (anomaly-indicator framing)

Use these constructions when describing what a test or signal reveals:

| Phrase | When to use |
|---|---|
| `anomaly indicator` | Generic catch-all for any quantitative flag |
| `data signal` | When the flag is purely arithmetic (e.g., flux variance) |
| `warrants inquiry` / `warrants further review` | Suggests CPA action without prescribing the outcome |
| `threshold breached` / `threshold deviation` | Numeric-comparison framing |
| `auditor judgment required to determine cause` | Explicit hand-off to the engagement team |
| `consider whether` | Open-ended prompt for the CPA |
| `flag` / `flagged` | Verb form; describes platform behavior |
| `ratio below configured threshold` | Quantitative-only; no inferred quality |
| `further inquiry into [estimate]` | Language used by ISA 540 itself |
| `coverage anomaly` / `concentration anomaly` | Numeric pattern descriptions |

## Deny (auditor-judgment framing — out of scope for an automated tool)

These constructions trigger the CI deny-pattern check. **Adding any of
them to a memo generator without an explicit allow-comment makes the
build fail.**

| Phrase | Why it's denied | Replacement |
|---|---|---|
| `deficiency` (in any inflection) | ISA 265 classification — auditor judgment | `anomaly indicator` |
| `material misstatement` / `misstatement` (as conclusion, not signal) | Quantification + opinion | `arithmetic discrepancy` |
| `control failure` / `control deficiency` | Control-design conclusion | `control-related signal warrants inquiry` |
| `should be` (prescriptive) | Tells the CPA what to do | `consider whether` |
| `recommended remediation` / `we recommend` | Advisory voice | `auditor may consider` |
| `is not adequate` / `is insufficient` | Sufficiency conclusion | `coverage anomaly indicator` |
| `understatement of [account]` (as conclusion) | Misstatement conclusion | `signal of potential understatement; auditor to investigate` |
| `systemic review … recommended` | Suggests root-cause conclusion | `auditor judgment required to determine cause` |
| `requires correction` / `must correct` | Directive | `warrants inquiry / further review` |
| `audit opinion` / `our opinion` / `we opine` | Attestation language | n/a — never use |
| `not in compliance with [standard]` | Compliance conclusion | `signal inconsistent with [standard] expectations` |

---

## Test allowlist exception

If a denied phrase legitimately appears in a memo (e.g., quoting a
standard's title, citing a reference document), wrap it in an explicit
inline annotation so the CI scan ignores it:

```python
# allow-deny-phrase: <reason>
text = "ISA 240 — The Auditor's Responsibilities Relating to Fraud (note: 'misstatement' here is the standard's own title, not a conclusion)"
```

The CI scanner skips any line carrying `# allow-deny-phrase:`.

---

## Sprint history

- **Sprint 721 (2026-04-25):** lexicon created. Two memos rephrased
  (`three_way_match_memo_generator.py` line 113, `ar_aging_memo_generator.py`
  line 34). CI test introduced.

## Adding a new memo generator?

1. Read this lexicon first.
2. Run `backend/tests/test_memo_boundary_phrasing.py` against your generator.
3. Any deny-pattern hit must either be rephrased per the table above
   or annotated `# allow-deny-phrase: <reason>`.
4. PR review will be on the *reason*, not the existence of the annotation.
