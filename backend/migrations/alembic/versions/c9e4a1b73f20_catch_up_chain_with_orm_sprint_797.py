"""Sprint 797: create the four tables and six columns the chain never had.

Revision ID: c9e4a1b73f20
Revises: d8b945d0b4e5
Create Date: 2026-10-22

WHAT THIS CLOSES
----------------
``alembic upgrade head`` on an empty database produced **25 of 29 tables**.
Four tables and six columns were defined on the ORM and created by no
migration — the identifiers below appear in **zero** of the 45 preceding
revision files. Verified by replaying the chain and probing:

* ``processed_webhook_events`` — Stripe webhook idempotency. Without it every
  webhook retry is reprocessed, which is a billing-correctness problem on any
  rebuilt environment.
* ``tool_activities`` — the multi-tool activity feed (Sprint 787b).
* ``password_reset_tokens`` — account recovery (Sprint 572).
* ``waitlist_signups`` — waitlist capture.
* ``engagements.completed_at`` / ``completed_by`` — the engagement completion
  gate. The column-level counterpart of Sprint 741d's
  ``engagementstatus.COMPLETED``, which no migration adds either.
* ``diagnostic_summaries.dso`` / ``dpo`` / ``dio`` / ``ccc`` — cash-conversion
  cycle metrics.

The gap was tracked as documented drift in ``tests/test_alembic_models_parity``
since Sprint 737 and filed as Sprint 738, which was recorded as blocked on a
production connection string. It was not: production was built by
``create_all()`` from ``Base.metadata``, so it already holds every one of these
objects, and nothing about writing the DDL needed a database read.

WHY EVERY STEP IS GUARDED
-------------------------
That same fact is what makes a bare ``op.create_table`` wrong here. Production
*already has* these tables and columns, so an unguarded create would fail the
deploy at startup — and a deploy that fails at startup is precisely the
failure mode that cost this project five months (Sprint 768). Each step
inspects first and skips what is already present, so the migration is a no-op
against production and a catch-up against a chain-built database.

The guards also make the migration safe to re-run, which matters because the
environments that need it are exactly the ones nobody is watching closely.

SCOPE — what this deliberately does NOT do
------------------------------------------
Autogenerate also proposed ~50 nullability changes and several type changes.
Both were rejected after measurement:

* The **type changes** (``VARCHAR`` to ``Enum``) are SQLite reflection
  artifacts. SQLite has no enum type, so a chain-built SQLite database reports
  VARCHAR for a column that is a native enum on PostgreSQL. Applying them
  would be acting on an artifact of the dialect used to compare.
* The **nullability drifts** are real but benign: every one is a column the
  ORM declares ``NOT NULL`` through a non-Optional ``Mapped[...]`` annotation
  while the migration created it nullable, and every one has a Python-side
  default, so no code path can emit NULL. Fifty migrations of churn for no
  behaviour change — and a fifty-row failure wall is how a gate gets switched
  off. The parity test's docstring now states that nullability is outside its
  scope rather than implying otherwise.

The three missing foreign keys **are** included: they carry integrity meaning,
and two of them hang off columns this migration creates.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c9e4a1b73f20"
down_revision: str | Sequence[str] | None = "d8b945d0b4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _has_column(table: str, column: str) -> bool:
    insp = _inspector()
    if table not in insp.get_table_names():
        return False
    return column in {c["name"] for c in insp.get_columns(table)}


def _has_fk(table: str, column: str) -> bool:
    insp = _inspector()
    if table not in insp.get_table_names():
        return False
    return any(column in fk.get("constrained_columns", []) for fk in insp.get_foreign_keys(table))


def _has_named_fk(table: str, name: str) -> bool:
    """Is there a foreign key with exactly this name?

    ``downgrade`` must only undo what ``upgrade`` did. On a database built by
    ``create_all()`` the same logical foreign key exists but was named by
    SQLAlchemy's convention, not by this migration — dropping it by our name
    raises ``No such constraint``. Checking the name rather than the column
    keeps the downgrade a true inverse instead of an approximation of one.
    """
    insp = _inspector()
    if table not in insp.get_table_names():
        return False
    return any(fk.get("name") == name for fk in insp.get_foreign_keys(table))


def upgrade() -> None:
    # ── processed_webhook_events (Stripe idempotency) ───────────────────
    if not _has_table("processed_webhook_events"):
        op.create_table(
            "processed_webhook_events",
            sa.Column("stripe_event_id", sa.String(length=255), nullable=False),
            sa.Column("processed_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("stripe_event_id"),
        )

    # ── waitlist_signups ────────────────────────────────────────────────
    if not _has_table("waitlist_signups"):
        op.create_table(
            "waitlist_signups",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_waitlist_signups_email"), "waitlist_signups", ["email"], unique=True)
        op.create_index(op.f("ix_waitlist_signups_id"), "waitlist_signups", ["id"], unique=False)

    # ── password_reset_tokens ───────────────────────────────────────────
    if not _has_table("password_reset_tokens"):
        op.create_table(
            "password_reset_tokens",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("used_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_password_reset_tokens_id"), "password_reset_tokens", ["id"], unique=False)
        op.create_index(
            op.f("ix_password_reset_tokens_token_hash"), "password_reset_tokens", ["token_hash"], unique=True
        )
        op.create_index(op.f("ix_password_reset_tokens_user_id"), "password_reset_tokens", ["user_id"], unique=False)

    # ── tool_activities (multi-tool activity feed) ──────────────────────
    # The engagement FK is use_alter=True to break the
    # users <-> organizations <-> engagements cycle, matching the ORM.
    if not _has_table("tool_activities"):
        op.create_table(
            "tool_activities",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("tool_name", sa.String(length=50), nullable=False),
            sa.Column("filename_display", sa.String(length=255), nullable=True),
            sa.Column("record_count", sa.Integer(), nullable=True),
            sa.Column("summary_json", sa.Text(), nullable=True),
            sa.Column("engagement_id", sa.Integer(), nullable=True),
            sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(
                ["engagement_id"],
                ["engagements.id"],
                name="fk_tool_activities_engagement_id",
                use_alter=True,
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_tool_activities_id"), "tool_activities", ["id"], unique=False)
        op.create_index(op.f("ix_tool_activities_timestamp"), "tool_activities", ["timestamp"], unique=False)
        op.create_index(op.f("ix_tool_activities_tool_name"), "tool_activities", ["tool_name"], unique=False)
        op.create_index(op.f("ix_tool_activities_user_id"), "tool_activities", ["user_id"], unique=False)
        op.create_index("ix_tool_activities_user_timestamp", "tool_activities", ["user_id", "timestamp"], unique=False)

    # ── engagements completion gate ─────────────────────────────────────
    with op.batch_alter_table("engagements", schema=None) as batch_op:
        if not _has_column("engagements", "completed_at"):
            batch_op.add_column(sa.Column("completed_at", sa.DateTime(), nullable=True))
        if not _has_column("engagements", "completed_by"):
            batch_op.add_column(sa.Column("completed_by", sa.Integer(), nullable=True))

    if not _has_fk("engagements", "completed_by"):
        with op.batch_alter_table("engagements", schema=None) as batch_op:
            batch_op.create_foreign_key("fk_engagements_completed_by_users", "users", ["completed_by"], ["id"])

    # ── diagnostic_summaries cash-conversion-cycle metrics ──────────────
    # Float is correct here: these are day counts and a cycle length, not
    # money. They are named in guards/accounting_policy.toml's float_allowlist
    # for exactly that reason.
    with op.batch_alter_table("diagnostic_summaries", schema=None) as batch_op:
        for col in ("dso", "dpo", "dio", "ccc"):
            if not _has_column("diagnostic_summaries", col):
                batch_op.add_column(sa.Column(col, sa.Float(), nullable=True))

    # ── archived_by foreign keys ────────────────────────────────────────
    # Both columns already exist in the chain; only the FK was missing.
    for table in ("analytical_expectations", "uncorrected_misstatements"):
        if _has_column(table, "archived_by") and not _has_fk(table, "archived_by"):
            with op.batch_alter_table(table, schema=None) as batch_op:
                batch_op.create_foreign_key(f"fk_{table}_archived_by_users", "users", ["archived_by"], ["id"])


def downgrade() -> None:
    for table in ("uncorrected_misstatements", "analytical_expectations"):
        name = f"fk_{table}_archived_by_users"
        if _has_named_fk(table, name):
            with op.batch_alter_table(table, schema=None) as batch_op:
                batch_op.drop_constraint(name, type_="foreignkey")

    with op.batch_alter_table("diagnostic_summaries", schema=None) as batch_op:
        for col in ("ccc", "dio", "dpo", "dso"):
            if _has_column("diagnostic_summaries", col):
                batch_op.drop_column(col)

    if _has_named_fk("engagements", "fk_engagements_completed_by_users"):
        with op.batch_alter_table("engagements", schema=None) as batch_op:
            batch_op.drop_constraint("fk_engagements_completed_by_users", type_="foreignkey")
    with op.batch_alter_table("engagements", schema=None) as batch_op:
        for col in ("completed_by", "completed_at"):
            if _has_column("engagements", col):
                batch_op.drop_column(col)

    for table in ("tool_activities", "password_reset_tokens", "waitlist_signups", "processed_webhook_events"):
        if _has_table(table):
            op.drop_table(table)
