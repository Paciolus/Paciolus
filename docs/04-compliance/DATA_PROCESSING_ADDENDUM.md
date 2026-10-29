# Data Processing Addendum — DRAFT

**Version:** 2.0-draft · **Status:** draft, not yet offered for signature · **Owner:** privacy@paciolus.com

> **This is a draft.** It has not been reviewed by counsel and no customer has signed it. Counsel
> reviews it with the Terms and Privacy Policy once the website is finalized (`tasks/ceo-actions.md`).
> Until then, organizations that need a DPA can request one at privacy@paciolus.com. Version 1.0 was
> required at checkout while describing a database host, a breach-impact argument and a
> position that financial data was not stored that were not accurate; the checkout checkbox was removed in Sprint 844.
> The previous text is in
> [`archive/DATA_PROCESSING_ADDENDUM_pre-sprint-845_2026-10-24.md`](archive/DATA_PROCESSING_ADDENDUM_pre-sprint-845_2026-10-24.md).

## 1. Roles

The Customer is the controller of personal data in what it uploads to or enters into Paciolus. Paciolus
processes that data as the Customer's processor, only to provide the service, and on the Customer's
documented instructions (this addendum, the Terms and the Customer's use of the product).

## 2. What is processed

- **Uploaded files** are processed in memory for the request and not kept. A previewed file may be held
  in memory for up to 10 minutes so the tool can reuse it.
- **Stored:** account data; client metadata; a summary of each analysis (category totals, ratios, row
  counts, total debits and credits, materiality, anomaly counts, the names of flagged accounts without
  amounts); Customer-entered engagement content, including analytical expectations (expected and
  actual values) and uncorrected misstatements (account, debit or credit, amount); activity history;
  security events.
- **Shared reports:** a report the Customer chooses to share by link is stored in Cloudflare R2 for
  24–48 hours and then deleted.

Uploaded data may contain personal data of the Customer's clients' employees, vendors or customers
(for example payroll registers or vendor lists). The Customer must not upload special-category data.

## 3. Subprocessors

Listed in the [Subprocessor List](SUBPROCESSOR_LIST.md). Paciolus will update the list before adding a
subprocessor and notify Customers who have asked to be told.

## 4. Security

As described in the [Security Policy](SECURITY_POLICY.md). Paciolus holds no SOC 2 or ISO certification.

## 5. Breaches

Paciolus will tell the Customer without undue delay after becoming aware of a personal-data breach
affecting the Customer's data, with what is known, and will help the Customer meet its own
notification duties.

## 6. Deletion and return

The Customer can export everything stored about its account (Settings → Profile → Your Data) and
delete the account there at any time; deletion is immediate. On termination, stored data is deleted
within 30 days. Stripe keeps the payment records the law requires.

## 7. Assistance and audits

Paciolus will answer reasonable written questions about its processing and help the Customer respond to
data-subject requests. There is no third-party audit report to provide.
