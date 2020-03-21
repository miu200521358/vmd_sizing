# -*- coding: utf-8 -*-
#
import math
import numpy as np
import quaternion


class MRect():

    def __init__(self, x=0, y=0, width=0, height=0):
        self.__x = x
        self.__y = y
        self.__width = width
        self.__height = height

    def x(self):
        return int(self.__x)

    def y(self):
        return int(self.__y)

    def width(self):
        return int(self.__width)

    def height(self):
        return int(self.__height)

    def __str__(self):
        return "MRect({0}, {1}, {2}, {3})".format(self.__x, self.__y, self.__width, self.__height)


class MVector3D():

    def __init__(self, x=0, y=0, z=0):
        if isinstance(x, MVector3D):
            # クラスの場合
            self.__data = x.__data
        elif isinstance(x, np.ndarray):
            # arrayそのものの場合
            self.__data = np.array([x[0], x[1], x[2]])
        else:
            self.__data = np.array([x, y, z], dtype=np.float64)

    def length(self):
        return float(np.linalg.norm(self.__data, ord=2))

    def lengthSquared(self):
        return float(np.linalg.norm(self.__data, ord=2)**2)

    def normalized(self):
        l2 = np.linalg.norm(self.__data, ord=2, axis=-1, keepdims=True)
        l2[l2 == 0] = 1
        normv = self.__data / l2
        return MVector3D(normv[0], normv[1], normv[2])

    def normalize(self):
        l2 = np.linalg.norm(self.__data, ord=2, axis=-1, keepdims=True)
        l2[l2 == 0] = 1
        normv = self.__data / l2
        self.__data = normv
    
    def distanceToPoint(self, v):
        return MVector3D(self.__data - v.__data).length()
    
    def project(self, modelView, projection, viewport):
        tmp = MVector4D(self.x(), self.y(), self.z(), 1)
        tmp = projection * modelView * tmp
        if is_almost_null(tmp.w()):
            tmp.setW(1)

        tmp /= tmp.w()
        tmp = tmp * 0.5 + MVector4D(0.5, 0.5, 0.5, 0.5)
        tmp.setX(tmp.x() * viewport.width() + viewport.x())
        tmp.setY(tmp.y() * viewport.height() + viewport.y())

        return tmp.toVector3D()

    def unproject(self, modelView, projection, viewport):
        inverse = (projection * modelView).inverted()

        tmp = MVector4D(self.x(), self.y(), self.z(), 1)
        tmp.setX((tmp.x() - viewport.x()) / viewport.width())
        tmp.setY((tmp.y() - viewport.y()) / viewport.height())
        tmp = tmp * 2 - MVector4D(1, 1, 1, 1)

        obj = inverse * tmp
        if is_almost_null(obj.w()):
            obj.setW(1)

        obj /= obj.w()
        
        return obj.toVector3D()
        
    def toVector4D(self):
        return MVector4D(self.__data[0], self.__data[1], self.__data[2], 0)

    def is_almost_null(self):
        return (is_almost_null(self.__data[0]) and is_almost_null(self.__data[1]) and is_almost_null(self.__data[2]))
                
    @classmethod
    def crossProduct(cls, v1, v2):
        crossv = np.cross(v1.__data, v2.__data)
        return MVector3D(crossv[0], crossv[1], crossv[2])

    @classmethod
    def dotProduct(cls, v1, v2):
        dotv = np.dot(v1.__data, v2.__data)
        return dotv
    
    def data(self):
        return self.__data

    def __str__(self):
        return "MVector3D({0}, {1}, {2})".format(self.__data[0], self.__data[1], self.__data[2])

    def __lt__(self, other):
        return np.all(self.__data < other.__data)

    def __le__(self, other):
        return np.all(self.__data <= other.__data)

    def __eq__(self, other):
        return np.all(self.__data == other.__data)

    def __ne__(self, other):
        return np.all(self.__data != other.__data)

    def __gt__(self, other):
        return np.all(self.__data > other.__data)

    def __ge__(self, other):
        return np.all(self.__data >= other.__data)

    def __add__(self, other):
        if isinstance(other, MVector3D):
            v = self.__data + other.__data
        else:
            v = self.__data + other
        return self.__class__(v)

    def __sub__(self, other):
        if isinstance(other, MVector3D):
            v = self.__data - other.__data
        else:
            v = self.__data - other
        return self.__class__(v)

    def __mul__(self, other):
        if isinstance(other, MVector3D):
            v = self.__data * other.__data
        else:
            v = self.__data * other
        return self.__class__(v)

    def __truediv__(self, other):
        if isinstance(other, MVector3D):
            v = self.__data / other.__data
        else:
            v = self.__data / other
        return self.__class__(v)

    def __floordiv__(self, other):
        if isinstance(other, MVector3D):
            v = self.__data // other.__data
        else:
            v = self.__data // other
        return self.__class__(v)

    def __mod__(self, other):
        if isinstance(other, MVector3D):
            v = self.__data % other.__data
        else:
            v = self.__data % other
        return self.__class__(v)

    def __pow__(self, other):
        if isinstance(other, MVector3D):
            v = self.__data ** other.__data
        else:
            v = self.__data ** other
        return self.__class__(v)

    def __lshift__(self, other):
        if isinstance(other, MVector3D):
            v = self.__data << other.__data
        else:
            v = self.__data << other
        return self.__class__(v)

    def __rshift__(self, other):
        if isinstance(other, MVector3D):
            v = self.__data >> other.__data
        else:
            v = self.__data >> other
        return self.__class__(v)

    def __and__(self, other):
        v = self.__data & other.__data
        return self.__class__(v)

    def __dataor__(self, other):
        v = self.__data ^ other.__data
        return self.__class__(v)

    def __or__(self, other):
        v = self.__data | other.__data
        return self.__class__(v)

    def __neg__(self):
        return self.__class__(-self.__data[0], -self.__data[1], -self.__data[2])

    def __pos__(self):
        return self.__class__(+self.__data[0], +self.__data[1], +self.__data[2])

    def __invert__(self):
        return self.__class__(~self.__data[0], ~self.__data[1], ~self.__data[2])
    
    def x(self):
        return float(self.__data[0])

    def y(self):
        return float(self.__data[1])

    def z(self):
        return float(self.__data[2])
    
    def setX(self, x):
        self.__data[0] = x

    def setY(self, y):
        self.__data[1] = y

    def setZ(self, z):
        self.__data[2] = z


class MVector4D():

    def __init__(self, x=0, y=0, z=0, w=0):
        if isinstance(x, MVector4D):
            # クラスの場合
            self.__data = x.__data
        elif isinstance(x, np.ndarray):
            # 行列そのものの場合
            self.__data = np.array([x[0], x[1], x[2], x[3]])
        else:
            self.__data = np.array([x, y, z, w], dtype=np.float64)

    def length(self):
        return np.linalg.norm(self.__data, ord=2)

    def lengthSquared(self):
        return np.linalg.norm(self.__data, ord=2)**2

    def normalized(self):
        l2 = np.linalg.norm(self.__data, ord=2, axis=-1, keepdims=True)
        l2[l2 == 0] = 1
        normv = self.__data / l2
        return MVector4D(normv[0], normv[1], normv[2], normv[3])

    def normalize(self):
        l2 = np.linalg.norm(self.__data, ord=2, axis=-1, keepdims=True)
        l2[l2 == 0] = 1
        normv = self.__data / l2
        self.__data = normv

    def toVector3D(self):
        return MVector3D(self.__data[0], self.__data[1], self.__data[2])

    def is_almost_null(self):
        return (is_almost_null(self.__data[0]) and is_almost_null(self.__data[1]) and is_almost_null(self.__data[2]) and is_almost_null(self.__data[3]))
                                
    @classmethod
    def dotProduct(cls, v1, v2):
        dotv = np.dot(v1.__data, v2.__data)
        return dotv
    
    def data(self):
        return self.__data

    def __str__(self):
        return "MVector4D({0}, {1}, {2}, {3})".format(self.__data[0], self.__data[1], self.__data[2], self.__data[3])

    def __lt__(self, other):
        return np.all(self.__data < other.__data)

    def __le__(self, other):
        return np.all(self.__data <= other.__data)

    def __eq__(self, other):
        return np.all(self.__data == other.__data)

    def __ne__(self, other):
        return np.all(self.__data != other.__data)

    def __gt__(self, other):
        return np.all(self.__data > other.__data)

    def __ge__(self, other):
        return np.all(self.__data >= other.__data)

    def __add__(self, other):
        if isinstance(other, MVector4D):
            v = self.__data + other.__data
        else:
            v = self.__data + other
        return self.__class__(v)

    def __sub__(self, other):
        if isinstance(other, MVector4D):
            v = self.__data - other.__data
        else:
            v = self.__data - other
        return self.__class__(v)

    def __mul__(self, other):
        if isinstance(other, MVector4D):
            v = self.__data * other.__data
        else:
            v = self.__data * other
        return self.__class__(v)

    def __truediv__(self, other):
        if isinstance(other, MVector4D):
            v = self.__data / other.__data
        else:
            v = self.__data / other
        return self.__class__(v)

    def __floordiv__(self, other):
        if isinstance(other, MVector4D):
            v = self.__data // other.__data
        else:
            v = self.__data // other
        return self.__class__(v)

    def __mod__(self, other):
        if isinstance(other, MVector4D):
            v = self.__data % other.__data
        else:
            v = self.__data % other
        return self.__class__(v)

    def __pow__(self, other):
        if isinstance(other, MVector4D):
            v = self.__data ** other.__data
        else:
            v = self.__data ** other
        return self.__class__(v)

    def __lshift__(self, other):
        if isinstance(other, MVector4D):
            v = self.__data << other.__data
        else:
            v = self.__data << other
        return self.__class__(v)

    def __rshift__(self, other):
        if isinstance(other, MVector4D):
            v = self.__data >> other.__data
        else:
            v = self.__data >> other
        return self.__class__(v)

    def __and__(self, other):
        v = self.__data & other.__data
        return self.__class__(v)

    def __dataor__(self, other):
        v = self.__data ^ other.__data
        return self.__class__(v)

    def __or__(self, other):
        v = self.__data | other.__data
        return self.__class__(v)

    def __neg__(self):
        return self.__class__(-self.__data[0], -self.__data[1], -self.__data[2], -self.__data[3])

    def __pos__(self):
        return self.__class__(+self.__data[0], +self.__data[1], +self.__data[2], +self.__data[3])

    def __invert__(self):
        return self.__class__(~self.__data[0], ~self.__data[1], ~self.__data[2], ~self.__data[3])
    
    def x(self):
        return float(self.__data[0])

    def y(self):
        return float(self.__data[1])

    def z(self):
        return float(self.__data[2])
    
    def w(self):
        return float(self.__data[3])
    
    def setX(self, x):
        self.__data[0] = x

    def setY(self, y):
        self.__data[1] = y

    def setZ(self, z):
        self.__data[2] = z

    def setW(self, w):
        self.__data[3] = w


class MQuaternion():

    def __init__(self, w=0, x=0, y=0, z=0):
        if isinstance(w, MQuaternion):
            # クラスの場合
            self.__data = w.__data
        elif isinstance(w, np.ndarray):
            # arrayそのものの場合
            self.__data = np.quaternion(w[0], w[1], w[2], w[3])
        else:
            self.__data = np.quaternion(w, x, y, z)
    
    def __str__(self):
        return "MQuaternion({0}, {1}, {2}, {3})".format(self.__data.w, self.__data.x, self.__data.y, self.__data.z)

    def inverted(self):
        v = self.__data.inverse()
        return self.__class__(v.w, v.x, v.y, v.z)

    def length(self):
        return self.__data.abs()

    def lengthSquared(self):
        return self.__data.abs()**2

    def normalized(self):
        v = self.__data.normalized()
        return MQuaternion(v.w, v.x, v.y, v.z)

    def normalize(self):
        self.__data = self.__data.normalized()
    
    def toMatrix4x4(self):
        mat = MMatrix4x4()
        m = mat.data()

        # q(w,x,y,z)から(x,y,z,w)に並べ替え.
        q2 = np.array([self.__data.x, self.__data.y, self.__data.z, self.__data.w])

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

        k = m[3, 3]
        for i in range(3):
            for j in range(3):
                m[i, j] /= k

        m[3, 3] = 1.0

        return mat
    
    def toVector4D(self):
        return MVector4D(self.__data.x, self.__data.y, self.__data.z, self.__data.w)

    # http://www.j3d.org/matrix_faq/matrfaq_latest.html#Q37
    def toEulerAngles(self):
        xp = self.__data.x
        yp = self.__data.y
        zp = self.__data.z
        wp = self.__data.w

        xx = xp * xp
        xy = xp * yp
        xz = xp * zp
        xw = xp * wp
        yy = yp * yp
        yz = yp * zp
        yw = yp * wp
        zz = zp * zp
        zw = zp * wp
        lengthSquared = xx + yy + zz + wp * wp

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

        pitch = math.asin(max(-1, min(1, -2.0 * (yz - xw))))
        
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

        v = MVector3D()
        v.setX(math.degrees(pitch))
        v.setY(math.degrees(yaw))
        v.setZ(math.degrees(roll))

        return v
        
    @classmethod
    def dotProduct(cls, v1, v2):
        dotv = np.sum(v1.__data.components * v2.__data.components)
        return dotv
    
    @classmethod
    def fromAxisAndAngle(cls, x, y, z, angle):
        length = math.sqrt(x * x + y * y + z * z)

        if not is_almost_null(length - 1.0) and not is_almost_null(length):
            x /= length
            y /= length
            z /= length

        a = math.radians(angle / 2.0)
        s = math.sin(a)
        c = math.cos(a)
        return MQuaternion(c, x * s, y * s, z * s).normalized()
    
    @classmethod
    def fromDirection(cls, direction, up):
        if direction.is_almost_null():
            return MQuaternion()

        zAxis = direction.normalized()
        xAxis = MVector3D.crossProduct(up, zAxis)
        if (is_almost_null(xAxis.lengthSquared())):
            # collinear or invalid up vector derive shortest arc to new direction
            return MQuaternion.rotationTo(MVector3D(0.0, 0.0, 1.0), zAxis)
        
        xAxis.normalize()
        yAxis = MVector3D.crossProduct(zAxis, xAxis)
        return MQuaternion.fromAxes(xAxis, yAxis, zAxis)
    
    @classmethod
    def fromAxes(cls, xAxis, yAxis, zAxis):
        rot3x3 = np.array([[xAxis.x(), yAxis.x(), zAxis.x()], [xAxis.y(), yAxis.y(), zAxis.y()], [xAxis.z(), yAxis.z(), zAxis.z()]])
        return MQuaternion.fromRotationMatrix(rot3x3)
    
    @classmethod
    def fromRotationMatrix(cls, rot3x3):
        scalar = 0
        axis = np.zeros(3)

        trace = rot3x3[0][0] + rot3x3[1][1] + rot3x3[2][2]
        if trace > 0.00000001:
            s = 2.0 * math.sqrt(trace + 1.0)
            scalar = 0.25 * s
            axis[0] = (rot3x3[2][1] - rot3x3[1][2]) / s
            axis[1] = (rot3x3[0][2] - rot3x3[2][0]) / s
            axis[2] = (rot3x3[1][0] - rot3x3[0][1]) / s
        else:
            s_next = np.array([1, 2, 0], dtype=np.int8)
            i = 0
            if rot3x3[1][1] > rot3x3[0][0]:
                i = 1
            if rot3x3[2][2] > rot3x3[i][i]:
                i = 2

            j = s_next[i]
            k = s_next[j]

            s = 2.0 * math.sqrt(rot3x3[i][i] - rot3x3[j][j] - rot3x3[k][k] + 1.0)
            axis[i] = 0.25 * s

            scalar = (rot3x3[k][j] - rot3x3[j][k]) / s
            axis[j] = (rot3x3[j][i] + rot3x3[i][j]) / s
            axis[k] = (rot3x3[k][i] + rot3x3[i][k]) / s

        return MQuaternion(scalar, axis[0], axis[1], axis[2])

    @classmethod
    def rotationTo(cls, fromv, tov):
        v0 = fromv.normalized()
        v1 = tov.normalized()
        d = MVector3D.dotProduct(v0, v1) + 1.0

        # if dest vector is close to the inverse of source vector, ANY axis of rotation is valid
        if is_almost_null(d):
            axis = MVector3D.crossProduct(MVector3D(1.0, 0.0, 0.0), v0)
            if is_almost_null(axis.lengthSquared()):
                axis = MVector3D.crossProduct(MVector3D(0.0, 1.0, 0.0), v0)
            axis.normalize()
            # same as MQuaternion.fromAxisAndAngle(axis, 180.0)
            return MQuaternion(0.0, axis.x(), axis.y(), axis.z())

        d = math.sqrt(2.0 * d)
        axis = MVector3D.crossProduct(v0, v1) / d
        return MQuaternion(d * 0.5, axis.x(), axis.y(), axis.z()).normalized()
    
    @classmethod
    def fromEulerAngles(cls, pitch, yaw, roll):
        pitch = math.radians(pitch)
        yaw = math.radians(yaw)
        roll = math.radians(roll)

        pitch *= 0.5
        yaw *= 0.5
        roll *= 0.5

        c1 = math.cos(yaw)
        s1 = math.sin(yaw)
        c2 = math.cos(roll)
        s2 = math.sin(roll)
        c3 = math.cos(pitch)
        s3 = math.sin(pitch)
        c1c2 = c1 * c2
        s1s2 = s1 * s2
        w = c1c2 * c3 + s1s2 * s3
        x = c1c2 * s3 + s1s2 * c3
        y = s1 * c2 * c3 - c1 * s2 * s3
        z = c1 * s2 * c3 - s1 * c2 * s3

        return MQuaternion(w, x, y, z)
    
    @classmethod
    def nlerp(cls, q1, q2, t):
        # Handle the easy cases first.
        if t <= 0.0:
            return q1
        elif t >= 1.0:
            return q2
            
        # Determine the angle between the two quaternions.
        q2b = MQuaternion(q2.scalar(), q2.x(), q2.y(), q2.z())
        
        dot = MQuaternion.dotProduct(q1, q2)
        if dot < 0.0:
            q2b = -q2b
        
        # Perform the linear interpolation.
        return (q1 * (1.0 - t) + q2b * t).normalized()

    @classmethod
    def slerp(cls, q1, q2, t):
        # Handle the easy cases first.
        if t <= 0.0:
            return q1
        elif t >= 1.0:
            return q2

        # Determine the angle between the two quaternions.
        q2b = MQuaternion(q2.scalar(), q2.x(), q2.y(), q2.z())
        dot = MQuaternion.dotProduct(q1, q2)
        
        if dot < 0.0:
            q2b = -q2b
            dot = -dot

        # Get the scale factors.  If they are too small,
        # then revert to simple linear interpolation.
        factor1 = 1.0 - t
        factor2 = t

        if (1.0 - dot) > 0.0000001:
            angle = math.acos(dot)
            sinOfAngle = math.sin(angle)
            if sinOfAngle > 0.0000001:
                factor1 = math.sin((1.0 - t) * angle) / sinOfAngle
                factor2 = math.sin(t * angle) / sinOfAngle

        # Construct the result quaternion.
        return q1 * factor1 + q2b * factor2
                
    def x(self):
        return float(self.__data.x)

    def y(self):
        return float(self.__data.y)

    def z(self):
        return float(self.__data.z)

    def scalar(self):
        return float(self.__data.w)
    
    def setX(self, x):
        self.__data.x = x

    def setY(self, y):
        self.__data.y = y

    def setZ(self, z):
        self.__data.z = z

    def setScalar(self, w):
        self.__data.w = w
    
    def data(self):
        return self.__data

    def __lt__(self, other):
        return np.all(self.__data < other.__data)

    def __le__(self, other):
        return np.all(self.__data <= other.__data)

    def __eq__(self, other):
        return np.all(self.__data == other.__data)

    def __ne__(self, other):
        return np.all(self.__data != other.__data)

    def __gt__(self, other):
        return np.all(self.__data > other.__data)

    def __ge__(self, other):
        return np.all(self.__data >= other.__data)

    def __add__(self, other):
        if isinstance(other, MQuaternion):
            v = self.__data + other.__data
        else:
            v = self.__data + other
        return self.__class__(v.w, v.x, v.y, v.z)

    def __sub__(self, other):
        if isinstance(other, MQuaternion):
            v = self.__data - other.__data
        else:
            v = self.__data - other
        return self.__class__(v.w, v.x, v.y, v.z)

    def __mul__(self, other):
        if isinstance(other, MQuaternion):
            v = self.__data * other.__data
        else:
            v = self.__data * other
        return self.__class__(v.w, v.x, v.y, v.z)

    def __truediv__(self, other):
        if isinstance(other, MQuaternion):
            v = self.__data / other.__data
        else:
            v = self.__data / other
        return self.__class__(v.w, v.x, v.y, v.z)

    def __floordiv__(self, other):
        if isinstance(other, MQuaternion):
            v = self.__data // other.__data
        else:
            v = self.__data // other
        return self.__class__(v.w, v.x, v.y, v.z)

    def __mod__(self, other):
        if isinstance(other, MQuaternion):
            v = self.__data % other.__data
        else:
            v = self.__data % other
        return self.__class__(v.w, v.x, v.y, v.z)

    def __pow__(self, other):
        if isinstance(other, MQuaternion):
            v = self.__data ** other.__data
        else:
            v = self.__data ** other
        return self.__class__(v.w, v.x, v.y, v.z)

    def __lshift__(self, other):
        if isinstance(other, MQuaternion):
            v = self.__data << other.__data
        else:
            v = self.__data << other
        return self.__class__(v.w, v.x, v.y, v.z)

    def __rshift__(self, other):
        if isinstance(other, MQuaternion):
            v = self.__data >> other.__data
        else:
            v = self.__data >> other
        return self.__class__(v.w, v.x, v.y, v.z)

    def __and__(self, other):
        v = self.__data & other.__data
        return self.__class__(v.w, v.x, v.y, v.z)

    def __dataor__(self, other):
        v = self.__data ^ other.__data
        return self.__class__(v.w, v.x, v.y, v.z)

    def __or__(self, other):
        v = self.__data | other.__data
        return self.__class__(v.w, v.x, v.y, v.z)
    
    def __neg__(self):
        return self.__class__(-self.__data.w, -self.__data.x, -self.__data.y, -self.__data.z)

    def __pos__(self):
        return self.__class__(+self.__data.w, +self.__data.x, +self.__data.y, +self.__data.z)

    def __invert__(self):
        return self.__class__(~self.__data.w, ~self.__data.x, ~self.__data.y, ~self.__data.z)


class MMatrix4x4():
    
    def __init__(self, m11=0, m12=0, m13=0, m14=0, m21=0, m22=0, m23=0, m24=0, m31=0, m32=0, m33=0, m34=0, m41=0, m42=0, m43=0, m44=0):
        if isinstance(m11, MMatrix4x4):
            # 行列クラスの場合
            self.__data = m11.__data
        elif isinstance(m11, np.ndarray):
            # 行列そのものの場合
            self.__data = m11
        else:
            # べた値の場合
            self.__data = np.array([[m11, m12, m13, m14], [m21, m22, m23, m24], [m31, m32, m33, m34], [m41, m42, m43, m44]], dtype=np.float64)

    def data(self):
        return self.__data
    
    # 逆行列
    def inverted(self):
        v = np.linalg.inv(self.__data)
        return MMatrix4x4(v)

    # 回転行列
    def rotate(self, qq):
        qq_mat = qq.toMatrix4x4()
        self.__data = self.__data.dot(qq_mat.__data)

    # 平行移動行列
    def translate(self, vec3):
        vec_mat = np.tile(np.array([vec3.x(), vec3.y(), vec3.z()]), (4, 1))
        data_mat = self.__data[:, :3] * vec_mat
        self.__data[:, 3] += np.sum(data_mat, axis=1)
    
    # 単位行列
    def setToIdentity(self):
        self.__data = np.identity(4, dtype=np.float64)
    
    def lookAt(self, eye, center, up):
        forward = center - eye
        if forward.is_almost_null():
            # ほぼ0の場合終了
            return
        
        forward.normalize()
        side = MVector3D.crossProduct(forward, up).normalized()
        upVector = MVector3D.crossProduct(side, forward)

        m = MMatrix4x4()
        m.__data[0, :-1] = side.data()
        m.__data[1, :-1] = upVector.data()
        m.__data[2, :-1] = -forward.data()
        m.__data[-1, -1] = 1.0

        self *= m
        self.translate(-eye)
    
    def perspective(self, verticalAngle, aspectRatio, nearPlane, farPlane):
        if nearPlane == farPlane or aspectRatio == 0:
            return

        radians = math.radians(verticalAngle / 2)
        sine = math.sin(radians)

        if sine == 0:
            return
        
        cotan = math.cos(radians) / sine
        clip = farPlane - nearPlane

        m = MMatrix4x4()
        m.__data[0, 0] = cotan / aspectRatio
        m.__data[1, 1] = cotan
        m.__data[2, 2] = -(nearPlane + farPlane) / clip
        m.__data[2, 3] = -(2 * nearPlane * farPlane) / clip
        m.__data[3, 2] = -1

        self *= m

    def __str__(self):
        return "MMatrix4x4({0})".format(self.__data)

    def __lt__(self, other):
        return np.all(self.__data < other.__data)

    def __le__(self, other):
        return np.all(self.__data <= other.__data)

    def __eq__(self, other):
        return np.all(self.__data == other.__data)

    def __ne__(self, other):
        return np.all(self.__data != other.__data)

    def __gt__(self, other):
        return np.all(self.__data > other.__data)

    def __ge__(self, other):
        return np.all(self.__data >= other.__data)

    def __add__(self, other):
        if isinstance(other, MMatrix4x4):
            v = self.__data + other.__data
        else:
            v = self.__data + other
        return self.__class__(v)

    def __sub__(self, other):
        if isinstance(other, MMatrix4x4):
            v = self.__data - other.__data
        else:
            v = self.__data - other
        return self.__class__(v)

    # *演算子
    def __mul__(self, other):
        if isinstance(other, MVector3D):
            vec_mat = np.tile(np.array([other.x(), other.y(), other.z()]), (4, 1))
            data_sum = np.sum(vec_mat * self.__data[:, :3], axis=1) + self.__data[:, 3]

            x = data_sum[0]
            y = data_sum[1]
            z = data_sum[2]
            w = data_sum[3]
                
            if w == 1.0:
                return MVector3D(x, y, z)
            else:
                return MVector3D(x / w, y / w, z / w)
        elif isinstance(other, MVector4D):
            vec_mat = np.tile(np.array([other.x(), other.y(), other.z(), other.w()]), (4, 1))
            data_sum = np.sum(vec_mat * self.__data, axis=1)

            x = data_sum[0]
            y = data_sum[1]
            z = data_sum[2]
            w = data_sum[3]

            return MVector4D(x, y, z, w)
        elif isinstance(other, MMatrix4x4):
            v = np.dot(self.__data, other.__data)
            return self.__class__(v)
        
        v = self.__data * other
        return self.__class__(v)
        
    def __iadd__(self, other):
        self.__data = self.__data + other.__data.T
        return self

    def __isub__(self, other):
        self.__data = self.__data + other.__data.T
        return self

    def __imul__(self, other):
        v = MMatrix4x4()

        v.__data[0, 0] = np.sum(self.__data[0, :] * other.__data[:, 0])
        v.__data[0, 1] = np.sum(self.__data[0, :] * other.__data[:, 1])
        v.__data[0, 2] = np.sum(self.__data[0, :] * other.__data[:, 2])
        v.__data[0, 3] = np.sum(self.__data[0, :] * other.__data[:, 3])

        v.__data[1, 0] = np.sum(self.__data[1, :] * other.__data[:, 0])
        v.__data[1, 1] = np.sum(self.__data[1, :] * other.__data[:, 1])
        v.__data[1, 2] = np.sum(self.__data[1, :] * other.__data[:, 2])
        v.__data[1, 3] = np.sum(self.__data[1, :] * other.__data[:, 3])

        v.__data[2, 0] = np.sum(self.__data[2, :] * other.__data[:, 0])
        v.__data[2, 1] = np.sum(self.__data[2, :] * other.__data[:, 1])
        v.__data[2, 2] = np.sum(self.__data[2, :] * other.__data[:, 2])
        v.__data[2, 3] = np.sum(self.__data[2, :] * other.__data[:, 3])

        v.__data[3, 0] = np.sum(self.__data[3, :] * other.__data[:, 0])
        v.__data[3, 1] = np.sum(self.__data[3, :] * other.__data[:, 1])
        v.__data[3, 2] = np.sum(self.__data[3, :] * other.__data[:, 2])
        v.__data[3, 3] = np.sum(self.__data[3, :] * other.__data[:, 3])
                
        self.__data = v.__data

        return self

    def __itruediv__(self, other):
        self.__data = self.__data / other.__data.T
        return self


def is_almost_null(v):
    return abs(v) < 0.00001
        