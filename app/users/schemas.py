"""
User schemas for request/response DTOs.

This module defines Pydantic v2 schemas for user operations:
- User schemas: System users with authentication
- Role schemas: User roles (Admin, Coordinator, Photographer, Editor)
- Permission schemas: Granular permissions
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# ==================== Permission Schemas ====================


class PermissionCreate(BaseModel):
    """Schema for creating a new permission."""

    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    module: str = Field(..., min_length=1, max_length=50)

    @field_validator('code', 'name', 'module')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure required fields are not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip()

    @field_validator('code')
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        """Ensure permission code follows pattern: module.action[.scope]."""
        parts = v.split('.')
        if len(parts) < 2:
            raise ValueError(
                'Permission code must follow pattern: module.action[.scope]'
            )
        return v


class PermissionUpdate(BaseModel):
    """Schema for updating an existing permission (all fields optional)."""

    code: str | None = Field(default=None, min_length=1, max_length=100)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    module: str | None = Field(default=None, min_length=1, max_length=50)
    status: str | None = Field(default=None, pattern='^(Active|Inactive)$')

    @field_validator('code', 'name', 'module')
    @classmethod
    def validate_not_empty(cls, v: str | None) -> str | None:
        """Ensure fields are not empty or whitespace if provided."""
        if v is not None and not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip() if v else None


class PermissionPublic(BaseModel):
    """Public permission response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None
    module: str
    status: str
    created_at: datetime
    updated_at: datetime


# ==================== Role Schemas ====================


class RoleCreate(BaseModel):
    """Schema for creating a new role."""

    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = None

    @field_validator('name')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure name is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip()


class RoleUpdate(BaseModel):
    """Schema for updating an existing role (all fields optional)."""

    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = None
    status: str | None = Field(default=None, pattern='^(Active|Inactive)$')

    @field_validator('name')
    @classmethod
    def validate_not_empty(cls, v: str | None) -> str | None:
        """Ensure name is not empty or whitespace if provided."""
        if v is not None and not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip() if v else None


class RolePublic(BaseModel):
    """Public role response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class RoleWithPermissions(RolePublic):
    """Role with associated permissions."""

    permissions: list[PermissionPublic] = []


# ==================== User Schemas ====================


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    full_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    phone: str | None = Field(default=None, max_length=20)

    @field_validator('full_name')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure full_name is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip()

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Ensure password meets minimum requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        # Check for at least one digit
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')

        # Check for at least one letter
        if not any(char.isalpha() for char in v):
            raise ValueError('Password must contain at least one letter')

        return v


class UserUpdate(BaseModel):
    """Schema for updating an existing user (all fields optional)."""

    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    status: str | None = Field(default=None, pattern='^(Active|Inactive)$')

    @field_validator('full_name')
    @classmethod
    def validate_not_empty(cls, v: str | None) -> str | None:
        """Ensure full_name is not empty or whitespace if provided."""
        if v is not None and not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip() if v else None


class UserPasswordUpdate(BaseModel):
    """Schema for updating user password."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Ensure password meets minimum requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')

        if not any(char.isalpha() for char in v):
            raise ValueError('Password must contain at least one letter')

        return v


class UserPublic(BaseModel):
    """Public user response schema (without password_hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    phone: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class UserWithRoles(UserPublic):
    """User with associated roles."""

    roles: list[RolePublic] = []


class UserDetail(UserWithRoles):
    """Detailed user information with roles and permissions."""

    # This will be populated via service layer logic
    # Permissions come from roles
    pass


# ==================== Assignment Schemas ====================


class UserRoleAssign(BaseModel):
    """Schema for assigning a role to a user."""

    user_id: int = Field(..., gt=0)
    role_id: int = Field(..., gt=0)

    @field_validator('user_id', 'role_id')
    @classmethod
    def validate_positive_id(cls, v: int) -> int:
        """Ensure IDs are positive."""
        if v <= 0:
            raise ValueError('ID must be greater than 0')
        return v


class RolePermissionAssign(BaseModel):
    """Schema for assigning a permission to a role."""

    role_id: int = Field(..., gt=0)
    permission_id: int = Field(..., gt=0)

    @field_validator('role_id', 'permission_id')
    @classmethod
    def validate_positive_id(cls, v: int) -> int:
        """Ensure IDs are positive."""
        if v <= 0:
            raise ValueError('ID must be greater than 0')
        return v


# ==================== Authentication Schemas ====================


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Response schema for successful authentication."""

    access_token: str
    token_type: str = 'bearer'
    expires_in: int  # seconds
    user: UserPublic
