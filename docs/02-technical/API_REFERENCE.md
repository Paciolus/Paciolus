# API Reference

**Document Classification:** Public (Developer Documentation)  
**Version:** 1.0  
**Last Updated:** February 4, 2026  
**API Version:** 0.16.0  
**Owner:** Engineering Team

---

## Introduction

This document provides complete reference documentation for the Paciolus REST API. The API enables trial balance diagnostics, client management, and user account operations.

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
3. [Trial Balance Diagnostics](#3-trial-balance-diagnostics)
4. [Activity & History](#4-activity--history)
5. [User Settings](#5-user-settings)
6. [Dashboard](#6-dashboard)
7. [Error Handling](#7-error-handling)
8. [Rate Limiting](#8-rate-limiting)
9. [Changelog](#9-changelog)

---

## 1. Authentication

### 1.1 Register User

**Endpoint:** `POST /auth/register`  
**Authentication:** Not required  
**Description:** Create a new user account

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

**Errors:**
- `400 Bad Request` — Email already exists or password doesn't meet requirements
- `422 Unprocessable Entity` — Invalid input format

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character (!@#$%^&*)

---

### 1.2 Login

**Endpoint:** `POST /auth/login`  
**Authentication:** Not required  
**Description:** Authenticate and receive JWT token

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "created_at": "2026-02-04T10:00:00Z",
    "last_login": "2026-02-04T15:30:00Z"
  }
}
```

**Errors:**
- `401 Unauthorized` — Invalid credentials

**Token Expiration:** 8 hours (28800 seconds)

---

### 1.3 Get Current User

**Endpoint:** `GET /auth/me`  
**Authentication:** Required  
**Description:** Get authenticated user's information

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "created_at": "2026-02-04T10:00:00Z",
  "last_login": "2026-02-04T15:30:00Z"
}
```

**Errors:**
- `401 Unauthorized` — Invalid or expired token

---

## 2. Client Management

### 2.1 List Clients

**Endpoint:** `GET /clients`  
**Authentication:** Required  
**Description:** Get all clients for authenticated user

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | integer | No | 1 | Page number (1-indexed) |
| `page_size` | integer | No | 50 | Items per page (max 100) |
| `search` | string | No | — | Search by client name |

**Example Request:**
```
GET /clients?page=1&page_size=25&search=Acme
```

**Response (200 OK):**
```json
{
  "clients": [
    {
      "id": "client-uuid-1",
      "user_id": "user-uuid",
      "name": "Acme Corp",
      "industry": "technology",
      "fiscal_year_end": "12-31",
      "created_at": "2026-01-15T10:00:00Z",
      "updated_at": "2026-02-01T14:30:00Z",
      "settings": "{}"
    }
  ],
  "total_count": 42,
  "page": 1,
  "page_size": 25
}
```

---

### 2.2 Create Client

**Endpoint:** `POST /clients`  
**Authentication:** Required  
**Description:** Create a new client

**Request Body:**
```json
{
  "name": "Acme Corp",
  "industry": "technology",
  "fiscal_year_end": "12-31",
  "settings": "{}"
}
```

**Response (201 Created):**
```json
{
  "id": "client-uuid-1",
  "user_id": "user-uuid",
  "name": "Acme Corp",
  "industry": "technology",
  "fiscal_year_end": "12-31",
  "created_at": "2026-02-04T10:00:00Z",
  "updated_at": "2026-02-04T10:00:00Z",
  "settings": "{}"
}
```

**Errors:**
- `400 Bad Request` — Invalid industry or fiscal year format
- `401 Unauthorized` — Not authenticated

**Industry Options:**
- `technology`
- `healthcare`
- `manufacturing`
- `retail`
- `professional_services`
- `real_estate`
- `construction`
- `hospitality`
- `nonprofit`
- `education`
- `other`

---

### 2.3 Get Client by ID

**Endpoint:** `GET /clients/{client_id}`  
**Authentication:** Required  
**Description:** Get specific client details

**Response (200 OK):**
```json
{
  "id": "client-uuid-1",
  "user_id": "user-uuid",
  "name": "Acme Corp",
  "industry": "technology",
  "fiscal_year_end": "12-31",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-02-01T14:30:00Z",
  "settings": "{}"
}
```

**Errors:**
- `404 Not Found` — Client doesn't exist or not owned by user

---

### 2.4 Update Client

**Endpoint:** `PUT /clients/{client_id}`  
**Authentication:** Required  
**Description:** Update client information

**Request Body** (all fields optional):
```json
{
  "name": "Acme Corporation",
  "industry": "manufacturing",
  "fiscal_year_end": "06-30"
}
```

**Response (200 OK):**
```json
{
  "id": "client-uuid-1",
  "user_id": "user-uuid",
  "name": "Acme Corporation",
  "industry": "manufacturing",
  "fiscal_year_end": "06-30",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-02-04T16:00:00Z",
  "settings": "{}"
}
```

---

### 2.5 Delete Client

**Endpoint:** `DELETE /clients/{client_id}`  
**Authentication:** Required  
**Description:** Delete a client

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Client deleted successfully"
}
```

---

## 3. Trial Balance Diagnostics

### 3.1 Inspect Workbook

**Endpoint:** `POST /audit/inspect-workbook`  
**Authentication:** Required  
**Description:** Inspect Excel workbook sheets before analysis

**Request:** `multipart/form-data`
```
file: <Excel file>
```

**Response (200 OK):**
```json
{
  "filename": "Q4_2024_TB.xlsx",
  "sheets": [
    {
      "name": "Consolidated",
      "row_count": 1547,
      "columns": ["Account", "Debit", "Credit"]
    },
    {
      "name": "Entity A",
      "row_count": 823,
      "columns": ["Account Name", "DR", "CR"]
    }
  ]
}
```

**Errors:**
- `400 Bad Request` — Invalid file format (must be .xlsx or .xls)
- `413 Payload Too Large` — File exceeds 50MB limit

---

### 3.2 Analyze Trial Balance

**Endpoint:** `POST /audit/trial-balance`  
**Authentication:** Required  
**Description:** Upload and analyze trial balance (Zero-Storage: processed in-memory, never stored)

**Request:** `multipart/form-data`
```
file: <CSV or Excel file>
materiality_threshold: 500 (optional, default from settings)
column_mappings: {"Account": "account_name", ...} (optional)
selected_sheets: ["Consolidated", "Entity A"] (optional, for Excel)
consolidate: true (optional, for multi-sheet)
```

**Response (200 OK):**
```json
{
  "summary": {
    "total_records": 1547,
    "total_debits": 25000000.00,
    "total_credits": 25000000.00,
    "is_balanced": true,
    "variance": 0.00,
    "materiality_threshold": 500.00
  },
  "classifications": {
    "assets": 542,
    "liabilities": 234,
    "equity": 123,
    "revenue": 345,
    "expenses": 303
  },
  "anomalies": [
    {
      "account_name": "Accounts Receivable",
      "account_number": "1200",
      "debit_balance": -15000.00,
      "credit_balance": 0.00,
      "anomaly_type": "abnormal_credit_balance",
      "severity": "high",
      "expected_balance_type": "debit",
      "is_material": true
    }
  ],
  "material_anomalies": 3,
  "immaterial_anomalies": 7
}
```

**Errors:**
- `400 Bad Request` — Invalid file format or column mapping
- `413 Payload Too Large` — File exceeds 50MB
- `422 Unprocessable Entity` — Missing required columns

**Zero-Storage Note:** The uploaded file is processed in-memory and immediately discarded. No financial data is persisted.

---

### 3.3 Export PDF Report

**Endpoint:** `POST /export/pdf`  
**Authentication:** Required  
**Description:** Generate PDF diagnostic report (Zero-Storage: generated on-demand, streamed to client)

**Request Body:**
```json
{
  "audit_result": { /* Full audit result from /audit/trial-balance */ },
  "client_name": "Acme Corp",
  "period_ending": "2024-12-31"
}
```

**Response:** Binary PDF file (streamed)

**Headers:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="Acme_Corp_Diagnostic_20260204.pdf"
```

---

### 3.4 Export Excel Workpaper

**Endpoint:** `POST /export/excel`  
**Authentication:** Required  
**Description:** Generate Excel workpaper with 4 tabs (Zero-Storage: generated on-demand, streamed to client)

**Request Body:**
```json
{
  "audit_result": { /* Full audit result */ },
  "client_name": "Acme Corp"
}
```

**Response:** Binary Excel file (streamed)

**Tabs:**
1. Summary
2. Standardized Trial Balance
3. Flagged Anomalies
4. Key Financial Ratios

---

## 4. Activity & History

### 4.1 Log Activity

**Endpoint:** `POST /activity/log`  
**Authentication:** Required  
**Description:** Log an audit activity (metadata only, GDPR-compliant)

**Request Body:**
```json
{
  "filename": "ClientABC_Q4.xlsx",
  "record_count": 1547,
  "total_debits": 25000000.00,
  "total_credits": 25000000.00,
  "materiality_threshold": 500.00,
  "was_balanced": true,
  "anomaly_count": 10,
  "material_count": 3,
  "immaterial_count": 7,
  "is_consolidated": false,
  "sheet_count": 1
}
```

**Response (201 Created):**
```json
{
  "id": "activity-uuid",
  "filename_hash": "abc123def456...",
  "filename_display": "ClientABC_Q4...",
  "timestamp": "2026-02-04T10:00:00Z",
  "record_count": 1547,
  "total_debits": 25000000.00,
  "total_credits": 25000000.00,
  "materiality_threshold": 500.00,
  "was_balanced": true,
  "anomaly_count": 10,
  "material_count": 3,
  "immaterial_count": 7
}
```

**Privacy Note:** Filename is hashed (SHA-256) before storage. Only first 12 characters stored for user convenience.

---

### 4.2 Get Activity History

**Endpoint:** `GET /activity/history`  
**Authentication:** Required  
**Description:** Get paginated activity history

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `page_size` | integer | 20 | Items per page (max 100) |

**Response (200 OK):**
```json
{
  "activities": [
    {
      "id": "activity-uuid",
      "filename_hash": "abc123...",
      "filename_display": "ClientABC_Q4...",
      "timestamp": "2026-02-04T10:00:00Z",
      "record_count": 1547,
      "total_debits": 25000000.00,
      "total_credits": 25000000.00,
      "was_balanced": true,
      "anomaly_count": 10
    }
  ],
  "total_count": 42,
  "page": 1,
  "page_size": 20
}
```

---

### 4.3 Clear Activity History

**Endpoint:** `DELETE /activity/clear`  
**Authentication:** Required  
**Description:** Delete all activity logs (GDPR Right to Erasure)

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Deleted 42 activity entries",
  "deleted_count": 42
}
```

---

## 5. User Settings

### 5.1 Get Settings

**Endpoint:** `GET /settings`  
**Authentication:** Required  
**Description:** Get user preferences

**Response (200 OK):**
```json
{
  "materiality_threshold": 500.00,
  "materiality_formula": {
    "type": "fixed",
    "value": 500.00
  },
  "theme": "dark",
  "notifications_enabled": true
}
```

---

### 5.2 Update Settings

**Endpoint:** `PUT /settings`  
**Authentication:** Required  
**Description:** Update user preferences

**Request Body:**
```json
{
  "materiality_threshold": 1000.00,
  "theme": "light"
}
```

**Response (200 OK):**
```json
{
  "materiality_threshold": 1000.00,
  "materiality_formula": {
    "type": "fixed",
    "value": 1000.00
  },
  "theme": "light",
  "notifications_enabled": true
}
```

---

## 6. Dashboard

### 6.1 Get Dashboard Stats

**Endpoint:** `GET /dashboard/stats`  
**Authentication:** Required  
**Description:** Get user dashboard statistics

**Response (200 OK):**
```json
{
  "total_clients": 15,
  "assessments_today": 3,
  "last_assessment_date": "2026-02-04T15:30:00Z",
  "total_assessments": 127
}
```

---

## 7. Error Handling

### 7.1 Error Response Format

All errors follow this structure:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### 7.2 HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| `200` | OK | Request succeeded |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid input, validation error |
| `401` | Unauthorized | Missing or invalid authentication token |
| `403` | Forbidden | Authenticated but not authorized for resource |
| `404` | Not Found | Resource doesn't exist |
| `413` | Payload Too Large | File exceeds 50MB limit |
| `422` | Unprocessable Entity | Invalid JSON structure |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Unexpected server error |
| `503` | Service Unavailable | Server temporarily unavailable |

---

## 8. Rate Limiting

**Limits:**
- **Authenticated users:** 1000 requests/hour
- **Unauthenticated users:** 100 requests/hour

**Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1675512000
```

**Rate Limit Exceeded (429):**
```json
{
  "detail": "Rate limit exceeded. Try again in 15 minutes."
}
```

---

## 9. Changelog

### v0.16.0 (2026-02-04)
- Added `/dashboard/stats` endpoint
- Added workspace architecture support

### v0.15.0 (2026-02-03)
- Multi-sheet Excel consolidation
- Workbook inspection endpoint

### v0.9.0 (2026-02-02)
- Client management endpoints
- Portfolio dashboard API

### v0.7.0 (2026-01-30)
- Activity logging endpoints
- GDPR-compliant metadata storage

### v0.6.0 (2026-01-29)
- JWT authentication
- User registration and login

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

# Upload trial balance
headers = {"Authorization": f"Bearer {token}"}
files = {"file": open("trial_balance.csv", "rb")}
data = {"materiality_threshold": 500}

response = requests.post(
    "https://api.paciolus.com/audit/trial-balance",
    headers=headers,
    files=files,
    data=data
)
result = response.json()
print(f"Balanced: {result['summary']['is_balanced']}")
```

---

**JavaScript (fetch API):**

```javascript
// Login
const loginResponse = await fetch('https://api.paciolus.com/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePass123!'
  })
});
const { access_token } = await loginResponse.json();

// Get clients
const clientsResponse = await fetch('https://api.paciolus.com/clients', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const { clients } = await clientsResponse.json();
console.log(`You have ${clients.length} clients`);
```

---

### Appendix B: Postman Collection

Download Postman collection: [paciolus-api.postman_collection.json](#)

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-04 | Engineering | Initial publication |

---

*Paciolus API v0.16.0 — Zero-Storage Trial Balance Diagnostic Intelligence*
