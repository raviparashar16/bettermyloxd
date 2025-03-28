from typing import Dict, List
from movie_cy cimport Movie

def combine_dictionaries(all_movie_lists: List[Dict[str, Movie]]) -> Dict[str, Movie]:
    cdef Dict[str, Movie] combined_list = all_movie_lists[0]
    cdef Dict[str, Movie] current_list
    cdef str movie_id
    cdef Movie movie
    
    for current_list in all_movie_lists[1:]:
        for movie_id, movie in current_list.items():
            if movie_id not in combined_list:
                combined_list[movie_id] = movie
    return combined_list 