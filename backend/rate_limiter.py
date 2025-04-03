import time
from typing import Optional
from cache import RedisCache

class RateLimiter:
    def __init__(self, redis_cache: RedisCache, window: int = 60, max_requests: int = 20):
        self.redis = redis_cache
        self.window = window
        self.max_requests = max_requests

    async def is_rate_limited(self, key: str) -> bool:
        """
        Check if the given key is rate limited.
        Returns True if rate limited, False otherwise.
        """
        current_time = time.time()
        window_start = current_time - self.window

        pipe = self.redis.redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(current_time): current_time})
        pipe.expire(key, self.window)
        _, request_count, _, _ = await pipe.execute()

        return request_count > self.max_requests

    async def get_remaining_requests(self, key: str) -> int:
        """
        Get the number of remaining requests for the given key.
        """
        current_time = time.time()
        window_start = current_time - self.window
        await self.redis.redis_client.zremrangebyscore(key, 0, window_start)
        request_count = await self.redis.redis_client.zcard(key)
        return max(0, self.max_requests - request_count)

    async def get_reset_time(self, key: str) -> Optional[float]:
        """
        Get the time when the rate limit will reset.
        Returns None if not rate limited.
        """
        oldest_request = await self.redis.redis_client.zrange(key, 0, 0, withscores=True)
        if not oldest_request:
            return None
        request_count = await self.redis.redis_client.zcard(key)
        if request_count <= self.max_requests:
            return None
        return oldest_request[0][1] + self.window
