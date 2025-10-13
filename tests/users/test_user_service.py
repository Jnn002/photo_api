"""
Tests for UserService business logic.

This module tests all user management operations including:
- Authentication with JWT tokens
- User CRUD operations
- Password management
- Role assignment and removal
- User activation/deactivation
- Business rule validation
"""

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.enums import Status
from app.core.exceptions import (
    BusinessValidationException,
    DuplicateEmailException,
    InactiveUserException,
    InvalidCredentialsException,
    RoleNotFoundException,
    UserNotFoundException,
)
from app.core.security import verify_password
from app.users.models import Role, User
from app.users.schemas import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserPasswordUpdate,
    UserUpdate,
)
from app.users.service import UserService


# ==================== Authentication Tests ====================


class TestAuthentication:
    """Test user authentication."""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test successful user authentication."""
        service = UserService(db_session)
        credentials = UserLogin(email=test_user.email, password='TestPass123!')

        result = await service.authenticate_user(credentials)

        assert isinstance(result, TokenResponse)
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.token_type == 'bearer'
        assert result.expires_in == 30 * 60  # 30 minutes
        assert result.user.email == test_user.email

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_email(self, db_session: AsyncSession):
        """Test authentication fails with non-existent email."""
        service = UserService(db_session)
        credentials = UserLogin(
            email='nonexistent@example.com', password='TestPass123!'
        )

        with pytest.raises(InvalidCredentialsException) as exc_info:
            await service.authenticate_user(credentials)

        assert 'Invalid email or password' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test authentication fails with incorrect password."""
        service = UserService(db_session)
        credentials = UserLogin(email=test_user.email, password='WrongPassword123!')

        with pytest.raises(InvalidCredentialsException) as exc_info:
            await service.authenticate_user(credentials)

        assert 'Invalid email or password' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(
        self, db_session: AsyncSession, inactive_user: User
    ):
        """Test authentication fails for inactive user."""
        service = UserService(db_session)
        credentials = UserLogin(
            email=inactive_user.email, password='InactivePass123!'
        )

        with pytest.raises(InactiveUserException) as exc_info:
            await service.authenticate_user(credentials)

        assert 'inactive' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_authenticate_returns_both_tokens(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test that authentication returns both access and refresh tokens."""
        service = UserService(db_session)
        credentials = UserLogin(email=test_user.email, password='TestPass123!')

        result = await service.authenticate_user(credentials)

        # Tokens should be different
        assert result.access_token != result.refresh_token
        # Both should be non-empty strings
        assert len(result.access_token) > 0
        assert len(result.refresh_token) > 0


# ==================== User Creation Tests ====================


class TestCreateUser:
    """Test user creation."""

    @pytest.mark.asyncio
    async def test_create_user_success(self, db_session: AsyncSession):
        """Test successful user creation."""
        service = UserService(db_session)
        data = UserCreate(
            full_name='New User',
            email='newuser@example.com',
            password='NewPass123!',
            phone='+502 9999-9999',
        )

        user = await service.create_user(data)

        assert user.id is not None
        assert user.full_name == 'New User'
        assert user.email == 'newuser@example.com'
        assert user.phone == '+502 9999-9999'
        assert user.status == Status.ACTIVE
        # Password should be hashed
        assert user.password_hash != 'NewPass123!'
        assert verify_password('NewPass123!', user.password_hash)

    @pytest.mark.asyncio
    async def test_create_user_with_duplicate_email(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test that creating user with duplicate email raises exception."""
        service = UserService(db_session)
        data = UserCreate(
            full_name='Duplicate User',
            email=test_user.email,  # Duplicate email
            password='DuplicatePass123!',
        )

        with pytest.raises(DuplicateEmailException) as exc_info:
            await service.create_user(data)

        assert test_user.email in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_user_with_created_by(
        self, db_session: AsyncSession, admin_user: User
    ):
        """Test creating user with created_by field."""
        service = UserService(db_session)
        data = UserCreate(
            full_name='Created User',
            email='created@example.com',
            password='CreatedPass123!',
        )

        user = await service.create_user(data, created_by=admin_user.id)

        assert user.created_by == admin_user.id

    @pytest.mark.asyncio
    async def test_create_user_password_is_hashed(self, db_session: AsyncSession):
        """Test that user password is properly hashed."""
        service = UserService(db_session)
        plain_password = 'PlainPass123!'
        data = UserCreate(
            full_name='Hash Test User',
            email='hashtest@example.com',
            password=plain_password,
        )

        user = await service.create_user(data)

        # Password should be hashed (not stored as plain text)
        assert user.password_hash != plain_password
        # Hash should start with bcrypt identifier
        assert user.password_hash.startswith('$2b$')
        # Should verify correctly
        assert verify_password(plain_password, user.password_hash)


# ==================== User Retrieval Tests ====================


class TestGetUser:
    """Test user retrieval operations."""

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test getting user by ID."""
        service = UserService(db_session)

        user = await service.get_user_by_id(test_user.id)  # type: ignore

        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, db_session: AsyncSession):
        """Test getting non-existent user raises exception."""
        service = UserService(db_session)

        with pytest.raises(UserNotFoundException) as exc_info:
            await service.get_user_by_id(99999)

        assert '99999' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_user_with_roles(
        self, db_session: AsyncSession, admin_user: User
    ):
        """Test getting user with roles eagerly loaded."""
        service = UserService(db_session)

        user = await service.get_user_with_roles(admin_user.id)  # type: ignore

        assert user is not None
        assert user.id == admin_user.id
        # Roles should be loaded
        assert hasattr(user, 'roles')
        assert len(user.roles) > 0

    @pytest.mark.asyncio
    async def test_get_user_with_roles_not_found(self, db_session: AsyncSession):
        """Test getting user with roles for non-existent user."""
        service = UserService(db_session)

        with pytest.raises(UserNotFoundException):
            await service.get_user_with_roles(99999)


# ==================== User Update Tests ====================


class TestUpdateUser:
    """Test user update operations."""

    @pytest.mark.asyncio
    async def test_update_user_success(
        self, db_session: AsyncSession, test_user: User, admin_user: User
    ):
        """Test successful user update."""
        service = UserService(db_session)
        data = UserUpdate(
            full_name='Updated Name',
            phone='+502 8888-8888',
        )

        user = await service.update_user(
            test_user.id, data, updated_by=admin_user.id  # type: ignore
        )

        assert user.full_name == 'Updated Name'
        assert user.phone == '+502 8888-8888'
        # Email should remain unchanged
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_update_user_email(
        self, db_session: AsyncSession, test_user: User, admin_user: User
    ):
        """Test updating user email."""
        service = UserService(db_session)
        data = UserUpdate(email='newemail@example.com')

        user = await service.update_user(
            test_user.id, data, updated_by=admin_user.id  # type: ignore
        )

        assert user.email == 'newemail@example.com'

    @pytest.mark.asyncio
    async def test_update_user_duplicate_email(
        self, db_session: AsyncSession, test_user: User, admin_user: User
    ):
        """Test updating user to duplicate email fails."""
        service = UserService(db_session)
        data = UserUpdate(email=admin_user.email)  # Use admin's email

        with pytest.raises(DuplicateEmailException):
            await service.update_user(test_user.id, data, updated_by=admin_user.id)  # type: ignore

    @pytest.mark.asyncio
    async def test_update_user_not_found(
        self, db_session: AsyncSession, admin_user: User
    ):
        """Test updating non-existent user raises exception."""
        service = UserService(db_session)
        data = UserUpdate(full_name='Should Fail')

        with pytest.raises(UserNotFoundException):
            await service.update_user(99999, data, updated_by=admin_user.id)  # type: ignore


# ==================== Password Update Tests ====================


class TestUpdatePassword:
    """Test password update operations."""

    @pytest.mark.asyncio
    async def test_update_password_success(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test successful password update."""
        service = UserService(db_session)
        data = UserPasswordUpdate(
            current_password='TestPass123!',
            new_password='NewSecurePass456!',
        )

        user = await service.update_password(test_user.id, data)  # type: ignore

        # New password should verify
        assert verify_password('NewSecurePass456!', user.password_hash)
        # Old password should not verify
        assert not verify_password('TestPass123!', user.password_hash)

    @pytest.mark.asyncio
    async def test_update_password_wrong_current_password(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test password update fails with wrong current password."""
        service = UserService(db_session)
        data = UserPasswordUpdate(
            current_password='WrongPassword123!',
            new_password='NewSecurePass456!',
        )

        with pytest.raises(InvalidCredentialsException) as exc_info:
            await service.update_password(test_user.id, data)  # type: ignore

        assert 'Current password is incorrect' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_password_same_as_current(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test password update fails if new password is same as current."""
        service = UserService(db_session)
        data = UserPasswordUpdate(
            current_password='TestPass123!',
            new_password='TestPass123!',  # Same as current
        )

        with pytest.raises(BusinessValidationException) as exc_info:
            await service.update_password(test_user.id, data)  # type: ignore

        assert 'must be different' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_update_password_user_not_found(self, db_session: AsyncSession):
        """Test password update for non-existent user."""
        service = UserService(db_session)
        data = UserPasswordUpdate(
            current_password='TestPass123!',
            new_password='NewPass456!',
        )

        with pytest.raises(UserNotFoundException):
            await service.update_password(99999, data)


# ==================== User Deactivation Tests ====================


class TestDeactivateUser:
    """Test user deactivation (soft delete)."""

    @pytest.mark.asyncio
    async def test_deactivate_user_success(
        self, db_session: AsyncSession, test_user: User, admin_user: User
    ):
        """Test successful user deactivation."""
        service = UserService(db_session)

        user = await service.deactivate_user(
            test_user.id, deactivated_by=admin_user.id  # type: ignore
        )

        assert user.status == Status.INACTIVE

    @pytest.mark.asyncio
    async def test_cannot_deactivate_self(
        self, db_session: AsyncSession, test_user: User
    ):
        """Test that user cannot deactivate themselves."""
        service = UserService(db_session)

        with pytest.raises(BusinessValidationException) as exc_info:
            await service.deactivate_user(
                test_user.id, deactivated_by=test_user.id  # type: ignore
            )

        assert 'Cannot deactivate yourself' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_deactivate_user_not_found(
        self, db_session: AsyncSession, admin_user: User
    ):
        """Test deactivating non-existent user."""
        service = UserService(db_session)

        with pytest.raises(UserNotFoundException):
            await service.deactivate_user(99999, deactivated_by=admin_user.id)  # type: ignore


# ==================== User Reactivation Tests ====================


class TestReactivateUser:
    """Test user reactivation."""

    @pytest.mark.asyncio
    async def test_reactivate_user_success(
        self, db_session: AsyncSession, inactive_user: User, admin_user: User
    ):
        """Test successful user reactivation."""
        service = UserService(db_session)

        user = await service.reactivate_user(
            inactive_user.id, reactivated_by=admin_user.id  # type: ignore
        )

        assert user.status == Status.ACTIVE

    @pytest.mark.asyncio
    async def test_reactivate_user_not_found(
        self, db_session: AsyncSession, admin_user: User
    ):
        """Test reactivating non-existent user."""
        service = UserService(db_session)

        with pytest.raises(UserNotFoundException):
            await service.reactivate_user(99999, reactivated_by=admin_user.id)  # type: ignore


# ==================== Role Assignment Tests ====================


class TestAssignRole:
    """Test role assignment to users."""

    @pytest.mark.asyncio
    async def test_assign_role_success(
        self, db_session: AsyncSession, test_user: User, test_role: Role, admin_user: User
    ):
        """Test successful role assignment."""
        service = UserService(db_session)

        user = await service.assign_role_to_user(
            test_user.id, test_role.id, assigned_by=admin_user.id  # type: ignore
        )

        # User should have the role
        assert any(role.id == test_role.id for role in user.roles)

    @pytest.mark.asyncio
    async def test_assign_role_user_not_found(
        self, db_session: AsyncSession, test_role: Role, admin_user: User
    ):
        """Test assigning role to non-existent user."""
        service = UserService(db_session)

        with pytest.raises(UserNotFoundException):
            await service.assign_role_to_user(
                99999, test_role.id, assigned_by=admin_user.id  # type: ignore
            )

    @pytest.mark.asyncio
    async def test_assign_role_role_not_found(
        self, db_session: AsyncSession, test_user: User, admin_user: User
    ):
        """Test assigning non-existent role to user."""
        service = UserService(db_session)

        with pytest.raises(RoleNotFoundException):
            await service.assign_role_to_user(
                test_user.id, 99999, assigned_by=admin_user.id  # type: ignore
            )

    @pytest.mark.asyncio
    async def test_assign_role_to_inactive_user(
        self, db_session: AsyncSession, inactive_user: User, test_role: Role, admin_user: User
    ):
        """Test assigning role to inactive user fails."""
        service = UserService(db_session)

        with pytest.raises(InactiveUserException):
            await service.assign_role_to_user(
                inactive_user.id, test_role.id, assigned_by=admin_user.id  # type: ignore
            )

    @pytest.mark.asyncio
    async def test_assign_inactive_role(
        self, db_session: AsyncSession, test_user: User, admin_user: User, create_test_role
    ):
        """Test assigning inactive role fails."""
        inactive_role = await create_test_role(
            name='InactiveRole', status=Status.INACTIVE
        )
        service = UserService(db_session)

        with pytest.raises(BusinessValidationException) as exc_info:
            await service.assign_role_to_user(
                test_user.id, inactive_role.id, assigned_by=admin_user.id  # type: ignore
            )

        assert 'inactive' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_assign_duplicate_role(
        self, db_session: AsyncSession, admin_user: User, admin_role: Role
    ):
        """Test assigning duplicate role fails."""
        service = UserService(db_session)

        # Admin user already has admin role
        with pytest.raises(BusinessValidationException) as exc_info:
            await service.assign_role_to_user(
                admin_user.id, admin_role.id, assigned_by=admin_user.id  # type: ignore
            )

        assert 'already has role' in str(exc_info.value).lower()


# ==================== Role Removal Tests ====================


class TestRemoveRole:
    """Test role removal from users."""

    @pytest.mark.asyncio
    async def test_remove_role_success(
        self, db_session: AsyncSession, admin_user: User, admin_role: Role
    ):
        """Test successful role removal."""
        service = UserService(db_session)

        user = await service.remove_role_from_user(
            admin_user.id, admin_role.id, removed_by=admin_user.id  # type: ignore
        )

        # User should not have the role anymore
        assert not any(role.id == admin_role.id for role in user.roles)

    @pytest.mark.asyncio
    async def test_remove_role_user_not_found(
        self, db_session: AsyncSession, test_role: Role, admin_user: User
    ):
        """Test removing role from non-existent user."""
        service = UserService(db_session)

        with pytest.raises(UserNotFoundException):
            await service.remove_role_from_user(
                99999, test_role.id, removed_by=admin_user.id  # type: ignore
            )

    @pytest.mark.asyncio
    async def test_remove_role_role_not_found(
        self, db_session: AsyncSession, test_user: User, admin_user: User
    ):
        """Test removing non-existent role from user."""
        service = UserService(db_session)

        with pytest.raises(RoleNotFoundException):
            await service.remove_role_from_user(
                test_user.id, 99999, removed_by=admin_user.id  # type: ignore
            )


# ==================== User Listing Tests ====================


class TestListUsers:
    """Test user listing operations."""

    @pytest.mark.asyncio
    async def test_list_all_users(
        self, db_session: AsyncSession, create_multiple_users
    ):
        """Test listing all users with pagination."""
        await create_multiple_users(count=5)
        service = UserService(db_session)

        users = await service.list_users(limit=10, offset=0)

        assert len(users) >= 5

    @pytest.mark.asyncio
    async def test_list_active_users_only(
        self, db_session: AsyncSession, test_user: User, inactive_user: User
    ):
        """Test listing only active users."""
        service = UserService(db_session)

        users = await service.list_users(active_only=True)

        # Should include active user
        assert any(u.id == test_user.id for u in users)
        # Should not include inactive user
        assert not any(u.id == inactive_user.id for u in users)

    @pytest.mark.asyncio
    async def test_list_users_pagination(
        self, db_session: AsyncSession, create_multiple_users
    ):
        """Test user listing with pagination."""
        await create_multiple_users(count=10, email_prefix='paginated')
        service = UserService(db_session)

        # Get first page
        page1 = await service.list_users(limit=5, offset=0)
        # Get second page
        page2 = await service.list_users(limit=5, offset=5)

        assert len(page1) == 5
        assert len(page2) >= 5
        # Pages should have different users
        page1_ids = {u.id for u in page1}
        page2_ids = {u.id for u in page2}
        assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_list_users_by_role(
        self, db_session: AsyncSession, admin_user: User, coordinator_user: User
    ):
        """Test listing users by role."""
        service = UserService(db_session)

        admins = await service.list_users_by_role('Admin')

        # Should include admin user
        assert any(u.id == admin_user.id for u in admins)
        # Should not include coordinator
        assert not any(u.id == coordinator_user.id for u in admins)
