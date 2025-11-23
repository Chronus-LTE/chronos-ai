"""Add google tokens to users

Revision ID: add_google_tokens
Revises:
Create Date: 2024-11-21 23:27:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_google_tokens'
down_revision = None  # Update this if you have previous migrations
branch_labels = None
depends_on = None


def upgrade():
    # Add google_access_token and google_refresh_token columns
    op.add_column('users', sa.Column('google_access_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('google_refresh_token', sa.String(), nullable=True))


def downgrade():
    # Remove the columns if rolling back
    op.drop_column('users', 'google_refresh_token')
    op.drop_column('users', 'google_access_token')
