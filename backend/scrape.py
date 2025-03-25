from bs4 import BeautifulSoup
import requests
from typing import List, Dict, Deque, Union
import random
from collections import deque, namedtuple


Movie = namedtuple('Movie', ['movie_id', 'letterboxd_url'])

class LetterboxdScraper:
    def __init__(self, seed: Union[int, None] = None):
        self.seed = random.seed(seed) if seed is not None else None
        self.url = "https://letterboxd.com/"
    
    def _combine_dictionaries(self, all_movie_lists: List[Dict[str, Movie]]) -> Dict[str, Movie]:
        combined_list = all_movie_lists[0]
        for movie_list_ind in range(1,len(all_movie_lists)):
            for movie_id, movie in all_movie_lists[movie_list_ind].items():
                if movie_id not in combined_list:
                    combined_list[movie_id] = movie
        return combined_list
    
    def _remove_used_movies(self, movies: Dict[str, Movie], exclude_ids: List[str]) -> Dict[str, Movie]:
        return {key: val for key, val in movies.items() if key not in exclude_ids}

    def _pick_movie(self, movies: Dict[str, Movie], exclude_ids: List[str]) -> Union[Movie, None]:
        if len(movies) > len(exclude_ids):
            while True:
                pick = random.choice(list(movies.keys()))
                if pick not in exclude_ids:
                    movie = movies[pick]
                    return movie
        else:
            movies = self._remove_used_movies(movies, exclude_ids)
            if not movies:
                return None

            return movies[random.choice(list(movies.keys()))] if movies else None
    
    def _get_url_from_usernames(self, usernames: List[str]) -> List[str]:
        return [f"{self.url}{username}/watchlist/" for username in usernames]

    def scrape(self, usernames: List[str], exclude_ids: List[str] = []) -> Union[Movie, None]:
        queue = deque(self._get_url_from_usernames(usernames))
        movie_lists = []
        while queue:
            response = requests.get(queue.popleft())
            movie_lists.append(self._parse(response.content, queue))
        movie_lists = self._combine_dictionaries(movie_lists)
        return self._pick_movie(movie_lists, exclude_ids)
    
    def _parse(self, response_data: bytes, queue: Deque[str]) -> Dict[str, Movie]:
        soup = BeautifulSoup(response_data, "html.parser")
        next_button = soup.find("a", class_="next")
        if next_button:
            queue.append(f"{self.url}{next_button['href']}")
        movie_elements = soup.find("ul", class_="poster-list")
        movie_elem_list = movie_elements.find_all("li")
        movies = {}
        for movie_elem in movie_elem_list:
            poster_div = movie_elem.find("div", class_="film-poster")
            if poster_div:
                film_id = poster_div.get("data-film-id")
                film_url = poster_div.get("data-target-link")
                movies[film_id] = Movie(film_id, film_url)
        return movies
