from setuptools import Extension
from numpy import get_include   # cimport numpy を使うため

bezier_path = 'C:/Development/Anaconda3/envs/vmdsizing_cython_exe1/Lib/site-packages/bezier/include'

ext = [Extension("module.MMath", sources=["module/MMath.pyx"], include_dirs=['.', bezier_path, get_include()]), \
       Extension("module.MParams", sources=["module/MParams.pyx"], include_dirs=['.', bezier_path, get_include()]), \
       Extension("module.MOptions", sources=["module/MOptions.pyx"], include_dirs=['.', bezier_path, get_include()]), \
       Extension("utils.MBezierUtils", sources=["utils/MBezierUtils.pyx"], include_dirs=['.', bezier_path, get_include()]), \
       Extension("utils.MLogger", sources=["utils/MLogger.py"], include_dirs=['.', bezier_path, get_include()]), \
       Extension("utils.MServiceUtils", sources=["utils/MServiceUtils.pyx"], include_dirs=['.', bezier_path, get_include()]), \
       Extension("mmd.PmxData", sources=["mmd/PmxData.pyx"], include_dirs=['.', bezier_path, get_include()]), \
       Extension("mmd.PmxReader", sources=["mmd/PmxReader.py"], include_dirs=['.', bezier_path, get_include()]), \
       Extension("mmd.VmdData", sources=["mmd/VmdData.pyx"], include_dirs=['.', bezier_path, get_include()]), \
       Extension("mmd.VmdReader", sources=["mmd/VmdReader.py"], include_dirs=['.', bezier_path, get_include()]), \
       Extension("service.parts.StanceService", sources=["service/parts/StanceService.pyx"], include_dirs=['.', bezier_path, get_include()]), \
       Extension("service.parts.ArmAvoidanceService", sources=["service/parts/ArmAvoidanceService.pyx"], include_dirs=['.', bezier_path, get_include()]), \
       ]


