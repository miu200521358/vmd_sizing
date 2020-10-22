# -*- coding: utf-8 -*-
#
import numpy as np
cimport numpy as np

from module.MMath cimport MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa

cdef double calc_catmull_rom_one_point(double x, double v0, double v1, double v2, double v3) except? -1

cpdef np.ndarray calc_value_from_catmullrom(str bone_name, list fnos, list values)

cdef bint fit_bezier_mmd(list bzs)

cdef tuple c_join_value_2_bezier(int fno, str bone_name, list values, double offset, double diff_limit)

cdef tuple convert_catmullrom_2_bezier(np.ndarray xs, np.ndarray ys)

cdef tuple c_evaluate(int x1v, int y1v, int x2v, int y2v, int start, int now, int end)

cdef tuple c_evaluate_by_t(int x1v, int y1v, int x2v, int y2v, int start, int end, double t)

cdef tuple split_bezier(int x1v, int y1v, int x2v, int y2v, int start, int now, int end)

cdef list scale_bezier(MVector2D p1, MVector2D p2, MVector2D p3, MVector2D p4)

cdef MVector2D scale_bezier_point(MVector2D pn, MVector2D p1, MVector2D diff)

cdef MVector2D round_bezier_mmd(MVector2D target)

cdef int round_integer(double t)



