# -*- coding: utf-8 -*-
#
import math # noqa
import unittest # noqa
import numpy as np # noqa
import sys
import pathlib
import itertools
import random # noqa
import _pickle as cPickle

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
from module import MOptions, MOptionsDataSet # noqa
from utils.MLogger import MLogger # noqa
from service.parts.StanceService import StanceService # noqa


logger = MLogger(__name__, level=1)


class MServiceTest(unittest.TestCase):

    def test_01(self):
        self.assertTrue(False)

    def test_stance_shoulder_01(self):
        arm_slope = MVector3D(-1.837494969367981, 18.923479080200195, 0.4923856854438782)
        shoulder_slope = MVector3D(-0.8141360282897949, 19.6701602935791, 0.4931679964065552)
        neck_base = MVector3D(0.0, 18.923479080200195, 0.4923856854438782)

        # 傾きパターン
        test_slope_param = [arm_slope, shoulder_slope, neck_base]
        slope_test_params = list(itertools.product(test_slope_param, repeat=2))
        # random.shuffle(slope_test_params)

        # 数値パターン
        test_number_param = [0, -1, 1]
        number_test_params = list(itertools.product(test_number_param, repeat=3))
        # random.shuffle(number_test_params)

        target_test_params = list(itertools.product(slope_test_params, number_test_params))

        for param in target_test_params:
            print("------------------")
            print("param[0][0]: %s" % param[0][0])
            print("param[0][1]: %s" % param[0][1])
            print("param[1][0]: %s" % param[1][0])
            print("param[1][1]: %s" % param[1][1])
            print("param[1][2]: %s" % param[1][2])
            rep_shoulder_slope = (param[0][0] - param[0][1]).normalized()
            rep_shoulder_slope_up = MVector3D(param[1][0], param[1][1], param[1][2])
            rep_shoulder_slope_cross = MVector3D.crossProduct(rep_shoulder_slope, rep_shoulder_slope_up).normalized()
            
            rep_shoulder_initial_slope_qq = MQuaternion.fromDirection(rep_shoulder_slope, rep_shoulder_slope_cross)
            print("rep_shoulder_slope: %s" % rep_shoulder_slope)
            print("rep_shoulder_slope_up: %s" % rep_shoulder_slope_up)
            print("qq: %s" % rep_shoulder_initial_slope_qq.toEulerAngles())
        
        self.assertTrue(True)

    def test_stance_shoulder_02(self):
        motion = VmdReader("D:/MMD/MikuMikuDance_v926x64/UserFile/Motion/_VMDサイジング/鳳仙花/鳳仙花mkmk髭切007bミュ第一_0-2000.vmd").read_data()
        model = PmxReader("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/刀剣乱舞/107_髭切/髭切【刀ミュ】mkmk008d 刀剣乱舞/髭切【刀ミュ】mkmk008d/髭切【刀ミュ3】mkmk008d_鳳仙花.pmx").read_data()

        # 傾きパターン
        test_slope_param = ["arm_name", "shoulder_name", "首根元"]
        all_slope_test_params = list(itertools.product(test_slope_param, repeat=2))
        slope_test_params = [(x00, x01) for (x00, x01) in all_slope_test_params if x00 != x01]

        # 数値パターン
        test_number_param = [0, -1, 1]
        all_number_test_params = list(itertools.product(test_number_param, repeat=3))
        number_test_params = [(x00, x01, x02) for (x00, x01, x02) in all_number_test_params if x00 == "0" or x01 == "0" or x02 == "0"]

        target_test_params = list(itertools.product(slope_test_params, number_test_params))

        for params in target_test_params:
            copy_motion = cPickle.loads(cPickle.dumps(motion, -1))
            dataset = MOptionsDataSet(copy_motion, model, model, "", False, False)
            dataset.test_params = params

            options = MOptions("", "", [dataset])

            service = StanceService(options)
            service.adjust_shoulder_stance(0, dataset)

            print("stance: %s" % dataset.motion.bones["右肩"][1625].rotation.toEulerAngles())
            print("original: %s" % motion.bones["右肩"][1625].rotation.toEulerAngles())

        self.assertTrue(True)
        

