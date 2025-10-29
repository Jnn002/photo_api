/**
 * Invitation interfaces - TypeScript version of app/invitations/schemas.py
 */

/**
 * InvitationCreate - Request DTO for creating a new invitation
 */
export interface InvitationCreate {
  email: string;
  custom_message?: string | null;
}

/**
 * InvitationResponse - Response DTO for invitation creation
 */
export interface InvitationResponse {
  invitation_url: string;
  email: string;
  expires_at: string;
  message: string;
}

/**
 * InvitationValidateResponse - Response DTO for invitation validation
 */
export interface InvitationValidateResponse {
  is_valid: boolean;
  email: string | null;
  message: string;
}

/**
 * InvitationResend - Request DTO for resending an invitation
 */
export interface InvitationResend {
  email: string;
  custom_message?: string | null;
}
