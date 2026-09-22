"""Explicit local application initialization; never invokes a model."""

import os
from pathlib import Path

from sqlalchemy.engine import make_url

from placement_agent.config import load_settings
from placement_agent.db.session import (
    create_sqlite_engine,
    restore_snapshot,
    run_migrations,
    session_factory,
    write_snapshot,
)
from placement_agent.services.preparation import PreparationService


def build_service():
    settings = load_settings()
    database = make_url(settings.database_url).database
    if database and database != ":memory:":
        Path(database).parent.mkdir(parents=True, exist_ok=True)
        restore_snapshot(database, os.environ.get("DATABASE_SNAPSHOT_PATH", "").strip())
    engine = create_sqlite_engine(settings.database_url)
    run_migrations(engine)
    factory = session_factory(engine)
    write_snapshot(factory)
    return PreparationService(factory)
