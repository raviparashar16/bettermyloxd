from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, conlist, conint
from typing import Optional
import asyncio
from config import (REDIS_HOST,
                    REDIS_PORT,
                    REDIS_DB,
                    RATE_LIMIT_WINDOW,
                    RATE_LIMIT_MAX_REQUESTS,
                    REDIS_CACHE_EXPIRE_SECONDS,
                    REDIS_CACHE_MAX_KEYS,
                    SSL_KEYFILE,
                    SSL_CERTFILE)
from cache import RedisCache
from rate_limiter import RateLimiter
from scrape import LetterboxdScraper
from contextlib import asynccontextmanager
import ssl
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Redis cache and rate limiter
redis_cache = RedisCache(host=REDIS_HOST,
                         port=REDIS_PORT,
                         db=REDIS_DB,
                         expire_seconds=REDIS_CACHE_EXPIRE_SECONDS,
                         max_keys=REDIS_CACHE_MAX_KEYS,)
rate_limiter = RateLimiter(redis_cache, RATE_LIMIT_WINDOW, RATE_LIMIT_MAX_REQUESTS)

# Create a queue for processing requests
request_queue = asyncio.Queue()
processing_tasks = set()

class MovieRequest(BaseModel):
    usernames: conlist(str, min_length=1, max_length=5)
    exclude_ids: Optional[conlist(str, max_length=5)] = []
    num_movies: conint(ge=1, le=5) = 1
    use_cache: bool = True

    class Config:
        schema_extra = {
            "example": {
                "usernames": ["username1", "username2"],
                "exclude_ids": ["123", "456"],
                "num_movies": 3
            }
        }

async def process_requests():
    """Background task to process queued requests"""
    scraper = LetterboxdScraper()
    while True:
        try:
            request_data = await request_queue.get()
            try:
                movies = await scraper.scrape(
                    num_movies=request_data['num_movies'],
                    usernames=request_data['usernames'],
                    exclude_ids=request_data['exclude_ids'],
                    use_cache=request_data['use_cache']
                )
                request_data['result'] = movies
                request_data['error'] = None
            except Exception as e:
                request_data['result'] = None
                request_data['error'] = str(e)
            finally:
                request_data['event'].set()
                request_queue.task_done()
        except Exception as e:
            print(f"Error in request processor: {e}")
            await asyncio.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    logger.info("Starting up application...")
    try:
        await redis_cache.redis_client.ping()
        logger.info("Successfully connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise
    
    # start background task
    processor_task = asyncio.create_task(process_requests())
    processing_tasks.add(processor_task)
    processor_task.add_done_callback(processing_tasks.discard)
    yield
    # shutdown
    for task in processing_tasks:
        task.cancel()
    await asyncio.gather(*processing_tasks, return_exceptions=True)
    await redis_cache.close_redis_connection()
    logger.info("Redis connection closed")

app = FastAPI(
    title="Letterboxd Movie Recommender API",
    description="API for getting random movie recommendations from Letterboxd watchlists",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/movies")
async def get_movie_recommendations(request: Request, movie_request: MovieRequest):
    """Endpoint to get movie recommendations from Letterboxd watchlists"""
    client_ip = request.client.host
    rate_limit_key = f"rate_limit:{client_ip}"
    logger.info(f"Received request for usernames: {movie_request.usernames}")
    if await rate_limiter.is_rate_limited(rate_limit_key):
        reset_time = await rate_limiter.get_reset_time(rate_limit_key)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Too many requests",
                "reset_time": reset_time,
                "message": "Please try again later"
            }
        )

    try:
        event = asyncio.Event()
        request_data = {
            'usernames': movie_request.usernames,
            'exclude_ids': movie_request.exclude_ids,
            'num_movies': movie_request.num_movies,
            'use_cache': movie_request.use_cache,
            'event': event
        }
        logger.info("Adding request to queue...")
        await request_queue.put(request_data)
        logger.info(f"Current queue size: {request_queue.qsize()}")
        logger.info("Waiting for queue processing...")
        await event.wait()
        logger.info("Processing complete")
        if request_data['error']:
            raise HTTPException(status_code=500, detail=request_data['error'])

        remaining = await rate_limiter.get_remaining_requests(rate_limit_key)
        
        return {
            "movies": request_data['result'],
            "remaining_requests": remaining
        }
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint that returns the current queue size and processing status."""
    return {
        "status": "healthy",
        "queue_size": request_queue.qsize(),
        "processing_tasks": len(processing_tasks)
    }

if __name__ == "__main__":
    import uvicorn
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(SSL_CERTFILE, SSL_KEYFILE)
    uvicorn.run(app, host="0.0.0.0", port=8000, ssl_keyfile=SSL_KEYFILE, ssl_certfile=SSL_CERTFILE)
