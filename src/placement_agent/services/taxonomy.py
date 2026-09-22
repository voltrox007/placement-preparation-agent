"""Versioned, deterministic role requirements used by goals and JD confirmation."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import cast

TAXONOMY_VERSION = "backend-v1"

SKILL_ALIASES = {
    "python": "python",
    "python3": "python",
    "data structures": "dsa",
    "algorithms": "dsa",
    "dsa": "dsa",
    "sql": "sql",
    "sqlite": "sql",
    "postgres": "sql",
    "postgresql": "sql",
    "git": "engineering",
    "testing": "engineering",
    "software engineering": "engineering",
}

ROLE_TEMPLATES = {
    "backend": {
        "version": TAXONOMY_VERSION,
        "name": "Junior Python/backend software engineer",
        "requirements": ("python", "dsa", "sql", "engineering"),
        "prerequisites": {"dsa": ("python",), "sql": (), "engineering": ("python",), "python": ()},
    }
}


def validate_taxonomy(templates=ROLE_TEMPLATES) -> None:
    """Reject missing skills and prerequisite cycles at startup/test time."""
    for role in templates.values():
        requirements = set(role["requirements"])
        graph = role["prerequisites"]
        if set(graph) != requirements or any(set(values) - requirements for values in graph.values()):
            raise ValueError("Role prerequisites must reference exactly the role requirements")
        indegree = {skill: 0 for skill in requirements}
        children: dict[str, list[str]] = defaultdict(list)
        for skill, prerequisites in graph.items():
            for prerequisite in prerequisites:
                children[prerequisite].append(skill)
                indegree[skill] += 1
        queue = deque(skill for skill, count in indegree.items() if count == 0)
        visited = 0
        while queue:
            visited += 1
            for child in children[queue.popleft()]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        if visited != len(requirements):
            raise ValueError("Role prerequisite graph contains a cycle")


def role_snapshot(role_id: str) -> dict:
    if role_id not in ROLE_TEMPLATES:
        raise ValueError("Unsupported role template")
    role = ROLE_TEMPLATES[role_id]
    prerequisites = cast(dict[str, tuple[str, ...]], role["prerequisites"])
    return {
        "role_id": role_id,
        "name": role["name"],
        "version": role["version"],
        "requirements": list(role["requirements"]),
        "prerequisites": {key: list(value) for key, value in prerequisites.items()},
        "provenance": "reviewed_role_template",
    }


def map_job_description(text: str) -> dict:
    """Produce a reviewable draft; callers must explicitly confirm it."""
    lowered = text.casefold()
    matches: dict[str, list[str]] = defaultdict(list)
    for alias, skill_id in sorted(SKILL_ALIASES.items(), key=lambda pair: (-len(pair[0]), pair[0])):
        if alias in lowered:
            matches[skill_id].append(alias)
    return {
        "taxonomy_version": TAXONOMY_VERSION,
        "mapped_requirements": sorted(matches),
        "matched_aliases": dict(sorted(matches.items())),
        "unresolved_requirements": [],
        "provenance": "deterministic_alias_match",
        "confirmed": False,
    }


validate_taxonomy()
