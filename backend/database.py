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

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import DATABASE_URL
from security_utils import log_secure_operation

# Create engine with SQLite-specific configuration
# check_same_thread=False is required for SQLite with FastAPI
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False  # Set to True for SQL debugging
)

# SQLite pragmas: WAL mode for concurrent read/write, FK enforcement
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
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


def init_db():
    """
    Initialize database tables.
    Called at application startup.

    IMPORTANT: This creates only metadata tables:
    - User table (credentials/settings)
    - ActivityLog table (audit summary metadata only)
    - Client table (client identification metadata only)

    No accounting/trial balance DATA tables exist by design.
    """
    from models import User, ActivityLog, Client  # Import here to avoid circular imports
    from engagement_model import Engagement, ToolRun  # Phase X: Engagement Layer

    log_secure_operation("database_init", f"Initializing database: {DATABASE_URL[:30]}...")
    Base.metadata.create_all(bind=engine)
    log_secure_operation("database_init_complete", "User + ActivityLog + Client + Engagement tables initialized (Zero-Storage exception)")
