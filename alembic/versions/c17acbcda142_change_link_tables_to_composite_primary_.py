"""Change link tables to composite primary keys

Revision ID: c17acbcda142
Revises: b971e06cb9f0
Create Date: 2025-10-11 21:31:12.520860

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c17acbcda142'
down_revision: Union[str, None] = 'b971e06cb9f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Manual migration: Change link tables from surrogate keys to composite PKs

    # 1. Drop existing primary key constraints and id columns from link tables
    op.drop_constraint('userrole_pkey', 'userrole', schema='studio', type_='primary')
    op.drop_column('userrole', 'id', schema='studio')

    op.drop_constraint(
        'rolepermission_pkey', 'rolepermission', schema='studio', type_='primary'
    )
    op.drop_column('rolepermission', 'id', schema='studio')

    op.drop_constraint(
        'packageitem_pkey', 'packageitem', schema='studio', type_='primary'
    )
    op.drop_column('packageitem', 'id', schema='studio')

    # 2. Add composite primary key constraints
    op.create_primary_key(
        'userrole_pkey', 'userrole', ['user_id', 'role_id'], schema='studio'
    )
    op.create_primary_key(
        'rolepermission_pkey',
        'rolepermission',
        ['role_id', 'permission_id'],
        schema='studio',
    )
    op.create_primary_key(
        'packageitem_pkey',
        'packageitem',
        ['package_id', 'item_id'],
        schema='studio',
    )


def downgrade() -> None:
    # Restore surrogate keys

    # 1. Drop composite primary keys
    op.drop_constraint('userrole_pkey', 'userrole', schema='studio', type_='primary')
    op.drop_constraint(
        'rolepermission_pkey', 'rolepermission', schema='studio', type_='primary'
    )
    op.drop_constraint(
        'packageitem_pkey', 'packageitem', schema='studio', type_='primary'
    )

    # 2. Add id columns back
    op.add_column(
        'userrole',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        schema='studio',
    )
    op.add_column(
        'rolepermission',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        schema='studio',
    )
    op.add_column(
        'packageitem',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        schema='studio',
    )

    # 3. Recreate original primary keys on id columns
    op.create_primary_key('userrole_pkey', 'userrole', ['id'], schema='studio')
    op.create_primary_key(
        'rolepermission_pkey', 'rolepermission', ['id'], schema='studio'
    )
    op.create_primary_key('packageitem_pkey', 'packageitem', ['id'], schema='studio')
