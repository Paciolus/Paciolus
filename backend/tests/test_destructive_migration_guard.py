"""Sprint 897 (O-9): destructive Alembic migrations must follow expand/contract."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "check_destructive_migrations.py"


@pytest.fixture(scope="module")
def guard():
    spec = importlib.util.spec_from_file_location("check_destructive_migrations", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


HEADER = 'from alembic import op\nimport sqlalchemy as sa\n\nrevision = "x"\ndown_revision = "y"\n\n'


def _write(tmp_path: Path, name: str, body: str) -> Path:
    path = tmp_path / name
    path.write_text(HEADER + body, encoding="utf-8")
    return path


def test_repository_migrations_pass(guard):
    assert guard.check(guard.DEFAULT_VERSIONS_DIR) == []


def test_grandfathered_files_exist(guard):
    """The frozen list must name real files, or it hides nothing and rots."""
    for name in guard.GRANDFATHERED:
        assert (guard.DEFAULT_VERSIONS_DIR / name).is_file(), name


@pytest.mark.parametrize(
    "upgrade_body",
    [
        'op.drop_column("users", "legacy")',
        'op.drop_table("old_things")',
        'op.rename_table("a", "b")',
        'op.alter_column("users", "name", new_column_name="full_name")',
        'op.alter_column("users", "amount", type_=sa.Numeric(19, 2))',
        'with op.batch_alter_table("users") as b:\n        b.drop_column("legacy")',
        'op.execute("ALTER TABLE users DROP COLUMN legacy")',
        'op.execute(sa.text("DROP TABLE old_things"))',
        'op.execute("ALTER TABLE users ALTER COLUMN tier TYPE text")',
    ],
)
def test_destructive_upgrade_is_flagged(guard, tmp_path, upgrade_body):
    _write(tmp_path, "m1.py", f"def upgrade():\n    {upgrade_body}\n\n\ndef downgrade():\n    pass\n")
    problems = guard.check(tmp_path, frozenset())
    assert len(problems) == 1 and problems[0].startswith("m1.py")


def test_marker_allows_a_deliberate_contract_step(guard, tmp_path):
    _write(
        tmp_path,
        "m1.py",
        "# expand-contract: contract step — no release since 2.0 reads users.legacy\n"
        'def upgrade():\n    op.drop_column("users", "legacy")\n',
    )
    assert guard.check(tmp_path, frozenset()) == []


def test_marker_needs_a_reason(guard, tmp_path):
    _write(
        tmp_path, "m1.py", '# expand-contract: contract step\ndef upgrade():\n    op.drop_column("users", "legacy")\n'
    )
    assert guard.check(tmp_path, frozenset()) != []


def test_downgrade_and_additive_upgrade_pass(guard, tmp_path):
    _write(
        tmp_path,
        "m1.py",
        "def upgrade():\n"
        '    op.add_column("users", sa.Column("x", sa.Integer(), nullable=True))\n'
        '    op.create_index("ix", "users", ["x"])\n'
        '    op.alter_column("users", "x", nullable=False)\n\n\n'
        "def downgrade():\n"
        '    op.drop_column("users", "x")\n'
        '    op.drop_table("anything")\n',
    )
    assert guard.check(tmp_path, frozenset()) == []


def test_cli_exit_codes(guard, tmp_path):
    assert guard.main(["prog", str(tmp_path)]) == 0
    _write(tmp_path, "m1.py", 'def upgrade():\n    op.drop_table("t")\n')
    assert guard.main(["prog", str(tmp_path)]) == 1
