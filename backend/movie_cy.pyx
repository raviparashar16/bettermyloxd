from cpython.ref cimport PyObject
from movie_cy cimport Movie

cdef extern from "Python.h":
    PyObject* PyUnicode_FromString(const char* u) nogil

cdef class Movie:
    __slots__ = ['movie_id', 'letterboxd_path', 'title']

    def __init__(self, str movie_id, str letterboxd_path, str title):
        self.movie_id = movie_id
        self.letterboxd_path = letterboxd_path
        self.title = title

    def __str__(self):
        return f"Movie(movie_id='{self.movie_id}', letterboxd_path='{self.letterboxd_path}', title='{self.title}')" 