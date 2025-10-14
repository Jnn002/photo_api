# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Photography Studio Management System API** - A FastAPI backend for managing photography sessions, clients, catalog, and team workflows for a professional photography studio in Guatemala.

**Tech Stack:**
- Python 3.13+
- FastAPI 0.115+ with async/await
- SQLModel 0.0.22 (SQLAlchemy 2.0 underneath)
- PostgreSQL 17 with asyncpg
- Alembic for migrations
- UV package manager (with virtual environment)
- Redis + Celery for background tasks
- Docker Compose for local development

## Development Commands

### Virtual Environment

**IMPORTANT:** This project uses a UV-managed virtual environment. All Python commands must be run within the virtual environment.

```bash
# Activate virtual environment
source .venv/bin/activate

# Deactivate when done
deactivate
```

### Setup & Installation
```bash
# Install dependencies with UV
uv sync

# Activate virtual environment
source .venv/bin/activate

# Start PostgreSQL and Redis with Docker Compose (uses docker-compose.env)
docker compose --env-file docker-compose.env up -d

# Run database migrations (within virtual environment)
alembic upgrade head

# Initialize system (creates permissions, roles, and admin user)
# IMPORTANT: Set ADMIN_EMAIL and ADMIN_PASSWORD in .env first!
python -m app.scripts.init_system

# Create a new migration (within virtual environment)
alembic revision --autogenerate -m "description"
```

### Running the Application
```bash
# Ensure virtual environment is activated first
source .venv/bin/activate

# Development server with auto-reload
uvicorn app.main:app --reload

# Run with specific host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Database Operations
```bash
# Activate virtual environment first
source .venv/bin/activate

# Check current migration status
alembic current

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Reset database (caution: destroys data)
alembic downgrade base
alembic upgrade head
```

### Docker Services

**IMPORTANT:** Always use `--env-file docker-compose.env` to load environment variables.

```bash
# Start services (loads variables from docker-compose.env)
docker compose --env-file docker-compose.env up -d

# Stop services
docker compose --env-file docker-compose.env stop

# Start stopped services
docker compose --env-file docker-compose.env start

# Restart services
docker compose --env-file docker-compose.env restart

# View logs
docker compose --env-file docker-compose.env logs -f postgres
docker compose --env-file docker-compose.env logs -f redis

# Stop and remove containers
docker compose --env-file docker-compose.env down

# Reset volumes (caution: destroys data)
docker compose --env-file docker-compose.env down -v
```

### Code Quality
```bash
# Activate virtual environment first
source .venv/bin/activate

# Format code with Ruff
ruff format .

# Run linter
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

## Architecture Overview

### Module Structure (Feature-Based)

The codebase follows a **layered architecture** organized by business features:

```
app/
├── core/                    # Shared infrastructure
│   ├── config.py           # Pydantic Settings (env vars)
│   ├── database.py         # Async DB session management
│   ├── security.py         # JWT & password hashing (to be implemented)
│   ├── permissions.py      # RBAC dependencies (to be implemented)
│   └── exceptions.py       # Custom exceptions (to be implemented)
├── users/                   # User, Role, Permission models
├── clients/                 # Client management
├── catalog/                 # Items, Packages, Rooms
├── sessions/                # Core photography session workflow
└── tasks/                   # Celery background tasks (to be implemented)
```

Each feature module follows this structure:
```
feature_module/
├── models.py          # SQLModel table definitions
├── schemas.py         # Pydantic I/O DTOs (to be implemented)
├── repository.py      # Database queries only (to be implemented)
├── service.py         # Business logic & orchestration (to be implemented)
└── router.py          # FastAPI endpoints (to be implemented)
```

### Layer Responsibilities

**Models** (`models.py`):
- SQLModel table definitions
- Database relationships using `Relationship(back_populates=...)`
- Field constraints via `Field()`
- NO business logic

**Schemas** (`schemas.py`):
- Request DTOs (Create, Update, Patch)
- Response DTOs (Public, Detail)
- Pydantic v2 validators (`@field_validator`, `@model_validator`)
- Separate from models for API flexibility

**Repository** (`repository.py`):
- Pure data access layer
- Async database queries only
- Returns models or None
- Uses `flush()` + `refresh()`, NOT `commit()`
- NO business logic or validation

**Service** (`service.py`):
- Business logic and orchestration
- Uses repositories for data access
- Manages transactions with `async with db.begin()`
- Raises custom exceptions for business rule violations
- Handles commits

**Router** (`router.py`):
- HTTP endpoints
- Dependency injection with `Annotated` types
- Permission checks via dependencies
- Delegates to services
- Returns appropriate HTTP status codes

### Critical Design Patterns

**1. Async Database Session Management**
```python
# Database sessions are injected via dependency
SessionDep = Annotated[AsyncSession, Depends(get_session)]

@router.post("/items")
async def create_item(db: SessionDep, data: ItemCreate):
    service = ItemService(db)
    return await service.create(data)
```

**2. Transaction Management in Services**
```python
# Repository does NOT commit
async def create(self, entity: Model) -> Model:
    self.db.add(entity)
    await self.db.flush()
    await self.db.refresh(entity)
    return entity

# Service layer handles commits
async def create_item(self, data: ItemCreate) -> Item:
    item = Item(**data.model_dump())
    item = await self.repo.create(item)
    await self.db.commit()  # Service commits
    return item
```

**3. Package Explosion Pattern (CRITICAL)**

When a package is added to a session, it must be "exploded" into denormalized `SessionDetail` records:

```python
# For each item in package:
session_detail = SessionDetail(
    session_id=session.id,
    line_type='Item',
    reference_id=package.id,        # Track original package
    reference_type='Package',
    item_code=item.code,            # Denormalized (immutable)
    item_name=item.name,            # Denormalized (immutable)
    quantity=package_item.quantity,
    unit_price=item.unit_price,     # Price at time of sale
    line_subtotal=quantity * unit_price
)
```

This ensures historical data integrity - changing package definitions doesn't affect past sessions.

**4. State Machine Transitions**

Sessions follow a strict state machine (see `files/business_rules_doc.md` for complete rules):

```
Request → Negotiation → Pre-scheduled → Confirmed → Assigned →
Attended → In Editing → Ready for Delivery → Completed

Any state (except Completed) → Canceled
```

Each transition has:
- Permission requirements
- Validation rules
- Automated actions (emails, calculations)

**5. Modern Python Type Hints**
```python
# ✅ Use Python 3.10+ syntax
def get_item(item_id: int) -> Item | None:
    ...

# ❌ Avoid old Optional/Union
from typing import Optional
def get_item(item_id: int) -> Optional[Item]:
    ...
```

## Business Logic References

**CRITICAL:** This system implements complex business rules. Always consult:

- **`files/business_rules_doc.md`** - State machine, validations, refund matrix, date calculations
- **`files/business_overview_doc.md`** - Business context, user personas, pain points
- **`files/permissions_doc.md`** - RBAC permission matrix by role
- **`files/backend_agent.md`** - Code patterns and examples

**DO NOT duplicate business rules in code comments.** Reference the docs when implementing features.

### Key Business Rules to Remember

1. **Deposit Calculation**: `deposit_amount = total × (deposit_percentage / 100)` (default 50%)
2. **Payment Deadline**: 5 days from Pre-scheduled transition
3. **Changes Deadline**: 7 days before session_date
4. **Refund Matrix**: Varies by status and cancellation initiator (see business_rules_doc.md section 4.1)
5. **Room Availability**: One session per room per time slot (studio sessions only)
6. **Photographer Availability**: One assignment per photographer per time slot

## Configuration

The app uses **Pydantic Settings** to load configuration from environment variables.

**Key Settings** (see `app/core/config.py`):
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET`, `JWT_ALGORITHM`: Authentication config
- `ADMIN_EMAIL`, `ADMIN_PASSWORD`: Initial admin credentials (for system initialization)
- `PAYMENT_DEADLINE_DAYS`: 5 (business rule)
- `CHANGES_DEADLINE_DAYS`: 7 (business rule)
- `DEFAULT_DEPOSIT_PERCENTAGE`: 50 (business rule)

Create a `.env` file for application config and use `docker-compose.env` for Docker services.

## System Initialization

After running database migrations for the first time, you must initialize the system with permissions, roles, and the admin user.

**Prerequisites:**
1. Database migrations applied: `alembic upgrade head`
2. Environment variables set in `.env`:
   - `ADMIN_EMAIL`: Email for the initial admin user (e.g., admin@studio.gt)
   - `ADMIN_PASSWORD`: Strong password for the admin user

**Run the initialization script:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Run initialization
python -m app.scripts.init_system
```

**What the script does:**
1. Creates all system permissions (45+ permissions across all modules)
2. Creates 5 predefined roles:
   - `admin`: Full system access
   - `coordinator`: Session and client management
   - `photographer`: View and mark assigned sessions
   - `editor`: Mark sessions as ready for delivery
   - `user`: Basic role for self-registered users
3. Associates permissions to roles according to `files/permissions_doc.md`
4. Creates the initial admin user with the specified email and password
5. Assigns the `admin` role to the initial user

**The script is idempotent** - you can run it multiple times safely. It will skip existing records and only create missing ones.

**After initialization:**
- Login at `POST /api/v1/auth/login` with admin credentials
- Use the admin account to create other users and assign roles
- Public users can self-register at `POST /api/v1/auth/register` (get `user` role automatically)

## Database

**PostgreSQL 17** with **asyncpg** driver. All models use the `studio` schema.

**Running Migrations:**
```bash
# Activate virtual environment first
source .venv/bin/activate

# Create migration after model changes
alembic revision --autogenerate -m "add new field to session"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

**Important:**
- Models must use `__table_args__ = {'schema': 'studio'}`
- Use `Field()` for constraints: `Field(max_length=100, index=True, unique=True)`
- Foreign keys: `Field(foreign_key='studio.tablename.id')`
- Use `Decimal` for money fields, NOT float
- Use `datetime.utcnow` for timestamps

## Code Style & Conventions

**Ruff Configuration:**
- Single quotes (`quote-style = "single"`)
- Format with `ruff format .`

**Type Hints:**
- Always use type hints
- Use modern syntax: `int | None` instead of `Optional[int]`
- Use `list[Model]` instead of `List[Model]`

**Async/Await:**
- ALL database operations are async
- Use `await` for database queries
- Use `async with` for transactions

**Pydantic v2 Patterns:**
```python
class ItemPublic(BaseModel):
    model_config = {"from_attributes": True}  # NOT orm_mode

    @field_validator('price')
    @classmethod  # Required in v2
    def validate_price(cls, v: Decimal) -> Decimal:
        ...

    @model_validator(mode='after')
    def validate_model(self) -> Self:  # Returns Self, not cls
        ...
```

**Dependency Injection:**
```python
# Use Annotated for reusable dependencies
SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("/items")
async def list_items(db: SessionDep, user: CurrentUser):
    ...
```

## Common Gotchas

1. **Always activate virtual environment** - Run `source .venv/bin/activate` before Python/Alembic commands
2. **Use --env-file with docker-compose** - Always include `--env-file docker-compose.env`
3. **Don't commit in repositories** - Let services handle transactions
4. **Don't put business logic in routers** - Use services
5. **Don't hardcode business rules** - Reference configuration or docs
6. **Always denormalize package items** - Package explosion pattern
7. **Validate state transitions** - Check business_rules_doc.md section 1
8. **Use Decimal for money** - Never float
9. **Check availability before assignment** - Rooms and photographers
10. **Send emails OUTSIDE transactions** - Avoid rollback issues

## Testing

*Note: Test structure to be implemented*

Run tests with:
```bash
# Activate virtual environment first
source .venv/bin/activate

# Run all tests
pytest

# Verbose output
pytest -v

# Specific file
pytest tests/test_sessions.py

# By pattern
pytest -k "test_session_creation"
```

## Project Status

**Current Phase:** Early development - core models defined, API routes and business logic implementation in progress.

**Implemented:**
- ✅ Database models (users, clients, sessions, catalog)
- ✅ Alembic migrations
- ✅ Async database configuration
- ✅ Docker Compose setup
- ✅ Virtual environment with UV
- ✅ Schemas (Pydantic DTOs)
- ✅ Repositories (data access layer)
- ✅ Authentication & RBAC

**implementation in Progress:**
- ⏳ Services (business logic)
- ⏳ Routers (API endpoints)

**To Implement:**
- ⏳ Background tasks (Celery)
- ⏳ Email notifications
- ⏳ Comprehensive tests
- cuando crees los test http con bruno, utiliza {{back}} esta variables es igual a http://127.0.0.1:8000/api/v1