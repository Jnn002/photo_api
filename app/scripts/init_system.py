"""
System Initialization Script.

This script initializes the Photography Studio API with:
- All system permissions
- Predefined roles (Admin, Coordinator, Photographer, Editor, User)
- Role-permission associations
- Initial administrator user

Usage:
    source .venv/bin/activate
    python -m app.scripts.init_system

Environment Variables Required:
    ADMIN_EMAIL: Email for the initial admin user
    ADMIN_PASSWORD: Password for the initial admin user
"""

import asyncio
import sys

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.catalog.models import Item, Package, Room  # noqa: F401
from app.clients.models import Client  # noqa: F401
from app.core.config import settings
from app.core.database import async_engine
from app.core.enums import Status
from app.core.security import hash_password
from app.sessions.models import Session  # noqa: F401
from app.users.models import Permission, Role, User, UserRole

# ==================== Permission Definitions ====================

PERMISSIONS = [
    # Session Module
    {
        'code': 'session.create',
        'name': 'Create Session',
        'module': 'session',
        'description': 'Create new photography sessions',
    },
    {
        'code': 'session.view.own',
        'name': 'View Own Sessions',
        'module': 'session',
        'description': 'View sessions assigned to user',
    },
    {
        'code': 'session.view.all',
        'name': 'View All Sessions',
        'module': 'session',
        'description': 'View all sessions in system',
    },
    {
        'code': 'session.edit.pre-assigned',
        'name': 'Edit Pre-Assigned Sessions',
        'module': 'session',
        'description': 'Edit sessions before Assigned status',
    },
    {
        'code': 'session.edit.all',
        'name': 'Edit All Sessions',
        'module': 'session',
        'description': 'Edit sessions in any status',
    },
    {
        'code': 'session.delete',
        'name': 'Delete Session',
        'module': 'session',
        'description': 'Delete sessions (soft delete)',
    },
    {
        'code': 'session.assign-resources',
        'name': 'Assign Resources',
        'module': 'session',
        'description': 'Assign photographers and rooms to sessions',
    },
    {
        'code': 'session.cancel',
        'name': 'Cancel Session',
        'module': 'session',
        'description': 'Cancel sessions',
    },
    {
        'code': 'session.mark-attended',
        'name': 'Mark Session Attended',
        'module': 'session',
        'description': 'Mark session as attended (photographer)',
    },
    {
        'code': 'session.mark-ready',
        'name': 'Mark Session Ready',
        'module': 'session',
        'description': 'Mark session as ready for delivery (editor)',
    },
    # Client Module
    {
        'code': 'client.create',
        'name': 'Create Client',
        'module': 'client',
        'description': 'Create new clients',
    },
    {
        'code': 'client.view',
        'name': 'View Client',
        'module': 'client',
        'description': 'View client information',
    },
    {
        'code': 'client.edit',
        'name': 'Edit Client',
        'module': 'client',
        'description': 'Edit client information',
    },
    {
        'code': 'client.delete',
        'name': 'Delete Client',
        'module': 'client',
        'description': 'Delete clients (soft delete)',
    },
    # Catalog Module - Items
    {
        'code': 'item.create',
        'name': 'Create Item',
        'module': 'catalog',
        'description': 'Create new catalog items',
    },
    {
        'code': 'item.edit',
        'name': 'Edit Item',
        'module': 'catalog',
        'description': 'Edit catalog items',
    },
    {
        'code': 'item.delete',
        'name': 'Delete Item',
        'module': 'catalog',
        'description': 'Delete catalog items (soft delete)',
    },
    # Catalog Module - Packages
    {
        'code': 'package.create',
        'name': 'Create Package',
        'module': 'catalog',
        'description': 'Create new packages',
    },
    {
        'code': 'package.edit',
        'name': 'Edit Package',
        'module': 'catalog',
        'description': 'Edit packages',
    },
    {
        'code': 'package.delete',
        'name': 'Delete Package',
        'module': 'catalog',
        'description': 'Delete packages (soft delete)',
    },
    # Catalog Module - Rooms
    {
        'code': 'room.create',
        'name': 'Create Room',
        'module': 'catalog',
        'description': 'Create new rooms',
    },
    {
        'code': 'room.edit',
        'name': 'Edit Room',
        'module': 'catalog',
        'description': 'Edit rooms',
    },
    {
        'code': 'room.delete',
        'name': 'Delete Room',
        'module': 'catalog',
        'description': 'Delete rooms (soft delete)',
    },
    # User Module
    {
        'code': 'user.create',
        'name': 'Create User',
        'module': 'user',
        'description': 'Create new users',
    },
    {
        'code': 'user.view',
        'name': 'View User',
        'module': 'user',
        'description': 'View user information',
    },
    {
        'code': 'user.edit',
        'name': 'Edit User',
        'module': 'user',
        'description': 'Edit user information',
    },
    {
        'code': 'user.delete',
        'name': 'Delete User',
        'module': 'user',
        'description': 'Delete users (soft delete)',
    },
    {
        'code': 'user.assign-role',
        'name': 'Assign Role',
        'module': 'user',
        'description': 'Assign roles to users',
    },
    # Report Module
    {
        'code': 'report.session',
        'name': 'Session Reports',
        'module': 'report',
        'description': 'View session reports',
    },
    {
        'code': 'report.financial',
        'name': 'Financial Reports',
        'module': 'report',
        'description': 'View financial reports',
    },
    {
        'code': 'report.performance',
        'name': 'Performance Reports',
        'module': 'report',
        'description': 'View performance reports',
    },
    # System Module
    {
        'code': 'system.settings',
        'name': 'System Settings',
        'module': 'system',
        'description': 'Manage system settings',
    },
    {
        'code': 'system.audit-log',
        'name': 'Audit Log',
        'module': 'system',
        'description': 'View system audit logs',
    },
    # Role Module
    {
        'code': 'role.create',
        'name': 'Create Role',
        'module': 'role',
        'description': 'Create new roles',
    },
    {
        'code': 'role.read',
        'name': 'Read Role',
        'module': 'role',
        'description': 'View role information',
    },
    {
        'code': 'role.edit',
        'name': 'Edit Role',
        'module': 'role',
        'description': 'Edit role information',
    },
    {
        'code': 'role.delete',
        'name': 'Delete Role',
        'module': 'role',
        'description': 'Delete roles (soft delete)',
    },
    {
        'code': 'role.list',
        'name': 'List Roles',
        'module': 'role',
        'description': 'List all roles',
    },
    {
        'code': 'role.assign',
        'name': 'Assign Role',
        'module': 'role',
        'description': 'Assign roles to users',
    },
    # Permission Module
    {
        'code': 'permission.create',
        'name': 'Create Permission',
        'module': 'permission',
        'description': 'Create new permissions',
    },
    {
        'code': 'permission.read',
        'name': 'Read Permission',
        'module': 'permission',
        'description': 'View permission information',
    },
    {
        'code': 'permission.edit',
        'name': 'Edit Permission',
        'module': 'permission',
        'description': 'Edit permission information',
    },
    {
        'code': 'permission.delete',
        'name': 'Delete Permission',
        'module': 'permission',
        'description': 'Delete permissions (soft delete)',
    },
    {
        'code': 'permission.list',
        'name': 'List Permissions',
        'module': 'permission',
        'description': 'List all permissions',
    },
    # User List Permission
    {
        'code': 'user.list',
        'name': 'List Users',
        'module': 'user',
        'description': 'List all users in the system',
    },
]

# ==================== Role Definitions ====================

ROLES = [
    {
        'name': 'admin',
        'description': 'System administrator with full access to all features',
    },
    {
        'name': 'coordinator',
        'description': 'Session coordinator and client manager',
    },
    {
        'name': 'photographer',
        'description': 'Photography service provider',
    },
    {
        'name': 'editor',
        'description': 'Photo and video editor',
    },
    {
        'name': 'user',
        'description': 'Basic user role for self-registered users',
    },
]

# ==================== Role-Permission Mapping ====================

ROLE_PERMISSIONS = {
    'admin': [
        # Admin gets ALL permissions
        'session.create',
        'session.view.own',
        'session.view.all',
        'session.edit.pre-assigned',
        'session.edit.all',
        'session.delete',
        'session.assign-resources',
        'session.cancel',
        'session.mark-attended',
        'session.mark-ready',
        'client.create',
        'client.view',
        'client.edit',
        'client.delete',
        'item.create',
        'item.edit',
        'item.delete',
        'package.create',
        'package.edit',
        'package.delete',
        'room.create',
        'room.edit',
        'room.delete',
        'user.create',
        'user.view',
        'user.edit',
        'user.delete',
        'user.assign-role',
        'user.list',
        'report.session',
        'report.financial',
        'report.performance',
        'system.settings',
        'system.audit-log',
        'role.create',
        'role.read',
        'role.edit',
        'role.delete',
        'role.list',
        'role.assign',
        'permission.create',
        'permission.read',
        'permission.edit',
        'permission.delete',
        'permission.list',
    ],
    'coordinator': [
        'session.create',
        'session.view.all',
        'session.edit.pre-assigned',
        'session.assign-resources',
        'session.cancel',
        'session.mark-attended',
        'session.mark-ready',
        'client.create',
        'client.view',
        'client.edit',
        'report.session',
        'report.financial',
        'report.performance',
    ],
    'photographer': [
        'session.view.own',
        'session.mark-attended',
    ],
    'editor': [
        'session.view.own',
        'session.mark-ready',
    ],
    'user': [
        # Basic users have minimal permissions
        # They can view their own profile (handled separately)
    ],
}


# ==================== Helper Functions ====================


async def create_permissions(db: AsyncSession) -> dict[str, Permission]:
    """Create all system permissions."""
    print('\n📝 Creating permissions...')

    permission_map: dict[str, Permission] = {}

    for perm_data in PERMISSIONS:
        # Check if permission already exists
        statement = select(Permission).where(Permission.code == perm_data['code'])
        result = await db.exec(statement)
        existing = result.first()

        if existing:
            print(f'  ⏭️  Permission {perm_data["code"]} already exists')
            permission_map[perm_data['code']] = existing
        else:
            # Create new permission
            permission = Permission(
                code=perm_data['code'],
                name=perm_data['name'],
                module=perm_data['module'],
                description=perm_data.get('description'),
                status=Status.ACTIVE,
            )
            db.add(permission)
            await db.flush()
            await db.refresh(permission)
            permission_map[perm_data['code']] = permission
            print(f'  ✅ Created permission: {perm_data["code"]}')

    await db.commit()
    print(f'✅ {len(permission_map)} permissions ready')
    return permission_map


async def create_roles(db: AsyncSession) -> dict[str, Role]:
    """Create all system roles."""
    print('\n👥 Creating roles...')

    role_map: dict[str, Role] = {}

    for role_data in ROLES:
        # Check if role already exists
        statement = select(Role).where(Role.name == role_data['name'])
        result = await db.exec(statement)
        existing = result.first()

        if existing:
            print(f'  ⏭️  Role {role_data["name"]} already exists')
            role_map[role_data['name']] = existing
        else:
            # Create new role
            role = Role(
                name=role_data['name'],
                description=role_data['description'],
                status=Status.ACTIVE,
            )
            db.add(role)
            await db.flush()
            await db.refresh(role)
            role_map[role_data['name']] = role
            print(f'  ✅ Created role: {role_data["name"]}')

    await db.commit()
    print(f'✅ {len(role_map)} roles ready')
    return role_map


async def assign_permissions_to_roles(
    db: AsyncSession,
    role_map: dict[str, Role],
    permission_map: dict[str, Permission],
) -> None:
    """Assign permissions to roles based on ROLE_PERMISSIONS mapping."""
    print('\n🔗 Assigning permissions to roles...')

    for role_name, permission_codes in ROLE_PERMISSIONS.items():
        role = role_map.get(role_name)
        if not role:
            print(f'  ⚠️  Role {role_name} not found, skipping')
            continue

        # Get existing permissions for this role
        await db.refresh(role, ['permissions'])
        existing_codes = {perm.code for perm in role.permissions}

        permissions_to_add = []
        for perm_code in permission_codes:
            permission = permission_map.get(perm_code)
            if not permission:
                print(f'  ⚠️  Permission {perm_code} not found, skipping')
                continue

            if perm_code not in existing_codes:
                permissions_to_add.append(permission)

        if permissions_to_add:
            role.permissions.extend(permissions_to_add)
            await db.commit()
            await db.refresh(role, ['permissions'])
            print(
                f'  ✅ Assigned {len(permissions_to_add)} permissions to role: {role_name} '
                f'(total: {len(role.permissions)})'
            )
        else:
            print(f'  ⏭️  All permissions already assigned to role: {role_name}')

    print('✅ Permission assignment completed')


async def create_admin_user(db: AsyncSession, role_map: dict[str, Role]) -> User:
    """Create the initial administrator user."""
    print('\n👤 Creating admin user...')

    # Get admin credentials from environment
    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD

    if not admin_email or not admin_password:
        print('❌ ERROR: ADMIN_EMAIL and ADMIN_PASSWORD must be set in environment')
        sys.exit(1)

    # Check if admin user already exists
    statement = select(User).where(User.email == admin_email)
    result = await db.exec(statement)
    existing_user = result.first()

    if existing_user:
        print(f'  ⏭️  User with email {admin_email} already exists')
        return existing_user

    # Create admin user
    admin_user = User(
        full_name='System Administrator',
        email=admin_email,
        password_hash=hash_password(admin_password),
        status=Status.ACTIVE,
    )

    db.add(admin_user)
    await db.flush()
    await db.refresh(admin_user)

    # Assign admin role
    admin_role = role_map.get('admin')
    if not admin_role:
        print('❌ ERROR: Admin role not found')
        sys.exit(1)

    # Create UserRole record directly to avoid async issues with .append()
    user_role = UserRole(
        user_id=admin_user.id,  # type: ignore
        role_id=admin_role.id,  # type: ignore
        assigned_by=admin_user.id,
    )
    db.add(user_role)
    await db.commit()
    await db.refresh(admin_user)

    print(f'  ✅ Created admin user: {admin_email}')
    print('  ✅ Assigned role: admin')

    return admin_user


# ==================== Main Initialization ====================


async def init_system() -> None:
    """Initialize the system with permissions, roles, and admin user."""
    print('=' * 60)
    print('🚀 Photography Studio API - System Initialization')
    print('=' * 60)

    async with AsyncSession(async_engine) as db:
        try:
            # Step 1: Create permissions
            permission_map = await create_permissions(db)

            # Step 2: Create roles
            role_map = await create_roles(db)

            # Step 3: Assign permissions to roles
            await assign_permissions_to_roles(db, role_map, permission_map)

            # Step 4: Create admin user
            admin_user = await create_admin_user(db, role_map)

            print('\n' + '=' * 60)
            print('✅ System initialization completed successfully!')
            print('=' * 60)
            print(f'\n📧 Admin Email: {admin_user.email}')
            print('🔑 Admin Password: (set via ADMIN_PASSWORD env var)')
            print('\n💡 You can now login at: POST /api/v1/auth/login')
            print('=' * 60)

        except Exception as e:
            print(f'\n❌ ERROR: System initialization failed: {e}')
            import traceback

            traceback.print_exc()
            sys.exit(1)


def main() -> None:
    """Entry point for the script."""
    asyncio.run(init_system())


if __name__ == '__main__':
    main()
