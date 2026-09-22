"""Create a new tool-free Foundry prompt-agent version without invoking the model."""

import argparse
import json

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential

from placement_agent.agent.client import INSTRUCTIONS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--agent-name", required=True)
    parser.add_argument("--model", required=True)
    args = parser.parse_args()

    with AIProjectClient(
        endpoint=args.endpoint,
        credential=DefaultAzureCredential(),
    ) as project:
        agent = project.agents.create_version(
            agent_name=args.agent_name,
            definition=PromptAgentDefinition(
                model=args.model,
                instructions=INSTRUCTIONS.strip(),
                tools=[],
            ),
        )
        print(
            json.dumps(
                {
                    "agent_name": agent.name,
                    "agent_version": str(agent.version),
                    "model": agent.definition.model,
                    "tools": len(agent.definition.tools or []),
                }
            )
        )


if __name__ == "__main__":
    main()
