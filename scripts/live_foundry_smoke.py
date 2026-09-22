"""Run one budgeted, idempotent, grounded Foundry response for release verification."""

import json

from placement_agent.agent.coach import AICoach
from placement_agent.bootstrap import build_service
from placement_agent.config import load_settings
from placement_agent.domain.contracts import RetrievedPassage, StudentContext


def main() -> None:
    settings = load_settings()
    if not settings.live_ai_enabled:
        raise SystemExit("LIVE_AI_ENABLED must be true for the explicit smoke request")

    service = build_service()
    service.ensure_student("foundry-smoke-final")
    profile = service.profile("foundry-smoke-final")
    context = StudentContext(
        student_id="foundry-smoke-final",
        state_version=profile["state_version"],
    )
    passage = RetrievedPassage(
        citation_id="smoke-source-1",
        title="Database index trade-off fixture",
        text=(
            "A database index can speed up reads while requiring additional storage "
            "and adding maintenance work to writes."
        ),
        source_url="https://example.invalid/approved-smoke-fixture",
        locator="fixture paragraph 1",
        corpus_version="smoke-v1",
    )
    engine = service.factory.kw["bind"]
    coach = AICoach(settings, engine)
    result = coach.answer(
        context,
        "foundry-smoke-v4-20260922-attempt-3",
        "What trade-off does a database index introduce?",
        [passage],
    )
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
