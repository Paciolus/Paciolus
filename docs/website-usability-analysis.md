# Website Usability Analysis — Customer Perspective

**Premise:** I'm a financial professional (CPA / audit manager at a mid-size firm) evaluating Paciolus for the first time. Everything below is based solely on what your public website tells me.

---

## A. Things That Genuinely Confused Me

### 1. Which 5 tools does Solo actually include?
The pricing page says **"TB Diagnostics + 5 testing tools"** but never names them. I had to leave the pricing page entirely, go to the demo page, click the "Solo" filter tab, and count the tool cards to figure out it's Multi-Period Comparison, Journal Entry Testing, Revenue Testing, AP Payment Testing, and Bank Reconciliation. A prospect comparing plans shouldn't have to play detective. **List the 6 Solo tools by name on the pricing page.**

### 2. What happens on Day 8 of the trial?
Every page says "7-day free trial — no credit card required." Great, I signed up. But what happens when the trial ends and I haven't entered a card?
- Is my account locked?
- Can I still log in and see past exports?
- Do I get downgraded to some limited free tier?
- Do I just see a paywall?

The FAQ says "you can cancel anytime during the trial period and will not be billed" — but says nothing about what the *default* state is on Day 8 with no payment method. This is the single most important conversion question and it's unanswered.

### 3. "Interactive Demo" isn't interactive in the way I expected
The demo page badge says **"Interactive Demo — No Account Required"** which made me expect I could upload a sample file and see real output. Instead it's 5 tabs of synthetic static mockups. The mockups are well-done, but "interactive" oversells it. I'd call this a "Product Tour" or "Sample Outputs" — the word "interactive" implies I'm driving.

### 4. "Diagnostic Workspace" — what is this?
Team tier includes "Diagnostic Workspace" (Solo does not). The pricing page feature table just shows a checkmark with no explanation. Is this a project dashboard? An engagement management layer? A collaboration space? I can't evaluate whether the $80/month jump from Solo to Team is worth it without knowing what this core differentiator actually does.

### 5. "Engagement Completion Gate" — what does this mean?
Organization tier ($400/mo) lists this as a key differentiator over Team ($130/mo). But there's no description anywhere on the pricing page. Am I paying $270/month extra partly for a feature I can't even understand from the website?

### 6. "Workpaper index & sign-off" — Organization only?
Does this mean Team users can't sign off on workpapers? Can they not index them? Or is this a specific formal workflow feature? The name suggests something critical to audit work, so gating it behind the $400 tier without explaining why feels opaque.

### 7. Zero-Storage messaging contradicts itself (slightly)
- Homepage: *"Zero data stored."*
- Footer: *"Twelve tools. Zero data stored."*
- Approach page: *"We store: aggregate diagnostic metadata (category totals, ratios, row counts), engagement records (narratives only), client metadata (names, industries)."*

I understand the nuance — you don't store *financial* data. But "Zero data stored" is a stronger claim than what the approach page describes. A skeptical compliance officer would flag this. The approach page is honest and clear; the homepage/footer tagline oversimplifies.

### 8. What counts as an "upload" on the Solo 20/month limit?
- If I upload a trial balance, realize a column is wrong, fix it, and re-upload — is that 2 uploads?
- If I upload a TB to the diagnostics tool and then upload journal entries to the JE Testing tool for the same client — is that 2?
- If I upload a multi-sheet Excel workbook — is that 1 upload or N?

This matters a lot at $50/month with a 20-upload cap. The pricing page and FAQ don't address it.

### 9. The "Vault" registration metaphor is unclear
"Create Your Vault" could mean a password vault, a document vault, a secure data vault. The metaphor doesn't map obviously to "create your account." It's aesthetically nice but functionally confusing for 2 seconds — which is 2 seconds too many on a registration page.

---

## B. Information I Looked For and Couldn't Find

### 10. No actual product screenshots
The demo page shows synthetic mockups. The homepage shows animated previews. But nowhere can I see what the real product UI looks like with real data loaded. Even a "Here's what TB Diagnostics looks like after uploading a real trial balance" screenshot would help enormously.

### 11. File formats undersold on marketing pages
The homepage ProcessTimeline says *"CSV, TSV, TXT, or Excel files."* But I later found (in the User Guide, not linked from marketing pages) that you support **10 formats** including QBO, OFX, IIF, PDF tables, and ODS. Why are you hiding 6 of your 10 supported formats? QBO/OFX support alone could be a deciding factor for firms working with QuickBooks clients.

### 12. No competitor positioning
I'm also evaluating CaseWare IDEA, ACL Analytics (now Galvanize/Diligent), MindBridge, and TeamMate Analytics. Your site never mentions why I should choose Paciolus over these. Even a "How We're Different" section (speed, zero-storage, no installation, standards-cited memos) would help me build the internal business case.

### 13. No case studies, testimonials, or social proof
The site shows credential badges (ISA 240, PCAOB AS 2315, etc.) and metric counts (140+ tests, 12 tools), but there are zero customer testimonials, zero firm logos, zero case studies, and no "trusted by X professionals" claim. For a B2B product at $130-400/month, this is a significant trust gap.

### 14. No integrations page
Where does Paciolus fit in my existing workflow? Does it integrate with QuickBooks, Xero, Sage, CaseWare, or any practice management software? Can I export directly to my working paper system? Even if the answer is "no integrations yet — it's standalone," that's useful information.

### 15. No phone number or live chat
Enterprise prospects want a conversation, not a form. The contact page only offers a web form and an email address. No phone number, no calendar booking link, no live chat widget. The "Contact Sales" CTA for Enterprise leads to the same generic contact form with "Enterprise" pre-selected in the dropdown.

### 16. SSO details missing
Organization tier ($400/mo) advertises "SSO integration" but doesn't specify: SAML? OIDC? Google Workspace? Microsoft Entra ID? Okta? For an IT department evaluating this, "SSO" without specifics is meaningless.

### 17. No maximum file size or row limit disclosed
I work with trial balances ranging from 200 rows (small client) to 50,000+ rows (large client). Is there a limit? Will a 100MB Excel file work? The site mentions "under 3 seconds" for analysis but never states capacity constraints.

### 18. Support SLA undefined
Solo gets "Priority email support." Team gets "Dedicated." Organization gets "Custom SLA." But none of these are defined. What's the response time? 4 hours? 24 hours? Next business day? "Priority" relative to what?

### 19. No training resources visible
No webinars, no tutorial videos, no knowledge base link, no certification program. The User Guide exists in your docs folder but I couldn't find a link to it from any marketing page. For a 12-tool platform, onboarding matters.

### 20. On-premise deployment details absent
Enterprise tier mentions "On-premise deployment option" with zero detail. Docker? Kubernetes? Air-gapped? Hardware requirements? This is a major enterprise purchasing criterion and it gets one bullet point.

---

## C. Functional Gaps — Features I'd Expect but Don't See

### 21. No cross-client dashboard
If I have 30 audit clients, I can't see a firm-wide view of "which clients have outstanding anomalies" or "which engagements are complete." Each client seems to be a silo.

### 22. No batch/bulk upload
With 30 clients, I apparently upload trial balances one-by-one. No mention of batch processing, scheduling, or automation.

### 23. Collaboration features unexplained
"Team Collaboration" appears as a checkmark in the comparison table for Team/Organization tiers. But what does collaboration actually mean? Can my team members:
- See each other's analysis results?
- Comment on specific anomalies?
- Assign follow-up items to each other?
- Review and approve each other's work?

This is the #1 question for any firm with more than one auditor.

### 24. No audit trail of the analytics process itself
Due to Zero-Storage, there's no history of past analyses. The approach page acknowledges the tradeoff ("exports are your permanent record"). But audit standards require documentation of the *process* — not just the *output*. If a reviewer asks "show me you actually ran Benford's analysis on Client X's journal entries," all I have is a PDF that I could have generated at any time. There's no timestamped log that I ran Tool Y on Date Z for Client X.

*Question: Does the activity log capture tool runs with timestamps? If so, is this visible to the user and exportable? This would partially solve the problem but it's never mentioned on the website.*

### 25. No custom memo templates
The PDF memos cite ISA/PCAOB standards, which is excellent. But can I add my firm's logo? Customize the memo language? Add firm-specific sections? This isn't mentioned anywhere.

### 26. No multi-entity / consolidation support
If my client has 5 subsidiaries, can I analyze each subsidiary's TB separately and then view consolidated results? No mention of group audit support.

---

## D. Minor Friction Points

### 27. "Limited time" promotions feel permanent
"Limited time: 20% off your first 3 months" — if this banner is always showing, it's not really limited time. Customers notice this and it erodes trust. Either make it genuinely time-bound (with an expiration date) or call it an "introductory offer."

### 28. Latin motto in footer
*"Particularis de Computis et Scripturis"* — I happen to know this is a Pacioli reference, but most CPAs won't. It's untranslated and unexplained in the footer. A nice touch for accounting history buffs; a "what?" moment for everyone else.

### 29. Annual savings math
The site says "~17% savings" for annual billing. Solo: $50/mo × 12 = $600 vs $500/yr = 16.67%. Team: $130 × 12 = $1,560 vs $1,300 = 16.67%. It's actually ~16.7%, not ~17%. Minor, but financial professionals notice rounding.

### 30. Tool page URLs require authentication
If someone sends me a link to `/tools/journal-entry-testing`, I can't see anything without logging in. There are no public tool detail pages — only the demo page mockups and the homepage slideshow. A dedicated landing page per tool (with screenshots, sample outputs, standards referenced, and a CTA) would help SEO and sharing.

---

## E. Questions I'd Want Answered Before Buying

1. Can I export the activity log / tool run history as evidence that I performed the analytics?
2. Is there a sandbox or playground mode where I can test with my own data before committing to a trial?
3. What's the data retention policy for engagement metadata? Can I delete a client and all associated metadata?
4. If I downgrade from Team to Solo, what happens to my workspace data and results from Team-only tools?
5. Do you have SOC 2 Type II certification? The Trust page mentions security controls but doesn't reference an independent audit.
6. Can I use Paciolus for non-audit engagements (e.g., forensic accounting, due diligence, management consulting)?
7. What's your uptime SLA? The Trust page mentions incident response but not availability guarantees.

---

## F. What the Website Does Well (Credit Where Due)

- **Approach page** — The most transparent "how we handle your data" page I've seen from any SaaS vendor. The trade-offs section is unusually honest.
- **Tool slideshow on homepage** — Cinematic, detailed, and actually explains what each tool does with specific standards citations. Best-in-class product showcase.
- **Pricing FAQ** — Covers the most common questions clearly (though it misses the ones above).
- **Professional tone** — The site reads like it was written by auditors for auditors, not by marketers who Googled "audit software."
- **Trust page** — The interactive security architecture diagram and 19-control matrix are exceptional. This is the page I'd send to my IT department.
- **Disclaimer in footer** — "Paciolus is a data analytics tool... It does not perform audits, provide assurance opinions, or generate audit evidence." This is exactly the right professional boundary to draw and it builds trust.

---

## Summary Priority Matrix

| Priority | Issue | Impact |
|----------|-------|--------|
| **P0 — Fix now** | #2 (trial expiration UX), #1 (Solo tools unnamed), #4 (Workspace unexplained) | Directly blocks purchase decisions |
| **P1 — Fix soon** | #8 (upload counting), #11 (file formats hidden), #13 (no social proof), #23 (collaboration unexplained), #3 (demo expectations) | Erodes confidence during evaluation |
| **P2 — Improve** | #7 (zero-storage nuance), #12 (competitor positioning), #15 (no phone/chat), #17 (file limits), #18 (SLA undefined), #24 (audit trail gap) | Professional buyers notice these |
| **P3 — Polish** | #27 (promo language), #28 (Latin motto), #29 (savings math), #30 (tool landing pages), #9 (vault metaphor) | Minor friction, low urgency |
