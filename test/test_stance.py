# -*- coding: utf-8 -*-
# 腕IK処理テスト
# 

import random
import copy
import os
import sys
import pathlib
import itertools
import shutil
import traceback
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
    
    def test_upper_stance_upper2_up_03(self):
        # DIRECTIONパターン
        rep_upper2_slope_direction_test_param_base = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_slope_direction_test_param_all_list = list(itertools.product(rep_upper2_slope_direction_test_param_base, repeat=4))
        rep_upper2_slope_direction_test_param_list = [(a, b, c, d) for (a, b, c, d) in rep_upper2_slope_direction_test_param_all_list if a != b and c != d]

        # XYZ パターン
        rep_upper2_slope_up_up_test_param_xyz_base = ["x", "x-", "y", "y-", "z", "z-"]
        rep_upper2_slope_up_up_test_param_xyz_all_list = list(itertools.product(rep_upper2_slope_up_up_test_param_xyz_base, repeat=3))
        rep_upper2_slope_up_up_test_param_xyz_list = [(x, y, z) for (x, y, z) in rep_upper2_slope_up_up_test_param_xyz_all_list if x[0] not in [y[0], z[0]] and y[0] not in [x[0], z[0]]]

        # 数値パターン
        rep_upper2_slope_up_up_test_param_number_base = ["0","1-","1"]
        rep_upper2_slope_up_up_test_param_number_list = list(itertools.product(rep_upper2_slope_up_up_test_param_number_base, repeat=3))

        # 直積
        rep_upper2_slope_test_param_xyz_list = list(itertools.product(rep_upper2_slope_direction_test_param_list, rep_upper2_slope_up_up_test_param_xyz_list))
        rep_upper2_slope_test_param_number_list = list(itertools.product(rep_upper2_slope_direction_test_param_list, rep_upper2_slope_up_up_test_param_number_list))

        target_test_params_base_list = rep_upper2_slope_test_param_xyz_list + rep_upper2_slope_test_param_number_list
        random.shuffle(target_test_params_base_list)

        target_test_params = [[a, b, c, d, e, f, g] for ((a, b, c, d), (e, f, g)) in target_test_params_base_list]
        ok_list = self.calc_stance(target_test_params, 0.5, False)

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)


    def test_upper_stance_upper2_up_04(self):
        # XYZ パターン
        rep_upper2_slope_up_up_test_param_xyz_base = ["x", "x-", "y", "y-", "z", "z-"]
        rep_upper2_slope_up_up_test_param_xyz_all_list = list(itertools.product(rep_upper2_slope_up_up_test_param_xyz_base, repeat=3))
        rep_upper2_slope_up_up_test_param_xyz_list = [(x, y, z) for (x, y, z) in rep_upper2_slope_up_up_test_param_xyz_all_list if x[0] not in [y[0], z[0]] and y[0] not in [x[0], z[0]]]

        # 数値パターン
        rep_upper2_slope_up_up_test_param_number_base = ["0","1-","1"]
        rep_upper2_slope_up_up_test_param_number_list = list(itertools.product(rep_upper2_slope_up_up_test_param_number_base, repeat=3))

        target_test_params_base_list = rep_upper2_slope_up_up_test_param_xyz_list + rep_upper2_slope_up_up_test_param_number_list
        random.shuffle(target_test_params_base_list)

        target_test_params = [[a, b, c] for (a, b, c) in target_test_params_base_list]
        ok_list = self.calc_stance(target_test_params, 0.5, False)

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)



    def test_upper_stance_upper2_up_05(self):
        # DIRECTIONパターン
        rep_upper2_slope_direction_test_param_base = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_slope_direction_test_param_all_list = list(itertools.product(rep_upper2_slope_direction_test_param_base, repeat=2))
        rep_upper2_slope_direction_test_param_list = [(a, b) for (a, b) in rep_upper2_slope_direction_test_param_all_list if a != b]

        # 数値パターン
        rep_upper2_slope_up_up_test_param_number_base = ["0","1-","1"]
        rep_upper2_slope_up_up_test_param_number_list = list(itertools.product(rep_upper2_slope_up_up_test_param_number_base, repeat=3))

        # 直積
        rep_upper2_slope_test_param_number_list = list(itertools.product(rep_upper2_slope_direction_test_param_list, rep_upper2_slope_up_up_test_param_number_list))

        target_test_params_base_list = rep_upper2_slope_test_param_number_list
        random.shuffle(target_test_params_base_list)

        target_test_params = [[a, b, e, f, g] for ((a, b), (e, f, g)) in target_test_params_base_list]
        ok_list = self.calc_stance(target_test_params, 0.5, False)

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)


    def test_upper_stance_upper2_up_06(self):
        # DIRECTIONパターン
        rep_upper2_initial_slope_test_param = ["上半身", "上半身2", "頭", "首"]
        # UPパターン
        # rep_upper2_initial_slope_test_param = ["右腕", "左腕"]
        rep_upper2_initial_slope_up_up_test_param = ["0","1-","1"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param, rep_upper2_initial_slope_test_param, \
            rep_upper2_initial_slope_test_param, rep_upper2_initial_slope_test_param, \
            rep_upper2_initial_slope_up_up_test_param, rep_upper2_initial_slope_up_up_test_param, rep_upper2_initial_slope_up_up_test_param))

        target_test_params_list = [(a, b, c, d, e, g, h) for (a, b, c, d, e, g, h) in target_test_params_base if a != b and c != d]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 0.5, False)

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
    


    def test_upper_stance_upper2_up_07(self):
        rep_upper2_initial_slope_test_param1 = ["上半身", "上半身2"]
        rep_upper2_initial_slope_test_param2 = ["左腕", "右腕"]
        rep_upper2_initial_slope_test_param3 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param4 = ["1","1-","2","2-"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param2, rep_upper2_initial_slope_test_param2, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param4, \
            rep_upper2_initial_slope_test_param4))

        target_test_params_list = [(a, b, c, d, e, f, g, h, i, j, k, l) for (a, b, c, d, e, f, g, h, i, j, k, l) in target_test_params_base if a != b and f != g and k[0] != l[0]]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 0.5, False)

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
    

    def test_upper_stance_upper2_up_08(self):
        rep_upper2_initial_slope_test_param1 = ["上半身", "上半身2"]
        rep_upper2_initial_slope_test_param2 = ["左腕", "右腕"]
        rep_upper2_initial_slope_test_param3 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param4 = ["1","1-","2","2-"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param4, rep_upper2_initial_slope_test_param4))

        target_test_params_list = [(a, b, c, d, e, f, g, h) for (a, b, c, d, e, f, g, h) in target_test_params_base if g[0] != h[0]]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 0.5, False)

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
    

    def test_upper_stance_upper2_up_09(self):
        rep_upper2_initial_slope_test_param1 = ["上半身", "上半身2"]
        rep_upper2_initial_slope_test_param2 = ["左腕", "右腕"]
        rep_upper2_initial_slope_test_param3 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param4 = ["1","1-","2","2-","3","3-"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param4, rep_upper2_initial_slope_test_param4))

        target_test_params_list = [(a, b, c, d, e, f, g, h) for (a, b, c, d, e, f, g, h) in target_test_params_base if g[0] != h[0]]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 0.5, False)

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
    


    def test_upper_stance_upper2_up_10(self):
        rep_upper2_initial_slope_test_param1 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param2 = ["左腕", "右腕"]
        rep_upper2_initial_slope_test_param3 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param4 = ["1","1-","2","2-","3","3-"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param4, rep_upper2_initial_slope_test_param4, \
            rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1, \
            rep_upper2_initial_slope_test_param2, rep_upper2_initial_slope_test_param2))

        target_test_params_list = [(a, b, c, d, e, f, g, h, i, j, k, l) for (a, b, c, d, e, f, g, h, i, j, k, l) in target_test_params_base if g[0] != h[0] and i != j and k != l]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 0.5, False)

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
    

    def test_upper_stance_upper2_up_11(self):
        rep_upper2_initial_slope_test_param1 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param2 = ["左腕", "右腕"]
        rep_upper2_initial_slope_test_param3 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param4 = ["s1","s2","u1"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1, \
            rep_upper2_initial_slope_test_param2, rep_upper2_initial_slope_test_param2, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param4, rep_upper2_initial_slope_test_param4, rep_upper2_initial_slope_test_param4))

        target_test_params_list = [(a, b, c, d, e, f, g, h, i, j) for (a, b, c, d, e, f, g, h, i, j) in target_test_params_base if g[0] != h[0] and a != b and c != d and h != i and i != j]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 0.5, False)

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
    


    def test_upper_stance_upper2_up_12(self):
        rep_upper2_initial_slope_test_param1 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param2 = ["左腕", "右腕"]
        rep_upper2_initial_slope_test_param3 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param4 = ["s1","u1"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param4, rep_upper2_initial_slope_test_param4, \
            rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1))

        target_test_params_list = [(a, b, c, d, e, f, g) for (a, b, c, d, e, f, g) in target_test_params_base if f != g and d != e]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 0.5, False)

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
    

    def test_upper_stance_upper2_up_13(self):
        rep_upper2_initial_slope_test_param1 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param2 = ["左腕", "右腕"]
        rep_upper2_initial_slope_test_param3 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param4 = ["n","i"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1, \
            rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1, \
            rep_upper2_initial_slope_test_param4))

        target_test_params_list = [(a, b, c, d, e) for (a, b, c, d, e) in target_test_params_base if a != b and c != d]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 0.5, False)

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
    

    def test_upper_stance_upper2_up_14(self):
        rep_upper2_initial_slope_test_param1 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param2 = ["左腕", "右腕"]
        rep_upper2_initial_slope_test_param3 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param4 = ["n","i"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1, \
            rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1, \
            rep_upper2_initial_slope_test_param4, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3))

        target_test_params_list = [(a, b, c, d, e, f, g, h) for (a, b, c, d, e, f, g, h) in target_test_params_base if a != b and c != d]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 5, False)

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
    
    def test_upper_stance_upper2_up_15(self):
        rep_upper2_initial_slope_test_param1 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param2 = ["左腕", "右腕"]
        rep_upper2_initial_slope_test_param3 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param4 = ["n","i"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1, \
            rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1, \
            rep_upper2_initial_slope_test_param4, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, 
            rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1))

        target_test_params_list = [(a, b, c, d, e, f, g, h, i, j) for (a, b, c, d, e, f, g, h, i, j) in target_test_params_base if a != b and c != d and i != j]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 5, False)

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
    
    def test_upper_stance_upper2_up_16(self):
        rep_upper2_initial_slope_test_param1 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param2 = ["右腕", "左腕"]
        rep_upper2_initial_slope_test_param3 = ["0","1-","1"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1,
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1))

        target_test_params_base2 = list(itertools.product(rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param2, rep_upper2_initial_slope_test_param2,
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1))

        target_test_params_base.extend(target_test_params_base2)

        target_test_params_list = [(x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11) for (x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11) \
            in target_test_params_base if x00 != x01 and x05 != x06]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 5, False, "016_TOまで指定_15")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
    
    def test_upper_stance_upper2_up_17(self):
        rep_upper2_initial_slope_test_param1 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param4 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param5 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param6 = ["右腕", "左腕"]
        rep_upper2_initial_slope_test_param7 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param8 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param3 = ["0","1-","1"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param4, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param5, rep_upper2_initial_slope_test_param5,
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param7, rep_upper2_initial_slope_test_param8))

        target_test_params_base.extend(list(itertools.product(rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param4, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param6, rep_upper2_initial_slope_test_param6,
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param7, rep_upper2_initial_slope_test_param8)))

        target_test_params_list = [(x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11) for (x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11) \
            in target_test_params_base if x00 != x01 and x05 != x06]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 5, False, "017_UPディレクション修正_06")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
    

    def test_upper_stance_upper2_up_18(self):
        rep_upper2_initial_slope_test_param1 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param3 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param4 = ["n","i"]
        rep_upper2_initial_slope_test_param5 = ["右腕", "左腕"]
        rep_upper2_initial_slope_test_param6 = ["上半身", "上半身2", "頭", "首"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param6, rep_upper2_initial_slope_test_param6, \
            rep_upper2_initial_slope_test_param4, rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3))

        target_test_params_base.extend(list(itertools.product(rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param5, rep_upper2_initial_slope_test_param5, \
            rep_upper2_initial_slope_test_param4, rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param1, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3)))

        target_test_params_list = [(x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12) for (x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12) \
            in target_test_params_base if x00 != x01 and x05 != x06 and x08 != x09]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 5, False, "018_UPディレクション修正_05")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)

    def test_upper_stance_upper2_up_19(self):
        rep_upper2_initial_slope_test_param1 = ["首"]
        rep_upper2_initial_slope_test_param2 = ["上半身"]
        rep_upper2_initial_slope_test_param3 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param4 = ["rn","ri","dn","di","1"]
        rep_upper2_initial_slope_test_param5 = ["右腕", "左腕"]
        rep_upper2_initial_slope_test_param6 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param7 = ["首"]
        rep_upper2_initial_slope_test_param8 = ["上半身2"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param2, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param6, rep_upper2_initial_slope_test_param6, \
            rep_upper2_initial_slope_test_param4, rep_upper2_initial_slope_test_param7, rep_upper2_initial_slope_test_param8, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param4))

        target_test_params_base.extend(list(itertools.product(rep_upper2_initial_slope_test_param1, rep_upper2_initial_slope_test_param2, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param5, rep_upper2_initial_slope_test_param5, \
            rep_upper2_initial_slope_test_param4, rep_upper2_initial_slope_test_param7, rep_upper2_initial_slope_test_param8, \
            rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, rep_upper2_initial_slope_test_param3, \
            rep_upper2_initial_slope_test_param4)))

        target_test_params_list = [(x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12, x13) \
            for (x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12, x13) \
            in target_test_params_base if x00 != x01 and x05 != x06 and x08 != x09]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 5, False, "019_04")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)


    def test_upper_stance_upper2_up_20(self):
        rep_upper2_initial_slope_test_param00 = ["頭"] # ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param01 = ["上半身2"] # ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param02 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param03 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param04 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param05 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param06 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param07 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param08 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param09 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param10 = ["d1","d1i","d2","d2i","d3","d3i", "1"]
        rep_upper2_initial_slope_test_param11 = ["d1","d1i","d2","d2i","d3","d3i", "1"]
        rep_upper2_initial_slope_test_param12 = ["d1","d1i","d2","d2i","d3","d3i", "1"]
        rep_upper2_initial_slope_test_param13 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param14 = ["上半身", "上半身2", "頭", "首"]


        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param00, rep_upper2_initial_slope_test_param01, \
            rep_upper2_initial_slope_test_param02, rep_upper2_initial_slope_test_param03, rep_upper2_initial_slope_test_param04, \
            rep_upper2_initial_slope_test_param05, rep_upper2_initial_slope_test_param06, \
            rep_upper2_initial_slope_test_param07, rep_upper2_initial_slope_test_param08, rep_upper2_initial_slope_test_param09, \
            rep_upper2_initial_slope_test_param10, rep_upper2_initial_slope_test_param11, rep_upper2_initial_slope_test_param12, \
            rep_upper2_initial_slope_test_param13, rep_upper2_initial_slope_test_param14))

        target_test_params_list = [(x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12, x13, x14) \
            for (x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12, x13, x14) \
            in target_test_params_base if x00 != x01 and x05 != x06 and x13 != x14 and \
                ((x10 == "1" and x11[:2] != x12[:2]) or (x11 == "1" and x10[:2] != x12[:2]) or (x12 == "1" and x11[:2] != x10[:2]) or (x10[:2] != x11[:2] != x12[:2]))]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 5, False, "020_01")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
    
    def test_upper_stance_upper2_up_21(self):
        rep_upper2_initial_slope_test_param00 = ["頭"] # ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param01 = ["上半身2"] # ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param02 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param03 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param04 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param05 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param06 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param07 = ["x", "x-", "y", "y-", "z", "z-"]
        rep_upper2_initial_slope_test_param08 = ["x", "x-", "y", "y-", "z", "z-"]
        rep_upper2_initial_slope_test_param09 = ["x", "x-", "y", "y-", "z", "z-"]
        rep_upper2_initial_slope_test_param10 = ["d1","d1i","d2","d2i","1"]
        rep_upper2_initial_slope_test_param11 = ["d1","d1i","d2","d2i","1"]
        rep_upper2_initial_slope_test_param12 = ["1"]
        rep_upper2_initial_slope_test_param13 = ["首"]
        rep_upper2_initial_slope_test_param14 = ["上半身2"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param00, rep_upper2_initial_slope_test_param01, \
            rep_upper2_initial_slope_test_param02, rep_upper2_initial_slope_test_param03, rep_upper2_initial_slope_test_param04, \
            rep_upper2_initial_slope_test_param05, rep_upper2_initial_slope_test_param06, \
            rep_upper2_initial_slope_test_param07, rep_upper2_initial_slope_test_param08, rep_upper2_initial_slope_test_param09, \
            rep_upper2_initial_slope_test_param10, rep_upper2_initial_slope_test_param11, rep_upper2_initial_slope_test_param12, \
            rep_upper2_initial_slope_test_param13, rep_upper2_initial_slope_test_param14))

        target_test_params_list = [(x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12, x13, x14) \
            for (x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12, x13, x14) \
            in target_test_params_base if x00 != x01 and x05 != x06 and x13 != x14 and  x07[0] not in [x08[0], x09[0]] and x08[0] not in [x07[0], x09[0]] and \
                ((x10 == "1" and x11[:2] != x12[:2]) or (x11 == "1" and x10[:2] != x12[:2]) or (x12 == "1" and x11[:2] != x10[:2]) or (x10[:2] != x11[:2] != x12[:2]))]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 5, False, "020_02_xyz")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
    

    def test_upper_stance_upper2_up_22(self):
        rep_upper2_initial_slope_test_param00 = ["頭"] # ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param01 = ["上半身2"] # ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param02 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param03 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param04 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param05 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param06 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param07 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param08 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param09 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param10 = ["d1","d1i","d2","d2i","u","ui","1"]
        rep_upper2_initial_slope_test_param11 = ["d1","d1i","d2","d2i","u","ui","1"]
        rep_upper2_initial_slope_test_param12 = ["d1","d1i","d2","d2i","u","ui","1"]
        rep_upper2_initial_slope_test_param13 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param14 = ["上半身", "上半身2", "頭", "首"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param00, rep_upper2_initial_slope_test_param01, \
            rep_upper2_initial_slope_test_param02, rep_upper2_initial_slope_test_param03, rep_upper2_initial_slope_test_param04, \
            rep_upper2_initial_slope_test_param05, rep_upper2_initial_slope_test_param06, \
            rep_upper2_initial_slope_test_param07, rep_upper2_initial_slope_test_param08, rep_upper2_initial_slope_test_param09, \
            rep_upper2_initial_slope_test_param10, rep_upper2_initial_slope_test_param11, rep_upper2_initial_slope_test_param12, \
            rep_upper2_initial_slope_test_param13, rep_upper2_initial_slope_test_param14))

        target_test_params_list = [(x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12, x13, x14) \
            for (x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12, x13, x14) \
            in target_test_params_base if x00 != x01 and x05 != x06 and x13 != x14 and \
                ((x10 == "1" and x11[:2] != x12[:2]) or (x11 == "1" and x10[:2] != x12[:2]) or (x12 == "1" and x11[:2] != x10[:2]) or (x10[:2] != x11[:2] != x12[:2]))]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 0, False, "022_01")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
    
    def test_upper_stance_upper2_up_23(self):
        rep_upper2_initial_slope_test_param00 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param01 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param02 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param03 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param04 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param05 = ["d1","d1i","d2","d2i","u","ui","1"]
        rep_upper2_initial_slope_test_param06 = ["d1","d1i","d2","d2i","u","ui","1"]
        rep_upper2_initial_slope_test_param07 = ["d1","d1i","d2","d2i","u","ui","1"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param00, rep_upper2_initial_slope_test_param01, \
            rep_upper2_initial_slope_test_param02, rep_upper2_initial_slope_test_param03, rep_upper2_initial_slope_test_param04, \
            rep_upper2_initial_slope_test_param05, rep_upper2_initial_slope_test_param06, rep_upper2_initial_slope_test_param07))

        target_test_params_list = [(x00, x01, x02, x03, x04, x05, x06, x07) \
            for (x00, x01, x02, x03, x04, x05, x06, x07) \
            in target_test_params_base if x00 != x01 and \
                ((x05 == "1" and x06[:2] != x07[:2]) or (x06 == "1" and x05[:2] != x07[:2]) or (x07 == "1" and x06[:2] != x05[:2]) or (x05[:2] != x06[:2] != x07[:2]))]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 0, False, "023_03_UP上半身2-上半身2")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)

    def test_upper_stance_upper2_up_24(self):
        rep_upper2_initial_slope_test_param00 = ["上半身2"]
        rep_upper2_initial_slope_test_param01 = ["上半身", "首"]
        rep_upper2_initial_slope_test_param02 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param03 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param04 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param05 = ["d1","d1i","d2","d2i","d3","d3i","du","dui","1"]
        rep_upper2_initial_slope_test_param06 = ["d1","d1i","d2","d2i","d3","d3i","du","dui","1"]
        rep_upper2_initial_slope_test_param07 = ["d1","d1i","d2","d2i","d3","d3i","du","dui","1"]
        rep_upper2_initial_slope_test_param08 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param09 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param10 = ["0","1-","1"]

        # 直積
        target_test_params_list = list(itertools.product(rep_upper2_initial_slope_test_param00, rep_upper2_initial_slope_test_param01, \
            rep_upper2_initial_slope_test_param02, rep_upper2_initial_slope_test_param03, rep_upper2_initial_slope_test_param04, \
            rep_upper2_initial_slope_test_param05, rep_upper2_initial_slope_test_param06, rep_upper2_initial_slope_test_param07, \
            rep_upper2_initial_slope_test_param08, rep_upper2_initial_slope_test_param09, rep_upper2_initial_slope_test_param10))

        # target_test_params_list = [(x00, x01, x02, x03, x04, x05, x06, x07) \
        #     for (x00, x01, x02, x03, x04, x05, x06, x07) \
        #     in target_test_params_base if x00 != x01 and \
        #         ((x05 == "1" and x06[:2] != x07[:2]) or (x06 == "1" and x05[:2] != x07[:2]) or (x07 == "1" and x06[:2] != x05[:2]) or (x05[:2] != x06[:2] != x07[:2]))]
        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 1, False, "024_02_上半身2u")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
        
    def test_upper_stance_upper2_up_25(self):
        rep_upper2_initial_slope_test_param00 = ["上半身2"]
        rep_upper2_initial_slope_test_param01 = ["首"]
        rep_upper2_initial_slope_test_param02_1 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param03_1 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param04_1 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param05 = ["上半身"]
        rep_upper2_initial_slope_test_param06 = ["頭"]
        rep_upper2_initial_slope_test_param07_1 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param08_1 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param09_1 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param10 = ["d1","d1i","d2","d2i","d6","d6i","d7","d7i","d5","d5i","00","01","02"]
        rep_upper2_initial_slope_test_param11 = ["d1","d1i","d2","d2i","d6","d6i","d7","d7i","d5","d5i","00","01","02"]
        rep_upper2_initial_slope_test_param12 = ["d1","d1i","d2","d2i","d6","d6i","d7","d7i","d5","d5i","00","01","02"]
        rep_upper2_initial_slope_test_param13 = ["d1","d1i","d2","d2i","d6","d6i","d7","d7i","d5","d5i","00","01","02"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param00, rep_upper2_initial_slope_test_param01, \
            rep_upper2_initial_slope_test_param02_1, rep_upper2_initial_slope_test_param03_1, rep_upper2_initial_slope_test_param04_1, \
            rep_upper2_initial_slope_test_param05, rep_upper2_initial_slope_test_param06, rep_upper2_initial_slope_test_param07_1, \
            rep_upper2_initial_slope_test_param08_1, rep_upper2_initial_slope_test_param09_1, rep_upper2_initial_slope_test_param10, \
            rep_upper2_initial_slope_test_param11, rep_upper2_initial_slope_test_param12, rep_upper2_initial_slope_test_param13))

        target_test_params_list = [(x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12, x13) \
            for (x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12, x13) \
            in target_test_params_base if x00 != x01 and x05 != x06 != x07 and x10[:2] != x11[:2] != x12[:2] != x13[:2]]

        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 1, False, "025_05")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
        




    
    def calc_stance(self, target_test_params, limit, exist_ok, prefix=""):
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

        os.makedirs("{0}/{1}_OK1".format(base_path, prefix), exist_ok=exist_ok)
        os.makedirs("{0}/{1}_OK2".format(base_path, prefix), exist_ok=exist_ok)
        os.makedirs("{0}/{1}_OK3".format(base_path, prefix), exist_ok=exist_ok)
        os.makedirs("{0}/{1}_OK4".format(base_path, prefix), exist_ok=exist_ok)
        os.makedirs("{0}/{1}_OK5".format(base_path, prefix), exist_ok=exist_ok)
        os.makedirs("{0}/{1}_OK6".format(base_path, prefix), exist_ok=exist_ok)
        os.makedirs("{0}/{1}_ALLOK".format(base_path, prefix), exist_ok=exist_ok)
        os.makedirs("{0}/{1}_NG".format(base_path, prefix), exist_ok=exist_ok)

        for test_param in target_test_params:
            logger.info("test_param: %s", test_param)

            file_name = "test_{0}.vmd".format(','.join([str(i) for i in test_param]))

            output_vmd_path = "{0}/{1}".format(base_path, file_name)

            copy_motion = copy.deepcopy(motion)

            try:
                main.main(copy_motion, trace_model, replace_model, output_vmd_path, \
                    is_avoidance, is_avoidance_finger, is_hand_ik, hand_distance, is_floor_hand, is_floor_hand_up, is_floor_hand_down, hand_floor_distance, leg_floor_distance, is_finger_ik, finger_distance, vmd_choice_values, rep_choice_values, rep_rate_values, \
                    camera_motion, camera_vmd_path, camera_pmx, output_camera_vmd_path, camera_y_offset, test_param)
            except Exception as e:
                print(traceback.format_exc())
                continue
            
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

                is_x_diff = org_euler.x() - limit <= to_euler.x() <= org_euler.x() + limit
                is_y_diff = org_euler.y() - limit <= to_euler.y() <= org_euler.y() + limit
                is_z_diff = org_euler.z() - limit <= to_euler.z() <= org_euler.z() + limit

                diff_euler = to_euler - org_euler

                is_x_same = round(diff_euler.x(),2) == 0
                is_y_same = round(diff_euler.y(),2) == 0
                is_z_same = round(diff_euler.z(),2) == 0

                result = (is_x_diff or is_y_diff or is_z_diff) or (is_x_same or is_y_same or is_z_same)
                result_list.append(is_x_diff or is_y_diff or is_z_diff)
                result_list.append(is_x_same or is_y_same or is_z_same)

                diff = "{0: 03.2f}#{1: 03.2f}#{2: 03.2f}".format( round(diff_euler.x(), 2), round(diff_euler.y(), 2), round(diff_euler.z(), 2) )
                diff_list.append(diff)

                if result:
                    logger.info("f: %s, org_target_pos: %s", bf.frame, org_target_pos)
                    logger.info("f: %s, rep_target_pos: %s", bf.frame, rep_target_pos)
                    logger.info("f: %s, org_rotation: %s", bf.frame, org_euler)
                    logger.info("f: %s, rep_rotation: %s", bf.frame, to_euler)
                    logger.info("f: %s, is_x_diff: %s, is_y_diff: %s, is_z_diff: %s, is_x_same: %s, is_y_same: %s, is_z_same: %s", bf.frame, is_x_diff, is_y_diff, is_z_diff, is_x_same, is_y_same, is_z_same)

            resutl_file_name = "{0}_{1}_{2}.vmd".format(','.join([str(i) for i in test_param]), ','.join([str(i) for i in result_list]), ','.join([str(i) for i in diff_list]))
            
            if result_list.count(True) == len(target_frames) * 2:
                # TRUE(全一致した場合)
                shutil.move(output_vmd_path, "{0}/{1}_ALLOK/{2}".format(base_path, prefix, resutl_file_name))
                ok_list.append(test_param)
                logger.info("result: TRUE")
            elif result_list.count(True) > 0:
                # TRUE(一致した場合)
                shutil.move(output_vmd_path, "{0}/{1}_OK{2}/{3}".format(base_path, prefix, result_list.count(True), resutl_file_name))
                ok_list.append(test_param)
                logger.info("result: TRUE")
            else:
                # FALSE(一致しない場合)
                shutil.move(output_vmd_path, "{0}/{1}_NG/{2}".format(base_path, prefix, resutl_file_name))
                logger.info("result: FALSE")
            
        return ok_list

if __name__ == "__main__":
    unittest.main(defaultTest="TestSubStance.test_upper_stance_upper2_up_25")
