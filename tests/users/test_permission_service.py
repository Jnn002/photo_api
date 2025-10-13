"""
Tests for PermissionService business logic.

This module tests permission management operations including:
- Permission creation and validation
- Permission listing and filtering
- Permission code format validation
"""

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.enums import Status
from app.core.exceptions import BusinessValidationException
from app.users.models import Permission
from app.users.schemas import PermissionCreate
from app.users.service import PermissionService


# ==================== Permission Creation Tests ====================


class TestCreatePermission:
    """Test permission creation."""

    @pytest.mark.asyncio
    async def test_create_permission_success(self, db_session: AsyncSession):
        """Test successful permission creation."""
        service = PermissionService(db_session)
        data = PermissionCreate(
            code='test.create',
            name='Test Create',
            description='Test creation permission',
            module='test',
        )

        permission = await service.create_permission(data)

        assert permission.id is not None
        assert permission.code == 'test.create'
        assert permission.name == 'Test Create'
        assert permission.description == 'Test creation permission'
        assert permission.module == 'test'
        assert permission.status == Status.ACTIVE

    @pytest.mark.asyncio
    async def test_create_permission_without_description(
        self, db_session: AsyncSession
    ):
        """Test creating permission without description."""
        service = PermissionService(db_session)
        data = PermissionCreate(
            code='test.read',
            name='Test Read',
            module='test',
        )

        permission = await service.create_permission(data)

        assert permission.code == 'test.read'
        assert permission.description is None

    @pytest.mark.asyncio
    async def test_create_permission_duplicate_code(
        self, db_session: AsyncSession, test_permission: Permission
    ):
        """Test creating permission with duplicate code fails."""
        service = PermissionService(db_session)
        data = PermissionCreate(
            code=test_permission.code,  # Duplicate code
            name='Should Fail',
            module='test',
        )

        with pytest.raises(BusinessValidationException) as exc_info:
            await service.create_permission(data)

        assert test_permission.code in str(exc_info.value)
        assert 'already exists' in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_permission_with_scope(self, db_session: AsyncSession):
        """Test creating permission with scope (module.action.scope)."""
        service = PermissionService(db_session)
        data = PermissionCreate(
            code='user.edit.own',
            name='Edit Own User',
            description='Edit own user profile',
            module='user',
        )

        permission = await service.create_permission(data)

        assert permission.code == 'user.edit.own'


# ==================== Permission Listing Tests ====================


class TestListPermissions:
    """Test permission listing operations."""

    @pytest.mark.asyncio
    async def test_list_all_permissions(
        self, db_session: AsyncSession, test_permission: Permission, create_test_permission
    ):
        """Test listing all permissions."""
        # Create additional permissions
        await create_test_permission(code='test.create', name='Test Create')
        await create_test_permission(code='test.update', name='Test Update')

        service = PermissionService(db_session)

        permissions = await service.list_permissions(limit=100, offset=0)

        assert len(permissions) >= 3
        permission_codes = {p.code for p in permissions}
        assert test_permission.code in permission_codes

    @pytest.mark.asyncio
    async def test_list_permissions_by_module(
        self, db_session: AsyncSession, create_test_permission
    ):
        """Test listing permissions filtered by module."""
        # Create permissions in different modules
        user_perm1 = await create_test_permission(
            code='user.create', name='User Create', module='user'
        )
        user_perm2 = await create_test_permission(
            code='user.edit', name='User Edit', module='user'
        )
        session_perm = await create_test_permission(
            code='session.create', name='Session Create', module='session'
        )

        service = PermissionService(db_session)

        # List only user module permissions
        user_permissions = await service.list_permissions(module='user')

        permission_ids = {p.id for p in user_permissions}
        # Should include user permissions
        assert user_perm1.id in permission_ids
        assert user_perm2.id in permission_ids
        # Should not include session permission
        assert session_perm.id not in permission_ids

    @pytest.mark.asyncio
    async def test_list_active_permissions_only(
        self, db_session: AsyncSession, test_permission: Permission, create_test_permission
    ):
        """Test listing only active permissions."""
        # Create an inactive permission
        inactive_perm = await create_test_permission(
            code='test.inactive',
            name='Inactive Permission',
            status=Status.INACTIVE,
        )

        service = PermissionService(db_session)

        permissions = await service.list_permissions(active_only=True)

        permission_ids = {p.id for p in permissions}
        # Should include active permission
        assert test_permission.id in permission_ids
        # Should not include inactive permission
        assert inactive_perm.id not in permission_ids

    @pytest.mark.asyncio
    async def test_list_permissions_pagination(
        self, db_session: AsyncSession, create_test_permission
    ):
        """Test permission listing with pagination."""
        # Create multiple permissions
        for i in range(10):
            await create_test_permission(
                code=f'paginated.perm{i}',
                name=f'Paginated Permission {i}',
                module='paginated',
            )

        service = PermissionService(db_session)

        # Get first page
        page1 = await service.list_permissions(limit=5, offset=0)
        # Get second page
        page2 = await service.list_permissions(limit=5, offset=5)

        assert len(page1) == 5
        assert len(page2) >= 5

        # Pages should have different permissions
        page1_ids = {p.id for p in page1}
        page2_ids = {p.id for p in page2}
        assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_list_permissions_by_module_with_pagination(
        self, db_session: AsyncSession, create_test_permission
    ):
        """Test listing permissions by module with pagination."""
        # Create multiple permissions in same module
        for i in range(7):
            await create_test_permission(
                code=f'catalog.action{i}',
                name=f'Catalog Action {i}',
                module='catalog',
            )

        service = PermissionService(db_session)

        # List catalog permissions with pagination
        page1 = await service.list_permissions(module='catalog', limit=5, offset=0)
        page2 = await service.list_permissions(module='catalog', limit=5, offset=5)

        assert len(page1) == 5
        assert len(page2) >= 2

        # All should be catalog module
        for perm in page1 + page2:
            assert perm.module == 'catalog'


# ==================== Permission Code Format Tests ====================


class TestPermissionCodeFormat:
    """Test permission code format validation."""

    @pytest.mark.asyncio
    async def test_permission_code_two_parts(self, db_session: AsyncSession):
        """Test permission with two-part code (module.action)."""
        service = PermissionService(db_session)
        data = PermissionCreate(
            code='module.action',
            name='Module Action',
            module='module',
        )

        permission = await service.create_permission(data)

        assert permission.code == 'module.action'

    @pytest.mark.asyncio
    async def test_permission_code_three_parts(self, db_session: AsyncSession):
        """Test permission with three-part code (module.action.scope)."""
        service = PermissionService(db_session)
        data = PermissionCreate(
            code='module.action.scope',
            name='Module Action Scope',
            module='module',
        )

        permission = await service.create_permission(data)

        assert permission.code == 'module.action.scope'

    @pytest.mark.asyncio
    async def test_permission_code_uniqueness(
        self, db_session: AsyncSession, create_test_permission
    ):
        """Test that permission codes must be unique."""
        code = 'unique.test.permission'
        await create_test_permission(code=code, name='First')

        service = PermissionService(db_session)
        data = PermissionCreate(
            code=code,  # Same code
            name='Second',
            module='unique',
        )

        with pytest.raises(BusinessValidationException) as exc_info:
            await service.create_permission(data)

        assert code in str(exc_info.value)


# ==================== Permission Business Rules Tests ====================


class TestPermissionBusinessRules:
    """Test permission-specific business rules."""

    @pytest.mark.asyncio
    async def test_create_multiple_permissions_same_module(
        self, db_session: AsyncSession
    ):
        """Test creating multiple permissions in the same module."""
        service = PermissionService(db_session)

        perm1 = await service.create_permission(
            PermissionCreate(code='module.create', name='Create', module='module')
        )
        perm2 = await service.create_permission(
            PermissionCreate(code='module.read', name='Read', module='module')
        )
        perm3 = await service.create_permission(
            PermissionCreate(code='module.update', name='Update', module='module')
        )

        assert perm1.module == perm2.module == perm3.module == 'module'
        assert perm1.code != perm2.code != perm3.code

    @pytest.mark.asyncio
    async def test_list_permissions_empty_module(self, db_session: AsyncSession):
        """Test listing permissions for module with no permissions."""
        service = PermissionService(db_session)

        permissions = await service.list_permissions(module='nonexistent')

        assert len(permissions) == 0

    @pytest.mark.asyncio
    async def test_create_permission_different_modules_same_action(
        self, db_session: AsyncSession
    ):
        """Test creating permissions with same action in different modules."""
        service = PermissionService(db_session)

        user_create = await service.create_permission(
            PermissionCreate(code='user.create', name='User Create', module='user')
        )
        session_create = await service.create_permission(
            PermissionCreate(
                code='session.create', name='Session Create', module='session'
            )
        )

        assert user_create.code != session_create.code
        assert user_create.module != session_create.module


# ==================== Module Filtering Tests ====================


class TestModuleFiltering:
    """Test module-based filtering functionality."""

    @pytest.mark.asyncio
    async def test_list_permissions_multiple_modules(
        self, db_session: AsyncSession, create_test_permission
    ):
        """Test that permissions are properly grouped by module."""
        # Create permissions in different modules
        await create_test_permission(code='users.create', module='users')
        await create_test_permission(code='users.edit', module='users')
        await create_test_permission(code='sessions.create', module='sessions')
        await create_test_permission(code='sessions.edit', module='sessions')
        await create_test_permission(code='clients.create', module='clients')

        service = PermissionService(db_session)

        # Get counts for each module
        users_perms = await service.list_permissions(module='users')
        sessions_perms = await service.list_permissions(module='sessions')
        clients_perms = await service.list_permissions(module='clients')

        assert len(users_perms) == 2
        assert len(sessions_perms) == 2
        assert len(clients_perms) == 1

    @pytest.mark.asyncio
    async def test_list_all_includes_all_modules(
        self, db_session: AsyncSession, create_test_permission
    ):
        """Test that listing all permissions includes all modules."""
        # Create permissions in different modules
        await create_test_permission(code='mod1.action', module='mod1')
        await create_test_permission(code='mod2.action', module='mod2')
        await create_test_permission(code='mod3.action', module='mod3')

        service = PermissionService(db_session)

        all_permissions = await service.list_permissions()

        modules = {p.module for p in all_permissions}
        assert 'mod1' in modules
        assert 'mod2' in modules
        assert 'mod3' in modules
