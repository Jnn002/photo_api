DROP SCHEMA  studio  CASCADE;
CREATE DATABASE photography_studio;
CREATE SCHEMA studio;
\c postgres;
USE postgres;
DROP DATABASE photography_studio WITH (FORCE);

SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'photography_studio'
  AND pid <> pg_backend_pid();

SELECT * FROM studio.client;

-- ======================================================================
-- Photography Studio API - Database Bootstrap
-- ======================================================================
-- This script initializes the database with:
-- 1. Default permissions for all modules
-- 2. Default roles (super_admin, admin, photographer, user)
-- 3. First super admin user
-- 4. Role-permission assignments
-- 5. User-role assignment for super admin
--
-- Usage:
--   psql -U postgres -d photography_studio_db -f scripts/bootstrap.sql
-- ======================================================================

-- Start transaction
BEGIN;

\echo '🔐 Creating permissions...'

-- Insert permissions (if not exist)
INSERT INTO studio.permission (code, name, description, module, status, created_at, updated_at)
VALUES
    -- User permissions
    ('user.create', 'Create User', 'Create new users', 'user', 'ACTIVE', NOW(), NOW()),
    ('user.read', 'Read User', 'View user information', 'user', 'ACTIVE', NOW(), NOW()),
    ('user.edit', 'Edit User', 'Edit user information', 'user', 'ACTIVE', NOW(), NOW()),
    ('user.delete', 'Delete User', 'Deactivate users', 'user', 'ACTIVE', NOW(), NOW()),
    ('user.list', 'List Users', 'List all users', 'user', 'ACTIVE', NOW(), NOW()),
    
    -- Role permissions
    ('role.create', 'Create Role', 'Create new roles', 'role', 'ACTIVE', NOW(), NOW()),
    ('role.read', 'Read Role', 'View role information', 'role', 'ACTIVE', NOW(), NOW()),
    ('role.edit', 'Edit Role', 'Edit role information', 'role', 'ACTIVE', NOW(), NOW()),
    ('role.delete', 'Delete Role', 'Deactivate roles', 'role', 'ACTIVE', NOW(), NOW()),
    ('role.list', 'List Roles', 'List all roles', 'role', 'ACTIVE', NOW(), NOW()),
    ('role.assign', 'Assign Role', 'Assign/remove roles to users', 'role', 'ACTIVE', NOW(), NOW()),
    
    -- Permission permissions
    ('permission.create', 'Create Permission', 'Create new permissions', 'permission', 'ACTIVE', NOW(), NOW()),
    ('permission.read', 'Read Permission', 'View permission information', 'permission', 'ACTIVE', NOW(), NOW()),
    ('permission.edit', 'Edit Permission', 'Edit permission information', 'permission', 'ACTIVE', NOW(), NOW()),
    ('permission.delete', 'Delete Permission', 'Deactivate permissions', 'permission', 'ACTIVE', NOW(), NOW()),
    ('permission.list', 'List Permissions', 'List all permissions', 'permission', 'ACTIVE', NOW(), NOW()),
    
    -- Client permissions
    ('client.create', 'Create Client', 'Create new clients', 'client', 'ACTIVE', NOW(), NOW()),
    ('client.read', 'Read Client', 'View client information', 'client', 'ACTIVE', NOW(), NOW()),
    ('client.edit', 'Edit Client', 'Edit client information', 'client', 'ACTIVE', NOW(), NOW()),
    ('client.delete', 'Delete Client', 'Deactivate clients', 'client', 'ACTIVE', NOW(), NOW()),
    ('client.list', 'List Clients', 'List all clients', 'client', 'ACTIVE', NOW(), NOW()),
    
    -- Session permissions
    ('session.create', 'Create Session', 'Create new sessions', 'session', 'ACTIVE', NOW(), NOW()),
    ('session.read', 'Read Session', 'View session information', 'session', 'ACTIVE', NOW(), NOW()),
    ('session.edit', 'Edit Session', 'Edit session information', 'session', 'ACTIVE', NOW(), NOW()),
    ('session.delete', 'Delete Session', 'Deactivate sessions', 'session', 'ACTIVE', NOW(), NOW()),
    ('session.list', 'List Sessions', 'List all sessions', 'session', 'ACTIVE', NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

SELECT * FROM studio.permission;

\echo '✅ Permissions created'

\echo '👥 Creating roles...'

-- Insert roles (if not exist)
INSERT INTO studio.role (name, description, status, created_at, updated_at)
VALUES
    ('super_admin', 'Super Administrator - Full system access', 'ACTIVE', NOW(), NOW()),
    ('admin', 'Administrator - Most system access except permission management', 'ACTIVE', NOW(), NOW()),
    ('photographer', 'Photographer - Can manage clients and sessions', 'ACTIVE', NOW(), NOW()),
    ('user', 'Regular User - Basic access', 'ACTIVE', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

\echo '✅ Roles created'

\echo '🔗 Assigning permissions to roles...'

-- Assign ALL permissions to super_admin
INSERT INTO studio.rolepermission (role_id, permission_id, granted_at)
SELECT 
    r.id,
    p.id,
    NOW()
FROM studio.role r
CROSS JOIN studio.permission p
WHERE r.name = 'super_admin'
ON CONFLICT (role_id, permission_id) DO NOTHING;

SELECT * FROM studio.rolepermission;

-- Assign permissions to admin (all except permission.*)
INSERT INTO studio.rolepermission (role_id, permission_id, granted_at)
SELECT 
    r.id,
    p.id,
    NOW()
FROM studio.role r
CROSS JOIN studio.permission p
WHERE r.name = 'admin'
  AND p.module != 'permission'
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Assign permissions to photographer (client.* and session.*)
INSERT INTO studio.rolepermission (role_id, permission_id, granted_at)
SELECT 
    r.id,
    p.id,
    NOW()
FROM studio.role r
CROSS JOIN studio.permission p
WHERE r.name = 'photographer'
  AND p.module IN ('client', 'session')
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- user role has no special permissions by default

\echo '✅ Permissions assigned to roles'

\echo '👤 Creating super admin user...'

-- Create super admin user (if not exists)
-- Password: Admin123! (hashed with bcrypt)
INSERT INTO studio."user" (full_name, email, password_hash, phone, status, created_at, updated_at)
VALUES (
    'Super Admin',
    'admin@studio.com',
    '$2b$12$zkL6aO62Fx4mg9w31NIUiu9zpD1l8NFfHzGqJ5gBmHwEFGoFQdyuK',
    '+1234567890',
    'ACTIVE',
    NOW(),
    NOW()
)
ON CONFLICT (email) DO NOTHING;

SELECT * FROM studio.user;

\echo '✅ Super admin user created'

\echo '🔗 Assigning super_admin role to admin user...'

-- Assign super_admin role to the admin user
INSERT INTO studio.userrole (user_id, role_id, assigned_at, assigned_by)
SELECT 
    u.id,
    r.id,
    NOW(),
    u.id  -- Self-assigned for bootstrap
FROM studio."user" u
CROSS JOIN studio.role r
WHERE u.email = 'admin@studio.com'
  AND r.name = 'super_admin'
ON CONFLICT (user_id, role_id) DO NOTHING;

\echo '✅ Super admin role assigned'

-- Commit transaction
COMMIT;

-- Display summary
\echo ''
\echo '======================================================================'
\echo '✅ DATABASE BOOTSTRAP COMPLETED SUCCESSFULLY!'
\echo '======================================================================'
\echo ''
\echo '📋 Summary:'
SELECT 
    (SELECT COUNT(*) FROM studio.permission) as permissions,
    (SELECT COUNT(*) FROM studio.role) as roles,
    (SELECT COUNT(*) FROM studio."user") as users;

\echo ''
\echo '📊 Role-Permission Assignments:'

SELECT 
    r.name as role,
    COUNT(rp.permission_id) as permissions_count
FROM studio.role r
LEFT JOIN studio.rolepermission rp ON r.id = rp.role_id
GROUP BY r.id, r.name
ORDER BY r.name;

\echo ''
\echo '🔑 Login Credentials:'
\echo '  Email: admin@studio.com'
\echo '  Password: Admin123!'
\echo ''
\echo '⚠️  IMPORTANT: Change the default password immediately!'
\echo '  Use PATCH /api/v1/users/{user_id}/password endpoint'
\echo ''
\echo '🎉 Your system is ready! You can now:'
\echo '  1. Login: POST /api/v1/auth/login'
\echo '  2. Create users: POST /api/v1/users'
\echo '  3. Assign roles: POST /api/v1/users/{user_id}/roles/{role_id}'
\echo '======================================================================'

