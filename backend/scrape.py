from bs4 import BeautifulSoup
import requests
from typing import List, Union
from movie import Movie
from random import choice
from collections import deque

class LetterboxdScraper:
    def __init__(self, seed:Union[int, None] = None):
        self.seed = seed
        self.url = "https://letterboxd.com/"
    
    def combine_dictionaries(self, all_movie_lists: List[dict[str: Movie]]) -> dict[str: Movie]:
        combined_list = all_movie_lists[0]
        for movie_list_ind in range(1,len(all_movie_lists)):
            for movie_id, movie in all_movie_lists[movie_list_ind].items():
                if movie_id not in combined_list:
                    combined_list[movie_id] = movie
        return combined_list
    
    def remove_used_movies(self, movies: dict[str: Movie], exclude_ids: List[str]) -> dict[str: Movie]:
        return {key: val for key, val in movies.items() if key not in exclude_ids}

    def pick_movie(self, movies: dict[str: Movie], exclude_ids: List[str]) -> Union[Movie, None]:
        if len(movies) > len(exclude_ids):
            while True:
                pick = choice(movies.keys())
                if pick not in exclude_ids:
                    return movies[pick]
        else:
            movies = self.remove_used_movies(movies, exclude_ids)
            return movies[choice(movies.keys())] if movies else None
    
    def get_url_from_usernames(self, usernames: List[str]) -> List[str]:
        return [f"{self.url}{username}/watchlist/" for username in usernames]

    def scrape(self, usernames: List[str]) -> List[dict[str: Movie]]:
        queue = deque(self.get_url_from_usernames(usernames))
        movie_lists = []
        while queue:
            response = requests.get(queue.popleft())
            movie_lists.append(self.parse(response.content, queue))
    
    def parse(self, response_data: bytes, queue: deque[str]) -> dict[str: Movie]:
        soup = BeautifulSoup(response_data, "html.parser")
        next_button = soup.find("a", class_="next")
        if next_button:
            queue.append(f"{self.url}{next_button['href']}")
        movie_elements = soup.find("ul", class_="poster-list")
        movie_elem_list = movie_elements.find_all("li")
        # TODO: implement the rest
