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

    cpdef x(self)

    cpdef y(self)

    cpdef width(self)

    cpdef height(self)


cdef class MVector2D:

    cdef np.ndarray __data

    cpdef DTYPE_FLOAT_t length(self)

    cpdef DTYPE_FLOAT_t lengthSquared(self)

    cpdef MVector2D normalized(self)

    cpdef MVector2D normalize(self)
    
    cpdef MVector2D effective(self)
            
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] data(self)

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

    cpdef DTYPE_FLOAT_t x(self)

    cpdef DTYPE_FLOAT_t y(self)

    cpdef setX(self, DTYPE_FLOAT_t x)

    cpdef setY(self, DTYPE_FLOAT_t y)


cdef class MVector3D:

    cdef np.ndarray __data

    cpdef MVector3D copy(self)

    cpdef DTYPE_FLOAT_t length(self)

    cpdef DTYPE_FLOAT_t lengthSquared(self)

    cpdef MVector3D normalized(self)

    cpdef normalize(self)
    
    cpdef DTYPE_FLOAT_t distanceToPoint(self, MVector3D v)
    
    cpdef MVector3D project(self, MMatrix4x4 modelView, MMatrix4x4 projection, MRect viewport)

    cpdef MVector3D unproject(self, MMatrix4x4 modelView, MMatrix4x4 projection, MRect viewport)
        
    cpdef MVector4D toVector4D(self)

    cpdef MVector3D effective(self)

    cdef MVector3D c_crossProduct(self, MVector3D v1, MVector3D v2)

    cdef DTYPE_FLOAT_t c_dotProduct(self, MVector3D v1, MVector3D v2)
    
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
    
    cpdef setX(self, DTYPE_FLOAT_t x)

    cpdef setY(self, DTYPE_FLOAT_t y)

    cpdef setZ(self, DTYPE_FLOAT_t z)


cdef class MVector4D:

    cdef np.ndarray __data

    cpdef MVector4D copy(self)

    cpdef DTYPE_FLOAT_t length(self)

    cpdef DTYPE_FLOAT_t lengthSquared(self)

    cpdef MVector4D normalized(self)

    cpdef normalize(self)

    cpdef MVector3D toVector3D(self)
                   
    cpdef MVector4D effective(self)

    cdef DTYPE_FLOAT_t c_dotProduct(self, MVector4D v1, MVector4D v2)
    
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
    
    cpdef setX(self, DTYPE_FLOAT_t x)

    cpdef setY(self, DTYPE_FLOAT_t y)

    cpdef setZ(self, DTYPE_FLOAT_t z)

    cpdef setW(self, DTYPE_FLOAT_t w)


cdef class MQuaternion:

    cdef np.ndarray __data

    cpdef effective(self)

    cpdef MMatrix4x4 toMatrix4x4(self)
    
    cpdef MVector4D toVector4D(self)

    cpdef MVector3D toEulerAngles4MMD(self)

    cpdef MVector3D toEulerAngles(self)
    
    cpdef DTYPE_FLOAT_t toDegree(self)

    cpdef DTYPE_FLOAT_t calcTheata(self, MQuaternion v)

    cdef DTYPE_FLOAT_t c_dotProduct(self, MQuaternion v1, MQuaternion v2)

    cdef MQuaternion c_fromAxisAndAngle(self, MVector3D vec3, DTYPE_FLOAT_t angle)

    cdef MQuaternion c_fromAxisAndQuaternion(self, MVector3D vec3, MQuaternion qq)

    cdef MQuaternion c_fromDirection(self, MVector3D direction, MVector3D up)

    cdef MQuaternion c_fromAxes(self, MVector3D xAxis, MVector3D yAxis, MVector3D zAxis)
    
    cdef MQuaternion c_fromRotationMatrix(self, np.ndarray[DTYPE_FLOAT_t, ndim=2] rot3x3)

    cdef MQuaternion c_rotationTo(self, MVector3D fromv, MVector3D tov)
        
    cdef MQuaternion c_fromEulerAngles(self, DTYPE_FLOAT_t pitch, DTYPE_FLOAT_t yaw, DTYPE_FLOAT_t roll)
    
    cdef MQuaternion c_nlerp(self, MQuaternion q1, MQuaternion q2, DTYPE_FLOAT_t t)
    
    cdef MQuaternion c_slerp(self, MQuaternion q1, MQuaternion q2, DTYPE_FLOAT_t t)

    cpdef DTYPE_FLOAT_t x(self)

    cpdef DTYPE_FLOAT_t y(self)

    cpdef DTYPE_FLOAT_t z(self)
    
    cpdef DTYPE_FLOAT_t scalar(self)
    
    cpdef setX(self, DTYPE_FLOAT_t x)

    cpdef setY(self, DTYPE_FLOAT_t y)

    cpdef setZ(self, DTYPE_FLOAT_t z)

    cpdef setScalar(self, DTYPE_FLOAT_t scalar)


cdef class MMatrix4x4:

    cdef np.ndarray __data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] data(self)
    
    cpdef MMatrix4x4 inverted(self)

    cpdef rotate(self, MQuaternion qq)

    cpdef translate(self, MVector3D vec3)

    cpdef scale(self, MVector3D vec3)
        
    cpdef setToIdentity(self)
    
    cpdef lookAt(self, MVector3D eye, MVector3D center, MVector3D up)
    
    cpdef perspective(self, DTYPE_FLOAT_t verticalAngle, DTYPE_FLOAT_t aspectRatio, DTYPE_FLOAT_t nearPlane, DTYPE_FLOAT_t farPlane)
    
    cpdef MVector3D mapVector(self, MVector3D vector)
    
    cpdef MQuaternion toQuaternion(self)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] add_MMatrix4x4(self, MMatrix4x4 other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] add_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] add_int(self, DTYPE_INT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] sub_MMatrix4x4(self, MMatrix4x4 other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] sub_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] sub_int(self, DTYPE_INT_t other)
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] mul_MMatrix4x4(self, MMatrix4x4 other)

    cpdef MVector3D mul_MVector3D(self, MVector3D other)

    cpdef MVector4D mul_MVector4D(self, MVector4D other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] mul_float(self, DTYPE_FLOAT_t other)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] mul_int(self, DTYPE_INT_t other)
    
    cpdef MMatrix4x4 iadd_MMatrix4x4(self, MMatrix4x4 other)
    
    cpdef MMatrix4x4 isub_MMatrix4x4(self, MMatrix4x4 other)
    
    cpdef MMatrix4x4 imul_MMatrix4x4(self, MMatrix4x4 other)
    
    cpdef MMatrix4x4 itruediv_MMatrix4x4(self, MMatrix4x4 other)


cpdef is_almost_null(v)

cpdef DTYPE_FLOAT_t get_effective_value(DTYPE_FLOAT_t v)

cpdef DTYPE_FLOAT_t get_almost_zero_value(DTYPE_FLOAT_t v)


