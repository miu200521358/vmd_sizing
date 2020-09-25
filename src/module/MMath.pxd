# -*- coding: utf-8 -*-
#
import math
import numpy as np
cimport numpy as np
cimport libc.math as cmath
import quaternion # noqa

from utils.MLogger import MLogger # noqa

DTYPE_INT = np.int
ctypedef np.int_t DTYPE_INT_t

DTYPE_INT8 = np.int8
ctypedef np.int8_t DTYPE_INT8_t

DTYPE_FLOAT = np.float64
ctypedef np.float64_t DTYPE_FLOAT_t

cdef class MRect:
    cdef DTYPE_FLOAT_t __x
    cdef DTYPE_FLOAT_t __y
    cdef DTYPE_FLOAT_t __width
    cdef DTYPE_FLOAT_t __height

cdef class MVector2D:
    cdef np.ndarray __data

    cpdef data(self)

    cpdef setX(self, x)

    cpdef setY(self, y)

    cpdef effective(self)

cdef class MVector3D:
    cdef np.ndarray __data

    cpdef data(self)

    cpdef setX(self, x)

    cpdef setY(self, y)

    cpdef setZ(self, z)

    cpdef effective(self)

cdef class MVector4D:
    cdef np.ndarray __data

    cpdef data(self)

    cpdef setX(self, x)

    cpdef setY(self, y)

    cpdef setZ(self, z)

    cpdef setW(self, w)

    cpdef effective(self)

cdef class MQuaternion:
    cdef np.ndarray __data

    cpdef data(self)

    cpdef setX(self, x)

    cpdef setY(self, y)
    
    cpdef setZ(self, z)

    cpdef setScalar(self, w)

cdef class MMatrix4x4:
    cdef np.ndarray __data

    cpdef data(self)

    cpdef rotate(self, qq)

    cpdef translate(self, vec3)

    cpdef scale(self, vec3)

    cpdef lookAt(self, eye, center, up)
    