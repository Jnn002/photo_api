"""
Photography Studio Management System API.

Main FastAPI application with CORS, exception handlers, and lifespan management.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.error_handlers import register_all_errors


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Handles database initialization on startup and cleanup on shutdown.
    """
    # Startup
    print('🚀 Starting Photography Studio API...')
    print(f'📍 Environment: {settings.ENVIRONMENT}')
    print('  Database: Connected')

    # Initialize database (optional - primarily for testing)
    # In production, use Alembic migrations instead
    if settings.ENVIRONMENT == 'development':
        await init_db()
        print('✅ Database tables initialized')

    yield

    # Shutdown
    print('🛑 Shutting down Photography Studio API...')
    await close_db()
    print('✅ Database connections closed')


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description='Backend API for Photography Studio Management System',
    docs_url='/docs' if settings.DEBUG else None,
    redoc_url='/redoc' if settings.DEBUG else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Register all exception handlers
register_all_errors(app)


# ==================== Health Check Endpoint ====================


@app.get('/health', tags=['Health'])
async def health_check():
    """
    Health check endpoint.

    Returns basic application status and version information.
    """
    return {
        'status': 'healthy',
        'app_name': settings.APP_NAME,
        'version': settings.APP_VERSION,
        'environment': settings.ENVIRONMENT,
    }


@app.get('/', tags=['Root'])
async def root():
    """
    Root endpoint.

    Welcome message with API information.
    """
    return {
        'message': 'Welcome to Photography Studio Management API',
        'version': settings.APP_VERSION,
        'docs': '/docs' if settings.DEBUG else 'Documentation disabled in production',
    }


# ==================== Router Includes ====================
# TODO: Include routers here when implemented
# Example:
# from app.users.router import router as users_router
# app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
