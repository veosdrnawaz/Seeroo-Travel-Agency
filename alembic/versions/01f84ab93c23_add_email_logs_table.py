"""add_email_logs_table

Revision ID: 01f84ab93c23
Revises: 0ce32efe01e2
Create Date: 2026-07-11 19:24:43.154280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01f84ab93c23'
down_revision: Union[str, Sequence[str], None] = '0ce32efe01e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema — create email_logs table."""
    # Note: SQLite stores UUID columns as NUMERIC internally; the spurious
    # ALTER COLUMN detections for existing tables are false positives from
    # autogenerate and have been intentionally omitted — SQLite does not
    # support ALTER COLUMN TYPE anyway.
    op.create_table(
        'email_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('booking_id', sa.UUID(), nullable=False),
        sa.Column('recipient_email', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_email_logs_booking_id'),
        'email_logs',
        ['booking_id'],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema — drop email_logs table."""
    op.drop_index(op.f('ix_email_logs_booking_id'), table_name='email_logs')
    op.drop_table('email_logs')
