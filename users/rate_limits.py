from django.core.cache import cache


def hit_rate_limit(
    *, scope: str, identity: str, limit: int, window_seconds: int
) -> bool:
    """Retorna True si supera limite para la identidad dada."""
    identity = (identity or "anon").strip().lower() or "anon"
    key = f"ratelimit:{scope}:{identity}"
    current = cache.get(key, 0)
    if current >= limit:
        return True

    cache.set(key, current + 1, timeout=window_seconds)
    return False
