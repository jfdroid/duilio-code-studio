"""
Database Configuration
=====================
SQLAlchemy database setup and session management.
"""

import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool
from core.config import get_settings
from core.logger import get_logger

Base = declarative_base()
logger = get_logger()

# Global session factory
SessionLocal: sessionmaker = None
engine = None


def get_database_url() -> str:
    """
    Get database URL from config or environment.
    
    Returns:
        Database URL string
    """
    settings = get_settings()
    
    # Check environment variable first
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    
    # Check secrets manager
    try:
        from core.secrets import SecretsManager
        db_url = SecretsManager.get_database_url()
        if db_url:
            return db_url
    except Exception:
        pass
    
    # Default: SQLite in data directory
    data_dir = settings.DATA_DIR or Path(settings.BASE_DIR) / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "duiliocode.db"
    
    return f"sqlite:///{db_path}"


def init_database():
    """
    Initialize database engine and session factory.
    """
    global SessionLocal, engine
    
    db_url = get_database_url()
    logger.info(f"Initializing database: {db_url}")
    
    # SQLite-specific configuration
    if db_url.startswith("sqlite"):
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
    else:
        engine = create_engine(db_url, echo=False)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("Database initialized successfully")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.
    
    Yields:
        Database session
    """
    if SessionLocal is None:
        init_database()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get a database session (for use outside FastAPI).
    
    Returns:
        Database session
    """
    if SessionLocal is None:
        init_database()
    
    return SessionLocal()
