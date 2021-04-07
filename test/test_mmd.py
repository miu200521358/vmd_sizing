# -*- coding: utf-8 -*-
#
import numpy as np
import glob
import _pickle as cPickle
from datetime import datetime
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
from mmd.VmdWriter import VmdWriter # noqa
from mmd.PmxData import PmxModel, Vertex, Material, Bone, Morph, DisplaySlot, RigidBody, Joint, Sdef # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MMath import MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MOptionsDataSet # noqa
from module.MParams import BoneLinks # noqa
from utils import MBezierUtils, MServiceUtils # noqa
from utils.MException import SizingException # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__, level=1)


class ModelNameTest(unittest.TestCase):

    def test_model_name(self):
        MLogger.initialize(level=MLogger.WARNING, is_file=True)
        logger = MLogger(__name__, level=MLogger.WARNING)

        for pmx_path in glob.glob("D:\\MMD\\MikuMikuDance_v926x64\\UserFile\\Model\\ヘタリア\\**\\*.pmx", recursive=True):
            reader = PmxReader(pmx_path, is_check=False)
            model = reader.read_data()
            if "プロイセン" in model.name:
                logger.warning("☆プロイセンモデル: %s, path: %s", model.name, pmx_path)

        self.assertTrue(True)



class MediapipeTest(unittest.TestCase):

    def test_init(self):
        MLogger.initialize(level=MLogger.WARNING, is_file=True)
        logger = MLogger(__name__, level=MLogger.WARNING)

        pmx_path = "D:\\MMD\\MikuMikuDance_v926x64\\UserFile\\Model\\初音ミクVer2 準標準.pmx"
        reader = PmxReader(pmx_path, is_check=False)
        model = reader.read_data()

        reader = VmdReader("E:\\MMD\\MikuMikuDance_v926x64\\Work\\202101_hand\\init\\init_avi_20210125_060727\\motion\\output_20210125_060729_no000.vmd")
        motion = reader.read_data()

        for bone_name, bf_list in motion.bones.items():
            for fno, bf in bf_list.items():
                euler = bf.rotation.toEulerAngles()
                logger.warning(f'{bf.name}: MQuaternion.fromEulerAngles({euler.x()}, {euler.y()}, {euler.z()})')
                bf.rotation = bf.rotation.inverted()

        data_set = MOptionsDataSet(motion, model, model, "E:\\MMD\\MikuMikuDance_v926x64\\Work\\202101_hand\\init\\init_avi_20210125_060727\\motion\\output_20210125_060729_no000_inverted.vmd")
        writer = VmdWriter(data_set)
        writer.write()

        self.assertTrue(True)



class HomeHarukaTest(unittest.TestCase):

    def test_awaodori(self):
        MLogger.initialize(level=MLogger.WARNING, is_file=True)
        logger = MLogger(__name__, level=MLogger.WARNING)

        pmx_path = "D:\\MMD\\MikuMikuDance_v926x64\\UserFile\\Model\\ゲーム\\アイドルマスター\\ほめ春香 マシシP\\ほめ春香さんver1_masisi_準標準.pmx"
        reader = PmxReader(pmx_path, is_check=False)
        model = reader.read_data()

        reader = VmdReader("D:\\MMD\\MikuMikuDance_v926x64\\Work\\2021\\20210201_ホメ春香\\女踊りジグザグ右足始まり0000-1440f.vmd")
        motion = reader.read_data()

        for bone_name, bf_list in motion.bones.items():
            for fno, bf in bf_list.items():
                x_qq, y_qq, z_qq, _ = MServiceUtils.separate_local_qq(fno, bone_name, bf.rotation, model.get_local_x_axis(bone_name))
                bf.rotation = y_qq.inverted() * x_qq.inverted() * z_qq.inverted()

        data_set = MOptionsDataSet(motion, model, model, "D:\\MMD\\MikuMikuDance_v926x64\\Work\\2021\\20210201_ホメ春香\\女踊りジグザグ右足始まり0000-1440f_ホメ春香.vmd")
        writer = VmdWriter(data_set)
        writer.write()

        self.assertTrue(True)


class MorphDataTest(unittest.TestCase):

    def test_bone_morph_check(self):
        MLogger.initialize(level=MLogger.WARNING, is_file=True)
        logger = MLogger(__name__, level=MLogger.WARNING)

        for pmx_path in glob.glob("D:\\MMD\\MikuMikuDance_v926x64\\UserFile\\Model\\刀剣乱舞\\**\\*.pmx", recursive=True):
            reader = PmxReader(pmx_path, is_check=False)
            model = reader.read_data()
            is_morph = False
            for morph_name, morph in model.morphs.items():
                if morph.morph_type == 2:
                    logger.warning("☆ボーンモーフありモデル: %s, %s, path: %s", morph_name, morph.panel, pmx_path)
                    is_morph = True
                    break
            if not is_morph:
                logger.warning("ボーンモーフなし: %s", pmx_path)

        self.assertTrue(True)


class NormalTest(unittest.TestCase):
    def test_normal_bone(self):
        MLogger.initialize(level=MLogger.WARNING, is_file=True)
        logger = MLogger(__name__, level=MLogger.WARNING)
        
        pmx_path = "D:\\MMD\\MikuMikuDance_v926x64\\UserFile\\Model\\ゲーム\\Neir\\eve_v100_pmx\\eve_足先EX.pmx"
        reader = PmxReader(pmx_path, is_check=False)
        model = reader.read_data()
        print(';Bone,ボーン名,ボーン名(英),変形階層,物理後(0/1),位置_x,位置_y,位置_z,回転(0/1),移動(0/1),IK(0/1),表示(0/1),操作(0/1),親ボーン名,表示先(0:オフセット/1:ボーン),表示先ボーン名,オフセット_x,オフセット_y,オフセット_z,ローカル付与(0/1),回転付与(0/1),移動付与(0/1),付与率,付与親名,軸制限(0/1),制限軸_x,制限軸_y,制限軸_z,ローカル軸(0/1),ローカルX軸_x,ローカルX軸_y,ローカルX軸_z,ローカルZ軸_x,ローカルZ軸_y,ローカルZ軸_z,外部親(0/1),外部親Key,IKTarget名,IKLoop,IK単位角[deg]')

        for bone_name in ["下半身","上半身","上半身2","首","頭"]:
        # for bone_name in ["下半身","左足","左ひざ","左足首","右足","右ひざ","右足首","上半身","上半身2","左肩","左腕","左ひじ","左手首","右肩","右腕","右ひじ","右手首","首","頭"]:
            bone = model.bones[bone_name]
            
            local_z_axis = model.get_local_x_axis(bone_name)
            local_x_axis = MVector3D.crossProduct(MVector3D(0, 0, 1), local_z_axis).normalized()
            local_y_axis = MVector3D.crossProduct(local_x_axis, local_z_axis).normalized()

            x_bone = bone.copy()
            x_bone.name = f'{bone_name}X'
            x_bone.fixed_axis = local_x_axis
            x_bone.local_x_vector = local_x_axis
            x_bone.local_z_vector = MVector3D.crossProduct(MVector3D(0, 0, 1), local_x_axis).normalized()

            y_bone = bone.copy()
            y_bone.name = f'{bone_name}Y'
            y_bone.fixed_axis = local_y_axis
            y_bone.local_x_vector = local_y_axis
            y_bone.local_z_vector = MVector3D.crossProduct(MVector3D(0, 0, 1), local_y_axis).normalized()

            z_bone = bone.copy()
            z_bone.name = f'{bone_name}Z'
            z_bone.fixed_axis = local_z_axis
            z_bone.local_x_vector = local_z_axis
            z_bone.local_z_vector = MVector3D.crossProduct(MVector3D(0, 0, 1), local_z_axis).normalized()

            print(f'Bone,"{x_bone.name}","",0,0,{x_bone.position.x()},{x_bone.position.y()},{x_bone.position.z()},1,0,0,1,1,{model.bone_indexes[bone.parent_index]},1,-1,0,0,0,0,0,0,1,,1,{x_bone.fixed_axis.x()},{x_bone.fixed_axis.y()},{x_bone.fixed_axis.z()},1,{bone.local_x_vector.x()},{bone.local_x_vector.y()},{bone.local_x_vector.z()},{bone.local_z_vector.x()},{bone.local_z_vector.y()},{bone.local_z_vector.z()},0,0,"",0,0')
            print(f'Bone,"{y_bone.name}","",0,0,{y_bone.position.x()},{y_bone.position.y()},{y_bone.position.z()},1,0,0,1,1,{x_bone.name},1,-1,0,0,0,0,0,0,1,,1,{y_bone.fixed_axis.x()},{y_bone.fixed_axis.y()},{y_bone.fixed_axis.z()},1,{bone.local_x_vector.x()},{bone.local_x_vector.y()},{bone.local_x_vector.z()},{bone.local_z_vector.x()},{bone.local_z_vector.y()},{bone.local_z_vector.z()},0,0,"",0,0')
            print(f'Bone,"{z_bone.name}","",0,0,{z_bone.position.x()},{z_bone.position.y()},{z_bone.position.z()},1,0,0,1,1,{y_bone.name},1,-1,0,0,0,0,0,0,1,,1,{z_bone.fixed_axis.x()},{z_bone.fixed_axis.y()},{z_bone.fixed_axis.z()},1,{bone.local_x_vector.x()},{bone.local_x_vector.y()},{bone.local_x_vector.z()},{bone.local_z_vector.x()},{bone.local_z_vector.y()},{bone.local_z_vector.z()},0,0,"",0,0')
            print(f'Bone,"{bone.name}","",0,0,{bone.position.x()},{bone.position.y()},{bone.position.z()},1,0,0,1,1,{z_bone.name},1,-1,0,0,0,0,0,0,1,,0,{bone.fixed_axis.x()},{bone.fixed_axis.y()},{bone.fixed_axis.z()},1,{bone.local_x_vector.x()},{bone.local_x_vector.y()},{bone.local_x_vector.z()},{bone.local_z_vector.x()},{bone.local_z_vector.y()},{bone.local_z_vector.z()},0,0,"",0,0')

        self.assertTrue(True)


class SdefDataTest(unittest.TestCase):

    def test_sdef_check(self):
        MLogger.initialize(level=MLogger.WARNING, is_file=True)
        logger = MLogger(__name__, level=MLogger.WARNING)

        for pmx_path in glob.glob("D:\\MMD\\MikuMikuDance_v926x64\\UserFile\\Model\\VOCALOID\\**\\*.pmx", recursive=True):
            reader = PmxReader(pmx_path, is_check=False)
            model = reader.read_data()
            is_sdef = False
            for bone_idx, vertices in model.vertices.items():
                for vertex in vertices:
                    if type(vertex.deform) is Sdef:
                        logger.warning("SDEFありモデル: %s, idx: %s, bone: %s", pmx_path, vertex.index, model.bone_indexes[bone_idx])
                        is_sdef = True
                        break
                logger.debug("SDEFなし: %s", pmx_path)

        self.assertTrue(True)


class PmxDataTest(unittest.TestCase):

    def test_get_wrist_vertex_01(self):
        model = PmxReader("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/_VMDサイジング/8頭身審神者 猫のしもべ/8頭身審神者3_軸制限無し.pmx").read_data()
        
        left_wrist_vertex = model.get_wrist_vertex("左")
        print(left_wrist_vertex)
        self.assertIsNotNone(left_wrist_vertex)

        right_wrist_vertex = model.get_wrist_vertex("右")
        print(right_wrist_vertex)
        self.assertIsNotNone(right_wrist_vertex)

    def test_get_wrist_vertex_02(self):
        model = PmxReader("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/刀剣乱舞/047_五虎退/五虎退 りっつ式 v1.42/五虎退.pmx").read_data()
        
        left_wrist_vertex = model.get_wrist_vertex("左")
        print(left_wrist_vertex)
        self.assertIsNotNone(left_wrist_vertex)

        right_wrist_vertex = model.get_wrist_vertex("右")
        print(right_wrist_vertex)
        self.assertIsNotNone(right_wrist_vertex)

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

    def test_calc_bf_01(self):
        motion = VmdReader("D:/MMD/MikuMikuDance_v926x64/UserFile/Motion/ダンス_1人/ドラマツルギー motion 配布用 moka/ドラマツルギー_0-500.vmd").read_data()
        
        bf = motion.calc_bf("右腕", 101)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 27.1, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 16.2, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), -32.9, delta=0.1)

        bf = motion.calc_bf("右腕", 143)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 32.2, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 57.3, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), -23.6, delta=0.1)

        bf = motion.calc_bf("右腕", 107)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 27.2, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 16.7, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), -32.8, delta=0.1)

        bf = motion.calc_bf("右腕", 121)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 28.6, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 24.5, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), -31.4, delta=0.1)

        bf = motion.calc_bf("右腕", 137)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 32.1, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 55.2, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), -24.1, delta=0.1)

        bf = motion.calc_bf("センター", 108)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 1.00, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 1.75, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0, delta=0.1)

        bf = motion.calc_bf("センター", 143)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 1.20, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 1.90, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0, delta=0.1)

        bf = motion.calc_bf("センター", 135)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 1.18, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 1.89, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0, delta=0.1)

        bf = motion.calc_bf("センター", 340)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 3.21, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), -0.96, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0, delta=0.1)

        bf = motion.calc_bf("右足ＩＫ", 417)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 2.75, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 2.92, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 2.19, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), -29.6, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), -25.2, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 5.0, delta=0.1)

        bf = motion.calc_bf("左足ＩＫ", 420)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 2.47, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 2.28, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 1.39, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), -17.4, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 1.9, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0.7, delta=0.1)

    def test_calc_bf_02(self):
        motion = VmdReader(u"test/data/補間曲線テスト01.vmd").read_data()
        
        bf = motion.calc_bf("ﾎﾞｰﾝ01", 0)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0, delta=0.1)

        bf = motion.calc_bf("ﾎﾞｰﾝ01", 15)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 20, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 30, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 40, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 50, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 60.00003815, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 70, delta=0.1)

        bf = motion.calc_bf("ﾎﾞｰﾝ01", 1)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.032109514, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 10.18260956, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 4.065711975, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0.000829206, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0.000238923, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0.000410508, delta=0.1)

        bf = motion.calc_bf("ﾎﾞｰﾝ01", 2)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.140442505, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 12.61500168, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 8.287061691, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0.007236294, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0.002085242, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0.003582553, delta=0.1)

        bf = motion.calc_bf("ﾎﾞｰﾝ01", 3)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.348192513, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 13.84411716, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 12.79018593, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0.026710032, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0.007699313, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0.013225263, delta=0.1)

        bf = motion.calc_bf("ﾎﾞｰﾝ01", 4)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 0.698622525, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 14.49679756, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 17.72015953, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0.069654942, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0.020092424, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0.034498487, delta=0.1)

        bf = motion.calc_bf("ﾎﾞｰﾝ01", 5)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 1.264359236, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 14.82721519, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 23.55570602, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0.151426569, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0.043738037, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0.07503701, delta=0.1)

        bf = motion.calc_bf("ﾎﾞｰﾝ01", 6)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 2.228799105, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 14.96385574, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 28.47421646, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0.293533772, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0.084980235, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0.145587772, delta=0.1)

        bf = motion.calc_bf("ﾎﾞｰﾝ01", 7)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 4.250654697, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 14.99863911, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 29.97695541, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0.529829144, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0.153979659, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0.263184816, delta=0.1)

        bf = motion.calc_bf("ﾎﾞｰﾝ01", 8)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 15.74932003, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 15.00131607, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 31.17938614, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 0.91197902, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0.266692847, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0.454135865, delta=0.1)

        bf = motion.calc_bf("ﾎﾞｰﾝ01", 9)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 17.77118301, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 15.03609848, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 32.36212158, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 1.525828362, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0.450684816, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 0.762894511, delta=0.1)

        bf = motion.calc_bf("ﾎﾞｰﾝ01", 10)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 18.73562622, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 15.17386436, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 33.57285309, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 2.53502202, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 0.761205316, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 1.276175618, delta=0.1)

        bf = motion.calc_bf("ﾎﾞｰﾝ01", 11)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 19.3013649, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 15.50316238, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 34.80752563, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 4.252967358, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 1.313556314, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 2.167253256, delta=0.1)

        bf = motion.calc_bf("ﾎﾞｰﾝ01", 12)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 19.65179825, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 16.15584373, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 36.06707764, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 7.438279152, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 2.422097683, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 3.884207487, delta=0.1)

        bf = motion.calc_bf("ﾎﾞｰﾝ01", 13)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 19.85955048, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 17.38496399, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 37.35407639, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 14.49954891, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 5.332914352, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 8.068556786, delta=0.1)

        bf = motion.calc_bf("ﾎﾞｰﾝ01", 14)
        print(bf)
        self.assertAlmostEqual(bf.position.x(), 19.96788788, delta=0.1)
        self.assertAlmostEqual(bf.position.y(), 19.81736565, delta=0.1)
        self.assertAlmostEqual(bf.position.z(), 38.66796112, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().x(), 33.70291519, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().y(), 18.53442383, delta=0.1)
        self.assertAlmostEqual(bf.rotation.toEulerAngles4MMD().z(), 24.47537041, delta=0.1)
    
    def test_vmd_output(self):
        motion = VmdReader(u"test/data/補間曲線テスト01.vmd").read_data()
        model = PmxReader("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/ダミーボーン頂点追加2.pmx").read_data()

        for n in range(100):
            fill_fno = 8
            fill_bone_name = "右腕{0:03d}".format(n)
            fill_bf = motion.calc_bf(fill_bone_name, fill_fno)
            fill_bf.key = True

            motion.bones[fill_bone_name][fill_fno] = fill_bf

        data_set = MOptionsDataSet(motion, model, model, "E:/WebDownload/test_vmd_output_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now()), False, False)

        VmdWriter(data_set).write()
        print(data_set.output_vmd_path)

    def test_split_bf_by_fno(self):
        motion = VmdReader(u"test/data/補間曲線テスト01.vmd").read_data()
        model = PmxReader("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/ダミーボーン頂点追加2.pmx").read_data()

        target_bone_name = "ﾎﾞｰﾝ01"

        prev_bf = motion.bones[target_bone_name][0]
        next_bf = motion.bones[target_bone_name][15]

        motion.split_bf_by_fno(target_bone_name, prev_bf, next_bf, 8)

        for fno in motion.get_bone_fnos(target_bone_name):
            bf = motion.bones[target_bone_name][fno]
            print("fno: %s ------------" % bf.fno)
            print("position: %s" % bf.position)
            print("rotation: %s" % bf.rotation.toEulerAngles4MMD())
            print("int move x: %s, %s, %s, %s" % (bf.interpolation[MBezierUtils.MX_x1_idxs[3]], bf.interpolation[MBezierUtils.MX_y1_idxs[3]], \
                  bf.interpolation[MBezierUtils.MX_x2_idxs[3]], bf.interpolation[MBezierUtils.MX_y2_idxs[3]]))
            print("int move y: %s, %s, %s, %s" % (bf.interpolation[MBezierUtils.MY_x1_idxs[3]], bf.interpolation[MBezierUtils.MY_y1_idxs[3]], \
                  bf.interpolation[MBezierUtils.MY_x2_idxs[3]], bf.interpolation[MBezierUtils.MY_y2_idxs[3]]))
            print("int move z: %s, %s, %s, %s" % (bf.interpolation[MBezierUtils.MZ_x1_idxs[3]], bf.interpolation[MBezierUtils.MZ_y1_idxs[3]], \
                  bf.interpolation[MBezierUtils.MZ_x2_idxs[3]], bf.interpolation[MBezierUtils.MZ_y2_idxs[3]]))
            print("int rot: %s, %s, %s, %s" % (bf.interpolation[MBezierUtils.R_x1_idxs[3]], bf.interpolation[MBezierUtils.R_y1_idxs[3]], \
                  bf.interpolation[MBezierUtils.R_x2_idxs[3]], bf.interpolation[MBezierUtils.R_y2_idxs[3]]))

        data_set = MOptionsDataSet(motion, model, model, "E:/WebDownload/test_split_bf_by_fno_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now()), False, False)

        VmdWriter(data_set).write()
        print(data_set.output_vmd_path)

    def test_split_bf_by_fno01(self):
        original_motion = VmdReader(u"test/data/補間曲線テスト01.vmd").read_data()
        model = PmxReader("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/ダミーボーン頂点追加2.pmx").read_data()

        target_bone_name = "ﾎﾞｰﾝ01"
        links = BoneLinks()
        links.append(model.bones["SIZING_ROOT_BONE"])
        links.append(model.bones["ﾎﾞｰﾝ01"])

        for pidx in range(10):
            try:
                params = np.random.randint(0, 127, (1, 4))
                # params = [[116, 24, 22, 82]]

                for fill_fno in range(original_motion.get_bone_fnos(target_bone_name)[0] + 1, original_motion.get_bone_fnos(target_bone_name)[-1]):

                    motion = original_motion.copy()

                    # bfの補間曲線を再設定する
                    next_bf = motion.bones[target_bone_name][motion.get_bone_fnos(target_bone_name)[-1]]
                    motion.reset_interpolation_parts(target_bone_name, next_bf, [None, MVector2D(20, 20), MVector2D(107, 107), None], \
                                                     MBezierUtils.R_x1_idxs, MBezierUtils.R_y1_idxs, MBezierUtils.R_x2_idxs, MBezierUtils.R_y2_idxs)
                    motion.reset_interpolation_parts(target_bone_name, next_bf, [None, MVector2D(params[0][0], params[0][1]), MVector2D(params[0][2], params[0][3]), None], \
                                                     MBezierUtils.MX_x1_idxs, MBezierUtils.MX_y1_idxs, MBezierUtils.MX_x2_idxs, MBezierUtils.MX_y2_idxs)
                    motion.reset_interpolation_parts(target_bone_name, next_bf, [None, MVector2D(20, 20), MVector2D(107, 107), None], \
                                                     MBezierUtils.MY_x1_idxs, MBezierUtils.MY_y1_idxs, MBezierUtils.MY_x2_idxs, MBezierUtils.MY_y2_idxs)
                    motion.reset_interpolation_parts(target_bone_name, next_bf, [None, MVector2D(20, 20), MVector2D(107, 107), None], \
                                                     MBezierUtils.MZ_x1_idxs, MBezierUtils.MZ_y1_idxs, MBezierUtils.MZ_x2_idxs, MBezierUtils.MZ_y2_idxs)
                    
                    # 補間曲線を再設定したモーションを再保持
                    org_motion = motion.copy()

                    # 間のキーフレをテスト
                    prev_bf = motion.bones[target_bone_name][motion.get_bone_fnos(target_bone_name)[0]]
                    next_bf = motion.bones[target_bone_name][motion.get_bone_fnos(target_bone_name)[-1]]

                    result = motion.split_bf_by_fno(target_bone_name, prev_bf, next_bf, fill_fno)
                    # 分割に成功した場合、誤差小。失敗してる場合は誤差大
                    delta = 0.3 if result else 1

                    print("-----------------------------")

                    for now_fno in motion.get_bone_fnos(target_bone_name):
                        # 有効なキーフレをテスト
                        now_bf = motion.calc_bf(target_bone_name, now_fno)

                        org_pos_dic = MServiceUtils.calc_global_pos(model, links, org_motion, now_fno)
                        now_pos_dic = MServiceUtils.calc_global_pos(model, links, motion, now_fno)

                        print("fill_fno: %s, now_fno: %s key: %s (%s) ------------" % (fill_fno, now_bf.fno, now_bf.key, pidx))
                        print("params: %s" % params)
                        print("position: %s" % now_bf.position)
                        print("rotation: %s" % now_bf.rotation.toEulerAngles4MMD())
                        print("int move x: %s, %s, %s, %s" % (now_bf.interpolation[MBezierUtils.MX_x1_idxs[3]], now_bf.interpolation[MBezierUtils.MX_y1_idxs[3]], \
                              now_bf.interpolation[MBezierUtils.MX_x2_idxs[3]], now_bf.interpolation[MBezierUtils.MX_y2_idxs[3]]))
                        print("int move y: %s, %s, %s, %s" % (now_bf.interpolation[MBezierUtils.MY_x1_idxs[3]], now_bf.interpolation[MBezierUtils.MY_y1_idxs[3]], \
                              now_bf.interpolation[MBezierUtils.MY_x2_idxs[3]], now_bf.interpolation[MBezierUtils.MY_y2_idxs[3]]))
                        print("int move z: %s, %s, %s, %s" % (now_bf.interpolation[MBezierUtils.MZ_x1_idxs[3]], now_bf.interpolation[MBezierUtils.MZ_y1_idxs[3]], \
                              now_bf.interpolation[MBezierUtils.MZ_x2_idxs[3]], now_bf.interpolation[MBezierUtils.MZ_y2_idxs[3]]))
                        print("int rot: %s, %s, %s, %s" % (now_bf.interpolation[MBezierUtils.R_x1_idxs[3]], now_bf.interpolation[MBezierUtils.R_y1_idxs[3]], \
                              now_bf.interpolation[MBezierUtils.R_x2_idxs[3]], now_bf.interpolation[MBezierUtils.R_y2_idxs[3]]))

                        self.assertAlmostEqual(org_pos_dic[target_bone_name].x(), now_pos_dic[target_bone_name].x(), delta=0.2)
                        self.assertAlmostEqual(org_pos_dic[target_bone_name].y(), now_pos_dic[target_bone_name].y(), delta=0.2)
                        self.assertAlmostEqual(org_pos_dic[target_bone_name].z(), now_pos_dic[target_bone_name].z(), delta=0.2)
                    
                    print("-----------------------------")

                    for fno in range(motion.get_bone_fnos(target_bone_name)[-1]):
                        # org_bf = org_motion.calc_bf(target_bone_name, fno)
                        now_bf = motion.calc_bf(target_bone_name, fno)

                        org_pos_dic = MServiceUtils.calc_global_pos(model, links, org_motion, fno)
                        now_pos_dic = MServiceUtils.calc_global_pos(model, links, motion, fno)

                        print("** fill_fno: %s, fno: %s key: %s (%s) ------------" % (fill_fno, now_bf.fno, now_bf.key, pidx))
                        print("** params: %s" % params)
                        print("** position: %s" % now_bf.position)
                        print("** rotation: %s" % now_bf.rotation.toEulerAngles4MMD())
                        print("** int move x: %s, %s, %s, %s" % (now_bf.interpolation[MBezierUtils.MX_x1_idxs[3]], now_bf.interpolation[MBezierUtils.MX_y1_idxs[3]], \
                              now_bf.interpolation[MBezierUtils.MX_x2_idxs[3]], now_bf.interpolation[MBezierUtils.MX_y2_idxs[3]]))
                        print("** int move y: %s, %s, %s, %s" % (now_bf.interpolation[MBezierUtils.MY_x1_idxs[3]], now_bf.interpolation[MBezierUtils.MY_y1_idxs[3]], \
                              now_bf.interpolation[MBezierUtils.MY_x2_idxs[3]], now_bf.interpolation[MBezierUtils.MY_y2_idxs[3]]))
                        print("** int move z: %s, %s, %s, %s" % (now_bf.interpolation[MBezierUtils.MZ_x1_idxs[3]], now_bf.interpolation[MBezierUtils.MZ_y1_idxs[3]], \
                              now_bf.interpolation[MBezierUtils.MZ_x2_idxs[3]], now_bf.interpolation[MBezierUtils.MZ_y2_idxs[3]]))
                        print("** int rot: %s, %s, %s, %s" % (now_bf.interpolation[MBezierUtils.R_x1_idxs[3]], now_bf.interpolation[MBezierUtils.R_y1_idxs[3]], \
                              now_bf.interpolation[MBezierUtils.R_x2_idxs[3]], now_bf.interpolation[MBezierUtils.R_y2_idxs[3]]))

                        self.assertAlmostEqual(org_pos_dic[target_bone_name].x(), now_pos_dic[target_bone_name].x(), delta=(delta * 2))
                        self.assertAlmostEqual(org_pos_dic[target_bone_name].y(), now_pos_dic[target_bone_name].y(), delta=(delta * 3))
                        self.assertAlmostEqual(org_pos_dic[target_bone_name].z(), now_pos_dic[target_bone_name].z(), delta=(delta * 4))

                    now = datetime.now()

                    data_set = MOptionsDataSet(motion, model, model, "E:/WebDownload/test_split_bf_by_fno01_{0:%Y%m%d_%H%M%S%f}.vmd".format(now), False, False)
                    VmdWriter(data_set).write()
                    print(data_set.output_vmd_path)

                    data_set = MOptionsDataSet(org_motion, model, model, "E:/WebDownload/test_split_bf_by_fno01_{0:%Y%m%d_%H%M%S%f}_orignal.vmd".format(now), False, False)
                    VmdWriter(data_set).write()
                    print(data_set.output_vmd_path)

            except Exception as e:
                # エラーになったらデータを出力する
                now = datetime.now()

                data_set = MOptionsDataSet(motion, model, model, "E:/WebDownload/test_split_bf_by_fno01_{0:%Y%m%d_%H%M%S%f}.vmd".format(now), False, False)
                VmdWriter(data_set).write()
                print(data_set.output_vmd_path)

                data_set = MOptionsDataSet(org_motion, model, model, "E:/WebDownload/test_split_bf_by_fno01_{0:%Y%m%d_%H%M%S%f}_orignal.vmd".format(now), False, False)
                VmdWriter(data_set).write()
                print(data_set.output_vmd_path)

                raise e

    def a_test_split_bf_by_fno02(self):
        original_motion = VmdReader(u"test/data/補間曲線テスト01.vmd").read_data()
        model = PmxReader("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/ダミーボーン頂点追加2.pmx").read_data()

        target_bone_name = "ﾎﾞｰﾝ01"
        links = BoneLinks()
        links.append(model.bones["SIZING_ROOT_BONE"])
        links.append(model.bones["ﾎﾞｰﾝ01"])

        base_params = [0, 16, 32, 127]

        # https://qiita.com/wakame1367/items/0744268e928a28810c20
        for xparams, yparams, zparams, rparams in zip(np.array(np.meshgrid(base_params, base_params, base_params, base_params)).T.reshape(-1, 4), \
                                                      np.array(np.meshgrid(base_params, base_params, base_params, base_params)).T.reshape(-1, 4), \
                                                      np.array(np.meshgrid(base_params, base_params, base_params, base_params)).T.reshape(-1, 4), \
                                                      np.array(np.meshgrid(base_params, base_params, base_params, base_params)).T.reshape(-1, 4)):
            try:
                for fill_fno in range(original_motion.get_bone_fnos(target_bone_name)[0] + 1, original_motion.get_bone_fnos(target_bone_name)[-1]):

                    motion = cPickle.loads(cPickle.dumps(original_motion, -1))

                    # bfの補間曲線を再設定する
                    next_bf = motion.bones[target_bone_name][motion.get_bone_fnos(target_bone_name)[-1]]
                    motion.reset_interpolation_parts(target_bone_name, next_bf, [None, MVector2D(xparams[0], xparams[1]), MVector2D(xparams[2], xparams[3]), None], \
                                                     MBezierUtils.MX_x1_idxs, MBezierUtils.MX_y1_idxs, MBezierUtils.MX_x2_idxs, MBezierUtils.MX_y2_idxs)
                    motion.reset_interpolation_parts(target_bone_name, next_bf, [None, MVector2D(yparams[0], yparams[1]), MVector2D(yparams[2], yparams[3]), None], \
                                                     MBezierUtils.MY_x1_idxs, MBezierUtils.MY_y1_idxs, MBezierUtils.MY_x2_idxs, MBezierUtils.MY_y2_idxs)
                    motion.reset_interpolation_parts(target_bone_name, next_bf, [None, MVector2D(zparams[0], zparams[1]), MVector2D(zparams[2], zparams[3]), None], \
                                                     MBezierUtils.MZ_x1_idxs, MBezierUtils.MZ_y1_idxs, MBezierUtils.MZ_x2_idxs, MBezierUtils.MZ_y2_idxs)
                    motion.reset_interpolation_parts(target_bone_name, next_bf, [None, MVector2D(rparams[0], rparams[1]), MVector2D(rparams[2], rparams[3]), None], \
                                                     MBezierUtils.R_x1_idxs, MBezierUtils.R_y1_idxs, MBezierUtils.R_x2_idxs, MBezierUtils.R_y2_idxs)
                    
                    # 補間曲線を再設定したモーションを再保持
                    org_motion = cPickle.loads(cPickle.dumps(motion, -1))

                    # 間のキーフレをテスト
                    prev_bf = motion.bones[target_bone_name][motion.get_bone_fnos(target_bone_name)[0]]
                    next_bf = motion.bones[target_bone_name][motion.get_bone_fnos(target_bone_name)[-1]]

                    result = motion.split_bf_by_fno(target_bone_name, prev_bf, next_bf, fill_fno)
                    # 分割に成功した場合、誤差小。失敗してる場合は誤差大
                    delta = 0.3 if result else 1

                    # print("-----------------------------")

                    # for now_fno in motion.get_bone_fnos(target_bone_name):
                    #     # 有効なキーフレをテスト
                    #     now_bf = motion.calc_bf(target_bone_name, now_fno)

                    #     org_pos_dic = MServiceUtils.calc_global_pos(model, links, org_motion, now_fno)
                    #     now_pos_dic = MServiceUtils.calc_global_pos(model, links, motion, now_fno)

                    #     print("fill_fno: %s, now_fno: %s key: %s ------------" % (fill_fno, now_bf.fno, now_bf.key))
                    #     print("xparams: %s" % xparams)
                    #     print("yparams: %s" % yparams)
                    #     print("zparams: %s" % zparams)
                    #     print("rparams: %s" % rparams)
                    #     print("position: %s" % now_bf.position)
                    #     print("rotation: %s" % now_bf.rotation.toEulerAngles4MMD())
                    #     print("int move x: %s, %s, %s, %s" % (now_bf.interpolation[MBezierUtils.MX_x1_idxs[3]], now_bf.interpolation[MBezierUtils.MX_y1_idxs[3]], \
                    #           now_bf.interpolation[MBezierUtils.MX_x2_idxs[3]], now_bf.interpolation[MBezierUtils.MX_y2_idxs[3]]))
                    #     print("int move y: %s, %s, %s, %s" % (now_bf.interpolation[MBezierUtils.MY_x1_idxs[3]], now_bf.interpolation[MBezierUtils.MY_y1_idxs[3]], \
                    #           now_bf.interpolation[MBezierUtils.MY_x2_idxs[3]], now_bf.interpolation[MBezierUtils.MY_y2_idxs[3]]))
                    #     print("int move z: %s, %s, %s, %s" % (now_bf.interpolation[MBezierUtils.MZ_x1_idxs[3]], now_bf.interpolation[MBezierUtils.MZ_y1_idxs[3]], \
                    #           now_bf.interpolation[MBezierUtils.MZ_x2_idxs[3]], now_bf.interpolation[MBezierUtils.MZ_y2_idxs[3]]))
                    #     print("int rot: %s, %s, %s, %s" % (now_bf.interpolation[MBezierUtils.R_x1_idxs[3]], now_bf.interpolation[MBezierUtils.R_y1_idxs[3]], \
                    #           now_bf.interpolation[MBezierUtils.R_x2_idxs[3]], now_bf.interpolation[MBezierUtils.R_y2_idxs[3]]))

                    #     self.assertAlmostEqual(org_pos_dic[target_bone_name].x(), now_pos_dic[target_bone_name].x(), delta=(delta * 2))
                    #     self.assertAlmostEqual(org_pos_dic[target_bone_name].y(), now_pos_dic[target_bone_name].y(), delta=(delta * 3))
                    #     self.assertAlmostEqual(org_pos_dic[target_bone_name].z(), now_pos_dic[target_bone_name].z(), delta=(delta * 4))
                    
                    print("-----------------------------")

                    for fno in range(motion.get_bone_fnos(target_bone_name)[-1]):
                        # org_bf = org_motion.calc_bf(target_bone_name, fno)
                        now_bf = motion.calc_bf(target_bone_name, fno)

                        org_pos_dic = MServiceUtils.calc_global_pos(model, links, org_motion, fno)
                        now_pos_dic = MServiceUtils.calc_global_pos(model, links, motion, fno)

                        print("** fill_fno: %s, fno: %s key: %s ------------" % (fill_fno, now_bf.fno, now_bf.key))
                        print("xparams: %s" % xparams)
                        print("yparams: %s" % yparams)
                        print("zparams: %s" % zparams)
                        print("rparams: %s" % rparams)
                        print("** position: %s" % now_bf.position)
                        print("** rotation: %s" % now_bf.rotation.toEulerAngles4MMD())
                        print("** int move x: %s, %s, %s, %s" % (now_bf.interpolation[MBezierUtils.MX_x1_idxs[3]], now_bf.interpolation[MBezierUtils.MX_y1_idxs[3]], \
                              now_bf.interpolation[MBezierUtils.MX_x2_idxs[3]], now_bf.interpolation[MBezierUtils.MX_y2_idxs[3]]))
                        print("** int move y: %s, %s, %s, %s" % (now_bf.interpolation[MBezierUtils.MY_x1_idxs[3]], now_bf.interpolation[MBezierUtils.MY_y1_idxs[3]], \
                              now_bf.interpolation[MBezierUtils.MY_x2_idxs[3]], now_bf.interpolation[MBezierUtils.MY_y2_idxs[3]]))
                        print("** int move z: %s, %s, %s, %s" % (now_bf.interpolation[MBezierUtils.MZ_x1_idxs[3]], now_bf.interpolation[MBezierUtils.MZ_y1_idxs[3]], \
                              now_bf.interpolation[MBezierUtils.MZ_x2_idxs[3]], now_bf.interpolation[MBezierUtils.MZ_y2_idxs[3]]))
                        print("** int rot: %s, %s, %s, %s" % (now_bf.interpolation[MBezierUtils.R_x1_idxs[3]], now_bf.interpolation[MBezierUtils.R_y1_idxs[3]], \
                              now_bf.interpolation[MBezierUtils.R_x2_idxs[3]], now_bf.interpolation[MBezierUtils.R_y2_idxs[3]]))

                        self.assertAlmostEqual(org_pos_dic[target_bone_name].x(), now_pos_dic[target_bone_name].x(), delta=(delta * 2))
                        self.assertAlmostEqual(org_pos_dic[target_bone_name].y(), now_pos_dic[target_bone_name].y(), delta=(delta * 3))
                        self.assertAlmostEqual(org_pos_dic[target_bone_name].z(), now_pos_dic[target_bone_name].z(), delta=(delta * 4))

                    # now = datetime.now()

                    # data_set = MOptionsDataSet(motion, model, model, "E:/WebDownload/test_split_bf_by_fno01_{0:%Y%m%d_%H%M%S%f}.vmd".format(now), False, False)
                    # VmdWriter(data_set).write()
                    # print(data_set.output_vmd_path)

                    # data_set = MOptionsDataSet(org_motion, model, model, "E:/WebDownload/test_split_bf_by_fno01_{0:%Y%m%d_%H%M%S%f}_orignal.vmd".format(now), False, False)
                    # VmdWriter(data_set).write()
                    # print(data_set.output_vmd_path)

            except Exception as e:
                # エラーになったらデータを出力する
                now = datetime.now()

                data_set = MOptionsDataSet(motion, model, model, "E:/WebDownload/test_split_bf_by_fno01_{0:%Y%m%d_%H%M%S%f}.vmd".format(now), False, False)
                VmdWriter(data_set).write()
                print(data_set.output_vmd_path)

                data_set = MOptionsDataSet(org_motion, model, model, "E:/WebDownload/test_split_bf_by_fno01_{0:%Y%m%d_%H%M%S%f}_orignal.vmd".format(now), False, False)
                VmdWriter(data_set).write()
                print(data_set.output_vmd_path)

                raise e


if __name__ == "__main__":
    unittest.main()

