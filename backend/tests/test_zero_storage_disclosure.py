"""
Sprint 783: every persisted model that holds money or account identifiers must be
disclosed in the Zero-Storage compliance document.

WHY THIS EXISTS
Zero-Storage is the product's central trust claim, made to customers who carry
their own professional confidentiality obligations. Two features shipped
(ISA 450 uncorrected misstatements, ISA 520 analytical expectations) that
legitimately persist practitioner-entered account names and amounts. Both were
documented in their own coverage docs — but the main
ZERO_STORAGE_ARCHITECTURE.md still carried an absolute claim that individual
account names are "Never Stored", and its §2.2 exception list omitted both
tables. The documents contradicted each other for roughly six months.

That is the same failure mode as the AS 1215 citation drift: a claim fixed in
one place and left wrong in another, with nothing mechanically tying them
together. This test is the tie.

It deliberately guards the dangerous direction only — a model that stores
money or account identifiers without being disclosed. Documenting a table that
no longer exists is harmless by comparison.
"""

import re
from pathlib import Path

import pytest
from sqlalchemy import Numeric

BACKEND = Path(__file__).resolve().parent.parent
ZERO_STORAGE_DOC = BACKEND.parent / "docs" / "04-compliance" / "ZERO_STORAGE_ARCHITECTURE.md"

# Models whose monetary/account columns are knowingly NOT in §2.2, each with a
# reason. Empty is the goal and the current state — keep it that way.
KNOWN_UNDISCLOSED: dict[str, str] = {}


def _normalize(name: str) -> str:
    """Collapse 'Follow-Up Items Table' and 'follow_up_items' to one key."""
    name = re.sub(r"(?i)\btable\b", "", name)
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _documented_tables() -> set[str]:
    """Normalized table names from the §2.2 controlled-storage exception list."""
    text = ZERO_STORAGE_DOC.read_text(encoding="utf-8")
    section = re.search(
        r"^###\s*2\.2\s+Controlled Storage Exceptions\s*$(.*?)^###\s*2\.3",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert section, "Could not locate §2.2 Controlled Storage Exceptions — has the doc been restructured?"
    return {_normalize(h) for h in re.findall(r"^####\s+(.+?)\s*$", section.group(1), re.MULTILINE)}


# Serialized (JSON/Text) columns known to carry money or account identifiers
# inside them. Static analysis cannot see through a Text column, so this is the
# one part of the check that must be maintained by hand. Both entries were found
# by code review, not by the type-based scan — which is exactly why the list
# exists.
SERIALIZED_MONEY_COLUMNS: dict[str, str] = {
    "admin_audit_logs": "details_json carries amount_cents for credits and refunds "
    "(backend/billing/admin_customers.py)",
    "tool_activities": "summary_json is a caller-supplied free-form blob (2000 chars), "
    "so its contents are bounded by length but not by type",
    "uncorrected_misstatements": "accounts_affected_json carries {account, debit_credit, amount}",
}


def _import_all_model_modules() -> None:
    """Import every module that could define a mapped model.

    Discovered by glob rather than hardcoded. An earlier revision of this test
    listed five modules by hand and silently missed ``admin_audit_model``, so a
    table holding monetary amounts escaped a check that claimed full coverage.
    Globbing means a new model file is swept in automatically.
    """
    import importlib

    import database  # noqa: F401  — registers the declarative Base

    for path in sorted(BACKEND.glob("*model*.py")) + sorted(BACKEND.glob("models.py")):
        importlib.import_module(path.stem)
    for package in ("billing", "engagement", "shared"):
        for path in sorted((BACKEND / package).glob("*model*.py")):
            importlib.import_module(f"{package}.{path.stem}")


def _models_holding_money() -> dict[str, list[str]]:
    """Map __tablename__ -> offending column names for every mapped model.

    "Offending" means any of:
      - a Numeric column (money);
      - a column whose name implies an account identifier or an amount;
      - a serialized column listed in SERIALIZED_MONEY_COLUMNS, because money
        hidden inside a Text/JSON payload is invisible to the type check.
    """
    _import_all_model_modules()
    from database import Base

    found: dict[str, list[str]] = {}
    for mapper in Base.registry.mappers:
        table = getattr(mapper.class_, "__tablename__", None)
        if not table:
            continue
        offending = [
            col.name
            for col in mapper.persist_selectable.columns
            if isinstance(col.type, Numeric) or "account" in col.name.lower() or "amount" in col.name.lower()
        ]
        if table in SERIALIZED_MONEY_COLUMNS:
            offending.append(SERIALIZED_MONEY_COLUMNS[table].split()[0])
        if offending:
            found[table] = sorted(set(offending))
    return found


class TestZeroStorageDisclosure:
    def test_doc_exists(self):
        assert ZERO_STORAGE_DOC.is_file(), f"missing {ZERO_STORAGE_DOC}"

    def test_section_2_2_parses(self):
        documented = _documented_tables()
        assert len(documented) >= 10, f"§2.2 yielded only {len(documented)} tables — parser or doc broke"

    def test_every_money_model_is_disclosed(self):
        """A model storing money or account identifiers must appear in §2.2."""
        documented = _documented_tables()
        offenders = _models_holding_money()

        undisclosed = {
            table: cols
            for table, cols in offenders.items()
            if _normalize(table) not in documented and table not in KNOWN_UNDISCLOSED
        }

        if undisclosed:
            lines = [
                "These models persist money or account identifiers but are NOT listed in",
                "ZERO_STORAGE_ARCHITECTURE.md §2.2 Controlled Storage Exceptions:",
                "",
            ]
            for table, cols in sorted(undisclosed.items()):
                lines.append(f"  {table}: {', '.join(cols)}")
            lines += [
                "",
                "Zero-Storage is a customer-facing trust claim. Either add a '#### <Name> Table'",
                "subsection to §2.2 describing what is stored and why it falls outside the",
                "exclusion, or add the table to KNOWN_UNDISCLOSED with a written reason.",
            ]
            pytest.fail("\n".join(lines))

    def test_allowlist_is_empty(self):
        """Full enforcement. If this fails, an exception was granted — justify it."""
        assert KNOWN_UNDISCLOSED == {}, (
            f"KNOWN_UNDISCLOSED is non-empty, so some model storing money is undisclosed: {KNOWN_UNDISCLOSED}"
        )

    def test_the_sprint_783_tables_are_disclosed(self):
        """Regression pin for every table this sprint had to add to §2.2."""
        documented = _documented_tables()
        for table in (
            "uncorrected_misstatements",
            "analytical_expectations",
            "admin_audit_logs",
            "tool_activities",
        ):
            assert _normalize(table) in documented, f"{table} missing from §2.2 — Sprint 783 regression"

    def test_serialized_money_columns_are_all_disclosed(self):
        """Every hand-maintained serialized-money entry must be documented."""
        documented = _documented_tables()
        missing = [t for t in SERIALIZED_MONEY_COLUMNS if _normalize(t) not in documented]
        assert not missing, f"serialized-money tables absent from §2.2: {missing}"

    def test_flagged_accounts_disclosure_is_honest(self):
        """`tool_runs.flagged_accounts` stores account NAMES, not a count.

        The §2.1 example originally read "3 flagged accounts", which reads as a
        tally. It is a JSON list of account-name strings extracted from uploaded
        tool output, so the row must not imply otherwise — this was the specific
        claim that made the rewritten §1.1 definition false on first attempt.
        """
        text = ZERO_STORAGE_DOC.read_text(encoding="utf-8")
        row = re.search(r"^\|\s*\*\*Tool Run Records\*\*\s*\|(.+)$", text, re.MULTILINE)
        assert row, "Tool Run Records row missing from the §2.1 matrix"
        assert "flagged account name" in row.group(1).lower(), (
            "The Tool Run Records row must state that flagged account NAMES are stored. "
            f"Got: {row.group(1).strip()[:120]}"
        )

    def test_no_unqualified_never_stored_account_names_claim(self):
        """The absolute claim that caused the contradiction must not come back.

        'Individual Account Names | Never Stored' was false: practitioner-entered
        ISA 450 lines store account names by design. The row must stay qualified
        as to origin (parsed from an upload vs typed by the practitioner).
        """
        text = ZERO_STORAGE_DOC.read_text(encoding="utf-8")
        for row in re.findall(r"^\|\s*\*\*([^|]*Account Names[^|]*)\*\*\s*\|([^|]*)\|", text, re.MULTILINE):
            label, status = row[0], row[1]
            if "Never Stored" in status:
                assert any(word in label.lower() for word in ("parsed", "upload")), (
                    f"Row '{label.strip()}' claims account names are Never Stored without "
                    "qualifying that it means names parsed from an upload. Practitioner-entered "
                    "account names ARE stored (ISA 450) — see §2.2."
                )
