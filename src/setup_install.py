from setuptools import setup
from Cython.Distutils import build_ext
from Cython.Build import cythonize
import setup_ext

setup(name="*", cmdclass={"build_ext": build_ext}, ext_modules=cythonize(setup_ext.get_ext(), \
      compiler_directives={'language_level': "3"}, **setup_ext.kwargs))


