"""SQLite connection policy and short units of work."""

from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from .models import Base


def create_sqlite_engine(database_url: str):
    if not database_url.startswith("sqlite:"):
        raise ValueError("This factory only supports SQLite")
    engine = create_engine(
        database_url,
        connect_args={"timeout": 30, "check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def configure(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=30000")
        # WAL uses shared-memory sidecar files and is unsuitable for the
        # network-mounted SQLite database used by the hosted showcase.
        cursor.execute("PRAGMA journal_mode=DELETE")
        cursor.execute("PRAGMA synchronous=FULL")
        cursor.close()

    return engine


def session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)


def run_migrations(engine) -> None:
    """Create the local schema idempotently.

    Alembic remains the release migration authority. This bootstrap path makes a
    fresh local demo usable without running a second process and never changes an
    existing column in place.
    """
    Base.metadata.create_all(engine)


@contextmanager
def unit_of_work(factory):
    with factory.begin() as session:
        # Serialize read-then-write workflows before their first ownership lookup.
        session.connection().exec_driver_sql("BEGIN IMMEDIATE")
        yield session
