/**
 * User with roles interface for frontend consumption
 *
 * This interface represents the UserWithRoles schema from the backend,
 * used in paginated responses when listing users with their assigned roles.
 */

export interface Role {
  id: number;
  name: string;
  description: string | null;
  status: 'ACTIVE' | 'INACTIVE';
  created_at: string; // ISO 8601 datetime
  updated_at: string; // ISO 8601 datetime
}

export interface UserWithRoles {
  id: number;
  full_name: string;
  email: string;
  phone: string | null;
  status: 'ACTIVE' | 'INACTIVE';
  created_at: string; // ISO 8601 datetime
  updated_at: string; // ISO 8601 datetime
  roles: Role[];
}

export interface PaginatedUsersWithRoles {
  items: UserWithRoles[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}
