# -*- coding: utf-8 -*-
# 腕IK処理テスト
# 

import copy
import os
import sys
import pathlib
import itertools
import shutil
# このソースのあるディレクトリの絶対パスを取得
current_dir = pathlib.Path(__file__).resolve().parent
# モジュールのあるパスを追加
sys.path.append( str(current_dir) + '/../' )
sys.path.append( str(current_dir) + '/../src/' )


import logging
import unittest
from PyQt5.QtGui import QQuaternion, QVector3D, QVector2D, QMatrix4x4, QVector4D

from VmdWriter import VmdWriter, VmdBoneFrame
from VmdReader import VmdReader, VmdMotion
from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader
import sub_arm_ik, utils, main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestSubStance(unittest.TestCase):

    def test_upper_stance_01(self):
        test_param_param = ["ou","ru","o2","r2","b"]
        self.calc_stance(list(itertools.permutations(test_param_param)))
        self.assertFalse(True)

    def test_upper_stance_upper2_up_01(self):
        # number_ok_list = []
        # # XYZ パターン
        # test_param_param = ["x", "x-", "y", "y-", "z", "z-"]
        # target_test_params_base = list(itertools.product(test_param_param, repeat=3))
        # target_test_params = [(x, y, z) for (x, y, z) in target_test_params_base if x[0] not in [y[0], z[0]] and y[0] not in [x[0], z[0]]]
        # xyz_ok_list = self.calc_stance(target_test_params, 0.5, False)

        xyz_ok_list = []
        # 数値パターン
        test_param_param = ["0","1-","1"]
        target_test_params = list(itertools.product(test_param_param, repeat=3))
        number_ok_list = self.calc_stance(target_test_params, 0.3, False)

        print("xyz_ok_list LIST: %s" % xyz_ok_list)
        print("number_ok_list LIST: %s" % number_ok_list)
        self.assertGreater(len(xyz_ok_list + number_ok_list), 0)

    def test_upper_stance_upper2_up_02(self):
        # DIRECTIONパターン
        directipn_directipn_test_param_param = ["上半身", "上半身2", "頭", "首"]
        direction_up_test_param_param = ["0","1-","1"]
        # UPパターン
        up_directipn_test_param_param = ["右腕", "左腕"]
        up_up_test_param_param = ["0","1-","1"]

        # 直積
        target_test_params_base = list(itertools.product(directipn_directipn_test_param_param, directipn_directipn_test_param_param, \
            direction_up_test_param_param, direction_up_test_param_param, direction_up_test_param_param, \
            up_directipn_test_param_param, up_directipn_test_param_param, \
            up_up_test_param_param, up_up_test_param_param, up_up_test_param_param))

        target_test_params = [(a, b, c, d, e, g, h, i, j, k) for (a, b, c, d, e, g, h, i, j, k) in target_test_params_base if a != b and g != h]
        ok_list = self.calc_stance(target_test_params, 0.5, False)

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
    
    def calc_stance(self, target_test_params, limit, exist_ok):
        # VMD読み込み
        motion = VmdReader().read_vmd_file("D:/MMD/MikuMikuDance_v926x64/UserFile/Motion/ダンス_1人/ドラマツルギー motion 配布用 moka/ドラマツルギー_0-500.vmd")

        # 作成元モデル
        trace_model = PmxReader().read_pmx_file("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/初音ミク/Tda式デフォ服ミク_ver1.1 金子卵黄/Tda式初音ミク_デフォ服ver.pmx")

        # 変換先モデル
        replace_model = PmxReader().read_pmx_file("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/初音ミク/Tda式デフォ服ミク_ver1.1 金子卵黄/Tda式初音ミク_デフォ服ver.pmx")
        # replace_model = PmxReader().read_pmx_file("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/刀剣乱舞/011_今剣/今剣 ゆるん式 ver0124/ライブ衣装/今剣インナー_準標準.pmx")

        test_target_name = "上半身2"
        links, indexes = replace_model.create_link_2_top_one(test_target_name)

        target_frames = [0, 202, 150]

        # 事前にグローバル位置を求めておく
        target_bfs = [x for x in motion.frames[test_target_name] if x.frame in target_frames]
        org_target_poss = []

        for bf in target_bfs:
            _, _, _, _, org_global_3ds = utils.create_matrix_global(replace_model, links, motion.frames, bf, None)
            org_target_poss.append(org_global_3ds[-1])

        is_avoidance = False
        is_avoidance_finger = False
        is_hand_ik = False
        hand_distance = 1.7
        is_floor_hand = False
        is_floor_hand_up = False
        is_floor_hand_down = False
        hand_floor_distance = 1
        leg_floor_distance = 1
        is_finger_ik = False
        finger_distance = 1
        vmd_choice_values = []
        rep_choice_values = []
        rep_rate_values = []
        camera_motion = None
        camera_vmd_path = None
        camera_pmx = None
        output_camera_vmd_path = None
        camera_y_offset = 0
        base_path = "E:/MMD/vmd_sizing/vmd/input_upper2_up"

        logger.info("len: %s", len(target_test_params))
        ok_list = []

        os.makedirs("{0}/OK".format(base_path), exist_ok=exist_ok)
        os.makedirs("{0}/NG".format(base_path), exist_ok=exist_ok)

        for test_param in target_test_params:
            logger.info("test_param: %s", test_param)

            file_name = "test_{0}.vmd".format(','.join([str(i) for i in test_param]))

            output_vmd_path = "{0}/{1}".format(base_path, file_name)

            copy_motion = copy.deepcopy(motion)

            main.main(copy_motion, trace_model, replace_model, output_vmd_path, \
                is_avoidance, is_avoidance_finger, is_hand_ik, hand_distance, is_floor_hand, is_floor_hand_up, is_floor_hand_down, hand_floor_distance, leg_floor_distance, is_finger_ik, finger_distance, vmd_choice_values, rep_choice_values, rep_rate_values, \
                camera_motion, camera_vmd_path, camera_pmx, output_camera_vmd_path, camera_y_offset, test_param)
            
            # 変換後のグローバル位置を求める
            org_target_bfs = copy.deepcopy([x for x in copy_motion.frames[test_target_name] if x.frame in target_frames])
            rep_target_poss = []

            for bf in org_target_bfs:
                _, _, _, _, rep_global_3ds = utils.create_matrix_global(replace_model, links, copy_motion.frames, bf, None)
                rep_target_poss.append(rep_global_3ds[-1])

            result_list = []
            diff_list = []

            for org_bf, bf, org_target_pos, rep_target_pos in zip(org_target_bfs, target_bfs, org_target_poss, rep_target_poss):
                # is_x = org_target_pos.x() - limit <= rep_target_pos.x() <= org_target_pos.x() + limit
                # is_y = org_target_pos.y() - limit <= rep_target_pos.y() <= org_target_pos.y() + limit
                # is_z = org_target_pos.z() - limit <= rep_target_pos.z() <= org_target_pos.z() + limit
                
                org_euler = org_bf.rotation.toEulerAngles()
                to_euler = bf.rotation.toEulerAngles()

                is_x = org_euler.x() - limit <= to_euler.x() <= org_euler.x() + limit
                is_y = org_euler.y() - limit <= to_euler.y() <= org_euler.y() + limit
                is_z = org_euler.z() - limit <= to_euler.z() <= org_euler.z() + limit

                diff_euler = to_euler - org_euler

                result = is_x and is_y and is_z
                result_list.append(result)

                diff = "{0: 03.2f}#{1: 03.2f}#{2: 03.2f}".format( round(diff_euler.x(), 2), round(diff_euler.y(), 2), round(diff_euler.z(), 2) )
                diff_list.append(diff)

                if result:
                    logger.info("f: %s, org_target_pos: %s", bf.frame, org_target_pos)
                    logger.info("f: %s, rep_target_pos: %s", bf.frame, rep_target_pos)
                    logger.info("f: %s, org_rotation: %s", bf.frame, org_euler)
                    logger.info("f: %s, rep_rotation: %s", bf.frame, to_euler)
                    logger.info("f: %s, is_x: %s, is_y: %s, is_z: %s", bf.frame, is_x, is_y, is_z)

            resutl_file_name = "{0}_{1}_{2}.vmd".format(','.join([str(i) for i in test_param]), ','.join([str(i) for i in result_list]), ','.join([str(i) for i in diff_list]))
            
            if result_list.count(True) > 0:
                # TRUE(一致した場合)
                shutil.move(output_vmd_path, "{0}/OK/{1}".format(base_path, resutl_file_name))
                ok_list.append(test_param)
                logger.info("result: TRUE")
            else:
                # FALSE(一致しない場合)
                shutil.move(output_vmd_path, "{0}/NG/{1}".format(base_path, resutl_file_name))
                logger.info("result: FALSE")
            
        return ok_list

if __name__ == "__main__":
    unittest.main(defaultTest="TestSubStance.test_upper_stance_upper2_up_02")
