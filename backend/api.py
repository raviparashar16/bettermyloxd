from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, conlist
from typing import List, Optional
from scrape import LetterboxdScraper

app = FastAPI()

class MovieRequest(BaseModel):
    usernames: conlist(str, min_items=1, max_items=5)
    exclude_ids: Optional[conlist(str, max_items=5)] = []
    num_movies: int = 1

@app.post("/api/movies")
async def get_movie_recommendations(request: MovieRequest):
    try:
        scraper = LetterboxdScraper()
        movie = await scraper.scrape(request.num_movies, request.usernames, request.exclude_ids)
        return {
            "movie": {
                "id": movie.movie_id,
                "title": movie.title,
                "url": f"https://letterboxd.com{movie.letterboxd_path}",
            } if movie else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
