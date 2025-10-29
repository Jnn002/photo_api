"""
Photography Studio Management System API.

Main FastAPI application with CORS, exception handlers, and lifespan management.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.catalog.router import router as catalog_router
from app.clients.router import router as clients_router
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.error_handlers import register_all_errors
from app.core.invitation_redis import close_invitation_redis_connection
from app.core.redis import close_redis_connection
from app.dashboard.router import router as dashboard_router
from app.invitations.router import router as invitations_router
from app.sessions.router import router as sessions_router
from app.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Handles database initialization on startup and cleanup on shutdown.
    """
    # Startup
    print('🚀 Starting Photography Studio API...')
    # print(f'📍 Environment: {settings.ENVIRONMENT}')
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
    await close_redis_connection()
    print('✅ Redis token blocklist connections closed')
    await close_invitation_redis_connection()
    print('✅ Redis invitation connections closed')


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
# For production, ensure CORS_ORIGINS in .env contains only trusted domains
# Example: CORS_ORIGINS=["https://studio.yourdomain.com","https://app.yourdomain.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    expose_headers=settings.CORS_EXPOSE_HEADERS,
    # expose_headers=settings.CORS_EXPOSE_HEADERS,
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


# ==================== Configuration Endpoints ====================


@app.get('/api/v1/config/business-rules', tags=['Configuration'])
async def get_business_rules():
    """
    Get business rules configuration.

    Returns configuration values that the frontend needs to display consistent
    messages, calculate deadlines, and validate business rules on the client side.

    This endpoint is public (no authentication required) to allow the frontend
    to load configuration before user login.

    **Returns:**
    - payment_deadline_days: Number of days from Pre-scheduled for payment (default: 5)
    - changes_deadline_days: Number of days before session for making changes (default: 7)
    - default_editing_days: Default days for photo editing (default: 15)
    - default_deposit_percentage: Default deposit percentage (default: 50)

    **Example response:**
    ```json
    {
        "payment_deadline_days": 5,
        "changes_deadline_days": 7,
        "default_editing_days": 15,
        "default_deposit_percentage": 50
    }
    ```

    **Frontend usage (Angular):**
    ```typescript
    // In a ConfigService
    async loadBusinessRules(): Promise<BusinessRules> {
        return this.http.get<BusinessRules>('/api/v1/config/business-rules').toPromise();
    }

    // Display message to user
    displayPaymentDeadline(session: Session) {
        const daysUntilPayment = this.config.business_rules.payment_deadline_days;
        return `Payment due within ${daysUntilPayment} days`;
    }
    ```
    """
    return {
        'payment_deadline_days': settings.PAYMENT_DEADLINE_DAYS,
        'changes_deadline_days': settings.CHANGES_DEADLINE_DAYS,
        'default_editing_days': settings.DEFAULT_EDITING_DAYS,
        'default_deposit_percentage': settings.DEFAULT_DEPOSIT_PERCENTAGE,
    }


@app.get('/api/v1/enums', tags=['Configuration'])
async def get_enums():
    """
    Get all enum values for frontend dropdowns and validation.

    Returns all possible values for enum fields used throughout the API.
    This allows the frontend to:
    - Populate dropdown/select controls
    - Generate TypeScript enums
    - Validate values before submission
    - Display localized labels

    This endpoint is public (no authentication required) to allow the frontend
    to load enum values before user login.

    **Example response:**
    ```json
    {
        "session_status": ["REQUEST", "NEGOTIATION", "PRE_SCHEDULED", ...],
        "session_type": ["STUDIO", "EXTERNAL"],
        "client_type": ["INDIVIDUAL", "INSTITUTIONAL"],
        "payment_type": ["CASH", "CARD", "TRANSFER", "CHECK"],
        ...
    }
    ```

    **Frontend usage (Angular):**
    ```typescript
    // Generate TypeScript enum
    export enum SessionStatus {
        REQUEST = 'REQUEST',
        NEGOTIATION = 'NEGOTIATION',
      // ... auto-generated from API
    }

    // Populate dropdown
    async ngOnInit() {
        const enums = await this.api.getEnums();
        this.statusOptions = enums.session_status.map(status => ({
        value: status,
        label: this.translate(status) // i18n translation
        }));
    }
    ```
    """
    from app.core.enums import (
        ClientType,
        DeliveryMethod,
        ItemType,
        LineType,
        PaymentType,
        PhotographerRole,
        ReferenceType,
        SessionStatus,
        SessionType,
        Status,
        UnitMeasure,
    )

    return {
        'session_status': [s.value for s in SessionStatus],
        'session_type': [t.value for t in SessionType],
        'client_type': [t.value for t in ClientType],
        'payment_type': [t.value for t in PaymentType],
        'delivery_method': [m.value for m in DeliveryMethod],
        'status': [s.value for s in Status],
        'photographer_role': [r.value for r in PhotographerRole],
        'line_type': [t.value for t in LineType],
        'reference_type': [t.value for t in ReferenceType],
        'item_type': [t.value for t in ItemType],
        'unit_measure': [u.value for u in UnitMeasure],
    }


# ==================== Router Includes ====================


app.include_router(users_router, prefix='/api/v1')
app.include_router(clients_router, prefix='/api/v1')
app.include_router(catalog_router, prefix='/api/v1')
app.include_router(sessions_router, prefix='/api/v1')
app.include_router(dashboard_router, prefix='/api/v1')
app.include_router(invitations_router, prefix='/api/v1')
