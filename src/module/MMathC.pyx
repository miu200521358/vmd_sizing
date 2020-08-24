# -*- coding: utf-8 -*-
#
import math
import numpy as np
from numpy.core.fromnumeric import ndim
cimport numpy as np
cimport cython

DTYPE_INT = np.int
ctypedef np.int_t DTYPE_INT_t

DTYPE_FLOAT = np.float
ctypedef np.float64_t DTYPE_FLOAT_t

from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 + v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, int v2):
    return v1 + v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, float v2):
    return v1 + v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 - v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, int v2):
    return v1 - v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, float v2):
    return v1 - v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 * v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, int v2):
    return v1 * v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, float v2):
    return v1 * v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 / v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, int v2):
    return v1 / v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, float v2):
    return v1 / v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 // v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, int v2):
    return v1 // v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, float v2):
    return v1 // v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 % v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, int v2):
    return v1 % v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, float v2):
    return v1 % v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] pow_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 ** v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] pow_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, int v2):
    return v1 ** v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] pow_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, float v2):
    return v1 ** v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] lshift_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 << v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] lshift_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, int v2):
    return v1 << v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] lshift_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, float v2):
    return v1 << v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] rshift_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 >> v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] rshift_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, int v2):
    return v1 >> v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] rshift_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, float v2):
    return v1 >> v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] and_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 & v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] and_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, int v2):
    return v1 & v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] and_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, float v2):
    return v1 & v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] dataor_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 ^ v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] dataor_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, int v2):
    return v1 ^ v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] dataor_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, float v2):
    return v1 ^ v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] or_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 | v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] or_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, int v2):
    return v1 | v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] or_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, float v2):
    return v1 | v2

cpdef float length(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1):
    return <float>np.linalg.norm(v1, ord=2)

cpdef float lengthSquared(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1):
    return <float>np.linalg.norm(v1, ord=2)**2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] normalized(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1):
    l2 = np.linalg.norm(v1, ord=2, axis=-1, keepdims=True)
    l2[l2 == 0] = 1
    normv = v1 / l2
    return normv

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] cross(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return np.cross(v1, v2)

cpdef float dot(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return np.dot(v1, v2)

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] inverted(np.ndarray[DTYPE_FLOAT_t, ndim=2] v1):
    return np.linalg.inv(v1)

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] dot2(np.ndarray[DTYPE_FLOAT_t, ndim=2] v1, np.ndarray[DTYPE_FLOAT_t, ndim=2] v2):
    return v1.dot(v2)

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] translate_MMatrix4x4(np.ndarray[DTYPE_FLOAT_t, ndim=2] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    vec_mat = np.tile(np.array([v2[0], v2[1], v2[2]]), (4, 1))
    data_mat = v1[:, :3] * vec_mat
    v1[:, 3] += np.sum(data_mat, axis=1)
    return v1

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] scale_MMatrix4x4(np.ndarray[DTYPE_FLOAT_t, ndim=2] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    vec_mat = np.tile(np.array([v2[0], v2[1], v2[2]]), (4, 1))
    v1[:, :3] *= vec_mat
    return v1

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] eye():
    return np.eye(4)




