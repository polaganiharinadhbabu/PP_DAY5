import hashlib
import os
import threading
import time

from collections import defaultdict
from fastapi import HTTPException, Request, status

_counts = defaultdict(lambda: (0, 0))
_lock = threading.Lock()


def enforce_rate_limit(request: Request) -> None:
    limit = max(
        1,
        int(os.getenv("RATE_LIMIT_REQUESTS", "60")),
    )

    window = max(
        1,
        int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
    )

    identity = (
        request.headers.get("X-API-Key")
        or (
            request.client.host
            if request.client
            else "unknown"
        )
    )

    key_hash = hashlib.sha256(
        identity.encode()
    ).hexdigest()[:24]

    now = int(time.time())
    window_start = now - (now % window)
    retry_after = max(1, window - (now % window))

    with _lock:
        count, bucket_start = _counts[key_hash]

        if bucket_start != window_start:
            count = 0

        count += 1
        _counts[key_hash] = (
            count,
            window_start,
        )

    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Try again later.",
            },
            headers={
                "Retry-After": str(retry_after)
            },
        )
