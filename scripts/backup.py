"""Create a consistent SQLite backup without stopping the application."""

import argparse
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


def backup(source: Path, destination: Path) -> Path:
    source = source.resolve(strict=True)
    if source.suffix not in {".db", ".sqlite", ".sqlite3"}:
        raise ValueError("Source must be a SQLite database file")
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / f"placement-{datetime.now(UTC):%Y%m%dT%H%M%SZ}.sqlite3"
    with sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True) as source_db:
        with sqlite3.connect(target) as target_db:
            source_db.backup(target_db)
            result = target_db.execute("PRAGMA integrity_check").fetchone()
    if result != ("ok",):
        target.unlink(missing_ok=True)
        raise RuntimeError("Backup integrity check failed")
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("data/private/placement.db"))
    parser.add_argument("--destination", type=Path, default=Path("backups"))
    args = parser.parse_args()
    print(backup(args.source, args.destination))


if __name__ == "__main__":
    main()
