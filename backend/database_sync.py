"""
Database configuration and session management for CRDB (synchronous version)
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "cockroachdb+psycopg://root@Kikias-MacBook-Pro-2.local:26257/tuning_reports?sslmode=disable"
)

print(f"[DB DEBUG] DATABASE_URL from env: {DATABASE_URL}", flush=True)
print(f"[DB DEBUG] DATABASE_URL is None: {DATABASE_URL is None}", flush=True)
print(f"[DB DEBUG] DATABASE_URL length: {len(DATABASE_URL) if DATABASE_URL else 0}", flush=True)

# Track database availability
db_available = False
engine = None
SessionLocal = None
Base = declarative_base()

def check_database_connection():
    """Check if we can connect to the database"""
    global db_available, engine, SessionLocal
    
    if not DATABASE_URL:
        print("No database connection string found")
        db_available = False
        return False
    
    try:
        # Create the SQLAlchemy engine
        engine = create_engine(
            DATABASE_URL,
            echo=False,  # Set to False in production
            connect_args={
                "application_name": "tuning_reports"
            }
        )
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            if result == 1:
                print("Database connection configured successfully")
                db_available = True
                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                return True
            else:
                print("Warning: Database connection test returned unexpected result")
                db_available = False
                return False
    except Exception as e:
        print(f"Error configuring database connection: {e}")
        db_available = False
        return False

# Check connection when module is loaded
check_database_connection()

# Dependency to get session
def get_db():
    """Get a database session if available"""
    if not db_available or not SessionLocal:
        yield None
        return
        
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database (create tables)
def init_db():
    """Initialize database by creating all tables"""
    global db_available
    
    if not db_available or not engine:
        print("Cannot initialize database - connection not available")
        return False
        
    try:
        # Ensure models are imported so they are registered on Base.metadata
        # Import locally to avoid circular import issues
        import models_sync  # noqa: F401
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

# Base class for models is defined above
