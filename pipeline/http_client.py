"""Shared HTTP client for OpenRouter calls.

We make at least one AI call per document (classification on hard docs,
vision on every doc, text-path on vision-off docs). Each `requests.post`
without a pooled connection pays the full TCP + TLS handshake — ~100–500 ms
of pure overhead per call. On a 300-doc batch that's 30–150 s of wasted
wall clock *per AI call type*.

This module exposes a single module-level `requests.Session` that every
pipeline OpenRouter call goes through, so concurrent calls issued from
different threads reuse sockets from a shared pool.

`requests.Session` is thread-safe for the kinds of operations we do
(independent POSTs), provided the Session is created once and reused.
That's the pattern here.
"""

from __future__ import annotations

import threading

import requests
from requests.adapters import HTTPAdapter

# Size the connection pool to the max concurrency we realistically hit.
# Backend limits batches to 3 concurrent docs today, but a single doc can
# fire 2 calls (classify + vision) back to back; raising pool_maxsize a
# bit above that avoids eviction+reconnect churn.
_POOL_CONNECTIONS = 8
_POOL_MAXSIZE = 16

_session: requests.Session | None = None
_lock = threading.Lock()


def get_session() -> requests.Session:
    """Return the process-wide shared Session, creating it on first use.

    Thread-safe — double-checked locking so the common hot path hits a
    single `if _session is not None` check without a mutex.
    """
    global _session
    if _session is not None:
        return _session
    with _lock:
        if _session is None:
            s = requests.Session()
            adapter = HTTPAdapter(
                pool_connections=_POOL_CONNECTIONS,
                pool_maxsize=_POOL_MAXSIZE,
            )
            s.mount("https://", adapter)
            s.mount("http://", adapter)
            _session = s
    return _session
