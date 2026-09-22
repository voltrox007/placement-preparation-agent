"""Validate local configuration, optionally read a pinned agent; never generate a response."""

import argparse
import json

from placement_agent.agent.client import FoundryProvider
from placement_agent.config import load_settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-remote",
        action="store_true",
        help="Read-only Azure agent verification using local Entra credentials",
    )
    args = parser.parse_args()
    settings = load_settings()
    missing = [
        name
        for name, value in {
            "FOUNDRY_PROJECT_ENDPOINT": settings.foundry_project_endpoint,
            "FOUNDRY_AGENT_NAME": settings.foundry_agent_name,
            "FOUNDRY_AGENT_VERSION": settings.foundry_agent_version,
        }.items()
        if not value
    ]
    if missing:
        print(json.dumps({"ready": False, "missing": missing}))
        raise SystemExit(1)
    if not args.check_remote:
        print(
            json.dumps(
                {
                    "local_configuration_present": True,
                    "remote_verified": False,
                    "live_ai_enabled": settings.live_ai_enabled,
                }
            )
        )
        return
    provider = FoundryProvider(settings)
    try:
        print(json.dumps({"remote_verified": True, **provider.prepare()}))
    finally:
        provider.close()


if __name__ == "__main__":
    main()
