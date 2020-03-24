# -*- coding: utf-8 -*-
#
import unittest

from mmd.PmxReader import PmxReader
from mmd.VmdReader import VmdReader
from mmd.PmxData import PmxModel, Vertex, Material, Bone, Morph, DisplaySlot, RigidBody, Joint # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MMath import MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MOptions # noqa
from module.MParams import BoneLinks # noqa
from utils import MBezierUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class VmdDataTest(unittest.TestCase):

    def test_calc_bone_by_interpolation_01(self):
        motion = VmdReader("C:/Self/20200324_sizing/vmd/syojo/少女ふぜゐIK_Tda式初音ミクV4X_Ver1.00_20190908_211835.vmd").read_data()
        bf = motion.calc_bone_by_interpolation("右手首", 0)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.scalar(), 0.9497644305229187, delta=0.1)
        self.assertAlmostEqual(bf.rotation.x(), -0.2827410101890564, delta=0.1)
        self.assertAlmostEqual(bf.rotation.y(), -0.08001948893070221, delta=0.1)
        self.assertAlmostEqual(bf.rotation.z(), 0.10771214962005615, delta=0.1)

        bf = motion.calc_bone_by_interpolation("上半身", 100)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.scalar(), 0.9193096160888672, delta=0.1)
        self.assertAlmostEqual(bf.rotation.x(), -0.006163282319903374, delta=0.1)
        self.assertAlmostEqual(bf.rotation.y(), 0.3934842646121979, delta=0.1)
        self.assertAlmostEqual(bf.rotation.z(), -0.001418940257281065, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 200)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), -0.9951982498168945, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), -0.330341100692749, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), -0.28153330087661743, delta=0.1)
        self.assertAlmostEqual(bf.rotation.scalar(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.z(), 0, delta=0.1)

        


if __name__ == "__main__":
    unittest.main()

