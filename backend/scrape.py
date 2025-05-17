from bs4 import BeautifulSoup
from typing import List, Dict, Tuple, NamedTuple, Union
import random
import asyncio
import aiohttp
from cython_utils import combine_dictionaries
from movie_cy import Movie
from concurrent.futures import ProcessPoolExecutor
import httpx
import base64
import itertools
from cache import RedisCache
import logging
import math
from config import SCRAPE_PER_USER, MAX_MOVIES_PER_PAGE, MAX_CONCURRENT_SCRAPES
from collections import deque
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PageResult(NamedTuple):
    ind: int
    movies: Dict[str, Movie]
    error: bool


class URLQueue:
    pages_per_user = math.ceil(SCRAPE_PER_USER / MAX_MOVIES_PER_PAGE)

    def __init__(self, usernames: List[str]):
        self.url_arr = [deque([(ind, i, f"{LetterboxdScraper.site_url}/{username}/watchlist/page/{i+1}")
                 for i in range(self.pages_per_user)])
                 for ind, username in enumerate(usernames)]
        self.dequeue_per_user = MAX_CONCURRENT_SCRAPES // len(usernames)
    
    def dequeue(self) -> List[Tuple[int, int, str]]:
        """Dequeue the URLs for the watchlist pages for each user"""
        dequeued_urls = []
        for ind in range(len(self.url_arr)):
            dequeued_urls.extend([self.url_arr[ind].popleft()
                                 for _ in range(min(self.dequeue_per_user, len(self.url_arr[ind])))])
        return dequeued_urls

    def clear(self, user_ind: int):
        """Clear the URLs for the watchlist pages for a given user"""
        self.url_arr[user_ind] = deque()

class LetterboxdScraper:
    site_url = "https://letterboxd.com"
    film_url_start = f"{site_url}/ajax/poster"
    film_url_end = "std/125x187/"
    
    def __init__(self,
                 seed: Union[int, None] = None,
                 max_workers: Union[int, None] = None,
                 redis_cache: RedisCache = None,
                ):
        self.seed = random.seed(seed) if seed is not None else None
        self.max_workers = max_workers
        self.redis_cache = redis_cache
    
    def _combine_dictionaries(self, all_movie_lists: List[Dict[str, Movie]]) -> Dict[str, Movie]:
        """Combine all movie lists into a single dictionary and remove duplicates"""
        combined_movies = combine_dictionaries(all_movie_lists)
        if not combined_movies:
            raise ValueError("No movies found in any of the watchlists!")
        return combined_movies
    
    def _remove_used_movies(self, movies: Dict[str, Movie], exclude_ids: List[str]) -> Dict[str, Movie]:
        """Remove movies that are already in the shortlist"""
        return {key: val for key, val in movies.items() if key not in exclude_ids}

    def _pick_movies(self, movies: Dict[str, Movie], exclude_ids: List[str], num_movies: int) -> List[Movie]:
        """Pick movies from the combined dictionary"""

        if len(movies) - len(exclude_ids) > num_movies:
            # if the number of movies in the combined dictionary minus the number of movies in the shortlist
            # is greater than the number of movies we need to return, pick random movies not in the shortlist
            # until we have the desired number
            final_picks = []
            while num_movies > 0:
                picks = self._random_pick(list(movies.keys()), num_movies)
                for movie_id in picks:
                    if movie_id not in exclude_ids:
                        final_picks.append(movies[movie_id])
                        num_movies -= 1
            return final_picks
        else:
            # otherwise, remove the movies that are already in the shortlist and pick randomly from the rest
            movies = self._remove_used_movies(movies, exclude_ids)
            if not movies:
                raise ValueError("No movies found in watchlists that are not already in the shortlist!")
            if len(movies) == num_movies:
                return list(movies.values())
            picks = self._random_pick(list(movies.keys()), num_movies)
            return [movies[movie_id] for movie_id in picks]
    
    def _random_pick(self, movie_keys: List[str], num_movies: int) -> List[str]:
        """Pick random movies from the combined dictionary"""
        return [random.sample(movie_keys, 1)[0]] if num_movies == 1 else random.sample(movie_keys, num_movies)
    
    @staticmethod
    def _get_url_from_usernames(usernames: List[str]) -> List[str]:
        """Construct the URLs for the watchlists"""
        return [f"{LetterboxdScraper.site_url}/{username}/watchlist/" for username in usernames]
    
    async def _fetch_page(
        self,
        session: aiohttp.ClientSession,
        executor: ProcessPoolExecutor,
        user_ind: int,
        page_ind: int,
        url: str,
        ) -> PageResult:
        """Fetch the watchlist page"""
        async with session.get(url) as response:
            if not response.ok:
                # if the first page is not found, raise an error
                if page_ind == 0:
                    raise aiohttp.ClientError(f"Failed to get watchlist pages. Please ensure your input is correct "
                                          f"(i.e. separated by spaces and valid usernames with public watchlists).")
                else:
                    # if the page is not the first watchlist page, return an empty dictionary and a True error flag
                    return PageResult(user_ind, {}, True)
            content = await response.read()
            loop = asyncio.get_event_loop()
            # use process pool to parse the watchlist page
            result = await loop.run_in_executor(executor, self._parse, content)
            return PageResult(user_ind, result, False)
    
    async def _handle_cache_search(self, usernames: List[str]) -> Tuple[List[Dict[str, Movie]], List[str]]:
        """Search the cache for stored results for given usernames"""
        parsed_results = []
        cache_miss_usernames = []
        
        # async gather the cached results for the given usernames
        cache_tasks = [self.redis_cache.get_cached_movies_async(username) for username in usernames]
        cache_results = await asyncio.gather(*cache_tasks)
        
        # extend the parsed results with the cached results
        for username, cached_movies in zip(usernames, cache_results):
            if cached_movies:
                parsed_results.extend(cached_movies)
            else:
                cache_miss_usernames.append(username)
        # return the parsed results and the usernames that were not found in the cache
        return parsed_results, cache_miss_usernames
    
    async def _handle_cache_write(self, usernames: List[str], movie_lists: List[List[Dict[str, Movie]]]):
        """Cache the results for the given usernames"""
        cache_tasks = [
            self.redis_cache.cache_movies_async(username, movie_list) for username, movie_list in zip(usernames, movie_lists)
        ]
        # async gather the cache tasks to cache the results for the given usernames
        await asyncio.gather(*cache_tasks)

    async def _scrape_async(self, usernames: List[str], use_cache: bool = True) -> List[Dict[str, Movie]]:
        """Scrape the watchlists for the given usernames"""
        usernames = list(set(usernames))
        parsed_results = []
        # if caching is enabled, search the cache for stored results for the given usernames
        if use_cache:
            parsed_results, cache_miss_usernames = await self._handle_cache_search(usernames)
            # if there are no cache misses, immediately return the parsed results
            if not cache_miss_usernames:
                return parsed_results
            usernames = cache_miss_usernames
        # create a queue to store the URLs for the watchlist pages
        url_queue = URLQueue(usernames)
        movie_lists = [[] for _ in usernames]
        movies_per_user = [0]*len(usernames)
        is_at_limit = [False]*len(usernames)
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=30, ttl_dns_cache=300)
            ) as session:
                # process the URLs in the queue until it is empty or all users have reached the limit of
                # number of movies we can parse per user
                while not sum(is_at_limit) == len(usernames):
                    tasks = [asyncio.create_task(self._fetch_page(session, executor, user_ind, page_ind, url))
                             for user_ind, page_ind, url in url_queue.dequeue()]
                    if tasks:
                        results = await asyncio.gather(*tasks)
                        for res_tuple in results:
                            user_ind, result, error = res_tuple
                            if not error:
                                movie_lists[user_ind].append(result)
                                movies_per_user[user_ind] += len(result)
                                # limit the number of movies we parse per user
                                if movies_per_user[user_ind] >= SCRAPE_PER_USER:
                                    is_at_limit[user_ind] = True
                                    url_queue.clear(user_ind)
                            else:
                                # if the page is not found, we've hit the limit for that user
                                is_at_limit[user_ind] = True
                                url_queue.clear(user_ind)
                    else:
                        break
        # write to cache the results for the given usernames
        asyncio.create_task(self._handle_cache_write(usernames, movie_lists))
        # extend the cached results with the results from the watchlists
        parsed_results.extend(list(itertools.chain.from_iterable(movie_lists)))
        return parsed_results
    
    async def _fetch_poster(self, movie: Movie) -> Tuple[Movie, Union[str, None]]:
        """Fetch the poster image for the given movie"""
        async with httpx.AsyncClient() as client:
            image_data = None
            try:
                response = await client.get(f"{LetterboxdScraper.film_url_start}{movie.letterboxd_path}{LetterboxdScraper.film_url_end}")
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "lxml")
                    img = soup.find("img", class_="image")
                    if img and img.get("src"):
                        img_response = await client.get(img["src"])
                        if img_response.status_code == 200:
                            # encode the image data in base64
                            image_base64 = base64.b64encode(img_response.content).decode('utf-8')
                            image_data = f"data:image/jpeg;base64,{image_base64}"
            except Exception as e:
                logger.info(f"Error fetching poster for {movie.title}: {e}")
            return movie, image_data

    async def scrape(self, num_movies: int, usernames: List[str], exclude_ids: List[str] = None, use_cache: bool = True) -> List[Dict]:
        """Scrape the watchlists for the given usernames and return movie suggestions"""
        movie_lists = await self._scrape_async(usernames, use_cache)
        movie_list = self._pick_movies(self._combine_dictionaries(movie_lists), exclude_ids or [], num_movies)
        poster_urls = await asyncio.gather(*[self._fetch_poster(movie) for movie in movie_list])
        return [
            {
                "title": tup[0].title,
                "id": tup[0].movie_id,
                "url": f"{LetterboxdScraper.site_url}{tup[0].letterboxd_path}",
                "image_data": tup[1]
            } for tup in poster_urls
        ]
    
    @staticmethod
    def _parse(response_data: bytes) -> Dict[str, Movie]:
        """Parse the watchlist page to get movie data"""
        try:
            soup = BeautifulSoup(response_data, "lxml")
            movie_elements = soup.find("ul", class_="poster-list")
            movie_elem_list = movie_elements.find_all("li")
            movies = {}
            for movie_elem in movie_elem_list:
                poster_div = movie_elem.find("div", class_="film-poster")
                if poster_div:
                    film_id = poster_div.get("data-film-id")
                    film_url = poster_div.get("data-target-link")
                    img = poster_div.find("img")
                    if img:
                        title = img.get("alt")
                        film_slug = poster_div.get("data-film-slug")
                        if film_slug:
                            movies[film_id] = Movie(film_id, film_url, title)
        except Exception as e:
            raise ValueError(f"Error parsing watchlist page: {e}")
        return movies
