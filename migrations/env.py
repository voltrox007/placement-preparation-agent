"""The application and migrations share connection-level SQLite safeguards."""
from alembic import context

from placement_agent.db.models import Base
from placement_agent.db.session import create_sqlite_engine

config = context.config
url = config.get_main_option("sqlalchemy.url")
if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_sqlite_engine(url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
