"""Add email sync models

Revision ID: add_email_sync_001
Revises:
Create Date: 2025-11-29 19:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_email_sync_001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create emails table
    op.create_table(
        'emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('gmail_id', sa.String(), nullable=False),
        sa.Column('thread_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('from_email', sa.String(), nullable=False),
        sa.Column('to_email', sa.String(), nullable=False),
        sa.Column('cc', sa.String(), nullable=True),
        sa.Column('bcc', sa.String(), nullable=True),
        sa.Column('reply_to', sa.String(), nullable=True),
        sa.Column('snippet', sa.String(), nullable=True),
        sa.Column('body_plain', sa.Text(), nullable=True),
        sa.Column('body_html', sa.Text(), nullable=True),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('internal_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('size_estimate', sa.Integer(), nullable=True),
        sa.Column('labels', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_unread', sa.Boolean(), nullable=True),
        sa.Column('is_starred', sa.Boolean(), nullable=True),
        sa.Column('is_important', sa.Boolean(), nullable=True),
        sa.Column('is_draft', sa.Boolean(), nullable=True),
        sa.Column('has_attachments', sa.Boolean(), nullable=True),
        sa.Column('raw_headers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('raw_payload', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_emails_id'), 'emails', ['id'], unique=False)
    op.create_index(op.f('ix_emails_gmail_id'), 'emails', ['gmail_id'], unique=True)
    op.create_index(op.f('ix_emails_thread_id'), 'emails', ['thread_id'], unique=False)
    op.create_index(op.f('ix_emails_user_id'), 'emails', ['user_id'], unique=False)
    op.create_index(op.f('ix_emails_subject'), 'emails', ['subject'], unique=False)
    op.create_index(op.f('ix_emails_from_email'), 'emails', ['from_email'], unique=False)
    op.create_index(op.f('ix_emails_date'), 'emails', ['date'], unique=False)
    op.create_index(op.f('ix_emails_is_unread'), 'emails', ['is_unread'], unique=False)
    op.create_index(op.f('ix_emails_is_starred'), 'emails', ['is_starred'], unique=False)
    op.create_index(op.f('ix_emails_has_attachments'), 'emails', ['has_attachments'], unique=False)
    op.create_index('idx_user_date', 'emails', ['user_id', 'date'], unique=False)
    op.create_index('idx_user_unread', 'emails', ['user_id', 'is_unread'], unique=False)
    op.create_index('idx_user_thread', 'emails', ['user_id', 'thread_id'], unique=False)
    op.create_index('idx_user_labels', 'emails', ['user_id', 'labels'], unique=False, postgresql_using='gin')

    # Create email_attachments table
    op.create_table(
        'email_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_id', sa.Integer(), nullable=False),
        sa.Column('gmail_attachment_id', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('mime_type', sa.String(), nullable=True),
        sa.Column('size', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('is_downloaded', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['email_id'], ['emails.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_attachments_id'), 'email_attachments', ['id'], unique=False)
    op.create_index(op.f('ix_email_attachments_email_id'), 'email_attachments', ['email_id'], unique=False)

    # Create email_threads table
    op.create_table(
        'email_threads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('gmail_thread_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('snippet', sa.String(), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=True),
        sa.Column('participants', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_unread', sa.Boolean(), nullable=True),
        sa.Column('is_starred', sa.Boolean(), nullable=True),
        sa.Column('has_attachments', sa.Boolean(), nullable=True),
        sa.Column('first_message_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_message_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_threads_id'), 'email_threads', ['id'], unique=False)
    op.create_index(op.f('ix_email_threads_gmail_thread_id'), 'email_threads', ['gmail_thread_id'], unique=True)
    op.create_index(op.f('ix_email_threads_user_id'), 'email_threads', ['user_id'], unique=False)
    op.create_index(op.f('ix_email_threads_is_unread'), 'email_threads', ['is_unread'], unique=False)
    op.create_index('idx_user_last_message', 'email_threads', ['user_id', 'last_message_date'], unique=False)

    # Create gmail_sync_states table
    op.create_table(
        'gmail_sync_states',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('sync_type', sa.String(), nullable=True),
        sa.Column('total_messages', sa.Integer(), nullable=True),
        sa.Column('synced_messages', sa.Integer(), nullable=True),
        sa.Column('failed_messages', sa.Integer(), nullable=True),
        sa.Column('history_id', sa.String(), nullable=True),
        sa.Column('last_sync_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gmail_sync_states_id'), 'gmail_sync_states', ['id'], unique=False)
    op.create_index(op.f('ix_gmail_sync_states_user_id'), 'gmail_sync_states', ['user_id'], unique=True)
    op.create_index(op.f('ix_gmail_sync_states_status'), 'gmail_sync_states', ['status'], unique=False)

    # Create gmail_labels table
    op.create_table(
        'gmail_labels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('gmail_label_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('message_list_visibility', sa.String(), nullable=True),
        sa.Column('label_list_visibility', sa.String(), nullable=True),
        sa.Column('total_messages', sa.Integer(), nullable=True),
        sa.Column('unread_messages', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gmail_labels_id'), 'gmail_labels', ['id'], unique=False)
    op.create_index(op.f('ix_gmail_labels_user_id'), 'gmail_labels', ['user_id'], unique=False)
    op.create_index('idx_user_label', 'gmail_labels', ['user_id', 'gmail_label_id'], unique=True)


def downgrade() -> None:
    op.drop_table('gmail_labels')
    op.drop_table('gmail_sync_states')
    op.drop_table('email_threads')
    op.drop_table('email_attachments')
    op.drop_table('emails')
