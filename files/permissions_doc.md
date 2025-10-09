# Permissions & RBAC - Photography Studio Management System

**Version:** 1.0  
**Last Updated:** 2025-01-07

This document defines the Role-Based Access Control (RBAC) system for the Photography Studio Management API. All permission checks must follow this matrix.

---

## Table of Contents

1. [System Roles](#1-system-roles)
2. [Permission Codes](#2-permission-codes)
3. [Permission Matrix](#3-permission-matrix)
4. [Implementation Guidelines](#4-implementation-guidelines)
5. [Special Cases](#5-special-cases)

---

## 1. System Roles

### 1.1 Role Definitions

| Role | Code | Description | Count |
|------|------|-------------|-------|
| **Admin** | `Admin` | System administrator with full access | 1 |
| **Coordinator** | `Coordinator` | Session coordinator and client manager | 2-3 |
| **Photographer** | `Photographer` | Photography service provider | 3-4 |
| **Editor** | `Editor` | Photo and video editor | 3 |

### 1.2 Role Hierarchy

```
Admin
  ├─ All permissions
  └─ Can manage users and system settings

Coordinator
  ├─ Manage sessions (create, edit, assign)
  ├─ Manage clients
  └─ View reports

Photographer
  ├─ View assigned sessions
  └─ Mark sessions as attended

Editor
  ├─ View sessions pending editing
  └─ Mark sessions as ready for delivery
```

---

## 2. Permission Codes

All permissions follow the format: `{module}.{action}[.scope]`

### 2.1 Session Module

| Code | Description | Access Level |
|------|-------------|--------------|
| `session.create` | Create new sessions | Write |
| `session.view.own` | View sessions assigned to user | Read |
| `session.view.all` | View all sessions in system | Read |
| `session.edit.pre-assigned` | Edit sessions before 'Assigned' state | Write |
| `session.edit.all` | Edit sessions in any state | Write |
| `session.delete` | Delete sessions (soft delete) | Write |
| `session.assign-resources` | Assign photographers and rooms | Write |
| `session.cancel` | Cancel sessions | Write |
| `session.mark-attended` | Mark session as attended (photographer) | Write |
| `session.mark-ready` | Mark session as ready (editor) | Write |

### 2.2 Client Module

| Code | Description | Access Level |
|------|-------------|--------------|
| `client.create` | Create new clients | Write |
| `client.view` | View client information | Read |
| `client.edit` | Edit client information | Write |
| `client.delete` | Delete clients (soft delete) | Write |

### 2.3 Catalog Module

| Code | Description | Access Level |
|------|-------------|--------------|
| `item.create` | Create new items | Write |
| `item.edit` | Edit items | Write |
| `item.delete` | Delete items (soft delete) | Write |
| `package.create` | Create new packages | Write |
| `package.edit` | Edit packages | Write |
| `package.delete` | Delete packages (soft delete) | Write |
| `room.create` | Create new rooms | Write |
| `room.edit` | Edit rooms | Write |
| `room.delete` | Delete rooms (soft delete) | Write |

### 2.4 User Module

| Code | Description | Access Level |
|------|-------------|--------------|
| `user.create` | Create new users | Write |
| `user.view` | View user information | Read |
| `user.edit` | Edit user information | Write |
| `user.delete` | Delete users (soft delete) | Write |
| `user.assign-role` | Assign roles to users | Write |

### 2.5 Report Module

| Code | Description | Access Level |
|------|-------------|--------------|
| `report.session` | View session reports | Read |
| `report.financial` | View financial reports | Read |
| `report.performance` | View performance reports | Read |

### 2.6 System Module

| Code | Description | Access Level |
|------|-------------|--------------|
| `system.settings` | Manage system settings | Write |
| `system.audit-log` | View system audit logs | Read |

---

## 3. Permission Matrix

### 3.1 Complete Permission Matrix by Role

| Permission Code | Admin | Coordinator | Photographer | Editor |
|-----------------|:-----:|:-----------:|:------------:|:------:|
| **Session Management** |
| `session.create` | ✅ | ✅ | ❌ | ❌ |
| `session.view.own` | ✅ | ✅ | ✅ | ✅ |
| `session.view.all` | ✅ | ✅ | ❌ | ❌ |
| `session.edit.pre-assigned` | ✅ | ✅ | ❌ | ❌ |
| `session.edit.all` | ✅ | ❌ | ❌ | ❌ |
| `session.delete` | ✅ | ❌ | ❌ | ❌ |
| `session.assign-resources` | ✅ | ✅ | ❌ | ❌ |
| `session.cancel` | ✅ | ✅ | ❌ | ❌ |
| `session.mark-attended` | ✅ | ✅ | ✅ | ❌ |
| `session.mark-ready` | ✅ | ✅ | ❌ | ✅ |
| **Client Management** |
| `client.create` | ✅ | ✅ | ❌ | ❌ |
| `client.view` | ✅ | ✅ | ❌ | ❌ |
| `client.edit` | ✅ | ✅ | ❌ | ❌ |
| `client.delete` | ✅ | ❌ | ❌ | ❌ |
| **Catalog Management** |
| `item.create` | ✅ | ❌ | ❌ | ❌ |
| `item.edit` | ✅ | ❌ | ❌ | ❌ |
| `item.delete` | ✅ | ❌ | ❌ | ❌ |
| `package.create` | ✅ | ❌ | ❌ | ❌ |
| `package.edit` | ✅ | ❌ | ❌ | ❌ |
| `package.delete` | ✅ | ❌ | ❌ | ❌ |
| `room.create` | ✅ | ❌ | ❌ | ❌ |
| `room.edit` | ✅ | ❌ | ❌ | ❌ |
| `room.delete` | ✅ | ❌ | ❌ | ❌ |
| **User Management** |
| `user.create` | ✅ | ❌ | ❌ | ❌ |
| `user.view` | ✅ | ❌ | ❌ | ❌ |
| `user.edit` | ✅ | ❌ | ❌ | ❌ |
| `user.delete` | ✅ | ❌ | ❌ | ❌ |
| `user.assign-role` | ✅ | ❌ | ❌ | ❌ |
| **Reports** |
| `report.session` | ✅ | ✅ | ❌ | ❌ |
| `report.financial` | ✅ | ✅ | ❌ | ❌ |
| `report.performance` | ✅ | ✅ | ❌ | ❌ |
| **System** |
| `system.settings` | ✅ | ❌ | ❌ | ❌ |
| `system.audit-log` | ✅ | ❌ | ❌ | ❌ |

### 3.2 Summary by Role

#### Admin
**Total Permissions:** ALL (40+)

**Key Capabilities:**
- Complete system control
- User and role management
- All CRUD operations on all modules
- System configuration
- Audit log access

**Restrictions:** None

---

#### Coordinator
**Total Permissions:** 15

**Can:**
- Create and manage sessions (up to 'Assigned' state)
- Create and manage clients
- Assign photographers and rooms to sessions
- Cancel sessions
- View all sessions and reports
- Mark sessions as attended and ready

**Cannot:**
- Edit sessions in 'Assigned' state or later (only Admin can)
- Delete sessions
- Manage catalog (items, packages, rooms)
- Manage users or system settings

---

#### Photographer
**Total Permissions:** 2

**Can:**
- View own assigned sessions only
- Mark own sessions as attended

**Cannot:**
- View sessions not assigned to them
- Create or edit sessions
- Manage any other data
- View reports

**Special Access:**
- Can view basic client contact info for assigned sessions
- Can add observations to sessions after attending

---

#### Editor
**Total Permissions:** 2

**Can:**
- View sessions in 'Attended' state (pending editing)
- Mark sessions as ready for delivery

**Cannot:**
- View sessions in other states (except assigned to them)
- Create or edit sessions
- Manage any other data
- View reports

**Special Access:**
- Can view basic client contact info for assigned sessions
- Can add observations to sessions during editing
- Can adjust estimated delivery date

---

## 4. Implementation Guidelines

### 4.1 Permission Check Pattern

**In Router (Dependency Injection):**

```python
from typing import Annotated
from fastapi import Depends
from app.core.permissions import require_permission
from app.users.models import User

@router.post("/sessions/")
async def create_session(
    session_data: SessionCreate,
    current_user: Annotated[User, Depends(require_permission("session.create"))],
    db: AsyncSession = Depends(get_session)
):
    # current_user is guaranteed to have permission
    # Implement logic here
    pass
```

**Multiple Permissions (OR logic):**

```python
from app.core.permissions import require_any_permission

@router.get("/sessions/{session_id}")
async def get_session(
    session_id: int,
    current_user: Annotated[User, Depends(
        require_any_permission(["session.view.all", "session.view.own"])
    )],
    db: AsyncSession = Depends(get_session)
):
    # Check if user has permission to view this specific session
    if not has_permission(current_user, "session.view.all"):
        # Only view.own - verify it's assigned to them
        if not is_assigned_to_user(session_id, current_user.id):
            raise HTTPException(status_code=403)
    
    # Continue with logic
    pass
```

**In Service Layer (Business Logic Check):**

```python
async def can_edit_session(
    user: User,
    session: Session,
    db: AsyncSession
) -> bool:
    """Check if user can edit specific session based on its state"""
    
    # Check basic permission
    has_edit_all = await check_user_permission(db, user.id, "session.edit.all")
    has_edit_pre = await check_user_permission(db, user.id, "session.edit.pre-assigned")
    
    if has_edit_all:
        return True
    
    if has_edit_pre and session.status in [
        'Request', 'Negotiation', 'Pre-scheduled', 'Confirmed'
    ]:
        return True
    
    return False
```

### 4.2 Seed Data for Roles & Permissions

**SQL Insert for Roles:**

```sql
INSERT INTO role (name, description, status) VALUES
    ('Admin', 'System administrator with full access', 'Active'),
    ('Coordinator', 'Session coordinator and client manager', 'Active'),
    ('Photographer', 'Photography service provider', 'Active'),
    ('Editor', 'Photo and video editor', 'Active');
```

**SQL Insert for Permissions (sample):**

```sql
-- Session permissions
INSERT INTO permission (code, name, description, module, status) VALUES
    ('session.create', 'Create Session', 'Create new photography sessions', 'session', 'Active'),
    ('session.view.own', 'View Own Sessions', 'View sessions assigned to user', 'session', 'Active'),
    ('session.view.all', 'View All Sessions', 'View all sessions in system', 'session', 'Active'),
    ('session.edit.pre-assigned', 'Edit Pre-Assigned Sessions', 'Edit sessions before Assigned status', 'session', 'Active'),
    ('session.edit.all', 'Edit All Sessions', 'Edit sessions in any status', 'session', 'Active'),
    -- ... (continue for all permissions)
```

**SQL Insert for Role-Permission Assignments (sample):**

```sql
-- Admin gets all permissions (repeat for each permission)
INSERT INTO role_permission (role_id, permission_id)
SELECT r.id, p.id
FROM role r, permission p
WHERE r.name = 'Admin' AND p.status = 'Active';

-- Coordinator gets specific permissions
INSERT INTO role_permission (role_id, permission_id)
SELECT r.id, p.id
FROM role r, permission p
WHERE r.name = 'Coordinator'
  AND p.code IN (
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
    'report.performance'
  );

-- Photographer gets limited permissions
INSERT INTO role_permission (role_id, permission_id)
SELECT r.id, p.id
FROM role r, permission p
WHERE r.name = 'Photographer'
  AND p.code IN (
    'session.view.own',
    'session.mark-attended'
  );

-- Editor gets limited permissions
INSERT INTO role_permission (role_id, permission_id)
SELECT r.id, p.id
FROM role r, permission p
WHERE r.name = 'Editor'
  AND p.code IN (
    'session.view.own',
    'session.mark-ready'
  );
```

### 4.3 Permission Query

**Get User Permissions:**

```sql
SELECT DISTINCT p.code, p.name, p.module
FROM permission p
JOIN role_permission rp ON rp.permission_id = p.id
JOIN user_role ur ON ur.role_id = rp.role_id
WHERE ur.user_id = $1
  AND p.status = 'Active';
```

**Check Specific Permission:**

```sql
SELECT EXISTS (
    SELECT 1
    FROM permission p
    JOIN role_permission rp ON rp.permission_id = p.id
    JOIN user_role ur ON ur.role_id = rp.role_id
    WHERE ur.user_id = $1
      AND p.code = $2
      AND p.status = 'Active'
) AS has_permission;
```

---

## 5. Special Cases

### 5.1 Session Ownership (view.own)

**Rule:** Users with `session.view.own` can only see sessions where they are:
- Assigned as photographer (in `session_photographer`)
- Assigned as editor (`session.assigned_editor_id`)

**Implementation:**

```python
async def get_user_sessions(
    db: AsyncSession,
    user_id: int,
    status: str | None = None
) -> list[Session]:
    """Get sessions visible to user based on ownership"""
    
    # Check if user has view.all permission
    if await has_permission(user_id, "session.view.all"):
        query = select(Session)
    else:
        # Only view.own - filter by assignment
        query = (
            select(Session)
            .where(
                or_(
                    Session.assigned_editor_id == user_id,
                    exists(
                        select(1)
                        .select_from(SessionPhotographer)
                        .where(
                            SessionPhotographer.session_id == Session.id,
                            SessionPhotographer.photographer_id == user_id
                        )
                    )
                )
            )
        )
    
    if status:
        query = query.where(Session.status == status)
    
    result = await db.execute(query)
    return list(result.scalars().all())
```

### 5.2 State-Based Edit Restrictions

**Rule:** Even with `session.edit.pre-assigned`, users cannot edit sessions after 'Assigned' state

**Implementation:**

```python
@router.patch("/sessions/{session_id}")
async def update_session(
    session_id: int,
    updates: SessionUpdate,
    current_user: Annotated[User, Depends(require_permission("session.edit.pre-assigned"))],
    db: AsyncSession = Depends(get_session)
):
    session = await get_session_by_id(db, session_id)
    
    # Additional check for state
    if session.status not in ['Request', 'Negotiation', 'Pre-scheduled', 'Confirmed']:
        # Only admin can edit beyond these states
        if not await has_permission(current_user.id, "session.edit.all"):
            raise HTTPException(
                status_code=403,
                detail="Cannot edit session in current state"
            )
    
    # Continue with update
    ...
```

### 5.3 Client Information Access

**Rule:** Photographers and Editors with `session.view.own` can see LIMITED client info for assigned sessions

**Allowed Fields:**
- `full_name`
- `primary_phone`
- `email`

**Restricted Fields:**
- `secondary_phone`
- `delivery_address`
- `notes`
- `client_type`

**Implementation:**

```python
class ClientBasicInfo(BaseModel):
    """Limited client info for photographers/editors"""
    full_name: str
    primary_phone: str
    email: str

class ClientFullInfo(ClientBasicInfo):
    """Full client info for coordinators/admin"""
    secondary_phone: str | None
    delivery_address: str | None
    notes: str | None
    client_type: str

@router.get("/clients/{client_id}")
async def get_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    client = await get_client_by_id(db, client_id)
    
    # Return different schema based on permissions
    if await has_permission(current_user.id, "client.view"):
        return ClientFullInfo.model_validate(client)
    else:
        # Limited info
        return ClientBasicInfo.model_validate(client)
```

### 5.4 Admin Override

**Rule:** Admins can perform ANY action regardless of state or ownership

**Implementation:**

```python
async def can_perform_action(
    user: User,
    action: str,
    resource: Any
) -> bool:
    """Check if user can perform action, with admin override"""
    
    # Admin bypass
    if await is_admin(user.id):
        return True
    
    # Regular permission check
    return await has_permission(user.id, action)
```

### 5.5 Multiple Roles

**Rule:** A user can have multiple roles (rare but supported)

**Example:** A user could be both Coordinator AND Photographer

**Permission Resolution:** Union of all permissions from all roles

**Implementation:**

```python
async def get_user_permissions(
    db: AsyncSession,
    user_id: int
) -> set[str]:
    """Get all permissions from all user's roles"""
    
    query = """
        SELECT DISTINCT p.code
        FROM permission p
        JOIN role_permission rp ON rp.permission_id = p.id
        JOIN user_role ur ON ur.role_id = rp.role_id
        WHERE ur.user_id = $1
          AND p.status = 'Active'
    """
    
    result = await db.execute(query, [user_id])
    return {row[0] for row in result}
```

---

## 6. Permission Testing Checklist

When implementing a new feature:

- [ ] Identify which permissions are required
- [ ] Add permission check to router via `Depends(require_permission(...))`
- [ ] Handle ownership checks for `.own` permissions
- [ ] Handle state-based restrictions if applicable
- [ ] Test with each role (Admin, Coordinator, Photographer, Editor)
- [ ] Test with user having no roles (should be denied)
- [ ] Test admin override works
- [ ] Document any special permission logic in code comments

---

## 7. Permission Audit

### 7.1 Logging Permission Checks

All permission denials should be logged for security audit:

```python
import logging

logger = logging.getLogger(__name__)

async def check_permission_with_audit(
    user_id: int,
    permission_code: str,
    resource_id: int | None = None
) -> bool:
    has_perm = await check_user_permission(user_id, permission_code)
    
    if not has_perm:
        logger.warning(
            "Permission denied",
            extra={
                "user_id": user_id,
                "permission": permission_code,
                "resource_id": resource_id,
                "timestamp": datetime.utcnow()
            }
        )
    
    return has_perm
```

### 7.2 Sensitive Operations

These operations should be logged even on success:

- User creation/deletion
- Role assignment changes
- Permission changes
- Session cancellations
- Large financial transactions

---

## 8. Future Considerations

### 8.1 Potential New Roles

**Assistant Coordinator:**
- Subset of Coordinator permissions
- Cannot cancel sessions
- Cannot assign resources

**Senior Photographer:**
- All Photographer permissions
- Can view other photographers' schedules
- Can assist in resource planning

### 8.2 Potential New Permissions

**Session Module:**
- `session.view.team` - View sessions for team members
- `session.reassign` - Reassign photographers/editors
- `session.extend-deadline` - Extend payment/changes deadlines

**Financial:**
- `payment.verify` - Verify payments
- `payment.refund` - Process refunds
- `report.financial.detailed` - View detailed financial data

---

**End of Document**

*For database schema details, see `database-schema.sql`*  
*For business rules, see `business-rules.md`*