"""Add Geometry column to Risk table

Revision ID: 49c435ef88a3
Revises: f6048c1f3032
Create Date: 2020-06-30 08:42:47.394494

"""
import geoalchemy2
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '49c435ef88a3'
down_revision = 'f6048c1f3032'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('risk', sa.Column('location', geoalchemy2.types.Geometry(geometry_type='POINT', srid=3857), nullable=True))


def downgrade():
    op.drop_column('risk', 'location')
