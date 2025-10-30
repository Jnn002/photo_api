/**
 * TypeScript interfaces for Photographer module
 *
 * These interfaces correspond 1:1 with the Pydantic schemas in
 * app/photographers/schemas.py
 *
 * Generated for Photography Studio Management System API
 */

// ==================== Enums ====================

/**
 * Session status enum
 */
export enum SessionStatus {
  REQUEST = 'REQUEST',
  NEGOTIATION = 'NEGOTIATION',
  PRE_SCHEDULED = 'PRE_SCHEDULED',
  CONFIRMED = 'CONFIRMED',
  ASSIGNED = 'ASSIGNED',
  ATTENDED = 'ATTENDED',
  IN_EDITING = 'IN_EDITING',
  READY_FOR_DELIVERY = 'READY_FOR_DELIVERY',
  COMPLETED = 'COMPLETED',
  CANCELED = 'CANCELED',
}

/**
 * Session type enum
 */
export enum SessionType {
  STUDIO = 'STUDIO',
  EXTERNAL = 'EXTERNAL',
}

/**
 * Line type enum (for session details/items)
 */
export enum LineType {
  ITEM = 'Item',
  PACKAGE = 'Package',
  ADJUSTMENT = 'Adjustment',
}

/**
 * Reference type enum
 */
export enum ReferenceType {
  ITEM = 'Item',
  PACKAGE = 'Package',
}

/**
 * Photographer role enum
 */
export enum PhotographerRole {
  LEAD = 'Lead',
  ASSISTANT = 'Assistant',
  SPECIALIST = 'Specialist',
}

/**
 * Delivery method enum
 */
export enum DeliveryMethod {
  DIGITAL = 'Digital',
  PHYSICAL = 'Physical',
  BOTH = 'Both',
}

// ==================== Client Info ====================

/**
 * Basic client information for photographers
 *
 * Limited to essential contact information only.
 * Does NOT include: secondary_phone, delivery_address, notes, client_type
 */
export interface ClientBasicInfo {
  id: number;
  full_name: string;
  email: string;
  primary_phone: string;
}

// ==================== Session Details ====================

/**
 * Basic session line item information
 *
 * Shows what items/packages are included in the session.
 * Excludes pricing information.
 */
export interface SessionDetailBasicInfo {
  id: number;
  line_type: LineType;
  reference_type: ReferenceType | null;
  item_code: string;
  item_name: string;
  item_description: string | null;
  quantity: number;
}

// ==================== Photographer Assignments ====================

/**
 * Information about a photographer assigned to a session
 */
export interface PhotographerAssignmentInfo {
  id: number;
  photographer_id: number;
  photographer_name: string;
  role: PhotographerRole | null;
  assigned_at: string; // ISO 8601 datetime
  attended: boolean;
  attended_at: string | null; // ISO 8601 datetime
}

/**
 * Team of photographers assigned to a session
 */
export interface SessionTeamInfo {
  session_id: number;
  photographers: PhotographerAssignmentInfo[];
}

// ==================== Session Views ====================

/**
 * Compact session info for list views
 *
 * Used in "My Assignments" list to show photographer's sessions at a glance.
 */
export interface SessionPhotographerListItem {
  id: number;
  client_name: string;
  session_type: SessionType;
  session_date: string; // ISO 8601 date (YYYY-MM-DD)
  session_time: string | null; // HH:MM format
  estimated_duration_hours: number | null;
  location: string | null;
  status: SessionStatus;
  my_role: PhotographerRole | null;
  my_attended: boolean;
  my_attended_at: string | null; // ISO 8601 datetime
}

/**
 * Detailed session information for photographers
 *
 * Complete view of a session with all information needed to prepare
 * and execute the photography session.
 */
export interface SessionPhotographerView {
  // Core session info
  id: number;
  session_type: SessionType;
  session_date: string; // ISO 8601 date (YYYY-MM-DD)
  session_time: string | null; // HH:MM format
  estimated_duration_hours: number | null;
  location: string | null;
  room_id: number | null;
  status: SessionStatus;

  // Client info (limited)
  client: ClientBasicInfo;

  // Session requirements
  client_requirements: string | null;

  // Delivery info (for context)
  delivery_method: DeliveryMethod | null;
  delivery_deadline: string | null; // ISO 8601 date

  // Session items (what to shoot)
  details: SessionDetailBasicInfo[];

  // My assignment info
  my_assignment_id: number;
  my_role: PhotographerRole | null;
  my_assigned_at: string; // ISO 8601 datetime
  my_attended: boolean;
  my_attended_at: string | null; // ISO 8601 datetime
  my_notes: string | null;

  // Timestamps
  created_at: string; // ISO 8601 datetime
  updated_at: string; // ISO 8601 datetime
}

// ==================== Action DTOs ====================

/**
 * Request body for marking session as attended
 */
export interface MarkAttendedRequest {
  /**
   * Mark as attended (true) or unmark (false)
   * @default true
   */
  attended: boolean;

  /**
   * Optional notes or observations about the session
   * @maxLength 1000
   */
  notes?: string | null;
}

// ==================== Statistics ====================

/**
 * Statistics and metrics for a photographer
 */
export interface PhotographerStats {
  // Assignment counts
  total_assignments: number;
  upcoming_sessions: number;
  attended_sessions: number;
  pending_sessions: number;

  // Recent assignments
  next_session_date: string | null; // ISO 8601 date
  sessions_this_week: number;

  // All-time stats
  total_sessions_completed: number;
}

// ==================== API Response Types ====================

/**
 * Generic error response
 */
export interface ApiError {
  detail: string;
  error_code?: string;
}

/**
 * Paginated response wrapper (if needed for future pagination)
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

// ==================== Type Guards ====================

/**
 * Type guard to check if a value is a valid SessionStatus
 */
export function isSessionStatus(value: string): value is SessionStatus {
  return Object.values(SessionStatus).includes(value as SessionStatus);
}

/**
 * Type guard to check if a value is a valid PhotographerRole
 */
export function isPhotographerRole(value: string): value is PhotographerRole {
  return Object.values(PhotographerRole).includes(value as PhotographerRole);
}

// ==================== Utility Types ====================

/**
 * Make all properties of T optional except K
 */
export type PartialExcept<T, K extends keyof T> = Partial<T> & Pick<T, K>;

/**
 * Extract date string from datetime string
 */
export type DateString = string;

/**
 * Extract time string in HH:MM format
 */
export type TimeString = string;
