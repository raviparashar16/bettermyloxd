from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, conlist, conint
from typing import List, Optional
from scrape import LetterboxdScraper
from collections import defaultdict
import time
import aiohttp

app = FastAPI(
    title="Letterboxd Movie Recommender API",
    description="API for getting random movie recommendations from Letterboxd watchlists",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, need to replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RATE_LIMIT_WINDOW = 60  # 1 minute
RATE_LIMIT_REQUESTS = 20  # 20 requests per minute
request_history = defaultdict(list)

def check_rate_limit(request: Request) -> bool:
    client_ip = request.client.host
    current_time = time.time()
    request_history[client_ip] = [t for t in request_history[client_ip] 
                                if current_time - t < RATE_LIMIT_WINDOW]
    if len(request_history[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False
    request_history[client_ip].append(current_time)
    return True

class MovieRequest(BaseModel):
    usernames: conlist(str, min_length=1, max_length=5)
    exclude_ids: Optional[conlist(str, max_length=5)] = []
    num_movies: conint(ge=1, le=5) = 1

    class Config:
        schema_extra = {
            "example": {
                "usernames": ["username1", "username2"],
                "exclude_ids": ["123", "456"],
                "num_movies": 3
            }
        }

@app.post("/api/movies")
async def get_movie_recommendations(request: Request, movie_request: MovieRequest):
    if not check_rate_limit(request):
        raise HTTPException(status_code=429, detail="You've made too many requests. Please try again later.")
    try:
        scraper = LetterboxdScraper()
        movie_list = await scraper.scrape(movie_request.num_movies, movie_request.usernames, movie_request.exclude_ids)
        return movie_list
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch watchlist page: {e}. Please check that the usernames are valid and try again.")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")