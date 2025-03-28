from bs4 import BeautifulSoup
import requests
from typing import List, Dict, Deque, Union
import random
from collections import deque
from cython_utils import combine_dictionaries
from movie_cy import Movie


class LetterboxdScraper:
    def __init__(self, seed: Union[int, None] = None):
        self.seed = random.seed(seed) if seed is not None else None
        self.site_url = "https://letterboxd.com"
        self.film_url_start = f"{self.site_url}/ajax/poster"
        self.film_url_end = "std/125x187/"
    
    def _combine_dictionaries(self, all_movie_lists: List[Dict[str, Movie]]) -> Dict[str, Movie]:
        return combine_dictionaries(all_movie_lists)
    
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
    
    def _get_url_from_usernames(self, usernames: List[str]) -> List[str]:
        return [f"{self.site_url}/{username}/watchlist/" for username in usernames]

    def scrape(self, num_movies: int, usernames: List[str], exclude_ids: List[str] = []) -> List[Movie]:
        queue = deque(self._get_url_from_usernames(usernames))
        movie_lists = []
        while queue:
            response = requests.get(queue.popleft())
            movie_lists.append(self._parse(response.content, queue))
        movie_lists = self._combine_dictionaries(movie_lists)
        return self._pick_movies(movie_lists, exclude_ids, num_movies)
    
    def _parse(self, response_data: bytes, queue: Deque[str]) -> Dict[str, Movie]:
        soup = BeautifulSoup(response_data, "html.parser")
        next_button = soup.find("a", class_="next")
        if next_button:
            queue.append(f"{self.site_url}{next_button['href']}")
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
