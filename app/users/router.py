"""
User routers for authentication and user management endpoints.

This module exposes REST endpoints for:
- Authentication (login, refresh, logout)
- User CRUD operations
- Role management
- Permission management
- User-role assignment
"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, status
from pydantic import Field

from app.core.dependencies import CurrentActiveUser, SessionDep
from app.core.permissions import require_permission
from app.core.schemas import PaginatedResponse
from app.core.security import (
    create_access_token,
    oauth2_scheme,
    verify_refresh_token,
)
from app.users.models import Role, User, UserRole
from app.users.schemas import (
    LogoutRequest,
    PermissionCreate,
    PermissionPublic,
    RoleCreate,
    RolePublic,
    RoleUpdate,
    RoleWithPermissions,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserPasswordUpdate,
    UserPublic,
    UserUpdate,
    UserWithRoles,
)
from app.users.service import PermissionService, RoleService, UserService

# ==================== Authentication Router ====================

auth_router = APIRouter(prefix='/auth', tags=['authentication'])


@auth_router.post(
    '/login',
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary='User login',
    description='Authenticate user with email and password. Returns access token and refresh token.',
)
async def login(
    credentials: UserLogin,
    db: SessionDep,
) -> TokenResponse:
    """
    Authenticate user and return JWT tokens.

    Returns both access token (30 min) and refresh token (30 days).

    **Required fields:**
    - email: User email address
    - password: User password

    **Returns:**
    - access_token: JWT access token for API requests
    - refresh_token: JWT refresh token for obtaining new access tokens
    - token_type: Always 'bearer'
    - expires_in: Access token expiration time in seconds
    - user: Public user information
    """
    service = UserService(db)
    return await service.authenticate_user(credentials)


@auth_router.post(
    '/refresh',
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary='Refresh access token',
    description='Exchange a valid refresh token for a new access token and refresh token.',
)
async def refresh_token(
    refresh_token: Annotated[str, Body(..., embed=True)],
    db: SessionDep,
) -> TokenResponse:
    """
    Refresh access token using a valid refresh token.

    When the access token expires, use this endpoint with your refresh token
    to obtain a new access token without requiring re-authentication.

    **Required:**
    - refresh_token: Valid JWT refresh token

    **Returns:**
    - New access_token and refresh_token pair
    - Updated user information

    **Security:**
    - Validates that the refresh token is not in the blocklist (not revoked)
    - Checks that the user is still active
    """
    from app.core.enums import Status
    from app.core.exceptions import (
        InactiveUserException,
        InvalidTokenException,
        UserNotFoundException,
    )
    from app.core.redis import token_in_blocklist
    from app.core.security import create_refresh_token

    # Verify the refresh token
    payload = verify_refresh_token(refresh_token)
    email = payload.get('sub')
    jti = payload.get('jti')

    if not jti:
        raise InvalidTokenException('Refresh token missing JTI claim')

    # Check if refresh token is in blocklist (revoked)
    if await token_in_blocklist(jti):
        raise InvalidTokenException('Refresh token has been revoked')

    # Get user and generate new tokens
    service = UserService(db)
    user_repo = service.user_repo
    user = await user_repo.find_by_email(email)  # type: ignore

    if not user:
        raise UserNotFoundException(email)  # type: ignore

    # Check if user is active
    if user.status != Status.ACTIVE:
        raise InactiveUserException(f'User {user.email} is inactive')

    # Generate new token pair
    new_access_token = create_access_token(data={'sub': user.email})
    new_refresh_token = create_refresh_token(data={'sub': user.email})

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=30 * 60,  # 30 minutes
        user=UserPublic.model_validate(user),
    )


@auth_router.post(
    '/logout',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='User logout',
    description='Logout current user by revoking both access and refresh tokens.',
)
async def logout(
    logout_data: LogoutRequest,
    current_user: CurrentActiveUser,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> None:
    """
    Logout current user by invalidating both access and refresh tokens.

    This endpoint adds both the access token (from Authorization header) and
    the refresh token (from request body) to Redis blocklist. Once added,
    these tokens cannot be used for authentication or token refresh.

    **How it works:**
    1. Extracts JTI from current access token (from Authorization header)
    2. Extracts JTI from provided refresh token (from request body)
    3. Calculates remaining TTL for both tokens
    4. Adds both JTIs to Redis blocklist with appropriate TTL
    5. Redis automatically removes expired tokens from blocklist

    **Required:**
    - refresh_token: The refresh token to revoke (from request body)
    - Authorization header: Bearer token (access token) - automatically extracted

    **Security:**
    - User must be authenticated (valid access token required)
    - Both tokens are immediately invalidated
    - Subsequent requests with these tokens will fail with 401 Unauthorized

    **Example request:**
    ```json
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
    """
    from datetime import datetime, timezone

    from app.core.exceptions import InvalidTokenException
    from app.core.redis import revoke_token_pair
    from app.core.security import decode_access_token

    # Extract JTI from access token (current request token)
    access_payload = decode_access_token(token)
    access_jti = access_payload.get('jti')
    access_exp = access_payload.get('exp')

    if not access_jti or not access_exp:
        raise InvalidTokenException('Invalid access token structure')

    # Extract JTI from refresh token
    refresh_payload = verify_refresh_token(logout_data.refresh_token)
    refresh_jti = refresh_payload.get('jti')
    refresh_exp = refresh_payload.get('exp')

    if not refresh_jti or not refresh_exp:
        raise InvalidTokenException('Invalid refresh token structure')

    # Calculate remaining TTL for both tokens
    now = datetime.now(timezone.utc).timestamp()
    access_ttl = max(int(access_exp - now), 0)
    refresh_ttl = max(int(refresh_exp - now), 0)

    # Add both tokens to blocklist
    await revoke_token_pair(
        access_jti=access_jti,
        refresh_jti=refresh_jti,
        access_ttl=access_ttl,
        refresh_ttl=refresh_ttl,
    )

    return None


# ==================== Users Router ====================

users_router = APIRouter(prefix='/users', tags=['users'])


@users_router.get(
    '',
    response_model=PaginatedResponse[UserPublic],
    status_code=status.HTTP_200_OK,
    summary='List users',
    description='Get paginated list of users. Requires user.list permission.',
)
async def list_users(
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('user.list'))],
    active_only: Annotated[
        bool, Query(description='Filter for active users only')
    ] = False,
    limit: Annotated[
        int, Query(ge=1, le=100, description='Maximum number of results')
    ] = 50,
    offset: Annotated[int, Query(ge=0, description='Number of results to skip')] = 0,
) -> PaginatedResponse[UserPublic]:
    """
    List users with pagination and metadata.

    **Query parameters:**
    - active_only: If true, return only active users (default: false)
    - limit: Maximum number of users to return (1-100, default: 50)
    - offset: Number of users to skip for pagination (default: 0)


    **Permissions required:** user.list
    """
    service = UserService(db)

    items = await service.list_users(
        active_only=active_only, limit=limit, offset=offset
    )
    total = await service.count_users(active_only=active_only)

    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )  # type: ignore


@users_router.get(
    '/with-roles',
    response_model=PaginatedResponse[UserWithRoles],
    status_code=status.HTTP_200_OK,
    summary='List users with roles',
    description='Get paginated list of users with their assigned roles. Requires user.list permission.',
)
async def list_users_with_roles(
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('user.list'))],
    active_only: Annotated[
        bool, Query(description='Filter for active users only')
    ] = False,
    limit: Annotated[
        int, Query(ge=1, le=100, description='Maximum number of results')
    ] = 50,
    offset: Annotated[int, Query(ge=0, description='Number of results to skip')] = 0,
) -> PaginatedResponse[UserWithRoles]:
    """
    List users with their assigned roles (pagination enabled).

    This endpoint is optimized for frontend consumption, providing users
    with their roles included in a single request.

    **Query parameters:**
    - active_only: If true, return only active users (default: false)
    - limit: Maximum number of users to return (1-100, default: 50)
    - offset: Number of users to skip for pagination (default: 0)

    **Permissions required:** user.list
    """
    service = UserService(db)

    items = await service.list_users_with_roles(
        active_only=active_only, limit=limit, offset=offset
    )
    total = await service.count_users(active_only=active_only)

    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )  # type: ignore


@users_router.post(
    '',
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary='Create user',
    description='Create a new user. Requires user.create permission.',
)
async def create_user(
    data: UserCreate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('user.create'))],
) -> User:
    """
    Create a new user.

    **Required fields:**
    - full_name: User's full name
    - email: Unique email address
    - password: Strong password (min 8 chars, must include uppercase, lowercase, digit, special char)

    **Optional fields:**
    - phone: Phone number

    **Permissions required:** user.create
    """
    service = UserService(db)
    return await service.create_user(data, created_by=current_user.id)


@auth_router.post(
    '/register',
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary='Public user registration',
    description='Register a new user without authentication. User gets basic "user" role. Optionally accepts invitation token.',
)
async def register_user(
    data: UserCreate,
    db: SessionDep,
    invitation_token: Annotated[
        str | None, Query(description='Optional invitation token')
    ] = None,
) -> UserPublic:
    """
    Public endpoint for user self-registration.

    Creates a new user with the default 'user' role.
    No authentication required.

    **Required fields:**
    - full_name: User's full name
    - email: Unique email address
    - password: Strong password

    **Optional query parameters:**
    - invitation_token: If provided, validates the token and verifies email matches

    **Registration flow with invitation:**
    1. User receives invitation email with token
    2. Frontend calls GET /invitations/validate/{token} to get email
    3. Frontend pre-fills email (readonly) in registration form
    4. User completes registration with invitation_token query param
    5. Backend validates token, creates user, invalidates token
    6. Admin assigns roles via POST /users/{id}/roles/{role_id}

    **Note:** This endpoint does not require authentication.
    """
    from sqlmodel import select

    from app.core.exceptions import InvalidTokenException
    from app.invitations.service import InvitationService

    service = UserService(db)

    # If invitation token provided, validate it
    if invitation_token:
        invitation_service = InvitationService(db)

        # Get email from invitation
        invitation_email = await invitation_service.get_invitation_email(
            invitation_token
        )

        # Verify email matches
        if invitation_email != data.email:
            raise InvalidTokenException(
                'Email does not match the invitation. Please use the email address that received the invitation.'
            )

    # Create user
    user = await service.create_user(data, created_by=None)

    # Assign default 'user' role
    statement = select(Role).where(Role.name == 'user')
    result = await db.exec(statement)
    user_role = result.first()

    if user_role:
        # Create UserRole link directly to avoid lazy-load issues
        user_role_link = UserRole(
            user_id=user.id, role_id=user_role.id, assigned_by=None
        )
        db.add(user_role_link)
        await db.commit()
        await db.refresh(user)

    # If invitation token was used, invalidate it
    if invitation_token:
        invitation_service = InvitationService(db)
        await invitation_service.invalidate_invitation(invitation_token)

    return UserPublic.model_validate(user)


@users_router.get(
    '/me',
    response_model=UserWithRoles,
    status_code=status.HTTP_200_OK,
    summary='Get current user',
    description='Get information about the currently authenticated user.',
)
async def get_current_user_info(
    current_user: CurrentActiveUser,
    db: SessionDep,
) -> User:
    """
    Get current authenticated user with their roles.

    Returns the user information for the currently authenticated user,
    including all assigned roles.

    **Authentication required:** Yes (any authenticated user)
    """
    service = UserService(db)
    return await service.get_user_with_roles(current_user.id)  # type: ignore


@users_router.get(
    '/me/permissions',
    response_model=list[str],
    status_code=status.HTTP_200_OK,
    summary='Get current user permissions',
    description='Get all permission codes for the currently authenticated user.',
)
async def get_current_user_permissions(
    current_user: CurrentActiveUser,
    db: SessionDep,
) -> list[str]:
    """
    Get all permission codes for the currently authenticated user.

    Returns a list of permission codes that the user has through their assigned roles.
    This endpoint is essential for Angular frontend to implement:
    - Route guards based on permissions
    - Conditional UI element visibility
    - Role-based feature access

    **Example response:**
    ```json
    [
        "user.list",
        "user.view",
        "session.create",
        "session.view",
        "session.edit",
        "client.list",
        "client.view"
    ]
    ```

    **Authentication required:** Yes (any authenticated user)

    **Frontend usage example (Angular):**
    ```typescript
    // In AuthService
    async loadUserPermissions(): Promise<string[]> {
      return this.http.get<string[]>('/users/me/permissions').toPromise();
    }

    // In Route Guard
    canActivate(route: ActivatedRouteSnapshot): boolean {
      const requiredPermission = route.data['permission'];
      return this.authService.hasPermission(requiredPermission);
    }
    ```
    """
    service = UserService(db)
    return await service.get_user_permissions(current_user.id)  # type: ignore


@users_router.get(
    '/{user_id}',
    response_model=UserWithRoles,
    status_code=status.HTTP_200_OK,
    summary='Get user by ID',
    description='Get user information by ID with roles. Requires user.read permission.',
)
async def get_user(
    user_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('user.list'))],
) -> User:
    """
    Get user by ID with their roles.

    **Path parameters:**
    - user_id: User ID to retrieve

    **Permissions required:** user.read
    """
    service = UserService(db)
    return await service.get_user_with_roles(user_id)


@users_router.patch(
    '/{user_id}',
    response_model=UserPublic,
    status_code=status.HTTP_200_OK,
    summary='Update user',
    description='Update user information. Requires user.edit permission.',
)
async def update_user(
    user_id: Annotated[int, Field(gt=0)],
    data: UserUpdate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('user.edit'))],
) -> User:
    """
    Update user information.

    **Path parameters:**
    - user_id: User ID to update

    **Optional fields (all):**
    - full_name: Updated full name
    - email: Updated email (must be unique)
    - phone: Updated phone number
    - status: Updated status (ACTIVE/INACTIVE)

    **Note:** Cannot update password through this endpoint. Use PATCH /users/{id}/password instead.

    **Permissions required:** user.edit
    """
    service = UserService(db)
    return await service.update_user(user_id, data, updated_by=current_user.id)  # type: ignore


@users_router.delete(
    '/{user_id}',
    status_code=status.HTTP_200_OK,
    response_model=UserPublic,
    summary='Deactivate user',
    description='Deactivate (soft delete) a user. Requires user.delete permission.',
)
async def deactivate_user(
    user_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('user.delete'))],
) -> User:
    """
    Deactivate a user (soft delete).

    Sets user status to INACTIVE. User can be reactivated later.
    Cannot deactivate yourself.

    **Path parameters:**
    - user_id: User ID to deactivate

    **Permissions required:** user.delete
    """
    service = UserService(db)
    return await service.deactivate_user(user_id, deactivated_by=current_user.id)  # type: ignore


@users_router.put(
    '/{user_id}/reactivate',
    response_model=UserPublic,
    status_code=status.HTTP_200_OK,
    summary='Reactivate user',
    description='Reactivate a deactivated user. Requires user.edit permission.',
)
async def reactivate_user(
    user_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('user.edit'))],
) -> User:
    """
    Reactivate a deactivated user.

    Sets user status back to ACTIVE.

    **Path parameters:**
    - user_id: User ID to reactivate

    **Permissions required:** user.edit
    """
    service = UserService(db)
    return await service.reactivate_user(user_id, reactivated_by=current_user.id)  # type: ignore


@users_router.patch(
    '/{user_id}/password',
    response_model=UserPublic,
    status_code=status.HTTP_200_OK,
    summary='Change password',
    description='Change user password. Users can change their own password, or admins can change any password.',
)
async def change_password(
    user_id: Annotated[int, Field(gt=0)],
    data: UserPasswordUpdate,
    db: SessionDep,
    current_user: CurrentActiveUser,
) -> User:
    """
    Change user password.

    Users can change their own password by providing current password.
    Admins with user.edit permission can change any user's password.

    **Path parameters:**
    - user_id: User ID to change password for

    **Required fields:**
    - current_password: Current password for verification
    - new_password: New password (must meet strength requirements)

    **Authorization:**
    - Own password: Any authenticated user can change their own password
    - Other users: Requires user.edit permission
    """
    service = UserService(db)

    # Check if user is changing their own password or has permission
    is_self = current_user.id == user_id

    if not is_self:
        # Check if user has user.edit permission
        from app.core.permissions import check_user_permission

        has_permission = await check_user_permission(current_user, 'user.edit', db)
        if not has_permission:
            from app.core.exceptions import InsufficientPermissionsException

            raise InsufficientPermissionsException()

    return await service.update_password(user_id, data)


# ==================== User Roles Router ====================

user_roles_router = APIRouter(prefix='/users', tags=['user-roles'])


@user_roles_router.get(
    '/{user_id}/roles',
    response_model=list[RolePublic],
    status_code=status.HTTP_200_OK,
    summary='List user roles',
    description='Get all roles assigned to a user.',
)
async def list_user_roles(
    user_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: CurrentActiveUser,
) -> list:
    """
    List all roles assigned to a user.

    **Path parameters:**
    - user_id: User ID to list roles for

    **Authorization:**
    - Own roles: Any authenticated user can view their own roles
    - Other users: Requires user.view permission
    """
    # Check if user is viewing their own roles or has permission
    is_self = current_user.id == user_id

    if not is_self:
        from app.core.permissions import check_user_permission

        has_permission = await check_user_permission(current_user, 'user.view', db)
        if not has_permission:
            from app.core.exceptions import InsufficientPermissionsException

            raise InsufficientPermissionsException()

    service = UserService(db)
    user = await service.get_user_with_roles(user_id)
    return user.roles


@user_roles_router.post(
    '/{user_id}/roles/{role_id}',
    response_model=UserWithRoles,
    status_code=status.HTTP_200_OK,
    summary='Assign role to user',
    description='Assign a role to a user. Requires role.assign permission.',
)
async def assign_role(
    user_id: Annotated[int, Field(gt=0)],
    role_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('role.assign'))],
) -> User:
    """
    Assign a role to a user.

    **Path parameters:**
    - user_id: User ID to assign role to
    - role_id: Role ID to assign

    **Business rules:**
    - User must exist and be active
    - Role must exist and be active
    - Cannot assign duplicate role

    **Permissions required:** role.assign
    """
    service = UserService(db)
    return await service.assign_role_to_user(
        user_id,
        role_id,
        assigned_by=current_user.id,  # type: ignore
    )


@user_roles_router.delete(
    '/{user_id}/roles/{role_id}',
    response_model=UserWithRoles,
    status_code=status.HTTP_200_OK,
    summary='Remove role from user',
    description='Remove a role from a user. Requires role.assign permission.',
)
async def remove_role(
    user_id: Annotated[int, Field(gt=0)],
    role_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('role.assign'))],
) -> User:
    """
    Remove a role from a user.

    **Path parameters:**
    - user_id: User ID to remove role from
    - role_id: Role ID to remove

    **Permissions required:** role.assign
    """
    service = UserService(db)
    return await service.remove_role_from_user(
        user_id,
        role_id,
        removed_by=current_user.id,  # type: ignore
    )


# ==================== Roles Router ====================

roles_router = APIRouter(prefix='/roles', tags=['roles'])


@roles_router.get(
    '',
    response_model=PaginatedResponse[RolePublic],
    status_code=status.HTTP_200_OK,
    summary='List roles',
    description='Get paginated list of roles. Requires role.list permission.',
)
async def list_roles(
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('role.list'))],
    active_only: Annotated[
        bool, Query(description='Filter for active roles only')
    ] = False,
    limit: Annotated[
        int, Query(ge=1, le=100, description='Maximum number of results')
    ] = 50,
    offset: Annotated[int, Query(ge=0, description='Number of results to skip')] = 0,
) -> PaginatedResponse[RolePublic]:
    """
    List roles with pagination and metadata.

    **Query parameters:**
    - active_only: If true, return only active roles (default: false)
    - limit: Maximum number of roles to return (1-100, default: 50)
    - offset: Number of roles to skip for pagination (default: 0)

    **Permissions required:** role.list
    """
    service = RoleService(db)

    items = await service.list_roles(
        active_only=active_only, limit=limit, offset=offset
    )
    total = await service.count_roles(active_only=active_only)

    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )  # type: ignore


@roles_router.post(
    '',
    response_model=RolePublic,
    status_code=status.HTTP_201_CREATED,
    summary='Create role',
    description='Create a new role. Requires role.create permission.',
)
async def create_role(
    data: RoleCreate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('role.create'))],
) -> RolePublic:
    """
    Create a new role.

    **Required fields:**
    - name: Unique role name

    **Optional fields:**
    - description: Role description

    **Permissions required:** role.create
    """
    service = RoleService(db)
    role = await service.create_role(data)
    return RolePublic.model_validate(role)


@roles_router.get(
    '/{role_id}',
    response_model=RoleWithPermissions,
    status_code=status.HTTP_200_OK,
    summary='Get role by ID',
    description='Get role information by ID with permissions. Requires role.read permission.',
)
async def get_role(
    role_id: Annotated[int, Field(gt=0)],
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('role.read'))],
) -> RoleWithPermissions:
    """
    Get role by ID with associated permissions.

    **Path parameters:**
    - role_id: Role ID to retrieve

    **Permissions required:** role.read
    """
    service = RoleService(db)
    role = await service.get_role_with_permissions(role_id)
    return RoleWithPermissions.model_validate(role)


@roles_router.patch(
    '/{role_id}',
    response_model=RolePublic,
    status_code=status.HTTP_200_OK,
    summary='Update role',
    description='Update role information. Requires role.edit permission.',
)
async def update_role(
    role_id: Annotated[int, Field(gt=0)],
    data: RoleUpdate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('role.edit'))],
) -> RolePublic:
    """
    Update role information.

    **Path parameters:**
    - role_id: Role ID to update

    **Optional fields (all):**
    - name: Updated role name (must be unique)
    - description: Updated description
    - status: Updated status (ACTIVE/INACTIVE)

    **Permissions required:** role.edit
    """
    service = RoleService(db)
    role = await service.update_role(role_id, data)
    return RolePublic.model_validate(role)


# ==================== Permissions Router ====================

permissions_router = APIRouter(prefix='/permissions', tags=['permissions'])


@permissions_router.get(
    '',
    response_model=PaginatedResponse[PermissionPublic],
    status_code=status.HTTP_200_OK,
    summary='List permissions',
    description='Get paginated list of permissions. Requires permission.list permission.',
)
async def list_permissions(
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('permission.list'))],
    module: Annotated[str | None, Query(description='Filter by module')] = None,
    active_only: Annotated[
        bool, Query(description='Filter for active permissions only')
    ] = False,
    limit: Annotated[
        int, Query(ge=1, le=100, description='Maximum number of results')
    ] = 100,
    offset: Annotated[int, Query(ge=0, description='Number of results to skip')] = 0,
) -> PaginatedResponse[PermissionPublic]:
    """
    List permissions with optional filtering and pagination metadata.

    **Query parameters:**
    - module: Filter permissions by module (e.g., 'user', 'session', 'client')
    - active_only: If true, return only active permissions (default: false)
    - limit: Maximum number of permissions to return (1-100, default: 100)
    - offset: Number of permissions to skip for pagination (default: 0)

    **Permissions required:** permission.list
    """
    service = PermissionService(db)

    items = await service.list_permissions(
        module=module, active_only=active_only, limit=limit, offset=offset
    )
    total = await service.count_permissions(module=module, active_only=active_only)

    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )  # type: ignore


@permissions_router.post(
    '',
    response_model=PermissionPublic,
    status_code=status.HTTP_201_CREATED,
    summary='Create permission',
    description='Create a new permission. Requires permission.create permission.',
)
async def create_permission(
    data: PermissionCreate,
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('permission.create'))],
) -> PermissionPublic:
    """
    Create a new permission.

    **Required fields:**
    - code: Unique permission code (format: module.action[.scope], e.g., 'user.create')
    - name: Human-readable permission name
    - module: Module this permission belongs to

    **Optional fields:**
    - description: Permission description

    **Permissions required:** permission.create
    """
    service = PermissionService(db)
    permission = await service.create_permission(data)
    return PermissionPublic.model_validate(permission)


@permissions_router.get(
    '/by-module',
    response_model=dict[str, list[PermissionPublic]],
    status_code=status.HTTP_200_OK,
    summary='List permissions grouped by module',
    description='Get all permissions grouped by module. Requires permission.list permission.',
)
async def list_permissions_by_module(
    db: SessionDep,
    current_user: Annotated[User, Depends(require_permission('permission.list'))],
    active_only: Annotated[
        bool, Query(description='Filter for active permissions only')
    ] = True,
) -> dict[str, list[PermissionPublic]]:
    """
    List all permissions grouped by module.

    Returns a dictionary where keys are module names and values are
    lists of permissions for that module.

    **Query parameters:**
    - active_only: If true, return only active permissions (default: true)

    **Example response:**
    ```json
    {
        "user": [
            {"code": "user.create", "name": "Create User", ...},
            {"code": "user.read", "name": "Read User", ...}
        ],
        "session": [
            {"code": "session.create", "name": "Create Session", ...}
        ]
    }
    ```

    **Permissions required:** permission.list
    """
    service = PermissionService(db)
    permissions = await service.list_permissions(active_only=active_only, limit=1000)

    # Group by module
    grouped: dict[str, list[PermissionPublic]] = {}
    for perm in permissions:
        module = perm.module
        if module not in grouped:
            grouped[module] = []
        grouped[module].append(PermissionPublic.model_validate(perm))

    return grouped


# ==================== Main Router for Export ====================

# Combine all routers
router = APIRouter()
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(user_roles_router)
router.include_router(roles_router)
router.include_router(permissions_router)
