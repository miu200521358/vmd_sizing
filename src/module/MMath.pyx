# -*- coding: utf-8 -*-
#
# cython: boundscheck=False
# cython: wraparound=False
#
# ccython: profile=True
# ccython: linetrace=True
# ccython: binding=True
# cdistutils: define_macros=CYTHON_TRACE_NOGIL=1
import math
import numpy as np
import quaternion # noqa
cimport numpy as np
cimport cython
from libc.math cimport sin, cos, acos, atan2, asin, pi, sqrt
from math import degrees, radians

from utils.MLogger import MLogger # noqa

logger = MLogger(__name__, level=1)


cdef class MRect:

    def __init__(self, x=0, y=0, width=0, height=0):
        self.__x = x
        self.__y = y
        self.__width = width
        self.__height = height

    cpdef x(self):
        return self.__x

    cpdef y(self):
        return self.__y

    cpdef width(self):
        return self.__width

    cpdef height(self):
        return self.__height

    def __str__(self):
        return "MRect({0}, {1}, {2}, {3})".format(self.__x, self.__y, self.__width, self.__height)


cdef class MVector2D:

    def __init__(self, x=0.0, y=0.0):
        if isinstance(x, float):
            self.__data = np.array([x, y], dtype=np.float64)
        elif isinstance(x, MVector2D):
            # クラスの場合
            self.__data = np.array([x.x(), x.y()], dtype=np.float64)
        elif isinstance(x, np.ndarray):
            # arrayそのものの場合
            self.__data = np.array([x[0], x[1]], dtype=np.float64)
        else:
            self.__data = np.array([x, y], dtype=np.float64)

    cpdef DTYPE_FLOAT_t length(self):
        return np.linalg.norm(self.__data, ord=2)

    cpdef DTYPE_FLOAT_t lengthSquared(self):
        return np.linalg.norm(self.__data, ord=2)**2

    cpdef MVector2D normalized(self):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] l2 = np.linalg.norm(self.__data, ord=2, axis=-1, keepdims=True)
        l2[l2 == 0] = 1
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] normv = self.__data / l2
        return MVector2D(normv[0], normv[1])

    cpdef MVector2D normalize(self):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] l2 = np.linalg.norm(self.__data, ord=2, axis=-1, keepdims=True)
        l2[l2 == 0] = 1
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] normv = self.__data / l2
        self.__data = normv
    
    cpdef MVector2D effective(self):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] d = self.data()
        d[np.isnan(d)] = 0
        d[np.isinf(d)] = 0
        self.__data = d

        return self
            
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] data(self):
        return self.__data

    def __str__(self):
        return "MVector2D({0}, {1})".format(self.x(), self.y())

    def __lt__(self, other):
        return np.all(np.less(self.data(), other.data()))

    def __le__(self, other):
        return np.all(np.less_equal(self.data(), other.data()))

    def __eq__(self, other):
        return np.all(np.equal(self.data(), other.data()))

    def __ne__(self, other):
        return np.any(np.not_equal(self.data(), other.data()))

    def __gt__(self, other):
        return np.all(np.greater(self.data(), other.data()))

    def __ge__(self, other):
        return np.all(np.greater_equal(self.data(), other.data()))

    def __add__(self, other):
        if isinstance(other, MVector2D):
            v = self.add_MVector2D(other)
        elif isinstance(other, np.int):
            v = self.add_int(other)
        else:
            v = self.add_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_MVector2D(self, MVector2D other):
        return self.data() + other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_float(self, DTYPE_FLOAT_t other):
        return self.data() + other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_int(self, DTYPE_INT_t other):
        return self.data() + other

    def __sub__(self, other):
        if isinstance(other, MVector2D):
            v = self.sub_MVector2D(other)
        elif isinstance(other, np.int):
            v = self.sub_int(other)
        else:
            v = self.sub_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_MVector2D(self, MVector2D other):
        return self.data() - other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_float(self, DTYPE_FLOAT_t other):
        return self.data() - other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_int(self, DTYPE_INT_t other):
        return self.data() - other

    def __mul__(self, other):
        if isinstance(other, MVector2D):
            v = self.mul_MVector2D(other)
        elif isinstance(other, np.int):
            v = self.mul_int(other)
        else:
            v = self.mul_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_MVector2D(self, MVector2D other):
        return self.data() * other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_float(self, DTYPE_FLOAT_t other):
        return self.data() * other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_int(self, DTYPE_INT_t other):
        return self.data() * other
        
    def __truediv__(self, other):
        if isinstance(other, MVector2D):
            v = self.truediv_MVector2D(other)
        elif isinstance(other, np.int):
            v = self.truediv_int(other)
        else:
            v = self.truediv_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_MVector2D(self, MVector2D other):
        return self.data() / other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_float(self, DTYPE_FLOAT_t other):
        return self.data() / other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_int(self, DTYPE_INT_t other):
        return self.data() / other

    def __floordiv__(self, other):
        if isinstance(other, MVector2D):
            v = self.floordiv_MVector2D(other)
        elif isinstance(other, np.int):
            v = self.floordiv_int(other)
        else:
            v = self.floordiv_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_MVector2D(self, MVector2D other):
        return self.data() // other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_float(self, DTYPE_FLOAT_t other):
        return self.data() // other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_int(self, DTYPE_INT_t other):
        return self.data() // other

    def __mod__(self, other):
        if isinstance(other, MVector2D):
            v = self.mod_MVector2D(other)
        elif isinstance(other, np.int):
            v = self.mod_int(other)
        else:
            v = self.mod_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_MVector2D(self, MVector2D other):
        return self.data() % other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_float(self, DTYPE_FLOAT_t other):
        return self.data() % other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_int(self, DTYPE_INT_t other):
        return self.data() % other

    # def __pow__(self, other):
    #     if isinstance(other, MVector2D):
    #         v = self.pow_MVector2D(other)
    #     elif isinstance(other, np.int):
    #         v = self.pow_int(other)
    #     else:
    #         v = self.pow_float(other)
    #     v2 = self.__class__(v)
    #     v2.effective()
    #     return v2
    
    # def pow_MVector2D(self, other):
    #     v = self.data() ** other.data()
    #     return v

    # def pow_float(self, other):
    #     v = self.data() ** other
    #     return v

    # def pow_int(self, other):
    #     v = self.data() ** other
    #     return v

    def __lshift__(self, other):
        if isinstance(other, MVector2D):
            v = self.data() << other.data()
        else:
            v = self.data() << other
        v2 = self.__class__(v)
        v2.effective()
        return v2

    def __rshift__(self, other):
        if isinstance(other, MVector2D):
            v = self.data() >> other.data()
        else:
            v = self.data() >> other
        v2 = self.__class__(v)
        v2.effective()
        return v2

    def __and__(self, other):
        v = self.data() & other.data()
        v2 = self.__class__(v)
        v2.effective()
        return v2

    def __dataor__(self, other):
        v = self.data() ^ other.data()
        v2 = self.__class__(v)
        v2.effective()
        return v2

    def __or__(self, other):
        v = self.data() | other.data()
        v2 = self.__class__(v)
        v2.effective()
        return v2

    def __neg__(self):
        return self.__class__(-self.x(), -self.y())

    def __pos__(self):
        return self.__class__(+self.x(), +self.y())

    # def __invert__(self):
    #     return self.__class__(~self.x(), ~self.y())
    
    cpdef DTYPE_FLOAT_t x(self):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] d = self.data()
        return d[0]

    cpdef DTYPE_FLOAT_t y(self):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] d = self.data()
        return d[1]
        
    cpdef setX(self, DTYPE_FLOAT_t x):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] d = self.data()
        d[0] = x
        self.__data = d

    cpdef setY(self, DTYPE_FLOAT_t y):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] d = self.data()
        d[1] = y
        self.__data = d

    def to_log(self):
        return "x: {0}, y: {1}".format(round(self.x(), 5), round(self.y(), 5))

    def __reduce__(self):
        return (rebuild_MVector2D, (self.x(), self.y(), self.z()))

def rebuild_MVector2D(x, y, z):
    return MVector2D(x, y, z)


cdef class MVector3D:

    def __init__(self, x=0.0, y=0.0, z=0.0):
        if isinstance(x, float):
            self.__data = np.array([x, y, z], dtype=np.float64)
        elif isinstance(x, MVector3D):
            # クラスの場合
            self.__data = np.array([x.x(), x.y(), x.z()], dtype=np.float64)
        elif isinstance(x, np.ndarray):
            # arrayそのものの場合
            self.__data = np.array([x[0], x[1], x[2]], dtype=np.float64)
        else:
            self.__data = np.array([x, y, z], dtype=np.float64)

    cpdef MVector3D copy(self):
        return MVector3D(self.x(), self.y(), self.z())

    cpdef DTYPE_FLOAT_t length(self):
        return np.linalg.norm(self.__data, ord=2)

    cpdef DTYPE_FLOAT_t lengthSquared(self):
        return np.linalg.norm(self.__data, ord=2)**2

    cpdef MVector3D normalized(self):
        self.effective()
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] l2 = np.linalg.norm(self.__data, ord=2, axis=-1, keepdims=True)
        l2[l2 == 0] = 1
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] normv = self.__data / l2
        return MVector3D(normv[0], normv[1], normv[2])

    cpdef normalize(self):
        self.effective()
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] l2 = np.linalg.norm(self.__data, ord=2, axis=-1, keepdims=True)
        l2[l2 == 0] = 1
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] normv = self.__data / l2
        self.__data = normv
    
    cpdef DTYPE_FLOAT_t distanceToPoint(self, MVector3D v):
        return MVector3D(self.data() - v.data()).length()
    
    cpdef MVector3D project(self, MMatrix4x4 modelView, MMatrix4x4 projection, MRect viewport):
        logger.debug("project 1")
        cdef MVector4D tmp = MVector4D(self.x(), self.y(), self.z(), 1)
        logger.debug("project 2")
        tmp = (projection * modelView) * tmp
        logger.debug("project 3")
        if is_almost_null(tmp.w()):
            tmp.setW(1)
        logger.debug("project 4")

        tmp /= tmp.w()
        logger.debug("project 5")
        tmp = tmp * 0.5 + MVector4D(0.5, 0.5, 0.5, 0.5)
        logger.debug("project 6")
        tmp.setX(tmp.x() * viewport.width() + viewport.x())
        logger.debug("project 7")
        tmp.setY(tmp.y() * viewport.height() + viewport.y())
        logger.debug("project 8")

        tmp.effective()
        logger.debug("project 9")

        return tmp.toVector3D()

    cpdef MVector3D unproject(self, MMatrix4x4 modelView, MMatrix4x4 projection, MRect viewport):
        cdef MMatrix4x4 inverse = (projection * modelView).inverted()

        cdef MVector4D tmp = MVector4D(self.x(), self.y(), self.z(), 1)
        tmp.setX((tmp.x() - viewport.x()) / viewport.width())
        tmp.setY((tmp.y() - viewport.y()) / viewport.height())
        tmp = tmp * 2 - MVector4D(1, 1, 1, 1)
        tmp.effective()

        obj = inverse * tmp
        if is_almost_null(obj.w()):
            obj.setW(1)

        obj /= obj.w()
        obj.effective()
        
        return obj.toVector3D()
        
    cpdef MVector4D toVector4D(self):
        return MVector4D(self.x(), self.y(), self.z(), 0)

    def is_almost_null(self):
        return (is_almost_null(self.x()) and is_almost_null(self.y()) and is_almost_null(self.z()))
    
    cpdef MVector3D effective(self):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] d = self.data()
        d[np.isnan(d)] = 0
        d[np.isinf(d)] = 0
        self.__data = d

        return self
                
    def abs(self):
        self.setX(abs(get_effective_value(self.x())))
        self.setY(abs(get_effective_value(self.y())))
        self.setZ(abs(get_effective_value(self.z())))

        return self
                
    def one(self):
        self.effective()
        self.setX(1 if is_almost_null(self.x()) else self.x())
        self.setY(1 if is_almost_null(self.y()) else self.y())
        self.setZ(1 if is_almost_null(self.z()) else self.z())

        return self
    
    def non_zero(self):
        self.effective()
        self.setX(0.0001 if is_almost_null(self.x()) else self.x())
        self.setY(0.0001 if is_almost_null(self.y()) else self.y())
        self.setZ(0.0001 if is_almost_null(self.z()) else self.z())

        return self
    
    def isnan(self):
        d = self.data().astype(np.float64)
        return np.isnan(d).any()

    @classmethod
    def crossProduct(cls, v1, v2):
        cdef MVector3D v = MVector3D()
        return v.c_crossProduct(v1, v2) 

    cdef MVector3D c_crossProduct(self, MVector3D v1, MVector3D v2):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] crossv = np.cross(v1.__data, v2.__data)
        return MVector3D(crossv[0], crossv[1], crossv[2])

    @classmethod
    def dotProduct(cls, v1, v2):
        cdef MVector3D v = MVector3D()
        return v.c_dotProduct(v1, v2) 

    cdef DTYPE_FLOAT_t c_dotProduct(self, MVector3D v1, MVector3D v2):
        return np.dot(v1.__data, v2.__data)
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] data(self):
        return self.__data
    
    def to_log(self):
        return "x: {0}, y: {1} z: {2}".format(round(self.x(), 5), round(self.y(), 5), round(self.z(), 5))

    def __str__(self):
        return "MVector3D({0}, {1}, {2})".format(self.x(), self.y(), self.z())

    def __lt__(self, other):
        return np.all(np.less(self.data(), other.data()))

    def __le__(self, other):
        return np.all(np.less_equal(self.data(), other.data()))

    def __eq__(self, other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] d1 = self.data()
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] d2 = other.data()
        return d1[0] == d2[0] and d1[1] == d2[1] and d1[2] == d2[2]

    def __ne__(self, other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] d1 = self.data()
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] d2 = other.data()
        return d1[0] != d2[0] or d1[1] != d2[1] or d1[2] != d2[2]

    def __gt__(self, other):
        return np.all(np.greater(self.data(), other.data()))

    def __ge__(self, other):
        return np.all(np.greater_equal(self.data(), other.data()))

    def __add__(self, other):
        if isinstance(other, MVector3D):
            v = self.add_MVector3D(other)
        elif isinstance(other, np.int):
            v = self.add_int(other)
        else:
            v = self.add_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_MVector3D(self, MVector3D other):
        return self.data() + other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_float(self, DTYPE_FLOAT_t other):
        return self.data() + other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_int(self, DTYPE_INT_t other):
        return self.data() + other

    def __sub__(self, other):
        if isinstance(other, MVector3D):
            v = self.sub_MVector3D(other)
        elif isinstance(other, np.int):
            v = self.sub_int(other)
        else:
            v = self.sub_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_MVector3D(self, MVector3D other):
        return self.data() - other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_float(self, DTYPE_FLOAT_t other):
        return self.data() - other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_int(self, DTYPE_INT_t other):
        return self.data() - other

    def __mul__(self, other):
        if isinstance(other, MVector3D):
            v = self.mul_MVector3D(other)
        elif isinstance(other, np.int):
            v = self.mul_int(other)
        else:
            v = self.mul_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_MVector3D(self, MVector3D other):
        return self.data() * other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_float(self, DTYPE_FLOAT_t other):
        return self.data() * other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_int(self, DTYPE_INT_t other):
        return self.data() * other
        
    def __truediv__(self, other):
        if isinstance(other, MVector3D):
            v = self.truediv_MVector3D(other)
        elif isinstance(other, np.int):
            v = self.truediv_int(other)
        else:
            v = self.truediv_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_MVector3D(self, MVector3D other):
        return self.data() / other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_float(self, DTYPE_FLOAT_t other):
        return self.data() / other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_int(self, DTYPE_INT_t other):
        return self.data() / other

    def __floordiv__(self, other):
        if isinstance(other, MVector3D):
            v = self.floordiv_MVector3D(other)
        elif isinstance(other, np.int):
            v = self.floordiv_int(other)
        else:
            v = self.floordiv_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_MVector3D(self, MVector3D other):
        return self.data() // other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_float(self, DTYPE_FLOAT_t other):
        return self.data() // other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_int(self, DTYPE_INT_t other):
        return self.data() // other

    def __mod__(self, other):
        if isinstance(other, MVector3D):
            v = self.mod_MVector3D(other)
        elif isinstance(other, np.int):
            v = self.mod_int(other)
        else:
            v = self.mod_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_MVector3D(self, MVector3D other):
        return self.data() % other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_float(self, DTYPE_FLOAT_t other):
        return self.data() % other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_int(self, DTYPE_INT_t other):
        return self.data() % other

    # def __pow__(self, other):
    #     if isinstance(other, MVector3D):
    #         v = self.pow_MVector3D(other)
    #     elif isinstance(other, np.int):
    #         v = self.pow_int(other)
    #     else:
    #         v = self.pow_float(other)
    #     v2 = self.__class__(v)
    #     v2.effective()
    #     return v2
    
    # def pow_MVector3D(self, other):
    #     v = self.__data ** other.__data
    #     return v

    # def pow_float(self, other):
    #     v = self.__data ** other
    #     return v

    # def pow_int(self, other):
    #     v = self.__data ** other
    #     return v

    def __lshift__(self, other):
        if isinstance(other, MVector3D):
            v = self.data() << other.data()
        else:
            v = self.data() << other
        v2 = self.__class__(v)
        v2.effective()
        return v2

    def __rshift__(self, other):
        if isinstance(other, MVector3D):
            v = self.data() >> other.data()
        else:
            v = self.data() >> other
        v2 = self.__class__(v)
        v2.effective()
        return v2

    def __and__(self, other):
        v = self.data() & other.data()
        v2 = self.__class__(v)
        v2.effective()
        return v2

    def __dataor__(self, other):
        v = self.data() ^ other.data()
        v2 = self.__class__(v)
        v2.effective()
        return v2

    def __or__(self, other):
        v = self.data() | other.data()
        v2 = self.__class__(v)
        v2.effective()
        return v2

    def __neg__(self):
        return self.__class__(-self.x(), -self.y(), -self.z())

    def __pos__(self):
        return self.__class__(+self.x(), +self.y(), +self.z())

    cpdef DTYPE_FLOAT_t x(self):
        return self.__data[0]

    cpdef DTYPE_FLOAT_t y(self):
        return self.__data[1]

    cpdef DTYPE_FLOAT_t z(self):
        return self.__data[2]
    
    cpdef setX(self, DTYPE_FLOAT_t x):
        self.__data[0] = x

    cpdef setY(self, DTYPE_FLOAT_t y):
        self.__data[1] = y

    cpdef setZ(self, DTYPE_FLOAT_t z):
        self.__data[2] = z

    def __reduce__(self):
        return (rebuild_MVector3D, (self.x(), self.y(), self.z()))

def rebuild_MVector3D(x, y, z):
    return MVector3D(x, y, z)

cdef class MVector4D:

    def __init__(self, x=0.0, y=0.0, z=0.0, w=0.0):
        if isinstance(x, float):
            self.__data = np.array([x, y, z, w], dtype=np.float64)
        elif isinstance(x, MVector4D):
            # クラスの場合
            self.__data = np.array([x.x(), x.y(), x.z(), x.w()], dtype=np.float64)
        elif isinstance(x, np.ndarray):
            # 行列そのものの場合
            self.__data = np.array([x[0], x[1], x[2], x[3]], dtype=np.float64)
        else:
            self.__data = np.array([x, y, z, w], dtype=np.float64)
    
    cpdef MVector4D copy(self):
        return MVector4D(self.x(), self.y(), self.z(), self.w())

    cpdef DTYPE_FLOAT_t length(self):
        return np.linalg.norm(self.__data, ord=2)

    cpdef DTYPE_FLOAT_t lengthSquared(self):
        return np.linalg.norm(self.__data, ord=2)**2

    cpdef MVector4D normalized(self):
        self.effective()
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] l2 = np.linalg.norm(self.__data, ord=2, axis=-1, keepdims=True)
        l2[l2 == 0] = 1
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] normv = self.__data / l2
        return MVector4D(normv[0], normv[1], normv[2], normv[3])

    cpdef normalize(self):
        self.effective()
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] l2 = np.linalg.norm(self.__data, ord=2, axis=-1, keepdims=True)
        l2[l2 == 0] = 1
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] normv = self.__data / l2
        self.__data = normv

    cpdef MVector3D toVector3D(self):
        return MVector3D(self.x(), self.y(), self.z())

    def is_almost_null(self):
        return (is_almost_null(self.x()) and is_almost_null(self.y()) and is_almost_null(self.z()) and is_almost_null(self.w()))
                   
    cpdef MVector4D effective(self):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] d = self.data()
        d[np.isnan(d)] = 0
        d[np.isinf(d)] = 0
        self.__data = d

        return self
    
    @classmethod
    def dotProduct(cls, v1, v2):
        cdef MVector4D v = MVector4D()
        return v.c_dotProduct(v1, v2) 

    cdef DTYPE_FLOAT_t c_dotProduct(self, MVector4D v1, MVector4D v2):
        return np.dot(v1.__data, v2.__data)
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] data(self):
        return self.__data

    def __str__(self):
        return "MVector4D({0}, {1}, {2}, {3})".format(self.x(), self.y(), self.z(), self.w())

    def __lt__(self, other):
        return self.data().less(other.data())

    def __le__(self, other):
        return self.data().less_equal(other.data())

    def __eq__(self, other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] d1 = self.data()
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] d2 = other.data()
        return d1[0] == d2[0] and d1[1] == d2[1] and d1[2] == d2[2] and d1[3] == d2[3]

    def __ne__(self, other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] d1 = self.data()
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] d2 = other.data()
        return d1[0] != d2[0] or d1[1] != d2[1] or d1[2] != d2[2] or d1[3] != d2[3]

    def __eq__(self, other):
        return self.data().equal(other.data())

    def __ne__(self, other):
        return self.data().not_equal(other.data())

    def __gt__(self, other):
        return self.data().greater(other.data())

    def __ge__(self, other):
        return self.data().greater_equal(other.data())

    def __add__(self, other):
        if isinstance(other, MVector4D):
            v = self.add_MVector4D(other)
        elif isinstance(other, np.int):
            v = self.add_int(other)
        else:
            v = self.add_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_MVector4D(self, MVector4D other):
        return self.data() + other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_float(self, DTYPE_FLOAT_t other):
        return self.data() + other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_int(self, DTYPE_INT_t other):
        return self.data() + other

    def __sub__(self, other):
        if isinstance(other, MVector4D):
            v = self.sub_MVector4D(other)
        elif isinstance(other, np.int):
            v = self.sub_int(other)
        else:
            v = self.sub_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_MVector4D(self, MVector4D other):
        return self.data() - other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_float(self, DTYPE_FLOAT_t other):
        return self.data() - other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_int(self, DTYPE_INT_t other):
        return self.data() - other

    def __mul__(self, other):
        if isinstance(other, MVector4D):
            v = self.mul_MVector4D(other)
        elif isinstance(other, np.int):
            v = self.mul_int(other)
        else:
            v = self.mul_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_MVector4D(self, MVector4D other):
        return self.data() * other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_float(self, DTYPE_FLOAT_t other):
        return self.data() * other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_int(self, DTYPE_INT_t other):
        return self.data() * other
        
    def __truediv__(self, other):
        if isinstance(other, MVector4D):
            v = self.truediv_MVector4D(other)
        elif isinstance(other, np.int):
            v = self.truediv_int(other)
        else:
            v = self.truediv_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_MVector4D(self, MVector4D other):
        return self.data() / other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_float(self, DTYPE_FLOAT_t other):
        return self.data() / other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_int(self, DTYPE_INT_t other):
        return self.data() / other

    def __floordiv__(self, other):
        if isinstance(other, MVector4D):
            v = self.floordiv_MVector4D(other)
        elif isinstance(other, np.int):
            v = self.floordiv_int(other)
        else:
            v = self.floordiv_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_MVector4D(self, MVector4D other):
        return self.data() // other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_float(self, DTYPE_FLOAT_t other):
        return self.data() // other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_int(self, DTYPE_INT_t other):
        return self.data() // other

    def __mod__(self, other):
        if isinstance(other, MVector4D):
            v = self.mod_MVector4D(other)
        elif isinstance(other, np.int):
            v = self.mod_int(other)
        else:
            v = self.mod_float(other)
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_MVector4D(self, MVector4D other):
        return self.data() % other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_float(self, DTYPE_FLOAT_t other):
        return self.data() % other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_int(self, DTYPE_INT_t other):
        return self.data() % other

    # def __pow__(self, other):
    #     if isinstance(other, MVector4D):
    #         v = self.pow_MVector4D(other)
    #     elif isinstance(other, np.int):
    #         v = self.pow_int(other)
    #     else:
    #         v = self.pow_float(other)
    #     v2 = self.__class__(v)
    #     v2.effective()
    #     return v2
    
    # def pow_MVector4D(self, other):
    #     v = self.__data ** other.__data
    #     return v

    # def pow_float(self, other):
    #     v = self.__data ** other
    #     return v

    # def pow_int(self, other):
    #     v = self.__data ** other
    #     return v

    def __lshift__(self, other):
        if isinstance(other, MVector4D):
            v = self.data() << other.data()
        else:
            v = self.data() << other
        v2 = self.__class__(v)
        v2.effective()
        return v2

    def __rshift__(self, other):
        if isinstance(other, MVector4D):
            v = self.data() >> other.data()
        else:
            v = self.data() >> other
        v2 = self.__class__(v)
        v2.effective()
        return v2

    def __and__(self, other):
        v = self.data() & other.data()
        v2 = self.__class__(v)
        v2.effective()
        return v2

    def __dataor__(self, other):
        v = self.data() ^ other.data()
        v2 = self.__class__(v)
        v2.effective()
        return v2

    def __or__(self, other):
        v = self.data() | other.data()
        v2 = self.__class__(v)
        v2.effective()
        return v2

    def __neg__(self):
        return self.__class__(-self.x(), -self.y(), -self.z(), -self.w())

    def __pos__(self):
        return self.__class__(+self.x(), +self.y(), +self.z(), +self.w())

    # def __invert__(self):
    #     return self.__class__(~self.__data[0], ~self.__data[1], ~self.__data[2], ~self.__data[3])
    
    cpdef DTYPE_FLOAT_t x(self):
        return self.__data[0]

    cpdef DTYPE_FLOAT_t y(self):
        return self.__data[1]

    cpdef DTYPE_FLOAT_t z(self):
        return self.__data[2]

    cpdef DTYPE_FLOAT_t w(self):
        return self.__data[3]
    
    cpdef setX(self, DTYPE_FLOAT_t x):
        self.__data[0] = x

    cpdef setY(self, DTYPE_FLOAT_t y):
        self.__data[1] = y

    cpdef setZ(self, DTYPE_FLOAT_t z):
        self.__data[2] = z

    cpdef setW(self, DTYPE_FLOAT_t w):
        self.__data[3] = w

    def __reduce__(self):
        return (rebuild_MVector4D, (self.x(), self.y(), self.z(), self.w()))

def rebuild_MVector4D(x, y, z, w):
    return MVector4D(x, y, z, w)


cdef class MQuaternion:

    def __init__(self, w=1.0, x=0.0, y=0.0, z=0.0):
        if isinstance(w, float):
            self.__data = np.array([w, x, y, z], dtype=np.float64)
        elif isinstance(w, MQuaternion):
            # クラスの場合
            self.__data = w.__data
        elif isinstance(w, np.quaternion):
            # quaternionの場合
            self.__data = w.components
        elif isinstance(w, np.ndarray):
            # arrayそのものの場合
            self.__data = np.array([w[0], w[1], w[2], w[3]], dtype=np.float64)
        else:
            self.__data = np.array([w, x, y, z], dtype=np.float64)

    def copy(self):
        return MQuaternion(self.scalar(), self.x(), self.y(), self.z())
    
    def __str__(self):
        return "MQuaternion({0}, {1}, {2}, {3})".format(self.scalar(), self.x(), self.y(), self.z())

    def inverted(self):
        v = self.data().inverse()
        return self.__class__(v.w, v.x, v.y, v.z)

    def length(self):
        return self.data().abs()

    def lengthSquared(self):
        return self.data().abs()**2

    def absolute(self):
        return self.data().absolute()

    def normalized(self):
        self.effective()
        v = self.data().normalized()
        return MQuaternion(v.w, v.x, v.y, v.z)

    def normalize(self):
        self.__data = self.data().normalized().components

    cpdef effective(self):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] d = self.data().components
        d[np.isnan(d)] = 0
        d[np.isinf(d)] = 0
        self.__data = d

        # Scalarは1がデフォルトとなる
        self.setScalar(1 if self.scalar() == 0 else self.scalar())

    cpdef MMatrix4x4 toMatrix4x4(self):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] m = np.eye(4, dtype=np.float64)

        # q(w,x,y,z)から(x,y,z,w)に並べ替え.
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] q2 = np.array([self.data().x, self.data().y, self.data().z, self.data().w], dtype=np.float64)

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

        return MMatrix4x4(m)
    
    cpdef MVector4D toVector4D(self):
        return MVector4D(self.data().x, self.data().y, self.data().z, self.data().w)

    cpdef MVector3D toEulerAngles4MMD(self):
        # MMDの表記に合わせたオイラー角
        cdef MVector3D euler = self.toEulerAngles()

        return MVector3D(euler.x(), -euler.y(), -euler.z())

    # http://www.j3d.org/matrix_faq/matrfaq_latest.html#Q37
    cpdef MVector3D toEulerAngles(self):
        cdef DTYPE_FLOAT_t xp = self.data().x
        cdef DTYPE_FLOAT_t yp = self.data().y
        cdef DTYPE_FLOAT_t zp = self.data().z
        cdef DTYPE_FLOAT_t wp = self.data().w

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

        if not is_almost_null(lengthSquared - 1.0) and not is_almost_null(lengthSquared):
            xx /= lengthSquared
            xy /= lengthSquared  # same as (xp / length) * (yp / length)
            xz /= lengthSquared
            xw /= lengthSquared
            yy /= lengthSquared
            yz /= lengthSquared
            yw /= lengthSquared
            zz /= lengthSquared
            zw /= lengthSquared

        cdef DTYPE_FLOAT_t pitch = asin(max(-1, min(1, -2.0 * (yz - xw))))
        cdef DTYPE_FLOAT_t yaw = 0
        cdef DTYPE_FLOAT_t roll = 0
        
        if pitch < (pi / 2):
            if pitch > -(pi / 2):
                yaw = atan2(2.0 * (xz + yw), 1.0 - 2.0 * (xx + yy))
                roll = atan2(2.0 * (xy + zw), 1.0 - 2.0 * (xx + zz))
            else:
                # not a unique solution
                roll = 0.0
                yaw = -atan2(-2.0 * (xy - zw), 1.0 - 2.0 * (yy + zz))
        else:
            # not a unique solution
            roll = 0.0
            yaw = atan2(-2.0 * (xy - zw), 1.0 - 2.0 * (yy + zz))

        return MVector3D(degrees(pitch), degrees(yaw), degrees(roll))
    
    # 角度に変換
    cpdef DTYPE_FLOAT_t toDegree(self):
        return degrees(2 * acos(min(1, max(-1, self.scalar()))))

    # 自分ともうひとつの値vとのtheta（変位量）を返す
    cpdef DTYPE_FLOAT_t calcTheata(self, MQuaternion v):
        return acos(min(1, max(-1, v.c_dotProduct(self.normalized(), v.normalized()))))
        # cdef DTYPE_FLOAT_t dot = v.c_dotProduct(self.normalized(), v.normalized())
        # cdef DTYPE_FLOAT_t theta = acos(min(1, max(-1, dot)))
        # cdef DTYPE_FLOAT_t sinOfAngle = sin(theta)
        # return sinOfAngle

    @classmethod
    def dotProduct(cls, v1, v2):
        cdef MQuaternion v = MQuaternion()
        return v.c_dotProduct(v1, v2) 
    
    cdef DTYPE_FLOAT_t c_dotProduct(self, MQuaternion v1, MQuaternion v2):
        return np.dot(v1.data().components, v2.data().components)
        # return np.sum(v1.data().components * v2.data().components)
    
    @classmethod
    def fromAxisAndAngle(cls, vec3, angle):
        cdef MQuaternion v = MQuaternion()
        return v.c_fromAxisAndAngle(vec3, angle) 
    
    cdef MQuaternion c_fromAxisAndAngle(self, MVector3D vec3, DTYPE_FLOAT_t angle):
        cdef DTYPE_FLOAT_t x = vec3.x()
        cdef DTYPE_FLOAT_t y = vec3.y()
        cdef DTYPE_FLOAT_t z = vec3.z()
        cdef DTYPE_FLOAT_t length = sqrt(x * x + y * y + z * z)

        if not is_almost_null(length - 1.0) and not is_almost_null(length):
            x /= length
            y /= length
            z /= length

        cdef DTYPE_FLOAT_t a = radians(angle / 2.0)
        cdef DTYPE_FLOAT_t s = sin(a)
        cdef DTYPE_FLOAT_t c = cos(a)
        return MQuaternion(c, x * s, y * s, z * s).normalized()

    @classmethod
    def fromAxisAndQuaternion(cls, vec3, qq):
        cdef MQuaternion v = MQuaternion()
        return v.c_fromAxisAndQuaternion(vec3, qq) 
    
    cdef MQuaternion c_fromAxisAndQuaternion(self, MVector3D vec3, MQuaternion qq):
        qq.normalize()

        cdef DTYPE_FLOAT_t x = vec3.x()
        cdef DTYPE_FLOAT_t y = vec3.y()
        cdef DTYPE_FLOAT_t z = vec3.z()
        cdef DTYPE_FLOAT_t length = sqrt(x * x + y * y + z * z)

        if not is_almost_null(length - 1.0) and not is_almost_null(length):
            x /= length
            y /= length
            z /= length

        cdef DTYPE_FLOAT_t a = acos(min(1, max(-1, qq.scalar())))
        cdef DTYPE_FLOAT_t s = sin(a)
        cdef DTYPE_FLOAT_t c = cos(a)

        # logger.test("scalar: %s, a: %s, c: %s, degree: %s", qq.scalar(), a, c, degrees(2 * acos(min(1, max(-1, qq.scalar())))))

        return MQuaternion(c, x * s, y * s, z * s).normalized()

    @classmethod
    def fromDirection(cls, direction, up):
        cdef MQuaternion v = MQuaternion()
        return v.c_fromDirection(direction, up) 
    
    cdef MQuaternion c_fromDirection(self, MVector3D direction, MVector3D up):
        if direction.is_almost_null():
            return MQuaternion()

        cdef MVector3D zAxis = direction.normalized()
        cdef MVector3D xAxis = up.c_crossProduct(up, zAxis)
        if (is_almost_null(xAxis.lengthSquared())):
            # collinear or invalid up vector derive shortest arc to new direction
            return MQuaternion.rotationTo(MVector3D(0.0, 0.0, 1.0), zAxis)
        
        xAxis.normalize()
        cdef MVector3D yAxis = zAxis.c_crossProduct(zAxis, xAxis)
        return MQuaternion.fromAxes(xAxis, yAxis, zAxis)

    @classmethod
    def fromAxes(cls, xAxis, yAxis, zAxis):
        cdef MQuaternion v = MQuaternion()
        return v.c_fromAxes(xAxis, yAxis, zAxis) 
    
    cdef MQuaternion c_fromAxes(self, MVector3D xAxis, MVector3D yAxis, MVector3D zAxis):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] rot3x3 = np.array([[xAxis.x(), yAxis.x(), zAxis.x()], [xAxis.y(), yAxis.y(), zAxis.y()], [xAxis.z(), yAxis.z(), zAxis.z()]])
        return MQuaternion.fromRotationMatrix(rot3x3)
    
    @classmethod
    def fromRotationMatrix(cls, rot3x3):
        cdef MQuaternion v = MQuaternion()
        return v.c_fromRotationMatrix(rot3x3) 
    
    cdef MQuaternion c_fromRotationMatrix(self, np.ndarray[DTYPE_FLOAT_t, ndim=2] rot3x3):
        cdef DTYPE_FLOAT_t scalar = 0
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] axis = np.zeros(3)

        cdef DTYPE_FLOAT_t trace = rot3x3[0][0] + rot3x3[1][1] + rot3x3[2][2]
        cdef DTYPE_FLOAT_t s = 0
        cdef np.ndarray[DTYPE_INT8_t, ndim=1] s_next
        cdef DTYPE_INT_t i = 0
        cdef DTYPE_INT_t j = 0
        cdef DTYPE_INT_t k = 0

        if trace > 0.00000001:
            s = 2.0 * sqrt(trace + 1.0)
            scalar = 0.25 * s
            axis[0] = (rot3x3[2][1] - rot3x3[1][2]) / s
            axis[1] = (rot3x3[0][2] - rot3x3[2][0]) / s
            axis[2] = (rot3x3[1][0] - rot3x3[0][1]) / s
        else:
            s_next = np.array([1, 2, 0], dtype=np.int8)
            if rot3x3[1][1] > rot3x3[0][0]:
                i = 1
            if rot3x3[2][2] > rot3x3[i][i]:
                i = 2

            j = s_next[i]
            k = s_next[j]

            s = 2.0 * sqrt(rot3x3[i][i] - rot3x3[j][j] - rot3x3[k][k] + 1.0)
            axis[i] = 0.25 * s

            scalar = (rot3x3[k][j] - rot3x3[j][k]) / s
            axis[j] = (rot3x3[j][i] + rot3x3[i][j]) / s
            axis[k] = (rot3x3[k][i] + rot3x3[i][k]) / s

        return MQuaternion(scalar, axis[0], axis[1], axis[2])

    @classmethod
    def rotationTo(cls, fromv, tov):
        cdef MQuaternion v = MQuaternion()
        return v.c_rotationTo(fromv, tov) 
    
    cdef MQuaternion c_rotationTo(self, MVector3D fromv, MVector3D tov):
        cdef MVector3D v0 = fromv.normalized()
        cdef MVector3D v1 = tov.normalized()
        cdef DTYPE_FLOAT_t d = v0.c_dotProduct(v0, v1) + 1.0
        cdef MVector3D axis

        # if dest vector is close to the inverse of source vector, ANY axis of rotation is valid
        if is_almost_null(d):
            axis = v0.c_crossProduct(MVector3D(1.0, 0.0, 0.0), v0)
            if is_almost_null(axis.lengthSquared()):
                axis = v0.c_crossProduct(MVector3D(0.0, 1.0, 0.0), v0)
            axis.normalize()
            # same as MQuaternion.fromAxisAndAngle(axis, 180.0)
            return MQuaternion(0.0, axis.x(), axis.y(), axis.z()).normalized()

        d = sqrt(2.0 * d)
        axis = v0.c_crossProduct(v0, v1) / d
        return MQuaternion(d * 0.5, axis.x(), axis.y(), axis.z()).normalized()
        
    @classmethod
    def fromEulerAngles(cls, pitch, yaw, roll):
        cdef MQuaternion v = MQuaternion()
        return v.c_fromEulerAngles(pitch, yaw, roll) 
    
    cdef MQuaternion c_fromEulerAngles(self, DTYPE_FLOAT_t pitch, DTYPE_FLOAT_t yaw, DTYPE_FLOAT_t roll):
        pitch = radians(pitch)
        yaw = radians(yaw)
        roll = radians(roll)

        pitch *= 0.5
        yaw *= 0.5
        roll *= 0.5

        cdef DTYPE_FLOAT_t c1 = cos(yaw)
        cdef DTYPE_FLOAT_t s1 = sin(yaw)
        cdef DTYPE_FLOAT_t c2 = cos(roll)
        cdef DTYPE_FLOAT_t s2 = sin(roll)
        cdef DTYPE_FLOAT_t c3 = cos(pitch)
        cdef DTYPE_FLOAT_t s3 = sin(pitch)
        cdef DTYPE_FLOAT_t c1c2 = c1 * c2
        cdef DTYPE_FLOAT_t s1s2 = s1 * s2
        cdef DTYPE_FLOAT_t w = c1c2 * c3 + s1s2 * s3
        cdef DTYPE_FLOAT_t x = c1c2 * s3 + s1s2 * c3
        cdef DTYPE_FLOAT_t y = s1 * c2 * c3 - c1 * s2 * s3
        cdef DTYPE_FLOAT_t z = c1 * s2 * c3 - s1 * c2 * s3

        return MQuaternion(w, x, y, z)
    
    @classmethod
    def nlerp(cls, q1, q2, t):
        cdef MQuaternion v = MQuaternion()
        return v.c_nlerp(q1, q2, t) 
    
    cdef MQuaternion c_nlerp(self, MQuaternion q1, MQuaternion q2, DTYPE_FLOAT_t t):
        # Handle the easy cases first.
        if t <= 0.0:
            return q1
        elif t >= 1.0:
            return q2
            
        # Determine the angle between the two quaternions.
        cdef MQuaternion q2b = MQuaternion(q2.scalar(), q2.x(), q2.y(), q2.z())
        
        cdef DTYPE_FLOAT_t dot = q2b.c_dotProduct(q1, q2)
        if dot < 0.0:
            q2b = -q2b
        
        # Perform the linear interpolation.
        return MQuaternion(q1.data() * (1.0 - t) + q2b.data() * t).normalized()
    
    @classmethod
    def slerp(cls, q1, q2, t):
        cdef MQuaternion v = MQuaternion()
        return v.c_slerp(q1, q2, t) 
        # cfun = profile(v.c_slerp)
        # return cfun(q1, q2, t) 

    cdef MQuaternion c_slerp(self, MQuaternion q1, MQuaternion q2, DTYPE_FLOAT_t t):
        # Handle the easy cases first.
        if t <= 0.0:
            return q1
        elif t >= 1.0:
            return q2

        # Determine the angle between the two quaternions.
        cdef MQuaternion q2b = MQuaternion(q2.scalar(), q2.x(), q2.y(), q2.z())
        cdef DTYPE_FLOAT_t dot = q2b.c_dotProduct(q1, q2)
        # dfunc = profile(q2b.c_dotProduct)
        # cdef DTYPE_FLOAT_t dot = dfunc(q1, q2)
        
        if dot < 0.0:
            q2b = -q2b
            dot = -dot

        # Get the scale factors.  If they are too small,
        # then revert to simple linear interpolation.
        cdef DTYPE_FLOAT_t factor1 = 1.0 - t
        cdef DTYPE_FLOAT_t factor2 = t
        cdef DTYPE_FLOAT_t angle
        cdef DTYPE_FLOAT_t sinOfAngle

        if (1.0 - dot) > 0.0000001:
            angle = acos(max(0, min(1, dot)))
            sinOfAngle = sin(angle)
            if sinOfAngle > 0.0000001:
                factor1 = sin((1.0 - t) * angle) / sinOfAngle
                factor2 = sin(t * angle) / sinOfAngle

        # Construct the result quaternion.
        return MQuaternion(q1.data() * factor1 + q2b.data() * factor2)

    def data(self):
        return np.quaternion(self.__data[0], self.__data[1], self.__data[2], self.__data[3])

    def __lt__(self, other):
        return self.data().less(other.data())

    def __le__(self, other):
        return self.data().less_equal(other.data())

    def __eq__(self, other):
        return self.data().equal(other.data())

    def __ne__(self, other):
        return self.data().not_equal(other.data())

    def __gt__(self, other):
        return self.data().greater(other.data())

    def __ge__(self, other):
        return self.data().greater_equal(other.data())

    def __add__(self, other):
        if isinstance(other, MQuaternion):
            v = self.data() + other.data()
        else:
            v = self.data() + other
        return self.__class__(v.w, v.x, v.y, v.z)

    def __sub__(self, other):
        if isinstance(other, MQuaternion):
            v = self.data() - other.data()
        else:
            v = self.data() - other
        return self.__class__(v.w, v.x, v.y, v.z)

    def __mul__(self, other):
        if isinstance(other, MQuaternion):
            v = self.data() * other.data()
            return self.__class__(v)
        elif isinstance(other, MVector3D):
            v = self.toMatrix4x4() * other
            return v
        else:
            v = self.data() * other
            return self.__class__(v.w, v.x, v.y, v.z)

    def __truediv__(self, other):
        if isinstance(other, MQuaternion):
            v = self.data() / other.data()
        else:
            v = self.data() / other
        return self.__class__(v.w, v.x, v.y, v.z)

    def __floordiv__(self, other):
        if isinstance(other, MQuaternion):
            v = self.data() // other.data()
        else:
            v = self.data() // other
        return self.__class__(v.w, v.x, v.y, v.z)

    def __mod__(self, other):
        if isinstance(other, MQuaternion):
            v = self.data() % other.data()
        else:
            v = self.data() % other
        return self.__class__(v.w, v.x, v.y, v.z)

    # def __pow__(self, other):
    #     if isinstance(other, MQuaternion):
    #         v = self.data() ** other.data()
    #     else:
    #         v = self.data() ** other
    #     return self.__class__(v.w, v.x, v.y, v.z)

    def __lshift__(self, other):
        if isinstance(other, MQuaternion):
            v = self.data() << other.data()
        else:
            v = self.data() << other
        return self.__class__(v.w, v.x, v.y, v.z)

    def __rshift__(self, other):
        if isinstance(other, MQuaternion):
            v = self.data() >> other.data()
        else:
            v = self.data() >> other
        return self.__class__(v.w, v.x, v.y, v.z)

    def __and__(self, other):
        v = self.data() & other.data()
        return self.__class__(v.w, v.x, v.y, v.z)

    def __dataor__(self, other):
        v = self.data() ^ other.data()
        return self.__class__(v.w, v.x, v.y, v.z)

    def __or__(self, other):
        v = self.data() | other.data()
        return self.__class__(v.w, v.x, v.y, v.z)
    
    def __neg__(self):
        return self.__class__(-self.data().w, -self.data().x, -self.data().y, -self.data().z)

    def __pos__(self):
        return self.__class__(+self.data().w, +self.data().x, +self.data().y, +self.data().z)

    # def __invert__(self):
    #     return self.__class__(~self.data().w, ~self.data().x, ~self.data().y, ~self.data().z)
    
    def vector(self):
        return MVector3D(self.data().x, self.data().y, self.data().z)

    cpdef DTYPE_FLOAT_t x(self):
        return self.data().x

    cpdef DTYPE_FLOAT_t y(self):
        return self.data().y

    cpdef DTYPE_FLOAT_t z(self):
        return self.data().z
    
    cpdef DTYPE_FLOAT_t scalar(self):
        return self.data().w
    
    cpdef setX(self, DTYPE_FLOAT_t x):
        self.__data[1] = x

    cpdef setY(self, DTYPE_FLOAT_t y):
        self.__data[2] = y

    cpdef setZ(self, DTYPE_FLOAT_t z):
        self.__data[3] = z

    cpdef setScalar(self, DTYPE_FLOAT_t scalar):
        self.__data[0] = scalar

    def __reduce__(self):
        return (rebuild_MQuaternion, (self.scalar(), self.x(), self.y(), self.z()))

def rebuild_MQuaternion(scalar, x, y, z):
    return MQuaternion(scalar, x, y, z)


cdef class MMatrix4x4:

    def __init__(self, m11=1.0, m12=0, m13=0, m14=0, m21=0, m22=1, m23=0, m24=0, m31=0, m32=0, m33=1, m34=0, m41=0, m42=0, m43=0, m44=1):
        if isinstance(m11, float):
            self.__data = np.array([[m11, m12, m13, m14], [m21, m22, m23, m24], [m31, m32, m33, m34], [m41, m42, m43, m44]], dtype=np.float64)
        elif isinstance(m11, MMatrix4x4):
            # 行列クラスの場合
            self.__data = np.array([[m11.__data[0, 0], m11.__data[0, 1], m11.__data[0, 2], m11.__data[0, 3]], \
                                    [m11.__data[1, 0], m11.__data[1, 1], m11.__data[1, 2], m11.__data[1, 3]], \
                                    [m11.__data[2, 0], m11.__data[2, 1], m11.__data[2, 2], m11.__data[2, 3]], \
                                    [m11.__data[3, 0], m11.__data[3, 1], m11.__data[3, 2], m11.__data[3, 3]]], dtype=np.float64)
        elif isinstance(m11, np.ndarray):
            # 行列そのものの場合
            self.__data = np.array([[m11[0, 0], m11[0, 1], m11[0, 2], m11[0, 3]], [m11[1, 0], m11[1, 1], m11[1, 2], m11[1, 3]], \
                                    [m11[2, 0], m11[2, 1], m11[2, 2], m11[2, 3]], [m11[3, 0], m11[3, 1], m11[3, 2], m11[3, 3]]], dtype=np.float64)
        else:
            # べた値の場合
            self.__data = np.array([[m11, m12, m13, m14], [m21, m22, m23, m24], [m31, m32, m33, m34], [m41, m42, m43, m44]], dtype=np.float64)

    def copy(self):
        return MMatrix4x4(self.__data[0, 0], self.__data[0, 1], self.__data[0, 2], self.__data[0, 3], \
                          self.__data[1, 0], self.__data[1, 1], self.__data[1, 2], self.__data[1, 3], \
                          self.__data[2, 0], self.__data[2, 1], self.__data[2, 2], self.__data[2, 3], \
                          self.__data[3, 0], self.__data[3, 1], self.__data[3, 2], self.__data[3, 3])

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] data(self):
        return self.__data
    
    # 逆行列
    cpdef MMatrix4x4 inverted(self):
        v = np.linalg.inv(self.data())
        return MMatrix4x4(v)

    # 回転行列
    cpdef rotate(self, MQuaternion qq):
        cdef MMatrix4x4 qq_mat = qq.toMatrix4x4()
        self.__data = self.data().dot(qq_mat.data())

    # 平行移動行列
    cpdef translate(self, MVector3D vec3):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] d = self.data()
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] vec_mat = np.array([[vec3.x(), vec3.y(), vec3.z()], 
                                                                   [vec3.x(), vec3.y(), vec3.z()], 
                                                                   [vec3.x(), vec3.y(), vec3.z()], 
                                                                   [vec3.x(), vec3.y(), vec3.z()]], dtype=np.float64)
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] data_mat = d[:, :3] * vec_mat
        d[:, 3] += np.sum(data_mat, axis=1)
        self.__data = d

    # 縮尺行列
    cpdef scale(self, MVector3D vec3):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] vec_mat = np.array([[vec3.x(), vec3.y(), vec3.z()], 
                                                                   [vec3.x(), vec3.y(), vec3.z()], 
                                                                   [vec3.x(), vec3.y(), vec3.z()], 
                                                                   [vec3.x(), vec3.y(), vec3.z()]], dtype=np.float64)
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] d = self.data()
        d[:, :3] *= vec_mat
        self.__data = d
        
    # 単位行列
    cpdef setToIdentity(self):
        self.__data = np.eye(4, dtype=np.float64)
    
    cpdef lookAt(self, MVector3D eye, MVector3D center, MVector3D up):
        cdef MVector3D forward = center - eye
        if forward.is_almost_null():
            # ほぼ0の場合終了
            return
        
        forward.normalize()
        cdef MVector3D side = up.c_crossProduct(forward, up).normalized()
        cdef MVector3D upVector = forward.c_crossProduct(side, forward)

        cdef MMatrix4x4 m = MMatrix4x4()
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] d = m.data()
        d[0, :-1] = side.data()
        d[1, :-1] = upVector.data()
        d[2, :-1] = -forward.data()
        d[-1, -1] = 1.0
        m.__data = d

        self *= m
        self.translate(-eye)
    
    cpdef perspective(self, DTYPE_FLOAT_t verticalAngle, DTYPE_FLOAT_t aspectRatio, DTYPE_FLOAT_t nearPlane, DTYPE_FLOAT_t farPlane):
        if nearPlane == farPlane or aspectRatio == 0:
            return

        cdef DTYPE_FLOAT_t rad = radians(verticalAngle / 2)
        cdef DTYPE_FLOAT_t sine = sin(rad)

        if sine == 0:
            return
        
        cdef DTYPE_FLOAT_t cotan = cos(rad) / sine
        cdef DTYPE_FLOAT_t clip = farPlane - nearPlane

        cdef MMatrix4x4 m = MMatrix4x4()
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] d = m.data()
        d[0, 0] = cotan / aspectRatio
        d[1, 1] = cotan
        d[2, 2] = -(nearPlane + farPlane) / clip
        d[2, 3] = -(2 * nearPlane * farPlane) / clip
        d[3, 2] = -1
        m.__data = d

        self *= m
    
    cpdef MVector3D mapVector(self, MVector3D vector):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] vec_mat = np.array([vector.x(), vector.y(), vector.z()], dtype=np.float64)
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] d = self.data()
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] xyz = np.sum(vec_mat * d[:3, :3], axis=1)

        return MVector3D(xyz[0], xyz[1], xyz[2])
    
    cpdef MQuaternion toQuaternion(self):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] d = self.data()
        a = [[d[0, 0], d[0, 1], d[0, 2], d[0, 3]],
             [d[1, 0], d[1, 1], d[1, 2], d[1, 3]],
             [d[2, 0], d[2, 1], d[2, 2], d[2, 3]],
             [d[3, 0], d[3, 1], d[3, 2], d[3, 3]]]
        
        cdef MQuaternion q = MQuaternion()
        
        # I removed + 1
        cdef DTYPE_FLOAT_t trace = a[0][0] + a[1][1] + a[2][2]
        cdef DTYPE_FLOAT_t s

        # I changed M_EPSILON to 0
        if trace > 0:
            s = 0.5 / sqrt(trace + 1)
            q.setScalar(0.25 / s)
            q.setX((a[2][1] - a[1][2]) * s)
            q.setY((a[0][2] - a[2][0]) * s)
            q.setZ((a[1][0] - a[0][1]) * s)
        else:
            if a[0][0] > a[1][1] and a[0][0] > a[2][2]:
                s = 2 * sqrt(1 + a[0][0] - a[1][1] - a[2][2])
                q.setScalar((a[2][1] - a[1][2]) / s)
                q.setX(0.25 * s)
                q.setY((a[0][1] + a[1][0]) / s)
                q.setZ((a[0][2] + a[2][0]) / s)
            elif a[1][1] > a[2][2]:
                s = 2 * sqrt(1 + a[1][1] - a[0][0] - a[2][2])
                q.setScalar((a[0][2] - a[2][0]) / s)
                q.setX((a[0][1] + a[1][0]) / s)
                q.setY(0.25 * s)
                q.setZ((a[1][2] + a[2][1]) / s)
            else:
                s = 2 * sqrt(1 + a[2][2] - a[0][0] - a[1][1])
                q.setScalar((a[1][0] - a[0][1]) / s)
                q.setX((a[0][2] + a[2][0]) / s)
                q.setY((a[1][2] + a[2][1]) / s)
                q.setZ(0.25 * s)

        return q

    def __str__(self):
        return "MMatrix4x4({0})".format(self.data())

    def __lt__(self, other):
        return np.all(np.less(self.data(), other.data()))

    def __le__(self, other):
        return np.all(np.less_equal(self.data(), other.data()))

    def __eq__(self, other):
        return np.all(np.equal(self.data(), other.data()))

    def __ne__(self, other):
        return np.any(np.not_equal(self.data(), other.data()))

    def __gt__(self, other):
        return np.all(np.greater(self.data(), other.data()))

    def __ge__(self, other):
        return np.all(np.greater_equal(self.data(), other.data()))

    def __add__(self, other):
        if isinstance(other, MMatrix4x4):
            v = self.add_MMatrix4x4(other)
        elif isinstance(other, np.int):
            v = self.add_int(other)
        else:
            v = self.add_float(other)
        return self.__class__(v)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] add_MMatrix4x4(self, MMatrix4x4 other):
        return self.data() + other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] add_float(self, DTYPE_FLOAT_t other):
        return self.data() + other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] add_int(self, DTYPE_INT_t other):
        return self.data() + other

    def __sub__(self, other):
        if isinstance(other, MMatrix4x4):
            v = self.sub_MMatrix4x4(other)
        elif isinstance(other, np.int):
            v = self.sub_int(other)
        else:
            v = self.data() - other
        return self.__class__(v)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] sub_MMatrix4x4(self, MMatrix4x4 other):
        return self.data() - other.data()

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] sub_float(self, DTYPE_FLOAT_t other):
        return self.data() - other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] sub_int(self, DTYPE_INT_t other):
        return self.data() - other

    # *演算子
    def __mul__(self, other):
        if isinstance(other, MVector3D):
            return self.mul_MVector3D(other)
        elif isinstance(other, MVector4D):
            return self.mul_MVector4D(other)
        elif isinstance(other, MMatrix4x4):
            v = self.mul_MMatrix4x4(other)
        elif isinstance(other, np.int):
            v = self.mul_int(other)
        elif isinstance(other, np.float):
            v = self.mul_float(other)
        else:       
            v = self.data() * other

        return MMatrix4x4(v)
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] mul_MMatrix4x4(self, MMatrix4x4 other):
        logger.debug("mul_MMatrix4x4")
        return np.dot(self.data(), other.data())

    cpdef MVector3D mul_MVector3D(self, MVector3D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] vec_mat = np.array([[other.x(), other.y(), other.z()], 
                                                                   [other.x(), other.y(), other.z()], 
                                                                   [other.x(), other.y(), other.z()], 
                                                                   [other.x(), other.y(), other.z()]], dtype=np.float64)
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] d = self.data()
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] data_sum = np.sum(vec_mat * d[:, :3], axis=1) + d[:, 3]

        cdef DTYPE_FLOAT_t x = data_sum[0]
        cdef DTYPE_FLOAT_t y = data_sum[1]
        cdef DTYPE_FLOAT_t z = data_sum[2]
        cdef DTYPE_FLOAT_t w = data_sum[3]

        if w == 1.0:
            return MVector3D(x, y, z)
        elif w == 0.0:
            return MVector3D()
        else:
            return MVector3D(x / w, y / w, z / w)

    cpdef MVector4D mul_MVector4D(self, MVector4D other):
        logger.debug("mul_MVector4D")
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] vec_mat = np.array([[other.x(), other.y(), other.z(), other.w()], 
                                                                   [other.x(), other.y(), other.z(), other.w()], 
                                                                   [other.x(), other.y(), other.z(), other.w()], 
                                                                   [other.x(), other.y(), other.z(), other.w()]], dtype=np.float64)
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] d = self.data()
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] data_sum = np.sum(vec_mat * d, axis=1)

        cdef DTYPE_FLOAT_t x = data_sum[0]
        cdef DTYPE_FLOAT_t y = data_sum[1]
        cdef DTYPE_FLOAT_t z = data_sum[2]
        cdef DTYPE_FLOAT_t w = data_sum[3]

        return MVector4D(x, y, z, w)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] mul_float(self, DTYPE_FLOAT_t other):
        return self.data() * other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] mul_int(self, DTYPE_INT_t other):
        return self.data() * other
        
    def __iadd__(self, other):
        return self.iadd_MMatrix4x4(other)
    
    cpdef MMatrix4x4 iadd_MMatrix4x4(self, MMatrix4x4 other):
        self.__data = self.data() + other.data().T
        return self

    def __isub__(self, other):
        return self.isub_MMatrix4x4(other)
    
    cpdef MMatrix4x4 isub_MMatrix4x4(self, MMatrix4x4 other):
        self.__data = self.data() - other.data().T
        return self

    def __imul__(self, other):
        # cfun = profile(self.imul_MMatrix4x4)
        # return cfun(other)
        return self.imul_MMatrix4x4(other)
    
    cpdef MMatrix4x4 imul_MMatrix4x4(self, MMatrix4x4 other):
        self.__data = np.dot(self.data(), other.data())
        return self

    def __itruediv__(self, other):
        return self.itruediv_MMatrix4x4(other)
    
    cpdef MMatrix4x4 itruediv_MMatrix4x4(self, MMatrix4x4 other):
        self.__data = self.data() / other.data().T
        return self

cpdef is_almost_null(v):
    return abs(v) < 0.0000001


cpdef DTYPE_FLOAT_t get_effective_value(DTYPE_FLOAT_t v):
    if math.isnan(v):
        return 0
    
    if math.isinf(v):
        return 0
    
    return v


cpdef DTYPE_FLOAT_t get_almost_zero_value(DTYPE_FLOAT_t v):
    if get_effective_value(v) == 0:
        return 0
        
    if is_almost_null(v):
        return 0

    return v


