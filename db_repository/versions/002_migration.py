from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
question_tag = Table('question_tag', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('text', String(length=20)),
    Column('timestamp', DateTime),
)

question_tags = Table('question_tags', post_meta,
    Column('question_tag_id', Integer),
    Column('question_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['question_tag'].create()
    post_meta.tables['question_tags'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['question_tag'].drop()
    post_meta.tables['question_tags'].drop()
