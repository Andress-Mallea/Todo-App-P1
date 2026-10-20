"""restaurant schema

Revision ID: 1a8fed6d0e70
Revises: 58740f96bb27
Create Date: 2026-10-19 11:22:55.624673

"""
from pathlib import Path
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a8fed6d0e70'
down_revision = '58740f96bb27'
branch_labels = None
depends_on = None

def upgrade():
    ddl = Path(__file__).resolve().parents[2] / "database.ddl"
    op.get_bind().exec_driver_sql(ddl.read_text(encoding="utf-8"))


def downgrade():
    op.execute("DROP SCHEMA IF EXISTS content CASCADE")
