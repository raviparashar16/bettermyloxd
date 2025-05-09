import argparse
from scrape import LetterboxdScraper
from cache import RedisCache
from config import (REDIS_HOST,
                    REDIS_PORT,
                    REDIS_DB,
                    REDIS_CACHE_EXPIRE_SECONDS,
                    REDIS_CACHE_MAX_KEYS)
import asyncio

async def main():
    parser = argparse.ArgumentParser(description='Get random movie recommendation from Letterboxd watchlist(s)')
    parser.add_argument('-u', '--usernames', nargs='+', type=str, required=True, 
                       help='valid public Letterboxd profile usernames (min 1, max 5)', metavar='USERNAME')
    parser.add_argument('-n', '--num_movies', type=int, default=1,
                       help='Number of movies to return (default 1, max 5)', metavar='NUM_MOVIES')
    parser.add_argument('-e', '--exclude', nargs='+', type=str, default=[],
                       help='Movie IDs to exclude (max 5)', metavar='MOVIE_ID')
    args = parser.parse_args()

    if args.num_movies > 5:
        parser.error("Maximum 5 movies allowed")
    if len(args.usernames) > 5:
        parser.error("Maximum 5 usernames allowed")
    if len(args.exclude) > 5:
        parser.error("Maximum 5 excluded movies allowed")

    redis_cache = RedisCache(REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_CACHE_EXPIRE_SECONDS, REDIS_CACHE_MAX_KEYS)
    scraper = LetterboxdScraper(redis_cache=redis_cache)
    movie_list = await scraper.scrape(args.num_movies, args.usernames, args.exclude)

    if movie_list:
        for movie_num, movie in enumerate(movie_list):
            print(f"Movie {movie_num + 1}--------------------------------")
            print(f"Title: {movie['title']}")
            print(f"Movie ID: {movie['id']}")
            print(f"Letterboxd URL: {LetterboxdScraper.site_url}{movie['url']}")
    else:
        print("No movies found matching criteria")
    await redis_cache.close_redis_connection()

if __name__ == "__main__":
    asyncio.run(main())
