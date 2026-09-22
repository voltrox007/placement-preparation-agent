"""Explicit user actions drive persistence and one-shot feedback requests."""

import json
from uuid import uuid4

import streamlit as st

from placement_agent.bootstrap import build_service
from placement_agent.config import load_settings
from placement_agent.integrations.document_parser import extract_document
from placement_agent.integrations.github import snapshot_repository

STUDENT = "demo-student"
PAGES = [
    "Home",
    "Profile & Goal",
    "Diagnostic",
    "Learning Plan",
    "Learn & Practice",
    "Interview",
    "Progress & Data",
]


@st.cache_resource
def service():
    return build_service()


def profile_page(svc):
    st.header("Profile & Goal")
    profile = svc.profile(STUDENT)
    goal = svc.goal(STUDENT) or {}
    with st.form("profile"):
        name = st.text_input("Display name", value=profile.get("display_name", "Student"))
        education = st.text_input("Education", value=profile.get("education", ""))
        daily = st.number_input("Daily study minutes", 10, 480, int(goal.get("daily_minutes", 45)))
        weekly = st.number_input("Weekly study minutes", 10, 3360, int(goal.get("weekly_minutes", 225)))
        st.caption("Initial role: junior Python/backend software engineer")
        if st.form_submit_button("Save profile and goal"):
            svc.save_profile(STUDENT, name, education, int(daily), int(weekly))
            svc.set_goal(STUDENT, "backend", int(daily), int(weekly))
            st.success("Profile and goal saved")
    st.subheader("Resume evidence")
    upload = st.file_uploader("Text-based resume (PDF or TXT)", type=["pdf", "txt"])
    if st.button("Extract uploaded text", disabled=upload is None):
        st.session_state["resume_text"] = extract_document(upload.name, upload.getvalue())
    with st.form("resume"):
        text = st.text_area("Resume text", key="resume_text", height=180, max_chars=60000)
        facts = st.text_area("Confirmed skills and project facts", max_chars=10000)
        confirmed = st.checkbox("I reviewed and confirm these facts")
        if st.form_submit_button("Save confirmed resume"):
            if not confirmed or not text.strip():
                st.warning("Provide resume text and confirm the facts first")
            else:
                svc.save_document(STUDENT, "resume", text, {"student_confirmed": facts})
                st.success("Confirmed resume saved. Claims do not establish skill mastery.")
    st.subheader("Public GitHub project")
    with st.form("github"):
        title = st.text_input("Project title")
        description = st.text_area("Your contribution")
        url = st.text_input("Public repository URL", placeholder="https://github.com/owner/repository")
        if st.form_submit_button("Import bounded repository snapshot"):
            snapshot = snapshot_repository(url)
            svc.save_project(STUDENT, title or url, description, snapshot)
            st.success("Repository evidence saved. Repository content does not verify authorship.")
    for project in svc.projects(STUDENT):
        with st.expander(project.get("title", "Project")):
            st.json(project)


def session_page(svc, kind):
    label = {"diagnostic": "Diagnostic", "practice": "Practice", "interview": "Mock interview"}[kind]
    st.subheader(label)
    st.caption("Questions are fixed. Answers are saved individually. AI feedback is requested once after completion.")
    key = f"{kind}_session"
    if st.button(f"Start new {label.lower()}"):
        result = svc.start_session(STUDENT, kind)
        st.session_state[key] = result["id"]
    session_id = st.session_state.get(key)
    if not session_id:
        st.info("Start a session to begin. Existing answers remain in your progress history.")
        return
    result = svc.get_session(STUDENT, session_id)
    st.write(f"Status: {result['status']} · Answered {result['answered']} of {result['total']}")
    for index, item in enumerate(result["items"], 1):
        with st.expander(f"Question {index}: {item['prompt']}", expanded=item.get("answer") is None):
            if item.get("answer") is not None:
                st.write("Your answer:", item["answer"])
                if item.get("feedback"):
                    st.write(item["feedback"])
                continue
            with st.form(f"answer_{item['id']}"):
                options = item.get("options") or []
                answer = (
                    st.radio("Answer", options, index=None) if options else st.text_area("Your answer", max_chars=10000)
                )
                if st.form_submit_button("Save answer"):
                    if not answer:
                        st.warning("Enter an answer first")
                    else:
                        request_key = st.session_state.setdefault(f"request_{item['id']}", str(uuid4()))
                        svc.submit_answer(STUDENT, item["id"], answer, request_key)
                        st.rerun()
    if result["status"] != "completed" and st.button("Finish session"):
        svc.finish_session(STUDENT, session_id)
        st.rerun()
    if result["status"] == "completed":
        st.success("Session completed and saved")
        if result.get("score") is not None:
            st.write("Observed objective score:", result["score"])
        st.info("Open answers and code require an explicit feedback request. Code is never executed.")
        enabled = load_settings().live_ai_enabled
        if st.button("Request one feedback report", disabled=not enabled):
            from placement_agent.services.ai_feedback import request_session_feedback

            st.session_state[f"feedback_{session_id}"] = request_session_feedback(
                STUDENT, session_id, f"session-feedback:{session_id}"
            )
        if f"feedback_{session_id}" in st.session_state:
            st.json(st.session_state[f"feedback_{session_id}"])
        if not enabled:
            st.caption("Live Foundry feedback is not configured. No model call is made.")


def main():
    st.set_page_config(page_title="Placement Preparation Agent", page_icon="🎓", layout="wide")
    st.title("Placement Preparation Agent")
    st.sidebar.warning("Local demo only · single demo student · no hosted authentication")
    try:
        svc = service()
        if not st.session_state.get("initialized"):
            if st.button("Initialize / open local demo"):
                svc.ensure_student(STUDENT)
                st.session_state["initialized"] = True
                st.rerun()
            st.info("Open the local demo to use your saved preparation profile.")
            return
        page = st.sidebar.radio("Navigate", PAGES)
        if page == "Home":
            st.header("Your preparation")
            st.write("Build evidence through diagnostics and practice, then choose your next activity.")
            st.json(svc.goal(STUDENT) or {"next_step": "Set your profile and goal"})
            st.dataframe(svc.skill_summary(STUDENT), use_container_width=True)
        elif page == "Profile & Goal":
            profile_page(svc)
        elif page == "Diagnostic":
            session_page(svc, "diagnostic")
        elif page == "Learning Plan":
            st.header("Seven-day learning plan")
            if st.button("Create / revise plan"):
                svc.create_plan(STUDENT)
            plan = svc.get_plan(STUDENT)
            if plan:
                st.dataframe(plan["items"], use_container_width=True)
            else:
                st.info("Set a goal, complete a diagnostic, then create your plan.")
        elif page == "Learn & Practice":
            st.header("Learn & Practice")
            st.dataframe(svc.activities(), width="stretch")
            with st.form("learning_question"):
                query = st.text_area("Ask one learning question", max_chars=3000)
                submitted = st.form_submit_button(
                    "Request one grounded answer", disabled=not load_settings().live_ai_enabled
                )
                if submitted and query.strip():
                    from placement_agent.services.ai_feedback import answer_learning

                    key = st.session_state.setdefault(f"learning_key_{query}", str(uuid4()))
                    st.session_state["learning_answer"] = answer_learning(STUDENT, query, key)
            if "learning_answer" in st.session_state:
                st.json(st.session_state["learning_answer"])
            if not load_settings().live_ai_enabled:
                st.caption("Foundry learning feedback is disabled until live Azure configuration is verified.")
            session_page(svc, "practice")
        elif page == "Interview":
            session_page(svc, "interview")
        elif page == "Progress & Data":
            st.header("Progress & Data")
            st.json(svc.progress(STUDENT))
            st.caption("Completion is not mastery. Unknown skills have not been assessed sufficiently.")
            st.download_button(
                "Export my data",
                json.dumps(svc.export_student(STUDENT), indent=2, default=str),
                "preparation-export.json",
            )
            confirmation = st.text_input("Type DELETE to delete the local demo student's data")
            if st.button("Delete my data", disabled=confirmation != "DELETE"):
                svc.delete_student(STUDENT)
                st.session_state.clear()
                st.rerun()
    except (ValueError, LookupError) as exc:
        st.error(str(exc))
