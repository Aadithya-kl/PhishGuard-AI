"""SlowAPI rate limiters.

* ``limiter``       — keyed by client IP (used for unauthenticated endpoints such as login).
* ``user_limiter``  — keyed by the authenticated user (set on ``request.state`` by the
                      tenant dependency), falling back to IP.

Storage defaults to in-process memory; set ``RATE_LIMIT_STORAGE_URI`` (e.g.
``redis://redis:6379/3``) so limits are shared across all API workers.
Client IPs come from uvicorn's ``--proxy-headers`` handling, so only trusted
proxies (``FORWARDED_ALLOW_IPS``) can influence them.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings

settings = get_settings()
_storage = settings.RATE_LIMIT_STORAGE_URI or "memory://"


def get_user_identifier(request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_storage,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"],
    headers_enabled=False,
)
user_limiter = Limiter(key_func=get_user_identifier, storage_uri=_storage, headers_enabled=False)
