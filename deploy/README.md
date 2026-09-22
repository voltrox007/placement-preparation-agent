# Azure deployment assets

The release uses the checked-in `Dockerfile` and `.github/workflows/build-container.yml`. The workflow builds the image in GitHub Actions and pushes it to ACR; no credentials are copied into the image.

The deployed topology and verified resource names are recorded in [deployment.md](../docs/deployment.md). Reproduction requires:

1. A workload-profiles Container Apps environment with Log Analytics enabled.
2. An Azure Files environment storage link named `placementdata` and a `/app/data/private` volume mount.
3. External ingress on port 8501 with Microsoft Entra Easy Auth and HTTPS required.
4. A system-assigned identity with ACR pull, Search read, Azure OpenAI inference, and project-scoped Foundry User access.
5. Single revision mode, zero-to-one replicas, and the documented live request limits.

Keep live AI disabled until authentication, persistence, identity, and budget checks pass. Do not place storage keys, registry passwords, Entra client secrets, or Azure API keys in deployment files.
