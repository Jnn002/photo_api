# Plan de Desarrollo - Spec-Driven Development
## Photography Studio Management System

**Versión:** 1.0  
**Fecha:** 8 de Octubre, 2025  
**Metodología:** Spec-Driven Development (SDD)  
**Enfoque:** Especificación → Tests → Implementación

---

## 📘 ¿Qué es Spec-Driven Development?

**Spec-Driven Development** es un enfoque donde:

1. **Primero escribimos especificaciones detalladas** (contratos de API, comportamiento esperado)
2. **Luego escribimos tests** basados en las especificaciones
3. **Finalmente implementamos** el código que cumple las especificaciones

**Beneficios:**
- ✅ Claridad antes de codificar (menos refactoring)
- ✅ Tests como documentación viva
- ✅ Menos bugs en producción
- ✅ API contracts claros para frontend

---

## 🎯 Tareas de Inicialización del Proyecto

Este documento cubre las **primeras 5 tareas** para inicializar el proyecto siguiendo SDD.

---

## TAREA 1: Setup del Proyecto y Base de Datos

### 📋 Especificación

**Objetivo:** Crear la infraestructura base del proyecto con PostgreSQL, FastAPI y estructura modular.

#### 1.1 Requisitos Funcionales

- **REQ-1.1.1:** El proyecto debe usar Python 3.12+ con UV como gestor de paquetes
- **REQ-1.1.2:** PostgreSQL 17 debe estar disponible via Docker Compose
- **REQ-1.1.3:** Redis debe estar disponible para Celery (futuro)
- **REQ-1.1.4:** La base de datos debe crearse con el schema completo (`postgres_database_schema.sql`)
- **REQ-1.1.5:** Debe existir seed data mínimo (roles, permisos, 1 usuario admin)

#### 1.2 Requisitos No Funcionales

- **REQ-1.2.1:** Tiempo de startup de Docker Compose < 30 segundos
- **REQ-1.2.2:** Conexión a DB debe usar pooling asíncrono
- **REQ-1.2.3:** Configuración via variables de entorno (`.env`)

#### 1.3 Estructura de Directorios Esperada

```
photography-studio-api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   └── core/
│       ├── __init__.py
│       ├── config.py
│       └── database.py
├── tests/
│   ├── __init__.py
│   └── conftest.py
├── docker-compose.yaml      # Ya existe
├── Dockerfile
├── .env.example
├── .env                      # Git ignored
├── pyproject.toml            # Ya existe
└── README.md
```

#### 1.4 Especificación de Configuración

**Archivo: `app/core/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application
    APP_NAME: str = "Photography Studio API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "studio_user"
    DB_PASSWORD: str
    DB_NAME: str = "photography_studio"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
settings = Settings()
```

#### 1.5 Especificación de Database Connection

**Archivo: `app/core/database.py`**

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.config import settings

# Engine global (singleton)
async_engine: AsyncEngine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
)

async_session_maker = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def init_db() -> None:
    """Initialize database (create all tables)"""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with async_session_maker() as session:
        yield session

async def close_db() -> None:
    """Close database connections"""
    await async_engine.dispose()
```

#### 1.6 Especificación de Docker Compose

**Archivo: `docker-compose.yaml`** (actualizar si es necesario)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:17-alpine
    container_name: photography_studio_db
    environment:
      POSTGRES_USER: studio_user
      POSTGRES_PASSWORD: ${DB_PASSWORD:-studio_password_dev}
      POSTGRES_DB: photography_studio
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./files/postgres_database_schema.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U studio_user -d photography_studio"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: photography_studio_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

#### 1.7 Tests de Aceptación

**Archivo: `tests/test_setup.py`**

```python
import pytest
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.config import settings
from app.core.database import async_engine, get_session

@pytest.mark.asyncio
async def test_database_connection():
    """Test: Database connection is established successfully"""
    async with async_engine.connect() as conn:
        result = await conn.execute("SELECT 1")
        assert result.scalar() == 1

@pytest.mark.asyncio
async def test_database_has_tables():
    """Test: Database has all required tables from schema"""
    required_tables = [
        'user', 'role', 'permission', 'client', 'session',
        'item', 'package', 'room', 'session_detail'
    ]
    
    async with async_engine.connect() as conn:
        for table in required_tables:
            result = await conn.execute(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'studio' AND table_name = '{table}')"
            )
            assert result.scalar() is True, f"Table {table} not found"

@pytest.mark.asyncio
async def test_seed_data_exists():
    """Test: Seed data (roles, permissions) exists"""
    async for session in get_session():
        from sqlmodel import select
        from app.users.models import Role
        
        result = await session.execute(select(Role))
        roles = list(result.scalars().all())
        
        assert len(roles) >= 4, "Should have at least 4 roles"
        role_names = [r.name for r in roles]
        assert 'Admin' in role_names
        assert 'Coordinator' in role_names
        assert 'Photographer' in role_names
        assert 'Editor' in role_names

def test_environment_variables_loaded():
    """Test: All required environment variables are loaded"""
    assert settings.DB_PASSWORD is not None
    assert settings.SECRET_KEY is not None
    assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")
```

#### 1.8 Criterios de Aceptación (DoD - Definition of Done)

- [ ] Docker Compose levanta PostgreSQL y Redis sin errores
- [ ] `docker-compose up -d` completa en < 30 segundos
- [ ] Base de datos contiene todas las tablas del schema
- [ ] Seed data (4 roles, permisos básicos) está insertado
- [ ] Archivo `.env.example` creado con todas las variables necesarias
- [ ] FastAPI app inicia sin errores (`uvicorn app.main:app`)
- [ ] Todos los tests de `test_setup.py` pasan (green)
- [ ] README actualizado con instrucciones de setup

#### 1.9 Comandos de Verificación

```bash
# 1. Levantar servicios
docker-compose up -d

# 2. Verificar salud de servicios
docker-compose ps

# 3. Verificar tablas en PostgreSQL
docker exec -it photography_studio_db psql -U studio_user -d photography_studio -c "\dt studio.*"

# 4. Instalar dependencias
uv sync

# 5. Correr tests
pytest tests/test_setup.py -v

# 6. Iniciar API
uvicorn app.main:app --reload
```

---

## TAREA 2: Sistema de Autenticación (JWT)

### 📋 Especificación

**Objetivo:** Implementar autenticación basada en JWT con login, logout y protección de endpoints.

#### 2.1 Requisitos Funcionales

- **REQ-2.1.1:** Usuario puede hacer login con email + password
- **REQ-2.1.2:** Sistema genera access token JWT (válido 30 min)
- **REQ-2.1.3:** Sistema genera refresh token JWT (válido 7 días)
- **REQ-2.1.4:** Tokens contienen: `user_id`, `email`, `roles[]`
- **REQ-2.1.5:** Endpoints protegidos validan token en header `Authorization: Bearer <token>`
- **REQ-2.1.6:** Passwords se almacenan hasheados con bcrypt (cost factor 12)

#### 2.2 API Contract Specification

**Endpoint 1: Login**

```yaml
POST /api/v1/auth/login
Content-Type: application/json

Request Body:
{
  "email": "admin@studio.com",      # Required, valid email
  "password": "SecurePass123!"      # Required, min 8 chars
}

Response 200 OK:
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "admin@studio.com",
    "full_name": "Admin User",
    "roles": ["Admin"]
  }
}

Response 401 Unauthorized:
{
  "detail": "Incorrect email or password"
}

Response 422 Unprocessable Entity:
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

**Endpoint 2: Refresh Token**

```yaml
POST /api/v1/auth/refresh
Content-Type: application/json

Request Body:
{
  "refresh_token": "eyJhbGci..."
}

Response 200 OK:
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 1800
}

Response 401 Unauthorized:
{
  "detail": "Invalid or expired refresh token"
}
```

**Endpoint 3: Get Current User**

```yaml
GET /api/v1/auth/me
Authorization: Bearer eyJhbGci...

Response 200 OK:
{
  "id": 1,
  "email": "admin@studio.com",
  "full_name": "Admin User",
  "phone": "+502 1234-5678",
  "roles": ["Admin"],
  "permissions": [
    "session.create",
    "session.view.all",
    "user.create",
    ...
  ]
}

Response 401 Unauthorized:
{
  "detail": "Could not validate credentials"
}
```

#### 2.3 Especificación de Seguridad

**Archivo: `app/core/security.py`**

```python
from datetime import datetime, timedelta
from typing import Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None
) -> str:
    """
    Create JWT access token
    
    Args:
        data: Payload data (must include 'sub' with user_id)
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict[str, Any]) -> str:
    """Create JWT refresh token (7 days expiration)"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate JWT token
    
    Raises:
        JWTError: If token is invalid or expired
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
```

#### 2.4 Especificación de Schemas

**Archivo: `app/auth/schemas.py`**

```python
from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserInfo(BaseModel):
    id: int
    email: str
    full_name: str
    roles: list[str]
    
class CurrentUserResponse(UserInfo):
    phone: str | None
    permissions: list[str]
```

#### 2.5 Tests de Aceptación

**Archivo: `tests/test_auth.py`**

```python
import pytest
from httpx import AsyncClient
from app.core.security import get_password_hash

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Test: User can login with correct credentials"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@studio.com", "password": "Admin123!"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 1800
    assert data["user"]["email"] == "admin@studio.com"
    assert "Admin" in data["user"]["roles"]

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Test: Login fails with incorrect password"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@studio.com", "password": "WrongPassword"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

@pytest.mark.asyncio
async def test_login_invalid_email(client: AsyncClient):
    """Test: Login fails with invalid email format"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "not-an-email", "password": "Admin123!"}
    )
    
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_current_user_with_valid_token(client: AsyncClient, auth_headers):
    """Test: Get current user info with valid token"""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["email"] == "admin@studio.com"
    assert "permissions" in data
    assert len(data["permissions"]) > 0

@pytest.mark.asyncio
async def test_get_current_user_without_token(client: AsyncClient):
    """Test: Get current user fails without token"""
    response = await client.get("/api/v1/auth/me")
    
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, refresh_token):
    """Test: Refresh token generates new access token"""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_protected_endpoint_requires_auth(client: AsyncClient):
    """Test: Protected endpoints return 401 without auth"""
    response = await client.get("/api/v1/users")
    assert response.status_code == 401
```

#### 2.6 Criterios de Aceptación (DoD)

- [ ] Usuario admin puede hacer login correctamente
- [ ] Login con credenciales incorrectas retorna 401
- [ ] Access token contiene user_id, email, roles
- [ ] Refresh token funciona correctamente
- [ ] Endpoint `/auth/me` retorna info del usuario con permisos
- [ ] Endpoints protegidos rechazan requests sin token
- [ ] Passwords nunca se exponen en respuestas
- [ ] Todos los tests de `test_auth.py` pasan
- [ ] Documentación OpenAPI generada automáticamente

---

## TAREA 3: Módulo de Usuarios y RBAC

### 📋 Especificación

**Objetivo:** Implementar CRUD completo de usuarios con sistema de roles y permisos.

#### 3.1 Requisitos Funcionales

- **REQ-3.1.1:** Admin puede crear nuevos usuarios
- **REQ-3.1.2:** Admin puede listar usuarios con paginación
- **REQ-3.1.3:** Admin puede ver detalles de un usuario
- **REQ-3.1.4:** Admin puede actualizar información de usuario
- **REQ-3.1.5:** Admin puede desactivar usuario (soft delete)
- **REQ-3.1.6:** Admin puede asignar/remover roles a usuarios
- **REQ-3.1.7:** Sistema valida permisos usando decorador `@require_permission`

#### 3.2 Modelos de Datos

**Archivo: `app/users/models.py`**

```python
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class User(SQLModel, table=True):
    __tablename__ = "user"
    __table_args__ = {"schema": "studio"}
    
    id: int | None = Field(default=None, primary_key=True)
    full_name: str = Field(max_length=100)
    email: str = Field(unique=True, index=True, max_length=100)
    password_hash: str = Field(max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    status: str = Field(default="Active", max_length=20)  # Active | Inactive
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: int | None = Field(default=None, foreign_key="studio.user.id")
    
    # Relationships
    roles: list["Role"] = Relationship(back_populates="users", link_model=UserRole)

class Role(SQLModel, table=True):
    __tablename__ = "role"
    __table_args__ = {"schema": "studio"}
    
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=50)
    description: str | None = None
    status: str = Field(default="Active", max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    users: list["User"] = Relationship(back_populates="roles", link_model=UserRole)
    permissions: list["Permission"] = Relationship(back_populates="roles", link_model=RolePermission)

class Permission(SQLModel, table=True):
    __tablename__ = "permission"
    __table_args__ = {"schema": "studio"}
    
    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(unique=True, max_length=100, index=True)
    name: str = Field(max_length=100)
    description: str | None = None
    module: str = Field(max_length=50)  # session, client, user, etc.
    status: str = Field(default="Active", max_length=20)
    
    # Relationships
    roles: list["Role"] = Relationship(back_populates="permissions", link_model=RolePermission)

# Link tables
class UserRole(SQLModel, table=True):
    __tablename__ = "user_role"
    __table_args__ = {"schema": "studio"}
    
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="studio.user.id")
    role_id: int = Field(foreign_key="studio.role.id")
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: int = Field(foreign_key="studio.user.id")

class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permission"
    __table_args__ = {"schema": "studio"}
    
    id: int | None = Field(default=None, primary_key=True)
    role_id: int = Field(foreign_key="studio.role.id")
    permission_id: int = Field(foreign_key="studio.permission.id")
```

#### 3.3 API Contract Specification

**Endpoint: Create User**

```yaml
POST /api/v1/users
Authorization: Bearer <admin_token>
Permission Required: user.create

Request Body:
{
  "full_name": "Carlos Pérez",
  "email": "carlos@studio.com",
  "password": "SecurePass123!",
  "phone": "+502 5555-1234",
  "role_ids": [2]  # Coordinator role
}

Response 201 Created:
{
  "id": 5,
  "full_name": "Carlos Pérez",
  "email": "carlos@studio.com",
  "phone": "+502 5555-1234",
  "status": "Active",
  "roles": ["Coordinator"],
  "created_at": "2025-10-08T10:30:00Z"
}

Response 403 Forbidden (if not admin):
{
  "detail": "Insufficient permissions"
}

Response 409 Conflict (email exists):
{
  "detail": "User with this email already exists"
}
```

**Endpoint: List Users**

```yaml
GET /api/v1/users?status=Active&limit=20&offset=0
Authorization: Bearer <admin_token>
Permission Required: user.view

Response 200 OK:
{
  "items": [
    {
      "id": 1,
      "full_name": "Admin User",
      "email": "admin@studio.com",
      "status": "Active",
      "roles": ["Admin"]
    },
    ...
  ],
  "total": 8,
  "limit": 20,
  "offset": 0
}
```

**Endpoint: Assign Role**

```yaml
POST /api/v1/users/{user_id}/roles
Authorization: Bearer <admin_token>
Permission Required: user.assign-role

Request Body:
{
  "role_id": 3  # Photographer
}

Response 200 OK:
{
  "id": 5,
  "full_name": "Carlos Pérez",
  "roles": ["Coordinator", "Photographer"]
}

Response 409 Conflict (already has role):
{
  "detail": "User already has this role"
}
```

#### 3.4 Tests de Aceptación

**Archivo: `tests/test_users.py`**

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user_as_admin(client: AsyncClient, admin_headers):
    """Test: Admin can create new user"""
    response = await client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "full_name": "Test User",
            "email": "test@studio.com",
            "password": "TestPass123!",
            "phone": "+502 1234-5678",
            "role_ids": [2]
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@studio.com"
    assert "Coordinator" in data["roles"]

@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient, admin_headers):
    """Test: Cannot create user with duplicate email"""
    # Create first user
    await client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "full_name": "User One",
            "email": "duplicate@studio.com",
            "password": "Pass123!",
            "role_ids": [2]
        }
    )
    
    # Try to create second with same email
    response = await client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "full_name": "User Two",
            "email": "duplicate@studio.com",
            "password": "Pass123!",
            "role_ids": [2]
        }
    )
    
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_list_users_with_pagination(client: AsyncClient, admin_headers):
    """Test: Can list users with pagination"""
    response = await client.get(
        "/api/v1/users?limit=10&offset=0",
        headers=admin_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) <= 10

@pytest.mark.asyncio
async def test_create_user_as_coordinator_forbidden(client: AsyncClient, coordinator_headers):
    """Test: Coordinator cannot create users"""
    response = await client.post(
        "/api/v1/users",
        headers=coordinator_headers,
        json={
            "full_name": "Test User",
            "email": "test@studio.com",
            "password": "Pass123!",
            "role_ids": [2]
        }
    )
    
    assert response.status_code == 403
```

#### 3.5 Criterios de Aceptación (DoD)

- [ ] Admin puede crear usuarios con roles
- [ ] No se permiten emails duplicados
- [ ] Lista de usuarios soporta paginación y filtros
- [ ] Passwords se almacenan hasheados
- [ ] Solo Admin puede gestionar usuarios
- [ ] Roles se asignan correctamente
- [ ] Soft delete funciona (status = Inactive)
- [ ] Todos los tests pasan
- [ ] OpenAPI docs muestran permisos requeridos

---

## TAREA 4: Módulo de Clientes (CRUD Completo)

### 📋 Especificación

**Objetivo:** Implementar gestión completa de clientes con búsqueda y validaciones.

#### 4.1 Requisitos Funcionales

- **REQ-4.1.1:** Coordinadores pueden crear clientes (Individual o Institutional)
- **REQ-4.1.2:** Email y teléfono primario son obligatorios
- **REQ-4.1.3:** Email debe ser único en el sistema
- **REQ-4.1.4:** Búsqueda por nombre, email o teléfono
- **REQ-4.1.5:** Filtrado por tipo de cliente y estado
- **REQ-4.1.6:** Paginación en listados

#### 4.2 Modelo de Datos

**Archivo: `app/clients/models.py`**

```python
from sqlmodel import SQLModel, Field
from datetime import datetime

class Client(SQLModel, table=True):
    __tablename__ = "client"
    __table_args__ = {"schema": "studio"}
    
    id: int | None = Field(default=None, primary_key=True)
    full_name: str = Field(max_length=100, index=True)
    email: str = Field(unique=True, index=True, max_length=100)
    primary_phone: str = Field(max_length=20)
    secondary_phone: str | None = Field(default=None, max_length=20)
    delivery_address: str | None = None
    client_type: str = Field(max_length=20)  # Individual | Institutional
    notes: str | None = None
    status: str = Field(default="Active", max_length=20)  # Active | Inactive
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: int = Field(foreign_key="studio.user.id")
```

#### 4.3 API Contract Specification

**Endpoint: Create Client**

```yaml
POST /api/v1/clients
Authorization: Bearer <coordinator_token>
Permission Required: client.create

Request Body:
{
  "full_name": "María González",
  "email": "maria@example.com",
  "primary_phone": "+502 5555-9876",
  "secondary_phone": "+502 4444-1234",
  "delivery_address": "5ta Avenida 10-20 Zona 10, Guatemala",
  "client_type": "Individual",
  "notes": "Cliente frecuente, prefiere sesiones matutinas"
}

Response 201 Created:
{
  "id": 15,
  "full_name": "María González",
  "email": "maria@example.com",
  "primary_phone": "+502 5555-9876",
  "client_type": "Individual",
  "status": "Active",
  "created_at": "2025-10-08T14:20:00Z"
}

Response 409 Conflict:
{
  "detail": "Client with this email already exists"
}
```

**Endpoint: Search Clients**

```yaml
GET /api/v1/clients/search?q=maria&client_type=Individual&limit=20
Authorization: Bearer <coordinator_token>
Permission Required: client.view

Response 200 OK:
{
  "items": [
    {
      "id": 15,
      "full_name": "María González",
      "email": "maria@example.com",
      "primary_phone": "+502 5555-9876",
      "client_type": "Individual",
      "status": "Active"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### 4.4 Tests de Aceptación

**Archivo: `tests/test_clients.py`**

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_client_success(client: AsyncClient, coordinator_headers):
    """Test: Coordinator can create client"""
    response = await client.post(
        "/api/v1/clients",
        headers=coordinator_headers,
        json={
            "full_name": "Test Client",
            "email": "testclient@example.com",
            "primary_phone": "+502 1234-5678",
            "client_type": "Individual"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testclient@example.com"
    assert data["status"] == "Active"

@pytest.mark.asyncio
async def test_create_client_duplicate_email(client: AsyncClient, coordinator_headers):
    """Test: Cannot create client with duplicate email"""
    # First client
    await client.post(
        "/api/v1/clients",
        headers=coordinator_headers,
        json={
            "full_name": "Client One",
            "email": "duplicate@example.com",
            "primary_phone": "+502 1111-1111",
            "client_type": "Individual"
        }
    )
    
    # Duplicate email
    response = await client.post(
        "/api/v1/clients",
        headers=coordinator_headers,
        json={
            "full_name": "Client Two",
            "email": "duplicate@example.com",
            "primary_phone": "+502 2222-2222",
            "client_type": "Individual"
        }
    )
    
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_search_clients_by_name(client: AsyncClient, coordinator_headers):
    """Test: Can search clients by name"""
    response = await client.get(
        "/api/v1/clients/search?q=María",
        headers=coordinator_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
    assert "maría" in data["items"][0]["full_name"].lower()

@pytest.mark.asyncio
async def test_photographer_cannot_view_clients(client: AsyncClient, photographer_headers):
    """Test: Photographer cannot access client data"""
    response = await client.get(
        "/api/v1/clients",
        headers=photographer_headers
    )
    
    assert response.status_code == 403
```

#### 4.5 Criterios de Aceptación (DoD)

- [ ] Coordinadores pueden crear clientes
- [ ] Email único validado correctamente
- [ ] Búsqueda funciona por nombre, email, teléfono
- [ ] Filtros por tipo y estado funcionan
- [ ] Paginación implementada
- [ ] Fotógrafos NO pueden ver clientes (permisos)
- [ ] Todos los tests pasan
- [ ] Validaciones de Pydantic funcionan

---

## TAREA 5: Módulo de Catálogo (Items y Packages)

### 📋 Especificación

**Objetivo:** Implementar gestión de items, packages y la lógica de "explosión de paquetes".

#### 5.1 Requisitos Funcionales

- **REQ-5.1.1:** Admin puede crear items individuales (fotos, videos, álbumes)
- **REQ-5.1.2:** Admin puede crear packages con múltiples items
- **REQ-5.1.3:** System implementa "package explosion" (patrón crítico)
- **REQ-5.1.4:** Datos históricos son inmutables (denormalización)
- **REQ-5.1.5:** Items y packages pueden activarse/desactivarse

#### 5.2 Modelos de Datos

**Archivo: `app/catalog/models.py`**

```python
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from decimal import Decimal

class Item(SQLModel, table=True):
    __tablename__ = "item"
    __table_args__ = {"schema": "studio"}
    
    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(unique=True, max_length=50, index=True)
    name: str = Field(max_length=100)
    description: str | None = None
    item_type: str = Field(max_length=50)  # Digital Photo, Printed Photo, Album, Video
    unit_price: Decimal = Field(max_digits=10, decimal_places=2)
    unit_measure: str = Field(max_length=20)  # Unit, Hour, Package
    default_quantity: int | None = None
    status: str = Field(default="Active", max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: int = Field(foreign_key="studio.user.id")

class Package(SQLModel, table=True):
    __tablename__ = "package"
    __table_args__ = {"schema": "studio"}
    
    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(unique=True, max_length=50, index=True)
    name: str = Field(max_length=100)
    description: str | None = None
    session_type: str = Field(max_length=20)  # Studio | External | Both
    base_price: Decimal = Field(max_digits=10, decimal_places=2)
    estimated_editing_days: int = Field(default=5)
    status: str = Field(default="Active", max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: int = Field(foreign_key="studio.user.id")
    
    # Relationships
    items: list["Item"] = Relationship(back_populates="packages", link_model=PackageItem)

class PackageItem(SQLModel, table=True):
    __tablename__ = "package_item"
    __table_args__ = {"schema": "studio"}
    
    id: int | None = Field(default=None, primary_key=True)
    package_id: int = Field(foreign_key="studio.package.id")
    item_id: int = Field(foreign_key="studio.item.id")
    quantity: int = Field(default=1)
    display_order: int | None = None
```

#### 5.3 Especificación de "Package Explosion"

**Concepto:** Cuando un package se agrega a una sesión, debe "explotar" en items individuales para denormalizar los datos y mantener inmutabilidad histórica.

**Servicio: `app/catalog/service.py`**

```python
from decimal import Decimal
from sqlmodel.ext.asyncio.session import AsyncSession
from app.catalog.models import Package, PackageItem, Item

async def explode_package(
    package_id: int,
    db: AsyncSession
) -> list[dict]:
    """
    Explode package into individual items for session_detail
    
    Returns list of dictionaries ready for SessionDetail creation:
    [
        {
            "line_type": "Item",
            "reference_id": package.id,
            "reference_type": "Package",
            "item_code": "FOTO-DIGITAL",
            "item_name": "Foto Digital 4x6",
            "quantity": 10,
            "unit_price": Decimal("5.00"),
            "line_subtotal": Decimal("50.00")
        },
        ...
    ]
    
    CRITICAL: Data is denormalized (copied) to preserve historical accuracy
    """
    # Implementation will be tested
    pass
```

#### 5.4 API Contract Specification

**Endpoint: Create Package**

```yaml
POST /api/v1/packages
Authorization: Bearer <admin_token>
Permission Required: package.create

Request Body:
{
  "code": "PKG-WEDDING-BASIC",
  "name": "Paquete Boda Básico",
  "description": "Incluye cobertura de 6 horas y 100 fotos digitales",
  "session_type": "External",
  "base_price": 3500.00,
  "estimated_editing_days": 7,
  "items": [
    {"item_id": 1, "quantity": 100},  # 100 digital photos
    {"item_id": 5, "quantity": 1},    # 1 video (hours)
    {"item_id": 10, "quantity": 1}    # 1 album
  ]
}

Response 201 Created:
{
  "id": 8,
  "code": "PKG-WEDDING-BASIC",
  "name": "Paquete Boda Básico",
  "base_price": 3500.00,
  "items": [
    {
      "item_code": "FOTO-DIGITAL",
      "item_name": "Foto Digital",
      "quantity": 100
    },
    ...
  ]
}
```

**Endpoint: Get Package with Explosion Preview**

```yaml
GET /api/v1/packages/{package_id}/explode
Authorization: Bearer <coordinator_token>

Response 200 OK:
{
  "package_id": 8,
  "package_name": "Paquete Boda Básico",
  "total_price": 3500.00,
  "exploded_items": [
    {
      "item_code": "FOTO-DIGITAL",
      "item_name": "Foto Digital",
      "quantity": 100,
      "unit_price": 10.00,
      "subtotal": 1000.00
    },
    {
      "item_code": "VIDEO-HORA",
      "item_name": "Video por Hora",
      "quantity": 1,
      "unit_price": 1500.00,
      "subtotal": 1500.00
    },
    {
      "item_code": "ALBUM-20X30",
      "item_name": "Álbum 20x30",
      "quantity": 1,
      "unit_price": 1000.00,
      "subtotal": 1000.00
    }
  ]
}
```

#### 5.5 Tests de Aceptación

**Archivo: `tests/test_catalog.py`**

```python
import pytest
from httpx import AsyncClient
from decimal import Decimal

@pytest.mark.asyncio
async def test_create_item(client: AsyncClient, admin_headers):
    """Test: Admin can create item"""
    response = await client.post(
        "/api/v1/items",
        headers=admin_headers,
        json={
            "code": "FOTO-DIGITAL-TEST",
            "name": "Foto Digital Test",
            "item_type": "Digital Photo",
            "unit_price": 10.00,
            "unit_measure": "Unit",
            "default_quantity": 1
        }
    )
    
    assert response.status_code == 201
    assert response.json()["code"] == "FOTO-DIGITAL-TEST"

@pytest.mark.asyncio
async def test_explode_package(client: AsyncClient, db_session, test_package):
    """Test: Package explosion returns correct items"""
    from app.catalog.service import explode_package
    
    exploded = await explode_package(test_package.id, db_session)
    
    assert len(exploded) > 0
    assert all("item_code" in item for item in exploded)
    assert all("quantity" in item for item in exploded)
    assert all("unit_price" in item for item in exploded)
    assert all("line_subtotal" in item for item in exploded)
    
    # Verify subtotal calculation
    total = sum(item["line_subtotal"] for item in exploded)
    assert total == test_package.base_price

@pytest.mark.asyncio
async def test_package_immutability(client: AsyncClient, admin_headers, test_package):
    """Test: Changing package doesn't affect historical sessions"""
    # This will be tested when we implement sessions
    # For now, just verify package can be updated
    response = await client.patch(
        f"/api/v1/packages/{test_package.id}",
        headers=admin_headers,
        json={"base_price": 4000.00}
    )
    
    assert response.status_code == 200
    assert response.json()["base_price"] == 4000.00
```

#### 5.6 Criterios de Aceptación (DoD)

- [ ] Admin puede crear items con validaciones
- [ ] Admin puede crear packages con items
- [ ] Package explosion genera lista correcta de items
- [ ] Datos denormalizados correctamente
- [ ] Subtotales calculados automáticamente
- [ ] Items y packages pueden desactivarse
- [ ] Coordinadores NO pueden modificar catálogo
- [ ] Todos los tests pasan
- [ ] Documentación de API completa

---

## 🎯 Resumen de las 5 Tareas

| Tarea | Componente | Complejidad | Estimación | Prioridad |
|-------|-----------|-------------|------------|-----------|
| **1** | Setup + DB | Baja | 1-2 días | 🔴 Crítica |
| **2** | Autenticación | Media | 2-3 días | 🔴 Crítica |
| **3** | Usuarios + RBAC | Media-Alta | 3-4 días | 🔴 Crítica |
| **4** | Clientes | Baja-Media | 2 días | 🟡 Alta |
| **5** | Catálogo | Media-Alta | 3-4 días | 🟡 Alta |
| **TOTAL** | - | - | **~2 semanas** | - |

---

## 📝 Checklist General de Spec-Driven Development

Para cada tarea, seguir este proceso:

### 1️⃣ Fase de Especificación
- [ ] Definir requisitos funcionales y no funcionales
- [ ] Documentar API contracts (request/response)
- [ ] Especificar modelos de datos
- [ ] Definir reglas de validación
- [ ] Establecer criterios de aceptación

### 2️⃣ Fase de Testing
- [ ] Escribir tests de aceptación (basados en specs)
- [ ] Escribir tests unitarios para lógica de negocio
- [ ] Verificar que tests fallan (RED)

### 3️⃣ Fase de Implementación
- [ ] Implementar código mínimo para pasar tests
- [ ] Verificar que tests pasan (GREEN)
- [ ] Refactorizar si es necesario (REFACTOR)
- [ ] Verificar criterios de aceptación

### 4️⃣ Fase de Documentación
- [ ] Actualizar README si necesario
- [ ] Verificar OpenAPI docs generada
- [ ] Agregar comentarios en código complejo

---

## 🚀 Próximos Pasos

Después de completar estas 5 tareas, el siguiente bloque sería:

**Tareas 6-10:**
- Tarea 6: Módulo de Sesiones (Modelos + State Machine)
- Tarea 7: Validación de Disponibilidad (CRÍTICO)
- Tarea 8: Asignación de Recursos (Fotógrafos + Salas)
- Tarea 9: Sistema de Pagos y Transiciones
- Tarea 10: Celery Jobs (Auto-cancelación, recordatorios)

---

## 📚 Referencias

- **Documentos del Proyecto:**
  - `business_rules_doc.md` - Reglas de negocio
  - `postgres_database_schema.sql` - Schema completo
  - `permissions_doc.md` - Matriz RBAC
  - `backend_agent.md` - Guías de desarrollo

- **Testing Frameworks:**
  - pytest + pytest-asyncio
  - httpx (test client)
  - pytest-cov (coverage)

- **Convenciones:**
  - Tests filename: `test_*.py`
  - Test function: `test_*`
  - Fixtures en `conftest.py`

---

**¡Comencemos con la Tarea 1! 🎉**

_Documento creado: 8 de Octubre, 2025_  
_Próxima actualización: Después de completar Tarea 5_
