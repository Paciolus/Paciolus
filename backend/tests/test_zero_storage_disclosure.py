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


def _models_holding_money() -> dict[str, list[str]]:
    """Map __tablename__ -> offending column names for every mapped model.

    "Offending" means a Numeric column (money) or a column whose name implies an
    account identifier or an amount — the two things the Zero-Storage claim is
    read as excluding.
    """
    # Import the model modules so their mappers are registered. Kept explicit
    # rather than globbed so a new model file fails loudly here instead of
    # silently escaping the check.
    import analytical_expectations_model  # noqa: F401
    import database  # noqa: F401  — registers the declarative Base
    import engagement_model  # noqa: F401
    import models  # noqa: F401
    import subscription_model  # noqa: F401
    import uncorrected_misstatements_model  # noqa: F401
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

    def test_the_two_sprint_783_tables_are_disclosed(self):
        """Regression pin for the specific pair that drifted for ~6 months."""
        documented = _documented_tables()
        for table in ("uncorrected_misstatements", "analytical_expectations"):
            assert _normalize(table) in documented, f"{table} missing from §2.2 — Sprint 783 regression"

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
