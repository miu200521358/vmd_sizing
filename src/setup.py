from distutils.core import setup, Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize
from numpy import get_include   # cimport numpy を使うため

ext = Extension("module.MMathC", sources=["module/MMathC.pyx"], include_dirs=['.', get_include()])
setup(name="module.MMathC", ext_modules=cythonize([ext]))

ext = Extension("utils.MBezierUtils", sources=["utils/MBezierUtils.pyx"], \
                include_dirs=['.', 'C:/Development/Anaconda3/envs/vmdsizing_cython_exe1/Lib/site-packages/bezier/include', get_include()])
setup(name="utils.MBezierUtils", cmdclass={"build_ext": build_ext}, ext_modules=cythonize([ext]))

ext = Extension("mmd.VmdData", sources=["mmd/VmdData.py"], include_dirs=['.', get_include()])
setup(name="mmd.VmdData", ext_modules=cythonize([ext]))

ext = Extension("mmd.VmdReader", sources=["mmd/VmdReader.py"], include_dirs=['.', get_include()])
setup(name="mmd.VmdReader", ext_modules=cythonize([ext]))

ext = Extension("module.OneEuroFilter", sources=["module/OneEuroFilter.py"], include_dirs=['.', get_include()])
setup(name="module.OneEuroFilter", cmdclass={"build_ext": build_ext}, ext_modules=cythonize([ext]))
