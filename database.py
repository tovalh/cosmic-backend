#!/usr/bin/env python3
"""
Database configuration for Railway PostgreSQL
"""

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get database URL from Railway environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Railway provides PostgreSQL URL, but SQLAlchemy needs postgresql:// not postgres://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Fallback to SQLite for local development
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./cosmic_genesis.db"
    print("⚠️  Using SQLite fallback - set DATABASE_URL for PostgreSQL")

print(f"🗄️  Database URL: {DATABASE_URL.split('@')[0] if '@' in DATABASE_URL else DATABASE_URL}")

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=300,    # Recycle connections every 5 minutes
        echo=False           # Set to True for SQL logging in development
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()
metadata = MetaData()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database tables"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            result.fetchone()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    # Test connection when run directly
    test_connection()
    init_database()