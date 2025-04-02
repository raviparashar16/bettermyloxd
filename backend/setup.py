from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize(["movie_cy.pyx", "cython_utils.pyx"])
) 