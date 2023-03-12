# -*- coding: utf-8 -*-
# 
# cython: boundscheck=False
# cython: wraparound=False
#
import quaternion # noqa
import numpy as np
cimport numpy as np
cimport cython
from libc.math cimport sin, cos, acos, atan2, asin, pi, sqrt
from math import degrees, radians, isnan, isinf

from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


cdef class MRect:

    def __init__(self, x=0, y=0, width=0, height=0):
        self.__x = x
        self.__y = y
        self.__width = width
        self.__height = height

    cpdef DTYPE_FLOAT_t x(self):
        return self.__x

    cpdef DTYPE_FLOAT_t y(self):
        return self.__y

    cpdef DTYPE_FLOAT_t width(self):
        return self.__width

    cpdef DTYPE_FLOAT_t height(self):
        return self.__height

    def __str__(self):
        return "MRect({0}, {1}, {2}, {3})".format(self.__x, self.__y, self.__width, self.__height)


cdef class MVector2D:

    def __init__(self, x=0.0, y=0.0):
        if isinstance(x, float):
            # 実数の場合
            self.__data = np.array([x, y], dtype=np.float64)
        elif isinstance(x, MVector2D):
            # クラスの場合
            self.__data = np.array([x.x(), x.y()], dtype=np.float64)
        elif isinstance(x, np.ndarray):
            # arrayそのものの場合
            self.__data = np.array([x[0], x[1]], dtype=np.float64)
        else:
            self.__data = np.array([x, y], dtype=np.float64)

    cpdef double length(self):
        return float(np.linalg.norm(self.data(), ord=2))

    cpdef double lengthSquared(self):
        return float(np.linalg.norm(self.data(), ord=2)**2)

    cpdef MVector2D normalized(self):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] l2 = np.linalg.norm(self.data(), ord=2, axis=-1, keepdims=True)
        l2[l2 == 0] = 1
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] normv = self.data() / l2
        return MVector2D(normv[0], normv[1])

    cpdef normalize(self):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] l2 = np.linalg.norm(self.data(), ord=2, axis=-1, keepdims=True)
        l2[l2 == 0] = 1
        self.__data /= l2
    
    cpdef effective(self):
        self.__data[np.isnan(self.data())] = 0
        self.__data[np.isinf(self.data())] = 0

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
        if isinstance(other, np.float64):
            v = self.add_float(other)
        elif isinstance(other, MVector2D):
            v = self.add_MVector2D(other)
        elif isinstance(other, np.int32):
            v = self.add_int(other)
        else:
            v = self.data() + other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_MVector2D(self, MVector2D other):
        return self.__data + other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_float(self, DTYPE_FLOAT_t other):
        return self.__data + other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_int(self, DTYPE_INT_t other):
        return self.__data + other

    def __sub__(self, other):
        if isinstance(other, np.float64):
            v = self.sub_float(other)
        elif isinstance(other, MVector2D):
            v = self.sub_MVector2D(other)
        elif isinstance(other, np.int32):
            v = self.sub_int(other)
        else:
            v = self.data() - other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_MVector2D(self, MVector2D other):
        return self.__data - other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_float(self, DTYPE_FLOAT_t other):
        return self.__data - other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_int(self, DTYPE_INT_t other):
        return self.__data - other

    def __mul__(self, other):
        if isinstance(other, np.float64):
            v = self.mul_float(other)
        elif isinstance(other, MVector2D):
            v = self.mul_MVector2D(other)
        elif isinstance(other, np.int32):
            v = self.mul_int(other)
        else:
            v = self.data() * other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_MVector2D(self, MVector2D other):
        return self.__data * other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_float(self, DTYPE_FLOAT_t other):
        return self.__data * other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_int(self, DTYPE_INT_t other):
        return self.__data * other

    def __truediv__(self, other):
        if isinstance(other, np.float64):
            v = self.truediv_float(other)
        elif isinstance(other, MVector2D):
            v = self.truediv_MVector2D(other)
        elif isinstance(other, np.int32):
            v = self.truediv_int(other)
        else:
            v = self.data() / other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_MVector2D(self, MVector2D other):
        return self.__data / other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_float(self, DTYPE_FLOAT_t other):
        return self.__data / other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_int(self, DTYPE_INT_t other):
        return self.__data / other

    def __floordiv__(self, other):
        if isinstance(other, np.float64):
            v = self.floordiv_float(other)
        elif isinstance(other, MVector2D):
            v = self.floordiv_MVector2D(other)
        elif isinstance(other, np.int32):
            v = self.floordiv_int(other)
        else:
            v = self.data() // other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_MVector2D(self, MVector2D other):
        return self.__data // other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_float(self, DTYPE_FLOAT_t other):
        return self.__data // other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_int(self, DTYPE_INT_t other):
        return self.__data // other

    def __mod__(self, other):
        if isinstance(other, np.float64):
            v = self.mod_float(other)
        elif isinstance(other, MVector2D):
            v = self.mod_MVector2D(other)
        elif isinstance(other, np.int32):
            v = self.mod_int(other)
        else:
            v = self.data() % other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_MVector2D(self, MVector2D other):
        return self.__data % other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_float(self, DTYPE_FLOAT_t other):
        return self.__data % other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_int(self, DTYPE_INT_t other):
        return self.__data % other

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

    cpdef DTYPE_FLOAT_t x(self):
        return self.__data[0]

    cpdef DTYPE_FLOAT_t y(self):
        return self.__data[1]
    
    cpdef setX(self, x):
        self.__data[0] = x

    cpdef setY(self, y):
        self.__data[1] = y

    cpdef MVector2D copy(self):
        return MVector2D(self.x(), self.y())

    def to_log(self):
        return "x: {0}, y: {1}".format(round(self.x(), 5), round(self.y(), 5))


class MPoint:

    def __init__(self, p: MVector3D):
        self.point = p

    def get_point(self, f: float):
        return self.point * f


class MLine:

    def __init__(self, p: MPoint, v: MVector3D):
        self.point = p
        self.vector_start = v
        self.vector_real = p.point - v
        self.vector = (p.point - v).normalized()

    def get_point(self, f: float):
        return self.vector_start + (self.vector_real * f)


class MSegment(MLine):

    def __init__(self, sv: MVector3D, ev: MVector3D):
        super().__init__(MPoint((sv + ev) / 2), sv)
        self.vector_end = ev
        self.vector_real = ev - sv
        self.vector = self.vector_real.normalized()

    def get_point(self, f: float):
        return self.vector_start + (self.vector_real * f)


class MSphere:

    def __init__(self, p: MPoint, r=1.0):
        self.point = p
        self.radius = r


class MCapsule:

    def __init__(self, s: MSegment, r=0.0):
        self.segment = s
        self.radius = r


cdef class MVector3D:

    def __init__(self, x=0.0, y=0.0, z=0.0):
        if isinstance(x, float):
            # 実数の場合
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

    cpdef double length(self):
        return float(np.linalg.norm(self.data(), ord=2))

    cpdef double lengthSquared(self):
        return float(np.linalg.norm(self.data(), ord=2)**2)

    cpdef MVector3D round(self, decimals):
        return MVector3D(np.round(self.data(), decimals=decimals))

    cpdef MVector3D normalized(self):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] l2 = np.linalg.norm(self.data(), ord=2, axis=-1, keepdims=True)
        l2[l2 == 0] = 1
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] normv = self.data() / l2
        return MVector3D(normv[0], normv[1], normv[2])

    cpdef normalize(self):
        self.effective()
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] l2 = np.linalg.norm(self.data(), ord=2, axis=-1, keepdims=True)
        l2[l2 == 0] = 1
        self.__data /= l2
    
    cpdef double distanceToPoint(self, MVector3D v):
        return MVector3D(self.data() - v.data()).length()
    
    cpdef MVector3D project(self, MMatrix4x4 modelView, MMatrix4x4 projection, MRect viewport):
        cdef MVector4D tmp = MVector4D(self.x(), self.y(), self.z(), 1)
        tmp = projection * modelView * tmp
        if is_almost_null(tmp.w()):
            tmp.setW(1)

        tmp /= tmp.w()
        tmp = tmp * 0.5 + MVector4D(0.5, 0.5, 0.5, 0.5)
        tmp.setX(tmp.x() * viewport.width() + viewport.x())
        tmp.setY(tmp.y() * viewport.height() + viewport.y())

        tmp.effective()
        return tmp.toVector3D()

    cpdef MVector3D unproject(self, MMatrix4x4 modelView, MMatrix4x4 projection, MRect viewport):
        cdef MMatrix4x4 inverse = (projection * modelView).inverted()

        cdef MVector4D tmp = MVector4D(self.x(), self.y(), self.z(), 1)
        tmp.setX((tmp.x() - viewport.x()) / viewport.width())
        tmp.setY((tmp.y() - viewport.y()) / viewport.height())
        tmp = tmp * 2 - MVector4D(1, 1, 1, 1)
        tmp.effective()

        cdef MVector4D obj = inverse * tmp
        if is_almost_null(obj.w()):
            obj.setW(1)

        obj /= obj.w()
        obj.effective()
        
        return obj.toVector3D()
        
    cpdef MVector4D toVector4D(self):
        return MVector4D(self.__data[0], self.__data[1], self.__data[2], 0)

    cpdef bint is_almost_null(self):
        return (is_almost_null(self.__data[0]) and is_almost_null(self.__data[1]) and is_almost_null(self.__data[2]))
    
    cpdef MVector3D effective(self):
        self.__data[np.isnan(self.data())] = 0
        self.__data[np.isinf(self.data())] = 0

        return self
                
    cpdef MVector3D abs(self):
        self.setX(abs(get_effective_value(self.x())))
        self.setY(abs(get_effective_value(self.y())))
        self.setZ(abs(get_effective_value(self.z())))

        return self
                
    cpdef MVector3D one(self):
        self.effective()
        self.setX(1 if is_almost_null(self.x()) else self.x())
        self.setY(1 if is_almost_null(self.y()) else self.y())
        self.setZ(1 if is_almost_null(self.z()) else self.z())

        return self
    
    cpdef MVector3D non_zero(self):
        self.effective()
        self.setX(0.0000001 if is_almost_null(self.x()) else self.x())
        self.setY(0.0000001 if is_almost_null(self.y()) else self.y())
        self.setZ(0.0000001 if is_almost_null(self.z()) else self.z())

        return self
    
    cpdef bint isnan(self):
        self.__data = self.data().astype(np.float64)
        return np.isnan(self.data()).any()

    @classmethod
    def crossProduct(cls, v1, v2):
        return crossProduct_MVector3D(v1, v2)

    @classmethod
    def dotProduct(cls, v1, v2):
        return dotProduct_MVector3D(v1, v2)
        
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] data(self):
        return self.__data

    def to_log(self):
        return "x: {0}, y: {1} z: {2}".format(round(self.__data[0], 5), round(self.__data[1], 5), round(self.__data[2], 5))

    def to_key(self, threshold=0.1):
        # return (round(self.__data[0], 1), round(self.__data[1], 1), round(self.__data[2], 1))
        # return (round(self.__data[0] * 5) / 5, round(self.__data[1] * 5) / 5, round(self.__data[2] * 5) / 5)
        return (round(self.__data[0] / threshold), round(self.__data[1] / threshold), round(self.__data[2] / threshold))

    def __str__(self):
        return "MVector3D({0}, {1}, {2})".format(self.__data[0], self.__data[1], self.__data[2])

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
        if isinstance(other, np.float64):
            v = self.add_float(other)
        elif isinstance(other, MVector3D):
            v = self.add_MVector3D(other)
        elif isinstance(other, np.int32):
            v = self.add_int(other)
        else:
            v = self.data() + other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_MVector3D(self, MVector3D other):
        return self.__data + other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_float(self, DTYPE_FLOAT_t other):
        return self.__data + other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_int(self, DTYPE_INT_t other):
        return self.__data + other

    def __sub__(self, other):
        if isinstance(other, np.float64):
            v = self.sub_float(other)
        elif isinstance(other, MVector3D):
            v = self.sub_MVector3D(other)
        elif isinstance(other, np.int32):
            v = self.sub_int(other)
        else:
            v = self.data() - other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_MVector3D(self, MVector3D other):
        return self.__data - other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_float(self, DTYPE_FLOAT_t other):
        return self.__data - other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_int(self, DTYPE_INT_t other):
        return self.__data - other

    def __mul__(self, other):
        if isinstance(other, np.float64):
            v = self.mul_float(other)
        elif isinstance(other, MVector3D):
            v = self.mul_MVector3D(other)
        elif isinstance(other, np.int32):
            v = self.mul_int(other)
        else:
            v = self.data() * other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_MVector3D(self, MVector3D other):
        return self.__data * other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_float(self, DTYPE_FLOAT_t other):
        return self.__data * other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_int(self, DTYPE_INT_t other):
        return self.__data * other

    def __truediv__(self, other):
        if isinstance(other, np.float64):
            v = self.truediv_float(other)
        elif isinstance(other, MVector3D):
            v = self.truediv_MVector3D(other)
        elif isinstance(other, np.int32):
            v = self.truediv_int(other)
        else:
            v = self.data() / other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_MVector3D(self, MVector3D other):
        return self.__data / other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_float(self, DTYPE_FLOAT_t other):
        return self.__data / other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_int(self, DTYPE_INT_t other):
        return self.__data / other

    def __floordiv__(self, other):
        if isinstance(other, np.float64):
            v = self.floordiv_float(other)
        elif isinstance(other, MVector3D):
            v = self.floordiv_MVector3D(other)
        elif isinstance(other, np.int32):
            v = self.floordiv_int(other)
        else:
            v = self.data() // other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_MVector3D(self, MVector3D other):
        return self.__data // other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_float(self, DTYPE_FLOAT_t other):
        return self.__data // other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_int(self, DTYPE_INT_t other):
        return self.__data // other

    def __mod__(self, other):
        if isinstance(other, np.float64):
            v = self.mod_float(other)
        elif isinstance(other, MVector3D):
            v = self.mod_MVector3D(other)
        elif isinstance(other, np.int32):
            v = self.mod_int(other)
        else:
            v = self.data() % other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_MVector3D(self, MVector3D other):
        return self.__data % other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_float(self, DTYPE_FLOAT_t other):
        return self.__data % other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_int(self, DTYPE_INT_t other):
        return self.__data % other

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
    
    cpdef setX(self, x):
        self.__data[0] = x

    cpdef setY(self, y):
        self.__data[1] = y

    cpdef setZ(self, z):
        self.__data[2] = z


cdef MVector3D crossProduct_MVector3D(MVector3D v1, MVector3D v2):
    cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] crossv = np.cross(v1.data(), v2.data())
    return MVector3D(crossv[0], crossv[1], crossv[2])


cdef double dotProduct_MVector3D(MVector3D v1, MVector3D v2):
    return np.dot(v1.data(), v2.data())


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
        return MVector4D(float(self.x()), float(self.y()), float(self.z()), float(self.w()))
    
    cpdef double length(self):
        return np.linalg.norm(self.data(), ord=2)

    cpdef double lengthSquared(self):
        return np.linalg.norm(self.data(), ord=2)**2

    cpdef MVector4D normalized(self):
        l2 = np.linalg.norm(self.data(), ord=2, axis=-1, keepdims=True)
        l2[l2 == 0] = 1
        normv = self.data() / l2
        return MVector4D(normv[0], normv[1], normv[2], normv[3])

    cpdef normalize(self):
        l2 = np.linalg.norm(self.data(), ord=2, axis=-1, keepdims=True)
        l2[l2 == 0] = 1
        normv = self.data() / l2
        self.__data = normv

    cpdef MVector3D toVector3D(self):
        return MVector3D(self.__data[0], self.__data[1], self.__data[2])

    cpdef bint is_almost_null(self):
        return (is_almost_null(self.__data[0]) and is_almost_null(self.__data[1]) and is_almost_null(self.__data[2]) and is_almost_null(self.__data[3]))
                   
    cpdef effective(self):
        self.__data[np.isnan(self.data())] = 0
        self.__data[np.isinf(self.data())] = 0
                                
    @classmethod
    def dotProduct(cls, v1, v2):
        return dotProduct_MVector4D(v1, v2)
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] data(self):
        return self.__data

    def __str__(self):
        return "MVector4D({0}, {1}, {2}, {3})".format(self.__data[0], self.__data[1], self.__data[2], self.__data[3])

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
        if isinstance(other, np.float64):
            v = self.add_float(other)
        elif isinstance(other, MVector4D):
            v = self.add_MVector4D(other)
        elif isinstance(other, np.int32):
            v = self.add_int(other)
        else:
            v = self.data() + other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_MVector4D(self, MVector4D other):
        return self.__data + other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_float(self, DTYPE_FLOAT_t other):
        return self.__data + other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] add_int(self, DTYPE_INT_t other):
        return self.__data + other

    def __sub__(self, other):
        if isinstance(other, np.float64):
            v = self.sub_float(other)
        elif isinstance(other, MVector4D):
            v = self.sub_MVector4D(other)
        elif isinstance(other, np.int32):
            v = self.sub_int(other)
        else:
            v = self.data() - other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_MVector4D(self, MVector4D other):
        return self.__data - other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_float(self, DTYPE_FLOAT_t other):
        return self.__data - other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] sub_int(self, DTYPE_INT_t other):
        return self.__data - other

    def __mul__(self, other):
        if isinstance(other, np.float64):
            v = self.mul_float(other)
        elif isinstance(other, MVector4D):
            v = self.mul_MVector4D(other)
        elif isinstance(other, np.int32):
            v = self.mul_int(other)
        else:
            v = self.data() * other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_MVector4D(self, MVector4D other):
        return self.__data * other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_float(self, DTYPE_FLOAT_t other):
        return self.__data * other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mul_int(self, DTYPE_INT_t other):
        return self.__data * other

    def __truediv__(self, other):
        if isinstance(other, np.float64):
            v = self.truediv_float(other)
        elif isinstance(other, MVector4D):
            v = self.truediv_MVector4D(other)
        elif isinstance(other, np.int32):
            v = self.truediv_int(other)
        else:
            v = self.data() / other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_MVector4D(self, MVector4D other):
        return self.__data / other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_float(self, DTYPE_FLOAT_t other):
        return self.__data / other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] truediv_int(self, DTYPE_INT_t other):
        return self.__data / other

    def __floordiv__(self, other):
        if isinstance(other, np.float64):
            v = self.floordiv_float(other)
        elif isinstance(other, MVector4D):
            v = self.floordiv_MVector4D(other)
        elif isinstance(other, np.int32):
            v = self.floordiv_int(other)
        else:
            v = self.data() // other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_MVector4D(self, MVector4D other):
        return self.__data // other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_float(self, DTYPE_FLOAT_t other):
        return self.__data // other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] floordiv_int(self, DTYPE_INT_t other):
        return self.__data // other

    def __mod__(self, other):
        if isinstance(other, np.float64):
            v = self.mod_float(other)
        elif isinstance(other, MVector4D):
            v = self.mod_MVector4D(other)
        elif isinstance(other, np.int32):
            v = self.mod_int(other)
        else:
            v = self.data() % other
        v2 = self.__class__(v)
        v2.effective()
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_MVector4D(self, MVector4D other):
        return self.__data % other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_float(self, DTYPE_FLOAT_t other):
        return self.__data % other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=1] mod_int(self, DTYPE_INT_t other):
        return self.__data % other

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

    cpdef DTYPE_FLOAT_t x(self):
        return self.__data[0]

    cpdef DTYPE_FLOAT_t y(self):
        return self.__data[1]

    cpdef DTYPE_FLOAT_t z(self):
        return self.__data[2]
    
    cpdef DTYPE_FLOAT_t w(self):
        return self.__data[3]
    
    cpdef setX(self, x):
        self.__data[0] = x

    cpdef setY(self, y):
        self.__data[1] = y

    cpdef setZ(self, z):
        self.__data[2] = z

    cpdef setW(self, w):
        self.__data[3] = w


cdef double dotProduct_MVector4D(MVector4D v1, MVector4D v2):
    return np.dot(v1.data(), v2.data())


cdef class MQuaternion:

    def __init__(self, w=1.0, x=0.0, y=0.0, z=0.0):
        if isinstance(w, float):
            self.__data = np.array([w, x, y, z], dtype=np.float64)
        elif isinstance(w, MQuaternion):
            # クラスの場合
            self.__data = np.array([w.data().components.w, w.data().components.x, w.data().components.y, w.data().components.z], dtype=np.float64)
        elif isinstance(w, np.quaternion):
            # quaternionの場合
            self.__data = w.components
        elif isinstance(w, np.ndarray):
            # arrayそのものの場合
            self.__data = np.array([w[0], w[1], w[2], w[3]], dtype=np.float64)
        else:
            self.__data = np.array([w, x, y, z], dtype=np.float64)

    cpdef MQuaternion copy(self):
        return MQuaternion(float(self.scalar()), float(self.x()), float(self.y()), float(self.z()))
    
    def __str__(self):
        return "MQuaternion({0}, {1}, {2}, {3})".format(self.scalar(), self.x(), self.y(), self.z())

    cpdef MQuaternion inverted(self):
        v = self.data().inverse()
        return self.__class__(v.w, v.x, v.y, v.z)

    cpdef double length(self):
        return self.data().abs()

    cpdef double lengthSquared(self):
        return self.data().abs()**2

    cpdef MQuaternion normalized(self):
        self.effective()
        v = self.data().normalized()
        return MQuaternion(v.w, v.x, v.y, v.z)

    cpdef normalize(self):
        self.__data = self.data().normalized().components

    cpdef effective(self):
        self.data().components[np.isnan(self.data().components)] = 0
        self.data().components[np.isinf(self.data().components)] = 0
        # # Scalarは1がデフォルトとなる【不要】
        # self.setScalar(1 if self.scalar() == 0 else self.scalar())
        if np.isclose(self.data().components, 0).all():
            # すべてが0の場合、scalarだけ1に設定する
            self.setScalar(1)

    cpdef MMatrix4x4 toMatrix4x4(self):
        cdef MMatrix4x4 mat = MMatrix4x4()
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] m = mat.data()

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

        return mat
    
    cpdef MVector4D toVector4D(self):
        return MVector4D(self.data().x, self.data().y, self.data().z, self.data().w)

    cpdef MVector3D toEulerAngles4MMD(self):
        # MMDの表記に合わせたオイラー角
        cdef MVector3D euler = self.toEulerAngles()

        return MVector3D(euler.x(), -euler.y(), -euler.z())

    cpdef MVector3D separateEulerAngles(self):
        # ZXYの回転順序でオイラー角度を分割する
        # https://programming-surgeon.com/script/euler-python-script/
        cdef MMatrix4x4 mat = self.normalized().toMatrix4x4()
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] m = mat.data()

        cdef float z_radian = atan2(-m[0, 1], m[0, 0])
        cdef float x_radian = atan2(m[2, 1] * cos(z_radian), m[1, 1])
        cdef float y_radian = atan2(-m[2, 0], m[2, 2])

        return MVector3D(degrees(x_radian), degrees(y_radian), degrees(z_radian))

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
    cpdef double toDegree(self):
        return degrees(2 * acos(min(1, max(-1, self.scalar()))))

    # 軸による符号付き角度に変換
    cpdef double toDegreeSign(self, MVector3D local_axis):
        cdef double deg =  self.toDegree() * np.sign(MVector3D.dotProduct(self.vector(), local_axis)) * np.sign(self.scalar())

        if abs(deg) > 180:
            # 180度を超してる場合、フリップなので、除去
            return (abs(deg) - 180) * np.sign(deg)
            
        return deg

    # 自分ともうひとつの値vとのtheta（変位量）を返す
    cpdef double calcTheata(self, MQuaternion v):
        return (1 - MQuaternion.dotProduct(self.normalized(), v.normalized()))
        # cdef double dot = MQuaternion.dotProduct(self.normalized(), v.normalized())
        # cdef double angle = acos(min(1, max(-1, dot)))
        # cdef double sinOfAngle = sin(angle)
        # return sinOfAngle

    @classmethod
    def dotProduct(cls, v1, v2):
        return dotProduct_MQuaternion(v1, v2)
    
    @classmethod
    def fromAxisAndAngle(cls, vec3, angle):
        return fromAxisAndAngle(vec3, angle)

    @classmethod
    def fromAxisAndQuaternion(cls, vec3, qq):
        return fromAxisAndQuaternion(vec3, qq)

    @classmethod
    def fromDirection(cls, direction, up):
        return fromDirection(direction, up)
    
    @classmethod
    def fromAxes(cls, xAxis, yAxis, zAxis):
        return fromAxes(xAxis, yAxis, zAxis)
        
    @classmethod
    def fromRotationMatrix(cls, rot3x3):
        return fromRotationMatrix(rot3x3)

    @classmethod
    def rotationTo(cls, fromv, tov):
        return rotationTo(fromv, tov)

    @classmethod
    def fromEulerAngles(cls, pitch, yaw, roll):
        return fromEulerAngles(pitch, yaw, roll)

    @classmethod
    def nlerp(cls, q1, q2, t):
        return nlerp(q1, q2, t)

    @classmethod
    def slerp(cls, q1, q2, t):
        return slerp(q1, q2, t)

    cpdef double x(self):
        return self.data().x

    cpdef double y(self):
        return self.data().y

    cpdef double z(self):
        return self.data().z

    cpdef double scalar(self):
        return self.data().w

    cpdef MVector3D vector(self):
        return MVector3D(self.data().x, self.data().y, self.data().z)

    cpdef setX(self, x):
        self.__data[1] = x

    cpdef setY(self, y):
        self.__data[2] = y

    cpdef setZ(self, z):
        self.__data[3] = z

    cpdef setScalar(self, w):
        self.__data[0] = w
        
    cpdef data(self):
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

    def __invert__(self):
        return self.__class__(~self.data().w, ~self.data().x, ~self.data().y, ~self.data().z)


cdef double dotProduct_MQuaternion(MQuaternion v1, MQuaternion v2):
    return np.sum(v1.data().components * v2.data().components)

cdef MQuaternion fromAxisAndAngle(MVector3D vec3, double angle):
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

cdef MQuaternion fromAxisAndQuaternion(MVector3D vec3, MQuaternion qq):
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

    # logger.test("scalar: %s, a: %s, c: %s, degree: %s", qq.scalar(), a, c, degrees(2 * math.acos(min(1, max(-1, qq.scalar())))))

    return MQuaternion(c, x * s, y * s, z * s).normalized()

cdef MQuaternion fromDirection(MVector3D direction, MVector3D up):
    if direction.is_almost_null():
        return MQuaternion()

    cdef MVector3D zAxis = direction.normalized()
    cdef MVector3D xAxis = crossProduct_MVector3D(up, zAxis)
    if (is_almost_null(xAxis.lengthSquared())):
        # collinear or invalid up vector derive shortest arc to new direction
        return rotationTo(MVector3D(0.0, 0.0, 1.0), zAxis)
    
    xAxis.normalize()
    cdef MVector3D yAxis = crossProduct_MVector3D(zAxis, xAxis)
    return MQuaternion.fromAxes(xAxis, yAxis, zAxis)

cdef MQuaternion fromAxes(MVector3D xAxis, MVector3D yAxis, MVector3D zAxis):
    return fromRotationMatrix(np.array([[xAxis.x(), yAxis.x(), zAxis.x()], [xAxis.y(), yAxis.y(), zAxis.y()], [xAxis.z(), yAxis.z(), zAxis.z()]], dtype=np.float64))

cdef MQuaternion fromRotationMatrix(np.ndarray[DTYPE_FLOAT_t, ndim=2] rot3x3):
    cdef DTYPE_FLOAT_t scalar = 0
    cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] axis = np.zeros(3)

    cdef DTYPE_FLOAT_t trace = rot3x3[0,0] + rot3x3[1,1] + rot3x3[2,2]
    cdef DTYPE_FLOAT_t s = 0
    cdef np.ndarray[DTYPE_INT8_t, ndim=1] s_next
    cdef int i = 0
    cdef int j = 0
    cdef int k = 0

    if trace > 0.00000001:
        s = 2.0 * sqrt(trace + 1.0)
        scalar = 0.25 * s
        axis[0] = (rot3x3[2,1] - rot3x3[1,2]) / s
        axis[1] = (rot3x3[0,2] - rot3x3[2,0]) / s
        axis[2] = (rot3x3[1,0] - rot3x3[0,1]) / s
    else:
        s_next = np.array([1, 2, 0], dtype=np.int8)
        i = 0
        if rot3x3[1,1] > rot3x3[0,0]:
            i = 1
        if rot3x3[2,2] > rot3x3[i,i]:
            i = 2

        j = s_next[i]
        k = s_next[j]

        s = 2.0 * sqrt(rot3x3[i,i] - rot3x3[j,j] - rot3x3[k,k] + 1.0)
        axis[i] = 0.25 * s

        scalar = (rot3x3[k,j] - rot3x3[j,k]) / s
        axis[j] = (rot3x3[j,i] + rot3x3[i,j]) / s
        axis[k] = (rot3x3[k,i] + rot3x3[i,k]) / s

    return MQuaternion(scalar, axis[0], axis[1], axis[2])

cdef MQuaternion rotationTo(MVector3D fromv, MVector3D tov):
    cdef MVector3D v0 = fromv.normalized()
    cdef MVector3D v1 = tov.normalized()
    cdef double d = MVector3D.dotProduct(v0, v1) + 1.0
    cdef MVector3D axis

    # if dest vector is close to the inverse of source vector, ANY axis of rotation is valid
    if is_almost_null(d):
        axis = crossProduct_MVector3D(MVector3D(1.0, 0.0, 0.0), v0)
        if is_almost_null(axis.lengthSquared()):
            axis = crossProduct_MVector3D(MVector3D(0.0, 1.0, 0.0), v0)
        axis.normalize()
        # same as MQuaternion.fromAxisAndAngle(axis, 180.0)
        return MQuaternion(0.0, axis.x(), axis.y(), axis.z()).normalized()

    d = sqrt(2.0 * d)
    axis = crossProduct_MVector3D(v0, v1) / d
    return MQuaternion(d * 0.5, axis.x(), axis.y(), axis.z()).normalized()

cdef MQuaternion fromEulerAngles(double pitch, double yaw, double roll):
    pitch = radians(pitch)
    yaw = radians(yaw)
    roll = radians(roll)

    pitch *= 0.5
    yaw *= 0.5
    roll *= 0.5

    cdef double c1 = cos(yaw)
    cdef double s1 = sin(yaw)
    cdef double c2 = cos(roll)
    cdef double s2 = sin(roll)
    cdef double c3 = cos(pitch)
    cdef double s3 = sin(pitch)
    cdef double c1c2 = c1 * c2
    cdef double s1s2 = s1 * s2
    cdef double w = c1c2 * c3 + s1s2 * s3
    cdef double x = c1c2 * s3 + s1s2 * c3
    cdef double y = s1 * c2 * c3 - c1 * s2 * s3
    cdef double z = c1 * s2 * c3 - s1 * c2 * s3

    return MQuaternion(w, x, y, z)

cdef MQuaternion nlerp(MQuaternion q1, MQuaternion q2, double t):
    # Handle the easy cases first.
    if t <= 0.0:
        return q1
    elif t >= 1.0:
        return q2
        
    # Determine the angle between the two quaternions.
    cdef MQuaternion q2b = MQuaternion(q2.scalar(), q2.x(), q2.y(), q2.z())
    
    cdef double dot = dotProduct_MQuaternion(q1, q2)
    if dot < 0.0:
        q2b = -q2b
    
    # Perform the linear interpolation.
    return (q1 * (1.0 - t) + q2b * t).normalized()

cdef MQuaternion slerp(MQuaternion q1, MQuaternion q2, double t):
    # Handle the easy cases first.
    if t <= 0.0:
        return q1
    elif t >= 1.0:
        return q2

    # Determine the angle between the two quaternions.
    cdef MQuaternion q2b = MQuaternion(q2.scalar(), q2.x(), q2.y(), q2.z())
    cdef double dot = dotProduct_MQuaternion(q1, q2)
    
    if dot < 0.0:
        q2b = -q2b
        dot = -dot

    # Get the scale factors.  If they are too small,
    # then revert to simple linear interpolation.
    cdef double factor1 = 1.0 - t
    cdef double factor2 = t
    cdef double angle
    cdef double sinOfAngle

    if (1.0 - dot) > 0.0000001:
        angle = acos(max(0, min(1, dot)))
        sinOfAngle = sin(angle)
        if sinOfAngle > 0.0000001:
            factor1 = sin((1.0 - t) * angle) / sinOfAngle
            factor2 = sin(t * angle) / sinOfAngle

    # Construct the result quaternion.
    return q1 * factor1 + q2b * factor2


cdef class MMatrix4x4:
    
    def __init__(self, m11=1.0, m12=0.0, m13=0.0, m14=0.0, m21=0.0, m22=1.0, m23=0.0, m24=0.0, m31=0.0, m32=0.0, m33=1.0, m34=0.0, m41=0.0, m42=0.0, m43=0.0, m44=1.0):
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

    cpdef MMatrix4x4 copy(self):
        return MMatrix4x4(self.data())
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] data(self):
        return self.__data

    # 逆行列
    cpdef MMatrix4x4 inverted(self):
        return MMatrix4x4(np.linalg.inv(self.data()))

    # 回転行列
    cpdef rotate(self, qq):
        self.__data = self.data().dot(qq.toMatrix4x4().data())

    # 平行移動行列
    cpdef translate(self, MVector3D vec3):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] vec_mat = np.array([[vec3.x(), vec3.y(), vec3.z()], 
                                                                   [vec3.x(), vec3.y(), vec3.z()], 
                                                                   [vec3.x(), vec3.y(), vec3.z()], 
                                                                   [vec3.x(), vec3.y(), vec3.z()]], dtype=np.float64)
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] data_mat = self.__data[:, :3] * vec_mat
        self.__data[:, 3] += np.sum(data_mat, axis=1)

    # 縮尺行列
    cpdef scale(self, MVector3D vec3):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] vec_mat = np.array([[vec3.x(), vec3.y(), vec3.z()], 
                                                                   [vec3.x(), vec3.y(), vec3.z()], 
                                                                   [vec3.x(), vec3.y(), vec3.z()], 
                                                                   [vec3.x(), vec3.y(), vec3.z()]], dtype=np.float64)
        self.__data[:, :3] *= vec_mat
        
    # 単位行列
    cpdef setToIdentity(self):
        self.__data = np.eye(4, dtype=np.float64)
    
    cpdef lookAt(self, MVector3D eye, MVector3D center, MVector3D up):
        cdef MVector3D forward = center - eye
        if forward.is_almost_null():
            # ほぼ0の場合終了
            return
        
        forward.normalize()
        cdef MVector3D side = crossProduct_MVector3D(forward, up).normalized()
        cdef MVector3D upVector = crossProduct_MVector3D(side, forward)

        cdef MMatrix4x4 m = MMatrix4x4()
        m.__data[0, :-1] = side.data()
        m.__data[1, :-1] = upVector.data()
        m.__data[2, :-1] = -forward.data()
        m.__data[-1, -1] = 1.0

        self *= m
        self.translate(-eye)
    
    cpdef perspective(self, double verticalAngle, double aspectRatio, double nearPlane, double farPlane):
        if nearPlane == farPlane or aspectRatio == 0:
            return

        cdef double rad = radians(verticalAngle / 2)
        cdef double sine = sin(rad)

        if sine == 0:
            return
        
        cdef double cotan = cos(rad) / sine
        cdef double clip = farPlane - nearPlane

        cdef MMatrix4x4 m = MMatrix4x4()
        m.__data[0, 0] = cotan / aspectRatio
        m.__data[1, 1] = cotan
        m.__data[2, 2] = -(nearPlane + farPlane) / clip
        m.__data[2, 3] = -(2 * nearPlane * farPlane) / clip
        m.__data[3, 2] = -1

        self *= m
    
    cpdef MVector3D mapVector(self, MVector3D vector):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] vec_mat = np.array([vector.x(), vector.y(), vector.z()])
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] xyz = np.sum(vec_mat * self.__data[:3, :3], axis=1)

        return MVector3D(xyz[0], xyz[1], xyz[2])
    
    cpdef MQuaternion toQuaternion(self):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] a = np.array([[self.__data[0, 0], self.__data[0, 1], self.__data[0, 2], self.__data[0, 3]],
                                                             [self.__data[1, 0], self.__data[1, 1], self.__data[1, 2], self.__data[1, 3]],
                                                             [self.__data[2, 0], self.__data[2, 1], self.__data[2, 2], self.__data[2, 3]],
                                                             [self.__data[3, 0], self.__data[3, 1], self.__data[3, 2], self.__data[3, 3]]], dtype=np.float64)
        
        cdef MQuaternion q = MQuaternion()
        cdef DTYPE_FLOAT_t trace, s

        # I removed + 1
        trace = a[0,0] + a[1,1] + a[2,2]
        # I changed M_EPSILON to 0
        if trace > 0:
            s = 0.5 / sqrt(trace + 1)
            q.setScalar(0.25 / s)
            q.setX((a[2,1] - a[1,2]) * s)
            q.setY((a[0,2] - a[2,0]) * s)
            q.setZ((a[1,0] - a[0,1]) * s)
        else:
            if a[0,0] > a[1,1] and a[0,0] > a[2,2]:
                s = 2 * sqrt(1 + a[0,0] - a[1,1] - a[2,2])
                q.setScalar((a[2,1] - a[1,2]) / s)
                q.setX(0.25 * s)
                q.setY((a[0,1] + a[1,0]) / s)
                q.setZ((a[0,2] + a[2,0]) / s)
            elif a[1,1] > a[2,2]:
                s = 2 * sqrt(1 + a[1,1] - a[0,0] - a[2,2])
                q.setScalar((a[0,2] - a[2,0]) / s)
                q.setX((a[0,1] + a[1,0]) / s)
                q.setY(0.25 * s)
                q.setZ((a[1,2] + a[2,1]) / s)
            else:
                s = 2 * sqrt(1 + a[2,2] - a[0,0] - a[1,1])
                q.setScalar((a[1,0] - a[0,1]) / s)
                q.setX((a[0,2] + a[2,0]) / s)
                q.setY((a[1,2] + a[2,1]) / s)
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
        if isinstance(other, np.float64):
            v = self.add_float(other)
        elif isinstance(other, MMatrix4x4):
            v = self.add_MMatrix4x4(other)
        elif isinstance(other, np.int32):
            v = self.add_int(other)
        else:
            v = self.data() + other
        v2 = self.__class__(v)
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] add_MMatrix4x4(self, MMatrix4x4 other):
        return self.__data + other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] add_float(self, DTYPE_FLOAT_t other):
        return self.__data + other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] add_int(self, DTYPE_INT_t other):
        return self.__data + other

    def __sub__(self, other):
        if isinstance(other, np.float64):
            v = self.sub_float(other)
        elif isinstance(other, MMatrix4x4):
            v = self.sub_MMatrix4x4(other)
        elif isinstance(other, np.int32):
            v = self.sub_int(other)
        else:
            v = self.data() - other
        v2 = self.__class__(v)
        return v2
    
    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] sub_MMatrix4x4(self, MMatrix4x4 other):
        return self.__data - other.__data

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] sub_float(self, DTYPE_FLOAT_t other):
        return self.__data - other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] sub_int(self, DTYPE_INT_t other):
        return self.__data - other

    def __mul__(self, other):
        if isinstance(other, np.float64):
            v = self.mul_float(other)
        elif isinstance(other, MMatrix4x4):
            v = self.mul_MMatrix4x4(other)
        elif isinstance(other, MVector3D):
            return self.mul_MVector3D(other)
        elif isinstance(other, MVector4D):
            return self.mul_MVector4D(other)
        elif isinstance(other, np.int32):
            v = self.mul_int(other)
        else:
            v = self.data() * other
        v2 = self.__class__(v)
        return v2
    
    cpdef MVector3D mul_MVector3D(self, MVector3D other):
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] vec_mat = np.array([[other.x(), other.y(), other.z()], 
                                                                   [other.x(), other.y(), other.z()], 
                                                                   [other.x(), other.y(), other.z()], 
                                                                   [other.x(), other.y(), other.z()]], dtype=np.float64)
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] data_sum = np.sum(vec_mat * self.__data[:, :3], axis=1) + self.__data[:, 3]

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
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=2] vec_mat = np.array([[other.x(), other.y(), other.z(), other.w()], 
                                                                   [other.x(), other.y(), other.z(), other.w()], 
                                                                   [other.x(), other.y(), other.z(), other.w()], 
                                                                   [other.x(), other.y(), other.z(), other.w()]], dtype=np.float64)
        cdef np.ndarray[DTYPE_FLOAT_t, ndim=1] data_sum = np.sum(vec_mat * self.__data, axis=1)

        cdef DTYPE_FLOAT_t x = data_sum[0]
        cdef DTYPE_FLOAT_t y = data_sum[1]
        cdef DTYPE_FLOAT_t z = data_sum[2]
        cdef DTYPE_FLOAT_t w = data_sum[3]

        return MVector4D(x, y, z, w)

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] mul_MMatrix4x4(self, MMatrix4x4 other):
        return np.dot(self.data(), other.data())

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] mul_float(self, DTYPE_FLOAT_t other):
        return self.__data * other

    cpdef np.ndarray[DTYPE_FLOAT_t, ndim=2] mul_int(self, DTYPE_INT_t other):
        return self.__data * other

    def __iadd__(self, other):
        self.__data = self.data() + other.data().T
        return self

    def __isub__(self, other):
        self.__data = self.data() + other.data().T
        return self

    def __imul__(self, other):
        self.__data = np.dot(self.data(), other.data())

        return self

    def __itruediv__(self, other):
        self.__data = self.data() / other.data().T
        return self


cpdef bint is_almost_null(v):
    return abs(v) < 0.0000001


cpdef double get_effective_value(v):
    if isnan(v):
        return 0
    
    if isinf(v):
        return 0
    
    return v


cpdef double get_almost_zero_value(v):
    if get_effective_value(v) == 0:
        return 0
        
    if is_almost_null(v):
        return 0

    return v


