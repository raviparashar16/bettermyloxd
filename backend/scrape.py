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


class LetterboxdScraper:
    site_url = "https://letterboxd.com"
    film_url_start = f"{site_url}/ajax/poster"
    film_url_end = "std/125x187/"
    
    def __init__(self, seed: Union[int, None] = None, max_workers: Union[int, None] = None):
        self.seed = random.seed(seed) if seed is not None else None
        self.max_workers = max_workers
    
    def _combine_dictionaries(self, all_movie_lists: List[Dict[str, Movie]]) -> Dict[str, Movie]:
        combined_movies = combine_dictionaries(all_movie_lists)
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
            if len(movies) == num_movies:
                return list(movies.values())
            picks = self._random_pick(list(movies.keys()), num_movies)
            return [movies[movie_id] for movie_id in picks]
    
    def _random_pick(self, movie_keys: List[str], num_movies: int) -> List[str]:
        return [random.choice(movie_keys)] if num_movies == 1 else random.choices(movie_keys, k=num_movies)
    
    @staticmethod
    def _get_url_from_usernames(usernames: List[str]) -> List[str]:
        return [f"{LetterboxdScraper.site_url}/{username}/watchlist/" for username in usernames]
    
    async def _fetch_page(self, session: aiohttp.ClientSession, url: str, executor: ProcessPoolExecutor, url_queue: asyncio.Queue) -> Dict[str, Movie]:
        async with session.get(url) as response:
            content = await response.read()
            soup = BeautifulSoup(content, "lxml")
            next_button = soup.find("a", class_="next")
            if next_button:
                next_url = f"{LetterboxdScraper.site_url}{next_button['href']}"
                await url_queue.put(next_url)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(executor, self._parse, content)
            return result

    async def _scrape_async(self, usernames: List[str]) -> List[Dict[str, Movie]]:
        url_queue = asyncio.Queue()
        for url in self._get_url_from_usernames(usernames):
            await url_queue.put(url)
        movie_lists = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=30, ttl_dns_cache=300)
            ) as session:
                while not url_queue.empty():
                    tasks = []
                    # Process up to 30 URLs concurrently
                    for _ in range(min(30, url_queue.qsize())):
                        url = await url_queue.get()
                        tasks.append(asyncio.create_task(
                            self._fetch_page(session, url, executor, url_queue)
                        ))
                    results = await asyncio.gather(*tasks)
                    movie_lists.extend(results)
        return movie_lists
    
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
                pass
            return movie, image_data

    def scrape_sync(self, num_movies: int, usernames: List[str], exclude_ids: List[str] = []) -> List[Movie]:
        movie_lists = asyncio.run(self._scrape_async(usernames))
        return self._pick_movies(self._combine_dictionaries(movie_lists), exclude_ids, num_movies)
    
    async def scrape(self, num_movies: int, usernames: List[str], exclude_ids: List[str] = []) -> List[Dict]:
        movie_lists = await self._scrape_async(usernames)
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
        return movies
