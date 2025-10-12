"""
Tests for RoleService business logic.

This module tests role management operations including:
- Role CRUD operations
- Role validation
- Role retrieval with permissions
"""

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.enums import Status
from app.core.exceptions import DuplicateNameException, RoleNotFoundException
from app.users.models import Role
from app.users.schemas import RoleCreate, RoleUpdate
from app.users.service import RoleService


# ==================== Role Creation Tests ====================


class TestCreateRole:
    """Test role creation."""

    @pytest.mark.asyncio
    async def test_create_role_success(self, db_session: AsyncSession):
        """Test successful role creation."""
        service = RoleService(db_session)
        data = RoleCreate(
            name='New Role',
            description='A new test role',
        )

        role = await service.create_role(data)

        assert role.id is not None
        assert role.name == 'New Role'
        assert role.description == 'A new test role'
        assert role.status == Status.ACTIVE

    @pytest.mark.asyncio
    async def test_create_role_without_description(self, db_session: AsyncSession):
        """Test creating role without description."""
        service = RoleService(db_session)
        data = RoleCreate(name='Role Without Description')

        role = await service.create_role(data)

        assert role.name == 'Role Without Description'
        assert role.description is None

    @pytest.mark.asyncio
    async def test_create_role_duplicate_name(
        self, db_session: AsyncSession, test_role: Role
    ):
        """Test creating role with duplicate name fails."""
        service = RoleService(db_session)
        data = RoleCreate(
            name=test_role.name,  # Duplicate name
            description='Should fail',
        )

        with pytest.raises(DuplicateNameException) as exc_info:
            await service.create_role(data)

        assert test_role.name in str(exc_info.value)


# ==================== Role Retrieval Tests ====================


class TestGetRole:
    """Test role retrieval operations."""

    @pytest.mark.asyncio
    async def test_get_role_by_id_success(
        self, db_session: AsyncSession, test_role: Role
    ):
        """Test getting role by ID."""
        service = RoleService(db_session)

        role = await service.get_role_by_id(test_role.id)  # type: ignore

        assert role is not None
        assert role.id == test_role.id
        assert role.name == test_role.name

    @pytest.mark.asyncio
    async def test_get_role_by_id_not_found(self, db_session: AsyncSession):
        """Test getting non-existent role raises exception."""
        service = RoleService(db_session)

        with pytest.raises(RoleNotFoundException) as exc_info:
            await service.get_role_by_id(99999)

        assert '99999' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_role_with_permissions(
        self, db_session: AsyncSession, admin_role: Role, test_permission, assign_permission_to_role
    ):
        """Test getting role with permissions eagerly loaded."""
        # Assign permission to role
        await assign_permission_to_role(admin_role, test_permission)

        service = RoleService(db_session)

        role = await service.get_role_with_permissions(admin_role.id)  # type: ignore

        assert role is not None
        assert role.id == admin_role.id
        # Permissions should be loaded
        assert hasattr(role, 'permissions')
        assert len(role.permissions) > 0
        assert any(p.id == test_permission.id for p in role.permissions)

    @pytest.mark.asyncio
    async def test_get_role_with_permissions_not_found(self, db_session: AsyncSession):
        """Test getting role with permissions for non-existent role."""
        service = RoleService(db_session)

        with pytest.raises(RoleNotFoundException):
            await service.get_role_with_permissions(99999)


# ==================== Role Update Tests ====================


class TestUpdateRole:
    """Test role update operations."""

    @pytest.mark.asyncio
    async def test_update_role_name(self, db_session: AsyncSession, test_role: Role):
        """Test updating role name."""
        service = RoleService(db_session)
        data = RoleUpdate(name='Updated Role Name')

        role = await service.update_role(test_role.id, data)  # type: ignore

        assert role.name == 'Updated Role Name'
        # Description should remain unchanged
        assert role.description == test_role.description

    @pytest.mark.asyncio
    async def test_update_role_description(
        self, db_session: AsyncSession, test_role: Role
    ):
        """Test updating role description."""
        service = RoleService(db_session)
        data = RoleUpdate(description='Updated description')

        role = await service.update_role(test_role.id, data)  # type: ignore

        assert role.description == 'Updated description'
        # Name should remain unchanged
        assert role.name == test_role.name

    @pytest.mark.asyncio
    async def test_update_role_status(self, db_session: AsyncSession, test_role: Role):
        """Test updating role status."""
        service = RoleService(db_session)
        data = RoleUpdate(status=Status.INACTIVE)

        role = await service.update_role(test_role.id, data)  # type: ignore

        assert role.status == Status.INACTIVE

    @pytest.mark.asyncio
    async def test_update_role_duplicate_name(
        self, db_session: AsyncSession, test_role: Role, admin_role: Role
    ):
        """Test updating role to duplicate name fails."""
        service = RoleService(db_session)
        data = RoleUpdate(name=admin_role.name)  # Use admin role's name

        with pytest.raises(DuplicateNameException):
            await service.update_role(test_role.id, data)  # type: ignore

    @pytest.mark.asyncio
    async def test_update_role_not_found(self, db_session: AsyncSession):
        """Test updating non-existent role raises exception."""
        service = RoleService(db_session)
        data = RoleUpdate(name='Should Fail')

        with pytest.raises(RoleNotFoundException):
            await service.update_role(99999, data)

    @pytest.mark.asyncio
    async def test_update_role_partial_update(
        self, db_session: AsyncSession, test_role: Role
    ):
        """Test partial role update (only updating one field)."""
        service = RoleService(db_session)
        original_name = test_role.name
        original_description = test_role.description

        data = RoleUpdate(description='New description only')

        role = await service.update_role(test_role.id, data)  # type: ignore

        # Only description should change
        assert role.description == 'New description only'
        assert role.name == original_name


# ==================== Role Listing Tests ====================


class TestListRoles:
    """Test role listing operations."""

    @pytest.mark.asyncio
    async def test_list_all_roles(self, db_session: AsyncSession, test_role: Role, admin_role: Role):
        """Test listing all roles."""
        service = RoleService(db_session)

        roles = await service.list_roles(limit=100, offset=0)

        assert len(roles) >= 2
        role_ids = {r.id for r in roles}
        assert test_role.id in role_ids
        assert admin_role.id in role_ids

    @pytest.mark.asyncio
    async def test_list_active_roles_only(
        self, db_session: AsyncSession, test_role: Role, create_test_role
    ):
        """Test listing only active roles."""
        # Create an inactive role
        inactive_role = await create_test_role(
            name='InactiveRole', status=Status.INACTIVE
        )

        service = RoleService(db_session)

        roles = await service.list_roles(active_only=True)

        role_ids = {r.id for r in roles}
        # Should include active role
        assert test_role.id in role_ids
        # Should not include inactive role
        assert inactive_role.id not in role_ids

    @pytest.mark.asyncio
    async def test_list_roles_pagination(
        self, db_session: AsyncSession, create_test_role
    ):
        """Test role listing with pagination."""
        # Create multiple roles
        for i in range(5):
            await create_test_role(name=f'PaginatedRole{i}')

        service = RoleService(db_session)

        # Get first page
        page1 = await service.list_roles(limit=3, offset=0)
        # Get second page
        page2 = await service.list_roles(limit=3, offset=3)

        assert len(page1) == 3
        assert len(page2) >= 2

        # Pages should have different roles
        page1_ids = {r.id for r in page1}
        page2_ids = {r.id for r in page2}
        assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_list_roles_empty_result(self, db_session: AsyncSession):
        """Test listing roles with offset beyond available roles."""
        service = RoleService(db_session)

        roles = await service.list_roles(limit=10, offset=10000)

        assert len(roles) == 0


# ==================== Role Business Rules Tests ====================


class TestRoleBusinessRules:
    """Test role-specific business rules."""

    @pytest.mark.asyncio
    async def test_role_name_uniqueness_case_sensitive(
        self, db_session: AsyncSession, test_role: Role
    ):
        """Test that role name uniqueness is enforced."""
        service = RoleService(db_session)

        # Try to create role with exact same name
        data = RoleCreate(name=test_role.name)

        with pytest.raises(DuplicateNameException):
            await service.create_role(data)

    @pytest.mark.asyncio
    async def test_create_multiple_roles_with_different_names(
        self, db_session: AsyncSession
    ):
        """Test creating multiple roles with different names."""
        service = RoleService(db_session)

        role1 = await service.create_role(RoleCreate(name='Role1'))
        role2 = await service.create_role(RoleCreate(name='Role2'))
        role3 = await service.create_role(RoleCreate(name='Role3'))

        assert role1.id != role2.id != role3.id
        assert role1.name != role2.name != role3.name

    @pytest.mark.asyncio
    async def test_role_update_to_same_name_allowed(
        self, db_session: AsyncSession, test_role: Role
    ):
        """Test that updating role to its current name is allowed."""
        service = RoleService(db_session)
        data = RoleUpdate(
            name=test_role.name,  # Same name
            description='Updated description',
        )

        role = await service.update_role(test_role.id, data)  # type: ignore

        assert role.name == test_role.name
        assert role.description == 'Updated description'
