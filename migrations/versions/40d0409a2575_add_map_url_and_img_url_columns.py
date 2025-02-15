"""Add map_url and img_url columns

Revision ID: 40d0409a2575
Revises: 
Create Date: 2025-02-02 21:10:02.225198

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '40d0409a2575'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('cafe', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.INTEGER(),
               nullable=False,
               autoincrement=True)
        batch_op.alter_column('name',
               existing_type=sa.TEXT(length=250),
               type_=sa.String(length=250),
               existing_nullable=False)
        batch_op.alter_column('map_url',
               existing_type=sa.TEXT(length=500),
               type_=sa.String(length=500),
               existing_nullable=False)
        batch_op.alter_column('img_url',
               existing_type=sa.TEXT(length=500),
               type_=sa.String(length=500),
               existing_nullable=False)
        batch_op.alter_column('location',
               existing_type=sa.TEXT(length=250),
               type_=sa.String(length=250),
               existing_nullable=False)
        batch_op.alter_column('seats',
               existing_type=sa.TEXT(length=250),
               type_=sa.String(length=250),
               nullable=False)
        batch_op.alter_column('coffee_price',
               existing_type=sa.TEXT(length=250),
               type_=sa.String(length=250),
               existing_nullable=True)
        batch_op.create_unique_constraint("uq_cafe_name", ['name'])

    with op.batch_alter_table('update_request', schema=None) as batch_op:
        batch_op.add_column(sa.Column('proposed_map_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('proposed_img_url', sa.String(length=500), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('update_request', schema=None) as batch_op:
        batch_op.drop_column('proposed_img_url')
        batch_op.drop_column('proposed_map_url')

    with op.batch_alter_table('cafe', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.alter_column('coffee_price',
               existing_type=sa.String(length=250),
               type_=sa.TEXT(length=250),
               existing_nullable=True)
        batch_op.alter_column('seats',
               existing_type=sa.String(length=250),
               type_=sa.TEXT(length=250),
               nullable=True)
        batch_op.alter_column('location',
               existing_type=sa.String(length=250),
               type_=sa.TEXT(length=250),
               existing_nullable=False)
        batch_op.alter_column('img_url',
               existing_type=sa.String(length=500),
               type_=sa.TEXT(length=500),
               existing_nullable=False)
        batch_op.alter_column('map_url',
               existing_type=sa.String(length=500),
               type_=sa.TEXT(length=500),
               existing_nullable=False)
        batch_op.alter_column('name',
               existing_type=sa.String(length=250),
               type_=sa.TEXT(length=250),
               existing_nullable=False)
        batch_op.alter_column('id',
               existing_type=sa.INTEGER(),
               nullable=True,
               autoincrement=True)

    # ### end Alembic commands ###
