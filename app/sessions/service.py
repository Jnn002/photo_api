"""
Session service layer for business logic.

This module provides business logic for session-related operations:
- SessionService: Main session management with state machine
- SessionDetailService: Line items and package explosion
- SessionPhotographerService: Photographer assignments
- SessionPaymentService: Payment tracking and validation

For business rules, see files/business_rules_doc.md
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.catalog.models import Item, Package, PackageItem
from app.catalog.repository import ItemRepository, PackageRepository, RoomRepository
from app.clients.repository import ClientRepository
from app.core.config import settings
from app.core.enums import (
    DeliveryMethod,
    LineType,
    PaymentType,
    ReferenceType,
    SessionStatus,
    SessionType,
    Status,
)
from app.core.exceptions import (
    ClientNotFoundException,
    DeadlineExpiredException,
    InactiveClientException,
    InactiveResourceException,
    InsufficientBalanceException,
    InvalidSessionTypeException,
    InvalidStatusTransitionException,
    ItemNotFoundException,
    PackageItemsEmptyException,
    PackageNotFoundException,
    PhotographerNotAvailableException,
    RoomNotAvailableException,
    RoomNotFoundException,
    SessionNotEditableException,
    SessionNotFoundException,
)
from app.core.time_utils import get_current_utc_time
from app.sessions.models import (
    Session as SessionModel,
)
from app.sessions.models import (
    SessionDetail,
    SessionPayment,
    SessionPhotographer,
    SessionStatusHistory,
)
from app.sessions.repository import (
    SessionDetailRepository,
    SessionPaymentRepository,
    SessionPhotographerRepository,
    SessionRepository,
    SessionStatusHistoryRepository,
)
from app.sessions.schemas import (
    SessionCancellation,
    SessionCreate,
    SessionDetailCreate,
    SessionPaymentCreate,
    SessionPhotographerAssign,
    SessionUpdate,
)

# ==================== Session Service ====================


class SessionService:
    """Service for Session business logic and state machine orchestration."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SessionRepository(db)
        self.client_repo = ClientRepository(db)
        self.room_repo = RoomRepository(db)
        self.detail_repo = SessionDetailRepository(db)
        self.payment_repo = SessionPaymentRepository(db)
        self.history_repo = SessionStatusHistoryRepository(db)

    # ==================== State Machine Transition Rules ====================

    VALID_TRANSITIONS = {
        SessionStatus.REQUEST: [
            SessionStatus.NEGOTIATION,
            SessionStatus.PRE_SCHEDULED,
            SessionStatus.CANCELED,
        ],
        SessionStatus.NEGOTIATION: [
            SessionStatus.PRE_SCHEDULED,
            SessionStatus.CANCELED,
        ],
        SessionStatus.PRE_SCHEDULED: [
            SessionStatus.CONFIRMED,
            SessionStatus.CANCELED,
        ],
        SessionStatus.CONFIRMED: [
            SessionStatus.ASSIGNED,
            SessionStatus.CANCELED,
        ],
        SessionStatus.ASSIGNED: [
            SessionStatus.ATTENDED,
            SessionStatus.CANCELED,
        ],
        SessionStatus.ATTENDED: [
            SessionStatus.IN_EDITING,
            SessionStatus.CANCELED,
        ],
        SessionStatus.IN_EDITING: [
            SessionStatus.READY_FOR_DELIVERY,
            SessionStatus.CANCELED,
        ],
        SessionStatus.READY_FOR_DELIVERY: [
            SessionStatus.COMPLETED,
            SessionStatus.CANCELED,
        ],
        SessionStatus.COMPLETED: [],  # Terminal state
        SessionStatus.CANCELED: [],  # Terminal state
    }

    def _is_valid_transition(self, from_status: SessionStatus, to_status: SessionStatus) -> bool:
        """Check if a status transition is valid."""
        return to_status in self.VALID_TRANSITIONS.get(from_status, [])

    # ==================== CRUD Operations ====================

    async def create_session(self, data: SessionCreate, created_by: int) -> SessionModel:
        """
        Create a new session in REQUEST status.

        Validates:
        - Client exists and is active
        - Room is available (if studio session)
        - Session date is in the future
        """
        # Validate client
        client = await self.client_repo.get_by_id(data.client_id)
        if not client:
            raise ClientNotFoundException(data.client_id)
        if client.status != Status.ACTIVE:
            raise InactiveClientException(f'Client {client.full_name} is inactive')

        # Validate room availability for studio sessions
        if data.session_type == SessionType.STUDIO and data.room_id:
            room = await self.room_repo.get_by_id(data.room_id)
            if not room:
                raise RoomNotFoundException(data.room_id)
            if room.status != Status.ACTIVE:
                raise InactiveResourceException(f'Room {room.name} is inactive')

            # Check room availability
            if data.session_time:
                is_available = await self.repo.check_room_availability(
                    data.room_id, data.session_date, data.session_time
                )
                if not is_available:
                    raise RoomNotAvailableException(
                        data.room_id,
                        str(data.session_date),
                        data.session_time,
                    )

        # Create session
        session = SessionModel(
            client_id=data.client_id,
            session_type=data.session_type,
            session_date=data.session_date,
            session_time=data.session_time,
            estimated_duration_hours=data.estimated_duration_hours,
            location=data.location,
            room_id=data.room_id,
            status=SessionStatus.REQUEST,
            client_requirements=data.client_requirements,
            created_by=created_by,
        )

        session = await self.repo.create(session)
        await self.db.commit()
        await self.db.refresh(session)

        # Create initial status history
        await self._record_status_change(
            session.id,
            None,
            SessionStatus.REQUEST,
            created_by,
            'Session created',
        )

        return session

    async def get_session(self, session_id: int) -> SessionModel:
        """Get session by ID."""
        session = await self.repo.get_by_id(session_id)
        if not session:
            raise SessionNotFoundException(session_id)
        return session

    async def get_session_with_details(self, session_id: int) -> SessionModel:
        """Get session by ID with details eagerly loaded."""
        session = await self.repo.get_with_details(session_id)
        if not session:
            raise SessionNotFoundException(session_id)
        return session

    async def list_sessions(
        self,
        client_id: int | None = None,
        status: SessionStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        photographer_id: int | None = None,
        editor_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SessionModel]:
        """
        List sessions with optional filters.

        Priority: specific filters > status > all
        """
        if start_date and end_date:
            return await self.repo.list_by_date_range(start_date, end_date, limit, offset)

        if client_id:
            return await self.repo.list_by_client(client_id, limit, offset)

        if photographer_id:
            return await self.repo.list_by_photographer(photographer_id, limit, offset)

        if editor_id:
            return await self.repo.list_by_editor(editor_id, limit, offset)

        if status:
            return await self.repo.list_by_status(status, limit, offset)

        return await self.repo.list_all(limit, offset)

    async def list_my_photographer_assignments(
        self,
        photographer_id: int,
        status: SessionStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SessionModel]:
        """
        List sessions assigned to a specific photographer.

        Used by photographers to view their own assignments.
        Supports filtering by status and date range.
        """
        # Get sessions assigned to this photographer
        sessions = await self.repo.list_by_photographer(photographer_id, limit, offset)

        # Apply optional filters
        if status:
            sessions = [s for s in sessions if s.status == status]

        if start_date:
            sessions = [s for s in sessions if s.session_date >= start_date]

        if end_date:
            sessions = [s for s in sessions if s.session_date <= end_date]

        return sessions

    async def list_my_editor_assignments(
        self,
        editor_id: int,
        status: SessionStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SessionModel]:
        """
        List sessions assigned to a specific editor.

        Used by editors to view sessions they need to edit.
        Typically filters for IN_EDITING status by default.
        """
        # Get sessions assigned to this editor
        sessions = await self.repo.list_by_editor(editor_id, limit, offset)

        # Apply optional filters
        if status:
            sessions = [s for s in sessions if s.status == status]

        if start_date:
            sessions = [s for s in sessions if s.session_date >= start_date]

        if end_date:
            sessions = [s for s in sessions if s.session_date <= end_date]

        return sessions

    async def update_session(
        self, session_id: int, data: SessionUpdate, updated_by: int
    ) -> SessionModel:
        """
        Update session details.

        Validates:
        - Session is not past changes deadline
        - Room availability (if changing room)
        """
        session = await self.get_session(session_id)

        # Check if session is editable (not past changes deadline)
        if session.changes_deadline and date.today() > session.changes_deadline:
            raise SessionNotEditableException(
                session_id, str(session.changes_deadline)
            )

        # Validate room availability if changing room or datetime
        update_dict = data.model_dump(exclude_unset=True)

        if 'room_id' in update_dict or 'session_date' in update_dict or 'session_time' in update_dict:
            room_id = update_dict.get('room_id', session.room_id)
            session_date = update_dict.get('session_date', session.session_date)
            session_time = update_dict.get('session_time', session.session_time)

            if room_id and session_time:
                is_available = await self.repo.check_room_availability(
                    room_id, session_date, session_time
                )
                if not is_available:
                    raise RoomNotAvailableException(
                        room_id,
                        str(session_date),
                        session_time,
                    )

        session = await self.repo.update(session, update_dict)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    # ==================== State Machine Transitions ====================

    async def transition_status(
        self,
        session_id: int,
        to_status: SessionStatus,
        changed_by: int,
        reason: str | None = None,
        notes: str | None = None,
    ) -> SessionModel:
        """
        Transition session to a new status.

        Validates:
        - Transition is valid per state machine rules
        - Business rules are satisfied for the transition
        """
        session = await self.get_session(session_id)

        # Validate transition
        if not self._is_valid_transition(session.status, to_status):
            allowed = self.VALID_TRANSITIONS.get(session.status, [])
            raise InvalidStatusTransitionException(
                session.status.value,
                to_status.value,
                [s.value for s in allowed],
            )

        # Apply transition-specific business logic
        await self._apply_transition_logic(session, to_status, changed_by)

        # Update session status
        old_status = session.status
        session.status = to_status
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)

        # Record status change
        await self._record_status_change(
            session_id, old_status, to_status, changed_by, reason, notes
        )

        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def _apply_transition_logic(
        self, session: SessionModel, to_status: SessionStatus, changed_by: int
    ) -> None:
        """
        Apply business logic for specific status transitions.

        See files/business_rules_doc.md for complete rules.
        """
        if to_status == SessionStatus.PRE_SCHEDULED:
            # Calculate payment deadline (5 days from today)
            session.payment_deadline = date.today() + timedelta(
                days=settings.PAYMENT_DEADLINE_DAYS
            )

            # Calculate changes deadline (7 days before session)
            session.changes_deadline = session.session_date - timedelta(
                days=settings.CHANGES_DEADLINE_DAYS
            )

        elif to_status == SessionStatus.CONFIRMED:
            # Validate deposit has been paid
            if session.paid_amount < session.deposit_amount:
                raise InsufficientBalanceException(
                    session.id,
                    float(session.deposit_amount - session.paid_amount),
                    0.0,
                )

        elif to_status == SessionStatus.IN_EDITING:
            # Calculate delivery deadline (based on editing days)
            editing_days = settings.DEFAULT_EDITING_DAYS
            session.delivery_deadline = date.today() + timedelta(days=editing_days)

            # Record editing start time
            if not session.editing_started_at:
                session.editing_started_at = get_current_utc_time()

        elif to_status == SessionStatus.READY_FOR_DELIVERY:
            # Record editing completion
            if not session.editing_completed_at:
                session.editing_completed_at = get_current_utc_time()

        elif to_status == SessionStatus.COMPLETED:
            # Validate full payment
            if session.paid_amount < session.total_amount:
                raise InsufficientBalanceException(
                    session.id,
                    float(session.total_amount - session.paid_amount),
                    0.0,
                )

            # Record delivery
            if not session.delivered_at:
                session.delivered_at = get_current_utc_time()

    async def _record_status_change(
        self,
        session_id: int,
        from_status: SessionStatus | None,
        to_status: SessionStatus,
        changed_by: int,
        reason: str | None = None,
        notes: str | None = None,
    ) -> None:
        """Record status change in history."""
        history = SessionStatusHistory(
            session_id=session_id,
            from_status=from_status.value if from_status else None,
            to_status=to_status.value,
            reason=reason,
            notes=notes,
            changed_by=changed_by,
        )
        await self.history_repo.create(history)
        await self.db.flush()

    # ==================== Session Cancellation ====================

    async def cancel_session(
        self,
        session_id: int,
        data: SessionCancellation,
        cancelled_by: int,
    ) -> SessionModel:
        """
        Cancel a session and apply refund logic.

        Refund matrix (see business_rules_doc.md section 4.1):
        - Before Pre-scheduled: 100% refund
        - Pre-scheduled/Confirmed: 50% if Client, 100% if Studio
        - After Confirmed: No refund if Client, 100% if Studio
        """
        session = await self.get_session(session_id)

        # Cannot cancel completed or already canceled sessions
        if session.status in [SessionStatus.COMPLETED, SessionStatus.CANCELED]:
            raise InvalidStatusTransitionException(
                session.status.value,
                SessionStatus.CANCELED.value,
                [],
            )

        # Apply refund logic based on status and initiator
        refund_amount = await self._calculate_refund(session, data.initiated_by)

        # Create refund payment if applicable
        if refund_amount > 0:
            refund_payment = SessionPayment(
                session_id=session_id,
                payment_type=PaymentType.REFUND,
                payment_method='Refund',
                amount=refund_amount,
                payment_date=date.today(),
                notes=f'Refund for cancellation. Initiated by: {data.initiated_by}',
                created_by=cancelled_by,
            )
            await self.payment_repo.create(refund_payment)

        # Update session
        session.status = SessionStatus.CANCELED
        session.cancellation_reason = data.cancellation_reason
        session.cancelled_at = get_current_utc_time()
        session.cancelled_by = cancelled_by

        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)

        # Record status change
        await self._record_status_change(
            session_id,
            session.status,
            SessionStatus.CANCELED,
            cancelled_by,
            f'Canceled by {data.initiated_by}: {data.cancellation_reason}',
            data.notes,
        )

        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def _calculate_refund(self, session: SessionModel, initiated_by: str) -> Decimal:
        """
        Calculate refund amount based on status and who initiated cancellation.

        See files/business_rules_doc.md section 4.1 for refund matrix.
        """
        # Studio always gets 100% refund
        if initiated_by == 'Studio':
            return session.paid_amount

        # Client refund depends on status
        if session.status == SessionStatus.REQUEST:
            return session.paid_amount  # 100%

        elif session.status in [SessionStatus.NEGOTIATION, SessionStatus.PRE_SCHEDULED]:
            return session.paid_amount * Decimal('0.5')  # 50%

        else:
            return Decimal('0.00')  # No refund after Confirmed

    # ==================== Financial Calculations ====================

    async def recalculate_totals(self, session_id: int) -> SessionModel:
        """
        Recalculate session financial totals from details.

        Updates:
        - total_amount (sum of all detail line_subtotals)
        - deposit_amount (total * deposit_percentage)
        - balance_amount (total - deposit)
        - paid_amount (sum of all payments)
        """
        session = await self.get_session(session_id)

        # Get all details
        details = await self.detail_repo.list_by_session(session_id)

        # Calculate total from details
        total = sum(detail.line_subtotal for detail in details)

        # Calculate deposit (default 50%)
        deposit_percentage = Decimal(str(settings.DEFAULT_DEPOSIT_PERCENTAGE))
        deposit = (total * deposit_percentage) / Decimal('100')

        # Calculate balance
        balance = total - deposit

        # Get paid amount from payments
        paid = await self.payment_repo.get_total_paid(session_id)
        refunded = await self.payment_repo.get_total_refunded(session_id)
        net_paid = paid - refunded

        # Update session
        session.total_amount = total
        session.deposit_amount = deposit
        session.balance_amount = balance
        session.paid_amount = net_paid

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    # ==================== Editor Assignment ====================

    async def assign_editor(
        self, session_id: int, editor_id: int, assigned_by: int
    ) -> SessionModel:
        """
        Assign an editor to a session and auto-transition to IN_EDITING.

        When an editor is assigned to an ATTENDED session:
        - Sets editing_assigned_to field
        - Automatically transitions session from ATTENDED to IN_EDITING
        - Records editing_started_at timestamp (via transition logic)
        - Calculates delivery_deadline (via transition logic)

        This ensures the editing phase starts immediately when editor is assigned.
        """
        session = await self.get_session(session_id)

        # Assign editor
        session.editing_assigned_to = editor_id
        self.db.add(session)
        await self.db.flush()

        # Auto-transition to IN_EDITING if session is ATTENDED
        if session.status == SessionStatus.ATTENDED:
            await self.transition_status(
                session_id=session_id,
                to_status=SessionStatus.IN_EDITING,
                changed_by=assigned_by,
                reason='Editor assigned to session',
                notes=f'Editor ID {editor_id} assigned for post-processing',
            )

        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def mark_ready_for_delivery(
        self, session_id: int, marked_by: int, notes: str | None = None
    ) -> SessionModel:
        """
        Mark a session as ready for delivery (editor completed editing).

        Automatically transitions from IN_EDITING to READY_FOR_DELIVERY status.

        Validates:
        - Session must be in IN_EDITING status
        - User marking must be the assigned editor (or admin/coordinator)
        """
        session = await self.get_session(session_id)

        # Validate session is in IN_EDITING status
        if session.status != SessionStatus.IN_EDITING:
            raise InvalidStatusTransitionException(
                session.status.value,
                SessionStatus.READY_FOR_DELIVERY.value,
                [SessionStatus.IN_EDITING.value],
            )

        # Transition to READY_FOR_DELIVERY
        await self.transition_status(
            session_id=session_id,
            to_status=SessionStatus.READY_FOR_DELIVERY,
            changed_by=marked_by,
            reason='Editor marked session as ready for delivery',
            notes=notes,
        )

        await self.db.refresh(session)
        return session


# ==================== Session Detail Service ====================


class SessionDetailService:
    """Service for SessionDetail business logic (line items and package explosion)."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SessionDetailRepository(db)
        self.session_repo = SessionRepository(db)
        self.item_repo = ItemRepository(db)
        self.package_repo = PackageRepository(db)

    async def add_item_to_session(
        self, session_id: int, item_id: int, quantity: int, created_by: int
    ) -> SessionDetail:
        """
        Add an individual item to a session.

        Validates:
        - Session exists and is editable
        - Item exists and is active
        """
        # Validate session
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise SessionNotFoundException(session_id)

        # Check if session is editable
        if session.changes_deadline and date.today() > session.changes_deadline:
            raise SessionNotEditableException(
                session_id, str(session.changes_deadline)
            )

        # Validate item
        item = await self.item_repo.get_by_id(item_id)
        if not item:
            raise ItemNotFoundException(item_id)
        if item.status != Status.ACTIVE:
            raise InactiveResourceException(f'Item {item.name} is inactive')

        # Create session detail
        line_subtotal = item.unit_price * Decimal(str(quantity))

        detail = SessionDetail(
            session_id=session_id,
            line_type=LineType.ITEM,
            reference_id=item_id,
            reference_type=ReferenceType.ITEM,
            item_code=item.code,
            item_name=item.name,
            item_description=item.description,
            quantity=quantity,
            unit_price=item.unit_price,
            line_subtotal=line_subtotal,
            created_by=created_by,
        )

        detail = await self.repo.create(detail)
        await self.db.commit()
        await self.db.refresh(detail)

        return detail

    async def add_package_to_session(
        self, session_id: int, package_id: int, created_by: int
    ) -> list[SessionDetail]:
        """
        Add a package to a session (PACKAGE EXPLOSION pattern).

        The package is "exploded" into individual SessionDetail records for each item,
        ensuring historical immutability.

        Validates:
        - Session exists and is editable
        - Package exists, is active, and has items
        - Package session_type matches session type
        """
        # Validate session
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise SessionNotFoundException(session_id)

        # Check if session is editable
        if session.changes_deadline and date.today() > session.changes_deadline:
            raise SessionNotEditableException(
                session_id, str(session.changes_deadline)
            )

        # Validate package
        package = await self.package_repo.get_with_items(package_id)
        if not package:
            raise PackageNotFoundException(package_id)
        if package.status != Status.ACTIVE:
            raise InactiveResourceException(f'Package {package.name} is inactive')

        # Validate package has items
        statement = (
            select(PackageItem)
            .where(PackageItem.package_id == package_id)
            .options(selectinload(PackageItem.item))  # type: ignore
        )
        result = await self.db.exec(statement)
        package_items = list(result.all())

        if not package_items:
            raise PackageItemsEmptyException(package_id)

        # Validate session type matches package
        if package.session_type not in [session.session_type, SessionType.BOTH]:
            raise InvalidSessionTypeException(
                f'Package {package.name} is for {package.session_type} sessions, '
                f'but session is {session.session_type}'
            )

        # PACKAGE EXPLOSION: Create detail for each item in package
        details: list[SessionDetail] = []

        for package_item in package_items:
            item = package_item.item

            # Skip inactive items
            if item.status != Status.ACTIVE:
                continue

            line_subtotal = item.unit_price * Decimal(str(package_item.quantity))

            detail = SessionDetail(
                session_id=session_id,
                line_type=LineType.ITEM,
                reference_id=package_id,  # Track original package
                reference_type=ReferenceType.PACKAGE,
                item_code=item.code,
                item_name=item.name,
                item_description=item.description,
                quantity=package_item.quantity,
                unit_price=item.unit_price,  # Price at time of sale
                line_subtotal=line_subtotal,
                created_by=created_by,
            )
            details.append(detail)

        # Bulk create details
        created_details = await self.repo.create_many(details)
        await self.db.commit()

        return created_details

    async def remove_detail(self, detail_id: int, removed_by: int) -> None:
        """
        Remove a session detail.

        Validates session is editable.
        """
        detail = await self.repo.get_by_id(detail_id)
        if not detail:
            return

        # Validate session is editable
        session = await self.session_repo.get_by_id(detail.session_id)
        if session and session.changes_deadline and date.today() > session.changes_deadline:
            raise SessionNotEditableException(
                detail.session_id, str(session.changes_deadline)
            )

        await self.db.delete(detail)
        await self.db.commit()

    async def list_session_details(self, session_id: int) -> list[SessionDetail]:
        """List all details for a session."""
        return await self.repo.list_by_session(session_id)


# ==================== Session Payment Service ====================


class SessionPaymentService:
    """Service for SessionPayment business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SessionPaymentRepository(db)
        self.session_repo = SessionRepository(db)

    async def record_payment(
        self, data: SessionPaymentCreate, created_by: int
    ) -> SessionPayment:
        """
        Record a payment for a session and update financial calculations.

        Validates:
        - Session exists
        - Payment amount does not exceed remaining balance

        Auto-updates:
        - paid_amount: Adds new payment to total paid
        - balance_amount: Recalculates remaining balance (total - paid)
        """
        # Validate session
        session = await self.session_repo.get_by_id(data.session_id)
        if not session:
            raise SessionNotFoundException(data.session_id)

        # Validate payment amount
        remaining_balance = session.total_amount - session.paid_amount
        if data.amount > remaining_balance:
            raise InsufficientBalanceException(
                data.session_id,
                float(remaining_balance),
                float(data.amount),
            )

        # Create payment
        payment = SessionPayment(
            session_id=data.session_id,
            payment_type=data.payment_type,
            payment_method=data.payment_method,
            amount=data.amount,
            transaction_reference=data.transaction_reference,
            payment_date=data.payment_date,
            notes=data.notes,
            created_by=created_by,
        )

        payment = await self.repo.create(payment)
        await self.db.flush()

        # Update session financial fields
        session.paid_amount += data.amount
        # Recalculate balance: total - paid (this replaces the previous deposit-based calculation)
        session.balance_amount = session.total_amount - session.paid_amount

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(payment)

        return payment

    async def list_session_payments(self, session_id: int) -> list[SessionPayment]:
        """List all payments for a session."""
        return await self.repo.list_by_session(session_id)


# ==================== Session Photographer Service ====================


class SessionPhotographerService:
    """Service for SessionPhotographer business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SessionPhotographerRepository(db)
        self.session_repo = SessionRepository(db)

    async def assign_photographer(
        self, data: SessionPhotographerAssign, assigned_by: int
    ) -> SessionPhotographer:
        """
        Assign a photographer to a session and auto-transition to ASSIGNED.

        When a photographer is assigned to a CONFIRMED session:
        - Creates photographer assignment record
        - Automatically transitions session from CONFIRMED to ASSIGNED

        Validates:
        - Session exists
        - Photographer is available for the session date/time
        """
        # Validate session
        session = await self.session_repo.get_by_id(data.session_id)
        if not session:
            raise SessionNotFoundException(data.session_id)

        # Check photographer availability
        if session.session_time:
            is_available = await self.repo.check_photographer_availability(
                data.photographer_id, session.session_date, session.session_time
            )
            if not is_available:
                raise PhotographerNotAvailableException(
                    data.photographer_id,
                    str(session.session_date),
                    session.session_time,
                )

        # Create assignment
        assignment = SessionPhotographer(
            session_id=data.session_id,
            photographer_id=data.photographer_id,
            role=data.role,
            assigned_by=assigned_by,
        )

        assignment = await self.repo.create(assignment)
        await self.db.flush()

        # Auto-transition to ASSIGNED if session is CONFIRMED
        if session.status == SessionStatus.CONFIRMED:
            from app.sessions.service import SessionService

            session_service = SessionService(self.db)
            await session_service.transition_status(
                session_id=data.session_id,
                to_status=SessionStatus.ASSIGNED,
                changed_by=assigned_by,
                reason='Photographer assigned to session',
                notes=f'Photographer ID {data.photographer_id} assigned for photography',
            )

        await self.db.commit()
        await self.db.refresh(assignment)

        return assignment

    async def mark_attended(
        self, assignment_id: int, marked_by: int, notes: str | None = None
    ) -> SessionPhotographer:
        """
        Mark photographer assignment as attended.

        When a photographer marks themselves as attended, the session
        automatically transitions to ATTENDED status if not already in that state.
        """
        assignment = await self.repo.get_by_id(assignment_id)
        if not assignment:
            raise SessionNotFoundException(assignment_id)

        if notes:
            assignment.notes = notes

        assignment = await self.repo.mark_attended(assignment)
        await self.db.flush()

        # Auto-transition session to ATTENDED status
        session = await self.session_repo.get_by_id(assignment.session_id)
        if session and session.status == SessionStatus.ASSIGNED:
            # Use SessionService to transition with proper business logic
            from app.sessions.service import SessionService

            session_service = SessionService(self.db)
            await session_service.transition_status(
                session_id=assignment.session_id,
                to_status=SessionStatus.ATTENDED,
                changed_by=marked_by,
                reason='Photographer marked as attended',
                notes=notes,
            )

        await self.db.commit()
        await self.db.refresh(assignment)

        return assignment

    async def remove_assignment(self, assignment_id: int) -> None:
        """Remove photographer assignment."""
        await self.repo.remove_assignment(assignment_id)
        await self.db.commit()

    async def list_session_photographers(
        self, session_id: int
    ) -> list[SessionPhotographer]:
        """List all photographer assignments for a session."""
        return await self.repo.list_by_session(session_id)
