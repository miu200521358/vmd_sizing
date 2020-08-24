# -*- coding: utf-8 -*-
#
import math
import numpy as np
from numpy.core.fromnumeric import ndim
cimport numpy as np
cimport cython

DTYPE_INT = np.int
ctypedef np.int_t DTYPE_INT_t

DTYPE_INT8 = np.int8
ctypedef np.int8_t DTYPE_INT8_t

DTYPE_FLOAT = np.float64
ctypedef np.float64_t DTYPE_FLOAT_t

cpdef class MRect:
    cdef DTYPE_INT_t __x
    cdef DTYPE_INT_t __y
    cdef DTYPE_INT_t __width
    cdef DTYPE_INT_t __height


cpdef class MVector2D:
    cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] __data

    cpdef DTYPE_FLOAT_t length(self):
        cdef DTYPE_FLOAT_t v
    
    cpdef DTYPE_FLOAT_t lengthSquared(self):
        cdef DTYPE_FLOAT_t v

    cpdef MVector3D normalized(self):
        cdef DTYPE_FLOAT_t l2
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] normv

    cpdef None normalize(self):
        cdef DTYPE_FLOAT_t l2
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] normv

    cpdef MVector2D add_MVector2D(self, MVector2D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D add_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D add_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D sub_MVector2D(self, MVector2D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D sub_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D sub_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D mul_MVector2D(self, MVector2D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D mul_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D mul_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D truediv_MVector2D(self, MVector2D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D truediv_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D truediv_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D floordiv_MVector2D(self, MVector2D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D floordiv_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D floordiv_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D mod_MVector2D(self, MVector2D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D mod_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D mod_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D pow_MVector2D(self, MVector2D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D pow_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector2D pow_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 


cpdef class MVector3D:
    cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] __data

    cpdef DTYPE_FLOAT_t length(self):
        cdef DTYPE_FLOAT_t v
    
    cpdef DTYPE_FLOAT_t lengthSquared(self):
        cdef DTYPE_FLOAT_t v

    cpdef MVector3D normalized(self):
        cdef DTYPE_FLOAT_t l2
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] normv

    cpdef None normalize(self):
        cdef DTYPE_FLOAT_t l2
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] normv
    
    cpdef DTYPE_FLOAT_t distanceToPoint(self, MVector3D v):
        cdef DTYPE_FLOAT_t p
    
    cdef MVector3D project(self, MMatrix4x4 modelView, MMatrix4x4 projection, MRect viewport):
        cdef MVector4D tmp

    cdef MVector3D unproject(self, MMatrix4x4 modelView, MMatrix4x4 projection, MRect viewport):
        cdef MMatrix4x4 inverse
        cdef MVector4D tmp
        cdef MVector4D obj
    
    cdef MVector3D crossProduct(cls, MVector3D v1, MVector3D v2):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] crossv
            
    cdef DTYPE_FLOAT_t dotProduct(cls, MVector3D v1, MVector3D v2):
        cdef DTYPE_FLOAT_t dotv

    cpdef MVector3D add_MVector3D(self, MVector3D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D add_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D add_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D sub_MVector3D(self, MVector3D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D sub_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D sub_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D mul_MVector3D(self, MVector3D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D mul_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D mul_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D truediv_MVector3D(self, MVector3D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D truediv_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D truediv_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D floordiv_MVector3D(self, MVector3D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D floordiv_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D floordiv_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D mod_MVector3D(self, MVector3D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D mod_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D mod_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D pow_MVector3D(self, MVector3D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D pow_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector3D pow_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 


cpdef class MVector4D:
    cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] __data

    cpdef DTYPE_FLOAT_t length(self):
        cdef DTYPE_FLOAT_t v
    
    cpdef DTYPE_FLOAT_t lengthSquared(self):
        cdef DTYPE_FLOAT_t v

    cpdef MVector4D normalized(self):
        cdef DTYPE_FLOAT_t l2
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] normv

    cpdef None normalize(self):
        cdef DTYPE_FLOAT_t l2
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] normv
    
    cdef DTYPE_FLOAT_t dotProduct(cls, MVector4D v1, MVector4D v2):
        cdef DTYPE_FLOAT_t dotv

    cpdef MVector4D add_MVector4D(self, MVector4D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D add_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D add_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D sub_MVector4D(self, MVector4D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D sub_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D sub_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D mul_MVector4D(self, MVector4D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D mul_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D mul_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D truediv_MVector4D(self, MVector4D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D truediv_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D truediv_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D floordiv_MVector4D(self, MVector4D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D floordiv_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D floordiv_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D mod_MVector4D(self, MVector4D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D mod_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D mod_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D pow_MVector4D(self, MVector4D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D pow_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 

    cpdef MVector4D pow_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] v 


cpdef class MQuaternion:
    cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] __data
    
    cdef MMatrix4x4 toMatrix4x4(self):
        cdef MMatrix4x4 mat
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] m
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] q2
    
    cdef MVector3D toEulerAngles(self):
        cdef DTYPE_FLOAT_t xp
        cdef DTYPE_FLOAT_t yp
        cdef DTYPE_FLOAT_t zp
        cdef DTYPE_FLOAT_t wp

        cdef DTYPE_FLOAT_t xx
        cdef DTYPE_FLOAT_t xy
        cdef DTYPE_FLOAT_t xz
        cdef DTYPE_FLOAT_t xw
        cdef DTYPE_FLOAT_t yy
        cdef DTYPE_FLOAT_t yz
        cdef DTYPE_FLOAT_t yw
        cdef DTYPE_FLOAT_t zz
        cdef DTYPE_FLOAT_t zw
        cdef DTYPE_FLOAT_t lengthSquared

        cdef DTYPE_FLOAT_t pitch
        cdef DTYPE_FLOAT_t yaw
        cdef DTYPE_FLOAT_t roll

    cdef DTYPE_FLOAT_t toDegree(self):
        cdef DTYPE_FLOAT_t v

    cdef DTYPE_FLOAT_t calcTheata(self, MQuaternion v):
        cdef DTYPE_FLOAT_t dot
        cdef DTYPE_FLOAT_t theta
        cdef DTYPE_FLOAT_t sinOfAngle
    
    cdef DTYPE_FLOAT_t dotProduct(cls, MQuaternion v1, MQuaternion v2):
        cdef DTYPE_FLOAT_t dotv

    cdef MQuaternion fromAxisAndAngle(cls, MVector3D vec3, DTYPE_FLOAT_t angle):
        cdef DTYPE_FLOAT_t dotv

        cdef DTYPE_FLOAT_t x
        cdef DTYPE_FLOAT_t y
        cdef DTYPE_FLOAT_t z
        cdef DTYPE_FLOAT_t length

        cdef DTYPE_FLOAT_t a
        cdef DTYPE_FLOAT_t s
        cdef DTYPE_FLOAT_t c

    cdef MQuaternion fromAxisAndQuaternion(cls, MVector3D vec3, MQuaternion angle):
        cdef DTYPE_FLOAT_t dotv

        cdef DTYPE_FLOAT_t x
        cdef DTYPE_FLOAT_t y
        cdef DTYPE_FLOAT_t z
        cdef DTYPE_FLOAT_t length

        cdef DTYPE_FLOAT_t a
        cdef DTYPE_FLOAT_t s
        cdef DTYPE_FLOAT_t c

    cdef MQuaternion fromDirection(cls, MVector3D direction, MVector3D up):
        cdef MVector3D xAxis
        cdef MVector3D yAxis
        cdef MVector3D zAxis

    cdef MQuaternion fromAxes(cls, MVector3D xAxis, MVector3D yAxis, MVector3D zAxis):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] rot3x3
    
    cdef MQuaternion fromRotationMatrix(cls, np.ndarray[DTYPE_FLOAT_t, ndim=1] rot3x3):
        cdef DTYPE_FLOAT_t scalar
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] axis
        cdef DTYPE_FLOAT_t trace
        cdef DTYPE_FLOAT_t s
        cdef DTYPE_INT8_t s_next
        cdef DTYPE_INT_t i
        cdef DTYPE_FLOAT_t j
        cdef DTYPE_FLOAT_t k

    cdef MQuaternion rotationTo(cls, MVector3D fromv, MVector3D tov):
        cdef MVector3D v0
        cdef MVector3D v1
        cdef DTYPE_FLOAT_t d
        cdef MVector3D axis
        cdef DTYPE_FLOAT_t d

    cdef MQuaternion fromEulerAngles(cls, DTYPE_FLOAT_t pitch, DTYPE_FLOAT_t yaw, DTYPE_FLOAT_t roll):
        cdef DTYPE_FLOAT_t pitch
        cdef DTYPE_FLOAT_t yaw
        cdef DTYPE_FLOAT_t roll

        cdef DTYPE_FLOAT_t c1
        cdef DTYPE_FLOAT_t s1
        cdef DTYPE_FLOAT_t c2
        cdef DTYPE_FLOAT_t s2
        cdef DTYPE_FLOAT_t c3
        cdef DTYPE_FLOAT_t s3
        cdef DTYPE_FLOAT_t c1c2
        cdef DTYPE_FLOAT_t s1s2
        cdef DTYPE_FLOAT_t w
        cdef DTYPE_FLOAT_t x
        cdef DTYPE_FLOAT_t y
        cdef DTYPE_FLOAT_t z

    cdef MQuaternion nlerp(cls, MQuaternion q1, MQuaternion q2, DTYPE_FLOAT_t t):
        cdef MQuaternion q2b
        cdef DTYPE_FLOAT_t dot

    cdef MQuaternion slerp(cls, MQuaternion q1, MQuaternion q2, DTYPE_FLOAT_t t):
        cdef MQuaternion q2b
        cdef DTYPE_FLOAT_t dot
        
        cdef DTYPE_FLOAT_t factor1
        cdef DTYPE_FLOAT_t factor2

        cdef DTYPE_FLOAT_t angle
        cdef DTYPE_FLOAT_t sinOfAngle


cpdef class MMatrix4x4:
    cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] __data

    cpdef MMatrix4x4 inverted(self):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v
    
    cpdef None rotate(self, MQuaternion qq):
        cdef MMatrix4x4 qq_mat
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] m

    cpdef None translate(self, MVector3D vec3):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] vec_mat
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] data_mat

    cpdef None scale(self, MVector3D vec3):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] vec_mat

    cpdef None setToIdentity(self):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v

    cpdef None lookAt(self, MVector3D eye, MVector3D center, MVector3D up):
        cdef MVector3D forward
        cdef MVector3D side
        cdef MVector3D upVector

        cdef MMatrix4x4 m

    cpdef None perspective(self, DTYPE_FLOAT_t verticalAngle, DTYPE_FLOAT_t aspectRatio, DTYPE_FLOAT_t nearPlane, DTYPE_FLOAT_t farPlane):
        cdef DTYPE_FLOAT_t radians
        cdef DTYPE_FLOAT_t sine
        cdef DTYPE_FLOAT_t cotan
        cdef DTYPE_FLOAT_t clip

        cdef MMatrix4x4 m

    cpdef MVector3D mapVector(self, MVector3D vector):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] vec_mat
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] xyz

    cpdef MQuaternion toQuaternion(self):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] a
        cdef MQuaternion q
        cdef DTYPE_FLOAT_t trace
        cdef DTYPE_FLOAT_t s








    cpdef DTYPE_FLOAT_t lengthSquared(self):
        cdef DTYPE_FLOAT_t v

    cpdef MMatrix4x4 normalized(self):
        cdef DTYPE_FLOAT_t l2
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] normv

    cpdef None normalize(self):
        cdef DTYPE_FLOAT_t l2
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] normv
    
    cdef DTYPE_FLOAT_t dotProduct(cls, MMatrix4x4 v1, MMatrix4x4 v2):
        cdef DTYPE_FLOAT_t dotv

    cpdef MMatrix4x4 add_MMatrix4x4(self, MMatrix4x4 other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 add_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 add_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 sub_MMatrix4x4(self, MMatrix4x4 other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 sub_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 sub_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 mul_MMatrix4x4(self, MMatrix4x4 other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MVector3D mul_MVector3D(self, MVector3D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] vec_mat
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] data_sum

        cdef DTYPE_FLOAT_t x
        cdef DTYPE_FLOAT_t y
        cdef DTYPE_FLOAT_t z
        cdef DTYPE_FLOAT_t w

    cpdef MMatrix4x4 mul_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 mul_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 truediv_MMatrix4x4(self, MMatrix4x4 other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 truediv_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 truediv_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 floordiv_MMatrix4x4(self, MMatrix4x4 other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 floordiv_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 floordiv_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 mod_MMatrix4x4(self, MMatrix4x4 other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 mod_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 mod_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 pow_MMatrix4x4(self, MMatrix4x4 other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 pow_int(self, DTYPE_INT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 

    cpdef MMatrix4x4 pow_float(self, DTYPE_FLOAT_t other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] v 
    

    


cpdef bool is_almost_null(DTYPE_FLOAT_t v)

cpdef DTYPE_FLOAT_t get_effective_value(DTYPE_FLOAT_t v)

cpdef bool get_almost_zero_value(DTYPE_FLOAT_t v)
