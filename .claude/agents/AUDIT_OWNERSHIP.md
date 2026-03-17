# Audit Ecosystem Ownership Boundaries

Defines scope, exclusions, and record-of-record status for each audit channel to prevent duplication.

| Channel | Scope | Does NOT Cover | Record of Record? |
|---------|-------|----------------|-------------------|
| **`/audit` (Project Auditor)** | Quick automated checks: lint baselines, test counts, build health, todo.md hygiene, stale references | Deep methodology review, ISA/PCAOB compliance, UI/UX quality | No — findings are ephemeral prompts for immediate action |
| **Digital Excellence Council (DEC)** | Comprehensive manual review: 9-agent council, cross-cutting quality (code, design, compliance, architecture), findings table with severity/ownership | Automated gate enforcement, CI check tuning, hook logic | **Yes — `reports/council-audit-*.md` is the remediation record of record** |
| **Accounting Expert Auditor** | ISA/PCAOB methodology correctness: report language, authoritative references, auditor-judgment boundaries, professional standards compliance | Code quality, UI design, CI pipelines, governance docs | No — findings feed into DEC or sprint backlog |
| **Audit journals / rolling summaries** | Historical narrative: what was done, when, why, lessons learned | Prescriptive findings or remediation tracking | No — informational archive only |

## Conflict Resolution

- If `/audit` and the DEC both flag the same issue, the DEC finding is canonical (higher-fidelity review).
- If the Accounting Expert Auditor flags a methodology issue, it is escalated to the next DEC round or handled as an immediate sprint item if severity warrants.
- Remediation is tracked in the DEC report's findings table until resolved. Sprint work references the DEC finding ID (e.g., `DEC F-042`).
