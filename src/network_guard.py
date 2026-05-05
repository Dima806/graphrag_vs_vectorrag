from urllib.parse import urlparse

_ALLOWED_HOSTS: frozenset[str] = frozenset({"localhost", "127.0.0.1", "::1"})


def validate_url(url: str) -> str:
    """Raise ValueError if url does not point to localhost."""
    host = urlparse(url).hostname or ""
    if host not in _ALLOWED_HOSTS:
        msg = f"NetworkGuard: non-localhost URL rejected: {url!r}"
        raise ValueError(msg)
    return url
