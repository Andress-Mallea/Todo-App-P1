"""drop users table, Auth0 stores the users"""
from alembic import op
import sqlalchemy as sa

revision = "9c1d2e3f4a5b"
down_revision = "1a8fed6d0e70"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP TABLE IF EXISTS users CASCADE")


def downgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("role", sa.String(length=20), server_default="user", nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)