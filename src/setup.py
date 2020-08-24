from distutils.core import setup, Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize
from numpy import get_include   # cimport numpy を使うため

ext = Extension("module.MMath", sources=["module/MMath.py"], include_dirs=['.', get_include()])
setup(name="module.MMath", cmdclass={"build_ext": build_ext}, ext_modules=cythonize([ext]))
