"""add email to users

Revision ID: 7edaa4a3513f
Revises: 68256d922542
Create Date: 2026-08-27 13:44:31.826983

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7edaa4a3513f'
down_revision = '68256d922542'
branch_labels = None
depends_on = None


def upgrade():
    # Adding a NOT NULL column to a table that already has rows fails -- there
    # is nothing to put in it for those rows. So: add it nullable, backfill,
    # then tighten.
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(), nullable=True))

    # `name` is already unique, so an address built from it is unique too --
    # which the constraint below needs. `.invalid` is a reserved TLD that can
    # never be a real domain, so these read clearly as placeholders.
    op.execute(
        "UPDATE users SET email = name || '@example.invalid' WHERE email IS NULL"
    )

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column("email", existing_type=sa.String(), nullable=False)
        batch_op.create_unique_constraint("uq_users_email", ["email"])


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint("uq_users_email", type_="unique")
        batch_op.drop_column("email")
