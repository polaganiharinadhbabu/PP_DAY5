import hmac
import os

from fastapi import Header, HTTPException, status

LOCAL_DEVELOPMENT_KEY = "local-dev-key"


def require_api_key(
    x_api_key: str | None = Header(
        default=None,
        alias="X-API-Key",
    ),
) -> str:
    expected_key = os.getenv(
        "API_KEY",
        LOCAL_DEVELOPMENT_KEY,
    )

    if (
        not x_api_key
        or not hmac.compare_digest(
            x_api_key,
            expected_key,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "unauthorized",
                "message": "A valid X-API-Key header is required.",
            },
        )

    return x_api_key
