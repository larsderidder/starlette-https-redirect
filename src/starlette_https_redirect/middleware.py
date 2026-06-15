"""
ASGI middleware for redirecting HTTP requests to HTTPS.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import Optional

from starlette.datastructures import URL
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class HTTPSRedirectMiddleware:
    """
    Redirect HTTP requests to HTTPS while allowing selected paths through.
    """

    def __init__(
        self,
        app: ASGIApp,
        excepted_paths: Optional[Collection[str]] = None,
        trust_x_forwarded_proto: bool = False,
    ) -> None:
        """
        Store the wrapped ASGI app and the paths that bypass redirects.
        """
        self.app = app
        self.excepted_paths = set(excepted_paths or ())
        self.trust_x_forwarded_proto = trust_x_forwarded_proto

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Redirect plain HTTP requests unless the path is excepted.
        """
        if self._should_redirect(scope):
            url = URL(scope=scope)
            redirected_url = url.replace(scheme="https", netloc=self._redirect_netloc(url))
            response = RedirectResponse(redirected_url, status_code=307)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)

    def _should_redirect(self, scope: Scope) -> bool:
        """
        Return whether an ASGI scope should be redirected to HTTPS.
        """
        return (
            scope.get("type") == "http"
            and scope.get("scheme") == "http"
            and not self._forwarded_as_https(scope)
            and scope.get("path") not in self.excepted_paths
        )

    def _forwarded_as_https(self, scope: Scope) -> bool:
        """
        Return whether a trusted proxy marked the original request as HTTPS.
        """
        if not self.trust_x_forwarded_proto:
            return False
        headers = dict(scope.get("headers") or [])
        return headers.get(b"x-forwarded-proto", b"").split(b",", 1)[0].strip().lower() == b"https"

    @staticmethod
    def _redirect_netloc(url: URL) -> str:
        """
        Return the netloc for a redirected URL without default ports.
        """
        return url.hostname if url.port in (80, 443) else url.netloc
