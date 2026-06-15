"""
Tests for HTTPS redirect middleware.
"""

import httpx
import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from starlette_https_redirect import HTTPSRedirectMiddleware


def _make_app(excepted_paths=None, trust_x_forwarded_proto=False) -> Starlette:
    """
    Create a minimal Starlette app wrapped with the middleware.
    """

    async def homepage(request):
        """
        Return a basic response for normal routes.
        """
        return PlainTextResponse("OK")

    async def health(request):
        """
        Return a basic response for health checks.
        """
        return PlainTextResponse("healthy")

    app = Starlette(
        routes=[
            Route("/", homepage),
            Route("/health", health),
            Route("/other", homepage),
        ],
    )
    app.add_middleware(
        HTTPSRedirectMiddleware,
        excepted_paths=excepted_paths,
        trust_x_forwarded_proto=trust_x_forwarded_proto,
    )
    return app


@pytest.mark.asyncio
async def test_http_request_is_redirected_to_https() -> None:
    """
    Redirect plain HTTP requests to HTTPS.
    """
    app = _make_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"].startswith("https://")


@pytest.mark.asyncio
async def test_https_request_is_not_redirected() -> None:
    """
    Pass HTTPS requests through without a redirect.
    """
    app = _make_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="https://testserver") as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_trusted_forwarded_proto_https_is_not_redirected() -> None:
    """
    Pass requests through when a trusted proxy marked the original scheme as HTTPS.
    """
    app = _make_app(trust_x_forwarded_proto=True)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/", headers={"x-forwarded-proto": "https"})

    assert response.status_code == 200
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_excepted_path_is_not_redirected() -> None:
    """
    Pass excepted HTTP paths through without a redirect.
    """
    app = _make_app(excepted_paths=["/health"])
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.text == "healthy"


@pytest.mark.asyncio
async def test_non_excepted_path_is_still_redirected() -> None:
    """
    Redirect paths that are not in the exception list.
    """
    app = _make_app(excepted_paths=["/health"])
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/other", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"].startswith("https://")


@pytest.mark.asyncio
async def test_custom_excepted_paths() -> None:
    """
    Pass all configured exception paths through without redirects.
    """
    app = _make_app(excepted_paths=["/health", "/other"])
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        health_resp = await client.get("/health")
        other_resp = await client.get("/other")

    assert health_resp.status_code == 200
    assert other_resp.status_code == 200


@pytest.mark.asyncio
async def test_redirect_preserves_path_and_query() -> None:
    """
    Preserve the original path and query string in the redirect URL.
    """
    app = _make_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/other?foo=bar", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "https://testserver/other?foo=bar"


@pytest.mark.asyncio
async def test_redirect_strips_default_http_port() -> None:
    """
    Remove the default HTTP port from redirect URLs.
    """
    app = _make_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver:80") as client:
        response = await client.get("/other", follow_redirects=False)

    assert response.headers["location"] == "https://testserver/other"
