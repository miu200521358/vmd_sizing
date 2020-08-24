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

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_INT_t v2):
    return v1 + v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_FLOAT_t v2):
    return v1 + v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 - v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_INT_t v2):
    return v1 - v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_FLOAT_t v2):
    return v1 - v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 * v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_INT_t v2):
    return v1 * v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_FLOAT_t v2):
    return v1 * v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 / v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_INT_t v2):
    return v1 / v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_FLOAT_t v2):
    return v1 / v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 // v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_INT_t v2):
    return v1 // v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_FLOAT_t v2):
    return v1 // v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 % v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_INT_t v2):
    return v1 % v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_FLOAT_t v2):
    return v1 % v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] pow_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 ** v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] pow_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_INT_t v2):
    return v1 ** v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] pow_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_FLOAT_t v2):
    return v1 ** v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] lshift_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 << v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] lshift_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_INT_t v2):
    return v1 << v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] lshift_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_FLOAT_t v2):
    return v1 << v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] rshift_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 >> v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] rshift_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_INT_t v2):
    return v1 >> v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] rshift_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_FLOAT_t v2):
    return v1 >> v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] and_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 & v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] and_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_INT_t v2):
    return v1 & v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] and_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_FLOAT_t v2):
    return v1 & v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] dataor_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 ^ v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] dataor_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_INT_t v2):
    return v1 ^ v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] dataor_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_FLOAT_t v2):
    return v1 ^ v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] or_array(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return v1 | v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] or_int(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_INT_t v2):
    return v1 | v2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] or_float(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, DTYPE_FLOAT_t v2):
    return v1 | v2

cpdef DTYPE_FLOAT_t length(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1):
    return <DTYPE_FLOAT_t>np.linalg.norm(v1, ord=2)

cpdef DTYPE_FLOAT_t lengthSquared(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1):
    return <DTYPE_FLOAT_t>np.linalg.norm(v1, ord=2)**2

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] normalized(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1):
    cdef np.ndarray l2 = np.linalg.norm(v1, ord=2, axis=-1, keepdims=True)
    l2[l2 == 0] = 1
    cdef np.ndarray normv = v1 / l2
    return normv

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] cross(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return np.cross(v1, v2)

cpdef DTYPE_FLOAT_t dot(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    return np.dot(v1, v2)

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] inverted(np.ndarray[DTYPE_FLOAT_t, ndim=2] v1):
    return np.linalg.inv(v1)

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] dot2(np.ndarray[DTYPE_FLOAT_t, ndim=2] v1, np.ndarray[DTYPE_FLOAT_t, ndim=2] v2):
    return v1.dot(v2)

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] translate_MMatrix4x4(np.ndarray[DTYPE_FLOAT_t, ndim=2] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    cdef np.ndarray vec_mat = np.tile(v2, (4, 1))
    cdef np.ndarray data_mat = v1[:, :3] * vec_mat
    v1[:, 3] += np.sum(data_mat, axis=1)
    return v1

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] scale_MMatrix4x4(np.ndarray[DTYPE_FLOAT_t, ndim=2] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    cdef np.ndarray vec_mat = np.tile(v2, (4, 1))
    v1[:, :3] *= vec_mat
    return v1

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] eye():
    return np.eye(4)

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] toMatrix4x4_MQuaternion(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1):
    cdef np.ndarray m = np.zeros((4, 4))

    # q(w,x,y,z)から(x,y,z,w)に並べ替え.
    q2 = np.array([v1[1], v1[2], v1[3], v1[0]], dtype=DTYPE_FLOAT)

    m[0, 0] = q2[3] * q2[3] + q2[0] * q2[0] - q2[1] * q2[1] - q2[2] * q2[2]
    m[0, 1] = 2.0 * q2[0] * q2[1] - 2.0 * q2[3] * q2[2]
    m[0, 2] = 2.0 * q2[0] * q2[2] + 2.0 * q2[3] * q2[1]
    m[0, 3] = 0.0

    m[1, 0] = 2.0 * q2[0] * q2[1] + 2.0 * q2[3] * q2[2]
    m[1, 1] = q2[3] * q2[3] - q2[0] * q2[0] + q2[1] * q2[1] - q2[2] * q2[2]
    m[1, 2] = 2.0 * q2[1] * q2[2] - 2.0 * q2[3] * q2[0]
    m[1, 3] = 0.0

    m[2, 0] = 2.0 * q2[0] * q2[2] - 2.0 * q2[3] * q2[1]
    m[2, 1] = 2.0 * q2[1] * q2[2] + 2.0 * q2[3] * q2[0]
    m[2, 2] = q2[3] * q2[3] - q2[0] * q2[0] - q2[1] * q2[1] + q2[2] * q2[2]
    m[2, 3] = 0.0

    m[3, 0] = 0.0
    m[3, 1] = 0.0
    m[3, 2] = 0.0
    m[3, 3] = q2[3] * q2[3] + q2[0] * q2[0] + q2[1] * q2[1] + q2[2] * q2[2]

    m /= m[3, 3]
    m[3, 3] = 1.0

    return m

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] toEulerAngles(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1):
    cdef DTYPE_FLOAT_t xp = v1[1]
    cdef DTYPE_FLOAT_t yp = v1[2]
    cdef DTYPE_FLOAT_t zp = v1[3]
    cdef DTYPE_FLOAT_t wp = v1[0]

    cdef DTYPE_FLOAT_t xx = xp * xp
    cdef DTYPE_FLOAT_t xy = xp * yp
    cdef DTYPE_FLOAT_t xz = xp * zp
    cdef DTYPE_FLOAT_t xw = xp * wp
    cdef DTYPE_FLOAT_t yy = yp * yp
    cdef DTYPE_FLOAT_t yz = yp * zp
    cdef DTYPE_FLOAT_t yw = yp * wp
    cdef DTYPE_FLOAT_t zz = zp * zp
    cdef DTYPE_FLOAT_t zw = zp * wp
    cdef DTYPE_FLOAT_t lengthSquared = xx + yy + zz + wp * wp

    if not np.isclose([lengthSquared - 1.0], [0.0]) and np.isclose([lengthSquared], [0.0]):
        xx /= lengthSquared
        xy /= lengthSquared  # same as (xp / length) * (yp / length)
        xz /= lengthSquared
        xw /= lengthSquared
        yy /= lengthSquared
        yz /= lengthSquared
        yw /= lengthSquared
        zz /= lengthSquared
        zw /= lengthSquared

    cdef DTYPE_FLOAT_t pitch = math.asin(max(-1, min(1, -2.0 * (yz - xw))))
    cdef DTYPE_FLOAT_t yaw = 0.0
    cdef DTYPE_FLOAT_t roll = 0.0
    
    if pitch < (math.pi / 2):
        if pitch > -(math.pi / 2):
            yaw = math.atan2(2.0 * (xz + yw), 1.0 - 2.0 * (xx + yy))
            roll = math.atan2(2.0 * (xy + zw), 1.0 - 2.0 * (xx + zz))
        else:
            # not a unique solution
            roll = 0.0
            yaw = -math.atan2(-2.0 * (xy - zw), 1.0 - 2.0 * (yy + zz))
    else:
        # not a unique solution
        roll = 0.0
        yaw = math.atan2(-2.0 * (xy - zw), 1.0 - 2.0 * (yy + zz))

    v = np.array([math.degrees(pitch), math.degrees(yaw), math.degrees(roll)], dtype=DTYPE_FLOAT)
    
    return v

cpdef DTYPE_FLOAT_t toDegree(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1):
    return math.degrees(2 * math.acos(min(1, max(-1, v1[0]))))

cpdef DTYPE_FLOAT_t calcTheata_MQuaternion(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    cdef DTYPE_FLOAT_t dot = dotProduct_MQuaternion(v1, v2)
    cdef DTYPE_FLOAT_t theta = math.acos(min(1, max(-1, dot)))
    cdef DTYPE_FLOAT_t sinOfAngle = math.sin(theta)
    return sinOfAngle

cpdef DTYPE_FLOAT_t dotProduct_MQuaternion(np.ndarray[DTYPE_FLOAT_t, ndim=1] v1, np.ndarray[DTYPE_FLOAT_t, ndim=1] v2):
    cdef DTYPE_FLOAT_t dotv = np.sum(v1 * v2)
    return dotv

cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] fromAxisAndAngle(np.ndarray[DTYPE_FLOAT_t, ndim=1] vec3, DTYPE_FLOAT_t angle):
    cdef DTYPE_FLOAT_t x = vec3[0]
    cdef DTYPE_FLOAT_t y = vec3[1]
    cdef DTYPE_FLOAT_t z = vec3[2]
    cdef DTYPE_FLOAT_t length = math.sqrt(x * x + y * y + z * z)

    if not np.isclose([length - 1.0], [0.0]) and np.isclose([length], [0.0]):
        x /= length
        y /= length
        z /= length

    cdef DTYPE_FLOAT_t a = math.radians(angle / 2.0)
    cdef DTYPE_FLOAT_t s = math.sin(a)
    cdef DTYPE_FLOAT_t c = math.cos(a)
    return np.array([c, x * s, y * s, z * s], dtype=DTYPE_FLOAT)


