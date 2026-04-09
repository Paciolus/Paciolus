"""Centralized configuration for the Paciolus overnight agent system."""

import datetime
import os
import sys
from pathlib import Path

# ── Load environment early ─────────────────────────────────────────────────
# This ensures env vars are available whether running from orchestrator or standalone.
try:
    from dotenv import load_dotenv
    _project = Path("D:/Dev/Paciolus")
    _overnight_env = _project / ".env.overnight"
    if _overnight_env.exists():
        load_dotenv(_overnight_env, override=True)
    _backend_env = _project / "backend" / ".env"
    if _backend_env.exists():
        load_dotenv(_backend_env, override=False)
except ImportError:
    pass

# ── Paths ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path("D:/Dev/Paciolus")
BACKEND_ROOT = PROJECT_ROOT / "backend"
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
PYTHON_BIN = PROJECT_ROOT / "backend/venv/Scripts/python.exe"
# System Python has pytest + all backend deps; venv has anthropic SDK
SYSTEM_PYTHON = Path("C:/Python312/python.exe")
REPORTS_DIR = PROJECT_ROOT / "reports/nightly"
BASELINE_FILE = REPORTS_DIR / ".baseline.json"

# ── Date tokens ────────────────────────────────────────────────────────────
TODAY = datetime.date.today().isoformat()
REPORT_PATH = REPORTS_DIR / f"{TODAY}.md"

# ── API credentials ────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "paciolus-scout/1.0")

# Claude model for API calls
CLAUDE_MODEL = "claude-sonnet-4-20250514"


def require_anthropic_key() -> str:
    """Return the Anthropic API key or exit with a clear error."""
    if not ANTHROPIC_API_KEY:
        print(
            "ERROR: ANTHROPIC_API_KEY not set. "
            "Set it in .env.overnight or export it before running.",
            file=sys.stderr,
        )
        sys.exit(1)
    return ANTHROPIC_API_KEY


# ── Known bugs tracker ─────────────────────────────────────────────────────
KNOWN_BUGS = {
    "BUG-001": "Suggested procedures rotation bug — procedures repeat rather than rotate across reports",
    "BUG-002": "Hardcoded risk tier labels — labels do not reflect dynamic risk scoring",
    "BUG-003": "PDF cell overflow — long text overflows table cells in generated PDFs",
    "BUG-004": "Orphaned ASC 250-10 references — appear in reports where not applicable",
    "BUG-005": "PP&E ampersand escaping — & renders as &amp; in PDF output",
    "BUG-006": "Identical data quality scores — multiple reports return same score regardless of input",
    "BUG-007": "Empty drill-down stubs — drill-down sections render with no content",
}

BUG_KEYWORDS = {
    # Keywords target the specific ANTI-PATTERNS that indicate the bug is present.
    # Never use fix-code patterns (e.g., the function/param the fix introduced)
    # or domain terms that legitimately appear in the codebase after a fix.
    "BUG-001": ["if not alts:\n        return primary"],
    "BUG-002": ['config.risk_assessments["low"]'],
    "BUG-003": ["doc_width / n_cols"],
    # BUG-004: Was "ASC 250-10" but that legitimately appears in allowlisted YAML.
    # The anti-pattern was unconditional inclusion — detect the old import path instead.
    "BUG-004": ["fasb_250_10_unguarded"],
    "BUG-005": ["raw &", "unescaped ampersand"],
    # BUG-006: Was "domain_offset"/"domain_hash" but those ARE the fix code.
    # The anti-pattern was identical score regardless of domain — detect the old pattern.
    "BUG-006": ["score = round(weighted_score, 1)\n    return"],
    # BUG-007: Was "suppress_empty: bool = True" but that IS the fix parameter.
    # The anti-pattern was unconditional stub rendering — detect old pattern.
    "BUG-007": ["build_drill_down_stub"],
}
