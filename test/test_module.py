# -*- coding: utf-8 -*-
#
import math
import unittest
import numpy as np # noqa
import sys
import pathlib
# このソースのあるディレクトリの絶対パスを取得
current_dir = pathlib.Path(__file__).resolve().parent
# モジュールのあるパスを追加
sys.path.append(str(current_dir) + '/../')
sys.path.append(str(current_dir) + '/../src/')

from module.MMath import MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__, level=1)


class MMathTest(unittest.TestCase):

    def test_MVector3D_setX(self):
        x = 0.123
        v = MVector3D()
        v.setX(x)
        print(v.data()[0])
        self.assertEqual(x, v.x())
    
    def test_MQuaternion_toMatrix4x4(self):
        qq = MQuaternion.fromEulerAngles(0, 0, 0)
        print(qq.toMatrix4x4())
        self.assertTrue(True)

    def test_MMatrix4x4_rotate(self):
        mat = MMatrix4x4()
        mat.setToIdentity()
        mat.translate(MVector3D(1, 2, 3))
        mat.rotate(MQuaternion.fromEulerAngles(10, 20, 30))

        print(mat)
    
    def test_MQuaternion_dotProduct(self):
        qq1 = MQuaternion.fromEulerAngles(0, 0, 0)
        qq2 = MQuaternion.fromEulerAngles(160, 0, 0)
        dot = MQuaternion.dotProduct(qq1, qq2)

        print(dot)

    def test_MQuaternion_rotationTo(self):
        vec1 = MVector3D(3.2637246521852603, -17.9330321457957, 0.30790635451710674)
        vec2 = MVector3D(3.2299432048123995, -17.563372285818442, -1.5114782033123464)
        vec3 = MVector3D(1.8119074772766035, -15.793834017971799, 0.24888510565615118)
        
        qq1 = MQuaternion.rotationTo(MVector3D(1, 0, 0), vec1.normalized())
        print(qq1.toEulerAngles4MMD())

        qq2 = MQuaternion.rotationTo(MVector3D(1, 0, 0), vec2.normalized())
        print(qq2.toEulerAngles4MMD())

        qq = qq2 * qq1.inverted()
        print(qq.toEulerAngles4MMD())

        vec = (vec1 - vec3)
        print(vec)

        qq3 = MQuaternion.rotationTo(MVector3D(1, 0, 0), vec2.normalized())
        print(qq3.toEulerAngles4MMD())

        dot = MVector3D.dotProduct(vec1.normalized(), vec2.normalized())
        print(dot)

        degree = math.degrees(2 * math.acos(min(1, max(-1, dot))))
        print(degree)




