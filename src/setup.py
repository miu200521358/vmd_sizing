from setuptools import Extension, setup
from Cython.Distutils import build_ext
from Cython.Build import cythonize
from numpy import get_include   # cimport numpy を使うため

ext = [Extension("module.MMath", sources=["module/MMath.pyx"], include_dirs=['.', get_include()]), \
       Extension("utils.MBezierUtils", sources=["utils/MBezierUtils.py"], \
                 include_dirs=['.', 'C:/Development/Anaconda3/envs/vmdsizing_cython_exe1/Lib/site-packages/bezier/include', get_include()])]

setup(name="*", cmdclass={"build_ext": build_ext}, ext_modules=cythonize(ext, annotate=True, compiler_directives={'language_level': "3"}))



