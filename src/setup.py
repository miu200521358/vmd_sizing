from setuptools import setup
from Cython.Distutils import build_ext
from Cython.Build import cythonize
import setup_ext

from Cython.Compiler.Options import get_directive_defaults
directive_defaults = get_directive_defaults()
directive_defaults['linetrace'] = True
directive_defaults['binding'] = True

setup(name="*", cmdclass={"build_ext": build_ext}, ext_modules=cythonize(setup_ext.get_ext(), annotate=True, \
      compiler_directives={'language_level': "3", 'profile': True, 'linetrace': True, 'binding': True}, **setup_ext.kwargs))


