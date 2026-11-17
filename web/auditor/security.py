"""SSRF protection and safe HTTP session for the RankPilot web application.

RankPilot fetches user-supplied URLs from the server, so every request is
validated before it leaves the machine:

* only http/https schemes are accepted;
* the hostname is resolved with DNS and every resolved address must be a
  global (public) unicast address — loopback, private, link-local,
  shared, reserved and multicast ranges are rejected;
* validation runs inside the session for *every* request, including each
  redirect hop, so a public site cannot redirect RankPilot to an
  internal service;
* responses are streamed and capped at MAX_RESPONSE_BYTES;
* all requests carry the engine's timeout.
"""

from __future__ import annotations

import socket
from ipaddress import ip_address
from urllib.parse import urlparse

import requests

MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MiB per response
CHUNK_SIZE = 64 * 1024


class SSRFError(Exception):
    """Raised when a URL must not be fetched for security reasons.

    The message is a translation key of the web interface.
    """


def assert_public_url(url: str) -> None:
    """Validate that ``url`` points to a public internet address.

    Raises SSRFError (translation key as message) otherwise.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SSRFError("err_url_scheme")
    host = parsed.hostname
    if not host:
        raise SSRFError("err_url_invalid")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise SSRFError("err_connection") from None
    if not infos:
        raise SSRFError("err_url_invalid")

    for info in infos:
        ip = ip_address(info[4][0])
        if not ip.is_global:
            raise SSRFError("err_ssrf_blocked")


class SSRFSafeSession(requests.Session):
    """Requests session that revalidates every URL, redirects included."""

    def send(self, request, **kwargs):
        assert_public_url(request.url)
        kwargs["stream"] = True
        response = super().send(request, **kwargs)
        return self._enforce_size_limit(response)

    @staticmethod
    def _enforce_size_limit(response: requests.Response) -> requests.Response:
        total = 0
        chunks = []
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            total += len(chunk)
            if total > MAX_RESPONSE_BYTES:
                response.close()
                raise SSRFError("err_response_too_large")
            chunks.append(chunk)
        response._content = b"".join(chunks)
        response._content_consumed = True
        return response
