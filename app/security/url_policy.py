"""Strict URL safety policy and secure fetch helpers."""

from __future__ import annotations

import ipaddress
import json
import socket
from dataclasses import dataclass
from typing import Iterable
from urllib.error import HTTPError
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, Request, build_opener


@dataclass
class UrlPolicy:
    """Policy controls for remote fetch safety."""

    allow_cross_domain_redirects: bool = False
    max_redirects: int = 2
    timeout_seconds: float = 10.0
    max_bytes: int = 1_000_000
    allowed_schemes: tuple[str, ...] = ("https",)
    allow_localhost: bool = False


class _NoRedirectHandler(HTTPRedirectHandler):
    """Disable automatic redirect following so policy can validate each hop."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def canonicalize_url(url: str) -> str:
    """Normalize query parameter ordering and strip fragments."""

    parsed = urlparse(url.strip())
    query_items = sorted(parse_qsl(parsed.query, keep_blank_values=False))
    query = urlencode(query_items, doseq=True)

    normalized_path = parsed.path.rstrip("/")
    if not normalized_path and parsed.scheme and parsed.netloc:
        normalized_path = ""

    canonical = parsed._replace(path=normalized_path, query=query, fragment="")
    return urlunparse(canonical)


def _is_public_ip(ip_str: str) -> bool:
    ip = ipaddress.ip_address(ip_str)
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def _resolve_public_ips(hostname: str) -> None:
    try:
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ValueError(f"failed to resolve hostname: {hostname}") from exc

    ips: set[str] = set()
    for row in addr_info:
        if row and row[-1]:
            ip = row[-1][0]
            if ip:
                ips.add(ip)

    if not ips:
        raise ValueError(f"hostname resolved to no addresses: {hostname}")

    for ip in ips:
        if not _is_public_ip(ip):
            raise ValueError(f"blocked non-public destination IP: {ip}")


def validate_safe_url(url: str, policy: UrlPolicy) -> None:
    """Validate scheme, host, and resolved addresses against safety policy."""

    parsed = urlparse(url)
    if parsed.scheme not in policy.allowed_schemes:
        allowed = ", ".join(policy.allowed_schemes)
        raise ValueError(f"URL scheme not allowed; expected one of: {allowed}")

    hostname = parsed.hostname or ""
    if not hostname:
        raise ValueError("URL must include a hostname")

    if policy.allow_localhost and hostname.lower() in {"localhost", "127.0.0.1", "::1"}:
        return

    _resolve_public_ips(hostname)


def _validate_content_type(content_type: str, expected_content_types: Iterable[str]) -> None:
    if not expected_content_types:
        return
    lowered = (content_type or "").lower()
    if any(fragment in lowered for fragment in expected_content_types):
        return
    raise ValueError(f"unexpected content type: {content_type}")


def _validate_redirect(source_url: str, target_url: str, policy: UrlPolicy) -> None:
    validate_safe_url(target_url, policy)
    if policy.allow_cross_domain_redirects:
        return

    source_host = (urlparse(source_url).hostname or "").lower()
    target_host = (urlparse(target_url).hostname or "").lower()
    if source_host != target_host:
        raise ValueError(
            f"redirect across domain boundary is blocked: {source_host} -> {target_host}"
        )


def fetch_text(
    url: str,
    *,
    policy: UrlPolicy,
    expected_content_types: tuple[str, ...] = ("text/html", "application/json", "text/plain"),
    user_agent: str = "last-minute/0.2",
) -> str:
    """Fetch remote text safely with SSRF and redirect/content guards."""

    opener = build_opener(_NoRedirectHandler)
    current_url = canonicalize_url(url)
    hops = 0

    while True:
        validate_safe_url(current_url, policy)
        request = Request(current_url, headers={"User-Agent": user_agent, "Accept": "*/*"})

        try:
            response = opener.open(request, timeout=policy.timeout_seconds)
            content_type = response.headers.get("Content-Type", "")
            _validate_content_type(content_type, expected_content_types)
            data = response.read(policy.max_bytes + 1)
            if len(data) > policy.max_bytes:
                raise ValueError("response exceeded maximum allowed size")
            return data.decode("utf-8", errors="ignore")
        except HTTPError as exc:
            if exc.code not in (301, 302, 303, 307, 308):
                raise
            location = exc.headers.get("Location", "")
            if not location:
                raise ValueError("redirect response missing Location header") from exc
            next_url = canonicalize_url(urljoin(current_url, location))
            _validate_redirect(current_url, next_url, policy)
            hops += 1
            if hops > policy.max_redirects:
                raise ValueError("too many redirects")
            current_url = next_url


def fetch_json(
    url: str,
    *,
    policy: UrlPolicy,
    expected_content_types: tuple[str, ...] = (
        "application/json",
        "text/json",
        "application/vnd.github+json",
    ),
    user_agent: str = "last-minute/0.2",
) -> dict:
    """Fetch JSON payload with strict URL policy."""

    payload = fetch_text(
        url,
        policy=policy,
        expected_content_types=expected_content_types,
        user_agent=user_agent,
    )
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError("expected a JSON object payload")
    return parsed
