from cpython.ref cimport PyObject

cdef extern from "Python.h":
    PyObject* PyUnicode_FromString(const char* u) nogil

cdef class Movie:
    cdef public str movie_id
    cdef public str letterboxd_path
    cdef public str title 