# Backup and recovery runbook

The scripts operate on SQLite's online backup API and validate integrity. Backups can be made while the app runs. Restore only while the app is stopped.

## Backup

```powershell
.venv\Scripts\python scripts\backup.py --source data/private/placement.db --destination backups
```

The command prints the timestamped backup path and fails if `PRAGMA integrity_check` is not `ok`. Store that file in encrypted storage outside the application host. Record its creation time, app commit, schema revision, and retention expiry. Do not commit it.

## Restore drill

1. Stop Streamlit or the container.
2. Preserve the damaged database for investigation.
3. Restore to a new path first:

```powershell
.venv\Scripts\python scripts\restore.py --source backups/placement-YYYYMMDDTHHMMSSZ.sqlite3 --destination data/private/restored.db
```

4. Point `DATABASE_URL` at the restored file and start the app locally.
5. Confirm health, profile access, progress history, export, and a deterministic plan view. Keep `LIVE_AI_ENABLED=false` during the drill.
6. Stop the app. Restore again to the production database path or atomically rename the verified file.
7. Start the app and record the recovery point and any data gap.

Restore rejects corrupt files, unrelated SQLite schemas, and identical source/destination paths. It removes stale WAL/SHM companions after replacement. The script does not merge databases or replay deletions. Hosted recovery must reapply deletions that occurred after the backup and validate provider-side state separately.
