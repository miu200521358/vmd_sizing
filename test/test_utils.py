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
from utils import MBezierUtils, MServiceUtils # noqa
from utils.MLogger import MLogger # noqa
import itertools

logger = MLogger(__name__)


class MServiceUtilsSeparateTest(unittest.TestCase):

    def test_separate(self):
        MLogger.initialize(level=MLogger.TEST, is_file=True)
        logger = MLogger(__name__, level=MLogger.TEST)

        # motion = VmdReader("D:\\MMD\\MikuMikuDance_v926x64\\UserFile\\Motion\\ダンス_1人\\桃源恋歌配布用motion moka\\ノーマルTda式用0-2000.vmd").read_data()
        model = PmxReader("D:\\MMD\\MikuMikuDance_v926x64\\UserFile\\Model\\VOCALOID\\初音ミク\\Tda式初音ミク・アペンドVer1.10\\Tda式初音ミク・アペンド_Ver1.10.pmx", is_check=False).read_data()

        bone_axis_dict = {}
        for bone_name in ["左ひじ", "右ひじ"]:
            local_x_axis = model.get_local_x_axis("左ひじ")
            local_z_axis = MVector3D(0, 0, -1)
            local_y_axis = MVector3D.crossProduct(local_x_axis, local_z_axis).normalized()
            bone_axis_dict[bone_name] = {"x": local_x_axis, "y": local_y_axis, "z": local_z_axis}

        new_ik_qq = MQuaternion.fromEulerAngles(24.58152072747821, 135.9182003500461, 56.36785502950723)
        ik_bone = model.bones["左ひじ"]
        fno = 394

        x_qq, y_qq, z_qq, yz_qq = MServiceUtils.separate_local_qq(fno, ik_bone.name, new_ik_qq, bone_axis_dict[ik_bone.name]["x"])

        logger.debug(f"now: {new_ik_qq.toEulerAngles()} -> {(y_qq * x_qq * z_qq).toEulerAngles()}")
        logger.debug(f"now: x: {x_qq.toDegree()}, y: {y_qq.toDegree()}, z: {z_qq.toDegree()}")
        
        for (x_sign, y_sign, z_sign) in list(itertools.product((1, -1), (1, -1), (1, -1))):
            new_x_qq = MQuaternion.fromAxisAndAngle(x_qq.vector(), x_qq.toDegree() * x_sign)
            new_y_qq = MQuaternion.fromAxisAndAngle(y_qq.vector(), y_qq.toDegree() * y_sign)
            new_z_qq = MQuaternion.fromAxisAndAngle(z_qq.vector(), z_qq.toDegree() * z_sign)

            logger.debug(f"x: {x_sign}, y: {y_sign}, z: {z_sign} -> {(new_y_qq * new_x_qq * new_z_qq).toEulerAngles()}")

        self.assertTrue(True)


class MServiceUtilsTest(unittest.TestCase):

    def test_calc_relative_position01(self):
        motion = VmdReader("D:/MMD/MikuMikuDance_v926x64/UserFile/Motion/ダンス_1人/ドラマツルギー motion 配布用 moka/ドラマツルギー_0-500.vmd").read_data()
        model = PmxReader("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/初音ミク/Tda式デフォ服ミク_ver1.1 金子卵黄/Tda式初音ミク_デフォ服ver.pmx").read_data()

        # --------------
        links = model.create_link_2_top_one("グルーブ")
        
        # ---------
        trans_vs = MServiceUtils.calc_relative_position(model, links, motion, 407)
        self.assertEqual(4, len(trans_vs))

        # SIZING_ROOT_BONE
        self.assertAlmostEqual(trans_vs[0].x(), 0, delta=0.1)
        self.assertAlmostEqual(trans_vs[0].y(), 0, delta=0.1)
        self.assertAlmostEqual(trans_vs[0].z(), 0, delta=0.1)

        # 全ての親
        self.assertAlmostEqual(trans_vs[1].x(), 0, delta=0.1)
        self.assertAlmostEqual(trans_vs[1].y(), 0, delta=0.1)
        self.assertAlmostEqual(trans_vs[1].z(), 0, delta=0.1)
        
        # センター
        self.assertAlmostEqual(trans_vs[2].x(), 3.30 + links.get("センター").position.x(), delta=0.1)
        self.assertAlmostEqual(trans_vs[2].y(), 0.00 + links.get("センター").position.y(), delta=0.1)
        self.assertAlmostEqual(trans_vs[2].z(), -0.15 + links.get("センター").position.z(), delta=0.1)

        # グルーブ
        self.assertAlmostEqual(trans_vs[3].x(), 0 + links.get("グルーブ").position.x() - links.get("センター").position.x(), delta=0.1)
        self.assertAlmostEqual(trans_vs[3].y(), -4.40 + links.get("グルーブ").position.y() - links.get("センター").position.y(), delta=0.1)
        self.assertAlmostEqual(trans_vs[3].z(), 0 + links.get("グルーブ").position.z() - links.get("センター").position.z(), delta=0.1)
        
        # ---------
        trans_vs = MServiceUtils.calc_relative_position(model, links, motion, 420)
        self.assertEqual(4, len(trans_vs))

        # SIZING_ROOT_BONE
        self.assertAlmostEqual(trans_vs[0].x(), 0, delta=0.1)
        self.assertAlmostEqual(trans_vs[0].y(), 0, delta=0.1)
        self.assertAlmostEqual(trans_vs[0].z(), 0, delta=0.1)

        # 全ての親
        self.assertAlmostEqual(trans_vs[1].x(), 0, delta=0.1)
        self.assertAlmostEqual(trans_vs[1].y(), 0, delta=0.1)
        self.assertAlmostEqual(trans_vs[1].z(), 0, delta=0.1)
        
        # センター
        self.assertAlmostEqual(trans_vs[2].x(), 3.21 + links.get("センター").position.x(), delta=0.1)
        self.assertAlmostEqual(trans_vs[2].y(), 0.00 + links.get("センター").position.y(), delta=0.1)
        self.assertAlmostEqual(trans_vs[2].z(), 2.77 + links.get("センター").position.z(), delta=0.1)

        # グルーブ
        self.assertAlmostEqual(trans_vs[3].x(), 0 + links.get("グルーブ").position.x() - links.get("センター").position.x(), delta=0.1)
        self.assertAlmostEqual(trans_vs[3].y(), -0.22 + links.get("グルーブ").position.y() - links.get("センター").position.y(), delta=0.1)
        self.assertAlmostEqual(trans_vs[3].z(), 0 + links.get("グルーブ").position.z() - links.get("センター").position.z(), delta=0.1)

        # --------------
        links = model.create_link_2_top_one("右足ＩＫ")
        
        # ---------
        trans_vs = MServiceUtils.calc_relative_position(model, links, motion, 415)
        self.assertEqual(4, len(trans_vs))

        # SIZING_ROOT_BONE
        self.assertAlmostEqual(trans_vs[0].x(), 0, delta=0.1)
        self.assertAlmostEqual(trans_vs[0].y(), 0, delta=0.1)
        self.assertAlmostEqual(trans_vs[0].z(), 0, delta=0.1)

        # 全ての親
        self.assertAlmostEqual(trans_vs[1].x(), 0, delta=0.1)
        self.assertAlmostEqual(trans_vs[1].y(), 0, delta=0.1)
        self.assertAlmostEqual(trans_vs[1].z(), 0, delta=0.1)
        
        # 右足IK親
        self.assertAlmostEqual(trans_vs[2].x(), 0 + links.get("右足IK親").position.x(), delta=0.1)
        self.assertAlmostEqual(trans_vs[2].y(), 0 + links.get("右足IK親").position.y(), delta=0.1)
        self.assertAlmostEqual(trans_vs[2].z(), 0 + links.get("右足IK親").position.z(), delta=0.1)

        # 右足ＩＫ
        self.assertAlmostEqual(trans_vs[3].x(), 2.43 + links.get("右足ＩＫ").position.x() - links.get("右足IK親").position.x(), delta=0.1)
        self.assertAlmostEqual(trans_vs[3].y(), 0.00 + links.get("右足ＩＫ").position.y() - links.get("右足IK親").position.y(), delta=0.1)
        self.assertAlmostEqual(trans_vs[3].z(), 1.52 + links.get("右足ＩＫ").position.z() - links.get("右足IK親").position.z(), delta=0.1)
                
        # ---------
        trans_vs = MServiceUtils.calc_relative_position(model, links, motion, 418)
        self.assertEqual(4, len(trans_vs))

        # SIZING_ROOT_BONE
        self.assertAlmostEqual(trans_vs[0].x(), 0, delta=0.1)
        self.assertAlmostEqual(trans_vs[0].y(), 0, delta=0.1)
        self.assertAlmostEqual(trans_vs[0].z(), 0, delta=0.1)

        # 全ての親
        self.assertAlmostEqual(trans_vs[1].x(), 0, delta=0.1)
        self.assertAlmostEqual(trans_vs[1].y(), 0, delta=0.1)
        self.assertAlmostEqual(trans_vs[1].z(), 0, delta=0.1)
        
        # 右足IK親
        self.assertAlmostEqual(trans_vs[2].x(), 0 + links.get("右足IK親").position.x(), delta=0.1)
        self.assertAlmostEqual(trans_vs[2].y(), 0 + links.get("右足IK親").position.y(), delta=0.1)
        self.assertAlmostEqual(trans_vs[2].z(), 0 + links.get("右足IK親").position.z(), delta=0.1)

        # 右足ＩＫ
        self.assertAlmostEqual(trans_vs[3].x(), 2.92 + links.get("右足ＩＫ").position.x() - links.get("右足IK親").position.x(), delta=0.1)
        self.assertAlmostEqual(trans_vs[3].y(), 4.17 + links.get("右足ＩＫ").position.y() - links.get("右足IK親").position.y(), delta=0.1)
        self.assertAlmostEqual(trans_vs[3].z(), 2.45 + links.get("右足ＩＫ").position.z() - links.get("右足IK親").position.z(), delta=0.1)

    def test_calc_relative_rotation01(self):
        motion = VmdReader("D:/MMD/MikuMikuDance_v926x64/UserFile/Motion/ダンス_1人/ドラマツルギー motion 配布用 moka/ドラマツルギー_0-500.vmd").read_data()
        model = PmxReader("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/初音ミク/Tda式デフォ服ミク_ver1.1 金子卵黄/Tda式初音ミク_デフォ服ver.pmx").read_data()

        # --------------
        links = model.create_link_2_top_one("右手首")
        
        # ---------
        add_qs = MServiceUtils.calc_relative_rotation(model, links, motion, 414)

        # SIZING_ROOT_BONE
        self.assertAlmostEqual(add_qs[0].toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[0].toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[0].toEulerAngles4MMD().z(), 0, delta=0.1)

        # 全ての親
        self.assertAlmostEqual(add_qs[1].toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[1].toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[1].toEulerAngles4MMD().z(), 0, delta=0.1)

        # センター
        self.assertAlmostEqual(add_qs[2].toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[2].toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[2].toEulerAngles4MMD().z(), 0, delta=0.1)

        # グルーブ
        self.assertAlmostEqual(add_qs[3].toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[3].toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[3].toEulerAngles4MMD().z(), 0, delta=0.1)

        # 腰
        self.assertAlmostEqual(add_qs[4].toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[4].toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[4].toEulerAngles4MMD().z(), 0, delta=0.1)

        # 上半身
        self.assertAlmostEqual(add_qs[5].toEulerAngles4MMD().x(), -13.2, delta=0.1)
        self.assertAlmostEqual(add_qs[5].toEulerAngles4MMD().y(), -5.0, delta=0.1)
        self.assertAlmostEqual(add_qs[5].toEulerAngles4MMD().z(), 1.1, delta=0.1)

        # 上半身2
        self.assertAlmostEqual(add_qs[6].toEulerAngles4MMD().x(), -9.1, delta=0.1)
        self.assertAlmostEqual(add_qs[6].toEulerAngles4MMD().y(), -7.1, delta=0.1)
        self.assertAlmostEqual(add_qs[6].toEulerAngles4MMD().z(), 3.7, delta=0.1)

        # 首根元
        self.assertAlmostEqual(add_qs[7].toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[7].toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[7].toEulerAngles4MMD().z(), 0, delta=0.1)

        # 右肩P
        self.assertAlmostEqual(add_qs[8].toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[8].toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[8].toEulerAngles4MMD().z(), 0, delta=0.1)

        # 右肩
        self.assertAlmostEqual(add_qs[9].toEulerAngles4MMD().x(), -1.7, delta=0.1)
        self.assertAlmostEqual(add_qs[9].toEulerAngles4MMD().y(), 14.4, delta=0.1)
        self.assertAlmostEqual(add_qs[9].toEulerAngles4MMD().z(), 13.5, delta=0.1)

        # 右肩C
        self.assertAlmostEqual(add_qs[10].toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[10].toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[10].toEulerAngles4MMD().z(), 0, delta=0.1)

        # 右腕
        self.assertAlmostEqual(add_qs[11].toEulerAngles4MMD().x(), -5.0, delta=0.1)
        self.assertAlmostEqual(add_qs[11].toEulerAngles4MMD().y(), 58.9, delta=0.1)
        self.assertAlmostEqual(add_qs[11].toEulerAngles4MMD().z(), 11.5, delta=0.1)

        # 右腕捩
        self.assertAlmostEqual(add_qs[12].toEulerAngles4MMD().x(), -0.1, delta=0.1)
        self.assertAlmostEqual(add_qs[12].toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[12].toEulerAngles4MMD().z(), 0, delta=0.1)

        # 右ひじ
        self.assertAlmostEqual(add_qs[13].toEulerAngles4MMD().x(), 30.6, delta=0.1)
        self.assertAlmostEqual(add_qs[13].toEulerAngles4MMD().y(), 48.3, delta=0.1)
        self.assertAlmostEqual(add_qs[13].toEulerAngles4MMD().z(), 14.0, delta=0.1)

        # 右ひじ下（スルー）
        self.assertAlmostEqual(add_qs[14].toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[14].toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[14].toEulerAngles4MMD().z(), 0, delta=0.1)

        # 右手捩
        self.assertAlmostEqual(add_qs[15].toEulerAngles4MMD().x(), -7.1, delta=0.1)
        self.assertAlmostEqual(add_qs[15].toEulerAngles4MMD().y(), 5.4, delta=0.1)
        self.assertAlmostEqual(add_qs[15].toEulerAngles4MMD().z(), -0.2, delta=0.1)

        # 右手首
        self.assertAlmostEqual(add_qs[16].toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[16].toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(add_qs[16].toEulerAngles4MMD().z(), -37.8, delta=0.1)

    def test_calc_global_pos01(self):
        motion = VmdReader("D:/MMD/MikuMikuDance_v926x64/UserFile/Motion/ダンス_1人/ドラマツルギー motion 配布用 moka/ドラマツルギー_0-500.vmd").read_data()
        model = PmxReader("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/初音ミク/Tda式デフォ服ミク_ver1.1 金子卵黄/Tda式初音ミク_デフォ服ver.pmx").read_data()

        # --------------
        links = model.create_link_2_top_one("グルーブ")

        # ---------
        pos_dic = MServiceUtils.calc_global_pos(model, links, motion, 420)
        self.assertEqual(4, len(pos_dic.keys()))

        # SIZING_ROOT_BONE
        print(pos_dic["SIZING_ROOT_BONE"])
        self.assertAlmostEqual(pos_dic["SIZING_ROOT_BONE"].x(), 0, delta=0.1)
        self.assertAlmostEqual(pos_dic["SIZING_ROOT_BONE"].y(), 0, delta=0.1)
        self.assertAlmostEqual(pos_dic["SIZING_ROOT_BONE"].z(), 0, delta=0.1)

        # 全ての親
        print(pos_dic["全ての親"])
        self.assertAlmostEqual(pos_dic["全ての親"].x(), 0, delta=0.1)
        self.assertAlmostEqual(pos_dic["全ての親"].y(), 0, delta=0.1)
        self.assertAlmostEqual(pos_dic["全ての親"].z(), 0, delta=0.1)
        
        # センター
        print(pos_dic["センター"])
        self.assertAlmostEqual(pos_dic["センター"].x(), 3.2, delta=0.1)
        self.assertAlmostEqual(pos_dic["センター"].y(), 8.4, delta=0.1)
        self.assertAlmostEqual(pos_dic["センター"].z(), 2.7, delta=0.1)

        # グルーブ
        print(pos_dic["グルーブ"])
        self.assertAlmostEqual(pos_dic["グルーブ"].x(), 3.2, delta=0.1)
        self.assertAlmostEqual(pos_dic["グルーブ"].y(), 8.4, delta=0.1)
        self.assertAlmostEqual(pos_dic["グルーブ"].z(), 2.7, delta=0.1)

        # --------------
        links = model.create_link_2_top_one("左足ＩＫ")

        # ---------
        pos_dic = MServiceUtils.calc_global_pos(model, links, motion, 420)
        self.assertEqual(4, len(pos_dic.keys()))

        # SIZING_ROOT_BONE
        print(pos_dic["SIZING_ROOT_BONE"])
        self.assertAlmostEqual(pos_dic["SIZING_ROOT_BONE"].x(), 0, delta=0.1)
        self.assertAlmostEqual(pos_dic["SIZING_ROOT_BONE"].y(), 0, delta=0.1)
        self.assertAlmostEqual(pos_dic["SIZING_ROOT_BONE"].z(), 0, delta=0.1)

        # 全ての親
        print(pos_dic["全ての親"])
        self.assertAlmostEqual(pos_dic["全ての親"].x(), 0, delta=0.1)
        self.assertAlmostEqual(pos_dic["全ての親"].y(), 0, delta=0.1)
        self.assertAlmostEqual(pos_dic["全ての親"].z(), 0, delta=0.1)
        
        # 左足IK親
        print(pos_dic["左足IK親"])
        self.assertAlmostEqual(pos_dic["左足IK親"].x(), 1.0, delta=0.1)
        self.assertAlmostEqual(pos_dic["左足IK親"].y(), 0, delta=0.1)
        self.assertAlmostEqual(pos_dic["左足IK親"].z(), 0.7, delta=0.1)

        # 右足IK親
        print(pos_dic["左足ＩＫ"])
        self.assertAlmostEqual(pos_dic["左足ＩＫ"].x(), 3.5, delta=0.1)
        self.assertAlmostEqual(pos_dic["左足ＩＫ"].y(), 3.9, delta=0.1)
        self.assertAlmostEqual(pos_dic["左足ＩＫ"].z(), 2.1, delta=0.1)

        # --------------
        links = model.create_link_2_top_one("右手首")
        
        # ---------
        pos_dic = MServiceUtils.calc_global_pos(model, links, motion, 420)
        # self.assertEqual(17, len(pos_dic.keys()))

        # SIZING_ROOT_BONE
        print(pos_dic["SIZING_ROOT_BONE"])
        self.assertAlmostEqual(pos_dic["SIZING_ROOT_BONE"].x(), 0, delta=0.1)
        self.assertAlmostEqual(pos_dic["SIZING_ROOT_BONE"].y(), 0, delta=0.1)
        self.assertAlmostEqual(pos_dic["SIZING_ROOT_BONE"].z(), 0, delta=0.1)

        # 全ての親
        print(pos_dic["全ての親"])
        self.assertAlmostEqual(pos_dic["全ての親"].x(), 0, delta=0.1)
        self.assertAlmostEqual(pos_dic["全ての親"].y(), 0, delta=0.1)
        self.assertAlmostEqual(pos_dic["全ての親"].z(), 0, delta=0.1)
        
        # センター
        print(pos_dic["センター"])
        self.assertAlmostEqual(pos_dic["センター"].x(), 3.2, delta=0.1)
        self.assertAlmostEqual(pos_dic["センター"].y(), 8.4, delta=0.1)
        self.assertAlmostEqual(pos_dic["センター"].z(), 2.7, delta=0.1)

        # グルーブ
        print(pos_dic["グルーブ"])
        self.assertAlmostEqual(pos_dic["グルーブ"].x(), 3.2, delta=0.1)
        self.assertAlmostEqual(pos_dic["グルーブ"].y(), 8.4, delta=0.1)
        self.assertAlmostEqual(pos_dic["グルーブ"].z(), 2.7, delta=0.1)

        # 腰
        self.assertAlmostEqual(pos_dic["腰"].x(), 3.2, delta=0.1)
        self.assertAlmostEqual(pos_dic["腰"].y(), 12.1, delta=0.1)
        self.assertAlmostEqual(pos_dic["腰"].z(), 3.0, delta=0.1)

        # 上半身
        self.assertAlmostEqual(pos_dic["上半身"].x(), 3.2, delta=0.1)
        self.assertAlmostEqual(pos_dic["上半身"].y(), 13.0, delta=0.1)
        self.assertAlmostEqual(pos_dic["上半身"].z(), 2.2, delta=0.1)

        # 上半身2
        self.assertAlmostEqual(pos_dic["上半身2"].x(), 3.25, delta=0.1)
        self.assertAlmostEqual(pos_dic["上半身2"].y(), 14.0, delta=0.1)
        self.assertAlmostEqual(pos_dic["上半身2"].z(), 2.25, delta=0.1)

        # 右肩P
        self.assertAlmostEqual(pos_dic["右肩P"].x(), 3.03, delta=0.1)
        self.assertAlmostEqual(pos_dic["右肩P"].y(), 16.26, delta=0.1)
        self.assertAlmostEqual(pos_dic["右肩P"].z(), 2.28, delta=0.1)

        # 右肩
        self.assertAlmostEqual(pos_dic["右肩"].x(), 3.03, delta=0.1)
        self.assertAlmostEqual(pos_dic["右肩"].y(), 16.26, delta=0.1)
        self.assertAlmostEqual(pos_dic["右肩"].z(), 2.28, delta=0.1)

        # # 右肩C
        # self.assertAlmostEqual(pos_dic["右肩C"].x(), 3.03, delta=0.1)
        # self.assertAlmostEqual(pos_dic["右肩C"].y(), 16.26, delta=0.1)
        # self.assertAlmostEqual(pos_dic["右肩C"].z(), 2.28, delta=0.1)

        # 右腕
        self.assertAlmostEqual(pos_dic["右腕"].x(), 2.15, delta=0.1)
        self.assertAlmostEqual(pos_dic["右腕"].y(), 16.32, delta=0.1)
        self.assertAlmostEqual(pos_dic["右腕"].z(), 2.39, delta=0.1)

        # 右腕捩
        self.assertAlmostEqual(pos_dic["右腕捩"].x(), 0.66, delta=0.1)
        self.assertAlmostEqual(pos_dic["右腕捩"].y(), 15.64, delta=0.1)
        self.assertAlmostEqual(pos_dic["右腕捩"].z(), 2.19, delta=0.1)

        # 右ひじ
        self.assertAlmostEqual(pos_dic["右ひじ"].x(), -0.31, delta=0.1)
        self.assertAlmostEqual(pos_dic["右ひじ"].y(), 15.17, delta=0.1)
        self.assertAlmostEqual(pos_dic["右ひじ"].z(), 2.03, delta=0.1)

        # 右手捩
        self.assertAlmostEqual(pos_dic["右手捩"].x(), 0.21, delta=0.1)
        self.assertAlmostEqual(pos_dic["右手捩"].y(), 14.36, delta=0.1)
        self.assertAlmostEqual(pos_dic["右手捩"].z(), 0.95, delta=0.1)

        # 右手首
        self.assertAlmostEqual(pos_dic["右手首"].x(), 0.56, delta=0.1)
        self.assertAlmostEqual(pos_dic["右手首"].y(), 13.83, delta=0.1)
        self.assertAlmostEqual(pos_dic["右手首"].z(), 0.23, delta=0.1)
                

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
    
    def test_round_integer(self):
        self.assertEqual(MBezierUtils.round_integer(3.56), 4)
        self.assertEqual(MBezierUtils.round_integer(3.52), 4)
        self.assertEqual(MBezierUtils.round_integer(3.55), 4)
        self.assertEqual(MBezierUtils.round_integer(3.48), 3)
        self.assertEqual(MBezierUtils.round_integer(3.12), 3)

    def test_round_bezier_mmd(self):
        v = MBezierUtils.round_bezier_mmd(MVector2D(0.56, 0))
        print("v: %s" % v)
        self.assertAlmostEqual(v.x(), 71, delta=0.1)
        self.assertAlmostEqual(v.y(), 0, delta=0.1)
    
    def test_scale_bezier_point(self):
        v = MBezierUtils.scale_bezier_point(MVector2D(1, 2), MVector2D(3, 4), MVector2D())
        print("v: %s" % v)
        self.assertAlmostEqual(v.x(), 0, delta=0.1)
        self.assertAlmostEqual(v.y(), 0, delta=0.1)

    def test_scale_bezier(self):
        s1, s2, s3, s4 = MBezierUtils.scale_bezier(MVector2D(0.2, 0.7), MVector2D(0.3, -0.5), MVector2D(0.4, 1.2), MVector2D(1.2, 2))
        print("s1: %s" % s1)
        print("s2: %s" % s2)
        print("s3: %s" % s3)
        print("s4: %s" % s4)

    def test_split_bezier(self):
        x, y, t, before_bz, after_bz = MBezierUtils.split_bezier(127, 0, 0, 127, 0, 3, 12)
        print("x: %s" % x)
        print("y: %s" % y)
        print("t: %s" % t)
        print("before_bz[0]: %s" % before_bz[0])
        print("before_bz[1]: %s" % before_bz[1])
        print("before_bz[2]: %s" % before_bz[2])
        print("before_bz[3]: %s" % before_bz[3])
        print("after_bz[0]: %s" % after_bz[0])
        print("after_bz[1]: %s" % after_bz[1])
        print("after_bz[2]: %s" % after_bz[2])
        print("after_bz[3]: %s" % after_bz[3])

        self.assertTrue(MBezierUtils.is_fit_bezier_mmd(before_bz))
        self.assertFalse(MBezierUtils.is_fit_bezier_mmd(after_bz))

    def test_split_bezier_mmd(self):
        x, y, t, is_fit_before_bz, is_fit_after_bz, before_bz, after_bz = MBezierUtils.split_bezier_mmd(127, 0, 0, 127, 0, 8, 15)
        
        print("x: %s" % x)
        print("y: %s" % y)
        print("t: %s" % t)
        print("is_fit_before_bz: %s" % is_fit_before_bz)
        print("is_fit_after_bz: %s" % is_fit_after_bz)
        print("before_bz[0]: %s" % before_bz[0])
        print("before_bz[1]: %s" % before_bz[1])
        print("before_bz[2]: %s" % before_bz[2])
        print("before_bz[3]: %s" % before_bz[3])
        print("after_bz[0]: %s" % after_bz[0])
        print("after_bz[1]: %s" % after_bz[1])
        print("after_bz[2]: %s" % after_bz[2])
        print("after_bz[3]: %s" % after_bz[3])

        self.assertFalse(is_fit_before_bz)
        self.assertTrue(is_fit_after_bz)


if __name__ == "__main__":
    unittest.main()

