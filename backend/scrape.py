from bs4 import BeautifulSoup
from typing import List, Dict, Tuple, Union
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
        combined_movies = combine_dictionaries(all_movie_lists)
        if not combined_movies:
            raise ValueError("No movies found in any of the watchlists!")
        return combined_movies
    
    def _remove_used_movies(self, movies: Dict[str, Movie], exclude_ids: List[str]) -> Dict[str, Movie]:
        return {key: val for key, val in movies.items() if key not in exclude_ids}

    def _pick_movies(self, movies: Dict[str, Movie], exclude_ids: List[str], num_movies: int) -> List[Movie]:
        if len(movies) - len(exclude_ids) > num_movies:
            final_picks = []
            while num_movies > 0:
                picks = self._random_pick(list(movies.keys()), num_movies)
                for movie_id in picks:
                    if movie_id not in exclude_ids:
                        final_picks.append(movies[movie_id])
                        num_movies -= 1
            return final_picks
        else:
            movies = self._remove_used_movies(movies, exclude_ids)
            if not movies:
                raise ValueError("No movies found in watchlists that are not already in the shortlist!")
            if len(movies) == num_movies:
                return list(movies.values())
            picks = self._random_pick(list(movies.keys()), num_movies)
            return [movies[movie_id] for movie_id in picks]
    
    def _random_pick(self, movie_keys: List[str], num_movies: int) -> List[str]:
        return [random.sample(movie_keys, 1)[0]] if num_movies == 1 else random.sample(movie_keys, num_movies)
    
    @staticmethod
    def _get_url_from_usernames(usernames: List[str]) -> List[str]:
        return [f"{LetterboxdScraper.site_url}/{username}/watchlist/" for username in usernames]
    
    async def _fetch_page(
        self,
        session: aiohttp.ClientSession,
        ind: int,
        url: str,
        executor: ProcessPoolExecutor,
        url_queue: asyncio.Queue
        ) -> Tuple[int, Dict[str, Movie]]:
        async with session.get(url) as response:
            if not response.ok:
                raise aiohttp.ClientError(f"Failed to fetch watchlist page: {response.status} {response.reason}")
            content = await response.read()
            try:
                soup = BeautifulSoup(content, "lxml")
                next_button = soup.find("a", class_="next")
                if next_button:
                    next_url = f"{LetterboxdScraper.site_url}{next_button['href']}"
                    await url_queue.put((ind, next_url))
            except Exception as e:
                raise ValueError(f"Error parsing watchlist page: {e}")
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(executor, self._parse, content)
            return ind, result
    
    async def _handle_cache_search(self, usernames: List[str]) -> Tuple[List[Dict[str, Movie]], List[str]]:
        parsed_results = []
        cache_miss_usernames = []
        
        cache_tasks = [self.redis_cache.get_cached_movies_async(username) for username in usernames]
        cache_results = await asyncio.gather(*cache_tasks)
        
        for username, cached_movies in zip(usernames, cache_results):
            if cached_movies:
                parsed_results.extend(cached_movies)
            else:
                cache_miss_usernames.append(username)
                
        return parsed_results, cache_miss_usernames
    
    async def _handle_cache_write(self, usernames: List[str], movie_lists: List[List[Dict[str, Movie]]]):
        cache_tasks = [
            self.redis_cache.cache_movies_async(username, movie_list) for username, movie_list in zip(usernames, movie_lists)
        ]
        await asyncio.gather(*cache_tasks)

    async def _scrape_async(self, usernames: List[str], use_cache: bool = True) -> List[Dict[str, Movie]]:
        usernames = list(set(usernames))
        parsed_results = []
        if use_cache:
            parsed_results, cache_miss_usernames = await self._handle_cache_search(usernames)
            if not cache_miss_usernames:
                return parsed_results
            usernames = cache_miss_usernames

        url_queue = asyncio.Queue()
        for ind, url in enumerate(self._get_url_from_usernames(usernames)):
            await url_queue.put((ind, url))
        movie_lists = [[] for _ in usernames]
        movies_per_user = [0]*len(usernames)
        is_at_limit = [False]*len(usernames)
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=30, ttl_dns_cache=300)
            ) as session:
                while not (url_queue.empty() or sum(is_at_limit) == len(usernames)):
                    tasks = []
                    # process up to 30 URLs concurrently
                    for _ in range(min(30, url_queue.qsize())):
                        ind, url = await url_queue.get()
                        if not is_at_limit[ind]:
                            tasks.append(asyncio.create_task(
                                self._fetch_page(session, ind, url, executor, url_queue)
                            ))
                    if tasks:
                        results = await asyncio.gather(*tasks)
                        for ind, result in results:
                            if not is_at_limit[ind]:
                                movie_lists[ind].append(result)
                                movies_per_user[ind] += len(result)
                                # limit the number of movies we parse per user
                                if movies_per_user[ind] >= 6000:
                                    is_at_limit[ind] = True
        asyncio.create_task(self._handle_cache_write(usernames, movie_lists))
        
        parsed_results.extend(list(itertools.chain.from_iterable(movie_lists)))
        return parsed_results
    
    async def _fetch_poster(self, movie: Movie) -> Tuple[Movie, Union[str, None]]:
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
                            image_base64 = base64.b64encode(img_response.content).decode('utf-8')
                            image_data = f"data:image/jpeg;base64,{image_base64}"
            except Exception as e:
                print(f"Error fetching poster: {e}")
            return movie, image_data

    def scrape_sync(self, num_movies: int, usernames: List[str], exclude_ids: List[str] = [], use_cache: bool = True) -> List[Movie]:
        movie_lists = asyncio.run(self._scrape_async(usernames, use_cache))
        return self._pick_movies(self._combine_dictionaries(movie_lists), exclude_ids, num_movies)
    
    async def scrape(self, num_movies: int, usernames: List[str], exclude_ids: List[str] = [], use_cache: bool = True) -> List[Dict]:
        movie_lists = await self._scrape_async(usernames, use_cache)
        movie_list = self._pick_movies(self._combine_dictionaries(movie_lists), exclude_ids, num_movies)
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
