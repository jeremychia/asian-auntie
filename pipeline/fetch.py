"""
HTTP fetching with per-domain rate limiting and exponential-backoff retry.
"""

import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import socket
from collections import defaultdict
from typing import Optional

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

_last_fetch: dict[str, float] = defaultdict(float)


def fetch(
    url: str,
    delay: float = 2.0,
    timeout: int = 20,
    retries: int = 3,
) -> Optional[str]:
    """Fetch URL, honouring per-domain rate limit and retrying on transient errors.

    Returns decoded HTML string, or None on permanent failure.
    """
    domain = urllib.parse.urlparse(url).netloc

    for attempt in range(retries):
        elapsed = time.time() - _last_fetch[domain]
        if elapsed < delay:
            time.sleep(delay - elapsed)

        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                _last_fetch[domain] = time.time()
                return data.decode("utf-8", errors="ignore")

        except urllib.error.HTTPError as e:
            _last_fetch[domain] = time.time()
            if e.code in (404, 410, 403):
                print(f"  [HTTP {e.code}] {url}", file=sys.stderr)
                return None
            backoff = delay * (2**attempt)
            print(
                f"  [HTTP {e.code}] {url} — retry {attempt + 1}/{retries} in {backoff:.1f}s",
                file=sys.stderr,
            )
            time.sleep(backoff)

        except (urllib.error.URLError, socket.timeout, OSError) as e:
            _last_fetch[domain] = time.time()
            backoff = delay * (2**attempt)
            print(
                f"  [FETCH ERROR] {url} — {e} — retry {attempt + 1}/{retries} in {backoff:.1f}s",
                file=sys.stderr,
            )
            time.sleep(backoff)

    print(f"  [FAILED] {url} after {retries} attempts", file=sys.stderr)
    return None
