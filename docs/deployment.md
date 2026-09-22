# Deployment, security, privacy, and cost controls

## Supported release boundary

The release supports a local single-user mode and a hosted single-replica mode. Hosted startup requires `AUTH_MODE=azure_easy_auth`; the application derives an opaque student identifier from Azure's authenticated `X-MS-CLIENT-PRINCIPAL-ID` header and fails closed when the header is absent. The hosting boundary must reject unauthenticated traffic before it reaches Streamlit and must strip client-supplied identity headers.

The supported hosted demo uses Microsoft Entra authentication at Azure ingress, HTTPS, one application replica, and a persistent Azure Files mount for SQLite. Multi-instance hosting requires PostgreSQL and object storage rather than shared-network SQLite.

## Local container release

Build and run the reproducible image without live Azure calls:

```powershell
docker compose build
docker compose up -d
docker compose ps
```

Open `http://127.0.0.1:8501`. Docker checks `/_stcore/health` every 30 seconds. Inspect with `docker inspect --format '{{json .State.Health}}' placement-preparation-agent-app-1` and stop with `docker compose down`. The named `placement-data` volume preserves SQLite data across container replacement. `docker compose down -v` permanently removes it and is only appropriate after a verified backup.

For local live-AI validation, pass an environment file containing only non-secret settings and authenticate with a developer identity outside the image. Never copy Azure credentials into the image or repository. Production should use managed identity. The container runs as unprivileged user `10001` and excludes local databases, logs, backups, and `.env` files from its build context.

## Azure deployment gate

The image is suitable for a private Azure Container Apps demo only after ingress authentication is enabled and anonymous requests receive 401/redirect before application code. Use:

```mermaid
flowchart TB
  Browser -->|HTTPS| Auth[Entra authenticated ingress]
  Auth --> App[One application replica]
  App --> Disk[(Persistent database volume)]
  App --> Budget[Atomic usage gate]
  Budget --> Agent[Foundry agent, managed identity]
  App --> Search[Azure AI Search]
  Disk --> Backup[Encrypted backup storage]
```

Required release checks are: authenticated subject derived server-side; one application replica; persistent storage mounted at `/app/data/private`; Foundry/Search roles granted to managed identity only; agent and corpus versions pinned; health probe configured; live call limits configured; encrypted backups tested; no secrets in image or environment export; and teardown commands reviewed. Verify current region support and price before provisioning any paid resource.

## Privacy and retention

The app stores profiles, resume/job-description text, public repository snapshots, answers, evaluations, plans, events, and usage reservations in SQLite. Export and deletion are explicit student actions. Local deletion removes that student's application rows; it does not claim to remove Azure provider telemetry or historical backups. Document provider retention separately before a public launch.

For a showcase, use synthetic student data and approved public repositories. Keep backups only for the showcase/recovery window, encrypt them at rest, restrict their readers, and expire old backups on a documented schedule. A restored backup may contain a student deleted after it was created; reapply deletion records before reopening access in a real hosted system.

## Cost controls

Azure budget alerts monitor spend but do not stop requests. The application additionally reserves per-action, per-student, and project usage before dispatch, performs no automatic model retry, and uses one-shot feedback. Search and hosting may incur costs even with no model responses; remove unused paid resources after the showcase.

## Rollback and teardown

Before replacing an image, create and verify a database backup. Keep the last known-good image tag and schema-compatible backup. Roll back by stopping the app, restoring the backup as described in [recovery.md](recovery.md), starting the previous image, and checking the health endpoint plus a read-only student view.

Teardown order: disable live AI, take the final export/backup, stop compute, confirm retention requirements, remove Search/Foundry/compute resources that are no longer needed, and finally remove local persistent storage. Never remove the only verified backup during teardown.
