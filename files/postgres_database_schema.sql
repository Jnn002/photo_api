-- ============================================================================
-- Photography Studio Management System - Database Schema
-- PostgreSQL 17
-- Version: 2.0
-- ============================================================================

-- ============================================================================
-- EXTENSIONS
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- SCHEMA
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS studio;
SET search_path TO studio, public;

-- ============================================================================
-- TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Table: user
-- Description: System collaborators (admin, coordinators, photographers, editors)
-- ----------------------------------------------------------------------------
CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    CONSTRAINT chk_user_status CHECK (status IN ('Active', 'Inactive')),
    CONSTRAINT fk_user_created_by FOREIGN KEY (created_by) REFERENCES "user"(id)
);

COMMENT ON TABLE "user" IS 'System users and collaborators';
COMMENT ON COLUMN "user".status IS 'Active, Inactive';

-- ----------------------------------------------------------------------------
-- Table: role
-- Description: System roles definition
-- ----------------------------------------------------------------------------
CREATE TABLE role (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_role_status CHECK (status IN ('Active', 'Inactive'))
);

COMMENT ON TABLE role IS 'System roles (Admin, Coordinator, Photographer, Editor)';

-- ----------------------------------------------------------------------------
-- Table: user_role
-- Description: Assignment of roles to users (many-to-many)
-- ----------------------------------------------------------------------------
CREATE TABLE user_role (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER NOT NULL,

    CONSTRAINT fk_user_role_user FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_role_role FOREIGN KEY (role_id) REFERENCES role(id),
    CONSTRAINT fk_user_role_assigned_by FOREIGN KEY (assigned_by) REFERENCES "user"(id),
    CONSTRAINT uk_user_role UNIQUE (user_id, role_id)
);

COMMENT ON TABLE user_role IS 'User-role assignments';

-- ----------------------------------------------------------------------------
-- Table: permission
-- Description: Granular permissions definition
-- ----------------------------------------------------------------------------
CREATE TABLE permission (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    module VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_permission_status CHECK (status IN ('Active', 'Inactive'))
);

COMMENT ON TABLE permission IS 'System permissions (session.create, user.edit, etc.)';
COMMENT ON COLUMN permission.module IS 'Module grouping: session, client, user, report, etc.';

-- ----------------------------------------------------------------------------
-- Table: role_permission
-- Description: Permissions assigned to roles (many-to-many)
-- ----------------------------------------------------------------------------
CREATE TABLE role_permission (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER,

    CONSTRAINT fk_role_permission_role FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE CASCADE,
    CONSTRAINT fk_role_permission_permission FOREIGN KEY (permission_id) REFERENCES permission(id) ON DELETE CASCADE,
    CONSTRAINT fk_role_permission_granted_by FOREIGN KEY (granted_by) REFERENCES "user"(id),
    CONSTRAINT uk_role_permission UNIQUE (role_id, permission_id)
);

COMMENT ON TABLE role_permission IS 'Role-permission assignments';

-- ----------------------------------------------------------------------------
-- Table: client
-- Description: Customer information (individuals or institutions)
-- ----------------------------------------------------------------------------
CREATE TABLE client (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    primary_phone VARCHAR(20) NOT NULL,
    secondary_phone VARCHAR(20),
    delivery_address TEXT,
    client_type VARCHAR(20) NOT NULL,
    notes TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    CONSTRAINT chk_client_type CHECK (client_type IN ('Individual', 'Institutional')),
    CONSTRAINT chk_client_status CHECK (status IN ('Active', 'Inactive')),
    CONSTRAINT fk_client_created_by FOREIGN KEY (created_by) REFERENCES "user"(id)
);

COMMENT ON TABLE client IS 'Customer information';
COMMENT ON COLUMN client.client_type IS 'Individual, Institutional';

-- ----------------------------------------------------------------------------
-- Table: item
-- Description: Individual services/products (photos, videos, albums, etc.)
-- ----------------------------------------------------------------------------
CREATE TABLE item (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    item_type VARCHAR(50) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    unit_measure VARCHAR(20) NOT NULL,
    default_quantity INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    CONSTRAINT chk_item_unit_price CHECK (unit_price >= 0),
    CONSTRAINT chk_item_default_quantity CHECK (default_quantity IS NULL OR default_quantity > 0),
    CONSTRAINT chk_item_status CHECK (status IN ('Active', 'Inactive')),
    CONSTRAINT fk_item_created_by FOREIGN KEY (created_by) REFERENCES "user"(id)
);

COMMENT ON TABLE item IS 'Individual services and products';
COMMENT ON COLUMN item.item_type IS 'Digital Photo, Printed Photo, Album, Video, etc.';
COMMENT ON COLUMN item.unit_measure IS 'Unit, Hour, Package';

-- ----------------------------------------------------------------------------
-- Table: package
-- Description: Predefined set of items with special pricing
-- ----------------------------------------------------------------------------
CREATE TABLE package (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    session_type VARCHAR(20) NOT NULL,
    base_price DECIMAL(10,2) NOT NULL,
    estimated_editing_days INTEGER NOT NULL DEFAULT 5,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,

    CONSTRAINT chk_package_session_type CHECK (session_type IN ('Studio', 'External', 'Both')),
    CONSTRAINT chk_package_base_price CHECK (base_price >= 0),
    CONSTRAINT chk_package_editing_days CHECK (estimated_editing_days > 0),
    CONSTRAINT chk_package_status CHECK (status IN ('Active', 'Inactive')),
    CONSTRAINT fk_package_created_by FOREIGN KEY (created_by) REFERENCES "user"(id)
);

COMMENT ON TABLE package IS 'Predefined service packages';
COMMENT ON COLUMN package.session_type IS 'Studio, External, Both';

-- ----------------------------------------------------------------------------
-- Table: package_item
-- Description: Many-to-many relationship between packages and items
-- ----------------------------------------------------------------------------
CREATE TABLE package_item (
    id SERIAL PRIMARY KEY,
    package_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    display_order INTEGER,

    CONSTRAINT chk_package_item_quantity CHECK (quantity > 0),
    CONSTRAINT fk_package_item_package FOREIGN KEY (package_id) REFERENCES package(id) ON DELETE CASCADE,
    CONSTRAINT fk_package_item_item FOREIGN KEY (item_id) REFERENCES item(id),
    CONSTRAINT uk_package_item UNIQUE (package_id, item_id)
);

COMMENT ON TABLE package_item IS 'Package composition';

-- ----------------------------------------------------------------------------
-- Table: room
-- Description: Studio physical spaces
-- ----------------------------------------------------------------------------
CREATE TABLE room (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    capacity INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_room_capacity CHECK (capacity IS NULL OR capacity > 0),
    CONSTRAINT chk_room_status CHECK (status IN ('Active', 'Inactive', 'Maintenance'))
);

COMMENT ON TABLE room IS 'Studio rooms/spaces';

-- ----------------------------------------------------------------------------
-- Table: session
-- Description: Main session information
-- ----------------------------------------------------------------------------
CREATE TABLE session (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    client_id INTEGER NOT NULL,
    session_type VARCHAR(20) NOT NULL,
    status VARCHAR(30) NOT NULL,

    -- Event information
    session_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    location TEXT,
    room_id INTEGER,
    event_description TEXT,
    special_notes TEXT,

    -- Editor assignment
    assigned_editor_id INTEGER,

    -- Financial information
    subtotal DECIMAL(10,2) NOT NULL DEFAULT 0,
    transportation_cost DECIMAL(10,2) DEFAULT 0,
    discount DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) NOT NULL DEFAULT 0,
    deposit_percentage INTEGER NOT NULL DEFAULT 50,
    deposit_amount DECIMAL(10,2),

    -- Time control and dates
    estimated_editing_days INTEGER DEFAULT 5,
    estimated_delivery_date DATE,
    changes_deadline TIMESTAMP,
    payment_deadline TIMESTAMP,

    -- Observations and incidents
    reported_incidents TEXT,
    photographer_observations TEXT,
    editor_observations TEXT,

    -- Audit trail
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    canceled_at TIMESTAMP,
    cancellation_reason TEXT,
    created_by INTEGER NOT NULL,
    updated_by INTEGER,

    CONSTRAINT chk_session_type CHECK (session_type IN ('Studio', 'External')),
    CONSTRAINT chk_session_status CHECK (status IN (
        'Request', 'Negotiation', 'Pre-scheduled', 'Confirmed',
        'Assigned', 'Attended', 'In Editing', 'Ready for Delivery',
        'Completed', 'Canceled'
    )),
    CONSTRAINT chk_session_times CHECK (end_time > start_time),
    CONSTRAINT chk_session_external_location CHECK (
        (session_type = 'External' AND location IS NOT NULL) OR
        (session_type = 'Studio')
    ),
    CONSTRAINT chk_session_studio_room CHECK (
        (session_type = 'Studio' AND room_id IS NOT NULL) OR
        (session_type = 'External')
    ),
    CONSTRAINT chk_session_total CHECK (total >= 0),
    CONSTRAINT chk_session_subtotal CHECK (subtotal >= 0),
    CONSTRAINT chk_session_transportation CHECK (transportation_cost >= 0),
    CONSTRAINT chk_session_discount CHECK (discount >= 0),
    CONSTRAINT chk_session_deposit_pct CHECK (deposit_percentage BETWEEN 0 AND 100),
    CONSTRAINT chk_session_editing_days CHECK (estimated_editing_days IS NULL OR estimated_editing_days > 0),
    CONSTRAINT fk_session_client FOREIGN KEY (client_id) REFERENCES client(id),
    CONSTRAINT fk_session_room FOREIGN KEY (room_id) REFERENCES room(id),
    CONSTRAINT fk_session_editor FOREIGN KEY (assigned_editor_id) REFERENCES "user"(id),
    CONSTRAINT fk_session_created_by FOREIGN KEY (created_by) REFERENCES "user"(id),
    CONSTRAINT fk_session_updated_by FOREIGN KEY (updated_by) REFERENCES "user"(id)
);

COMMENT ON TABLE session IS 'Photography sessions - main information';
COMMENT ON COLUMN session.status IS 'Request, Negotiation, Pre-scheduled, Confirmed, Assigned, Attended, In Editing, Ready for Delivery, Completed, Canceled';
COMMENT ON COLUMN session.deposit_percentage IS 'Percentage of total for deposit (default 50%)';

-- ----------------------------------------------------------------------------
-- Table: session_detail
-- Description: Breakdown of items/services per session (DENORMALIZED)
-- ----------------------------------------------------------------------------
CREATE TABLE session_detail (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    line_type VARCHAR(20) NOT NULL,

    -- Reference to original item/package (for tracking only)
    reference_id INTEGER,
    reference_type VARCHAR(20),

    -- Denormalized data (what was actually sold)
    item_code VARCHAR(50),
    item_name VARCHAR(200) NOT NULL,
    item_description TEXT,

    -- Quantity and pricing
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    line_subtotal DECIMAL(10,2) NOT NULL,

    -- Control
    description_override TEXT,
    display_order INTEGER,
    added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    added_by INTEGER,

    CONSTRAINT chk_session_detail_line_type CHECK (line_type IN ('Package', 'Item')),
    CONSTRAINT chk_session_detail_quantity CHECK (quantity > 0),
    CONSTRAINT chk_session_detail_unit_price CHECK (unit_price >= 0),
    CONSTRAINT chk_session_detail_subtotal CHECK (line_subtotal >= 0),
    CONSTRAINT chk_session_detail_reference_type CHECK (
        reference_type IS NULL OR reference_type IN ('Package', 'Item')
    ),
    CONSTRAINT fk_session_detail_session FOREIGN KEY (session_id) REFERENCES session(id) ON DELETE CASCADE,
    CONSTRAINT fk_session_detail_added_by FOREIGN KEY (added_by) REFERENCES "user"(id)
);

COMMENT ON TABLE session_detail IS 'Session line items - denormalized for historical immutability';
COMMENT ON COLUMN session_detail.reference_id IS 'Original package_id or item_id (informational only, not FK)';
COMMENT ON COLUMN session_detail.line_type IS 'Package or Item';

-- ----------------------------------------------------------------------------
-- Table: session_photographer
-- Description: Assignment of photographers to sessions (many-to-many)
-- ----------------------------------------------------------------------------
CREATE TABLE session_photographer (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    photographer_id INTEGER NOT NULL,
    assignment_date DATE NOT NULL,
    coverage_start_time TIME NOT NULL,
    coverage_end_time TIME NOT NULL,
    is_lead_photographer BOOLEAN DEFAULT FALSE,
    assignment_status VARCHAR(20) DEFAULT 'Assigned',
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL,

    CONSTRAINT chk_session_photographer_times CHECK (coverage_end_time > coverage_start_time),
    CONSTRAINT chk_session_photographer_status CHECK (
        assignment_status IN ('Assigned', 'Confirmed', 'Reassigned')
    ),
    CONSTRAINT fk_session_photographer_session FOREIGN KEY (session_id) REFERENCES session(id) ON DELETE CASCADE,
    CONSTRAINT fk_session_photographer_photographer FOREIGN KEY (photographer_id) REFERENCES "user"(id),
    CONSTRAINT fk_session_photographer_created_by FOREIGN KEY (created_by) REFERENCES "user"(id),
    CONSTRAINT uk_session_photographer UNIQUE (session_id, photographer_id)
);

COMMENT ON TABLE session_photographer IS 'Photographer assignments with coverage times';
COMMENT ON COLUMN session_photographer.coverage_start_time IS 'Includes travel time';
COMMENT ON COLUMN session_photographer.coverage_end_time IS 'Includes return time';

-- ----------------------------------------------------------------------------
-- Table: session_payment
-- Description: Payment records associated with sessions
-- ----------------------------------------------------------------------------
CREATE TABLE session_payment (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    payment_type VARCHAR(20) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    document_number VARCHAR(100) NOT NULL,
    payment_method VARCHAR(50),
    payment_date DATE NOT NULL,
    notes TEXT,
    payment_status VARCHAR(20) DEFAULT 'Verified',
    registered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    registered_by INTEGER NOT NULL,
    verified_by INTEGER,

    CONSTRAINT chk_session_payment_type CHECK (payment_type IN ('Deposit', 'Balance', 'Refund')),
    CONSTRAINT chk_session_payment_amount CHECK (
        (payment_type IN ('Deposit', 'Balance') AND amount > 0) OR
        (payment_type = 'Refund')
    ),
    CONSTRAINT chk_session_payment_status CHECK (
        payment_status IN ('Pending', 'Verified', 'Rejected')
    ),
    CONSTRAINT fk_session_payment_session FOREIGN KEY (session_id) REFERENCES session(id) ON DELETE CASCADE,
    CONSTRAINT fk_session_payment_registered_by FOREIGN KEY (registered_by) REFERENCES "user"(id),
    CONSTRAINT fk_session_payment_verified_by FOREIGN KEY (verified_by) REFERENCES "user"(id)
);

COMMENT ON TABLE session_payment IS 'Payment records (deposit, balance, refund)';
COMMENT ON COLUMN session_payment.payment_type IS 'Deposit, Balance, Refund';

-- ----------------------------------------------------------------------------
-- Table: session_status_history
-- Description: Audit trail of session status changes
-- ----------------------------------------------------------------------------
CREATE TABLE session_status_history (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    previous_status VARCHAR(30),
    new_status VARCHAR(30) NOT NULL,
    reason TEXT,
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by INTEGER NOT NULL,

    CONSTRAINT fk_session_status_history_session FOREIGN KEY (session_id) REFERENCES session(id) ON DELETE CASCADE,
    CONSTRAINT fk_session_status_history_changed_by FOREIGN KEY (changed_by) REFERENCES "user"(id)
);

COMMENT ON TABLE session_status_history IS 'Audit trail for session status changes';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- User indexes
CREATE INDEX idx_user_email ON "user"(email);
CREATE INDEX idx_user_status ON "user"(status);

-- Role indexes
CREATE INDEX idx_role_name ON role(name);
CREATE INDEX idx_role_status ON role(status);

-- User Role indexes
CREATE INDEX idx_user_role_user ON user_role(user_id);
CREATE INDEX idx_user_role_role ON user_role(role_id);

-- Permission indexes
CREATE INDEX idx_permission_code ON permission(code);
CREATE INDEX idx_permission_module ON permission(module);
CREATE INDEX idx_permission_status ON permission(status);

-- Role Permission indexes
CREATE INDEX idx_role_permission_role ON role_permission(role_id);
CREATE INDEX idx_role_permission_permission ON role_permission(permission_id);

-- Client indexes
CREATE INDEX idx_client_email ON client(email);
CREATE INDEX idx_client_type ON client(client_type);
CREATE INDEX idx_client_status ON client(status);
CREATE INDEX idx_client_full_name ON client(full_name);

-- Item indexes
CREATE INDEX idx_item_code ON item(code);
CREATE INDEX idx_item_type ON item(item_type);
CREATE INDEX idx_item_status ON item(status);

-- Package indexes
CREATE INDEX idx_package_code ON package(code);
CREATE INDEX idx_package_session_type ON package(session_type);
CREATE INDEX idx_package_status ON package(status);

-- Package Item indexes
CREATE INDEX idx_package_item_package ON package_item(package_id);
CREATE INDEX idx_package_item_item ON package_item(item_id);

-- Room indexes
CREATE INDEX idx_room_code ON room(code);
CREATE INDEX idx_room_status ON room(status);

-- Session indexes
CREATE INDEX idx_session_code ON session(code);
CREATE INDEX idx_session_client ON session(client_id);
CREATE INDEX idx_session_status ON session(status);
CREATE INDEX idx_session_type ON session(session_type);
CREATE INDEX idx_session_date ON session(session_date);
CREATE INDEX idx_session_editor ON session(assigned_editor_id);
CREATE INDEX idx_session_room ON session(room_id);
CREATE INDEX idx_session_created_at ON session(created_at);

-- Session Detail indexes
CREATE INDEX idx_session_detail_session ON session_detail(session_id);
CREATE INDEX idx_session_detail_line_type ON session_detail(line_type);
CREATE INDEX idx_session_detail_reference ON session_detail(reference_type, reference_id);

-- Session Photographer indexes
CREATE INDEX idx_session_photographer_session ON session_photographer(session_id);
CREATE INDEX idx_session_photographer_photographer ON session_photographer(photographer_id);
CREATE INDEX idx_session_photographer_date ON session_photographer(assignment_date);
CREATE INDEX idx_session_photographer_coverage ON session_photographer(
    assignment_date, coverage_start_time, coverage_end_time
);

-- Session Payment indexes
CREATE INDEX idx_session_payment_session ON session_payment(session_id);
CREATE INDEX idx_session_payment_type ON session_payment(payment_type);
CREATE INDEX idx_session_payment_date ON session_payment(payment_date);
CREATE INDEX idx_session_payment_document ON session_payment(document_number);

-- Session Status History indexes
CREATE INDEX idx_session_status_history_session ON session_status_history(session_id);
CREATE INDEX idx_session_status_history_date ON session_status_history(changed_at);
CREATE INDEX idx_session_status_history_status ON session_status_history(previous_status, new_status);

-- ============================================================================
-- TRIGGERS FOR updated_at
-- ============================================================================

-- Generic function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables with updated_at column
CREATE TRIGGER trigger_user_updated_at
    BEFORE UPDATE ON "user"
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_role_updated_at
    BEFORE UPDATE ON role
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_permission_updated_at
    BEFORE UPDATE ON permission
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_client_updated_at
    BEFORE UPDATE ON client
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_item_updated_at
    BEFORE UPDATE ON item
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_package_updated_at
    BEFORE UPDATE ON package
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_room_updated_at
    BEFORE UPDATE ON room
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_session_updated_at
    BEFORE UPDATE ON session
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SEED DATA
-- ============================================================================

-- Insert default roles
INSERT INTO role (name, description, status) VALUES
    ('Admin', 'System administrator with full access', 'Active'),
    ('Coordinator', 'Session coordinator and client manager', 'Active'),
    ('Photographer', 'Photography service provider', 'Active'),
    ('Editor', 'Photo and video editor', 'Active');

-- Insert sample permissions (session module)
INSERT INTO permission (code, name, description, module, status) VALUES
    ('session.create', 'Create Session', 'Create new photography sessions', 'session', 'Active'),
    ('session.view.own', 'View Own Sessions', 'View sessions assigned to user', 'session', 'Active'),
    ('session.view.all', 'View All Sessions', 'View all sessions in system', 'session', 'Active'),
    ('session.edit.pre-assigned', 'Edit Pre-Assigned Sessions', 'Edit sessions before Assigned status', 'session', 'Active'),
    ('session.edit.all', 'Edit All Sessions', 'Edit sessions in any status', 'session', 'Active'),
    ('session.delete', 'Delete Session', 'Delete sessions', 'session', 'Active'),
    ('session.assign-resources', 'Assign Resources', 'Assign photographers and rooms to sessions', 'session', 'Active'),
    ('session.cancel', 'Cancel Session', 'Cancel sessions', 'session', 'Active'),
    ('session.mark-attended', 'Mark as Attended', 'Mark session as attended (photographer action)', 'session', 'Active'),
    ('session.mark-ready', 'Mark as Ready', 'Mark session as ready for delivery (editor action)', 'session', 'Active');

-- Insert sample permissions (client module)
INSERT INTO permission (code, name, description, module, status) VALUES
    ('client.create', 'Create Client', 'Create new clients', 'client', 'Active'),
    ('client.view', 'View Clients', 'View client information', 'client', 'Active'),
    ('client.edit', 'Edit Client', 'Edit client information', 'client', 'Active'),
    ('client.delete', 'Delete Client', 'Delete clients', 'client', 'Active');

-- Insert sample permissions (catalog module)
INSERT INTO permission (code, name, description, module, status) VALUES
    ('item.create', 'Create Item', 'Create new items', 'catalog', 'Active'),
    ('item.edit', 'Edit Item', 'Edit items', 'catalog', 'Active'),
    ('item.delete', 'Delete Item', 'Delete items', 'catalog', 'Active'),
    ('package.create', 'Create Package', 'Create new packages', 'catalog', 'Active'),
    ('package.edit', 'Edit Package', 'Edit packages', 'catalog', 'Active'),
    ('package.delete', 'Delete Package', 'Delete packages', 'catalog', 'Active');

-- Insert sample permissions (user module)
INSERT INTO permission (code, name, description, module, status) VALUES
    ('user.create', 'Create User', 'Create new users', 'user', 'Active'),
    ('user.view', 'View Users', 'View user information', 'user', 'Active'),
    ('user.edit', 'Edit User', 'Edit user information', 'user', 'Active'),
    ('user.delete', 'Delete User', 'Delete users', 'user', 'Active'),
    ('user.assign-role', 'Assign Role', 'Assign roles to users', 'user', 'Active');

-- Insert sample permissions (report module)
INSERT INTO permission (code, name, description, module, status) VALUES
    ('report.session', 'Session Reports', 'View session reports', 'report', 'Active'),
    ('report.financial', 'Financial Reports', 'View financial reports', 'report', 'Active'),
    ('report.performance', 'Performance Reports', 'View performance reports', 'report', 'Active');

-- Insert sample permissions (system module)
INSERT INTO permission (code, name, description, module, status) VALUES
    ('system.settings', 'System Settings', 'Manage system settings', 'system', 'Active'),
    ('system.audit-log', 'Audit Log', 'View system audit logs', 'system', 'Active');

-- ============================================================================
-- USEFUL QUERIES (commented out - for reference)
-- ============================================================================

-- Check room availability
/*
SELECT EXISTS (
    SELECT 1
    FROM session
    WHERE room_id = $1
        AND session_date = $2
        AND (start_time, end_time) OVERLAPS ($3::TIME, $4::TIME)
        AND status NOT IN ('Canceled')
) AS is_occupied;
*/

-- Check photographer availability
/*
SELECT EXISTS (
    SELECT 1
    FROM session_photographer sp
    JOIN session s ON s.id = sp.session_id
    WHERE sp.photographer_id = $1
        AND sp.assignment_date = $2
        AND (sp.coverage_start_time, sp.coverage_end_time) OVERLAPS ($3::TIME, $4::TIME)
        AND s.status NOT IN ('Canceled')
) AS is_busy;
*/

-- Get user permissions
/*
SELECT DISTINCT p.code, p.name, p.module
FROM permission p
JOIN role_permission rp ON rp.permission_id = p.id
JOIN user_role ur ON ur.role_id = rp.role_id
WHERE ur.user_id = $1
    AND p.status = 'Active';
*/

-- Get session with all details
/*
SELECT
    s.*,
    c.full_name AS client_name,
    c.email AS client_email,
    u.full_name AS editor_name,
    r.name AS room_name,
    (SELECT json_agg(
        json_build_object(
            'id', sd.id,
            'item_name', sd.item_name,
            'quantity', sd.quantity,
            'unit_price', sd.unit_price,
            'line_subtotal', sd.line_subtotal
        ) ORDER BY sd.display_order
    ) FROM session_detail sd WHERE sd.session_id = s.id) AS details,
    (SELECT json_agg(
        json_build_object(
            'photographer_id', sp.photographer_id,
            'photographer_name', pu.full_name,
            'coverage_start', sp.coverage_start_time,
            'coverage_end', sp.coverage_end_time
        )
    ) FROM session_photographer sp
    JOIN "user" pu ON pu.id = sp.photographer_id
    WHERE sp.session_id = s.id) AS photographers
FROM session s
JOIN client c ON c.id = s.client_id
LEFT JOIN "user" u ON u.id = s.assigned_editor_id
LEFT JOIN room r ON r.id = s.room_id
WHERE s.id = $1;
*/

