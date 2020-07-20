# -*- coding: utf-8 -*-
#
import numpy as np
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
from mmd.PmxData import PmxModel, Vertex, Material, Bone, Morph, DisplaySlot, RigidBody, Joint # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MMath import MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MOptionsDataSet # noqa
from module.MParams import BoneLinks # noqa
from utils import MBezierUtils, MServiceUtils # noqa
from utils.MException import SizingException # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__, level=1)


class MotionTest(unittest.TestCase):

    def test_front_2_left(self):
        motion = VmdReader("D:/MMD/MikuMikuDance_v926x64/Work/20180423_マツケンサンバ/022_モーション・ポーズ/マツケンサンバ_バック_左方向_1870-2100.vmd").read_data()
        model = PmxReader("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/初音ミクVer2 準標準.pmx").read_data()

        parent_bf = motion.calc_bf("全ての親", 0)
        parent_bf.rotation = MQuaternion.fromEulerAngles(0, 180, 0)
        motion.regist_bf(parent_bf, "全ての親", 0)

        for bone_name in ["センター", "右足ＩＫ", "左足ＩＫ"]:
            links = model.create_link_2_top_one(bone_name)
            for (fno, bf) in motion.bones[bone_name].items():
                global_3ds_dic = MServiceUtils.calc_global_pos(model, links, motion, fno)
                bone_global_pos = global_3ds_dic[bone_name]

                bf.position = bone_global_pos - model.bones[bone_name].position
                motion.regist_bf(bf, bone_name, fno)
        
        for bone_name in ["上半身", "下半身", "右足ＩＫ", "左足ＩＫ"]:
            links = model.create_link_2_top_one(bone_name)
            for (fno, bf) in motion.bones[bone_name].items():
                bf.rotation = parent_bf.rotation * bf.rotation
                motion.regist_bf(bf, bone_name, fno)
        
        parent_bf.rotation = MQuaternion()
        motion.regist_bf(parent_bf, "全ての親", 0)
        
        data_set = MOptionsDataSet(motion, model, model, "D:/MMD/MikuMikuDance_v926x64/Work/20180423_マツケンサンバ/022_モーション・ポーズ/マツケンサンバ_バック_左方向_1870-2100_right.vmd")
        VmdWriter(data_set).write()
        print("FINISH")


if __name__ == "__main__":
    unittest.main()

