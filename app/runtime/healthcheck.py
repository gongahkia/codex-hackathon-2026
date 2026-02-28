"""Runtime health checks."""

from __future__ import annotations

import time
from urllib.error import URLError
from urllib.request import urlopen

from app.security.url_policy import UrlPolicy, validate_safe_url


def probe_dev_server(
    url: str,
    *,
    retries: int = 10,
    delay_seconds: float = 1.0,
    timeout_seconds: float = 2.0,
    policy: UrlPolicy | None = None,
) -> bool:
    """Poll dev server endpoint until healthy or retries exhausted."""

    effective_policy = policy or UrlPolicy()
    validate_safe_url(url, effective_policy)

    for _ in range(retries):
        try:
            with urlopen(url, timeout=timeout_seconds) as response:
                if 200 <= response.status < 400:
                    return True
        except URLError:
            pass
        time.sleep(delay_seconds)
    return False
