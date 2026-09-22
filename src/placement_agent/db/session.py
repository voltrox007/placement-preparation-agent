"""SQLite connection policy and short units of work."""

import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from uuid import uuid4

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from .models import Base

_WRITE_LOCK = Lock()
_SNAPSHOT_PATHS: dict[int, str] = {}


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
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    _SNAPSHOT_PATHS[id(factory)] = os.environ.get("DATABASE_SNAPSHOT_PATH", "").strip()
    return factory


def restore_snapshot(database_path: str, snapshot_path: str) -> None:
    """Restore a hosted local SQLite file from its Azure Files snapshot."""
    if not snapshot_path:
        return
    database, snapshot = Path(database_path), Path(snapshot_path)
    database.parent.mkdir(parents=True, exist_ok=True)
    if not database.exists() and snapshot.is_file():
        shutil.copyfile(snapshot, database)


def write_snapshot(factory) -> None:
    """Atomically copy a committed local SQLite file to persistent storage."""
    snapshot_value = _SNAPSHOT_PATHS.get(id(factory), "")
    database_value = factory.kw["bind"].url.database
    if not snapshot_value or not database_value or database_value == ":memory:":
        return
    source, destination = Path(database_value), Path(snapshot_value)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")
    shutil.copyfile(source, temporary)
    os.replace(temporary, destination)


def run_migrations(engine) -> None:
    """Create the local schema idempotently.

    Alembic remains the release migration authority. This bootstrap path makes a
    fresh local demo usable without running a second process and never changes an
    existing column in place.
    """
    Base.metadata.create_all(engine)


@contextmanager
def unit_of_work(factory):
    with _WRITE_LOCK:
        with factory.begin() as session:
            # Serialize read-then-write workflows before their first ownership lookup.
            session.connection().exec_driver_sql("BEGIN IMMEDIATE")
            yield session
        write_snapshot(factory)
