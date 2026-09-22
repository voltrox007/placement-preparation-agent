from placement_agent.security import redact


def test_redaction_covers_nested_secret_fields_without_mutation():
    event = {
        "student_id": "student-a",
        "authorization": "Bearer abc.def",
        "nested": {"api_key": "top-secret", "safe": "visible"},
    }
    safe = redact(event)
    assert safe == {
        "student_id": "student-a",
        "authorization": "[REDACTED]",
        "nested": {"api_key": "[REDACTED]", "safe": "visible"},
    }
    assert event["nested"]["api_key"] == "top-secret"


def test_redaction_removes_credentials_embedded_in_text():
    safe = redact("Authorization: Bearer abc.def api-key=secret-value")
    assert "abc.def" not in safe
    assert "secret-value" not in safe
    assert safe == "Authorization: Bearer [REDACTED] api-key=[REDACTED]"
