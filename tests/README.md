# Photography Studio API - Test Suite

Comprehensive test suite for the Users module with >80% code coverage.

## Structure

```
tests/
├── conftest.py                    # Root fixtures (DB, client, sessions)
├── users/
│   ├── conftest.py                # User-specific fixtures and factories
│   ├── test_security.py           # JWT & password hashing tests (120+ tests)
│   ├── test_user_service.py       # UserService business logic tests (80+ tests)
│   ├── test_role_service.py       # RoleService business logic tests (30+ tests)
│   ├── test_permission_service.py # PermissionService tests (25+ tests)
│   ├── test_auth_router.py        # Authentication endpoints tests (40+ tests)
│   └── test_user_router.py        # User management endpoints tests (50+ tests)
```

## Running Tests

### Prerequisites

1. Activate virtual environment:
```bash
source .venv/bin/activate
```

2. Ensure test database is available:
```bash
# Update docker-compose.env with test database name
# or create test database manually
createdb studio_test_db
```

3. Install test dependencies (if not already installed):
```bash
uv sync
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app/users --cov-report=html --cov-report=term

# Run specific test file
pytest tests/users/test_security.py

# Run specific test class
pytest tests/users/test_user_service.py::TestAuthentication

# Run specific test
pytest tests/users/test_security.py::TestPasswordHashing::test_password_hashing_creates_hash
```

### Run Tests by Category

```bash
# Unit tests (service layer)
pytest tests/users/test_*_service.py

# Integration tests (API endpoints)
pytest tests/users/test_*_router.py

# Security tests
pytest tests/users/test_security.py

# Specific module
pytest tests/users/test_user_service.py -v
```

### Run Tests with Markers

```bash
# Run async tests only
pytest -m asyncio

# Run specific test pattern
pytest -k "login"
pytest -k "password"
pytest -k "authentication"
```

## Test Coverage

Expected coverage for Users module:

- **app/core/security.py**: >95%
- **app/users/service.py**: >85%
- **app/users/repository.py**: >80% (tested via service layer)
- **app/users/router.py**: >80%
- **Overall Users Module**: >80%

Generate coverage report:
```bash
pytest --cov=app/users --cov=app/core/security --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Categories

### 1. Security Tests (test_security.py)
- Password hashing with bcrypt (12 rounds)
- JWT access token creation and validation
- JWT refresh token creation and validation
- Token expiration handling
- Token claim validation (jti, iat, iss, aud, type)
- Permission caching
- Security best practices

**Key Features Tested:**
- ✅ Bcrypt password hashing with 12 rounds
- ✅ JWT with RFC 7519 standard claims
- ✅ Access vs Refresh token differentiation
- ✅ Issuer and audience validation
- ✅ Token expiration handling
- ✅ Permission caching on user object

### 2. UserService Tests (test_user_service.py)
- User authentication with JWT tokens
- User CRUD operations
- Password management
- User activation/deactivation
- Role assignment and removal
- Business rule validations

**Key Features Tested:**
- ✅ Login returns access + refresh tokens
- ✅ Email uniqueness validation
- ✅ Cannot deactivate self
- ✅ New password must differ from current
- ✅ Only active roles can be assigned
- ✅ No duplicate role assignments

### 3. RoleService Tests (test_role_service.py)
- Role CRUD operations
- Role name uniqueness
- Role with permissions eager loading
- Pagination

**Key Features Tested:**
- ✅ Unique role names
- ✅ Role status management (ACTIVE/INACTIVE)
- ✅ Load roles with permissions

### 4. PermissionService Tests (test_permission_service.py)
- Permission creation and validation
- Permission code format (module.action[.scope])
- Filtering by module
- Permission code uniqueness

**Key Features Tested:**
- ✅ Code format validation (module.action[.scope])
- ✅ Unique permission codes
- ✅ Filter by module
- ✅ Active/inactive filtering

### 5. Authentication Router Tests (test_auth_router.py)
- POST /auth/login - Login endpoint
- POST /auth/refresh - Token refresh endpoint
- POST /auth/logout - Logout endpoint
- Complete authentication workflows
- Security validations

**Key Features Tested:**
- ✅ Successful login returns tokens
- ✅ Invalid credentials return 401
- ✅ Inactive users cannot login
- ✅ Refresh token rotation
- ✅ Cannot use access token as refresh
- ✅ Logout placeholder (TODO: Redis blacklist)

### 6. User Router Tests (test_user_router.py)
- GET /users - List users with pagination
- POST /users - Create user
- GET /users/me - Get current user
- GET /users/{id} - Get user by ID
- PATCH /users/{id} - Update user
- DELETE /users/{id} - Deactivate user
- PUT /users/{id}/reactivate - Reactivate user
- PATCH /users/{id}/password - Change password
- Role assignment endpoints
- Permission checks

**Key Features Tested:**
- ✅ Permission-based authorization
- ✅ Pagination and filtering
- ✅ Self-service operations (change own password, view own data)
- ✅ Admin operations (change other users)
- ✅ Business rule enforcement via HTTP responses

## Fixtures Overview

### Root Fixtures (conftest.py)
- `test_engine`: Test database engine (session-scoped)
- `setup_database`: Creates/drops test tables (session-scoped)
- `db_session`: Database session with auto-rollback (function-scoped)
- `client`: AsyncClient with dependency overrides (function-scoped)

### User Fixtures (users/conftest.py)

**Permission Fixtures:**
- `create_test_permission`: Factory for creating permissions
- `test_permission`: Pre-created test permission

**Role Fixtures:**
- `create_test_role`: Factory for creating roles
- `test_role`: Generic test role
- `admin_role`: Admin role
- `coordinator_role`: Coordinator role
- `photographer_role`: Photographer role

**User Fixtures:**
- `create_test_user`: Factory for creating users
- `test_user`: Active test user
- `inactive_user`: Inactive test user
- `admin_user`: User with admin role
- `coordinator_user`: User with coordinator role
- `create_user_with_roles`: Factory for users with specific roles
- `create_multiple_users`: Batch user creation

**Authentication Helpers:**
- `get_auth_headers`: Generate JWT auth headers
- `test_user_headers`: Headers for test user
- `admin_headers`: Headers for admin user
- `coordinator_headers`: Headers for coordinator user

**Role/Permission Helpers:**
- `assign_permission_to_role`: Helper for permission assignment

## Best Practices

### Writing New Tests

1. **Use Descriptive Names:**
```python
async def test_create_user_with_duplicate_email_raises_exception():
    """Test that creating user with duplicate email raises DuplicateEmailException."""
    ...
```

2. **Arrange-Act-Assert Pattern:**
```python
async def test_example():
    # Arrange
    user = await create_test_user(email='test@example.com')

    # Act
    result = await service.some_operation(user.id)

    # Assert
    assert result is not None
    assert result.status == Status.ACTIVE
```

3. **Use Fixtures for Setup:**
```python
async def test_with_fixtures(db_session, test_user, admin_role):
    """Fixtures handle setup and teardown."""
    service = UserService(db_session)
    ...
```

4. **Test Both Success and Failure Cases:**
```python
async def test_operation_success(...):
    """Test successful operation."""
    ...

async def test_operation_fails_with_invalid_input(...):
    """Test operation fails with invalid input."""
    with pytest.raises(ValidationException):
        ...
```

5. **Isolate Tests:**
- Each test should be independent
- Use `db_session` fixture for automatic rollback
- Don't rely on test execution order

## Common Patterns

### Testing Service Layer
```python
@pytest.mark.asyncio
async def test_service_method(db_session: AsyncSession, test_user: User):
    """Test service business logic."""
    service = UserService(db_session)

    result = await service.some_method(test_user.id)

    assert result is not None
    # Assertions...
```

### Testing API Endpoints
```python
@pytest.mark.asyncio
async def test_api_endpoint(client: AsyncClient, admin_headers: dict[str, str]):
    """Test API endpoint."""
    response = await client.post(
        '/users',
        headers=admin_headers,
        json={'email': 'test@example.com', ...},
    )

    assert response.status_code == 201
    data = response.json()
    assert data['email'] == 'test@example.com'
```

### Testing Permissions
```python
@pytest.mark.asyncio
async def test_operation_requires_permission(
    client: AsyncClient,
    test_user_headers: dict[str, str]  # User without permission
):
    """Test that operation fails without required permission."""
    response = await client.post('/users', headers=test_user_headers, json={...})

    assert response.status_code == 403  # Forbidden
```

### Testing Exceptions
```python
@pytest.mark.asyncio
async def test_operation_raises_exception(db_session: AsyncSession):
    """Test that operation raises specific exception."""
    service = UserService(db_session)

    with pytest.raises(UserNotFoundException) as exc_info:
        await service.get_user_by_id(99999)

    assert '99999' in str(exc_info.value)
```

## Troubleshooting

### Tests Fail to Connect to Database
- Ensure test database exists: `createdb studio_test_db`
- Check `TEST_DATABASE_URL` in `tests/conftest.py`
- Verify Docker containers are running: `docker compose --env-file docker-compose.env ps`

### Import Errors
- Activate virtual environment: `source .venv/bin/activate`
- Install dependencies: `uv sync`

### Tests Hang or Timeout
- Check for deadlocks in async operations
- Ensure all `async def` test functions have `@pytest.mark.asyncio` decorator
- Verify database connections are properly closed

### Flaky Tests
- Tests should be idempotent
- Check for race conditions in async code
- Ensure proper test isolation (use fixtures with rollback)

### Coverage Not Accurate
- Run with: `pytest --cov=app/users --cov-report=html`
- Check that all modules are imported in tests
- Verify test database is separate from development database

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_DB: studio_test_db
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install UV
        run: pip install uv

      - name: Install dependencies
        run: uv sync

      - name: Run tests
        run: |
          source .venv/bin/activate
          pytest --cov=app/users --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Future Improvements

- [ ] Add Redis blacklist tests for token revocation
- [ ] Add rate limiting tests (slowapi)
- [ ] Add WebSocket tests (if applicable)
- [ ] Add load testing (locust)
- [ ] Add mutation testing (mutmut)
- [ ] Add contract tests for external APIs

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [HTTPX AsyncClient](https://www.python-httpx.org/async/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLModel Testing](https://sqlmodel.tiangolo.com/tutorial/testing/)
