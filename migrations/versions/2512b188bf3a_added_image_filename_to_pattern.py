"""added image_filename to pattern

Revision ID: 2512b188bf3a
Revises: 4c17bf280e76
Create Date: 2019-12-04 03:52:32.985124

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2512b188bf3a'
down_revision = '4c17bf280e76'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pattern', sa.Column('image_filename', sa.String(length=120), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('pattern', 'image_filename')
    # ### end Alembic commands ###
