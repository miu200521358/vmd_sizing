# -*- coding: utf-8 -*-
#
import unittest

from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "src"))

from mmd.PmxReader import PmxReader
from mmd.VmdReader import VmdReader
from mmd.PmxData import PmxModel, Vertex, Material, Bone, Morph, DisplaySlot, RigidBody, Joint # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MMath import MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MOptions # noqa
from module.MParams import BoneLinks # noqa
from utils import MBezierUtils # noqa
from utils.MException import SizingException # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__, level=1)


class PmxDataTest(unittest.TestCase):

    def test_create_link_2_top_one_01(self):
        pmx_data = PmxModel()
        pmx_data.bones["SIZING_ROOT_BONE"] = Bone("SIZING_ROOT_BONE", "SIZING_ROOT_BONE", MVector3D(), -1, 0, 0)
        pmx_data.bones["SIZING_ROOT_BONE"].index = -1
        pmx_data.bones["右肩"] = Bone("右肩", None, MVector3D(), -1, 0, 0)
        pmx_data.bones["右肩"].index = 0

        with self.assertRaises(SizingException):
            links = pmx_data.create_link_2_top_one("右手首")

            print(links)

    def test_create_link_2_top_one_02(self):
        pmx_data = PmxModel()
        pmx_data.bones["SIZING_ROOT_BONE"] = Bone("SIZING_ROOT_BONE", "SIZING_ROOT_BONE", MVector3D(), -1, 0, 0)
        pmx_data.bones["SIZING_ROOT_BONE"].index = -1
        pmx_data.bones["右肩"] = Bone("右肩", None, MVector3D(), -1, 0, 0)
        pmx_data.bones["右肩"].index = 0
        pmx_data.bones["右手首"] = Bone("右手首", None, MVector3D(), -1, 0, 0)
        pmx_data.bones["右手首"].index = 1

        links = pmx_data.create_link_2_top_one("右手首")
        self.assertEqual(len(links.all()), 1)

    def test_create_link_2_top_one_03(self):
        pmx_data = PmxModel()
        pmx_data.bones["SIZING_ROOT_BONE"] = Bone("SIZING_ROOT_BONE", "SIZING_ROOT_BONE", MVector3D(), -1, 0, 0)
        pmx_data.bones["SIZING_ROOT_BONE"].index = -1
        pmx_data.bones["右肩"] = Bone("右肩", None, MVector3D(), -1, 0, 0)
        pmx_data.bones["右肩"].index = len(pmx_data.bones) - 1
        pmx_data.bones["右腕"] = Bone("右腕", None, MVector3D(), -1, 0, 0)
        pmx_data.bones["右腕"].index = len(pmx_data.bones) - 1
        pmx_data.bones["右ひじ"] = Bone("右ひじ", None, MVector3D(), -1, 0, 0)
        pmx_data.bones["右ひじ"].index = len(pmx_data.bones) - 1
        pmx_data.bones["右手首"] = Bone("右手首", None, MVector3D(), -1, 0, 0)
        pmx_data.bones["右手首"].index = len(pmx_data.bones) - 1
        pmx_data.bones["左腕"] = Bone("左腕", None, MVector3D(), -1, 0, 0)
        pmx_data.bones["左腕"].index = len(pmx_data.bones) - 1

        links = pmx_data.create_link_2_top_one("右手首")
        self.assertEqual(len(links.all()), 4)

if __name__ == "__main__":
    unittest.main()

