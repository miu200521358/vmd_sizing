# -*- coding: utf-8 -*-
#
import unittest
import sys
import pathlib
# このソースのあるディレクトリの絶対パスを取得
current_dir = pathlib.Path(__file__).resolve().parent
# モジュールのあるパスを追加
sys.path.append(str(current_dir) + '/../')
sys.path.append(str(current_dir) + '/../src/')

from mmd.PmxData import PmxModel, Vertex, Material, Bone, Morph, DisplaySlot, RigidBody, Joint # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MMath import MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MOptions # noqa
from module.MParams import BoneLinks # noqa
from utils import MBezierUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class MServiceUtilsTest(unittest.TestCase):

    def test_calc_global_pos_dic01(self):
        self.assertTrue(True)


class MBezierUtilsTest(unittest.TestCase):

    def test_MBezierUtils_evaluate01(self):
        x, y, t = MBezierUtils.evaluate(20, 20, 107, 107, 0, 5, 10)
        print("x: %s" % x)
        print("y: %s" % y)
        print("t: %s" % t)

        self.assertAlmostEqual(x, 0.5, delta=0.01)
        self.assertAlmostEqual(y, 0.5, delta=0.01)
        self.assertAlmostEqual(t, 0.5, delta=0.01)

    def test_MBezierUtils_evaluate02(self):
        x, y, t = MBezierUtils.evaluate(20, 20, 107, 107, 181, 200, 205)
        print("x: %s" % x)
        print("y: %s" % y)
        print("t: %s" % t)

        self.assertAlmostEqual(x, 0.79, delta=0.01)
        self.assertAlmostEqual(y, 0.79, delta=0.01)
        self.assertAlmostEqual(t, 0.74, delta=0.01)

    def test_MBezierUtils_evaluate03(self):
        x, y, t = MBezierUtils.evaluate(104, 63, 13, 111, 0, 5, 10)
        print("x: %s" % x)
        print("y: %s" % y)
        print("t: %s" % t)

        self.assertAlmostEqual(x, 0.5, delta=0.01)
        self.assertAlmostEqual(y, 0.74, delta=0.01)
        self.assertAlmostEqual(t, 0.61, delta=0.01)

    def test_MBezierUtils_evaluate04(self):
        x, y, t = MBezierUtils.evaluate(0, 127, 127, 0, 0, 1, 30)
        print("x: %s" % x)
        print("y: %s" % y)
        print("t: %s" % t)

        self.assertAlmostEqual(x, 0.03, delta=0.01)
        self.assertAlmostEqual(y, 0.26, delta=0.01)
        self.assertAlmostEqual(t, 0.11, delta=0.01)

    def test_MBezierUtils_evaluate05(self):
        x, y, t = MBezierUtils.evaluate(0, 127, 127, 0, 0, 2, 30)
        print("x: %s" % x)
        print("y: %s" % y)
        print("t: %s" % t)

        self.assertAlmostEqual(x, 0.06, delta=0.01)
        self.assertAlmostEqual(y, 0.34, delta=0.01)
        self.assertAlmostEqual(t, 0.16, delta=0.01)


if __name__ == "__main__":
    unittest.main()

