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
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 27.2, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 16.7, delta=0.1)
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
        self.assertAlmostEqual(bf.position.y(), 2.28, delta=0.1)  # 急すぎてちょっとズレる？
        self.assertAlmostEqual(bf.position.z(), 1.39, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), -17.4, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 1.9, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0.7, delta=0.1)

    def test_calc_bone_by_interpolation_02(self):
        motion = VmdReader(u"test/data/補間曲線テスト01.vmd").read_data()

        bf = motion.calc_bone_by_interpolation("センター", 0)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 30)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 3.149999619, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.700000048, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 6.549999237, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.99999809, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 29.99999809, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 39.99999619, delta=0.1)
           
        bf = motion.calc_bone_by_interpolation("センター", 1)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.001208697, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0.968675971, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0.140791774, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 3.937894821, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 3.196340561, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 4.818815231, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 2)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.002522668, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 1.693461657, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0.281450838, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 7.193121433, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 6.322115898, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 9.302928925, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 3)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.003890587, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 2.232982159, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0.424674749, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 9.85978508, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 9.31887722, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 13.44856834, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 4)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.005370149, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 2.633183956, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0.570137918, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 12.02462006, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 12.14039612, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 17.24782372, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 5)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.006965585, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 2.928799868, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0.717516661, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 13.76086807, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 14.74285889, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 20.68190575, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 6)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.008743186, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.145775557, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0.866490364, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 15.14802742, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 17.11488724, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 23.76445007, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 7)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.010647158, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.304029226, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 1.016742468, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 16.24446678, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 19.23688316, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 26.49024963, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 8)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.012749105, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.419059038, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 1.17042768, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 17.10861397, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 21.11429405, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 28.88066292, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 9)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.015058434, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.502044439, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 1.327022076, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 17.78543854, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 22.75117111, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 30.95079803, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 10)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.017584471, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.561547279, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 1.48600626, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 18.31396294, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 24.16161156, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 32.72537231, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 11)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.020336455, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.60392642, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 1.646867275, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 18.72516251, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 25.36146927, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 34.22903442, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 12)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.023404857, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.633889437, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 1.811258435, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.04433823, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 26.37034035, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 35.48951721, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 13)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.026806016, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.654931784, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 1.978454709, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.29050636, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 27.20512962, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 36.53007889, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 14)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.030646885, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.669575453, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 2.147742748, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.47965622, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 27.88671303, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 37.3781662, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 15)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.035049777, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.679668665, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 2.322246552, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.6239357, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 28.43400192, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 38.05823135, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 16)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.040050752, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.686569452, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 2.500795364, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.73313141, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 28.86619377, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 38.59472275, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 17)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.045795817, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.691236973, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 2.682239056, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.8146801, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 29.20017242, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 39.00898361, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 18)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.052451514, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.694359303, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 2.868748426, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.87472343, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 29.45277596, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 39.32213211, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 19)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.060336307, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.696423769, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 3.06182003, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.91801453, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 29.63866615, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 39.55247498, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 20)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.069826499, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.697768688, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 3.260805607, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.9483757, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 29.77101898, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 39.71643829, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 21)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.081365548, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.698632717, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 3.466094971, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.96894073, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 29.86164474, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 39.82868195, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 22)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.095816322, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.699179411, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 3.678640604, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.98226357, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 29.92076111, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 39.90188217, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 23)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.114430249, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.699518442, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 3.900592804, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.99040031, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 29.95703316, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 39.94680023, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 24)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.139199123, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.699724674, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 4.133212566, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.99503326, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 29.97775269, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 39.97245026, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 25)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.173660755, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.699846983, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 4.378130913, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.99503326, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 29.97775269, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 39.97245026, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 26)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.225477695, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.699917555, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 4.638724804, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.99503326, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 29.97775269, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 39.97245026, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 27)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.312407255, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.699957132, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 4.919608116, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.99503326, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 29.97775269, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 39.97245026, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 28)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.49179405, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.699978352, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 5.227443695, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.99503326, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 29.97775269, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 39.97245026, delta=0.1)

        bf = motion.calc_bone_by_interpolation("センター", 29)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 1.843770266, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 3.69998908, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 5.572102547, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 19.99503326, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 29.97775269, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 39.97245026, delta=0.1)


if __name__ == "__main__":
    unittest.main()

