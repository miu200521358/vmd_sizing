from setuptools import Extension
from numpy import get_include   # cimport numpy を使うため

bezier_path = 'C:/Development/Anaconda3/envs/vmdsizing_cython_exe1/Lib/site-packages/bezier/include'

kwargs = {"output_dir": "./build/output", "build_dir": "./build/"}

sources = ["module/MMath.py", "module/MParams.py"]


def get_ext():
    ext = []
    for source in sources:
        path = source.replace("/", ".").replace(".py", "")
        ext.append(Extension(path, sources=[source], include_dirs=['.', bezier_path, get_include()], define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")]))
    
    return ext

# ext = [Extension("module.MMath", sources=["module/MMath.py"], include_dirs=['.', bezier_path, get_include()]), \
#        # Extension("module.MMath", sources=["module/MMath.py"], include_dirs=['.', bezier_path, get_include()], define_macros=[('CYTHON_TRACE', '1')]), \
#        Extension("module.MParams", sources=["module/MParams.py"], include_dirs=['.', bezier_path, get_include()]), \
#        Extension("module.MOptions", sources=["module/MOptions.py"], include_dirs=['.', bezier_path, get_include()]), \
#        Extension("utils.MBezierUtils", sources=["utils/MBezierUtils.py"], include_dirs=['.', bezier_path, get_include()]), \
#        Extension("utils.MLogger", sources=["utils/MLogger.py"], include_dirs=['.', bezier_path, get_include()]), \
#        # Extension("utils.MServiceUtils", sources=["utils/MServiceUtils.py"], include_dirs=['.', bezier_path, get_include()], define_macros=[('CYTHON_TRACE', '1')]), \
#        Extension("utils.MServiceUtils", sources=["utils/MServiceUtils.py"], include_dirs=['.', bezier_path, get_include()]), \
#        Extension("mmd.PmxData", sources=["mmd/PmxData.py"], include_dirs=['.', bezier_path, get_include()]), \
#        Extension("mmd.PmxReader", sources=["mmd/PmxReader.py"], include_dirs=['.', bezier_path, get_include()]), \
#        # Extension("mmd.VmdData", sources=["mmd/VmdData.py"], include_dirs=['.', bezier_path, get_include()], define_macros=[('CYTHON_TRACE', '1')]), \
#        Extension("mmd.VmdData", sources=["mmd/VmdData.py"], include_dirs=['.', bezier_path, get_include()]), \
#        Extension("mmd.VmdReader", sources=["mmd/VmdReader.py"], include_dirs=['.', bezier_path, get_include()]), \
#        # Extension("mmd.VpdReader", sources=["mmd/VpdReader.py"], include_dirs=['.', bezier_path, get_include()]), \
#        # Extension("mmd.VmdWriter", sources=["mmd/VmdWriter.py"], include_dirs=['.', bezier_path, get_include()]), \
#        # Extension("service.parts.MoveService", sources=["service/parts/MoveService.py"], include_dirs=['.', bezier_path, get_include()]), \
#        # Extension("service.parts.CameraService", sources=["service/parts/CameraService.py"], include_dirs=['.', bezier_path, get_include()]), \
#        # Extension("service.parts.MorphService", sources=["service/parts/MorphService.py"], include_dirs=['.', bezier_path, get_include()]), \
#        Extension("service.parts.StanceService", sources=["service/parts/StanceService.py"], include_dirs=['.', bezier_path, get_include()]), \
#        # Extension("service.parts.ArmAvoidanceService", sources=["service/parts/ArmAvoidanceService.py"], include_dirs=['.', bezier_path, get_include()], define_macros=[('CYTHON_TRACE', '1')]), \
#        Extension("service.parts.ArmAvoidanceService", sources=["service/parts/ArmAvoidanceService.py"], include_dirs=['.', bezier_path, get_include()]), \
#        Extension("service.parts.ArmAlignmentService", sources=["service/parts/ArmAlignmentService.py"], include_dirs=['.', bezier_path, get_include()]), \
#        Extension("service.SizingService", sources=["service/SizingService.py"], include_dirs=['.', bezier_path, get_include()]), \
#        # Extension("service.ConvertSmoothService", sources=["service/ConvertSmoothService.py"], include_dirs=['.', bezier_path, get_include()]), \
#        ]


