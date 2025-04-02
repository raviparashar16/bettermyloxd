import redis.asyncio as redis
import json
from typing import List, Dict
from movie_cy import Movie
import time

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True,
)

# key for tracking last access times
LAST_ACCESS_KEY = "cache:last_access"
MAX_KEYS = 1000

async def update_last_access(username: str):
    """Update the last access time for a username in the cache."""
    await redis_client.zadd(LAST_ACCESS_KEY, {username: time.time()})

async def enforce_key_limit():
    """Enforce the maximum number of keys in the cache."""
    all_keys = await redis_client.keys("movies:*")
    if len(all_keys) > MAX_KEYS:
        # get the oldest keys based on last access time
        oldest_keys = await redis_client.zrange(LAST_ACCESS_KEY, 0, len(all_keys) - MAX_KEYS)
        # delete the oldest keys and their access times
        if oldest_keys:
            await redis_client.delete(*[f"movies:{key}" for key in oldest_keys])
            await redis_client.zrem(LAST_ACCESS_KEY, *oldest_keys)

async def close_redis_connection():
    """Close the Redis connection."""
    await redis_client.close()

def serialize_movie(movie: Movie) -> Dict[str, str]:
    """Convert a Movie object to a dictionary for JSON serialization."""
    return {
        'movie_id': movie.movie_id,
        'letterboxd_path': movie.letterboxd_path,
        'title': movie.title
    }

def deserialize_movie(data: Dict[str, str]) -> Movie:
    """Convert a dictionary back to a Movie object."""
    return Movie(
        movie_id=data['movie_id'],
        letterboxd_path=data['letterboxd_path'],
        title=data['title']
    )

def get_cache_key(username: str) -> str:
    """Generate a cache key from username."""
    return f"movies:{username}"

async def get_cached_movies_async(username: str) -> List[Dict[str, Movie]]:
    """Async version of get_cached_movies using redis.asyncio."""
    try:
        cache_key = get_cache_key(username)
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            await update_last_access(username)
            data = json.loads(cached_data)
            return [
                {
                    movie_id: deserialize_movie(movie_data)
                    for movie_id, movie_data in parsed_page_dict.items()
                }
                for parsed_page_dict in data
            ]
        return None
    except redis.RedisError as e:
        print(f"Redis error in get_cached_movies_async: {e}")
        return None

async def cache_movies_async(username: str, user_movie_list: List[Dict[str, Movie]], expire_seconds: int = 86400):
    """Async version of cache_movies using redis.asyncio."""
    try:
        await enforce_key_limit()
        cache_key = get_cache_key(username)
        serialized_data = [
            {
                movie_id: serialize_movie(movie)
                for movie_id, movie in parsed_page_dict.items()
            }
            for parsed_page_dict in user_movie_list
        ]
        async with redis_client.pipeline() as pipe:
            await pipe.setex(
                cache_key,
                expire_seconds,
                json.dumps(serialized_data)
            )
            await pipe.zadd(LAST_ACCESS_KEY, {username: time.time()})
            await pipe.execute()
            
    except redis.RedisError as e:
        print(f"Redis error in cache_movies_async: {e}")
