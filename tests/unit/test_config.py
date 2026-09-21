"""Configuration tests require no third-party packages or Azure access."""

import unittest

from placement_agent.config import ConfigurationError, load_settings


def live_environment() -> dict[str, str]:
    return {
        "LIVE_AI_ENABLED": "true",
        "FOUNDRY_PROJECT_ENDPOINT": "https://example.services.ai.azure.com/api/projects/demo",
        "FOUNDRY_AGENT_NAME": "placement-coach",
        "FOUNDRY_AGENT_VERSION": "1",
        "MAX_INPUT_TOKENS": "1000",
        "MAX_OUTPUT_TOKENS": "500",
        "STUDENT_DAILY_TOKEN_LIMIT": "3000",
        "PROJECT_DAILY_TOKEN_LIMIT": "9000",
        "MAX_INTERVIEW_QUESTIONS": "5",
        "MAX_ANSWER_CHARS": "2000",
    }


class ConfigurationTests(unittest.TestCase):
    def test_offline_defaults(self) -> None:
        settings = load_settings({})
        self.assertFalse(settings.live_ai_enabled)
        self.assertIsNone(settings.project_daily_token_limit)

    def test_missing_live_settings_fail_closed(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "PROJECT_DAILY_TOKEN_LIMIT"):
            load_settings({"LIVE_AI_ENABLED": "true"})

    def test_each_live_requirement_is_mandatory(self) -> None:
        for name in live_environment():
            if name != "LIVE_AI_ENABLED":
                with self.subTest(name=name):
                    env = live_environment()
                    del env[name]
                    with self.assertRaises(ConfigurationError):
                        load_settings(env)

    def test_valid_explicit_limits(self) -> None:
        self.assertTrue(load_settings(live_environment()).live_ai_enabled)

    def test_invalid_numbers_and_boolean(self) -> None:
        for value in ("0", "-1", "1.5", "secret-value"):
            with self.subTest(value=value):
                with self.assertRaises(ConfigurationError) as caught:
                    load_settings({"MAX_INPUT_TOKENS": value})
                self.assertNotIn(value, str(caught.exception))
        with self.assertRaises(ConfigurationError):
            load_settings({"LIVE_AI_ENABLED": "yes"})

    def test_inconsistent_limits(self) -> None:
        for student_limit in ("10", "10000"):
            env = live_environment()
            env["STUDENT_DAILY_TOKEN_LIMIT"] = student_limit
            with self.assertRaisesRegex(ConfigurationError, "action <= student"):
                load_settings(env)

    def test_unsafe_or_malformed_endpoint(self) -> None:
        for endpoint in (
            "http://example.com", "https://user:secret@example.com",
            "https://x/?key=x", "https://[invalid",
        ):
            env = live_environment()
            env["FOUNDRY_PROJECT_ENDPOINT"] = endpoint
            with self.subTest(endpoint=endpoint), self.assertRaises(ConfigurationError):
                load_settings(env)

    def test_invalid_local_settings(self) -> None:
        for env in (
            {"AUTH_MODE": "hosted"}, {"LOG_LEVEL": "invalid"},
            {"DATABASE_URL": ""}, {"PRIVATE_STORAGE_DIR": " "},
        ):
            with self.subTest(env=env), self.assertRaises(ConfigurationError):
                load_settings(env)

    def test_interview_question_limit_matches_contract(self) -> None:
        for value in ("13", "1000"):
            with self.subTest(value=value), self.assertRaises(ConfigurationError):
                load_settings({"MAX_INTERVIEW_QUESTIONS": value})
        self.assertEqual(load_settings({"MAX_INTERVIEW_QUESTIONS": "12"}).max_interview_questions, 12)
