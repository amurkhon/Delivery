"""add product_images table

Revision ID: 0005_product_images
Revises: 0004_qty_to_volume
Create Date: 2026-03-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0005_product_images'
down_revision: Union[str, None] = '0004_qty_to_volume'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'product_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_product_images_id'), 'product_images', ['id'], unique=False)
    op.create_index(op.f('ix_product_images_product_id'), 'product_images', ['product_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_product_images_product_id'), table_name='product_images')
    op.drop_index(op.f('ix_product_images_id'), table_name='product_images')
    op.drop_table('product_images')
