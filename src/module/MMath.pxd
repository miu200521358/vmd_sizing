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

    cpdef DTYPE_FLOAT_t x(self)

    cpdef DTYPE_FLOAT_t y(self)

    cpdef DTYPE_FLOAT_t width(self)

    cpdef DTYPE_FLOAT_t height(self)

cdef class MVector2D:
    cdef np.ndarray __data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] data(self)

    cpdef DTYPE_FLOAT_t x(self)

    cpdef DTYPE_FLOAT_t y(self)

    cpdef setX(self, x)

    cpdef setY(self, y)

    cpdef double length(self)

    cpdef double lengthSquared(self)

    cpdef MVector2D normalized(self)

    cpdef normalize(self)

    cpdef effective(self)


cdef class MVector3D:
    cdef np.ndarray __data

    cpdef MVector3D copy(self)

    cpdef double length(self)

    cpdef double lengthSquared(self)

    cpdef MVector3D normalized(self)

    cpdef normalize(self)

    cpdef double distanceToPoint(self, v)

    cpdef MVector3D project(self, modelView, projection, viewport)

    cpdef MVector3D unproject(self, modelView, projection, viewport)

    cpdef MVector4D toVector4D(self)

    cpdef bint is_almost_null(self)

    cpdef MVector3D effective(self)
                
    cpdef MVector3D abs(self)
                
    cpdef MVector3D one(self)

    cpdef MVector3D non_zero(self)

    cpdef bint isnan(self)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] data(self)

    cpdef DTYPE_FLOAT_t x(self)

    cpdef DTYPE_FLOAT_t y(self)

    cpdef DTYPE_FLOAT_t z(self)
    
    cpdef setX(self, x)

    cpdef setY(self, y)

    cpdef setZ(self, z)

cdef MVector3D crossProduct_MVector3D(v1, v2)

cdef double dotProduct_MVector3D(v1, v2)


cdef class MVector4D:
    cdef np.ndarray __data

    cpdef double length(self)

    cpdef double lengthSquared(self)

    cpdef MVector4D normalized(self)

    cpdef normalize(self)

    cpdef MVector3D toVector3D(self)

    cpdef bint is_almost_null(self)

    cpdef effective(self)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] data(self)

    cpdef DTYPE_FLOAT_t x(self)

    cpdef DTYPE_FLOAT_t y(self)

    cpdef DTYPE_FLOAT_t z(self)
    
    cpdef DTYPE_FLOAT_t w(self)
    
    cpdef setX(self, x)

    cpdef setY(self, y)

    cpdef setZ(self, z)

    cpdef setW(self, w)

cdef double dotProduct_MVector4D(v1, v2)

cdef class MQuaternion:
    cdef np.ndarray __data

    cpdef MQuaternion copy(self)

    cpdef MQuaternion inverted(self)

    cpdef double length(self)

    cpdef double lengthSquared(self)

    cpdef MQuaternion normalized(self)

    cpdef normalize(self)

    cpdef effective(self)

    cpdef MMatrix4x4 toMatrix4x4(self)

    cpdef MVector4D toVector4D(self)

    cpdef MVector3D toEulerAngles4MMD(self)

    cpdef MVector3D toEulerAngles(self)

    cpdef double toDegree(self)

    cpdef double calcTheata(self, v)

    cpdef data(self)

    cpdef double x(self)

    cpdef double y(self)

    cpdef double z(self)
    
    cpdef double scalar(self)

    cpdef MVector3D vector(self)

    cpdef setX(self, x)

    cpdef setY(self, y)
    
    cpdef setZ(self, z)

    cpdef setScalar(self, w)

cdef dotProduct_MQuaternion(v1, v2)

cdef MQuaternion fromAxisAndAngle(vec3, angle)

cdef MQuaternion fromAxisAndQuaternion(vec3, qq)

cdef MQuaternion fromDirection(direction, up)

cdef MQuaternion fromAxes(xAxis, yAxis, zAxis)

cdef MQuaternion fromRotationMatrix(rot3x3)

cdef MQuaternion rotationTo(fromv, tov)

cdef MQuaternion fromEulerAngles(pitch, yaw, roll)

cdef MQuaternion nlerp(q1, q2, t)

cdef MQuaternion slerp(q1, q2, t)


cdef class MMatrix4x4:
    cdef np.ndarray __data

    cpdef MMatrix4x4 copy(self)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] data(self)

    cpdef MMatrix4x4 inverted(self)

    cpdef rotate(self, qq)

    cpdef translate(self, vec3)

    cpdef scale(self, vec3)

    cpdef setToIdentity(self)

    cpdef lookAt(self, eye, center, up)

    cpdef perspective(self, verticalAngle, aspectRatio, nearPlane, farPlane)
    
    cpdef MVector3D mapVector(self, vector)

    cpdef MQuaternion toQuaternion(self)


cpdef bint is_almost_null(v)    

cpdef double get_effective_value(v)

cpdef double get_almost_zero_value(v)

