# Paciolus Website Review

**Date:** 2026-11-14
**Scope:** Marketing pages (`frontend/src/app/(marketing)/*`, `components/marketing/*`, `components/trust/*`, `components/demo/*`, `components/pricing/*`, `content/*`, `domain/pricing.ts`, marketing CSS in `app/globals.css`). The logged-in app (`app/tools`, `app/(workspace)`, `app/(auth)`, `app/settings`, `components/*`) was reviewed only for wording and continuity.
**Method:** I read the code directly. I searched case-insensitively for every "avoid" term and its variants (zero storage / zero-storage / ZeroStorage, never stored / not written to disk, findings, passed / clean / verified, intelligent / AI, SOC / ISO / GDPR, and so on). I viewed the background images. I checked the share-link TTL (`backend/routes/export_sharing.py`: 24h Professional / 48h Enterprise) and the sign-off default (`backend/shared/memo_base.py`: off unless `include_signoff=True`).

> **Addendum, 2026-11-14 (after CEO review).** All recommendations were approved under one rule: what we can't prove gets removed. The work is filed as Sprints 861–865 in `tasks/todo.md`.
>
> **Facts checked in the code**
> - Shared links store the whole export file.
> - The 10-minute cache applies only to the preview and workbook-inspection flow.
> - Summaries are archived after 365 days, not deleted.
> - Flagged account names can include a person's name.
> - Our code does not encrypt shared exports.
>
> **Checked on the live site**
> - `/security` and `/subprocessors` return 404.
> - The Trust page links none of the Security Policy, Subprocessor List or architecture document, although all three exist and are current in `docs/04-compliance/`.
> - `/status` is public and shows "25/25 Passed" from hard-coded results.
> - The Trust page count-up loads showing "2 Security Controls / 1 Control Domains".
>
> **Changes to earlier recommendations**
> - Questions Q2, Q3, Q7 and Q9–Q13 were decided in favor of the safest option.
> - Where this report proposes replacement copy that names a standard or makes a speed claim, the Sprint 861 entry supersedes it: no standard names on marketing pages, and no speed claims.

**Map of where copy lives**

| Surface | Source of copy |
|---|---|
| Homepage | `app/(marketing)/page.tsx` → `components/marketing/hero/*`, `ToolLedger`, `FeaturePillars`, `ProcessTimeline`, `EvidenceBand`, `BottomProof` → `StandardsSpecimen` |
| Trust | `app/(marketing)/trust/page.tsx` + **`content/trust.ts`** (all lists) + `components/trust/*` |
| About / Approach / Demo / Pricing / Sources / Contact | inline in each `page.tsx`; pricing tiers and FAQ in `domain/pricing.ts`; demo mocks in `components/marketing/DemoTabExplorer.tsx` |
| Shared data-handling sentence | `content/storage-statement.ts` (`UPLOAD_HANDLING`, `WHAT_WE_KEEP`, `STORAGE_STATEMENT`) |
| Disclaimers | `content/disclaimers.ts` |
| Page metadata | `app/layout.tsx`, `app/(marketing)/*/layout.tsx` |
| Tool catalog / standards chips | `content/tool-ledger.ts`, `content/standards-specimen.ts` |
| Palette | `frontend/tailwind.config.js` (obsidian `#212121`, oatmeal `#EBE9E4`, clay `#BC4749`, sage `#4A7C59`, plus scarcity-scoped brass `#B08D57`) |

Effort key: **S** = copy edit · **M** = component change · **L** = new page or asset.

---

## 1. Inaccurate or risky claims

### 1.1 Security and certification

**R-01 · SOC 2 Type II is shown with an "Available" badge (highest priority)**
- **Where:** `content/trust.ts:177-183` (SOC 2 entry, `status: 'planned'`), rendered by `components/trust/ComplianceTimeline.tsx:20-24`, which maps `planned` to the label **"Available"**. It appears under the Trust page section headed "Independent Attestation" / "Compliance Roadmap" (`app/(marketing)/trust/page.tsx:215-223`).
- **Now:** A card titled "SOC 2 Type II" with a status pill reading "Available". The small print says "No SOC 2 audit has been performed and none is currently scheduled."
- **Why:** Security avoid list: "Any statement or badge implying SOC 1, SOC 2…" and "SOC 2 planned / SOC 2 ready". A reader skimming the badge sees "SOC 2 Type II — Available". A "Compliance Roadmap" that includes SOC 2 also implies the examination is planned, which contradicts the fixed fact that none is scheduled.
- **Change:** Delete the SOC 2 milestone and the whole "Compliance Roadmap" timeline. Replace it with a plain text block, no badges:
  > **Certifications.** Paciolus holds no SOC 1, SOC 2, ISO 27001 or other third-party certification, and does not claim one. What we do is described in our Security Policy, our architecture document and our Subprocessor List.
  Link the three documents once their URLs are final (**dependency:** these documents are being updated, so do not guess the URLs). Also drop the "Independent Attestation" meta label (`trust/page.tsx:217`) and the subtitle "independent attestation progress" (`:219`).
- **Effort:** M

**R-02 · Self-awarded "Compliant" badges for GDPR and CCPA**
- **Where:** `content/trust.ts:157-170` (`status: 'compliant'`), rendered as a sage "Compliant" pill (`ComplianceTimeline.tsx:10-14`). Footnote at `ComplianceTimeline.tsx:143`: "GDPR and CCPA compliance reflects our self-assessed posture…"
- **Now:** "GDPR — Compliant" and "CCPA — Compliant" pills, each with "Self-assessed — no third-party audit" in small italics.
- **Why:** Security avoid list: "Self-awarded 'GDPR compliant' or 'CCPA compliant' badges." The small print does not undo the badge.
- **Change:** Remove the pills. In the text block that replaces the timeline (R-01), add:
  > **Privacy law.** Our Privacy Policy explains how we handle requests under GDPR and the CCPA/CPRA, including access, deletion and breach notification.
  Link `/privacy`.
- **Effort:** S (falls out of R-01)

**R-03 · The DPA is labelled "Available" while the text says it is being finalized**
- **Where:** `content/trust.ts:171-176` (`status: 'planned'` → "Available"); `:237`.
- **Now:** "DPA — Available" pill, with detail text "being finalized with counsel. Available on request in the meantime."
- **Why:** The badge and the sentence contradict each other. The DPA strong-fit element calls for an accurate availability statement.
- **Change:** Use one line: "Data Processing Addendum: available on request while counsel finalizes it." Link Contact. Remove the badge. (**Needs input from Paciolus:** when the DPA is final, say whether it will be downloadable or still by request.)
- **Effort:** S

**R-04 · "SOC 1" appears as a standards chip on the homepage tool ledger**
- **Where:** `content/tool-ledger.ts:164` (`standards: ['SOC 1', 'COSO 2013']`) for Segregation of Duties, rendered as a pill in `components/marketing/ToolLedger.tsx:161-170` on the homepage.
- **Now:** A rounded "SOC 1" pill beside a Paciolus tool, styled like the other standards chips.
- **Why:** Security avoid list: "Any statement or badge implying SOC 1…". Out of context, a "SOC 1" pill on a vendor homepage reads as a certification badge. The app's SoD page (`app/tools/sod/page.tsx:116`) explains that the analysis "can support SOC 1 or SOX 404 work", but the homepage gives no such context.
- **Change:** On marketing surfaces, change the SoD chips to `['COSO 2013']`. Keep the SOC 1 explanation on the Sources page and inside the tool. The Sources page lists AICPA "SOC" prefixes via `content/authorities.ts:49`, which is acceptable because it is a citation list.
- **Effort:** S

**R-05 · The Trust page hero promises "the evidence to prove it"**
- **Where:** `app/(marketing)/trust/page.tsx:33-35`.
- **Now:** "How we protect your data — and the evidence to prove it."
- **Why:** Everything on the page is self-described, with no independent evidence. Skeptical readers take "evidence" literally. Rule: claims must be backed by something the reader can check.
- **Change:** "How we protect your data, what we keep, and the documents you can check."
- **Effort:** S

**R-06 · Unverifiable absolutes in the security control list**
- **Where:** `content/trust.ts:153` ("No PII in logs"); `content/trust.ts:202` ("Immediate isolation of affected systems to prevent lateral movement"); `components/trust/ArchitectureDiagram.tsx:215` ("No client PII in analysis results").
- **Why:** These are absolute claims with nothing the reader can check. Two of them are doubtful on the facts. Flagged account names are stored, and some tools flag names: payroll's duplicate-name test flags employees, and AP and 1099 flag vendors. "Immediate isolation" also sits badly beside the page's own honest statement that "there is no 24/7 on-call; incidents are handled by the founder" (`trust.ts:191`).
- **Change:**
  - `:153` → "Request-ID correlated logs with error output sanitized; we design logging to exclude personal data." (**Needs input from Paciolus:** confirm whether any PII can reach logs or Sentry.)
  - `:202` → "Affected credentials and sessions are revoked and the affected service is taken offline while we investigate."
  - `ArchitectureDiagram.tsx:215` → delete "No client PII in analysis results" unless engineering confirms that flagged names can never be personal names (**needs input from Paciolus**).
- **Effort:** S

**R-07 · A control is mapped to "PCAOB AS 1215"**
- **Where:** `content/trust.ts:149` (Optional Sign-Off Block → `standard: 'PCAOB AS 1215'`), shown in the Trust control matrix.
- **Why:** AS 1215 sets duties for audit firms, not software vendors. Mapping a Paciolus "control" to it implies Paciolus satisfies part of AS 1215, and it names the standard outside the one allowed context (a direct Trust/FAQ question, with AU-C 230 first).
- **Change:** Remove the standard reference (`standard: '—'`), or move the item out of the security-control matrix. Sign-off lines are a memo layout option, not a security control.
- **Effort:** S

### 1.2 Audit and professional claims

**R-08 · The homepage names PCAOB AS 1215 and says it "governs every memo/export"**
- **Where:** `content/standards-specimen.ts:93-97`, rendered on the homepage by `StandardsSpecimen` inside `BottomProof`.
- **Now:** "PCAOB AS 1215 — Audit documentation — content, completion, and retention requirements (governs every memo/export, not a procedure standard)."
- **Why:** This breaks two rules at once. Marketing pages "do not name standards" in the documentation-duty context, and AU-C 230 / AS 1215 may be named only on the Trust/FAQ page in answer to a direct question. "Governs every memo/export" also reads as a claim that Paciolus outputs conform to AS 1215, a duty that belongs to the firm.
- **Change:** Delete the AS 1215 entry from the specimen. In its place, add one line under the specimen with the required wording: "Paciolus exports are not a substitute for your firm's audit documentation and retention obligations." Then answer the question on the Trust FAQ (see S-09).
- **Effort:** S

**R-09 · The hero shows a "3 findings" badge**
- **Where:** `components/marketing/hero/HeroFilmFrame.tsx:352`.
- **Now:** A clay pill reading "3 findings" with a warning-triangle icon.
- **Why:** Audit avoid list: "Findings." The site's own disclaimer says results are "not findings or conclusions" (`content/disclaimers.ts:20`), so the hero contradicts it.
- **Change:** "3 items flagged". The summary line at `:362` already uses that wording.
- **Effort:** S

**R-10 · "Every export cites the governing standard"**
- **Where:** `components/marketing/EvidenceBand.tsx:339-342` (cell "ISA · PCAOB · ASC / Per-Memo Citations / Every export cites the governing standard").
- **Why:** "Governing" implies the cited standard governs Paciolus's output. The project's own claims review says memos cite the standards their tests draw on, and Excel and CSV exports do not carry citations. The claim is overstated.
- **Change:** Label: "Per-test citations". Sub: "Each PDF memo cites the standard each test draws on, or marks the threshold as a Paciolus convention." Link it to `/sources`, which makes the claim checkable.
- **Effort:** S

**R-11 · "Workpaper-ready CSV"**
- **Where:** `app/tools/bank-rec/page.tsx:360` (app).
- **Why:** This is a near variant of "Ready to attach to workpapers," which is on the audit avoid list.
- **Change:** "Export matched items, outstanding deposits, outstanding checks and the reconciliation summary to CSV for your review."
- **Effort:** S

**R-12 · "Formatted for your working papers / workpapers" and "review and file"**
- **Where:** `about/page.tsx:27` ("Exports … formatted for your working papers, after your review"), `:58` ("Formatted for Your Workpapers"), `:274` ("Formatted for your working papers after your review"); `hero/HeroProductFilm.tsx:99` ("exports you can review and file"); `about/page.tsx:310` ("import them directly into your working paper system — whether that's CaseWare, TeamMate…").
- **Why:** These are softer than "ready to attach to workpapers", but they lean the same way. They also miss the approved division-of-responsibility wording. The CaseWare/TeamMate sentence claims an import path nobody has verified.
- **Change:** Replace the About "Where Paciolus fits" paragraph (`:309-311`) with the approved text: "Paciolus produces PDF memos and Excel/CSV workpapers. Your firm keeps them in its own documentation system; Paciolus is not a workpaper archive." Keep CaseWare/TeamMate only if tested (**needs input from Paciolus**). Hero subline: "Drop your trial balance. Get flags that cite the standards they draw on, and PDF and Excel exports for your review."
- **Effort:** S

**R-13 · App tables say "All tests returned clean results"**
- **Where:** Empty state in seven tables: `components/apTesting/FlaggedPaymentTable.tsx:57`, `arAging/FlaggedARTable.tsx:52`, `fixedAssetTesting/FlaggedFixedAssetTable.tsx:52`, `inventoryTesting/FlaggedInventoryTable.tsx:62`, `jeTesting/FlaggedEntryTable.tsx:60`, `payrollTesting/FlaggedEmployeeTable.tsx:57`, `revenueTesting/FlaggedRevenueTable.tsx:52`.
- **Why:** Audit avoid list: "'Passed,' 'clean,' or 'verified' as test results." The required wording is "no exceptions flagged."
- **Change:** "No exceptions flagged. No flag does not mean nothing is wrong; see the results disclaimer above." The simplest fix is a shared constant in `content/disclaimers.ts`.
- **Effort:** S

**R-14 · App score card is headed "Top Findings"**
- **Where:** `components/shared/testing/TestingScoreCard.tsx:178` (used by every testing tool). The prop name `findings_renderer` and the API field `top_findings` are internal and can stay.
- **Change:** "Top flagged items".
- **Effort:** S

### 1.3 Data-handling claims

**R-15 · Hero: "Zero data retained."**
- **Where:** `components/marketing/hero/HeroProductFilm.tsx:105`.
- **Now:** "Professional-grade analysis across 18 testing tools. Zero data retained."
- **Why:** This is the most visible data claim on the site, and it is false. You retain accounts, client lists, summaries, flagged account names, engagement workpapers and shared exports. It is the "Zero-Storage" promise in different words, and it falls under "nothing retained" / "no data is stored".
- **Change:** "18 tools. Your uploaded files are processed in memory and not kept after analysis. *See what we keep →*" (link to the "what we keep" page; see S-06).
- **Effort:** S

**R-16 · Trust page: "Zero Raw Data Stored", "Zero raw data persisted", "What We NEVER Store"**
- **Where:** `trust/page.tsx:54-55` (metrics bar "Zero / Raw Data Stored"), `:193` (subtitle "Four stages. Every control documented. Zero raw data persisted."), `:166` (heading "What We NEVER Store"). The same heading appears at `approach/page.tsx:288` ("What We Store vs What We Never Store") and `:326`.
- **Why:** These are "Zero-…" and "never" absolutes. Shared exports are stored for up to 24 or 48 hours. If an Excel export contains "full underlying data" (`FeaturePillars.tsx:289`) or "raw flagged data" (`DemoTabExplorer.tsx:213`), raw rows are stored for that window. See Question Q1.
- **Change:** Remove the "Zero" metric. Make the subtitle "Four stages, and what each one keeps." Rename both "NEVER" headings to "What We Don't Keep" and add a footnote under the list: "Exception: a report you share by link is stored with our storage provider for up to 24 hours (Professional) or 48 hours (Enterprise), then deleted."
- **Effort:** S

**R-17 · "Data destroyed after processing" and other instant-deletion wording**
- **Where:**
  - `components/trust/ArchitectureDiagram.tsx:197`: "Data destroyed after processing" (with a trash-can icon)
  - `content/trust.ts:121, 152`: "Uploaded data is released from memory after every analysis operation completes"
  - `approach/page.tsx:43, 57`: "released from memory" "when the response completes"
  - `approach/page.tsx:74`: "Uploaded file: the length of the request"
  - `approach/page.tsx:187`: "Entire lifecycle: <5 seconds"
  - `FeaturePillars.tsx:261`, `EvidenceBand.tsx:348`, `ArchitectureDiagram.tsx:33`: "processed in memory, then released"
- **Why:** Avoid list: "Wording that implies uploaded files are deleted instantly." Fixed fact: uploads are cached in memory for up to 10 minutes so a tool can reuse them. "Data destroyed" is also broader than uploads, since summaries persist. "<5 seconds" for the entire lifecycle is false whenever the cache applies.
- **Change:**
  - Diagram label: "Uploaded file released from memory (cached up to 10 minutes for reuse)".
  - Approach step 4: "The uploaded file stays in memory for up to 10 minutes so another tool can reuse it, then is released. A summary is saved to your history."
  - Comparison row: "Uploaded file: in memory only, up to 10 minutes".
  - Delete "Entire lifecycle: <5 seconds".
  - Replace "then released" taglines with "Processed in memory. Not kept after analysis."
  - (See Q5: Privacy says the 10-minute cache applies only to previewed PDFs/workbooks. Confirm which statement is correct before publishing.)
- **Effort:** S

**R-18 · "Never saved" / "not written to disk"**
- **Where:**
  - `components/marketing/FeaturePillars.tsx:263`: "the ledger rows in them are never saved"
  - `about/page.tsx:199-200`: "the ledger rows, invoices and payroll records in them are never saved"
  - `approach/page.tsx:79`: "Uploaded files are never kept"
  - `approach/page.tsx:111`: "uploaded ledger rows were never kept"
  - `privacy/page.tsx:340`: "(it is not written to disk)"
  - `privacy/page.tsx:373`: "are not written to disk"
- **Why:** Avoid list: "Never written to disk" and the "never" family. These are false for shared exports that contain line-level rows (Q1). "Not written to disk" is also hard to stand behind on hosted infrastructure, where swap and memory dumps are outside your control.
- **Change:** Use the approved sentence verbatim wherever these appear: "Your uploaded files are processed in memory and not kept after analysis. We save your account, client list, analysis summaries and anything you enter in an engagement." Link the "what we keep" page. In Privacy, replace "not written to disk" with "not saved to our database or file storage". This needs counsel; the Privacy page is being updated.
- **Effort:** S

**R-19 · "Exports are … not kept" / "does not store your exported files"**
- **Where:** `components/marketing/DemoTabExplorer.tsx:252` ("Exports are generated on demand and not kept"); `domain/pricing.ts:359` (FAQ: "Paciolus does not store your exported files").
- **Why:** False for shared-link exports.
- **Change:** "Exports are generated when you request them and sent to your browser. If you share one by link, it is stored for up to 24 hours (Professional) or 48 hours (Enterprise), then deleted."
- **Effort:** S

**R-20 · Shared-link retention is given as a flat "48 hours" everywhere**
- **Where:** `about/page.tsx:203`, `approach/page.tsx:96`, `content/trust.ts:252`, `privacy/page.tsx:230, 373, 420`, `terms/page.tsx:429`.
- **Why:** Fixed fact, confirmed in `backend/routes/export_sharing.py:8`: 24 hours on Professional, 48 hours on Enterprise. "Up to 48 hours" is not wrong as a ceiling, but it does not match the required wording.
- **Change:** "…stored with our storage provider for up to 24 hours (Professional) or 48 hours (Enterprise), then deleted."
- **Effort:** S

**R-21 · Statements that "nothing is at rest to breach"**
- **Where:** `content/trust.ts:213` ("there are no uploaded files or ledger rows at rest to exfiltrate"), `:215` ("No raw files stored means no file-level breach surface"); `approach/page.tsx:69` ("No uploaded files or ledger rows at rest"), `:108` ("No uploaded files or line-level ledger data at rest to breach"); `ArchitectureDiagram.tsx:215` ("No line-level financial data").
- **Why:** False on two counts. Shared exports sit in R2 for up to 48 hours. Misstatement workpapers store account plus amount, and analytical expectations store expected and actual values, which is line-level financial data the auditor typed in.
- **Change:** "Uploaded files are not kept, so a breach of our database would not expose them. The database does hold what you enter in an engagement, including misstatement amounts and analytical expectations, and shared reports are held for up to 24 or 48 hours."
- **Effort:** S

**R-22 · About page section is still titled "Zero-Storage Commitment" in code, and the app shows "Uploads Not Kept" badges with a pulsing dot**
- **Where:** `about/page.tsx:186` is a comment only and is not rendered (fine). Customer-facing text: no rendered "Zero-Storage" string was found; the 2026-10 claims-review sweep worked. The `/status` page is the exception (see A-05).
- **Change:** None on About. Rename the `ZeroStorageNotice` component and comments when convenient, so the retired term stops being reintroduced (dev hygiene, **S**).

**R-23 · The "Traditional SaaS vs Paciolus" comparison table is a straw man and contains a compliance claim**
- **Where:** `approach/page.tsx:60-86, 248`.
- **Now:** Rows include "Deletion Requests — Traditional: Complex, error-prone" and "Compliance (GDPR/CCPA) — Paciolus: Simplified — minimal PI stored". The closing line at `:416` reads "the security benefits far outweigh the convenience costs".
- **Why:** The "traditional" column is unsourced and pejorative, the kind of unquantified claim the brief bans. "Compliance (GDPR/CCPA): Simplified" edges toward a self-awarded compliance claim. "Data Retention: Months or years" is also unsourced.
- **Change:** Replace the table with a factual two-column table: "What happens" | "How long". Rows: Uploaded file (in memory, up to 10 minutes) · Analysis summary (kept until you delete it or your account; **needs input from Paciolus** on the actual retention period, since the table currently says "per retention policy" and links nothing) · Engagement entries (until you delete them) · Shared export (24h Pro / 48h Ent). This doubles as the data-flow fact sheet.
- **Effort:** M

### 1.4 Accuracy and consistency

**R-24 · Hero mock contradicts the catalog**
- **Where:** `hero/HeroFilmFrame.tsx:24-37, 412`.
- **Now:** The "analyze" frame shows 12 tiles, not 18. It includes "Multi-Currency", which CLAUDE.md describes as a side-car rather than an audit tool. Three tiles are struck through, which reads as "not available". The export frame says "17 PDF Memos" while the site elsewhere says 18 tools and 18 memos.
- **Why:** A literal-minded reader spots the mismatch with "18 testing tools" in the line just above it.
- **Change:** Replace the mock with a screenshot (S-01). Until then, fix the numbers to match `TOOL_LEDGER` and remove the strike-through.
- **Effort:** S (interim) / L (screenshot)

**R-25 · Trial wording: "Free" vs card required**
- **Where:** `demo/page.tsx:182` ("Start 7-Day Trial — Free"); hero `:157` ("Free plan needs no card. Paid trials ask for one; no charge for 7 days."). Pricing (`pricing/page.tsx:122`, `domain/pricing.ts:312`) is accurate and clear.
- **Change:** Demo CTA: "Start 7-day trial". Add beneath it: "Card required; no charge for 7 days. Cancel before day 8 and you are not charged." Hero line is fine as-is.
- **Effort:** S

**R-26 · `/status` publishes hard-coded "simulated" test results as live**
- **Where:** `app/status/page.tsx:19-50` (comment: "Simulated test results"), rendered as "Paciolus Backend Status & Test Results" with "N/N Passed". One category is named "ZeroStorageLeak".
- **Why:** A visitor would take it as a real CI result. It is fabricated, and it uses "Passed" and the retired term. For a skeptical buyer who finds it, this would undo a lot of credibility.
- **Change:** Remove the test-results section, or make the page internal-only. Keep the health check. See Q7.
- **Effort:** S

---

## 2. Generic-AI-startup elements

### 2.1 Visual

**G-01 · Gradient text in the hero headline**
- **Where:** `hero/HeroProductFilm.tsx:89` (`bg-gradient-to-r from-sage-400 via-sage-300 to-oatmeal-300 bg-clip-text text-transparent`).
- **Change:** Solid `text-sage-300` on the second line. This keeps the bold brand color without the gradient.
- **Effort:** S

**G-02 · Glows, pulses and gradient hairlines across the homepage**
- **Where:**
  - `.lobby-glow-sage` radial glow (`globals.css:588-601`), used at `page.tsx:47`, `trust/page.tsx:194, 233`
  - Scrubber "glow ring" with `animate-pulse` (`HeroProductFilm.tsx:337-338`)
  - Colored glow shadows (`shadow-sage-600/25`, `shadow-sage-500/30`, …) on CTAs and icons (`HeroProductFilm.tsx:138, 262, 331`; `BottomProof.tsx:108`; `ProcessTimeline.tsx:80-94, 201, 250`; `PricingCard.tsx:35`)
  - "Inner glow" overlays (`ProcessTimeline.tsx:204, 265`; `ArchitectureDiagram.tsx:221, 289`)
  - Gradient lines (`FeaturePillars.tsx:375, 402`; `ProcessTimeline.tsx:161, 168, 233`; `MarketingFooter.tsx:197`; `trust/page.tsx:116, 122`; `.lobby-divider*` with glowing center dot, `globals.css:755-800`)
  - Pulsing status dots (`ProcessTimeline.tsx:291`, `ArchitectureDiagram.tsx:240`, `register/page.tsx:220`)
- **Why:** Visual avoid list: "Glow, neon, and gradient effects, including gradient borders and washes."
- **Change:** Use solid 1px hairlines in `obsidian-500/40` or `oatmeal-400/20`, which are the workpaper rules the brief asks for. Use neutral `shadow-obsidian-900` drop shadows only, and no pulsing. Delete `.lobby-glow-sage`, the glow ring and the inner-glow overlays.
- **Effort:** M

**G-03 · Glassmorphism**
- **Where:** `backdrop-blur-xl` on the hero product frame (`HeroProductFilm.tsx:364`), the demo explorer ("Glass container", `DemoTabExplorer.tsx:333`), the nav (`MarketingNav.tsx:69-70, 119, 126, 172, 199, 207`), and About panels (`about/page.tsx:197, 305`).
- **Change:** Use opaque `bg-obsidian-800` panels with a hairline border. The nav can keep a solid background on scroll.
- **Effort:** S

**G-04 · Stock photography as section backgrounds**
- **Where:**
  - `.lobby-atmosphere-heritage` → `public/backgrounds/background1.jpg` (a quill pen on a handwritten ledger), used on About (`about/page.tsx:71`)
  - `.lobby-atmosphere-modern` → `background2.jpg` (a neon-green-tinted office tower at night), used behind the homepage tool ledger (`page.tsx:37`)
  - `.lobby-atmosphere-foil` → `background3.jpg` ("metallic sage foil"), used behind the footer (`MarketingFooter.tsx:195`)
  - `background5.jpg` (a vintage cash register), used on Pricing (`pricing/page.tsx:194`)
- **Why:** Visual avoid list: "stock photography." The green-tinted tower is also close to the "neon" look.
- **Change:** Remove all four. Use flat `obsidian` surfaces. Product screenshots (S-01) become the imagery.
- **Effort:** S

**G-05 · Fake UI fragments as the main product imagery**
- **Where:** The hero "product film" (`HeroFilmFrame.tsx`), with an animated cursor dragging a file card, a 12-tile grid with a scan-line sweep, and a fake download progress bar. Also `DemoTabExplorer.tsx`, a five-tab mock of the app with a `ScanlineOverlay` CRT effect (`:51`) and a `MechanicalGauge`. There are no real screenshots anywhere in `public/`.
- **Why:** Visual avoid list: "Bento grids of fake or fragmentary UI". The scan-line sweep and CRT overlay are decorative effects. Strong-fit list: "Real product screenshots as the primary visual, including in the hero."
- **Change:** See S-01. Replace the film with a static screenshot. Keep the three-step labels (Drop your file / See what's flagged / Take the exports) as captions under three screenshots. Remove `ScanlineOverlay`.
- **Effort:** L

**G-06 · Heavy, content-delaying motion**
- **Where:**
  - Hero auto-plays a 23-second loop (`useHeroAnimation.ts:41-45`)
  - Cursor-following `MagneticButton` (`HeroProductFilm.tsx:35-68`)
  - Scroll-linked `ParallaxSection` (`page.tsx:47, 62`; `utils/marketingMotion.ts:162`)
  - Clip-path reveal wipes (`FeaturePillars.tsx:299-306`)
  - Step badges that spin in from −180° (`ProcessTimeline.tsx:114-121`) and rotate on hover (`:200`)
  - Count-up numbers (`ProcessTimeline` step numbers; Trust metrics `trust/page.tsx:41, 48`)
  - Staggered entrance delays of up to 0.6 s on About (`about/page.tsx:324`) and the Trust page
- **Why:** Visual avoid list: "Heavy animation, scroll-driven effects… or motion that delays content." Count-up figures are especially bad for an audience that wants to read a number once and trust it.
- **Change:** Keep only short opacity fades (≤200 ms, no delay) and hover color changes. Remove parallax, magnetic hover, spin-ins, clip wipes and count-ups. The homepage `BottomProof` already retired count-ups; Sprint 704's note says "a stable number more than an animated one", so apply that everywhere.
- **Effort:** M

**G-07 · Rows of three icon cards**
- **Where:**
  - `FeaturePillars.tsx` (three icon cards: "Uploads Not Kept / Precision at Every Threshold / Professional-Grade Exports")
  - `ProcessTimeline.tsx` (three big icon tiles: "Upload / Analyze / Export" with one-line taglines)
  - `about/page.tsx:38-66, 227` (three icon cards: "Designed Around How Auditors Work / Professional Standards / Formatted for Your Workpapers")
- **Why:** Visual avoid list: "Rows of three feature cards with an icon and one sentence each."
- **Change:** Turn `FeaturePillars` into the long-form "What goes in / what Paciolus does / what you get" table (S-04), with numbered rows and hairline rules. Merge `ProcessTimeline` into the hero screenshots' captions. Rewrite the About cards as a short prose section.
- **Effort:** M

**G-08 · Centered hero with a pill badge above the headline**
- **Where:** `demo/page.tsx:67-73` (pill "Product Tour — Sample Outputs, No Account Required" above a centered h1). The Trust hero is centered, with a pill-shaped metrics bar under it (`trust/page.tsx:38`).
- **Change:** Use a left-aligned headline on the shared grid. Turn the pill into a plain line of small text under the headline: "Sample outputs on synthetic data. No account required."
- **Effort:** S

**G-09 · Emoji tab icons and a "Trial Balance: Balanced" checkmark in the demo**
- **Where:** `DemoTabExplorer.tsx:36-41` (📊 🔍 📋 📄 ⚖️), `:219-226` (📃 etc.).
- **Change:** Use the existing `BrandIcon` set, or plain text labels.
- **Effort:** S

### 2.2 General copy

**G-10 · "Intelligent", "intelligence", "Surgical Precision"**
- **Where:**
  - `ProcessTimeline.tsx:56` ("Intelligent classification")
  - `:65` ("Reclassified intelligence")
  - `:136` ("From Raw Data to Diagnostic Intelligence")
  - `approach/layout.tsx:5` ("receive diagnostic intelligence in seconds")
  - `about/layout.tsx:4` (title "Diagnostic Intelligence for Financial Professionals")
  - `app/layout.tsx:48` and `about/layout.tsx:5` ("Surgical Precision…")
  - App: `bank-rec/page.tsx:349` ("Intelligent column detection"), `InsightMicrocopy.tsx:40` ("Intelligence Briefing"), `flux/page.tsx:161` ("Flux & Variance Intelligence")
- **Why:** General avoid list: "'intelligent' as a standalone descriptor". These phrases could describe any analytics startup.
- **Change:**
  - Homepage step: "Account classification: each account is typed by keyword rules you can review."
  - Section head: "From trial balance to flagged accounts and exports".
  - Site title: "Paciolus: trial balance and ledger testing for auditors".
  - Bank rec: "Column detection for date, amount, description and reference fields."
  - "Intelligence Briefing" → "Notes for this engagement".
  - "Flux & Variance Intelligence" → "Flux & Variance Analysis".
- **Effort:** S

**G-11 · Unquantified speed claims ("in seconds")**
- **Where:**
  - Hero h1 `HeroProductFilm.tsx:87` ("Diagnostics in Seconds.")
  - `ANALYSIS_LABEL_SHORT = 'Seconds'`, used in `HeroFilmFrame.tsx:223` and `EvidenceBand.tsx:353`
  - `FeaturePillars.tsx:338`, `ProcessTimeline.tsx:57, 139, 293`, `MarketingFooter.tsx:215`, `approach/layout.tsx:5`, `about/page.tsx:278`, `demo/page.tsx:174`
- **Why:** General avoid list: unquantified speed claims. A qualified version already exists and is unused: `ANALYSIS_LABEL_QUALIFIED` = "usually a few seconds for files up to 10,000 rows" (`utils/constants.ts:60`).
- **Change:** Use the qualified label wherever speed is mentioned, and drop "in seconds" from the h1 (see G-12). **Needs input from Paciolus:** confirm the 10,000-row figure has been measured on production. If it has, add the hardware and file type to the Sources page so it can be checked.
- **Effort:** S

**G-12 · Headlines that would fit any SaaS product**
- **Where:**
  - "Built for Financial Professionals" (`FeaturePillars.tsx:335`, `about/page.tsx:224`)
  - "See Paciolus in Action" (`demo/page.tsx:76`)
  - "Straightforward Pricing for Serious Work" (`pricing/page.tsx:115`)
  - "Ready to Analyze Your Own Data?" (`demo/page.tsx:170`)
  - "Start your first analysis." (`about/page.tsx:328`)
  - "Professional-Grade Exports" / "Professional-grade analysis" (`FeaturePillars.tsx:286`, `HeroProductFilm.tsx:105`)
  - "Done before you close the tab." (`FeaturePillars.tsx:287`)
  - "One gesture. Instant recognition." (`useHeroAnimation.ts:26`)
- **Change:** Headlines should name the object and the result. Suggestions, all checked against the avoid lists:
  - Hero h1: "Test the whole ledger. Keep the judgment." Second line: "Trial balance, journal entry, AP, payroll and revenue testing, with every flag tied to a cited rule."
  - Demo: "Sample outputs from all 18 tools, on synthetic data"
  - Pricing: "Every paid plan includes all 18 tools"
  - Exports card title: "PDF memos and Excel workpapers"
- **Effort:** S

**G-13 · "Unlocks"**
- **Where:** `ToolLedger.tsx:74` ("Every paid tier unlocks the full suite").
- **Change:** "Every paid plan includes all 18 tools."
- **Effort:** S

---

## 3. Missing or weak strong-fit elements

**S-01 · Real product screenshots (none exist)**
- **Now:** `public/` contains only logos and background textures. Every product image is an animated mock (G-05).
- **Placements (you supply the screenshots from synthetic data):**
  1. **Homepage hero, right column** (replacing `FilmStage`, `HeroProductFilm.tsx:347-425`): one large screenshot of TB Diagnostics results with the flagged-accounts table visible.
  2. **Under the hero, three captioned screenshots** in a strict three-column grid, captioned as reference figures: "Fig. 1: Upload and column mapping" · "Fig. 2: JE Testing results, flagged entries" · "Fig. 3: Export panel".
  3. **Tool ledger expanded row** (`ToolLedger.tsx:181-209`): a small screenshot of that tool's results screen.
  4. **Demo page:** replace each `DemoTabExplorer` tab body with a screenshot of the real screen it imitates (TB Diagnostics, Testing Suite, Workspace, Exports, Standards).
  5. **Memo page images:** first page of a JE Testing memo and a TB Diagnostics memo, shown in the **default** layout with no sign-off block (the default, per `backend/shared/memo_base.py:665`). If you also show the optional sign-off version, the lines must be empty and captioned "Optional, completed by the firm."
  6. **Workspace screenshot** on About ("Where Paciolus fits"), to show the follow-up tracker and misstatement schedule. It also helps visual continuity, since the app is white.
- **Effort:** L

**S-02 · Data-flow diagram with the two required paths**
- **Now:** The Approach page has a single four-step path that ends with "<5 seconds" (`approach/page.tsx:13-50, 187`). The Trust page has Upload → Verify → Analyze plus "Data destroyed after processing" (`ArchitectureDiagram.tsx`). Neither shows the shared-link path.
- **Change:** Build one static SVG diagram in the palette and use it on both pages:
  - **Path A (sage):** Upload → Processed in memory (cached up to 10 min for reuse) → Results returned to your browser → Uploaded file discarded.
  - **Path B (oatmeal):** Shared link created (Professional / Enterprise) → Export stored with our storage provider for up to 24 hours (Professional) or 48 hours (Enterprise) → Deleted.
  - A separate box underneath (obsidian, hairline border), titled "Kept in your account", listing the four kept categories from the brief.
  - Use hairline arrows and numbered stages (A1–A4, B1–B3) so readers can cite them, with no glow or pulse.
- **Effort:** L

**S-03 · Approved data-handling sentence: used verbatim almost nowhere**
- **Now:** The verbatim sentence exists as `STORAGE_STATEMENT` in `content/storage-statement.ts:57`, but no marketing page renders it. Close paraphrases appear in `FeaturePillars.tsx:263`, `about/page.tsx:199`, `register/page.tsx:228`, `login/page.tsx:168`, and the app's `ZeroStorageNotice` shows only the first half.
- **Change:** Render `{STORAGE_STATEMENT}` plus the link `STORAGE_DETAIL_LABEL → STORAGE_DETAIL_HREF` in these places: the hero (R-15), the footer brand column (`MarketingFooter.tsx:214-221`, replacing "Uploaded files are not kept" and the badge), the About "What we keep" box, the Approach hero, Pricing under the plan cards, Register, Login, and `ZeroStorageNotice` (switch `UPLOAD_HANDLING` to `STORAGE_STATEMENT`).
- **Effort:** S

**S-04 · Feature descriptions don't state the mechanism**
- **Now:** "Precision at Every Threshold … What matters surfaces. What doesn't, stays out of the way." (`FeaturePillars.tsx:276`); "Every flag, every ratio, every anomaly is weighted against your criteria". Tool summaries in the ledger are good (`tool-ledger.ts`), but they are hidden behind a click.
- **Change:** Add a long-form "How each tool works" section (or extend `/sources`) with three columns per tool: **Input** (file type, required columns) · **What Paciolus does** (tests, by number, e.g. "19 tests incl. Benford first-digit MAD per Nigrini 2012") · **What you get** (memo sections, Excel tabs). Rewrite the materiality card the same way: "You enter overall and performance materiality once per engagement. Each tool uses those amounts as its default flag threshold; you can change them per run." (**Needs input from Paciolus:** confirm this matches the materiality cascade behavior.)
- **Effort:** M (section) / L (all 18 tools)

**S-05 · Division-of-responsibility and documentation-obligation wording are absent**
- **Now:** Neither the approved sentence ("Paciolus produces PDF memos and Excel/CSV workpapers. Your firm keeps them in its own documentation system; Paciolus is not a workpaper archive.") nor "not a substitute for your firm's audit documentation and retention obligations" appears anywhere on the site. The footer disclaimer (`content/disclaimers.ts:11-16`) is good but covers different ground.
- **Change:** Add both sentences to `content/disclaimers.ts` as constants. Render them in the footer disclaimer bar, under the homepage export screenshot, in About "Where Paciolus fits" (R-12), and in the Pricing FAQ. Do not name standards in any of these places.
- **Effort:** S

**S-06 · A dedicated, linkable "What we keep" page**
- **Now:** The list lives in three slightly different places: `content/trust.ts:246-261`, `approach/page.tsx:90-105`, and `terms/page.tsx` §5. The Approach list omits flagged-account-name amounts detail and follow-up items. All links point to `/trust#transparency`.
- **Change:** Make one source list in `content/` that renders identically on the Trust anchor and Approach, and point every "See exactly what we keep" link there. Content follows the brief's four facts exactly, including follow-up items, misstatement workpapers and analytical-expectation workpapers by name. (**Dependency:** the Trust page is being updated; keep the anchor stable.)
- **Effort:** M

**S-07 · Downloadable sample memo and workpaper**
- **Now:** The Demo "Sample Reports" tab describes formats (`DemoTabExplorer.tsx:200-230`) but offers nothing to download.
- **Change:** Add "Download sample JE Testing memo (PDF)" and "Download sample workpaper (XLSX)" buttons on the Demo page, the homepage export section and the Trust artifacts list. Files would be generated from synthetic data, in the default memo layout. (**Needs input from Paciolus:** the files themselves.)
- **Effort:** L

**S-08 · Data residency, DPA and security-questionnaire answers aren't surfaced**
- **Now:** Residency appears only inside the Privacy table (`privacy/page.tsx:600-610`, "United States (Virginia)"). DPA is "on request" (R-03). There is no questionnaire pack.
- **Change:**
  - Add a "Facts for your vendor review" block to the Trust page, as a plain definition list with tabular figures. Rows: Hosting region: US East (**needs input from Paciolus:** confirm that the Vercel, Render, Neon and Cloudflare R2 locations all support saying "US East"); Certifications: none held or claimed (R-01); DPA: on request; Subprocessors: link (dependency); Incident contact; Support response: 1–2 business days.
  - Offer a short security-questionnaire answer pack (PDF or a page, about 25 common questions answered in one line each). **Needs input from Paciolus** for the answers.
- **Effort:** M (block) / L (pack)

**S-09 · Trust/FAQ answer naming AU-C 230 and AS 1215**
- **Now:** No such answer exists. AS 1215 appears in the wrong places instead (R-07, R-08).
- **Change:** Add a Trust FAQ item, worded as a direct question:
  > **Does Paciolus satisfy AU-C 230 or PCAOB AS 1215?**
  > No. AU-C 230 and PCAOB AS 1215 set documentation and retention duties for audit firms, not for software vendors, so Paciolus does not claim compliance with them. Paciolus produces PDF memos and Excel/CSV workpapers. Your firm keeps them in its own documentation system; Paciolus is not a workpaper archive.
- **Effort:** S

**S-10 · Curated release notes**
- **Now:** None. (A full public changelog is out of scope, and none exists, correctly.)
- **Change:** Add a short "Recent improvements" list on the Trust or About page: 5–8 dated, plain-language entries such as "Nov 2026: share-link retention set per plan". **Needs input from Paciolus** for which items to publish.
- **Effort:** M

**S-11 · Workpaper visual language: grid, hairlines, reference numbers, tabular figures**
- **Now:** Some good work exists. The tool ledger uses Roman numerals, hairline rows and tabular-nums (`ToolLedger.tsx`), BottomProof has engraved stats, and the Sources page is long-form and checkable. But most other sections use rounded glowing cards, centered text and decorative dividers. The marketing default is `oldstyle-nums proportional-nums` (`(marketing)/layout.tsx:87-91`); EvidenceBand and the pricing cards display prices and stats without forcing tabular figures in every case.
- **Change:**
  - Adopt one 12-column grid with left-aligned section heads.
  - Give each section a reference number in the margin ("§2 Data handling", "Fig. 3").
  - Use annotation-style callouts (the existing `MarginAnnotation` component in `components/demo/` is the right idea; reuse it on real screenshots).
  - Force `tabular-nums lining-nums` on all prices (`PricingCard`), the estimator, stats (`EngravedStat`, `EvidenceBand`) and the Trust metrics.
  - Right-align numeric columns.
- **Effort:** M

**S-12 · Visual continuity with the app**
- **Now:** Logo treatment matches: the marketing nav uses `PaciolusLogo_DarkBG.png`, and the app toolbar and profile menu use `PaciolusLogo_LightBG.png`. The difference is component shape. Marketing uses `rounded-2xl` glass cards, glow shadows and pill buttons; the app uses `theme-card` surfaces.
- **Change:** Give marketing buttons and cards the app's border radius and border style so a screenshot of the app sits naturally on the page. Use the same sage primary button, so the button in a hero screenshot matches the CTA next to it.
- **Effort:** M

**S-13 · A factual "who builds this" note**
- **Now:** The only mention is on the Trust page ("incidents are handled by the founder"). About has a quote attributed to "Paciolus — founding motivation".
- **Change:** Add a two-sentence note on About: "Paciolus is built and run by its founder in the United States. Support and incident response are handled directly, with replies within 1–2 business days." This adds no names or credentials, per the brief. (**Needs input from Paciolus:** confirm the wording and location.)
- **Effort:** S

**S-14 · Claims backed by checkable references**
- **Now:** Test counts and standard-setter counts are backed by `/sources`, which is good. Speed (G-11), "19 security controls" (Trust) and "Every test names its rule" have no link next to them.
- **Change:** Add a small "Check →" link next to each claim, pointing to `/sources` or the control matrix.
- **Effort:** S

---

## 4. App wording and continuity

The app was checked against the wording rules and for continuity only; marketing layout criteria were not applied.

**A-01 · "All tests returned clean results"** in seven tables. See R-13. **S**

**A-02 · "Top Findings"** in `TestingScoreCard.tsx:178`. See R-14. **S**

**A-03 · "Workpaper-ready CSV"** in `bank-rec/page.tsx:360`. See R-11. **S**

**A-04 · "Intelligent column detection" / "Intelligence Briefing" / "Flux & Variance Intelligence".** See G-10. **S**

**A-05 · `/status` page:** simulated test results labelled "Passed", with category "ZeroStorageLeak" shown. See R-26. **S**

**A-06 · Upload notice shows only half the approved wording**
- **Where:** `components/shared/ZeroStorageNotice.tsx:27` shows `UPLOAD_HANDLING` on every tool page.
- **Change:** Show `STORAGE_STATEMENT` and the link. **S**

**A-07 · Register and Login paraphrase the approved sentence**
- **Where:** `register/page.tsx:228` ("…analysis summaries and engagement entries"), `login/page.tsx:168` ("…what you enter in an engagement"). Register also shows a pulsing "Uploads Not Kept" badge (`:219-223`).
- **Change:** Use `STORAGE_STATEMENT` verbatim and drop the pulsing dot. **S**

**A-08 · Negated avoid-terms in disclaimers**
- **Where:** Follow-up tracker: "Items listed here are NOT findings or control deficiencies…" (`portfolio/[clientId]/workspace/[engagementId]/page.tsx:307`). Workspace banner: "…does not track … assurance engagements, or compliance with ISA/PCAOB standards" (`:38`). Results disclaimer: "not findings or conclusions" (`content/disclaimers.ts:20`).
- **Why:** These are negations and they are protective, so I recommend keeping them. Flagged only because the brief says "flag every occurrence." See Q9.
- **Effort:** none, or **S** if you want them reworded

**A-09 · "Archive" and "audit trail" for engagement entries**
- **Where:** Misstatement and expectation rows have an "Archive" button, and the notes say deleting "archives it … so it stays in the audit trail" (`CreateMisstatementModal.tsx:283-284`, `AnalyticalExpectationsPanel.tsx:598`).
- **Why:** This is accurate, because these entries are kept. But the word "archive" sits awkwardly next to "Paciolus is not a workpaper archive."
- **Change:** Rename the button "Remove", and the note to "Removed lines stay in this engagement's change history." **S**

**A-10 · Continuity**
- Logo and brand color match. The app's `MegaDropdown` (`components/shared/UnifiedToolbar/MegaDropdown.tsx`) is a mega-menu, but the brief limits the mega-menu rule to marketing structure. Noted, not flagged.
- Visual continuity improves most with S-12 (shared button and card shapes) and S-01 (app screenshots on marketing pages).

---

## 5. Questions for Paciolus

**Q1. Do shared-link exports contain line-level rows?**
`FeaturePillars.tsx:289` says Excel workpapers carry "full underlying data". The demo says Excel has "raw flagged data" and the CSV is a "flat file of flagged transactions". If a shared export includes those rows, then every "we never store line-level rows / journal entries / invoices" list is false for up to 24 or 48 hours. Your own "what we keep" list should then say: "Shared exports, which may include the rows in your file, for up to 24/48 hours." Which is it?

**Q2. Does "do not name standards" on marketing pages apply only to documentation and retention standards (AU-C 230, AS 1215)?**
The alternative reading covers every citation. Under that reading the tool ledger chips, the homepage standards specimen, the EvidenceBand "ISA · PCAOB · ASC", About ("Memos cite ISA 240, ISA 500, PCAOB AS 2401") and the Demo tool descriptions would all have to go. The citations are a core differentiator, so I have assumed the narrow reading and flagged only AS 1215 (R-07, R-08).

**Q3. Should "SOC 1" appear anywhere on marketing pages, even as a framework the SoD tool can support?**
I recommended removing it from the homepage chip (R-04).

**Q4. Does the 10-minute in-memory cache apply to every upload, or only to previewed PDFs and workbooks?**
Your brief says the former. Privacy (`privacy/page.tsx:373`) and Terms (`terms/page.tsx:379`) say the latter. The data-flow diagram depends on the answer.

**Q5. How long are analysis summaries kept?**
Approach says "per retention policy" and "archived on schedule, and deleted on request" (`approach/page.tsx:74, 79`), but no retention period is stated or linked.

**Q6. Can flagged account names be personal names?**
Examples are payroll employees, and AP or 1099 vendors who are sole proprietors. If they can, the claims "No client PII in analysis results" and "No PII in logs" need to go (R-06), and the "what we keep" list should say names can include people.

**Q7. Is `/status` meant to be public?**
It presents hard-coded "simulated" test results as live (R-26).

**Q8. Is it accurate to describe shared exports as "encrypted"?**
The site says "held encrypted" (`trust.ts:252`, Terms, Privacy). Is that provider-managed encryption at rest in R2, or your own? Literal readers will ask.

**Q9. Should the protective negations stay?**
For example, "not findings or control deficiencies" and "does not … compliance with ISA/PCAOB standards" (A-08). They contain avoid-list words but serve your position. I recommend keeping them.

**Q10. Is the CaseWare / TeamMate import path tested?**
About says exports "import directly into" both (`about/page.tsx:310`).

**Q11. Has the speed figure been measured on production?**
The code has a qualified label: "usually a few seconds for files up to 10,000 rows".

**Q12. Do the Privacy Policy and Terms count as marketing pages for this review?**
Both contain avoid-list wording ("not written to disk"; a flat "48 hours"). Counsel is updating them, so I flagged the wording but proposed only light changes.

**Q13. Should the Trust page's four-phase incident playbook stay?**
The "Preparedness Playbook" (`trust.ts:186-231`) presents a four-phase incident process for a one-person operation. It is honest about having no on-call. Do you want to keep the formal phase structure, or replace it with three plain sentences? The phase structure risks reading as more process than exists.

---

## Summary: the ten changes that would improve the site most

| # | Change | Where | Effort |
|---|---|---|---|
| 1 | **Remove the SOC 2 "Available" badge, the GDPR/CCPA "Compliant" badges and the "Compliance Roadmap"**, and replace them with one plain paragraph: no certification held or claimed, with links to the Security Policy, architecture document and Subprocessor List once their URLs are final. (R-01–R-03) | `content/trust.ts:156-184`, `components/trust/ComplianceTimeline.tsx` | M |
| 2 | **Delete "Zero data retained." from the hero** and put the approved data-handling sentence plus its link in its place, and in the footer, Approach, Pricing, Register, Login and tool notices. (R-15, S-03, A-06/07) | `HeroProductFilm.tsx:105`, `MarketingFooter.tsx:214-221`, `ZeroStorageNotice.tsx` | S |
| 3 | **Fix every "never / zero / destroyed / <5 seconds / not written to disk" claim** to match the facts: 10-minute cache, shared exports kept 24h (Pro) / 48h (Ent), engagement entries stored. Answer Q1 first. (R-16–R-21) | Trust, Approach, About, FeaturePillars, Demo, Pricing FAQ, Privacy | S |
| 4 | **Remove PCAOB AS 1215 from the homepage and the control matrix**, and add the Trust FAQ answer naming AU-C 230 first, then AS 1215. (R-07, R-08, S-09) | `standards-specimen.ts:93-97`, `trust.ts:149` | S |
| 5 | **Replace the animated hero film and demo mock-ups with real screenshots** (synthetic data): one large hero screenshot plus three captioned figures; default memo, no sign-off lines. (S-01, G-05, R-24) | `hero/*`, `DemoTabExplorer.tsx` | L |
| 6 | **Build the two-path data-flow diagram** (upload path, shared-link path) in the palette and use it on Trust and Approach, replacing the current diagrams. (S-02) | `ArchitectureDiagram.tsx`, `approach/page.tsx:13-50` | L |
| 7 | **Fix the audit-language slips**: "3 findings" → "3 items flagged"; "All tests returned clean results" → "No exceptions flagged"; "Top Findings" → "Top flagged items"; "workpaper-ready"; "governing standard". (R-09–R-11, R-13, R-14) | Hero, 7 app tables, `TestingScoreCard`, bank-rec, EvidenceBand | S |
| 8 | **Strip the decorative layer**: gradient headline text, glows, pulses, glassmorphism, four stock-photo backgrounds, parallax, magnetic buttons, spin-ins, count-ups. Use hairlines, opaque panels and short fades. (G-01–G-06) | `globals.css` lobby utilities, homepage components, nav | M |
| 9 | **Add the approved division-of-responsibility sentence and "not a substitute for your firm's audit documentation and retention obligations"** to the footer, the homepage export section, About and the Pricing FAQ, and replace the CaseWare/TeamMate claim. (S-05, R-12) | `content/disclaimers.ts`, footer, About | S |
| 10 | **Add a vendor-review facts block and downloadable proof**: residency (US East, once confirmed), DPA on request, subprocessor link, sample memo PDF and sample workpaper XLSX, a short questionnaire answer pack. Also replace the three-icon-card rows with an input / mechanism / output table per tool. (S-04, S-07, S-08, G-07) | Trust, Demo, homepage | L |

Also do immediately: take down or make internal the `/status` page's simulated "Passed" test results (R-26, small). It costs five minutes, and a skeptical buyer who finds it would stop trusting the rest of the site.
