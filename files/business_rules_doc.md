# Business Rules - Photography Studio Management System

**Version:** 1.0  
**Last Updated:** 2025-01-07

This document defines the core business rules, validations, and workflows for the Photography Studio Management System. All implementations must follow these rules strictly.

---

## Table of Contents

1. [Session State Machine](#1-session-state-machine)
2. [Date Calculations](#2-date-calculations)
3. [Availability Validations](#3-availability-validations)
4. [Cancellation & Refund Rules](#4-cancellation--refund-rules)
5. [Financial Rules](#5-financial-rules)
6. [Package Management](#6-package-management)
7. [Configuration Constants](#7-configuration-constants)

---

## 1. Session State Machine

### 1.1 Valid States

```
Request → Negotiation → Pre-scheduled → Confirmed → Assigned → 
Attended → In Editing → Ready for Delivery → Completed

Any state (except Completed) → Canceled
```

### 1.2 State Transition Rules

| From State | To State | Executor | Conditions |
|------------|----------|----------|------------|
| **Request** | Negotiation | Coordinator, Admin | Initial evaluation positive |
| **Request** | Canceled | Coordinator, Admin | Evaluation negative |
| **Negotiation** | Pre-scheduled | Coordinator, Admin | Agreement reached, has items, total > 0 |
| **Negotiation** | Canceled | Coordinator, Admin | Negotiation failed |
| **Pre-scheduled** | Confirmed | Coordinator, Admin | Deposit payment verified |
| **Pre-scheduled** | Negotiation | Coordinator, Admin | Client requests changes |
| **Pre-scheduled** | Canceled | System, Coordinator, Admin | Payment deadline expired |
| **Confirmed** | Assigned | System, Coordinator, Admin | `changes_deadline` passed + resources assigned |
| **Confirmed** | Negotiation | Coordinator, Admin | Within `changes_deadline` |
| **Confirmed** | Canceled | Coordinator, Admin | Force majeure or client cancels |
| **Assigned** | Attended | Photographer (assigned) | Session date has passed |
| **Assigned** | Canceled | Coordinator, Admin | Force majeure by company |
| **Attended** | In Editing | Editor | Editor takes session for processing |
| **In Editing** | Ready for Delivery | Editor (assigned) | Editing completed |
| **Ready for Delivery** | Completed | Coordinator, Admin | Material delivered to client |

### 1.3 Transition Validation Rules

#### Request → Negotiation
- Session must have valid client
- Session date must be in the future
- Session type must be set
- User has permission: `session.edit.pre-assigned`

#### Negotiation → Pre-scheduled
- Session must have at least one item in `session_detail`
- `total` must be greater than 0
- User has permission: `session.edit.pre-assigned`

**Actions on transition:**
- Calculate `payment_deadline` = current timestamp + PAYMENT_DEADLINE_DAYS
- Calculate `deposit_amount` = `total` × (`deposit_percentage` / 100)

#### Pre-scheduled → Confirmed
- Deposit payment must be verified (record in `session_payment`)
- Payment amount ≥ `deposit_amount`
- Current timestamp ≤ `payment_deadline`
- User has permission: `session.edit.pre-assigned`

**Actions on transition:**
- Create `session_payment` record (type='Deposit')
- Clear `payment_deadline`
- Calculate `changes_deadline` = `session_date` - CHANGES_DEADLINE_DAYS (23:59:59)
- Send confirmation email to client
- Create entry in `session_status_history`

#### Confirmed → Assigned
- Current timestamp > `changes_deadline`
- At least one photographer assigned in `session_photographer`
- If `session_type` = 'Studio': `room_id` must be set
- User has permission: `session.assign-resources`

**Actions on transition:**
- Calculate `estimated_delivery_date` = `session_date` + `estimated_editing_days`
- Notify photographers via dashboard

#### Assigned → Attended
- Current date ≥ `session_date`
- User is assigned photographer OR has `session.edit.all` permission
- User has permission: `session.mark-attended`

**Actions on transition:**
- Session becomes visible to editors
- Photographer can add observations/incidents

#### Attended → In Editing
- `assigned_editor_id` must be NULL (no editor assigned yet)
- User has role 'Editor'
- User has permission: `session.view.own`

**Actions on transition:**
- Set `assigned_editor_id` = current user
- Editor can adjust `estimated_delivery_date` if needed

#### In Editing → Ready for Delivery
- User must be the assigned editor
- User has permission: `session.mark-ready`

**Actions on transition:**
- Send "material ready" email to client
- Notify coordinators via dashboard

#### Ready for Delivery → Completed
- Optional: verify total payments ≥ `total`
- User has permission: `session.edit.all`

**Actions on transition:**
- Session becomes read-only (except for admins)

#### Any State → Canceled
- State must NOT be 'Completed' or already 'Canceled'
- `cancellation_reason` must be provided
- User has permission: `session.cancel`

**Actions on transition:**
- Set `canceled_at` = current timestamp
- Calculate refund (see section 4)
- Create `session_payment` record if refund applies (type='Refund')
- Free assigned resources (photographers, rooms)
- Send cancellation email to client

### 1.4 Reopening Negotiation from Confirmed States

When transitioning from 'Pre-scheduled' or 'Confirmed' back to 'Negotiation':

**From Pre-scheduled:**
- Resets `payment_deadline` counter when returning to 'Pre-scheduled'

**From Confirmed:**
- Resets `changes_deadline` counter when returning to 'Confirmed'
- Only allowed if within original `changes_deadline`

---

## 2. Date Calculations

### 2.1 Payment Deadline

**Formula:**
```
payment_deadline = created_at + PAYMENT_DEADLINE_DAYS days
Time: 23:59:59 on the deadline day
```

**Applied when:**
- Transitioning to 'Pre-scheduled'

**Auto-cancellation:**
- Daily job checks for sessions in 'Pre-scheduled' with expired `payment_deadline`
- Automatically transitions to 'Canceled' with reason: "Payment deadline expired"

### 2.2 Changes Deadline

**Formula:**
```
changes_deadline = session_date - CHANGES_DEADLINE_DAYS days
Time: 23:59:59 on the deadline day
```

**Applied when:**
- Transitioning to 'Confirmed'

**Auto-assignment:**
- Daily job checks for sessions in 'Confirmed' with expired `changes_deadline`
- If resources assigned and requirements met: auto-transition to 'Assigned'
- If resources NOT assigned: alert coordinators

### 2.3 Estimated Delivery Date

**Formula:**
```
estimated_delivery_date = session_date + estimated_editing_days
```

**Applied when:**
- Transitioning to 'Assigned' (initial calculation)
- Can be adjusted by editor during 'In Editing' state

---

## 3. Availability Validations

### 3.1 Room Availability (Studio Sessions)

**Rule:** A room can only have ONE active session at a time for any overlapping time period.

**Validation Logic:**
```python
def is_room_available(
    room_id: int,
    session_date: date,
    start_time: time,
    end_time: time,
    exclude_session_id: int | None = None
) -> bool:
    """
    Returns True if room is available, False if occupied.
    
    Check for ANY session where:
    - Same room_id
    - Same session_date
    - Times overlap: (start_time, end_time) OVERLAPS (existing_start, existing_end)
    - Status NOT IN ('Canceled', 'Completed')
    - Different session_id (if excluding)
    """
```

**When to validate:**
- Creating a Studio session
- Editing session date/time
- Assigning/changing room

**Error if unavailable:**
- HTTP 409 Conflict
- Error code: `ROOM_NOT_AVAILABLE`
- Include conflicting session details in response

### 3.2 Photographer Availability

**Rule:** A photographer can only be assigned to ONE session at a time for any overlapping coverage period.

**Coverage time includes:**
- Travel time to location (if external)
- Event time
- Return time (if external)

**Validation Logic:**
```python
def is_photographer_available(
    photographer_id: int,
    assignment_date: date,
    coverage_start_time: time,  # Includes travel
    coverage_end_time: time,    # Includes return
    exclude_session_id: int | None = None
) -> bool:
    """
    Returns True if photographer is available, False if busy.
    
    Check for ANY assignment where:
    - Same photographer_id
    - Same assignment_date
    - Times overlap: (coverage_start, coverage_end) OVERLAPS (existing_start, existing_end)
    - Associated session status NOT IN ('Canceled', 'Completed')
    - Different session_id (if excluding)
    """
```

**When to validate:**
- Assigning photographer to session
- Reasigning photographer
- Editing session date/time with photographers already assigned

**Error if unavailable:**
- HTTP 409 Conflict
- Error code: `PHOTOGRAPHER_NOT_AVAILABLE`
- Include conflicting assignment details

### 3.3 Session Date Validation

**Rule:** Session date cannot be in the past (except for retroactive entry)

**Logic:**
```python
def is_valid_session_date(session_date: date, current_status: str) -> bool:
    """
    Returns True if date is valid.
    
    - If status IN ('Attended', 'In Editing', 'Ready for Delivery', 'Completed'):
      Allow past dates (retroactive entry)
    - Otherwise: session_date >= today
    """
```

---

## 4. Cancellation & Refund Rules

### 4.1 Refund Matrix

| Status at Cancellation | Payment Made | Initiator | Refund % | Refund Amount |
|------------------------|--------------|-----------|----------|---------------|
| Request | None | Any | N/A | Q 0.00 |
| Negotiation | None | Any | N/A | Q 0.00 |
| Pre-scheduled | None | Any | N/A | Q 0.00 |
| Confirmed (within `changes_deadline`) | Deposit | Client | 100% | Full deposit |
| Confirmed (after `changes_deadline`) | Deposit | Client | 50% | 50% of deposit |
| Assigned | Deposit | Company/Force Majeure | 100% | Full deposit |
| Assigned | Deposit | Client | 0% | Q 0.00 |
| Attended or later | Any | Any | 0% | Q 0.00 |

### 4.2 Refund Calculation Logic

```python
def calculate_refund(
    session_status: str,
    total_paid: Decimal,
    initiator: str,  # 'client', 'company', 'system', 'force_majeure'
    changes_deadline: datetime | None
) -> tuple[Decimal, str]:
    """
    Returns (refund_amount, reason)
    
    Logic:
    1. If total_paid == 0: return (0, "No payments made")
    
    2. If status in ('Request', 'Negotiation', 'Pre-scheduled'):
       return (0, "Cancellation before confirmation")
    
    3. If status == 'Confirmed':
       if current_time <= changes_deadline:
           return (total_paid, "Within changes deadline")
       else:
           return (total_paid * 0.5, "After changes deadline - 50% refund")
    
    4. If status == 'Assigned':
       if initiator in ('company', 'force_majeure'):
           return (total_paid, "Company cannot fulfill - full refund")
       else:
           return (0, "Client cancellation after assignment - no refund")
    
    5. If status in ('Attended', 'In Editing', 'Ready for Delivery', 'Completed'):
       return (0, "Service already provided - no refund")
    """
```

### 4.3 Cancellation Process

1. Validate cancellation is allowed (not Completed, not already Canceled)
2. Calculate refund amount
3. **Begin transaction:**
   - Update `session.status` = 'Canceled'
   - Set `session.canceled_at` = current timestamp
   - Set `session.cancellation_reason`
   - If refund > 0: Create `session_payment` record (type='Refund')
   - Create `session_status_history` entry
4. **Commit transaction**
5. Send cancellation email to client (outside transaction)

---

## 5. Financial Rules

### 5.1 Deposit Calculation

```
deposit_amount = total × (deposit_percentage / 100)

Default: deposit_percentage = 50
```

### 5.2 Total Calculation

```
subtotal = SUM(session_detail.line_subtotal)
total = subtotal + transportation_cost - discount
```

**Rules:**
- `subtotal` must match sum of all `session_detail.line_subtotal`
- `total` must be ≥ 0
- `transportation_cost` must be ≥ 0
- `discount` must be ≥ 0

### 5.3 Payment Validation

**Rule:** Total payments (Deposit + Balance) cannot exceed `session.total`

```python
def validate_payments(session_id: int) -> dict:
    """
    Calculate:
    - total_paid = SUM(amount WHERE type IN ('Deposit', 'Balance'))
    - total_refunded = SUM(amount WHERE type = 'Refund')
    - net_paid = total_paid - total_refunded
    - remaining_balance = session.total - net_paid
    
    Validation:
    - net_paid must be <= session.total
    """
```

### 5.4 Payment Types

- **Deposit:** Initial payment to confirm session (usually 50%)
- **Balance:** Final payment (remaining amount)
- **Refund:** Money returned to client on cancellation

**Rules:**
- Only ONE deposit payment per session
- Balance payments allowed only after deposit
- Refund only when deposit/balance exists

---

## 6. Package Management

### 6.1 Package Explosion (Critical Pattern)

When a package is added to a session, it must be "exploded" into individual items:

**Process:**
1. Retrieve package with all its items (`package_item` relationships)
2. For EACH item in the package:
   - Create a `session_detail` record with:
     - `line_type` = 'Item'
     - `reference_id` = package.id (track original package)
     - `reference_type` = 'Package'
     - `item_code` = item.code (denormalized)
     - `item_name` = item.name (denormalized)
     - `item_description` = item.description (denormalized)
     - `quantity` = package_item.quantity
     - `unit_price` = item.unit_price (at time of sale)
     - `line_subtotal` = quantity × unit_price
3. Recalculate session totals

**Why denormalize?**
- Historical immutability: changing package definition doesn't affect past sessions
- Simple reporting: just sum `line_subtotal`
- Clear audit trail: see exactly what was sold

### 6.2 Adding Individual Items

When adding an item NOT from a package:

**Process:**
1. Create a `session_detail` record with:
   - `line_type` = 'Item'
   - `reference_id` = item.id
   - `reference_type` = 'Item'
   - All denormalized fields (code, name, description, price)
2. Recalculate session totals

### 6.3 Modification Rules

**Can modify `session_detail` when:**
- Status IN ('Request', 'Negotiation', 'Pre-scheduled')
- Status = 'Confirmed' AND within `changes_deadline`

**Cannot modify when:**
- Status = 'Confirmed' AND after `changes_deadline`
- Status IN ('Assigned', 'Attended', 'In Editing', 'Ready for Delivery', 'Completed', 'Canceled')

**Exception:** Admins can modify in any state (audit logged)

### 6.4 Transportation Cost

**Rule:** Transportation cost is added manually for external sessions in remote locations

**Application:**
- Only for `session_type` = 'External'
- Added as flat amount to `session.transportation_cost`
- Included in `total` calculation
- Can only be modified in states where `session_detail` can be modified

---

## 7. Configuration Constants

These values are configurable via environment variables:

```python
# Time limits
PAYMENT_DEADLINE_DAYS = 5        # Days to pay deposit (Pre-scheduled → Confirmed)
CHANGES_DEADLINE_DAYS = 7        # Days before session to allow changes (Confirmed)
DEFAULT_EDITING_DAYS = 5         # Default estimated editing time

# Financial
DEFAULT_DEPOSIT_PERCENTAGE = 50  # Default deposit percentage

# Refund percentages (see matrix in section 4.1)
REFUND_WITHIN_DEADLINE = 100     # %
REFUND_AFTER_DEADLINE = 50       # %
REFUND_FORCE_MAJEURE = 100       # %
REFUND_CLIENT_AFTER_ASSIGNED = 0 # %

# Transportation
REMOTE_TRANSPORTATION_COST = 200.00  # Fixed cost for remote locations (Quetzales)

# Editor workload (optional limit)
MAX_CONCURRENT_EDITING_SESSIONS = 10
```

---

## 8. Email Notifications

### 8.1 Automated Emails to Clients

| Trigger | Template | Recipient |
|---------|----------|-----------|
| Pre-scheduled → Confirmed | `confirmation_email` | Client |
| In Editing → Ready for Delivery | `material_ready_email` | Client |
| Any state → Canceled | `cancellation_email` | Client |
| 1 day before `payment_deadline` | `payment_reminder_email` | Client |

### 8.2 Dashboard Notifications to Staff

| Trigger | Notification | Recipient |
|---------|--------------|-----------|
| Photographer assigned | "New session assigned" | Assigned photographer(s) |
| Photographer reassigned | "Assignment changed" | Old & new photographer |
| Session attended | "New session for editing" | All editors |
| Session ready | "Material ready for delivery" | Coordinators |

---

## 9. Scheduled Jobs

### 9.1 Auto-cancel Unpaid Sessions

**Schedule:** Daily at 00:00  
**Logic:**
```sql
UPDATE session 
SET 
  status = 'Canceled',
  canceled_at = CURRENT_TIMESTAMP,
  cancellation_reason = 'Payment deadline expired - no deposit received'
WHERE status = 'Pre-scheduled'
  AND payment_deadline < CURRENT_TIMESTAMP;
```

### 9.2 Auto-assign Confirmed Sessions

**Schedule:** Daily at 00:00  
**Logic:**
```sql
UPDATE session 
SET status = 'Assigned'
WHERE status = 'Confirmed'
  AND changes_deadline < CURRENT_TIMESTAMP
  AND EXISTS (
    SELECT 1 FROM session_photographer 
    WHERE session_photographer.session_id = session.id
  )
  AND (
    session_type = 'External' OR
    (session_type = 'Studio' AND room_id IS NOT NULL)
  );
```

### 9.3 Payment Reminders

**Schedule:** Daily at 09:00  
**Logic:**
```sql
SELECT s.*, c.email, c.full_name
FROM session s
JOIN client c ON c.id = s.client_id
WHERE s.status = 'Pre-scheduled'
  AND s.payment_deadline BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '1 day';
```
Send `payment_reminder_email` to each.

### 9.4 Data Integrity Validation

**Schedule:** Daily at 02:00  
**Checks:**
- Sessions with inconsistent totals (subtotal vs session_detail sum)
- Sessions in 'Assigned'+ without photographers
- Payments exceeding session total
- Sessions with overlapping room assignments
- Photographers with overlapping assignments

**Action:** Log issues and alert admins

---

## 10. Special Cases & Edge Cases

### 10.1 Client Pays More Than Deposit

If client payment > `deposit_amount`:

**Option A (Recommended):** Apply excess to balance
- Record deposit payment for `deposit_amount`
- Record balance payment for excess amount
- Update remaining balance

**Option B:** Reject and request exact amount

### 10.2 Multiple Photographers for One Session

**Allowed:** Yes, via `session_photographer` table

**Rules:**
- Each photographer has own coverage times (may differ)
- One can be marked as `is_lead_photographer`
- All must be available for their respective times
- Each can mark session as attended independently

### 10.3 Editor Extends Editing Time

**Allowed:** Yes, during 'In Editing' state

**Process:**
- Editor updates `estimated_editing_days`
- System recalculates `estimated_delivery_date`
- Editor adds note in `editor_observations`
- System sends email to client with new delivery date

### 10.4 Photographer Reassignment

**Allowed:** Yes, at any time before 'Completed'

**Process:**
- Mark old assignment as `assignment_status` = 'Reassigned'
- Create new `session_photographer` record
- Validate new photographer availability
- Notify both photographers

### 10.5 Client with High Cancellation Rate

**Detection:**
```python
cancellation_rate = canceled_sessions / total_sessions

if cancellation_rate > 50% and canceled_sessions > 2:
    # Flag as high-risk client
    # Consider: requiring 100% upfront payment
```

**Action:** Alert coordinator, may require policy adjustment

---

## 11. Validation Error Codes

Standard error codes for business rule violations:

| Code | Message | HTTP Status |
|------|---------|-------------|
| `SESSION_NOT_FOUND` | Session not found | 404 |
| `INVALID_STATE_TRANSITION` | Cannot transition from {current} to {target} | 409 |
| `PAYMENT_DEADLINE_EXPIRED` | Payment deadline has passed | 422 |
| `CHANGES_DEADLINE_EXPIRED` | Changes deadline has passed | 422 |
| `INSUFFICIENT_PAYMENT` | Payment amount less than required | 422 |
| `ROOM_NOT_AVAILABLE` | Room is occupied during requested time | 409 |
| `PHOTOGRAPHER_NOT_AVAILABLE` | Photographer is busy during requested time | 409 |
| `INVALID_SESSION_DATE` | Session date cannot be in the past | 422 |
| `MISSING_RESOURCES` | Session requires assigned resources | 422 |
| `PAYMENT_EXCEEDS_TOTAL` | Total payments exceed session total | 422 |
| `IMMUTABLE_SESSION` | Session cannot be modified in current state | 422 |

---

## 12. Implementation Checklist

When implementing a new feature that involves sessions:

- [ ] Check if state transition is involved → validate against section 1
- [ ] Check if dates are calculated → follow section 2 formulas
- [ ] Check if resources are assigned → validate availability (section 3)
- [ ] Check if money is involved → follow financial rules (section 5)
- [ ] Check if cancellation is possible → apply refund matrix (section 4)
- [ ] Check if packages are involved → use explosion pattern (section 6)
- [ ] Add appropriate status history entry
- [ ] Trigger appropriate notifications (section 8)
- [ ] Use correct error codes (section 11)
- [ ] Write tests for edge cases

---

**End of Document**

*For database schema details, see `database-schema.sql`*  
*For permission matrix, see `permissions.md`*