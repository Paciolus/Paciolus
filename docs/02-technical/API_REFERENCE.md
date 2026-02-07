# API Reference

**Document Classification:** Public (Developer Documentation)
**Version:** 2.0
**Last Updated:** February 6, 2026
**API Version:** 0.70.0
**Owner:** Engineering Team

---

## Introduction

This document provides complete reference documentation for the Paciolus REST API. The API enables a 5-tool audit intelligence suite, client management, and user account operations across 17 APIRouter modules.

**Base URL:**
- **Production:** `https://api.paciolus.com`
- **Staging:** `https://api-staging.paciolus.com`
- **Local Development:** `http://localhost:8000`

**Authentication:** Bearer token (JWT)
**Format:** JSON
**Rate Limiting:** 1000 requests/hour (authenticated), 100 requests/hour (unauthenticated)

**Interactive Documentation:**
- Swagger UI: `https://api.paciolus.com/docs`
- ReDoc: `https://api.paciolus.com/redoc`

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Client Management](#2-client-management)
3. [Trial Balance Diagnostics (Tool 1)](#3-trial-balance-diagnostics-tool-1)
4. [Multi-Period Comparison (Tool 2)](#4-multi-period-comparison-tool-2)
5. [Journal Entry Testing (Tool 3)](#5-journal-entry-testing-tool-3)
6. [AP Payment Testing (Tool 4)](#6-ap-payment-testing-tool-4)
7. [Bank Reconciliation (Tool 5)](#7-bank-reconciliation-tool-5)
8. [Export Endpoints](#8-export-endpoints)
9. [Activity & History](#9-activity--history)
10. [Settings & Benchmarks](#10-settings--benchmarks)
11. [Error Handling](#11-error-handling)
12. [Changelog](#12-changelog)

---

## 1. Authentication

### 1.1 Register User

**Endpoint:** `POST /auth/register`
**Authentication:** Not required

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2026-02-04T10:00:00Z"
  }
}
```

**Password Requirements:** Min 8 chars, uppercase, lowercase, number, special character.

---

### 1.2 Login

**Endpoint:** `POST /auth/login`
**Authentication:** Not required

**Request/Response:** Same structure as Register. Returns JWT token (8-hour expiration).

---

### 1.3 Get Current User

**Endpoint:** `GET /auth/me`
**Authentication:** Required

---

### 1.4 Email Verification

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/verify-email` | POST | No | Verify email with token |
| `/auth/resend-verification` | POST | Yes | Resend verification email |
| `/auth/verification-status` | GET | Yes | Check verification status |
| `/auth/csrf` | GET | No | Get CSRF token |

---

## 2. Client Management

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `GET /clients` | GET | Yes | List user's clients (paginated, searchable) |
| `POST /clients` | POST | Yes | Create client |
| `GET /clients/{id}` | GET | Yes | Get client details |
| `PUT /clients/{id}` | PUT | Yes | Update client |
| `DELETE /clients/{id}` | DELETE | Yes | Delete client |
| `GET /clients/industries` | GET | No | List available industries |

**Industry Options:** technology, healthcare, manufacturing, retail, professional_services, real_estate, construction, hospitality, nonprofit, education, other

---

## 3. Trial Balance Diagnostics (Tool 1)

### 3.1 Inspect Workbook

**Endpoint:** `POST /audit/inspect-workbook`
**Authentication:** Verified user required
**Content-Type:** multipart/form-data

Returns sheet names, row counts, and column headers for multi-sheet Excel files.

### 3.2 Analyze Trial Balance

**Endpoint:** `POST /audit/trial-balance`
**Authentication:** Verified user required
**Content-Type:** multipart/form-data

**Form Fields:**
- `file` — CSV or Excel file (required)
- `materiality_threshold` — Override threshold (optional)
- `column_mappings` — JSON column mapping (optional)
- `selected_sheets` — Sheet names for Excel (optional)
- `consolidate` — Merge sheets (optional)

**Response:** Summary (totals, balance status), classifications, anomalies, lead sheet groupings, financial ratios, risk summary.

**Zero-Storage Note:** File processed in-memory, immediately discarded.

---

## 4. Multi-Period Comparison (Tool 2)

### 4.1 Two-Way Comparison

**Endpoint:** `POST /audit/compare-periods`
**Authentication:** Verified user required

**Request Body:**
```json
{
  "current_accounts": [
    {"account_name": "Cash", "debit": 50000, "credit": 0}
  ],
  "prior_accounts": [
    {"account_name": "Cash", "debit": 45000, "credit": 0}
  ]
}
```

**Response:** MovementSummary with categorized account movements (NEW, CLOSED, SIGN_CHANGE, INCREASE, DECREASE, UNCHANGED), significance tiers, lead sheet grouping.

### 4.2 Three-Way Comparison

**Endpoint:** `POST /audit/compare-three-way`
**Authentication:** Verified user required

Accepts current, prior, and budget period accounts. Returns two-way movements enriched with budget variance data.

### 4.3 Export Movements CSV

**Endpoint:** `POST /export/csv/movements`
**Authentication:** Verified user required

---

## 5. Journal Entry Testing (Tool 3)

### 5.1 Run JE Test Battery

**Endpoint:** `POST /audit/journal-entries`
**Authentication:** Verified user required
**Content-Type:** multipart/form-data

**Form Fields:**
- `file` — GL export CSV/Excel (required)
- `config` — JSON test configuration (optional, 18 threshold fields)

**Response:**
```json
{
  "test_results": [
    {
      "test_key": "JE-T1",
      "test_name": "Unbalanced Journal Entries",
      "tier": "structural",
      "passed": false,
      "flagged_count": 3,
      "total_tested": 1000,
      "flag_rate": 0.003,
      "severity": "high",
      "flagged_entries": [...]
    }
  ],
  "composite_score": {
    "score": 35.5,
    "risk_tier": "ELEVATED",
    "tests_run": 18,
    "tests_with_findings": 5
  },
  "data_quality": {...},
  "column_detection": {...}
}
```

**18 Tests:**
- Tier 1 (Structural): Unbalanced, Missing Fields, Duplicates, Backdated, Unusual Amounts
- Tier 2 (Statistical): Benford's Law, Round Amounts, Weekend Posting, Unusual Users, Description Anomalies
- Tier 3 (Advanced): Split Transactions, Sequential Anomalies, Cross-Period, Related Party, Fraud Keywords

### 5.2 Stratified Sampling

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /audit/journal-entries/sample/preview` | POST | Preview sample stratification |
| `POST /audit/journal-entries/sample` | POST | Execute CSPRNG-based sample selection |

---

## 6. AP Payment Testing (Tool 4)

### 6.1 Run AP Test Battery

**Endpoint:** `POST /audit/ap-payments`
**Authentication:** Verified user required
**Content-Type:** multipart/form-data

**Form Fields:**
- `file` — AP payment register CSV/Excel (required)
- `config` — JSON AP test configuration (optional, 14 threshold fields)

**Response:**
```json
{
  "test_results": [
    {
      "test_key": "AP-T1",
      "test_name": "Exact Duplicate Payments",
      "tier": "structural",
      "flagged_count": 2,
      "flagged_payments": [...]
    }
  ],
  "composite_score": {
    "score": 22.0,
    "risk_tier": "LOW",
    "tests_run": 13,
    "tests_with_findings": 3
  },
  "data_quality": {
    "overall_score": 0.92,
    "field_completeness": {...}
  },
  "column_detection": {
    "detected_columns": {...},
    "confidence": 0.95
  }
}
```

**13 Tests:**
- Tier 1 (Structural): Exact Duplicates, Missing Fields, Check Gaps, Round Amounts, Payment Before Invoice
- Tier 2 (Statistical): Fuzzy Duplicates, Invoice Reuse, Unusual Amounts (z-score), Weekend Payments, High-Frequency Vendors
- Tier 3 (Fraud): Vendor Variations (SequenceMatcher), Just-Below-Threshold, Suspicious Descriptions

---

## 7. Bank Reconciliation (Tool 5)

### 7.1 Reconcile Bank Statement

**Endpoint:** `POST /audit/bank-reconciliation`
**Authentication:** Verified user required
**Content-Type:** multipart/form-data

**Form Fields:**
- `bank_file` — Bank statement CSV/Excel (required)
- `ledger_file` — GL cash detail CSV/Excel (required)
- `bank_column_mappings` — JSON column mapping (optional)
- `ledger_column_mappings` — JSON column mapping (optional)

**Response:**
```json
{
  "summary": {
    "total_bank_transactions": 150,
    "total_ledger_transactions": 145,
    "matched_count": 130,
    "bank_only_count": 20,
    "ledger_only_count": 15,
    "matched_amount": 250000.00,
    "bank_only_amount": 15000.00,
    "ledger_only_amount": 12000.00,
    "reconciling_difference": 3000.00,
    "match_rate": 0.867
  },
  "matches": [...],
  "bank_column_detection": {...},
  "ledger_column_detection": {...}
}
```

### 7.2 Export Reconciliation CSV

**Endpoint:** `POST /export/csv/bank-rec`
**Authentication:** Verified user required

Exports 4-section CSV: matched transactions, bank-only items, ledger-only items, summary.

---

## 8. Export Endpoints

All export endpoints require verified user authentication and return streamed binary files.

| Endpoint | Method | Format | Description |
|----------|--------|--------|-------------|
| `POST /export/pdf` | POST | PDF | TB diagnostic report (Renaissance Ledger) |
| `POST /export/excel` | POST | Excel | TB workpaper (4-tab) |
| `POST /export/csv/trial-balance` | POST | CSV | Standardized trial balance |
| `POST /export/csv/anomalies` | POST | CSV | Flagged anomalies |
| `POST /export/leadsheets` | POST | Excel | A-Z lead sheet workbook |
| `POST /export/financial-statements` | POST | PDF/Excel | Balance Sheet + Income Statement (`?format=pdf\|excel`) |
| `POST /export/je-testing-memo` | POST | PDF | JE Testing Memo (PCAOB AS 1215) |
| `POST /export/csv/je-testing` | POST | CSV | Flagged journal entries |
| `POST /export/ap-testing-memo` | POST | PDF | AP Testing Memo (ISA 240 / PCAOB AS 2401) |
| `POST /export/csv/ap-testing` | POST | CSV | Flagged AP payments |
| `POST /export/csv/bank-rec` | POST | CSV | Bank reconciliation report |
| `POST /export/csv/movements` | POST | CSV | Multi-period movements |

---

## 9. Activity & History

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `POST /activity/log` | POST | Yes | Log audit activity (metadata only) |
| `GET /activity/history` | GET | Yes | Paginated activity history |
| `DELETE /activity/clear` | DELETE | Yes | Clear all history (GDPR Right to Erasure) |
| `GET /dashboard/stats` | GET | Yes | Dashboard statistics |

---

## 10. Settings & Benchmarks

### Settings

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `GET /settings/practice` | GET | Yes | Get practice settings |
| `PUT /settings/practice` | PUT | Yes | Update practice settings (JE + AP thresholds) |
| `GET /clients/{id}/settings` | GET | Yes | Get client-specific settings |
| `PUT /clients/{id}/settings` | PUT | Yes | Update client settings |
| `POST /settings/materiality/preview` | POST | Yes | Preview materiality formula |
| `GET /settings/materiality/resolve` | GET | Yes | Resolve materiality chain |

### Benchmarks (Public)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `GET /benchmarks/industries` | GET | No | List benchmark industries |
| `GET /benchmarks/sources` | GET | No | Benchmark data sources |
| `GET /benchmarks/{industry}` | GET | No | Get industry benchmarks |
| `POST /benchmarks/compare` | POST | No | Compare ratios to benchmarks |

**Industries:** Manufacturing, Retail, Technology, Healthcare, Professional Services, Construction

### Trends & Prior Period

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `GET /clients/{id}/trends` | GET | Yes | Ratio trend data |
| `GET /clients/{id}/industry-ratios` | GET | Yes | Industry-specific ratios |
| `GET /clients/{id}/rolling-analysis` | GET | Yes | Rolling window analysis |
| `POST /clients/{id}/periods` | POST | Yes | Store period snapshot |
| `GET /clients/{id}/periods` | GET | Yes | List stored periods |
| `POST /audit/compare` | POST | Yes | Compare two periods |

### Adjusting Entries

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `POST /audit/adjustments` | POST | Yes | Create adjusting entry |
| `GET /audit/adjustments` | GET | Yes | List entries |
| `GET /audit/adjustments/{id}` | GET | Yes | Get entry details |
| `PUT /audit/adjustments/{id}/status` | PUT | Yes | Update entry status |
| `DELETE /audit/adjustments/{id}` | DELETE | Yes | Delete entry |
| `POST /audit/adjustments/apply` | POST | Yes | Apply entries to TB |
| `GET /audit/adjustments/types` | GET | Yes | Entry type options |
| `GET /audit/adjustments/statuses` | GET | Yes | Status options |

### User Management

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `PUT /users/me` | PUT | Yes | Update user profile |
| `PUT /users/me/password` | PUT | Yes | Change password |

---

## 11. Error Handling

All errors return JSON: `{"detail": "Error message"}`

| Code | Meaning |
|------|---------|
| `200` | OK |
| `201` | Created |
| `400` | Bad Request (invalid input) |
| `401` | Unauthorized (missing/invalid token) |
| `403` | Forbidden (authenticated but not authorized / unverified) |
| `404` | Not Found |
| `413` | Payload Too Large (>50MB) |
| `422` | Unprocessable Entity |
| `429` | Too Many Requests |
| `500` | Internal Server Error |

---

## 12. Changelog

### v0.70.0 (2026-02-06)
- 5-tool navigation standardization
- Homepage updated for 5-tool suite
- Version 0.70.0

### v0.60.0 (2026-02-06)
- Bank Reconciliation: `/audit/bank-reconciliation`, `/export/csv/bank-rec`
- AP Payment Testing: `/audit/ap-payments`, `/export/ap-testing-memo`, `/export/csv/ap-testing`
- Financial Statements: `/export/financial-statements`
- JE Testing Sampling: `/audit/journal-entries/sample`, `/audit/journal-entries/sample/preview`
- Diagnostic zone protection (3-state auth gating)

### v0.40.0 (2026-02-06)
- Multi-Period: `/audit/compare-periods`, `/audit/compare-three-way`
- JE Testing: `/audit/journal-entries`
- JE Testing Memo: `/export/je-testing-memo`
- Platform tool routes (`/tools/*`)

### v0.16.0 (2026-02-04)
- Dashboard stats, workspace architecture
- Multi-sheet Excel, workbook inspection
- Client management, activity logging
- JWT authentication, user registration

---

## Appendices

### Appendix A: Code Examples

**Python (requests library):**

```python
import requests

# Login
response = requests.post(
    "https://api.paciolus.com/auth/login",
    json={"email": "user@example.com", "password": "SecurePass123!"}
)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Upload trial balance
files = {"file": open("trial_balance.csv", "rb")}
result = requests.post(
    "https://api.paciolus.com/audit/trial-balance",
    headers=headers, files=files
).json()

# Run AP Payment Testing
files = {"file": open("ap_register.csv", "rb")}
ap_result = requests.post(
    "https://api.paciolus.com/audit/ap-payments",
    headers=headers, files=files
).json()
print(f"Risk Tier: {ap_result['composite_score']['risk_tier']}")

# Bank Reconciliation
files = {
    "bank_file": open("bank_statement.csv", "rb"),
    "ledger_file": open("gl_cash.csv", "rb")
}
rec_result = requests.post(
    "https://api.paciolus.com/audit/bank-reconciliation",
    headers=headers, files=files
).json()
print(f"Match Rate: {rec_result['summary']['match_rate']:.0%}")
```

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.0 | 2026-02-06 | Engineering | Added Tools 2-5 endpoints, export endpoints, v0.70.0 |
| 1.0 | 2026-02-04 | Engineering | Initial publication |

---

*Paciolus API v0.70.0 — Professional Audit Intelligence Suite*
