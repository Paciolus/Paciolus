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

from config import (
    DATABASE_URL,
    DB_MAX_OVERFLOW,
    DB_POOL_RECYCLE,
    DB_POOL_SIZE,
    DB_TLS_OVERRIDE_TICKET,
    DB_TLS_OVERRIDE_VALID,
    DB_TLS_REQUIRED,
)
from security_utils import log_secure_operation


def _is_pooled_hostname(database_url: str) -> bool:
    """Return True if DATABASE_URL hostname looks like a transparent pooler endpoint.

    Transparent poolers (e.g., Neon's `-pooler` hostnames) terminate TLS at the
    pool layer. `pg_stat_ssl` reports the pooler-to-backend hop, not the
    client-to-pooler hop, so the view returns ssl=false even when the
    client-to-pooler connection IS encrypted. Client-to-pooler TLS is still
    enforced separately by the `sslmode` check in `config.py`.
    """
    from urllib.parse import urlparse

    host = (urlparse(database_url).hostname or "").lower()
    return "-pooler" in host


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

    # Schema evolution is Alembic's responsibility — Dockerfile CMD runs
    # `alembic upgrade head` before gunicorn (Sprint 544c). The in-process
    # ALTER TABLE patch blocks that lived here were removed in Sprint 737
    # after evidence confirmed they were dead code in production and tests.
    # Drift between models and migrations is caught by
    # tests/test_alembic_models_parity.py.

    if dialect_name == "postgresql":
        try:
            pooled = _is_pooled_hostname(DATABASE_URL)
            with engine.connect() as conn:
                pg_version = conn.execute(text("SELECT version()")).scalar()
                # Transparent poolers terminate TLS at the pool layer, so
                # pg_stat_ssl reports the pooler-to-backend hop, not the
                # client-to-pooler hop. Skip the assertion on pooled hosts;
                # client-to-pooler TLS is enforced by the sslmode check in
                # config.py.
                if pooled:
                    ssl_row = None
                else:
                    ssl_row = conn.execute(text("SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()")).fetchone()
                ssl_active = bool(ssl_row and ssl_row[0])
            logger.info(
                "PostgreSQL: version=%s, pool_size=%d, max_overflow=%d, recycle=%ds, tls=%s",
                pg_version,
                DB_POOL_SIZE,
                DB_MAX_OVERFLOW,
                DB_POOL_RECYCLE,
                "pooler-skip" if pooled else ("active" if ssl_active else "INACTIVE"),
            )
            if pooled:
                log_secure_operation(
                    "db_tls_pooler_skip",
                    "pg_stat_ssl assertion skipped for -pooler hostname "
                    "(transparent pooler TLS blindspot; sslmode enforced in config)",
                )
            elif ssl_active:
                log_secure_operation("db_tls_verified", "PostgreSQL TLS active at startup")
            elif DB_TLS_OVERRIDE_VALID:
                # Break-glass exception: TLS not active but documented override exists
                logger.warning(
                    "PostgreSQL TLS INACTIVE — bypassed via DB_TLS_OVERRIDE (ticket=%s). "
                    "This exception must be resolved before expiration.",
                    DB_TLS_OVERRIDE_TICKET,
                )
                log_secure_operation(
                    "db_tls_override",
                    f"TLS inactive but bypassed via override ticket={DB_TLS_OVERRIDE_TICKET}",
                )
            elif DB_TLS_REQUIRED:
                log_secure_operation(
                    "db_tls_enforcement_failure",
                    "PostgreSQL TLS inactive — startup blocked by DB_TLS_REQUIRED",
                )
                logger.critical(
                    "FAIL-CLOSED: PostgreSQL connection is NOT using TLS encryption. "
                    "DB_TLS_REQUIRED is enabled — refusing to start. "
                    "Fix: add ?sslmode=require to DATABASE_URL, or set a temporary "
                    "override: DB_TLS_OVERRIDE=TICKET_ID:YYYY-MM-DD"
                )
                raise RuntimeError(
                    "Database TLS verification failed: connection is not encrypted and DB_TLS_REQUIRED is enabled"
                )
            else:
                logger.warning(
                    "PostgreSQL connection is NOT using TLS encryption — "
                    "add ?sslmode=require to DATABASE_URL for production"
                )
        except RuntimeError:
            raise  # Re-raise TLS enforcement failure
        except Exception:
            if DB_TLS_REQUIRED and not DB_TLS_OVERRIDE_VALID:
                logger.critical(
                    "FAIL-CLOSED: Could not verify PostgreSQL TLS status. "
                    "DB_TLS_REQUIRED is enabled — refusing to start without TLS confirmation."
                )
                raise RuntimeError(
                    "Database TLS verification failed: could not query TLS status and DB_TLS_REQUIRED is enabled"
                )
            logger.warning("Could not retrieve PostgreSQL server version or TLS status")
    elif dialect_name == "sqlite":
        logger.info("SQLite mode (development): WAL journal, FK constraints enabled")

    log_secure_operation(
        "database_init_complete",
        "User + ActivityLog + Client + Engagement tables initialized (Zero-Storage exception)",
    )
