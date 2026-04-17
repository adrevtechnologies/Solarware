"""Database connection and session management."""
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, Session, sessionmaker
from sqlalchemy_utils import database_exists, create_database
from contextlib import contextmanager
import logging

from .config import get_settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def get_engine():
    """Get synchronous database engine."""
    settings = get_settings()
    return create_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_pre_ping=True,
        pool_recycle=3600
    )


def get_async_engine():
    """Get asynchronous database engine."""
    settings = get_settings()
    # Convert postgresql:// to postgresql+asyncpg://
    async_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    return create_async_engine(
        async_url,
        echo=settings.DATABASE_ECHO,
        pool_pre_ping=True,
        pool_recycle=3600
    )


def setup_database():
    """Initialize database tables and extensions."""
    settings = get_settings()
    engine = get_engine()
    
    # Create database if it doesn't exist
    if not database_exists(settings.DATABASE_URL):
        logger.info(f"Creating database: {settings.DATABASE_URL}")
        create_database(settings.DATABASE_URL)
    
    # Create PostGIS extension
    with engine.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        connection.commit()
        logger.info("PostGIS extension enabled")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")


def get_db():
    """Dependency for getting database session (synchronous)."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """Dependency for getting async database session."""
    async_engine = get_async_engine()
    AsyncSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()


@contextmanager
def get_db_context():
    """Context manager for database session."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Import here to avoid circular imports
try:
    from sqlalchemy.orm import sessionmaker
except ImportError:
    pass
