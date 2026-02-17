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

from sqlalchemy import create_engine, event
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
    def _set_sqlite_pragmas(dbapi_conn, connection_record) -> None:
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
    """
    Initialize database tables.
    Called at application startup.

    IMPORTANT: This creates only metadata tables:
    - User table (credentials/settings)
    - ActivityLog table (audit summary metadata only)
    - Client table (client identification metadata only)

    No accounting/trial balance DATA tables exist by design.
    """

    log_secure_operation("database_init", f"Initializing database: {DATABASE_URL[:30]}...")
    Base.metadata.create_all(bind=engine)
    log_secure_operation("database_init_complete", "User + ActivityLog + Client + Engagement tables initialized (Zero-Storage exception)")
