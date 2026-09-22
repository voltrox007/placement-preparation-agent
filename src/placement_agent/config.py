"""Side-effect-free configuration; loading settings never makes an AI request."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlparse


class ConfigurationError(ValueError):
    """Invalid configuration; error messages never echo supplied values."""


def _positive_int(env: Mapping[str, str], name: str) -> int | None:
    value = env.get(name, "").strip()
    if not value:
        return None
    try:
        number = int(value)
    except ValueError:
        raise ConfigurationError(f"{name} must be a positive integer") from None
    if number <= 0:
        raise ConfigurationError(f"{name} must be a positive integer")
    return number


@dataclass(frozen=True)
class Settings:
    live_ai_enabled: bool
    foundry_project_endpoint: str
    foundry_agent_name: str
    foundry_agent_version: str
    max_input_tokens: int | None
    max_output_tokens: int | None
    student_daily_token_limit: int | None
    project_daily_token_limit: int | None
    max_interview_questions: int | None
    max_answer_chars: int | None
    database_url: str
    private_storage_dir: str
    auth_mode: str
    log_level: str
    search_endpoint: str = ""
    search_index_name: str = ""
    embedding_deployment: str = ""
    knowledge_corpus_version: str = ""
    embedding_dimensions: int | None = None


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Read process settings without dotenv, disk writes, or cloud access.

    P06 must implement atomic usage reservations. Configuration alone is not a
    budget ledger and does not authorize any automatic model calls.
    """
    values = os.environ if env is None else env
    enabled = values.get("LIVE_AI_ENABLED", "false").strip().lower()
    if enabled not in {"true", "false"}:
        raise ConfigurationError("LIVE_AI_ENABLED must be true or false")
    endpoint = values.get("FOUNDRY_PROJECT_ENDPOINT", "").strip()
    agent_name = values.get("FOUNDRY_AGENT_NAME", "").strip()
    agent_version = values.get("FOUNDRY_AGENT_VERSION", "").strip()
    names = (
        "MAX_INPUT_TOKENS",
        "MAX_OUTPUT_TOKENS",
        "STUDENT_DAILY_TOKEN_LIMIT",
        "PROJECT_DAILY_TOKEN_LIMIT",
        "MAX_INTERVIEW_QUESTIONS",
        "MAX_ANSWER_CHARS",
    )
    limits = {name: _positive_int(values, name) for name in names}
    if limits["MAX_INTERVIEW_QUESTIONS"] is not None and limits["MAX_INTERVIEW_QUESTIONS"] > 12:
        raise ConfigurationError("MAX_INTERVIEW_QUESTIONS cannot exceed the 12-item batch contract")
    if enabled == "true":
        required = {
            "FOUNDRY_PROJECT_ENDPOINT": endpoint,
            "FOUNDRY_AGENT_NAME": agent_name,
            "FOUNDRY_AGENT_VERSION": agent_version,
            **limits,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ConfigurationError("Live AI requires: " + ", ".join(missing))
        try:
            parsed = urlparse(endpoint)
            valid = (
                parsed.scheme == "https"
                and bool(parsed.hostname)
                and not parsed.username
                and not parsed.password
                and not parsed.query
                and not parsed.fragment
            )
        except ValueError:
            valid = False
        if not valid:
            raise ConfigurationError("FOUNDRY_PROJECT_ENDPOINT must be a clean HTTPS URL")
        input_limit = limits["MAX_INPUT_TOKENS"]
        output_limit = limits["MAX_OUTPUT_TOKENS"]
        student_limit = limits["STUDENT_DAILY_TOKEN_LIMIT"]
        project_limit = limits["PROJECT_DAILY_TOKEN_LIMIT"]
        assert input_limit and output_limit and student_limit and project_limit
        if input_limit + output_limit > student_limit or student_limit > project_limit:
            raise ConfigurationError("Token limits must satisfy action <= student <= project")
    auth_mode = values.get("AUTH_MODE", "local_demo").strip()
    if auth_mode != "local_demo":
        raise ConfigurationError("Only AUTH_MODE=local_demo is implemented; hosting is not ready")
    log_level = values.get("LOG_LEVEL", "INFO").strip().upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ConfigurationError("LOG_LEVEL is invalid")
    database_url = values.get("DATABASE_URL", "sqlite:///data/private/placement.db").strip()
    private_storage_dir = values.get("PRIVATE_STORAGE_DIR", "data/private").strip()
    if not database_url or not private_storage_dir:
        raise ConfigurationError("DATABASE_URL and PRIVATE_STORAGE_DIR must not be blank")
    search_endpoint = values.get("AZURE_SEARCH_ENDPOINT", "").strip()
    search_index_name = values.get("AZURE_SEARCH_INDEX_NAME", "").strip()
    embedding_deployment = values.get("EMBEDDING_DEPLOYMENT", "").strip()
    corpus_version = values.get("KNOWLEDGE_CORPUS_VERSION", "").strip()
    embedding_dimensions = _positive_int(values, "EMBEDDING_DIMENSIONS")
    search_values = (
        search_endpoint,
        search_index_name,
        embedding_deployment,
        corpus_version,
        embedding_dimensions,
    )
    if any(search_values) and not all(search_values):
        raise ConfigurationError("Azure retrieval configuration must be complete")
    if search_endpoint and not search_endpoint.startswith("https://"):
        raise ConfigurationError("AZURE_SEARCH_ENDPOINT must be HTTPS")
    return Settings(
        live_ai_enabled=enabled == "true",
        foundry_project_endpoint=endpoint,
        foundry_agent_name=agent_name,
        foundry_agent_version=agent_version,
        max_input_tokens=limits["MAX_INPUT_TOKENS"],
        max_output_tokens=limits["MAX_OUTPUT_TOKENS"],
        student_daily_token_limit=limits["STUDENT_DAILY_TOKEN_LIMIT"],
        project_daily_token_limit=limits["PROJECT_DAILY_TOKEN_LIMIT"],
        max_interview_questions=limits["MAX_INTERVIEW_QUESTIONS"],
        max_answer_chars=limits["MAX_ANSWER_CHARS"],
        database_url=database_url,
        private_storage_dir=private_storage_dir,
        auth_mode=auth_mode,
        log_level=log_level,
        search_endpoint=search_endpoint,
        search_index_name=search_index_name,
        embedding_deployment=embedding_deployment,
        knowledge_corpus_version=corpus_version,
        embedding_dimensions=embedding_dimensions,
    )
