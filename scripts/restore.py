"""Validate and atomically restore a SQLite backup while the app is stopped."""

import argparse
import os
import shutil
import sqlite3
from pathlib import Path


def restore(source: Path, destination: Path) -> Path:
    source = source.resolve(strict=True)
    destination = destination.resolve()
    if source == destination:
        raise ValueError("Source and destination must differ")
    with sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True) as database:
        if database.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise ValueError("Backup integrity check failed")
        tables = {row[0] for row in database.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "students" not in tables:
        raise ValueError("Backup does not contain the application schema")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".restore.tmp")
    shutil.copyfile(source, temporary)
    os.replace(temporary, destination)
    for suffix in ("-wal", "-shm"):
        destination.with_name(destination.name + suffix).unlink(missing_ok=True)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, default=Path("data/private/placement.db"))
    args = parser.parse_args()
    print(restore(args.source, args.destination))


if __name__ == "__main__":
    main()
