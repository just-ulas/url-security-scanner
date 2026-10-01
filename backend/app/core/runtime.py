import hashlib
import time
from functools import lru_cache

from fastapi import HTTPException, Request
from redis import Redis, RedisError

from app.core.config import get_settings


@lru_cache
def get_redis() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)


def enforce_scan_rate_limit(request: Request, redis: Redis) -> None:
    settings = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    ip_digest = hashlib.sha256(client_ip.encode("utf-8")).hexdigest()[:24]
    window = int(time.time() // 60)
    key = f"urlscanner:rate:{ip_digest}:{window}"
    try:
        count = redis.incr(key)
        if count == 1:
            redis.expire(key, 70)
    except RedisError as exc:
        raise HTTPException(status_code=503, detail="tarama kuyruğuna şu an ulaşılamıyor.") from exc
    if count > settings.scan_rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="çok kısa sürede fazla tarama istendi; bir dakika sonra yeniden dene.")
