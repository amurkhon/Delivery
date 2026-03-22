"""add staff to userrole enum

Revision ID: 0006_add_staff_role_to_userrole
Revises: 0005_product_images
Create Date: 2026-03-22 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0006_add_staff_role_to_userrole"
down_revision: Union[str, None] = "0005_product_images"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extend existing PostgreSQL enum used by users.role.
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'staff'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values safely.
    pass
