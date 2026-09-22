"""Public GitHub snapshots with fixed hosts, bounded reads, and no execution."""

import base64
import re
from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx

MAX_RESPONSE_BYTES = 1_000_000
MAX_FILE_BYTES = 40_000
ALLOWED_FILES = ("README.md", "pyproject.toml", "requirements.txt", "package.json")


def parse_repository_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.query or parsed.fragment or parsed.username:
        raise ValueError("Use a public repository URL: https://github.com/owner/repository")
    parts = parsed.path.strip("/").split("/")
    if len(parts) != 2 or any(not re.fullmatch(r"[A-Za-z0-9_.-]+", p) for p in parts):
        raise ValueError("Provide a repository URL, not a file or branch URL")
    owner, repo = parts
    repo = repo.removesuffix(".git")
    if not repo or owner in {".", ".."} or repo in {".", ".."}:
        raise ValueError("Invalid repository name")
    return owner, repo


def snapshot_repository(url: str, client: httpx.Client | None = None) -> dict:
    owner, repo = parse_repository_url(url)
    own_client = client is None
    client = client or httpx.Client(timeout=10, follow_redirects=False)

    def get(path: str, optional: bool = False):
        with client.stream(
            "GET",
            "https://api.github.com" + path,
            headers={"Accept": "application/vnd.github+json"},
        ) as response:
            if optional and response.status_code == 404:
                return None
            if response.status_code in (403, 429):
                raise ValueError("GitHub request limit reached; retry later")
            if response.status_code != 200:
                raise ValueError("Public repository could not be read")
            chunks = bytearray()
            for chunk in response.iter_bytes():
                chunks.extend(chunk)
                if len(chunks) > MAX_RESPONSE_BYTES:
                    raise ValueError("GitHub response exceeds the snapshot size limit")
            import json

            return json.loads(chunks)

    try:
        prefix = f"/repos/{owner}/{repo}"
        metadata = get(prefix)
        if metadata.get("private"):
            raise ValueError("Only public repositories are supported")
        commit = get(prefix + "/commits/HEAD")
        sha = commit.get("sha", "")
        if not re.fullmatch(r"[a-fA-F0-9]{40,64}", sha):
            raise ValueError("Repository did not return a valid commit reference")
        files = []
        for path in ALLOWED_FILES:
            entry = get(prefix + f"/contents/{path}?ref={sha}", optional=True)
            if not isinstance(entry, dict) or entry.get("type") != "file":
                continue
            if entry.get("size", MAX_FILE_BYTES + 1) > MAX_FILE_BYTES:
                continue
            if entry.get("encoding") != "base64":
                continue
            raw = base64.b64decode(entry.get("content", ""))
            if len(raw) > MAX_FILE_BYTES:
                continue
            files.append(
                {
                    "path": path,
                    "text": raw.decode("utf-8", errors="replace"),
                    "source_url": f"https://github.com/{owner}/{repo}/blob/{sha}/{path}",
                }
            )
        return {
            "repository_url": f"https://github.com/{owner}/{repo}",
            "commit_sha": sha,
            "fetched_at": datetime.now(UTC).isoformat(),
            "files": files,
            "authorship_verified": False,
        }
    except httpx.HTTPError as exc:
        raise ValueError("GitHub is unavailable; retry later") from exc
    finally:
        if own_client:
            client.close()
