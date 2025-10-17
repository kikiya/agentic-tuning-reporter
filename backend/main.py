"""
FastAPI backend for CRDB Cluster Tuning Report Generator (Synchronous Version)
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from database_sync import SessionLocal, init_db
from sqlalchemy.orm import Session
from models_sync import User
from routers.reports_sync import router as reports_router
from routers.cluster_metrics import router as cluster_router

# Load environment variables
load_dotenv()


# Lifespan event handler for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    try:
        # Initialize tables
        init_db()

        # Seed default user 'system' if missing
        if SessionLocal is not None:
            db: Session = SessionLocal()
            try:
                existing = db.query(User).filter(User.id == "system").first()
                if not existing:
                    system_user = User(
                        id="system",
                        name="System",
                        email="system@example.com",
                        role="admin",
                    )
                    db.add(system_user)
                    db.commit()
            finally:
                db.close()
    except Exception as e:
        # Avoid crashing app on startup; log and continue
        print(f"Startup initialization error: {e}")
    
    yield
    
    # Shutdown (if needed in the future)
    # Add cleanup code here


# Create FastAPI application
app = FastAPI(
    title="CRDB Tuning Report Generator API",
    description="API for managing CockroachDB cluster tuning reports, findings, and recommendations",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "http://localhost:3000",  # CRA dev server
        # "http://localhost:5173",  # Vite dev server
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(reports_router, prefix="/api/v1", tags=["reports"])
app.include_router(cluster_router, prefix="/api/v1", tags=["cluster"])

@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "CRDB Tuning Report Generator API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = SessionLocal()
        if db is None:
            return {"status": "unhealthy", "database": "not_configured"}
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "error", "error": str(e)}

@app.post("/admin/init-db")
def initialize_database():
    """Initialize database tables (admin endpoint)"""
    try:
        success = init_db()
        if success:
            return {"message": "Database initialized successfully"}
        else:
            return {"error": "Failed to initialize database"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
