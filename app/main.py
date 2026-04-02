"""
Finance System Backend - Main Application Entry Point.

A FastAPI-based finance tracking system with:
- User authentication and role-based access control
- Transaction management (CRUD operations)
- Financial summaries and analytics
- CSV/JSON export functionality
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.core.config import settings
from app.database import init_db, SessionLocal
from app.services.auth_service import AuthService
from app.routes import auth, users, transactions, summaries

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events handler.
    Initializes database and seeds admin user on startup.
    """
    # Startup
    logger.info("Starting up Finance System Backend...")
    
    # Initialize database tables
    init_db()
    logger.info("Database tables created")
    
    # Create admin user if doesn't exist
    db = SessionLocal()
    try:
        admin = AuthService.create_admin_user(db)
        if admin:
            logger.info(f"Admin user created: {admin.username}")
        else:
            logger.info("Admin user already exists")
    finally:
        db.close()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Finance System Backend...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## Finance System Backend API

A comprehensive finance tracking system with the following features:

### Features
- **User Management**: Registration, authentication, and role-based access control
- **Transactions**: Full CRUD operations for income and expense records
- **Analytics**: Financial summaries, category breakdowns, and monthly reports
- **Export**: Export data in JSON or CSV format

### User Roles
- **Viewer**: Can view transactions and summaries
- **Analyst**: Can create, update transactions and access detailed insights
- **Admin**: Full access including user management and data deletion

### Authentication
All protected endpoints require a Bearer token in the Authorization header.
Obtain a token by registering and logging in via `/auth/register` and `/auth/login`.
    """,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors."""
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "A database error occurred",
            "message": str(exc) if settings.debug else "Internal server error"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "message": str(exc) if settings.debug else "Internal server error"
        }
    )


# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(summaries.router, prefix="/api")


# Health check endpoint
@app.get("/", tags=["Health"])
def root():
    """Root endpoint - API health check."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "healthy",
        "docs": "/api/docs"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
