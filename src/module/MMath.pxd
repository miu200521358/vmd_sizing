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

    cpdef MVector2D copy(self)

    cpdef DTYPE_FLOAT_t x(self)

    cpdef DTYPE_FLOAT_t y(self)

    cpdef setX(self, x)

    cpdef setY(self, y)

    cpdef double length(self)

    cpdef double lengthSquared(self)

    cpdef MVector2D normalized(self)

    cpdef normalize(self)

    cpdef effective(self)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_MVector2D(self, MVector2D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_int(self, DTYPE_INT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_MVector2D(self, MVector2D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_int(self, DTYPE_INT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_MVector2D(self, MVector2D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_int(self, DTYPE_INT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_MVector2D(self, MVector2D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_int(self, DTYPE_INT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_MVector2D(self, MVector2D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_int(self, DTYPE_INT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_MVector2D(self, MVector2D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_int(self, DTYPE_INT_t other)


cdef class MVector3D:
    cdef np.ndarray __data

    cpdef MVector3D copy(self)

    cpdef double length(self)

    cpdef double lengthSquared(self)

    cpdef MVector3D round(self, decimals)

    cpdef MVector3D normalized(self)

    cpdef normalize(self)

    cpdef double distanceToPoint(self, MVector3D v)

    cpdef MVector3D project(self, MMatrix4x4 modelView, MMatrix4x4 projection, MRect viewport)

    cpdef MVector3D unproject(self, MMatrix4x4 modelView, MMatrix4x4 projection, MRect viewport)

    cpdef MVector4D toVector4D(self)

    cpdef bint is_almost_null(self)

    cpdef MVector3D effective(self)
                
    cpdef MVector3D abs(self)
                
    cpdef MVector3D one(self)

    cpdef MVector3D non_zero(self)

    cpdef bint isnan(self)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] data(self)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_MVector3D(self, MVector3D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_int(self, DTYPE_INT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_MVector3D(self, MVector3D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_int(self, DTYPE_INT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_MVector3D(self, MVector3D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_int(self, DTYPE_INT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_MVector3D(self, MVector3D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_int(self, DTYPE_INT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_MVector3D(self, MVector3D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_int(self, DTYPE_INT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_MVector3D(self, MVector3D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_int(self, DTYPE_INT_t other)

    cpdef DTYPE_FLOAT_t x(self)

    cpdef DTYPE_FLOAT_t y(self)

    cpdef DTYPE_FLOAT_t z(self)
    
    cpdef setX(self, x)

    cpdef setY(self, y)

    cpdef setZ(self, z)

cdef MVector3D crossProduct_MVector3D(MVector3D v1, MVector3D v2)

cdef double dotProduct_MVector3D(MVector3D v1, MVector3D v2)


cdef class MVector4D:
    cdef np.ndarray __data

    cpdef MVector4D copy(self)

    cpdef double length(self)

    cpdef double lengthSquared(self)

    cpdef MVector4D normalized(self)

    cpdef normalize(self)

    cpdef MVector3D toVector3D(self)

    cpdef bint is_almost_null(self)

    cpdef effective(self)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] data(self)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_MVector4D(self, MVector4D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_int(self, DTYPE_INT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_MVector4D(self, MVector4D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_int(self, DTYPE_INT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_MVector4D(self, MVector4D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_int(self, DTYPE_INT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_MVector4D(self, MVector4D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_int(self, DTYPE_INT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_MVector4D(self, MVector4D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_int(self, DTYPE_INT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_MVector4D(self, MVector4D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_int(self, DTYPE_INT_t other)

    cpdef DTYPE_FLOAT_t x(self)

    cpdef DTYPE_FLOAT_t y(self)

    cpdef DTYPE_FLOAT_t z(self)
    
    cpdef DTYPE_FLOAT_t w(self)
    
    cpdef setX(self, x)

    cpdef setY(self, y)

    cpdef setZ(self, z)

    cpdef setW(self, w)

cdef double dotProduct_MVector4D(MVector4D v1, MVector4D v2)

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

    cpdef MVector3D separateEulerAngles(self)

    cpdef double toDegree(self)

    cpdef double toDegreeSign(self, MVector3D local_axis)
    
    cpdef double calcTheata(self, MQuaternion v)

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

cdef double dotProduct_MQuaternion(MQuaternion v1, MQuaternion v2)

cdef MQuaternion fromAxisAndAngle(MVector3D vec3, double angle)

cdef MQuaternion fromAxisAndQuaternion(MVector3D vec3, MQuaternion qq)

cdef MQuaternion fromDirection(MVector3D direction, MVector3D up)

cdef MQuaternion fromAxes(MVector3D xAxis, MVector3D yAxis, MVector3D zAxis)

cdef MQuaternion fromRotationMatrix(np.ndarray[DTYPE_FLOAT_t, ndim=2] rot3x3)

cdef MQuaternion rotationTo(MVector3D fromv, MVector3D tov)

cdef MQuaternion fromEulerAngles(double pitch, double yaw, double roll)

cdef MQuaternion nlerp(MQuaternion q1, MQuaternion q2, double t)

cdef MQuaternion slerp(MQuaternion q1, MQuaternion q2, double t)


cdef class MMatrix4x4:
    cdef np.ndarray __data

    cpdef MMatrix4x4 copy(self)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] data(self)

    cpdef MMatrix4x4 inverted(self)

    cpdef rotate(self, qq)

    cpdef translate(self, MVector3D vec3)

    cpdef scale(self, MVector3D vec3)

    cpdef setToIdentity(self)

    cpdef lookAt(self, MVector3D eye, MVector3D center, MVector3D up)

    cpdef perspective(self, double verticalAngle, double aspectRatio, double nearPlane, double farPlane)
    
    cpdef MVector3D mapVector(self, MVector3D vector)

    cpdef MQuaternion toQuaternion(self)
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] add_MMatrix4x4(self, MMatrix4x4 other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] add_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] add_int(self, DTYPE_INT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] sub_MMatrix4x4(self, MMatrix4x4 other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] sub_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] sub_int(self, DTYPE_INT_t other)

    cpdef MVector3D mul_MVector3D(self, MVector3D other)

    cpdef MVector4D mul_MVector4D(self, MVector4D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] mul_MMatrix4x4(self, MMatrix4x4 other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] mul_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] mul_int(self, DTYPE_INT_t other)



cpdef bint is_almost_null(v)    

cpdef double get_effective_value(v)

cpdef double get_almost_zero_value(v)

