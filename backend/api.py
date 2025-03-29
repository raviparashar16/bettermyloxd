from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, conlist, conint
from typing import List, Optional
from scrape import LetterboxdScraper
from collections import defaultdict
import time

app = FastAPI(
    title="Letterboxd Movie Recommender API",
    description="API for getting random movie recommendations from Letterboxd watchlists",
    version="1.0.0"
)

# Simple rate limiting
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
    usernames: conlist(str, min_items=1, max_items=5)
    exclude_ids: Optional[conlist(str, max_items=5)] = []
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
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
    try:
        scraper = LetterboxdScraper()
        movie_list = scraper.scrape(movie_request.num_movies, movie_request.usernames, movie_request.exclude_ids)
        return [
            {
                "title": movie.title,
                "id": movie.movie_id,
                "url": f"{LetterboxdScraper.site_url}{movie.letterboxd_path}",
                "image_url": f"{LetterboxdScraper.film_url_start}{movie.letterboxd_path}{LetterboxdScraper.film_url_end}"
            } for movie in movie_list
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")