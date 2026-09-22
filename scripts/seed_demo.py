"""Create a synthetic, repeatable student journey for the project showcase."""

import json

from placement_agent.bootstrap import build_service
from placement_agent.services.catalog import ITEMS


def main() -> None:
    service = build_service()
    student_id = "demo-student"
    service.ensure_student(student_id)
    service.save_profile(student_id, "Demo Student", "Synthetic final-year computing student", 45, 225)
    service.set_goal(student_id, "backend", 45, 225)
    session = service.start_session(student_id, "diagnostic")
    correct_by_prompt = {
        prompt: options[correct]
        for questions in ITEMS.values()
        for prompt, options, correct, _explanation in questions
    }
    for index, item in enumerate(session["items"]):
        if item.get("answer") is not None:
            continue
        correct = correct_by_prompt[item["prompt"]]
        answer = correct if index % 4 else next(option for option in item["options"] if option != correct)
        service.submit_answer(student_id, item["id"], answer, f"seed-demo:{item['id']}")
    completed = service.finish_session(student_id, session["id"])
    plan = service.create_plan(student_id)
    print(
        json.dumps(
            {
                "student_id": student_id,
                "diagnostic_score": completed["score"],
                "plan_items": len(plan["items"]),
                "synthetic": True,
            }
        )
    )


if __name__ == "__main__":
    main()
