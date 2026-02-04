# Feature Roadmap

**Document Classification:** Internal (Product, Engineering)  
**Version:** 1.0  
**Last Updated:** February 4, 2026  
**Owner:** Product Manager  
**Review Cycle:** Monthly

---

## Overview

This roadmap outlines Paciolus's feature development plan from Q1 2026 through Q4 2027. Features are prioritized using the RICE framework (Reach, Impact, Confidence, Effort) and aligned with our product vision.

**Current Version:** 0.16.0 (February 2026)  
**Next Milestone:** 1.0.0 (Q2 2026)

---

## Q1 2026 (Jan-Mar) — COMPLETE ✅

**Theme:** Foundation & MVP Launch

**Completed Features:**

Sprint 1-24 (Complete feature history):
- ✅ Zero-Storage trial balance processing
- ✅ Automated account classification (80+ keywords)
- ✅ Anomaly detection (abnormal balances)
- ✅ Materiality threshold customization
- ✅ Multi-sheet Excel support with consolidation
- ✅ PDF/Excel export (professional reports)
- ✅ JWT authentication + user accounts
- ✅ Client portfolio management
- ✅ Activity history (GDPR-compliant metadata)
- ✅ Practice settings & materiality formulas
- ✅ Real-time sensitivity tuning
- ✅ Workspace architecture (guest vs. authenticated)
- ✅ Dashboard statistics (`/dashboard/stats`)

**Metrics:**
- Users: 0 → TBD (launching)
- ARR: $0

---

## Q2 2026 (Apr-Jun) — Production Launch & Growth

**Theme:** Market validation + scaling features

### Sprint 25-26: Mobile Optimization & PWA
**Priority:** High  
**Effort:** 3 weeks  
**Why:** Sarah (Fractional CFO) wants to check diagnostics on-the-go

**Features:**
- [ ] Progressive Web App (PWA) support- [ ] Touch-optimized UI for tablets
- [ ] Offline mode (limited: view cached results)
- [ ] iOS/Android home screen install prompts

**Success Metrics:**
- 20% of users access via mobile
- \u003c5% bounce rate on mobile

---

### Sprint 27-28: Team Collaboration (Enterprise Tier)
**Priority:** Medium  
**Effort:** 4 weeks  
**Why:** Mike (CPA Manager) needs multi-user accounts

**Features:**
- [ ] Team workspaces (invite members)
- [ ] Role-based access control (Admin, Member, Viewer)
- [ ] Shared client portfolios
- [ ] Activity audit trail (who did what)
- [ ] Team billing (single invoice for all members)

**Pricing:**
- Professional: $99/month (1 user)
- Team: $249/month (5 users) + $39/user additional
- Enterprise: Custom (10+ users, SLA)

---

### Sprint 29: Comparative Analytics (Zero-Storage Compliant)
**Priority:** High  
**Effort:** 2 weeks  
**Why:** Users want to compare "this quarter vs. last quarter"

**Features:**
- [ ] Store aggregate category totals only (not detailed accounts)
- [ ] Compare current diagnostic vs. previous diagnostic summaries
- [ ] Variance analysis dashboard
- [ ] Trend visualization (line charts for totals)

**Zero-Storage Compliance:**
- ✅ Only store aggregate stats (assets, liabilities, revenue, expenses totals)
- ❌ Never store account-level details

---

### Sprint 30: SOC 2 Type II Preparation
**Priority:** Critical  
**Effort:** 6 weeks (async with engineering)  
**Why:** Enterprise customers require SOC 2 compliance

**Deliverables:**
- [ ] Hire external auditor (Bishop Fox, Vanta)
- [ ] Implement required controls:
  - [ ] Access logging
  - [ ] Change management policy
  - [ ] Incident response testing
  - [ ] Backup/recovery testing
- [ ] Documentation (evidence collection)
- [ ] Final audit and certification

**Timeline:** May-June 2026  
**Cost:** $15-25K

---

**Q2 Targets:**
- Users: 500
- ARR: $25K
- Churn: \u003c10%

---

## Q3 2026 (Jul-Sep) — Intelligence & Automation

**Theme:** AI-powered insights + workflow automation

### Sprint 31-32: AI Anomaly Explanations
**Priority:** High  
**Effort:** 3 weeks  
**Why:** Users want to know *why* something is flagged

**Features:**
- [ ] OpenAI GPT-4 integration (anomaly descriptions)
- [ ] Example: "Accounts Receivable has a credit balance of $15,000. This is unusual because A/R typically carries a debit balance (customers owe money). Possible causes: overpayment, misclassification, or data entry error."
- [ ] In-app explanations (expandable cards)
- [ ] PDF report includes AI commentary

**Privacy:**
- ✅ Send only anomaly type + amount (no account names, no client identifiers)
- ✅ Zero-Storage maintained (explanations generated on-the-fly)

---

### Sprint 33: Industry Benchmarking (Anonymized)
**Priority:** Medium  
**Effort:** 2 weeks  
**Why:** "How do my client's ratios compare to industry averages?"

**Features:**
- [ ] Aggregate anonymized data by industry vertical
- [ ] Display percentile rank (e.g., "Your client's current ratio is better than 65% of technology companies")
- [ ] Opt-in only (users choose to contribute aggregated data)

**Privacy:**
- ✅ Only aggregated, anonymized category totals (no client names)
- ✅ Minimum 100 data points per industry (no small sample bias)

---

### Sprint 34: Zapier/Make.com Integration
**Priority:** Medium  
**Effort:** 2 weeks  
**Why:** Automate workflows (e.g., "Send diagnostic to Slack when uploaded")

**Features:**
- [ ] Zapier triggers:
  - New diagnostic completed
  - Anomaly count exceeds threshold
  - Client added
- [ ] Actions:
  - Upload trial balance (via API)
  - Create client
  - Get diagnostic summary

---

### Sprint 35-36: QuickBooks Online Integration
**Priority:** High  
**Effort:** 4 weeks  
**Why:** Jessica (Startup CFO) uses QB Online

**Features:**
- [ ] OAuth connection to QuickBooks
- [ ] Import trial balance directly (no manual export)
- [ ] One-click diagnostic from QB data
- [ ] Sync client list (optional)

**Challenges:**
- Zero-Storage: Must pull data on-demand, not persist
- QB API rate limits (throttling)

---

**Q3 Targets:**
- Users: 2,000
- ARR: $100K
- NPS: 50+

---

## Q4 2026 (Oct-Dec) — Scale & Polish

**Theme:** Mobile apps + enterprise features

### Sprint 37-40: Native Mobile Apps (iOS/Android)
**Priority:** High  
**Effort:** 8 weeks  
**Why:** 30% of users request mobile app

**Features:**
- [ ] React Native app (iOS + Android)
- [ ] Camera upload (scan paper trial balance)
- [ ] Push notifications (diagnostic complete)
- [ ] Offline mode (view cached results)

**App Store Presence:**
- App Store (iOS)
- Google Play (Android)

---

### Sprint 41: White-Label Branding (Enterprise)
**Priority:** Low  
**Effort:** 2 weeks  
**Why:** Large CPA firms want custom branding

**Features:**
- [ ] Custom logo upload
- [ ] Custom color scheme
- [ ] Custom PDF footer (firm name, address)
- [ ] Custom domain (e.g., diagnostics.smithcpa.com)

**Pricing:** Enterprise tier only ($1,000+/month)

---

### Sprint 42: Advanced Materiality Formulas
**Priority:** Medium  
**Effort:** 1 week  
**Why:** Power users want complex formulas

**Features:**
- [ ] Multi-factor formulas (e.g., "1% of revenue OR $5,000, whichever is GREATER")
- [ ] Conditional materiality (different thresholds by account type)
- [ ] Formula templates library

---

**Q4 Targets:**
- Users: 5,000
- ARR: $250K
- SOC 2 certified ✅

---

## 2027 Roadmap (High-Level)

### Q1 2027: International Expansion
- Multi-language support (Spanish, French, German)
- Multi-currency support
- IFRS account classification (in addition to GAAP)
- European data residency (GDPR)

### Q2 2027: Open-Source Core
- Open-source audit engine (trust through transparency)
- Community contributions
- Plugin ecosystem

### Q3 2027: Real-Time Collaboration
- Live co-working sessions (like Google Docs)
- Team comments on anomalies
- @mentions and notifications

### Q4 2027: Predictive Analytics
- Cash flow forecasting
- Scenario modeling ("What if revenue drops 20%?")
- Anomaly prediction (flag potential issues before they occur)

---

## Feature Prioritization Framework (RICE)

| Feature | Reach | Impact | Confidence | Effort | RICE Score |
|---------|-------|--------|------------|--------|------------|
| **Mobile apps** | 5000 | 3 | 80% | 8 | 1500 |
| **Team collaboration** | 500 | 3 | 90% | 4 | 338 |
| **QB integration** | 2000 | 3 | 70% | 4 | 1050 |
| **AI explanations** | 5000 | 2 | 60% | 3 | 2000 |
| **White-label** | 50 | 2 | 80% | 2 | 40 |

**RICE = (Reach × Impact × Confidence) / Effort**

---

## Backlog (Nice-to-Have)

**Low Priority, Future Consideration:**
- [ ] API webhooks (real-time event notifications)
- [ ] Custom report templates (user-defined layouts)
- [ ] Data visualization (interactive charts)
- [ ] Excel add-in (analyze without leaving Excel)
- [ ] Desktop app (Electron wrapper)

---

## Sunset / Will Not Build

**Features we've decided NOT to pursue:**

| Feature | Why Not |
|---------|---------|
| **Full accounting suite** | Out of scope (we're diagnostics-only) |
| **Tax preparation** | Not our expertise |
| **Payroll integration** | Too far from core value prop |
| **Social features** | Not relevant to workflow |

---

## Changelog

**Version 1.0 (Feb 2026):** Initial roadmap through Q4 2027

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-04 | Product | Initial publication |

---

*Paciolus — Roadmap to 50,000 Users*
