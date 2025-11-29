"""Change user_id from Integer to String

Revision ID: 002_change_user_id_to_string
Revises: add_email_sync_001
Create Date: 2025-11-29 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_change_user_id_to_string'
down_revision: Union[str, None] = 'add_email_sync_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Change users.id from Integer to String with auto-generated values
    op.execute("ALTER TABLE users ADD COLUMN id_new VARCHAR(50);")
    op.execute("UPDATE users SET id_new = CAST(id AS VARCHAR(50)) WHERE id_new IS NULL;")
    op.execute("ALTER TABLE users DROP CONSTRAINT users_pkey;")
    op.execute("ALTER TABLE users DROP COLUMN id;")
    op.execute("ALTER TABLE users RENAME COLUMN id_new TO id;")
    op.execute("ALTER TABLE users ADD PRIMARY KEY (id);")
    op.create_index('ix_users_id', 'users', ['id'], unique=False)

    # Step 2: Update foreign keys in conversations
    op.execute("ALTER TABLE conversations ADD COLUMN user_id_new VARCHAR(50);")
    op.execute("UPDATE conversations SET user_id_new = CAST(user_id AS VARCHAR(50));")
    op.execute("ALTER TABLE conversations DROP COLUMN user_id;")
    op.execute("ALTER TABLE conversations RENAME COLUMN user_id_new TO user_id;")
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'], unique=False)

    # Step 3: Update foreign keys in messages
    op.execute("ALTER TABLE messages ADD COLUMN user_id_new VARCHAR(50);")
    op.execute("UPDATE messages SET user_id_new = CAST(user_id AS VARCHAR(50));")
    op.execute("ALTER TABLE messages DROP COLUMN user_id;")
    op.execute("ALTER TABLE messages RENAME COLUMN user_id_new TO user_id;")
    op.create_index('ix_messages_user_id', 'messages', ['user_id'], unique=False)

    # Step 4: Update foreign keys in emails
    op.execute("ALTER TABLE emails ADD COLUMN user_id_new VARCHAR(50);")
    op.execute("UPDATE emails SET user_id_new = CAST(user_id AS VARCHAR(50));")
    op.execute("ALTER TABLE emails DROP CONSTRAINT IF EXISTS emails_user_id_fkey;")
    op.execute("ALTER TABLE emails DROP COLUMN user_id;")
    op.execute("ALTER TABLE emails RENAME COLUMN user_id_new TO user_id;")
    op.create_index('ix_emails_user_id', 'emails', ['user_id'], unique=False)

    # Step 5: Update foreign keys in gmail_sync_states
    op.execute("ALTER TABLE gmail_sync_states ADD COLUMN user_id_new VARCHAR(50);")
    op.execute("UPDATE gmail_sync_states SET user_id_new = CAST(user_id AS VARCHAR(50));")
    op.execute("ALTER TABLE gmail_sync_states DROP CONSTRAINT IF EXISTS gmail_sync_states_user_id_key;")
    op.execute("ALTER TABLE gmail_sync_states DROP CONSTRAINT IF EXISTS gmail_sync_states_user_id_fkey;")
    op.execute("ALTER TABLE gmail_sync_states DROP COLUMN user_id;")
    op.execute("ALTER TABLE gmail_sync_states RENAME COLUMN user_id_new TO user_id;")
    op.execute("ALTER TABLE gmail_sync_states ADD UNIQUE(user_id);")
    op.create_index('ix_gmail_sync_states_user_id', 'gmail_sync_states', ['user_id'], unique=False)

    # Step 6: Update foreign keys in gmail_labels
    op.execute("ALTER TABLE gmail_labels ADD COLUMN user_id_new VARCHAR(50);")
    op.execute("UPDATE gmail_labels SET user_id_new = CAST(user_id AS VARCHAR(50));")
    op.execute("ALTER TABLE gmail_labels DROP CONSTRAINT IF EXISTS gmail_labels_user_id_fkey;")
    op.execute("ALTER TABLE gmail_labels DROP COLUMN user_id;")
    op.execute("ALTER TABLE gmail_labels RENAME COLUMN user_id_new TO user_id;")
    op.create_index('ix_gmail_labels_user_id', 'gmail_labels', ['user_id'], unique=False)

    # Step 7: Update foreign keys in knowledge_base
    op.execute("ALTER TABLE knowledge_base ADD COLUMN user_id_new VARCHAR(50);")
    op.execute("UPDATE knowledge_base SET user_id_new = CAST(user_id AS VARCHAR(50)) WHERE user_id IS NOT NULL;")
    op.execute("ALTER TABLE knowledge_base DROP COLUMN user_id;")
    op.execute("ALTER TABLE knowledge_base RENAME COLUMN user_id_new TO user_id;")
    op.create_index('ix_knowledge_base_user_id', 'knowledge_base', ['user_id'], unique=False)


def downgrade() -> None:
    # This is complex to downgrade - in production you'd need careful planning
    # For now, we'll raise an exception
    raise NotImplementedError("Downgrading user_id type change is not supported")
