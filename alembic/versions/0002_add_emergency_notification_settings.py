"""Add emergency notification settings to admin_settings

Revision ID: 0002_emerg_notif
Revises:
Create Date: 2026-10-08

Adds three new columns to the admin_settings table to support the
Emergency Contact Notification feature:
  - emergency_contact_number   (VARCHAR 20, nullable)
  - emergency_notifications_enabled (BOOLEAN, default False)
  - hospital_notifications_enabled  (BOOLEAN, default False)
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '0002_emerg_notif'
down_revision = '9ac644ce1bf2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'admin_settings',
        sa.Column('emergency_contact_number', sa.String(20), nullable=True)
    )
    op.add_column(
        'admin_settings',
        sa.Column('emergency_notifications_enabled', sa.Boolean(), nullable=False, server_default='false')
    )
    op.add_column(
        'admin_settings',
        sa.Column('hospital_notifications_enabled', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    op.drop_column('admin_settings', 'hospital_notifications_enabled')
    op.drop_column('admin_settings', 'emergency_notifications_enabled')
    op.drop_column('admin_settings', 'emergency_contact_number')
