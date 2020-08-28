from setuptools import Extension
from numpy import get_include   # cimport numpy を使うため

ext = [Extension("module.MMath", sources=["module/MMath.pyx"], include_dirs=['.', get_include()]), \
       Extension("module.MParams", sources=["module/MParams.pyx"], include_dirs=['.', get_include()]), \
       Extension("module.MOptions", sources=["module/MOptions.pyx"], include_dirs=['.', get_include()]), \
       Extension("mmd.PmxData", sources=["mmd/PmxData.pyx"], include_dirs=['.', get_include()]), \
       Extension("mmd.VmdData", sources=["mmd/VmdData.pyx"], include_dirs=['.', get_include()], define_macros=[("CYTHON_TRACE", "1")]), \
       Extension("utils.MBezierUtils", sources=["utils/MBezierUtils.pyx"], \
                 include_dirs=['.', 'C:/Development/Anaconda3/envs/vmdsizing_cython_exe1/Lib/site-packages/bezier/include', get_include()]), \
       Extension("utils.MLogger", sources=["utils/MLogger.py"], include_dirs=['.', get_include()]), \
       Extension("utils.MServiceUtils", sources=["utils/MServiceUtils.pyx"], include_dirs=['.', get_include()]), \
       Extension("service.parts.StanceService", sources=["service/parts/StanceService.pyx"], include_dirs=['.', get_include()], define_macros=[("CYTHON_TRACE", "1")]), \
       ]


