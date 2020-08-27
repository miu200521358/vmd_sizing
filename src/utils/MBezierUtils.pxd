# -*- coding: utf-8 -*-
#
from module.MMath cimport MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
import numpy as np
cimport numpy as np
cimport libc.math as cmath
import bezier
cimport bezier._curve
from utils.MLogger import MLogger # noqa

cdef public int INTERPOLATION_MMD_MAX
cdef public list LINEAR_MMD_INTERPOLATION
cdef public list R_x1_idxs
cdef public list R_y1_idxs
cdef public list R_x2_idxs
cdef public list R_y2_idxs
cdef public list MX_x1_idxs
cdef public list MX_y1_idxs
cdef public list MX_x2_idxs
cdef public list MX_y2_idxs
cdef public list MY_x1_idxs
cdef public list MY_y1_idxs
cdef public list MY_x2_idxs
cdef public list MY_y2_idxs
cdef public list MZ_x1_idxs
cdef public list MZ_y1_idxs
cdef public list MZ_x2_idxs
cdef public list MZ_y2_idxs
cdef public str BZ_TYPE_MX
cdef public str BZ_TYPE_MY
cdef public str BZ_TYPE_MZ
cdef public str BZ_TYPE_R

cdef list calc_value_from_catmullrom(str bone_name, int fnos, list values)

cdef float calc_catmull_rom_one_point(float x, float v0, float v1, float v2, float v3)

cdef fit_bezier_mmd(MVector2D bzs)

cdef tuple c_join_value_2_bezier(int fno, str bone_name, list values, float offset, float diff_limit)

cdef tuple convert_catmullrom_2_bezier(np.ndarray xs, np.ndarray ys)

cdef tuple c_evaluate(int x1v, int y1v, int x2v, int y2v, int start, int now, int end)

cdef tuple c_evaluate_by_t(int x1v, int y1v, int x2v, int y2v, int start, int end, float t)

cdef tuple split_bezier(int x1v, int y1v, int x2v, int y2v, int start, int now, int end)

cdef list scale_bezier(MVector2D p1, MVector2D p2, MVector2D p3, MVector2D p4)

cdef MVector2D scale_bezier_point(MVector2D pn, MVector2D p1, MVector2D diff)

cdef MVector2D round_bezier_mmd(MVector2D target)

cdef int round_integer(float t)



