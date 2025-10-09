"""Add catalog and sessions models

Revision ID: b971e06cb9f0
Revises: 561b40e42efb
Create Date: 2025-10-08 22:37:46.971656

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b971e06cb9f0'
down_revision: Union[str, None] = '561b40e42efb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Room table
    op.create_table('room',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('capacity', sa.Integer(), nullable=True),
    sa.Column('hourly_rate', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    schema='studio'
    )

    # Create Item table
    op.create_table('item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('item_type', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('unit_measure', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
    sa.Column('default_quantity', sa.Integer(), nullable=True),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['studio.user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='studio'
    )
    op.create_index(op.f('ix_studio_item_code'), 'item', ['code'], unique=True, schema='studio')

    # Create Package table
    op.create_table('package',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('session_type', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
    sa.Column('base_price', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('estimated_editing_days', sa.Integer(), nullable=False),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['studio.user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='studio'
    )
    op.create_index(op.f('ix_studio_package_code'), 'package', ['code'], unique=True, schema='studio')

    # Create PackageItem table (link table)
    op.create_table('packageitem',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('package_id', sa.Integer(), nullable=False),
    sa.Column('item_id', sa.Integer(), nullable=False),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('display_order', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['studio.item.id'], ),
    sa.ForeignKeyConstraint(['package_id'], ['studio.package.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='studio'
    )

    # Create Session table
    op.create_table('session',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('client_id', sa.Integer(), nullable=False),
    sa.Column('session_type', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
    sa.Column('session_date', sa.Date(), nullable=False),
    sa.Column('session_time', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=True),
    sa.Column('estimated_duration_hours', sa.Integer(), nullable=True),
    sa.Column('location', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('room_id', sa.Integer(), nullable=True),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('deposit_amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('balance_amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('paid_amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('payment_deadline', sa.Date(), nullable=True),
    sa.Column('changes_deadline', sa.Date(), nullable=True),
    sa.Column('delivery_deadline', sa.Date(), nullable=True),
    sa.Column('editing_assigned_to', sa.Integer(), nullable=True),
    sa.Column('editing_started_at', sa.DateTime(), nullable=True),
    sa.Column('editing_completed_at', sa.DateTime(), nullable=True),
    sa.Column('delivery_method', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
    sa.Column('delivery_address', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('delivered_at', sa.DateTime(), nullable=True),
    sa.Column('client_requirements', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('internal_notes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('cancellation_reason', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.Column('cancelled_at', sa.DateTime(), nullable=True),
    sa.Column('cancelled_by', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['cancelled_by'], ['studio.user.id'], ),
    sa.ForeignKeyConstraint(['client_id'], ['studio.client.id'], ),
    sa.ForeignKeyConstraint(['created_by'], ['studio.user.id'], ),
    sa.ForeignKeyConstraint(['editing_assigned_to'], ['studio.user.id'], ),
    sa.ForeignKeyConstraint(['room_id'], ['studio.room.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='studio'
    )

    # Create SessionDetail table
    op.create_table('sessiondetail',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('line_type', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.Column('reference_type', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True),
    sa.Column('item_code', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('item_name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('item_description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('quantity', sa.Integer(), nullable=False),
    sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('line_subtotal', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('is_delivered', sa.Boolean(), nullable=False),
    sa.Column('delivered_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['studio.user.id'], ),
    sa.ForeignKeyConstraint(['session_id'], ['studio.session.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='studio'
    )

    # Create SessionPayment table
    op.create_table('sessionpayment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('payment_type', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
    sa.Column('payment_method', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('transaction_reference', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
    sa.Column('payment_date', sa.Date(), nullable=False),
    sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('created_by', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['studio.user.id'], ),
    sa.ForeignKeyConstraint(['session_id'], ['studio.session.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='studio'
    )

    # Create SessionPhotographer table
    op.create_table('sessionphotographer',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('photographer_id', sa.Integer(), nullable=False),
    sa.Column('role', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
    sa.Column('assigned_at', sa.DateTime(), nullable=False),
    sa.Column('assigned_by', sa.Integer(), nullable=False),
    sa.Column('attended', sa.Boolean(), nullable=False),
    sa.Column('attended_at', sa.DateTime(), nullable=True),
    sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.ForeignKeyConstraint(['assigned_by'], ['studio.user.id'], ),
    sa.ForeignKeyConstraint(['photographer_id'], ['studio.user.id'], ),
    sa.ForeignKeyConstraint(['session_id'], ['studio.session.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='studio'
    )

    # Create SessionStatusHistory table
    op.create_table('sessionstatushistory',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('from_status', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
    sa.Column('to_status', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
    sa.Column('reason', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('notes', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('changed_at', sa.DateTime(), nullable=False),
    sa.Column('changed_by', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['changed_by'], ['studio.user.id'], ),
    sa.ForeignKeyConstraint(['session_id'], ['studio.session.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='studio'
    )


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('sessionstatushistory', schema='studio')
    op.drop_table('sessionphotographer', schema='studio')
    op.drop_table('sessionpayment', schema='studio')
    op.drop_table('sessiondetail', schema='studio')
    op.drop_table('session', schema='studio')
    op.drop_table('packageitem', schema='studio')
    op.drop_index(op.f('ix_studio_package_code'), table_name='package', schema='studio')
    op.drop_table('package', schema='studio')
    op.drop_index(op.f('ix_studio_item_code'), table_name='item', schema='studio')
    op.drop_table('item', schema='studio')
    op.drop_table('room', schema='studio')
