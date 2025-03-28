from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize(["backend/movie_cy.pyx", "backend/cython_utils.pyx"])
) 