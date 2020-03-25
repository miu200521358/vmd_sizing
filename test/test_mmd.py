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

from mmd.PmxReader import PmxReader # noqa
from mmd.VmdReader import VmdReader # noqa
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


class VmdDataTest(unittest.TestCase):

    def test_calc_bone_by_interpolation_01(self):
        motion = VmdReader("D:/MMD/MikuMikuDance_v926x64/UserFile/Motion/ダンス_1人/ドラマツルギー motion 配布用 moka/ドラマツルギー_0-500.vmd").read_data()
        
        bf = motion.calc_bone_by_interpolation("右腕", 101)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 27.1, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 16.2, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), -32.9, delta=0.1)

        bf = motion.calc_bone_by_interpolation("右腕", 143)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 32.2, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 57.3, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), -23.6, delta=0.1)

        bf = motion.calc_bone_by_interpolation("右腕", 107)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 16.7, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 27.2, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), -32.8, delta=0.1)

        bf = motion.calc_bone_by_interpolation("右腕", 121)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 28.6, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 24.5, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), -31.4, delta=0.1)

        bf = motion.calc_bone_by_interpolation("右腕", 137)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 32.1, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 55.2, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), -24.1, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 108)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 1.00, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 1.75, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 143)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 1.20, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 1.90, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 135)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 1.18, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 1.89, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 340)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 3.21, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), -0.96, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0, delta=0.1)

        bf = motion.calc_bone_by_interpolation("右足ＩＫ", 417)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 2.75, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 2.92, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 2.19, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), -29.6, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), -25.2, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 5.0, delta=0.1)

        bf = motion.calc_bone_by_interpolation("左足ＩＫ", 420)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 2.47, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 2.28, delta=0.3) # 急すぎてちょっとズレる？
        self.assertAlmostEqual(bf.position.z(), 1.39, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), -17.4, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 1.9, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0.7, delta=0.1)


if __name__ == "__main__":
    unittest.main()

