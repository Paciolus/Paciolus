"""
Paciolus Database Module
Day 13: Secure Commercial Infrastructure
Day 14: Activity Logging & Metadata History
Sprint 16: Client Core Infrastructure

SQLAlchemy setup for user authentication, activity logging, and client management.

ZERO-STORAGE EXCEPTION: This database stores ONLY:
- User credentials and settings (Day 13)
- Audit summary metadata (Day 14) - aggregate stats only, no file content
- Client identification metadata (Sprint 16) - name/industry only, no financial data

Trial balance data is NEVER persisted - it remains in-memory only.
"""

from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import DATABASE_URL, DB_MAX_OVERFLOW, DB_POOL_RECYCLE, DB_POOL_SIZE
from security_utils import log_secure_operation

# Create engine with dialect-specific configuration
_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    # SQLite: check_same_thread=False required for FastAPI, no pool tuning
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    # PostgreSQL: connection pool tuning (Sprint 274)
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_recycle=DB_POOL_RECYCLE,
        echo=False,
    )

# SQLite pragmas: WAL mode for concurrent read/write, FK enforcement
if _is_sqlite:

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn: Any, connection_record: Any) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base class for models (SQLAlchemy 2.0 DeclarativeBase)
class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    Ensures proper cleanup after request completion.

    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables and log connection info.

    Expected dialects:
    - development: SQLite (WAL + FK pragmas, no pool tuning)
    - production: PostgreSQL (pool_pre_ping, sized pool, recycle)

    IMPORTANT: This creates only metadata tables:
    - User table (credentials/settings)
    - ActivityLog table (audit summary metadata only)
    - Client table (client identification metadata only)

    No accounting/trial balance DATA tables exist by design.
    """
    import logging

    logger = logging.getLogger(__name__)

    log_secure_operation("database_init", f"Initializing database: {DATABASE_URL[:30]}...")

    # Ensure ALL model modules are imported so Base.metadata sees every table
    # before create_all() — prevents NoReferencedTableError for cross-model FKs.
    import engagement_model  # noqa: F401
    import export_share_model  # noqa: F401
    import firm_branding_model  # noqa: F401
    import follow_up_items_model  # noqa: F401
    import models  # noqa: F401
    import organization_model  # noqa: F401
    import scheduler_lock_model  # noqa: F401
    import subscription_model  # noqa: F401
    import team_activity_model  # noqa: F401
    import tool_session_model  # noqa: F401
    import upload_dedup_model  # noqa: F401

    Base.metadata.create_all(bind=engine)

    dialect_name = engine.dialect.name
    pool_class = type(engine.pool).__name__
    logger.info("Database initialized: dialect=%s, pool=%s", dialect_name, pool_class)

    # create_all() creates new tables but does NOT add columns to existing tables.
    # Patch missing columns that were added by migrations after the table was first created.
    if dialect_name == "sqlite":
        try:
            with engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(users)"))
                columns = {row[1] for row in result.fetchall()}
                if "organization_id" not in columns:
                    conn.execute(
                        text("ALTER TABLE users ADD COLUMN organization_id INTEGER REFERENCES organizations(id)")
                    )
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_organization_id ON users (organization_id)"))
                    conn.commit()
                    logger.info("Patched users table (SQLite): added organization_id column")
        except Exception:
            logger.warning("Could not patch users table for organization_id column (SQLite)", exc_info=True)

        # AUDIT-02 FIX 2: Patch refresh_tokens with session metadata columns
        # (last_used_at, user_agent, ip_address added by migration b6c7d8e9f0a1)
        try:
            with engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(refresh_tokens)"))
                columns = {row[1] for row in result.fetchall()}
                added = []
                for col_name, col_type in [
                    ("last_used_at", "DATETIME"),
                    ("user_agent", "VARCHAR(512)"),
                    ("ip_address", "VARCHAR(45)"),
                ]:
                    if col_name not in columns:
                        conn.execute(text(f"ALTER TABLE refresh_tokens ADD COLUMN {col_name} {col_type}"))
                        added.append(col_name)
                if added:
                    conn.commit()
                    logger.info("Patched refresh_tokens table (SQLite): added %s", ", ".join(added))
        except Exception:
            logger.warning("Could not patch refresh_tokens table for session metadata columns (SQLite)", exc_info=True)

    if dialect_name == "postgresql":
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'users' AND column_name = 'organization_id'"
                    )
                )
                if not result.fetchone():
                    conn.execute(
                        text("ALTER TABLE users ADD COLUMN organization_id INTEGER REFERENCES organizations(id)")
                    )
                    conn.execute(text("CREATE INDEX ix_users_organization_id ON users (organization_id)"))
                    conn.commit()
                    logger.info("Patched users table: added organization_id column")
        except Exception:
            logger.warning("Could not patch users table for organization_id column", exc_info=True)

        # AUDIT-02 FIX 2: Patch refresh_tokens with session metadata columns
        try:
            with engine.connect() as conn:
                added = []
                for col_name, col_type in [
                    ("last_used_at", "TIMESTAMP"),
                    ("user_agent", "VARCHAR(512)"),
                    ("ip_address", "VARCHAR(45)"),
                ]:
                    result = conn.execute(
                        text(
                            "SELECT column_name FROM information_schema.columns "
                            "WHERE table_name = :table_name AND column_name = :col_name"
                        ),
                        {"table_name": "refresh_tokens", "col_name": col_name},
                    )
                    if not result.fetchone():
                        # col_name and col_type are from a hardcoded allowlist above — safe for DDL
                        conn.execute(text(f"ALTER TABLE refresh_tokens ADD COLUMN {col_name} {col_type}"))
                        added.append(col_name)
                if added:
                    conn.commit()
                    logger.info("Patched refresh_tokens table: added %s", ", ".join(added))
        except Exception:
            logger.warning("Could not patch refresh_tokens table for session metadata columns", exc_info=True)

    # Ensure ENTERPRISE value exists in the usertier PG enum (added in Phase LXIX).
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block, so use autocommit.
    if dialect_name == "postgresql":
        try:
            raw_conn = engine.raw_connection()
            try:
                raw_conn.autocommit = True  # type: ignore[attr-defined]
                cur = raw_conn.cursor()
                cur.execute(
                    "SELECT 1 FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid "
                    "WHERE pg_type.typname = 'usertier' AND pg_enum.enumlabel = 'ENTERPRISE'"
                )
                if not cur.fetchone():
                    cur.execute("ALTER TYPE usertier ADD VALUE 'ENTERPRISE'")
                    logger.info("Added ENTERPRISE to usertier enum")
                cur.close()
            finally:
                raw_conn.close()
        except Exception:
            logger.warning("Could not add ENTERPRISE to usertier enum", exc_info=True)

    if dialect_name == "postgresql":
        try:
            with engine.connect() as conn:
                pg_version = conn.execute(text("SELECT version()")).scalar()
                ssl_row = conn.execute(text("SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()")).fetchone()
                ssl_active = bool(ssl_row and ssl_row[0])
            logger.info(
                "PostgreSQL: version=%s, pool_size=%d, max_overflow=%d, recycle=%ds, tls=%s",
                pg_version,
                DB_POOL_SIZE,
                DB_MAX_OVERFLOW,
                DB_POOL_RECYCLE,
                "active" if ssl_active else "INACTIVE",
            )
            if not ssl_active:
                logger.warning(
                    "PostgreSQL connection is NOT using TLS encryption — "
                    "add ?sslmode=require to DATABASE_URL for production"
                )
        except Exception:
            logger.warning("Could not retrieve PostgreSQL server version or TLS status")
    elif dialect_name == "sqlite":
        logger.info("SQLite mode (development): WAL journal, FK constraints enabled")

    log_secure_operation(
        "database_init_complete",
        "User + ActivityLog + Client + Engagement tables initialized (Zero-Storage exception)",
    )
