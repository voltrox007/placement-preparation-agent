import base64

import httpx
import pytest

from placement_agent.integrations.github import parse_repository_url, snapshot_repository


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/a/b",
        "https://evil.com/a/b",
        "https://github.com@evil.com/a/b",
        "https://github.com/a/b/tree/main",
        "https://github.com/a/b?x=1",
        "https://github.com/a/..",
    ],
)
def test_urls_are_restricted(url):
    with pytest.raises(ValueError):
        parse_repository_url(url)


def test_snapshot_is_bounded_and_pinned():
    seen = []
    sha = "a" * 40

    def handle(request):
        seen.append(request)
        if request.url.path.endswith("/commits/HEAD"):
            return httpx.Response(200, json={"sha": sha})
        if "/contents/" in request.url.path:
            assert request.url.params["ref"] == sha
            if request.url.path.endswith("README.md"):
                return httpx.Response(
                    200,
                    json={
                        "type": "file",
                        "size": 5,
                        "encoding": "base64",
                        "content": base64.b64encode(b"hello").decode(),
                    },
                )
            return httpx.Response(404)
        return httpx.Response(200, json={"private": False})

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        result = snapshot_repository("https://github.com/student/project", client)
    assert len(seen) == 6
    assert all(request.method == "GET" and request.url.host == "api.github.com" for request in seen)
    assert result["files"][0]["text"] == "hello"
    assert sha in result["files"][0]["source_url"]
    assert result["authorship_verified"] is False


def test_redirect_is_not_followed():
    with httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(302, headers={"Location": "https://evil.com"}))
    ) as client:
        with pytest.raises(ValueError):
            snapshot_repository("https://github.com/student/project", client)
