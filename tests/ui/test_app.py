from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_demo_requires_explicit_open_and_navigation_does_not_call_ai(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///" + str(tmp_path / "demo.db"))
    monkeypatch.setenv("LIVE_AI_ENABLED", "false")
    from placement_agent.ui.application import service

    service.clear()
    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run(timeout=20)
    assert not app.exception
    assert app.button[0].label == "Initialize / open local demo"
    app.button[0].click().run(timeout=20)
    assert not app.exception
    for page in (
        "Profile & Goal",
        "Diagnostic",
        "Learning Plan",
        "Learn & Practice",
        "Interview",
        "Progress & Data",
    ):
        app.sidebar.radio[0].set_value(page).run(timeout=20)
        assert not app.exception, page
    service.clear()
