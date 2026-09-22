# Placement Preparation Agent

A group software project for evidence-based placement preparation, powered by a **persistent Azure Foundry agent**.

**Status: MVP release deployed and validated.** The authenticated single-host demo runs on Azure Container Apps with persistent Azure Files storage, managed identity, Azure AI Search, and the pinned Foundry agent. See the [deployment guide](docs/deployment.md), [demo guide](docs/demo.md), and [v0.1.0 release notes](docs/release-notes-v0.1.0.md).

Track development in the [28 assigned issues](https://github.com/voltrox007/placement-preparation-agent/issues) and [seven milestones](https://github.com/voltrox007/placement-preparation-agent/milestones). Each of the four team members owns seven issues.

## Product goal

Help a student understand their target role, distinguish claimed skills from demonstrated skills, take reviewed assessments, follow a feasible study plan, and receive grounded feedback. New accepted evidence improves the next recommendation.

## Credit-conscious interaction model

Azure Foundry Agent Service is mandatory, but continuous AI conversation is not part of this project.

- Coding practice stores a submission and produces **one feedback report only when requested**. Code is not executed in the MVP.
- Mock interviews use a stored question set. Students submit all answers and request **one final report**. No adaptive follow-ups or per-answer AI calls.
- Resume/project viva questions may be prepared in one explicit, bounded batch and reused for that evidence version.
- Objective scoring, skill updates, plan scheduling, dashboards, and next-activity ranking use deterministic Python logic.
- Technical help is a single question and answer, initiated explicitly by the student. No automatic conversation continuation.
- Valid feedback is cached. Refreshing a page, reopening a report, and resuming a session must not trigger model calls.
- Application budgets limit tokens, calls, and retries. The MVP defaults to **one model response request per explicit AI action**, with no automatic AI retry or schema-repair call.

Credit usage cannot be guaranteed solely by limiting conversation turns: input/output tokens, embeddings, Search, and hosting also have costs. We will measure and cap usage.

## Implemented stack

Python · Streamlit · Azure Foundry Agent Service · Azure AI Search · SQLAlchemy/Alembic · SQLite · Pydantic · GitHub REST API.

One modular application, one persistent agent, one student database, and one curated educational index. No custom MCP server or multi-agent architecture in the MVP.

## Scope

Profiles and goals; confirmed resume/JD extraction; bounded public GitHub evidence; reviewed diagnostics; evidence-backed skill summaries; seven-day plans; cited learning answers; static code feedback; fixed text interviews; progress and privacy controls.

Not included: live coding assistance, conversational interviews, autonomous follow-ups, untrusted code execution, private repositories, voice/video, placement probability predictions, automated job applications, or model fine-tuning.

## Documentation

- [Master blueprint and decisions](docs/blueprint.md)
- [Architecture and data flows](docs/architecture.md)
- [Foundry agent, tools, and credit policy](docs/agent-and-tools.md)
- [Student state and database](docs/data-model.md)
- [Knowledge and retrieval](docs/knowledge.md)
- [Complete issue roadmap](docs/roadmap.md)
- [Team ownership](docs/team.md)
- [Development workflow](docs/development.md)
- [Testing and acceptance gates](docs/testing.md)
- [Setup and environment plan](docs/setup.md)
- [Deployment and privacy](docs/deployment.md)
- [Demo plan](docs/demo.md)
- [Implementation decisions and agent roles](docs/implementation-decisions.md)
- [Azure readiness](docs/azure-readiness.md)
- [Implementation status and pending GitHub updates](docs/implementation-status.md)

## Development workflow

Approved plan → GitHub issue → small branch/PR → relevant tests → fixes → documentation → review → merge → next issue.

Issue dependencies determine order. Agent roles own implementation tasks and independent review; existing human GitHub assignments remain unchanged. Preparatory code for a blocked integration is recorded as incomplete until its prerequisites and acceptance checks pass.

## Important limitations

Skill levels are transparent product heuristics, not employment predictions. Resume and repository claims do not establish mastery. AI feedback is provisional and traceable to evidence; it may be disputed. Static code review does not prove that code runs or passes tests.

## Privacy

This is a public repository. Use synthetic examples only. Never commit real resumes, student answers, credentials, database files, or private repository content.

## Hosted demo

The release endpoint is [placement-prep-agent-prod](https://placement-prep-agent-prod.proudtree-dd527a5a.uaenorth.azurecontainerapps.io/). Access requires a Microsoft Entra account in the project tenant. Anonymous requests redirect to Microsoft sign-in before reaching Streamlit.
