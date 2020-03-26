# -*- coding: utf-8 -*-
#
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

