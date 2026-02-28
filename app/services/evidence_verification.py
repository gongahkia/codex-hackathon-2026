"""URL reachability verification for candidate evidence links."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List
from urllib.request import Request, urlopen

from app.models.candidate import Candidate
from app.security.url_policy import UrlPolicy, validate_safe_url
from app.services.evidence import extract_build_writeup_links, extract_code_artifact_links


@dataclass
class VerificationResult:
    """Per-candidate verification record."""

    verified_code_links: List[str]
    verified_writeup_links: List[str]
    verification_errors: List[str]


ProbeFn = Callable[[str, UrlPolicy, float], tuple[bool, str | None]]


def probe_url_reachable(
    url: str,
    policy: UrlPolicy,
    timeout_seconds: float = 1.5,
) -> tuple[bool, str | None]:
    """Validate URL and probe reachability with a lightweight HEAD request."""

    try:
        validate_safe_url(url, policy)
    except Exception as exc:
        return False, str(exc)

    request = Request(url, method="HEAD", headers={"User-Agent": "last-minute/0.2"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            if 200 <= response.status < 400:
                return True, None
            return False, f"unexpected status {response.status}"
    except Exception as exc:
        return False, str(exc)


def verify_candidate_evidence(
    candidate: Candidate,
    *,
    policy: UrlPolicy | None = None,
    max_links_per_type: int = 2,
    probe_fn: ProbeFn = probe_url_reachable,
) -> VerificationResult:
    """Probe candidate code/writeup URLs and return verified evidence links."""

    effective_policy = policy or UrlPolicy()
    verified_code_links: List[str] = []
    verified_writeup_links: List[str] = []
    errors: List[str] = []

    for url in extract_code_artifact_links(candidate)[: max(0, max_links_per_type)]:
        ok, error = probe_fn(url, effective_policy, 1.5)
        if ok:
            verified_code_links.append(url)
        elif error:
            errors.append(f"{url}: {error}")

    for url in extract_build_writeup_links(candidate)[: max(0, max_links_per_type)]:
        ok, error = probe_fn(url, effective_policy, 1.5)
        if ok:
            verified_writeup_links.append(url)
        elif error:
            errors.append(f"{url}: {error}")

    return VerificationResult(
        verified_code_links=verified_code_links,
        verified_writeup_links=verified_writeup_links,
        verification_errors=errors,
    )


def verify_candidates_evidence(
    candidates: list[Candidate],
    *,
    policy: UrlPolicy | None = None,
    max_links_per_type: int = 2,
    probe_fn: ProbeFn = probe_url_reachable,
) -> list[Candidate]:
    """Attach verification metadata to candidate signals in-place and return candidates."""

    effective_policy = policy or UrlPolicy()
    for candidate in candidates:
        record = verify_candidate_evidence(
            candidate,
            policy=effective_policy,
            max_links_per_type=max_links_per_type,
            probe_fn=probe_fn,
        )
        candidate.signals["verified_code_links"] = record.verified_code_links
        candidate.signals["verified_writeup_links"] = record.verified_writeup_links
        candidate.signals["verification_errors"] = record.verification_errors
    return candidates
