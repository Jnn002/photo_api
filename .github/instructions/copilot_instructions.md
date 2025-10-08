---
applyTo: "**"
---
# Project general coding standards

You are an expert backend developer, and you follow the next instructions:

### Module Structure (Feature-Based)
```
app/
├── core/
│   ├── config.py          # Pydantic Settings
│   ├── database.py        # Async DB connection
│   ├── security.py        # JWT & password hashing
│   ├── permissions.py     # RBAC dependencies
│   └── exceptions.py      # Custom exceptions
├── users/
│   ├── models.py          # SQLModel tables
│   ├── schemas.py         # Pydantic I/O schemas
│   ├── repository.py      # DB queries
│   ├── service.py         # Business logic
│   └── router.py          # FastAPI endpoints
├── sessions/
│   ├── models.py
│   ├── schemas.py
│   ├── repository.py
│   ├── service.py
│   ├── router.py
│   └── state_machine.py   # State transitions
├── clients/
├── catalog/               # items, packages, rooms
└── tasks/
    ├── celery_app.py
    └── session_tasks.py
```

### Layer Responsibilities

**Models** (`models.py`):
- SQLModel table definitions
- Relationships using `Relationship()`
- Database constraints via `Field()`
- NO business logic

**Schemas** (`schemas.py`):
- Request DTOs (Create, Update)
- Response DTOs (Public, Detail)
- Pydantic v2 validators
- Separate from models for flexibility

**Repository** (`repository.py`):
- Pure data access layer
- Async database queries only
- Return models or None
- NO business logic or validation

**Service** (`service.py`):
- Business logic and orchestration
- Use repositories for data access
- Transaction management
- Call external services
- Raise custom exceptions

**Router** (`router.py`):
- HTTP endpoints
- Dependency injection
- Permission checks
- Call services
- Handle HTTP responses/errors

## Package Management
- Use UV for all package management
- Pin exact versions in `pyproject.toml`


If you are working with python files, follow the FastAPI and SQLModel best practices from the `fastapi.instructions.md` file.