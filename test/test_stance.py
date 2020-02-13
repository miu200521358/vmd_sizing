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
import glob
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
        
    def test_upper_stance_upper2_up_26(self):
        rep_upper2_initial_slope_test_param00 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param01 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param02 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param03 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param04 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param05 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param06 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param07 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param08 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param09 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param10 = ["d1","d1i","d2","d2i","d3","d3i","00"]
        rep_upper2_initial_slope_test_param11 = ["d1","d1i","d2","d2i","d3","d3i","00"]
        rep_upper2_initial_slope_test_param12 = ["d1","d1i","d2","d2i","d3","d3i","00"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param00, rep_upper2_initial_slope_test_param01, \
            rep_upper2_initial_slope_test_param02, rep_upper2_initial_slope_test_param03, rep_upper2_initial_slope_test_param04, \
            rep_upper2_initial_slope_test_param05, rep_upper2_initial_slope_test_param06, rep_upper2_initial_slope_test_param07, \
            rep_upper2_initial_slope_test_param08, rep_upper2_initial_slope_test_param09, rep_upper2_initial_slope_test_param10, \
            rep_upper2_initial_slope_test_param11, rep_upper2_initial_slope_test_param12))

        target_test_params_list = [(x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12) \
            for (x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12) \
            in target_test_params_base if x00 != x01 and x05 != x06 and x10[:2] != x11[:2] != x12[:2]]

        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 1, False, "026_05")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
        
    def test_upper_stance_upper2_up_27(self):
        rep_upper2_initial_slope_test_param00 = ["上半身"]
        rep_upper2_initial_slope_test_param01 = ["上半身2"]
        rep_upper2_initial_slope_test_param02 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param03 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param04 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param05 = ["上半身2"]
        rep_upper2_initial_slope_test_param06 = ["頭"]
        rep_upper2_initial_slope_test_param07 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param08 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param09 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param10 = ["d1i"]
        rep_upper2_initial_slope_test_param11 = ["d2i"]
        rep_upper2_initial_slope_test_param12 = ["d1"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param00, rep_upper2_initial_slope_test_param01, \
            rep_upper2_initial_slope_test_param02, rep_upper2_initial_slope_test_param03, rep_upper2_initial_slope_test_param04, \
            rep_upper2_initial_slope_test_param05, rep_upper2_initial_slope_test_param06, rep_upper2_initial_slope_test_param07, \
            rep_upper2_initial_slope_test_param08, rep_upper2_initial_slope_test_param09, rep_upper2_initial_slope_test_param10, \
            rep_upper2_initial_slope_test_param11, rep_upper2_initial_slope_test_param12))

        target_test_params_list = [(x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12) \
            for (x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12) \
            in target_test_params_base if x00 != x01 and x05 != x06 and x10[:2] != x11[:2] != x12[:2]]

        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 1, False, "027_04")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)

    def test_upper_stance_upper2_up_28(self):
        rep_upper2_initial_slope_test_param00 = ["上半身"]
        rep_upper2_initial_slope_test_param01 = ["上半身2"]
        rep_upper2_initial_slope_test_param02 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param03 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param04 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param05 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param06 = ["上半身", "上半身2", "頭", "首"]
        rep_upper2_initial_slope_test_param07 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param08 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param09 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param10 = ["d1","d1i","d2","d2i","00","01"]
        rep_upper2_initial_slope_test_param11 = ["d1","d1i","d2","d2i","00","01"]
        rep_upper2_initial_slope_test_param12 = ["d1","d1i","d2","d2i","00","01"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param00, rep_upper2_initial_slope_test_param01, \
            rep_upper2_initial_slope_test_param02, rep_upper2_initial_slope_test_param03, rep_upper2_initial_slope_test_param04, \
            rep_upper2_initial_slope_test_param05, rep_upper2_initial_slope_test_param06, rep_upper2_initial_slope_test_param07, \
            rep_upper2_initial_slope_test_param08, rep_upper2_initial_slope_test_param09, rep_upper2_initial_slope_test_param10, \
            rep_upper2_initial_slope_test_param11, rep_upper2_initial_slope_test_param12))

        target_test_params_list = [(x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12) \
            for (x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12) \
            in target_test_params_base if x00 != x01 and x05 != x06 and x10[:2] != x11[:2] != x12[:2]]

        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 1, False, "028_01")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)

    def test_upper_stance_upper2_up_29(self):
        rep_upper2_initial_slope_test_param00 = ["上半身"]
        rep_upper2_initial_slope_test_param01 = ["上半身2"]
        rep_upper2_initial_slope_test_param02 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param03 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param04 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param05 = ["上半身"]
        rep_upper2_initial_slope_test_param06 = ["頭"]
        rep_upper2_initial_slope_test_param07 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param08 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param09 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param10 = ["d1","d1i","d2","d2i","00"]
        rep_upper2_initial_slope_test_param11 = ["d1","d1i","d2","d2i","00"]
        rep_upper2_initial_slope_test_param12 = ["d1","d1i","d2","d2i","00"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param00, rep_upper2_initial_slope_test_param01, \
            rep_upper2_initial_slope_test_param02, rep_upper2_initial_slope_test_param03, rep_upper2_initial_slope_test_param04, \
            rep_upper2_initial_slope_test_param05, rep_upper2_initial_slope_test_param06, rep_upper2_initial_slope_test_param07, \
            rep_upper2_initial_slope_test_param08, rep_upper2_initial_slope_test_param09, rep_upper2_initial_slope_test_param10, \
            rep_upper2_initial_slope_test_param11, rep_upper2_initial_slope_test_param12))

        target_test_params_list = [(x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12) \
            for (x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12) \
            in target_test_params_base if x00 != x01 and x05 != x06 and x10[:2] != x11[:2] != x12[:2]]

        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 1, False, "029_03")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)

    def test_upper_stance_upper2_up_31(self):
        rep_upper2_initial_slope_test_param00 = ["上半身"]
        rep_upper2_initial_slope_test_param01 = ["上半身2"]
        rep_upper2_initial_slope_test_param02 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param03 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param04 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param05 = ["上半身2"]
        rep_upper2_initial_slope_test_param06 = ["頭"]
        rep_upper2_initial_slope_test_param07 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param08 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param09 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param10 = ["d1","d1i","d2","d2i","00","01"]
        rep_upper2_initial_slope_test_param11 = ["d1","d1i","d2","d2i","00","01"]
        rep_upper2_initial_slope_test_param12 = ["d1","d1i","d2","d2i","00","01"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param00, rep_upper2_initial_slope_test_param01, \
            rep_upper2_initial_slope_test_param02, rep_upper2_initial_slope_test_param03, rep_upper2_initial_slope_test_param04, \
            rep_upper2_initial_slope_test_param05, rep_upper2_initial_slope_test_param06, rep_upper2_initial_slope_test_param07, \
            rep_upper2_initial_slope_test_param08, rep_upper2_initial_slope_test_param09, rep_upper2_initial_slope_test_param10, \
            rep_upper2_initial_slope_test_param11, rep_upper2_initial_slope_test_param12))

        target_test_params_list = [(x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12) \
            for (x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12) \
            in target_test_params_base if x00 != x01 and x05 != x06 and x10[:2] != x11[:2] != x12[:2]]

        random.shuffle(target_test_params_list)

        ok_list = self.calc_stance(target_test_params_list, 1, False, "030_07_上半身2-頭")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)

    def test_upper_stance_upper2_up_32(self):
        rep_upper2_initial_slope_test_param00 = ["上半身"]
        rep_upper2_initial_slope_test_param01 = ["上半身2"]
        rep_upper2_initial_slope_test_param02 = ["1-"]
        rep_upper2_initial_slope_test_param03 = ["1"]
        rep_upper2_initial_slope_test_param04 = ["0"]
        rep_upper2_initial_slope_test_param05 = ["首"]
        rep_upper2_initial_slope_test_param06 = ["頭"]
        rep_upper2_initial_slope_test_param07 = ["1"]
        rep_upper2_initial_slope_test_param08 = ["0"]
        rep_upper2_initial_slope_test_param09 = ["0"]
        rep_upper2_initial_slope_test_param10 = [(0,"上半身"), (1,"上半身2"), (2,"首"), (3,"頭")]
        rep_upper2_initial_slope_test_param11 = [(0,"上半身"), (1,"上半身2"), (2,"首"), (3,"頭")]
        rep_upper2_initial_slope_test_param12 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param13 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param14 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param15 = ["d1","d1i","d2","d2i","d3","d3i","d0","d0i","00","01"]
        rep_upper2_initial_slope_test_param16 = ["d1","d1i","d2","d2i","d3","d3i","d0","d0i","00","01"]
        rep_upper2_initial_slope_test_param17 = ["d1","d1i","d2","d2i","d3","d3i","d0","d0i","00","01"]
        rep_upper2_initial_slope_test_param18 = ["d1","d1i","d2","d2i","d3","d3i","d0","d0i","00","01"]
        rep_upper2_initial_slope_test_param19 = ["d1","d1i","d2","d2i","d3","d3i","d0","d0i","00","01"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param00, rep_upper2_initial_slope_test_param01, \
            rep_upper2_initial_slope_test_param02, rep_upper2_initial_slope_test_param03, rep_upper2_initial_slope_test_param04, \
            rep_upper2_initial_slope_test_param05, rep_upper2_initial_slope_test_param06, rep_upper2_initial_slope_test_param07, \
            rep_upper2_initial_slope_test_param08, rep_upper2_initial_slope_test_param09, rep_upper2_initial_slope_test_param10, \
            rep_upper2_initial_slope_test_param11, rep_upper2_initial_slope_test_param12, rep_upper2_initial_slope_test_param13, \
            rep_upper2_initial_slope_test_param14, rep_upper2_initial_slope_test_param15, rep_upper2_initial_slope_test_param16, \
            rep_upper2_initial_slope_test_param17, rep_upper2_initial_slope_test_param18, rep_upper2_initial_slope_test_param19, \
        ))

        target_test_params_list = [(x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10[1], x11[1], x12, x13, x14, x15, x16, x17, x18, x19) \
            for (x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12, x13, x14, x15, x16, x17, x18, x19) \
            in target_test_params_base if x10 != x11 and x10[0] < x11[0] and x15[:2] not in [x16[:2], x17[:2], x18[:2], x19[:2]] and x16[:2] not in [x15[:2], x17[:2], x18[:2], x19[:2]] and x17[:2] not in [x16[:2], x15[:2], x18[:2], x19[:2]] \
                 and x18[:2] not in [x16[:2], x17[:2], x15[:2], x19[:2]] and x19[:2] not in [x16[:2], x17[:2], x18[:2], x15[:2]]]

        random.shuffle(target_test_params_list)
        
        prefix = "032-02_03-02追加"
        ok_list = self.calc_stance(target_test_params_list, 1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)

    def test_upper_stance_upper2_up_33(self):
        rep_upper2_initial_slope_test_param00 = ["上半身"]
        rep_upper2_initial_slope_test_param01 = ["上半身2"]
        rep_upper2_initial_slope_test_param02 = ["0"]
        rep_upper2_initial_slope_test_param03 = ["1"]
        rep_upper2_initial_slope_test_param04 = ["1-"]
        rep_upper2_initial_slope_test_param05 = ["上半身2"]
        rep_upper2_initial_slope_test_param06 = ["頭"]
        rep_upper2_initial_slope_test_param07 = ["0"]
        rep_upper2_initial_slope_test_param08 = ["1"]
        rep_upper2_initial_slope_test_param09 = ["1"]
        rep_upper2_initial_slope_test_param10 = [(0,"上半身"), (1,"上半身2"), (2,"首"), (3,"頭")]
        rep_upper2_initial_slope_test_param11 = [(0,"上半身"), (1,"上半身2"), (2,"首"), (3,"頭")]
        rep_upper2_initial_slope_test_param12 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param13 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param14 = ["0","1-","1"]
        rep_upper2_initial_slope_test_param15 = ["d1","d1i","d2","d2i","d3","d3i","d0","d0i","00","01"]
        rep_upper2_initial_slope_test_param16 = ["d1","d1i","d2","d2i","d3","d3i","d0","d0i","00","01"]
        rep_upper2_initial_slope_test_param17 = ["d1","d1i","d2","d2i","d3","d3i","d0","d0i","00","01"]
        rep_upper2_initial_slope_test_param18 = ["d1","d1i","d2","d2i","d3","d3i","d0","d0i","00","01"]
        rep_upper2_initial_slope_test_param19 = ["d1","d1i","d2","d2i","d3","d3i","d0","d0i","00","01"]

        # 直積
        target_test_params_base = list(itertools.product(rep_upper2_initial_slope_test_param00, rep_upper2_initial_slope_test_param01, \
            rep_upper2_initial_slope_test_param02, rep_upper2_initial_slope_test_param03, rep_upper2_initial_slope_test_param04, \
            rep_upper2_initial_slope_test_param05, rep_upper2_initial_slope_test_param06, rep_upper2_initial_slope_test_param07, \
            rep_upper2_initial_slope_test_param08, rep_upper2_initial_slope_test_param09, rep_upper2_initial_slope_test_param10, \
            rep_upper2_initial_slope_test_param11, rep_upper2_initial_slope_test_param12, rep_upper2_initial_slope_test_param13, \
            rep_upper2_initial_slope_test_param14, rep_upper2_initial_slope_test_param15, rep_upper2_initial_slope_test_param16, \
            rep_upper2_initial_slope_test_param17, rep_upper2_initial_slope_test_param18, rep_upper2_initial_slope_test_param19, \
        ))

        target_test_params_list = [(x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10[1], x11[1], x12, x13, x14, x15, x16, x17, x18, x19) \
            for (x00, x01, x02, x03, x04, x05, x06, x07, x08, x09, x10, x11, x12, x13, x14, x15, x16, x17, x18, x19) \
            in target_test_params_base if x10 != x11 and x10[0] < x11[0] and x15[:2] not in [x16[:2], x17[:2], x18[:2], x19[:2]] and x16[:2] not in [x15[:2], x17[:2], x18[:2], x19[:2]] and x17[:2] not in [x16[:2], x15[:2], x18[:2], x19[:2]] \
                 and x18[:2] not in [x16[:2], x17[:2], x15[:2], x19[:2]] and x19[:2] not in [x16[:2], x17[:2], x18[:2], x15[:2]]]

        random.shuffle(target_test_params_list)
        
        prefix = "033-01_上半身2-頭"
        ok_list = self.calc_stance(target_test_params_list, 1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)
                                                                

    def test_upper_stance_upper2_up_34(self):
        
        # ボーン名の組合せ
        rep_upper2_initial_slope_test_bone_names = [(0,"上半身"), (1,"上半身2"), (2,"首"), (3,"頭")]
        target_test_params_base_bone_names = list(itertools.product(rep_upper2_initial_slope_test_bone_names, repeat=2))
        target_test_params_list_bone_names = [(x00[1], x01[1]) for (x00, x01) in target_test_params_base_bone_names if x00[0] < x01[0]]
        print("bone_names LIST: %s" % len(target_test_params_list_bone_names))

        # 数字の組合せ
        rep_upper2_initial_slope_test_numbers = ["0","1-","1"]
        base_target_test_params_list_numbers = list(itertools.product(rep_upper2_initial_slope_test_numbers, repeat=3))
        list_target_test_params_list_numbers = [(x00, x01, x02) for (x00, x01, x02) in base_target_test_params_list_numbers if (x00 != x01 or x01 != x02)]
        print("numbers LIST: %s" % len(list_target_test_params_list_numbers))

        # 最後の組合せ
        rep_upper2_initial_slope_test_pairs = ["d1","d1i","d2","d2i","d3","d3i","00"]
        target_test_params_base_pairs = list(itertools.product(rep_upper2_initial_slope_test_pairs, repeat=4))
        target_test_params_list_pairs = [(x00, x01, x02, x03) for (x00, x01, x02, x03) in target_test_params_base_pairs 
            if x00[:3] not in [x01[:3], x02[:3], x03[:3]] and x01[:3] not in [x00[:3], x02[:3], x03[:3]] and x02[:3] not in [x01[:3], x00[:3], x03[:3]] \
            and x03[:3] not in [x01[:3], x02[:3], x00[:3]]]
        print("pairs LIST: %s" % len(target_test_params_list_pairs))

        # 直積
        target_test_params_base = list(itertools.product(target_test_params_list_bone_names, target_test_params_list_bone_names, \
            list_target_test_params_list_numbers, list_target_test_params_list_numbers, target_test_params_list_pairs))

        target_test_params_list = [("頭", "上半身2", "1-", "0", "0", names1[0], names1[1], numbers1[0], numbers1[1], numbers1[2], \
            names2[0], names2[1], numbers2[0], numbers2[1], numbers2[2], pairs[0], pairs[1], pairs[2], pairs[3]) \
            for (names1, names2, numbers1, numbers2, pairs) in target_test_params_base]
        random.shuffle(target_test_params_list)
        print("targets LIST: %s" % len(target_test_params_list))
        
        prefix = "034-10"
        ok_list = self.calc_stance(target_test_params_list, 0.1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)
                       

    def test_upper_stance_upper2_up_35(self):
        
        # ボーン名の組合せ
        rep_upper2_initial_slope_test_bone_names = [(0,"上半身"), (1,"上半身2"), (2,"首"), (3,"頭")]
        target_test_params_base_bone_names = list(itertools.product(rep_upper2_initial_slope_test_bone_names, repeat=2))
        target_test_params_list_bone_names = [(x00[1], x01[1]) for (x00, x01) in target_test_params_base_bone_names if x00[0] < x01[0]]
        print("bone_names LIST: %s" % len(target_test_params_list_bone_names))

        # 数字の組合せ
        rep_upper2_initial_slope_test_numbers = ["0","1-","1"]
        base_target_test_params_list_numbers = list(itertools.product(rep_upper2_initial_slope_test_numbers, repeat=3))
        list_target_test_params_list_numbers = [(x00, x01, x02) for (x00, x01, x02) in base_target_test_params_list_numbers if (x00 != x01 or x01 != x02)]
        print("numbers LIST: %s" % len(list_target_test_params_list_numbers))

        # 最後の組合せ
        rep_upper2_initial_slope_test_pairs = ["d1","d1i","d2","d2i","d3","d3i","00","01"]
        target_test_params_base_pairs = list(itertools.product(rep_upper2_initial_slope_test_pairs, repeat=4))
        target_test_params_list_pairs = [(x00, x01, x02, x03) for (x00, x01, x02, x03) in target_test_params_base_pairs 
            if x00[:3] not in [x01[:3], x02[:3], x03[:3]] and x01[:3] not in [x00[:3], x02[:3], x03[:3]] and x02[:3] not in [x01[:3], x00[:3], x03[:3]] \
            and x03[:3] not in [x01[:3], x02[:3], x00[:3]]]
        print("pairs LIST: %s" % len(target_test_params_list_pairs))

        # 直積
        target_test_params_base = list(itertools.product(target_test_params_list_bone_names, \
            list_target_test_params_list_numbers, list_target_test_params_list_numbers, target_test_params_list_pairs))

        target_test_params_list = [("頭", "上半身2", "1-", "0", "0", "上半身", "上半身2", numbers1[0], numbers1[1], numbers1[2], \
            names2[0], names2[1], numbers2[0], numbers2[1], numbers2[2], pairs[0], pairs[1], pairs[2], pairs[3]) \
            for (names2, numbers1, numbers2, pairs) in target_test_params_base]
        random.shuffle(target_test_params_list)
        print("targets LIST: %s" % len(target_test_params_list))
        
        prefix = "035-02"
        ok_list = self.calc_stance(target_test_params_list, 0.1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)
                             

    def test_upper_stance_upper2_up_36(self):
        
        # 最後の組合せ
        rep_upper2_initial_slope_test_pairs = ["d1","d1i","d2","d2i","d3","d3i","00","01"]
        target_test_params_base_pairs = list(itertools.product(rep_upper2_initial_slope_test_pairs, repeat=4))
        target_test_params_list_pairs = [(x00, x01, x02, x03) for (x00, x01, x02, x03) in target_test_params_base_pairs 
            if x00[:3] not in [x01[:3], x02[:3], x03[:3]] and x01[:3] not in [x00[:3], x02[:3], x03[:3]] and x02[:3] not in [x01[:3], x00[:3], x03[:3]] \
            and x03[:3] not in [x01[:3], x02[:3], x00[:3]]]
        print("pairs LIST: %s" % len(target_test_params_list_pairs))

        target_test_params_list = [("首", "上半身", "1-", "0", "0", "上半身", "上半身2", "0", "0", "1-", \
            "首", "頭", "0", "0", "1-", "01", pairs[0], pairs[1], pairs[2]) \
            for (pairs) in target_test_params_list_pairs]
        random.shuffle(target_test_params_list)
        print("targets LIST: %s" % len(target_test_params_list))
        
        prefix = "036-03"
        ok_list = self.calc_stance(target_test_params_list, 0.1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)
                       


    def test_upper_stance_upper2_up_37(self):
        
        # ボーン名の組合せ
        rep_upper2_initial_slope_test_bone_names = [(0,"上半身"), (1,"上半身2"), (2,"首"), (3,"頭")]
        target_test_params_base_bone_names = list(itertools.product(rep_upper2_initial_slope_test_bone_names, repeat=2))
        target_test_params_list_bone_names = [(x00[1], x01[1]) for (x00, x01) in target_test_params_base_bone_names if x00[0] < x01[0]]
        print("bone_names LIST: %s" % len(target_test_params_list_bone_names))

        # 直積
        target_test_params_base = list(itertools.product(target_test_params_list_bone_names, target_test_params_list_bone_names, target_test_params_list_bone_names))

        # 首,上半身,1-,0,0,上半身,上半身2,0,0,1-,首,頭,0,0,1-,01,d3,d1,d2_True,True,True,True,False,False_ 2.77#-0.00#-0.37,-4.20# 0.00# 0.11, 1.03#-0.28#-4.72.vmd
        target_test_params_list = [(names1[0], names1[1], "1-", "0", "0", names2[0], names2[1], "0", "0", "1-", \
            names3[0], names3[1], "0", "0", "1-", "01", "d3", "d1", "d2") \
            for (names1, names2, names3) in target_test_params_base]
        random.shuffle(target_test_params_list)
        print("targets LIST: %s" % len(target_test_params_list))
        
        prefix = "037-01"
        ok_list = self.calc_stance(target_test_params_list, 0.1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)
                             

    # 頭,上半身2,1-,0,0,上半身,上半身2,0,1,0,上半身2,頭,0,1,1,d2i,d3i,00,d2_True,True,True,False,True,True_ 0.85# 0.00# 90.05,-6.12# 0.02# 90.53,-0.87#-0.00# 85.68
    def test_upper_stance_upper2_up_38(self):
        
        # # ボーン名の組合せ
        # rep_upper2_initial_slope_test_bone_names = [(0,"上半身"), (1,"上半身2"), (2,"首"), (3,"頭")]
        # target_test_params_base_bone_names = list(itertools.product(rep_upper2_initial_slope_test_bone_names, repeat=2))
        # target_test_params_list_bone_names = [(x00[1], x01[1]) for (x00, x01) in target_test_params_base_bone_names if x00[0] < x01[0]]
        # print("bone_names LIST: %s" % len(target_test_params_list_bone_names))

        # 数字の組合せ
        rep_upper2_initial_slope_test_numbers = ["0","1-","1"]
        base_target_test_params_list_numbers = list(itertools.product(rep_upper2_initial_slope_test_numbers, repeat=3))
        list_target_test_params_list_numbers = [(x00, x01, x02) for (x00, x01, x02) in base_target_test_params_list_numbers if (x00 != x01 or x01 != x02)]
        print("numbers LIST: %s" % len(list_target_test_params_list_numbers))

        # 最後の組合せ
        rep_upper2_initial_slope_test_pairs = ["d2","d2i","d3","d3i","00"]
        target_test_params_base_pairs = list(itertools.product(rep_upper2_initial_slope_test_pairs, repeat=3))
        target_test_params_list_pairs = [(x00, x01, x02) for (x00, x01, x02) in target_test_params_base_pairs 
            if x00[:3] not in [x01[:3], x02[:3] and x01[:3] not in [x00[:3], x02[:3]] and x02[:3] not in [x01[:3], x00[:3]] ]]
        print("pairs LIST: %s" % len(target_test_params_list_pairs))

        # 直積
        target_test_params_base = list(itertools.product(list_target_test_params_list_numbers, list_target_test_params_list_numbers, target_test_params_list_pairs))

        target_test_params_list = [("頭", "上半身2", "1-", "0", "0", "上半身", "上半身2", numbers1[0], numbers1[1], numbers1[2], \
            "上半身2", "頭", numbers2[0], numbers2[1], numbers2[2], pairs[0], pairs[1], pairs[2], "01") \
            for (numbers1, numbers2, pairs) in target_test_params_base]
        random.shuffle(target_test_params_list)
        print("targets LIST: %s" % len(target_test_params_list))
        
        prefix = "038-01"
        ok_list = self.calc_stance(target_test_params_list, 0.1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)
                            

    # 頭,上半身2,1-,0,0,上半身,上半身2,0,0,1-,上半身2,頭,0,0,1,d2i,d3i,d2,01_True,True,True,False,True,True_ 0.85# 0.00# 90.05,-6.12# 0.02# 90.53,-0.87#-0.00# 85.68
    def test_upper_stance_upper2_up_40(self):
        
        # ボーン名の組合せ
        rep_upper2_initial_slope_test_bone_names = [(0,"上半身"), (1,"上半身2"), (2,"首"), (3,"頭")]
        target_test_params_base_bone_names = list(itertools.product(rep_upper2_initial_slope_test_bone_names, repeat=2))
        target_test_params_list_bone_names = [(x00[1], x01[1]) for (x00, x01) in target_test_params_base_bone_names if x00[0] < x01[0] and ((0,"上半身"), (1,"上半身2")) != (x00, x01) and ((1,"上半身2"), (3,"頭")) != (x00, x01)]
        print("bone_names LIST: %s" % len(target_test_params_list_bone_names))

        # 数字の組合せ
        rep_upper2_initial_slope_test_numbers = ["0","1-","1"]
        list_target_test_params_base_numbers = list(itertools.product(rep_upper2_initial_slope_test_numbers, repeat=3))
        list_target_test_params_list_numbers = [(x00, x01, x02) for (x00, x01, x02) in list_target_test_params_base_numbers if x00 == "0" or x01 == "0" or x02 == "0" ]
        print("numbers LIST: %s" % len(list_target_test_params_list_numbers))

        # 最後の組合せ
        rep_upper2_initial_slope_test_pairs = ["d1","d1i","d2","d2i","d3","d3i"]
        target_test_params_base_pairs = list(itertools.product(rep_upper2_initial_slope_test_pairs, repeat=3))
        target_test_params_list_pairs = [(x00, x01, x02) for (x00, x01, x02) in target_test_params_base_pairs 
            if x00[:2] not in [x01[:2], x02[:2]] and x01[:2] not in [x00[:2], x02[:2]] and x02[:2] not in [x01[:2], x00[:2]] ]
        print("pairs LIST: %s" % len(target_test_params_list_pairs))

        # 直積
        target_test_params_base = list(itertools.product(list_target_test_params_list_numbers, list_target_test_params_list_numbers, list_target_test_params_list_numbers, target_test_params_list_bone_names, target_test_params_list_pairs))

        target_test_params_list = [("上半身", "上半身2", numbers1[0], numbers1[1], numbers1[2], "上半身2", "頭", numbers2[0], numbers2[1], numbers2[2], \
            names1[0], names1[1], numbers3[0], numbers3[1], numbers3[2], pairs[0], pairs[1], pairs[2], "01") \
            for (numbers1, numbers2, numbers3, names1, pairs) in target_test_params_base]
        random.shuffle(target_test_params_list)
        print("targets LIST: %s" % len(target_test_params_list))
        
        prefix = "040-02"
        ok_list = self.calc_stance(target_test_params_list, 0.1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)
    
    # 上半身,上半身2,0,0,1-,上半身2,頭,0,1,1,首,頭,1,0,0,d3i,d2i,d1,01_True,True,True,False,False,False_ 3.97#-0.00# 0.05,-3.00#-0.01# 0.54, 2.22#-0.45#-4.28
    # 上半身,上半身2,0,1-,1-,上半身2,頭,0,1,1,首,頭,1,0,0,d3i,d1i,d2,01_True,True,True,False,False,False_ 3.97#-0.00# 0.05,-3.00#-0.01# 0.54, 2.22#-0.45#-4.28
    # 上半身,上半身2,1-,1-,0,上半身2,頭,1,0,0,首,頭,1,0,0,d2i,d3i,d1i,01_True,False,True,False,True,False_ 0.41#-0.05# 1.10,-6.56#-0.03# 1.58,-1.31# 0.01#-3.28
    def test_upper_stance_upper2_up_41(self):
        
        # # ボーン名の組合せ
        # rep_upper2_initial_slope_test_bone_names = [(0,"上半身"), (1,"上半身2"), (2,"首"), (3,"頭")]
        # target_test_params_base_bone_names = list(itertools.product(rep_upper2_initial_slope_test_bone_names, repeat=2))
        # target_test_params_list_bone_names = [(x00[1], x01[1]) for (x00, x01) in target_test_params_base_bone_names if x00[0] < x01[0] and ((0,"上半身"), (1,"上半身2")) != (x00, x01) and ((1,"上半身2"), (3,"頭")) != (x00, x01)]
        # print("bone_names LIST: %s" % len(target_test_params_list_bone_names))

        # 数字の組合せ
        rep_upper2_initial_slope_test_numbers = ["0","1-","1"]
        list_target_test_params_base_numbers = list(itertools.product(rep_upper2_initial_slope_test_numbers, repeat=3))
        list_target_test_params_list_numbers = [(x00, x01, x02) for (x00, x01, x02) in list_target_test_params_base_numbers if x00 == "0" or x01 == "0" or x02 == "0" ]
        print("numbers LIST: %s" % len(list_target_test_params_list_numbers))

        # 最後の組合せ
        rep_upper2_initial_slope_test_pairs = ["d1","d1i","d2","d2i","d3","d3i"]
        target_test_params_base_pairs = list(itertools.product(rep_upper2_initial_slope_test_pairs, repeat=3))
        target_test_params_list_pairs = [(x00, x01, x02) for (x00, x01, x02) in target_test_params_base_pairs 
            if x00[:2] not in [x01[:2], x02[:2]] and x01[:2] not in [x00[:2], x02[:2]] and x02[:2] not in [x01[:2], x00[:2]] ]
        print("pairs LIST: %s" % len(target_test_params_list_pairs))

        # 直積
        target_test_params_base = list(itertools.product(list_target_test_params_list_numbers, list_target_test_params_list_numbers, list_target_test_params_list_numbers, target_test_params_list_pairs))

        target_test_params_list = [("上半身", "上半身2", numbers1[0], numbers1[1], numbers1[2], "上半身2", "頭", numbers2[0], numbers2[1], numbers2[2], \
            "首", "頭", numbers3[0], numbers3[1], numbers3[2], pairs[0], pairs[1], pairs[2], "01") \
            for (numbers1, numbers2, numbers3, pairs) in target_test_params_base]
        random.shuffle(target_test_params_list)
        print("targets LIST: %s" % len(target_test_params_list))
        
        prefix = "041-02"
        ok_list = self.calc_stance(target_test_params_list, 0.1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)
                             
    
    # 上半身,上半身2,0,0,1-,上半身2,頭,0,1,1,首,頭,1,0,0,d3i,d2i,d1,01_True,True,True,False,False,False_ 3.97#-0.00# 0.05,-3.00#-0.01# 0.54, 2.22#-0.45#-4.28
    # 上半身,上半身2,0,1-,1-,上半身2,頭,0,1,1,首,頭,1,0,0,d3i,d1i,d2,01_True,True,True,False,False,False_ 3.97#-0.00# 0.05,-3.00#-0.01# 0.54, 2.22#-0.45#-4.28
    # 上半身,上半身2,1-,1-,0,上半身2,頭,1,0,0,首,頭,1,0,0,d2i,d3i,d1i,01_True,False,True,False,True,False_ 0.41#-0.05# 1.10,-6.56#-0.03# 1.58,-1.31# 0.01#-3.28
    def test_upper_stance_upper2_up_42(self):
        
        # ボーン名の組合せ
        rep_upper2_initial_slope_test_bone_names = [(0,"上半身"), (1,"上半身2"), (2,"首"), (3,"頭")]
        target_test_params_base_bone_names = list(itertools.product(rep_upper2_initial_slope_test_bone_names, repeat=2))
        target_test_params_list_bone_names = [(x00[1], x01[1]) for (x00, x01) in target_test_params_base_bone_names if x00[0] < x01[0]]
        print("bone_names LIST: %s" % len(target_test_params_list_bone_names))

        # 数字の組合せ
        rep_upper2_initial_slope_test_numbers = ["0","1-","1"]
        list_target_test_params_base_numbers = list(itertools.product(rep_upper2_initial_slope_test_numbers, repeat=3))
        list_target_test_params_list_numbers = [(x00, x01, x02) for (x00, x01, x02) in list_target_test_params_base_numbers if 0 < [x00, x01, x02].count("0") < 3 ]
        print("numbers LIST: %s" % len(list_target_test_params_list_numbers))

        # 最後の組合せ
        rep_upper2_initial_slope_test_pairs = ["d1","d2","d3"]
        target_test_params_base_pairs = list(itertools.product(rep_upper2_initial_slope_test_pairs, repeat=3))
        target_test_params_list_pairs = [(x00, x01, x02) for (x00, x01, x02) in target_test_params_base_pairs 
            if x00[:2] not in [x01[:2], x02[:2]] and x01[:2] not in [x00[:2], x02[:2]] and x02[:2] not in [x01[:2], x00[:2]] ]
        print("pairs LIST: %s" % len(target_test_params_list_pairs))

        # 直積
        target_test_params_base = list(itertools.product(target_test_params_list_bone_names, list_target_test_params_list_numbers, \
            target_test_params_list_bone_names, list_target_test_params_list_numbers, \
            target_test_params_list_bone_names, list_target_test_params_list_numbers, target_test_params_list_pairs))

        target_test_params_list = [(names1[0], names1[1], numbers1[0], numbers1[1], numbers1[2], names2[0], names2[1], numbers2[0], numbers2[1], numbers2[2], \
            names3[0], names3[1], numbers3[0], numbers3[1], numbers3[2], pairs[0], pairs[1], pairs[2], "01") \
            for (names1, numbers1, names2, numbers2, names3, numbers3, pairs) in target_test_params_base]
        random.shuffle(target_test_params_list)
        print("targets LIST: %s" % len(target_test_params_list))
        
        prefix = "042-02"
        ok_list = self.calc_stance(target_test_params_list, 0.1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)
                             
    # 首,頭,0,1-,0,上半身,上半身2,0,1,1,上半身2,頭,1,1,0,d2,d3,d1,01_True,False,True,False,True,False_-0.18#-0.08# 9.07,-7.14#-0.05# 9.56,-1.89# 0.06# 4.69
    # 首,頭,1-,1-,0,上半身,上半身2,1,1-,0,首,頭,1,1,0,d3,d2,d1,01_True,True,True,False,False,False_ 4.72#-0.00# 1.11,-2.25#-0.01# 1.60, 2.96#-0.56#-3.21
    # 上半身,首,1,1,0,上半身,首,1-,1-,0,首,頭,1,0,0,d2,d3,d1,01_True,False,True,False,True,False_ 4.00#-0.08# 4.27,-2.97#-0.09# 4.77, 2.24#-0.54#-0.05
    # 上半身,首,1,1,0,上半身,上半身2,1-,0,1-,上半身2,頭,1,0,1,d2,d1,d3,01_True,False,True,False,True,False_ 1.55# 0.04#-9.84,-5.42# 0.06#-9.36,-0.17#-0.06#-14.21
    # 上半身,上半身2,0,1,0,上半身,頭,1,1,0,上半身,上半身2,0,1-,1,d3,d2,d1,01_True,False,True,False,True,False_ 0.70# 0.06# 11.30,-6.26# 0.08# 11.78,-1.00# 0.07# 6.92
    # 上半身,上半身2,0,1,0,上半身,頭,1,1-,0,上半身2,首,0,1,1,d1,d2,d3,01_True,False,True,False,True,False_ 0.70# 0.01#-9.82,-6.26# 0.03#-9.34,-1.01# 0.03#-14.20
    # 上半身,上半身2,0,1,1,上半身,頭,1,1,0,首,頭,0,1-,0,d1,d2,d3,01_True,False,True,False,True,False_ 0.70#-0.09# 8.19,-6.26#-0.07# 8.68,-1.02#-0.07# 3.82
    # 上半身,上半身2,1,0,0,上半身,首,1-,0,1-,首,頭,1,0,1,d2,d1,d3,01_True,True,True,False,False,False_ 8.51#-0.00# 2.26, 1.54#-0.05# 2.76, 6.72#-1.12#-1.97
    # 上半身,上半身2,1,0,0,上半身,上半身2,1-,0,1-,首,頭,1,0,1,d2,d1,d3,01_True,True,True,False,False,False_ 4.53#-0.00# 2.25,-2.44#-0.01# 2.74, 2.78#-0.54#-2.07
    # 上半身,頭,1,0,1-,上半身,頭,1-,0,1,上半身2,頭,1,0,0,d2,d3,d1,01_True,False,True,False,True,False_ 0.54# 0.01# 11.54,-6.42# 0.04# 12.02,-1.17# 0.05# 7.17
    def test_upper_stance_upper2_up_43(self):

        target_test_params_list_bone_names1 = [("上半身","上半身2")]
        target_test_params_list_bone_names2 = [("上半身","首"), ("上半身","頭"), ("上半身2","首"), ("上半身2","頭")]
        target_test_params_list_bone_names3 = [("首","頭")]
        
        # 数字の組合せ
        rep_upper2_initial_slope_test_numbers = ["0","1-","1"]
        list_target_test_params_base_numbers = list(itertools.product(rep_upper2_initial_slope_test_numbers, repeat=3))
        list_target_test_params_list_numbers = [(x00, x01, x02) for (x00, x01, x02) in list_target_test_params_base_numbers if 0 < [x00, x01, x02].count("0") < 3 ]
        print("numbers LIST: %s" % len(list_target_test_params_list_numbers))

        # 最後の組合せ
        rep_upper2_initial_slope_test_pairs = ["d1","d2","d3"]
        target_test_params_base_pairs = list(itertools.product(rep_upper2_initial_slope_test_pairs, repeat=3))
        target_test_params_list_pairs = [(x00, x01, x02) for (x00, x01, x02) in target_test_params_base_pairs 
            if x00[:2] not in [x01[:2], x02[:2]] and x01[:2] not in [x00[:2], x02[:2]] and x02[:2] not in [x01[:2], x00[:2]] ]
        print("pairs LIST: %s" % len(target_test_params_list_pairs))

        # 直積
        target_test_params_base = list(itertools.product(target_test_params_list_bone_names1, list_target_test_params_list_numbers, \
            target_test_params_list_bone_names2, list_target_test_params_list_numbers, \
            target_test_params_list_bone_names3, list_target_test_params_list_numbers, target_test_params_list_pairs))

        target_test_params_list = [(names1[0], names1[1], numbers1[0], numbers1[1], numbers1[2], names2[0], names2[1], numbers2[0], numbers2[1], numbers2[2], \
            names3[0], names3[1], numbers3[0], numbers3[1], numbers3[2], pairs[0], pairs[1], pairs[2], "01") \
            for (names1, numbers1, names2, numbers2, names3, numbers3, pairs) in target_test_params_base]
        random.shuffle(target_test_params_list)
        print("targets LIST: %s" % len(target_test_params_list))
        
        prefix = "043-01"
        ok_list = self.calc_stance(target_test_params_list, 0.1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)
                             

    def test_upper_stance_upper2_up_45(self):

        # ボーン名の組合せ
        rep_upper2_initial_slope_test_bone_names = [(0,"上半身"), (1,"上半身2"), (2,"首"), (3,"頭")]
        target_test_params_base_bone_names = list(itertools.product(rep_upper2_initial_slope_test_bone_names, repeat=2))
        target_test_params_list_bone_names = [(x00[1], x01[1]) for (x00, x01) in target_test_params_base_bone_names if x00[0] < x01[0]]
        target_test_params_base_bone_names_comb = list(itertools.combinations(target_test_params_list_bone_names, 2))
        target_test_params_list_bone_names_comb = [(x00, x01) for (x00, x01) in target_test_params_base_bone_names_comb if x00 != x01]
        print("bone_names LIST: %s" % len(target_test_params_list_bone_names_comb))
        print("bone_names LIST: %s" % target_test_params_list_bone_names_comb)
        
        # 数字の組合せ
        rep_upper2_initial_slope_test_numbers = ["0","1-","1"]
        list_target_test_params_base_numbers = list(itertools.product(rep_upper2_initial_slope_test_numbers, repeat=3))
        list_target_test_params_list_numbers = [(x00, x01, x02) for (x00, x01, x02) in list_target_test_params_base_numbers if 0 < [x00, x01, x02].count("0") < 3 ]
        print("numbers LIST: %s" % len(list_target_test_params_list_numbers))

        # 直積
        target_test_params_base = list(itertools.product(target_test_params_list_bone_names_comb, list_target_test_params_list_numbers
            , list_target_test_params_list_numbers))

        target_test_params_list = [(names_comb[0][0], names_comb[0][1], numbers1[0], numbers1[1], numbers1[2], names_comb[1][0], names_comb[1][1], numbers2[0], numbers2[1], numbers2[2], \
            "上半身", "上半身2", "0", "0", "0", "d1","d2","d3","01") \
            for (names_comb, numbers1, numbers2) in target_test_params_base]
        random.shuffle(target_test_params_list)
        print("targets LIST: %s" % len(target_test_params_list))
        
        prefix = "045-02"
        ok_list = self.calc_stance(target_test_params_list, 0.1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)
                             

    def test_upper_stance_upper2_up_46(self):

        # ボーン名の組合せ
        rep_upper2_initial_slope_test_bone_names = [(0,"上半身"), (1,"上半身2"), (2,"首"), (3,"頭")]
        target_test_params_base_bone_names = list(itertools.product(rep_upper2_initial_slope_test_bone_names, repeat=2))
        target_test_params_list_bone_names = [(x00[1], x01[1]) for (x00, x01) in target_test_params_base_bone_names if x00[0] < x01[0]]
        target_test_params_base_bone_names_comb = list(itertools.combinations(target_test_params_list_bone_names, 3))
        target_test_params_list_bone_names_comb = [(x00, x01, x02) for (x00, x01, x02) in target_test_params_base_bone_names_comb if x00 != x01 != x02]
        print("bone_names LIST: %s" % len(target_test_params_list_bone_names_comb))
        print("bone_names LIST: %s" % target_test_params_list_bone_names_comb)
        
        # 数字の組合せ
        rep_upper2_initial_slope_test_numbers = ["0","1-","1"]
        list_target_test_params_base_numbers = list(itertools.product(rep_upper2_initial_slope_test_numbers, repeat=3))
        list_target_test_params_list_numbers = [(x00, x01, x02) for (x00, x01, x02) in list_target_test_params_base_numbers if 0 < [x00, x01, x02].count("0") < 3 ]
        print("numbers LIST: %s" % len(list_target_test_params_list_numbers))

        # 最後の組合せ
        rep_upper2_initial_slope_test_pairs = ["d1","d2","d3"]
        target_test_params_base_pairs = list(itertools.product(rep_upper2_initial_slope_test_pairs, repeat=3))
        target_test_params_list_pairs = [(x00, x01, x02) for (x00, x01, x02) in target_test_params_base_pairs 
            if x00[:2] not in [x01[:2], x02[:2]] and x01[:2] not in [x00[:2], x02[:2]] and x02[:2] not in [x01[:2], x00[:2]] ]
        print("pairs LIST: %s" % len(target_test_params_list_pairs))

        # 直積
        target_test_params_base = list(itertools.product(target_test_params_list_bone_names_comb, list_target_test_params_list_numbers
            , list_target_test_params_list_numbers, list_target_test_params_list_numbers, target_test_params_list_pairs))

        target_test_params_list = [(names_comb[0][0], names_comb[0][1], numbers1[0], numbers1[1], numbers1[2], names_comb[1][0], names_comb[1][1], numbers2[0], numbers2[1], numbers2[2], \
        names_comb[2][0], names_comb[2][1], numbers3[0], numbers3[1], numbers3[2], pairs[0], pairs[1], pairs[2],"01") \
            for (names_comb, numbers1, numbers2, numbers3, pairs) in target_test_params_base]
        random.shuffle(target_test_params_list)
        print("targets LIST: %s" % len(target_test_params_list))
        
        prefix = "046-01"
        ok_list = self.calc_stance(target_test_params_list, 0.1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)
                             
    # 上半身,首,1-,0,0,上半身,頭,1,1,0,首,頭,1,0,0,d1,d2,d3,01_True,True,True,False,False,False_ 5.28#-0.00#-1.56,-1.69#-0.02#-1.07, 3.52#-0.64#-5.87
    # 上半身,首,1-,0,0,上半身2,首,1,0,0,首,頭,1,1,0,d1,d3,d2,01_True,True,True,False,False,False_ 2.21#-0.00# 4.20,-4.76# 0.01# 4.69, 0.48#-0.20#-0.16
    # 上半身,首,1,0,1-,上半身,頭,1,1,0,上半身2,首,1-,0,1,d3,d2,d1,01_True,True,True,False,False,False_-0.33#-0.00# 8.13,-7.30# 0.03# 8.62,-2.04# 0.16# 3.75
    # 上半身,上半身2,0,0,1-,上半身,首,1,1-,0,上半身2,首,0,0,1,d1,d2,d3,01_True,False,True,True,False,False_-0.60#-0.04#-11.13,-7.56#-0.00#-10.65,-2.30# 0.17#-15.51
    # 上半身,上半身2,0,0,1,上半身,頭,1,1,0,首,頭,0,1,1-,d1,d2,d3,01_True,False,True,False,True,False_ 0.70#-0.09# 8.19,-6.26#-0.07# 8.68,-1.02#-0.07# 3.82
    # 上半身,上半身2,0,0,1-,上半身,頭,1,1-,0,上半身2,首,0,1-,0,d1,d2,d3,01_True,False,True,False,True,False_ 0.70# 0.01#-9.82,-6.26# 0.03#-9.34,-1.01# 0.03#-14.20
    # 上半身,上半身2,0,0,1-,上半身,頭,1,1-,0,上半身2,首,0,1-,1,d1,d2,d3,01_True,False,True,False,True,False_ 0.70# 0.01#-9.82,-6.26# 0.03#-9.34,-1.01# 0.03#-14.20
    # 上半身,上半身2,0,1,0,上半身,首,1,1-,0,上半身2,首,0,0,1,d1,d2,d3,01_True,False,True,True,False,False_-0.60#-0.04#-11.13,-7.56#-0.00#-10.65,-2.30# 0.17#-15.51
    # 上半身,上半身2,0,1,0,上半身,首,1,1-,0,上半身2,首,0,1-,1,d1,d2,d3,01_True,False,True,True,False,False_-0.60#-0.04#-11.13,-7.56#-0.00#-10.65,-2.30# 0.17#-15.51
    # 上半身,上半身2,0,1,0,上半身,頭,1,1-,0,上半身2,首,0,1,1,d1,d2,d3,01_True,False,True,False,True,False_ 0.70# 0.01#-9.82,-6.26# 0.03#-9.34,-1.01# 0.03#-14.20
    # 上半身,上半身2,0,1,1-,上半身,首,1,1-,0,上半身2,首,0,1,1,d1,d2,d3,01_True,False,True,True,False,False_-0.60#-0.04#-11.13,-7.56#-0.00#-10.65,-2.30# 0.17#-15.51
    # 上半身,上半身2,0,1-,1-,上半身,首,1,1-,0,上半身2,首,0,1-,1,d1,d2,d3,01_True,False,True,True,False,False_-0.60#-0.04#-11.13,-7.56#-0.00#-10.65,-2.30# 0.17#-15.51
    # 上半身,上半身2,0,1,1,上半身,頭,1,1,0,首,頭,0,0,1-,d1,d2,d3,01_True,False,True,False,True,False_ 0.70#-0.09# 8.19,-6.26#-0.07# 8.68,-1.02#-0.07# 3.82
    # 上半身,上半身2,0,1-,1,上半身,頭,1,1,0,首,頭,0,1-,0,d1,d2,d3,01_True,False,True,False,True,False_ 0.70#-0.09# 8.19,-6.26#-0.07# 8.68,-1.02#-0.07# 3.82
    # 上半身,上半身2,0,1-,1,上半身,頭,1,1,0,首,頭,0,1-,1-,d1,d2,d3,01_True,False,True,False,True,False_ 0.70#-0.09# 8.19,-6.26#-0.07# 8.68,-1.02#-0.07# 3.82
    # 上半身,上半身2,0,1,1,上半身2,頭,1,1,0,首,頭,0,1-,1-,d1,d2,d3,01_True,False,True,False,True,False_-0.18#-0.08# 9.07,-7.14#-0.05# 9.56,-1.89# 0.06# 4.69
    # 上半身,上半身2,1-,0,0,上半身,首,1,0,0,首,頭,1,1-,0,d3,d2,d1,01_True,False,True,True,False,False_ 11.81# 0.07# 3.55, 4.84#-0.00# 4.04, 9.99#-1.54#-0.58
    # 上半身,上半身2,1,0,0,上半身,首,1-,0,1-,首,頭,1,0,1,d2,d1,d3,01_True,True,True,False,False,False_ 8.51#-0.00# 2.26, 1.54#-0.05# 2.76, 6.72#-1.12#-1.97
    # 上半身,上半身2,1,0,0,上半身,頭,1,1,0,首,頭,1-,0,0,d3,d2,d1,01_True,True,True,False,False,False_-4.93# 0.00#-1.57,-11.90# 0.07#-1.09,-6.59# 0.82#-5.95
    # 上半身,上半身2,1,0,0,上半身,頭,1,1-,0,上半身2,頭,1-,0,0,d3,d2,d1,01_True,False,True,False,True,False_ 1.73# 0.02# 8.77,-5.23# 0.04# 9.25, 0.01#-0.11# 4.40
    # 上半身,上半身2,1-,0,0,上半身2,頭,1,1-,0,首,頭,1,1-,0,d1,d2,d3,01_True,False,True,False,True,False_ 0.42#-0.04# 9.66,-6.54#-0.01# 10.15,-1.29# 0.02# 5.29
    # 上半身,上半身2,1,0,1-,上半身,首,1-,0,1,首,頭,1,1-,0,d1,d3,d2,01_True,False,True,True,False,False_ 10.49# 0.06#-0.14, 3.52#-0.00# 0.35, 8.68#-1.35#-4.31
    # 上半身,上半身2,1,1,0,上半身,首,0,1-,1,上半身,頭,1-,1-,0,d2,d1,d3,01_True,True,False,False,True,False_ 0.00#-95.81# 10.71,-12.09#-95.73# 14.86,-12.81#-95.36#-0.04
    # 上半身,上半身2,1,1-,0,上半身,頭,1-,0,0,上半身2,頭,1,1,0,d3,d1,d2,01_True,False,True,True,False,False_ 17.19# 5.78#-0.05, 10.25# 5.81# 0.00, 16.13# 3.36#-4.22
    # 上半身,上半身2,1,1-,0,上半身,頭,1-,1-,0,上半身2,首,0,0,1-,d2,d3,d1,01_True,False,True,True,False,False_-4.31#-0.06#-86.02,-11.28# 0.00#-85.54,-5.98# 0.67#-90.41
    # 上半身,頭,1-,0,0,上半身2,首,1,1-,0,首,頭,1,1-,0,d1,d2,d3,01_True,False,True,False,True,False_ 0.92#-0.01# 11.79,-6.04# 0.01# 12.27,-0.80#-0.02# 7.42
    # 上半身,頭,1,1,0,上半身2,首,1-,0,1,上半身2,頭,1,0,1-,d2,d1,d3,01_True,False,True,False,True,False_-0.03#-0.06# 7.84,-7.00#-0.03# 8.33,-1.75# 0.06# 3.46
    # 上半身,頭,1-,1-,0,上半身2,頭,0,1,1,首,頭,1,1-,0,d3,d2,d1,01_True,False,True,True,False,False_ 7.94# 0.04#-86.89, 0.98# 0.00#-86.40, 6.16#-0.99#-91.13
    # 上半身,頭,1-,1-,0,上半身2,頭,0,1-,1,首,頭,1,1-,0,d3,d2,d1,01_True,False,True,True,False,False_ 7.94# 0.04#-86.89, 0.98# 0.00#-86.40, 6.16#-0.99#-91.13
    def test_upper_stance_upper2_up_47(self):

        # ボーン名の組合せ
        rep_upper2_initial_slope_test_bone_names = [(0,"上半身"), (1,"上半身2"), (2,"首"), (3,"頭")]
        target_test_params_base_bone_names = list(itertools.product(rep_upper2_initial_slope_test_bone_names, repeat=2))
        target_test_params_list_bone_names = [(x00[1], x01[1]) for (x00, x01) in target_test_params_base_bone_names if x00[0] < x01[0]]
        target_test_params_base_bone_names_comb = list(itertools.combinations(target_test_params_list_bone_names, 3))
        target_test_params_list_bone_names_comb = [(x00, x01, x02) for (x00, x01, x02) in target_test_params_base_bone_names_comb if x00 != x01 != x02 and x00 == ("上半身", "上半身2")]
        print("bone_names LIST: %s" % len(target_test_params_list_bone_names_comb))
        print("bone_names LIST: %s" % target_test_params_list_bone_names_comb)
        
        # 数字の組合せ
        rep_upper2_initial_slope_test_numbers = ["0","1-","1"]
        list_target_test_params_base_numbers = list(itertools.product(rep_upper2_initial_slope_test_numbers, repeat=3))
        list_target_test_params_list_numbers = [(x00, x01, x02) for (x00, x01, x02) in list_target_test_params_base_numbers if 0 < [x00, x01, x02].count("0") < 3 ]
        print("numbers LIST: %s" % len(list_target_test_params_list_numbers))

        # 直積
        target_test_params_base = list(itertools.product(target_test_params_list_bone_names_comb, list_target_test_params_list_numbers
            , list_target_test_params_list_numbers, list_target_test_params_list_numbers))

        target_test_params_list = [(names_comb[0][0], names_comb[0][1], numbers1[0], numbers1[1], numbers1[2], names_comb[1][0], names_comb[1][1], numbers2[0], numbers2[1], numbers2[2], \
        names_comb[2][0], names_comb[2][1], numbers3[0], numbers3[1], numbers3[2], "d1", "d2", "d3","01") \
            for (names_comb, numbers1, numbers2, numbers3) in target_test_params_base]
        random.shuffle(target_test_params_list)
        print("targets LIST: %s" % len(target_test_params_list))
        
        prefix = "047-02"
        ok_list = self.calc_stance(target_test_params_list, 0.1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
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
        is_alternative_model = False
        is_no_delegate = True
        target_avoidance_rigids = []
        target_avoidance_bones = []
        base_path = "E:/MMD/MikuMikuDance_v926x64/Work/202001_sizing/input_upper2_up/"

        logger.info("len: %s", len(target_test_params))
        ok_list = []

        os.makedirs("{0}/{1}".format(base_path, prefix), exist_ok=exist_ok)

        for pidx, test_param in enumerate(target_test_params):
            logger.info("prefix: %s, test_param(%s -> %s): %s", prefix, len(target_test_params), pidx, test_param)

            file_name = "test_{0}.vmd".format(','.join([str(i) for i in test_param]))

            output_vmd_path = "{0}/{1}/{2}".format(base_path, prefix, file_name)

            copy_motion = copy.deepcopy(motion)

            try:
                main.main(copy_motion, trace_model, replace_model, output_vmd_path, \
                    is_avoidance, is_avoidance_finger, is_hand_ik, hand_distance, is_floor_hand, is_floor_hand_up, is_floor_hand_down, hand_floor_distance, leg_floor_distance, is_finger_ik, finger_distance, vmd_choice_values, rep_choice_values, rep_rate_values, \
                    camera_motion, camera_vmd_path, camera_pmx, output_camera_vmd_path, camera_y_offset, is_alternative_model, is_no_delegate, target_avoidance_rigids, target_avoidance_bones, test_param)
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
        
            dir_path = "{0}/{1}/{1}_OK{2}".format(base_path, prefix, result_list.count(True))
            os.makedirs(dir_path, exist_ok=True)

            if result_list.count(True) > 0:
                ok_list.append(test_param)

            shutil.move(output_vmd_path, "{0}/{1}".format(dir_path, resutl_file_name))               
            logger.info("result: %s %s", result_list.count(True), resutl_file_name)

        return ok_list



    
        
    def test_delegate_qq_01(self):
        test_param00 = ["ttt","dtx","dtz","dxz"]
        test_param01 = ["ttt","dtx","dtz","dxz"]
        test_param02 = ["ttt","dtx","dtz","dxz"]
        test_param03 = ["ttt","dtx","dtz","dxz"]

        # 直積
        target_test_params_base = list(itertools.product(test_param00, test_param01, test_param02, test_param03))

        target_test_params_list = [(x00, x01, x02, x03) \
            for (x00, x01, x02, x03) \
            in target_test_params_base if x00[:3] != x01[:3] != x02[:3] != x03[:3]]

        random.shuffle(target_test_params_list)

        ok_list = self.calc_delegate_qq(target_test_params_list, 1, False, "delegate_qq_07")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
                
        
    def test_delegate_qq_02(self):
        test_param00 = ("d1","d2","d3","d4","d5")

        # 直積
        target_test_params_list = list(itertools.permutations(test_param00))
        print("start LIST: %s" % len(target_test_params_list))

        random.shuffle(target_test_params_list)

        ok_list = self.calc_delegate_qq(target_test_params_list, 1, False, "delegate_qq_17")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)
        

    def test_delegate_qq_03(self):
        test_param00 = ("x1","x2","x3","x4","x5","x6","x7","x8","xd1","xd2","xd3","xd4","xd5","xd6","xd7","xd8")
        test_param01 = ("z1","z2","z3","z4")
        test_param02 = ("xa","xb","xc","xd","xe","xai","xbi","xci","xdi","xei")

        # 直積
        target_test_params_base = list(itertools.product(test_param00, test_param01, test_param02))
        target_test_params_list = target_test_params_base
        random.shuffle(target_test_params_list)
        print("start LIST: %s" % len(target_test_params_list))

        random.shuffle(target_test_params_list)

        ok_list = self.calc_delegate_qq(target_test_params_list, 1, False, "delegate_qq_07")

        print("ok_list LIST: %s" % ok_list)
        self.assertGreater(len(ok_list), 0)

    def test_delegate_qq_05(self):
        target_dir_path = "E:/MMD/MikuMikuDance_v926x64/Work/202001_sizing/delegate_qq/delegate_qq_18_test/*.vmd"
        rep_target_name_list = ["手首A","手首B","手首C","手首D","手首E","手首F","手首H","手首I","手首J","手首K"]
        limit = 1

        # 変換先モデル
        replace_model = PmxReader().read_pmx_file("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/初音ミク/Tda式初音ミク_盗賊つばき流Ｍトレースモデル配布 v1.07/Tda式初音ミク_盗賊つばき流Mトレースモデルv1.07_腕回転.pmx")
        # replace_model = PmxReader().read_pmx_file("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/刀剣乱舞/011_今剣/今剣 ゆるん式 ver0124/ライブ衣装/今剣インナー_準標準.pmx")

        target_frames = [187,227,241,300,412]

        for target_vmd_path in glob.glob(target_dir_path):
            # VMD読み込み
            motion = VmdReader().read_vmd_file(target_vmd_path)

            result_txt_list = []
            total_result_list = []

            for rep_bone_index in rep_target_name_list:
                result_list = []
                diff_list = []

                for direction in ["右", "左"]:
                    rep_bone_name = "{0}{1}".format(direction, rep_bone_index)
                    test_target_name = rep_bone_name[:3]
                    links, indexes = replace_model.create_link_2_top_one(test_target_name)

                    # 事前にグローバル位置を求めておく
                    target_bfs = [x for x in motion.frames[test_target_name] if x.frame in target_frames]
                    org_target_poss = []

                    for bf in target_bfs:
                        _, _, _, _, org_global_3ds = utils.create_matrix_global(replace_model, links, motion.frames, bf, None)
                        org_target_poss.append(org_global_3ds[-1])

                    # 変換後のグローバル位置を求める
                    rep_target_bfs = copy.deepcopy([x for x in motion.frames[rep_bone_name] if x.frame in target_frames])
                    rep_target_poss = []

                    for bf in rep_target_bfs:
                        rep_links, _ = replace_model.create_link_2_top_all(rep_bone_name)
                        _, _, _, _, rep_global_3ds = utils.create_matrix_global(replace_model, rep_links, motion.frames, bf, None)
                        rep_target_poss.append(rep_global_3ds[-1])

                    for org_target_pos, rep_target_pos in zip(org_target_poss, rep_target_poss):
                        is_x_diff = org_target_pos.x() - limit <= rep_target_pos.x() <= org_target_pos.x() + limit
                        # is_y_diff = org_target_pos.y() - limit <= rep_target_pos.y() <= org_target_pos.y() + limit
                        is_z_diff = org_target_pos.z() - limit <= rep_target_pos.z() <= org_target_pos.z() + limit
                        
                        # org_euler = org_bf.rotation.toEulerAngles()
                        # to_euler = bf.rotation.toEulerAngles()

                        # is_x_diff = org_euler.x() - limit <= to_euler.x() <= org_euler.x() + limit
                        # is_y_diff = org_euler.y() - limit <= to_euler.y() <= org_euler.y() + limit
                        # is_z_diff = org_euler.z() - limit <= to_euler.z() <= org_euler.z() + limit

                        diff_euler = rep_target_pos - org_target_pos

                        # is_x_same = round(diff_euler.x(),2) == 0
                        # is_y_same = round(diff_euler.y(),2) == 0
                        # is_z_same = round(diff_euler.z(),2) == 0

                        result = is_x_diff and is_z_diff
                        result_list.append(result)
                        total_result_list.append(result)

                        diff = "{0: 03.2f}".format(round(diff_euler.y(), 2))
                        diff_list.append(diff)

                        # if result:
                        #     logger.info("f: %s, org_target_pos: %s", bf.frame, org_target_pos)
                        #     logger.info("f: %s, rep_target_pos: %s", bf.frame, rep_target_pos)
                            # logger.info("f: %s, org_rotation: %s", bf.frame, org_euler)
                            # logger.info("f: %s, rep_rotation: %s", bf.frame, to_euler)
                            # logger.info("f: %s, is_x_diff: %s, is_y_diff: %s, is_z_diff: %s, is_x_same: %s, is_y_same: %s, is_z_same: %s", bf.frame, is_x_diff, is_y_diff, is_z_diff, is_x_same, is_y_same, is_z_same)

                result_txt_list.append("{0}{1:02}".format(rep_bone_index[2], result_list.count(True)))

            resutl_file_path =  target_vmd_path.replace("\\test", "/{0:02}_{1}".format(total_result_list.count(True), ','.join([str(i) for i in result_txt_list])))
            
            shutil.copy(target_vmd_path, resutl_file_path)

        self.assertGreater(limit, 0)


    def test_delegate_qq_04(self):
        test_param00 = ("x1","x2","x3","x4","x5","x6","x7","x8","x9","x10")
        test_param01 = ("z1","z2","z3","z4","z5","z6","z7","z8","z9","z10")
        test_param02 = ("xa","xb","xc","xd","xe","xai","xbi","xci","xdi","xei")

        # 直積
        target_test_params_base = list(itertools.product(test_param00, test_param01, test_param02))
        target_test_params_list = target_test_params_base
        random.shuffle(target_test_params_list)
        print("start LIST: %s" % len(target_test_params_list))

        random.shuffle(target_test_params_list)

        prefix = "delegate_qq_20"
        ok_list = self.calc_delegate_qq(target_test_params_list, 1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)

    def test_delegate_qq_06(self):
        test_param00 = ["t1" ,"t2" ,"x1" ,"y1" ,"z1" ,"x2" ,"y2" ,"z2" ,"d1" ,"d2"]

        # 直積
        target_test_params_base = list(itertools.product(test_param00, repeat=5))

        target_test_params_list = [(x00, x01, x02, x03, x04) \
            for (x00, x01, x02, x03, x04) \
            in target_test_params_base if x00[:1] not in [x01[:1],x02[:1],x03[:1],x04[:1]] and x01[:1] not in[x00[:1],x02[:1],x03[:1],x04[:1]] and \
            x02[:1] not in [x01[:1],x00[:1],x03[:1],x04[:1]] and x03[:1] not in [x00[:1],x02[:1],x01[:1],x04[:1]] and x04[:1] not in [x01[:1],x02[:1],x03[:1],x00[:1]]]

        random.shuffle(target_test_params_list)
        print("start LIST: %s" % len(target_test_params_list))

        random.shuffle(target_test_params_list)

        prefix = "delegate_qq_38"
        ok_list = self.calc_delegate_qq(target_test_params_list, 1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)

    def test_delegate_qq_07(self):
        test_param00 = ["t1"]
        test_param01 = ["x1","x2","x3","x4","x5","x6","d1","d2","d3","d4","d5","d6"]
        test_param02 = ["x1","x2","x3","x4","x5","x6","d1","d2","d3","d4","d5","d6"]

        # 直積
        target_test_params_base = list(itertools.product(test_param00, test_param01, test_param02))

        target_test_params_list = [(x00, x01, x02) \
            for (x00, x01, x02) \
            in target_test_params_base if x00[:1] not in [x01[:1],x02[:1]] and x01[:1] not in[x00[:1],x02[:1]] and x02[:1] not in [x01[:1],x00[:1]]]

        random.shuffle(target_test_params_list)
        print("start LIST: %s" % len(target_test_params_list))

        random.shuffle(target_test_params_list)

        prefix = "delegate_qq_43"
        ok_list = self.calc_delegate_qq(target_test_params_list, 1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)


    def test_delegate_qq_08(self):
        test_param00 = ["t1"]
        test_param01 = ["x2","d5","a1","a2","a3","a4","a5","a6"]

        # 直積
        target_test_params_base = list(itertools.product(test_param00, test_param01, test_param01, test_param01, "00"))

        target_test_params_list = [(x00, x01, x02, x03, x04) \
            for (x00, x01, x02, x03, x04) \
            in target_test_params_base if x00[:1] not in [x01[:1],x02[:1],x03[:1],x04[:1]] and x01[:1] not in[x00[:1],x02[:1],x03[:1],x04[:1]] and \
            x02[:1] not in [x01[:1],x00[:1],x03[:1],x04[:1]] and x03[:1] not in [x00[:1],x02[:1],x01[:1],x04[:1]] and x04[:1] not in [x01[:1],x02[:1],x03[:1],x00[:1]]]

        random.shuffle(target_test_params_list)
        print("start LIST: %s" % len(target_test_params_list))

        random.shuffle(target_test_params_list)

        prefix = "delegate_qq_44"
        ok_list = self.calc_delegate_qq(target_test_params_list, 1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)


    def test_delegate_qq_09(self):
        test_param00 = ["t1"]
        test_param01 = ["x2"]
        test_param02 = ["d3"]
        test_param03 = ["01","a1","a2","a3","a4","a5","a6"]

        # 直積
        target_test_params_base = list(itertools.product(test_param00, test_param01, test_param02, test_param03, "00"))

        target_test_params_list = [(x00, x01, x02, x03, x04) \
            for (x00, x01, x02, x03, x04) \
            in target_test_params_base if x00[:1] not in [x01[:1],x02[:1],x03[:1],x04[:1]] and x01[:1] not in[x00[:1],x02[:1],x03[:1],x04[:1]] and \
            x02[:1] not in [x01[:1],x00[:1],x03[:1],x04[:1]] and x03[:1] not in [x00[:1],x02[:1],x01[:1],x04[:1]] and x04[:1] not in [x01[:1],x02[:1],x03[:1],x00[:1]]]

        random.shuffle(target_test_params_list)
        print("start LIST: %s" % len(target_test_params_list))

        random.shuffle(target_test_params_list)

        prefix = "delegate_qq_49"
        ok_list = self.calc_delegate_qq(target_test_params_list, 1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)

    def test_delegate_qq_10(self):
        test_param00 = ("t1","x1","d1","a1")

        # 順番
        target_test_params_list = list(itertools.permutations(test_param00))
        print("start LIST: %s" % len(target_test_params_list))

        # target_test_params_list = [(x00, x01, x02, x03, x04) \
        #     for (x00, x01, x02, x03, x04) \
        #     in target_test_params_base if x00[:1] not in [x01[:1],x02[:1],x03[:1],x04[:1]] and x01[:1] not in[x00[:1],x02[:1],x03[:1],x04[:1]] and \
        #     x02[:1] not in [x01[:1],x00[:1],x03[:1],x04[:1]] and x03[:1] not in [x00[:1],x02[:1],x01[:1],x04[:1]] and x04[:1] not in [x01[:1],x02[:1],x03[:1],x00[:1]]]

        random.shuffle(target_test_params_list)
        print("start LIST: %s" % len(target_test_params_list))

        random.shuffle(target_test_params_list)

        prefix = "delegate_qq_50"
        ok_list = self.calc_delegate_qq(target_test_params_list, 1, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)

    def test_delegate_qq_11(self):
        test_param00 = ["t1"]
        test_param01 = ["x1","x2","x3","x4","x5","x6","x7"]
        test_param02 = ["d1","d2","d3","d4","d5","d6","d7"]
        test_param03 = ["y1","y2","y3","y4","y5","y6","y7","b1","b2","b3","b4","b5","b6","b7"]
        test_param04 = ["y1","y2","y3","y4","y5","y6","y7","b1","b2","b3","b4","b5","b6","b7"]

        # 直積
        target_test_params_base = list(itertools.product(test_param00, test_param01, test_param02, test_param03, test_param04, "00"))

        target_test_params_list = [(x00, x01, x02, x03, x04, x05) \
            for (x00, x01, x02, x03, x04, x05) \
            in target_test_params_base if x00[:1] not in [x01[:1],x02[:1],x03[:1],x04[:1]] and x01[:1] not in[x00[:1],x02[:1],x03[:1],x04[:1]] and \
            x02[:1] not in [x01[:1],x00[:1],x03[:1],x04[:1]] and x03[:1] not in [x00[:1],x02[:1],x01[:1],x04[:1]] and x04[:1] not in [x01[:1],x02[:1],x03[:1],x00[:1]]]

        random.shuffle(target_test_params_list)
        print("start LIST: %s" % len(target_test_params_list))

        random.shuffle(target_test_params_list)

        prefix = "delegate_qq_11_07"
        rep_target_name_list = ["手首D","ひじD"]
        ok_list = self.calc_delegate_qq(target_test_params_list, 1, rep_target_name_list, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)

    def test_delegate_qq_12(self):
        test_param00 = ["t1"]
        test_param01 = ["x1","x2","x3","x4","x5","x6","x7"]
        test_param02 = ["d1","d2","d3","d4","d5","d6","d7"]
        test_param03 = ["e1"]
        test_param04 = ["f1","f2","f3","f4","f5","f6","f7"]
        test_param05 = ["g1","g2","g3","g4","g5","g6","g7","g0"]

        # 直積
        target_test_params_base = list(itertools.product(test_param00, test_param01, test_param02, test_param03, test_param04, test_param05))
        
        target_test_params_list = target_test_params_base
        # target_test_params_list = [(x00, x01, x02, x03, x04, x05) \
        #     for (x00, x01, x02, x03, x04, x05) \
        #     in target_test_params_base if x00[:1] not in [x01[:1],x02[:1],x03[:1],x04[:1]] and x01[:1] not in[x00[:1],x02[:1],x03[:1],x04[:1]] and \
        #     x02[:1] not in [x01[:1],x00[:1],x03[:1],x04[:1]] and x03[:1] not in [x00[:1],x02[:1],x01[:1],x04[:1]] and x04[:1] not in [x01[:1],x02[:1],x03[:1],x00[:1]]]

        random.shuffle(target_test_params_list)
        print("start LIST: %s" % len(target_test_params_list))

        random.shuffle(target_test_params_list)

        prefix = "delegate_qq_12_07"
        rep_target_name_list = ["手首D","ひじD"]
        ok_list = self.calc_delegate_qq(target_test_params_list, 1, rep_target_name_list, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)

    def test_delegate_qq_13(self):
        test_param00 = ["t1"]
        test_param01 = ["x1","x2","x3","x4","x5","x6","x7"]
        # test_param02 = ["d1","d2","d3","d4","d5","d6","d7"]
        test_param02 = ["f1","f2","f3","f4","f5","f6","f7"]
        test_param03 = ["y1","y2","y3","y4","y5","y6","y7"]

        # 直積
        target_test_params_base = list(itertools.product(test_param00, test_param01, test_param02, test_param03, "00", "00"))

        target_test_params_list = [(x00, x01, x02, x03, x04, x05) \
            for (x00, x01, x02, x03, x04, x05) \
            in target_test_params_base if x00[:1] not in [x01[:1],x02[:1],x03[:1],x04[:1]] and x01[:1] not in[x00[:1],x02[:1],x03[:1],x04[:1]] and \
            x02[:1] not in [x01[:1],x00[:1],x03[:1],x04[:1]] and x03[:1] not in [x00[:1],x02[:1],x01[:1],x04[:1]] and x04[:1] not in [x01[:1],x02[:1],x03[:1],x00[:1]]]

        random.shuffle(target_test_params_list)
        print("start LIST: %s" % len(target_test_params_list))

        random.shuffle(target_test_params_list)

        prefix = "delegate_qq_13_06"
        rep_target_name_list = ["手首C","ひじC"]
        ok_list = self.calc_delegate_qq(target_test_params_list, 1, rep_target_name_list, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)

    def test_delegate_qq_14(self):
        test_param00 = ["t1"]
        test_param01 = ["x0"]
        test_param02 = ["d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da"]
        test_param03 = ["y0","y1","y2","y3","y4","y5","y6","y7","y8","y9","ya"]

        # 直積
        target_test_params_base = list(itertools.product(test_param00, test_param01, test_param02, test_param03))

        target_test_params_list = [(x00, x01, x02, x03) \
            for (x00, x01, x02, x03) \
            in target_test_params_base if x00[:1] not in [x01[:1],x02[:1],x03[:1]] and x01[:1] not in[x00[:1],x02[:1],x03[:1]] and \
            x02[:1] not in [x01[:1],x00[:1],x03[:1]] and x03[:1] not in [x00[:1],x02[:1],x01[:1]]]

        random.shuffle(target_test_params_list)
        print("start LIST: %s" % len(target_test_params_list))

        random.shuffle(target_test_params_list)

        prefix = "delegate_qq_14-02"
        rep_target_name_list = ["手首C","ひじC"]
        ok_list = self.calc_delegate_qq(target_test_params_list, 1, rep_target_name_list, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)

    def test_delegate_qq_15(self):
        test_param00 = ["d2t_y","d2t2d_x2y","d2t2d_y2y","d2t2d_z2y","d2t_x2y","d2t_y2y","d2t_z2y","dl_d2y","dl_x2y","dl_y2y","dl_z2y","t2d_x2y","t2d_y2y","t2d_z2y","d2t_y_i","d2t2d_x2y_i","d2t2d_y2y_i","d2t2d_z2y_i","d2t_x2y_i","d2t_y2y_i","d2t_z2y_i","dl_d2y_i","dl_x2y_i","dl_y2y_i","dl_z2y_i","t2d_x2y_i","t2d_y2y_i","t2d_z2y_i","00"]

        # 直積
        target_test_params_base = list(itertools.product(test_param00, repeat=3))

        target_test_params_list = target_test_params_base

        random.shuffle(target_test_params_list)
        print("start LIST: %s" % len(target_test_params_list))

        random.shuffle(target_test_params_list)

        prefix = "delegate_qq_15-05"
        rep_target_name_list = ["手首B","ひじB"]
        ok_list = self.calc_delegate_qq(target_test_params_list, 1, rep_target_name_list, False, prefix)

        print("ok_list LIST: %s" % ok_list)
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)


    def test_delegate_qq_18(self):
        test_param01 = ["d2dy_lnn", "d2dy_xnn", "d2dy_ynn", "d2dy_znn", "t2dy_lnn", "t2dy_xnn", "t2dy_ynn", "t2dy_znn", "d2dy_lin", "d2dy_xin", "d2dy_yin", "d2dy_zin", "t2dy_lin", "t2dy_xin", "t2dy_yin", "t2dy_zin", "d2dy_lnl", "d2dy_xnl", "d2dy_ynl", "d2dy_znl", "t2dy_lnl", "t2dy_xnl", "t2dy_ynl", "t2dy_znl", "d2dy_lil", "d2dy_xil", "d2dy_yil", "d2dy_zil", "t2dy_lil", "t2dy_xil", "t2dy_yil", "t2dy_zil", "d2dy_lnr", "d2dy_xnr", "d2dy_ynr", "d2dy_znr", "t2dy_lnr", "t2dy_xnr", "t2dy_ynr", "t2dy_znr", "d2dy_lir", "d2dy_xir", "d2dy_yir", "d2dy_zir", "t2dy_lir", "t2dy_xir", "t2dy_yir", "t2dy_zir","00"]

        # 直積
        target_test_params_base = list(itertools.product(test_param01, repeat=3))

        target_test_params_list = target_test_params_base

        random.shuffle(target_test_params_list)
        print("start LIST: %s" % len(target_test_params_list))

        random.shuffle(target_test_params_list)

        prefix = "delegate_qq_18-02"
        rep_target_index_list = ["C","D","E"]
        ok_list = self.calc_delegate_qq(target_test_params_list, 0.5, rep_target_index_list, False, prefix)

        print("ok_list LIST: %s" % len(ok_list))
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)


    def test_delegate_qq_20(self):
        test_param01 = ["d2d_local_qq","d2d_x2x_qq","d2d_y2x_qq","d2d_z2x_qq","t2d_local_qq","t2d_x2x_qq","t2d_y2x_qq","t2d_z2x_qq","d2d_local_lqq","d2d_x2x_lqq","d2d_y2x_lqq","d2d_z2x_lqq","t2d_local_lqq","t2d_x2x_lqq","t2d_y2x_lqq","t2d_z2x_lqq","d2d_local_rqq","d2d_x2x_rqq","d2d_y2x_rqq","d2d_z2x_rqq","t2d_local_rqq","t2d_x2x_rqq","t2d_y2x_rqq","t2d_z2x_rqq","dl_x2y","dl_y2y","dl_z2y","d2d_local_qqi","d2d_x2x_qqi","d2d_y2x_qqi","d2d_z2x_qqi","t2d_local_qqi","t2d_x2x_qqi","t2d_y2x_qqi","t2d_z2x_qqi","d2d_local_lqqi","d2d_x2x_lqqi","d2d_y2x_lqqi","d2d_z2x_lqqi","t2d_local_lqqi","t2d_x2x_lqqi","t2d_y2x_lqqi","t2d_z2x_lqqi","d2d_local_rqqi","d2d_x2x_rqqi","d2d_y2x_rqqi","d2d_z2x_rqqi","t2d_local_rqqi","t2d_x2x_rqqi","t2d_y2x_rqqi","t2d_z2x_rqqi","dl_x2yi","dl_y2yi","dl_z2yi"]

        # 直積
        target_test_params_base = list(itertools.product(test_param01, repeat=3))

        target_test_params_list = target_test_params_base

        random.shuffle(target_test_params_list)
        print("start LIST: %s" % len(target_test_params_list))

        random.shuffle(target_test_params_list)

        prefix = "delegate_qq_20-03"
        rep_target_index_list = ["C","D","E"]
        ok_list = self.calc_delegate_qq(target_test_params_list, 0.5, rep_target_index_list, False, prefix)

        print("ok_list LIST: %s" % len(ok_list))
        print("ok_list target: %s" % prefix)
        self.assertGreater(len(ok_list), 0)




    def calc_delegate_qq(self, target_test_params, limit, rep_target_index_list, exist_ok, prefix=""):
        # VMD読み込み
        motion = VmdReader().read_vmd_file("D:/MMD/MikuMikuDance_v926x64/UserFile/Motion/ダンス_1人/愛言葉III なつき/nac_aikotoba3_0-500_操作中心.vmd")

        # 作成元モデル
        trace_model = PmxReader().read_pmx_file("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/初音ミク/らぶ式ミク/らぶ式ミク_準標準.pmx")

        # 変換先モデル
        replace_model = PmxReader().read_pmx_file("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/初音ミク/Tda式初音ミク_盗賊つばき流Ｍトレースモデル配布 v1.07/Tda式初音ミク_盗賊つばき流Mトレースモデルv1.07_腕回転.pmx")
        # replace_model = PmxReader().read_pmx_file("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/刀剣乱舞/011_今剣/今剣 ゆるん式 ver0124/ライブ衣装/今剣インナー_準標準.pmx")

        target_frames = [187,227,241,300,309,318,412]

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
        is_alternative_model = True
        is_no_delegate = False
        target_avoidance_rigids = []
        target_avoidance_bones = []
        base_path = "E:/MMD/MikuMikuDance_v926x64/Work/202001_sizing/delegate_qq"

        logger.info("len: %s", len(target_test_params))
        ok_list = []

        dir_path = "{0}/{1}/test".format(base_path, prefix)
        os.makedirs(dir_path, exist_ok=exist_ok)

        for pidx, test_param in enumerate(target_test_params):
            logger.info("prefix: %s, test_param(%s): %s", len(target_test_params) - pidx, prefix, test_param)

            file_name = "test_{0}.vmd".format(','.join([str(i) for i in test_param]))

            dir_path = "{0}/{1}/test".format(base_path, prefix)
            os.makedirs(dir_path, exist_ok=True)
            output_vmd_path = "{0}/{1}".format(dir_path, file_name)

            copy_motion = copy.deepcopy(motion)

            try:
                main.main(copy_motion, trace_model, replace_model, output_vmd_path, \
                    is_avoidance, is_avoidance_finger, is_hand_ik, hand_distance, is_floor_hand, is_floor_hand_up, is_floor_hand_down, hand_floor_distance, leg_floor_distance, is_finger_ik, finger_distance, vmd_choice_values, rep_choice_values, rep_rate_values, \
                    camera_motion, camera_vmd_path, camera_pmx, output_camera_vmd_path, camera_y_offset, is_alternative_model, is_no_delegate, target_avoidance_rigids, target_avoidance_bones, test_param)
            except Exception as e:
                print(traceback.format_exc())
                continue
            
            for rep_bone_index in rep_target_index_list:
                result_txt_list = []
                total_result_list = []
                total_diff_list = []

                for bone_part_name in ["ひじ", "手首"]:
                    result_list = []
                    diff_list = []

                    is_elbow_ok = True

                    for direction in ["右", "左"]:
                        rep_bone_name = "{0}{1}{2}".format(direction, bone_part_name, rep_bone_index)

                        test_target_name = rep_bone_name[:3]
                        links, indexes = replace_model.create_link_2_top_one(test_target_name)

                        # 事前にグローバル位置を求めておく
                        target_bfs = [x for x in copy_motion.frames[test_target_name] if x.frame in target_frames]
                        org_target_poss = []

                        for bf in target_bfs:
                            _, _, _, _, org_global_3ds = utils.create_matrix_global(replace_model, links, copy_motion.frames, bf, None)
                            org_target_poss.append(org_global_3ds[-1])

                        # 変換後のグローバル位置を求める
                        rep_target_bfs = copy.deepcopy([x for x in copy_motion.frames[rep_bone_name] if x.frame in target_frames])
                        rep_target_poss = []

                        for bf in rep_target_bfs:
                            rep_links, _ = replace_model.create_link_2_top_all(rep_bone_name)
                            _, _, _, _, rep_global_3ds = utils.create_matrix_global(replace_model, rep_links, copy_motion.frames, bf, None)
                            rep_target_poss.append(rep_global_3ds[-1])

                        for org_target_pos, rep_target_pos in zip(org_target_poss, rep_target_poss):
                            is_x_diff = org_target_pos.x() - limit <= rep_target_pos.x() <= org_target_pos.x() + limit
                            is_y_diff = org_target_pos.y() - limit <= rep_target_pos.y() <= org_target_pos.y() + limit
                            is_z_diff = org_target_pos.z() - limit <= rep_target_pos.z() <= org_target_pos.z() + limit
                            
                            result = is_x_diff and is_y_diff and is_z_diff
                            result_list.append(result)
                            total_result_list.append(result)

                            if bone_part_name == "手首":
                                diff_euler = rep_target_pos - org_target_pos
                                total_diff_list.append(diff_euler.length())
                                diff_txt = "{0: 03.2f}".format(round(diff_euler.length(), 2))
                                diff_list.append(diff_txt)

                    result_txt = "{0:02}#{1}".format(result_list.count(True), ','.join([str(i) for i in diff_list]))

                resutl_file_name = "{0:02}_{1: 03.2f}_{2}_{3}_{4}.vmd".format(total_result_list.count(True), sum(total_diff_list), rep_bone_index, ','.join([str(i) for i in test_param]), result_txt)
                
                dir_path = "{0}/{1}/{1}_OK{2:02}".format(base_path, prefix, total_result_list.count(True))
                os.makedirs(dir_path, exist_ok=True)

                # TRUE(一致した場合)
                if total_result_list.count(True) > 0:
                    ok_list.append(test_param)

                shutil.copy(output_vmd_path, "{0}/{1}".format(dir_path, resutl_file_name))
                logger.info("result: %s %s", total_result_list.count(True), resutl_file_name)
                        
        return ok_list

if __name__ == "__main__":
    unittest.main(defaultTest="TestSubStance.test_upper_stance_upper2_up_47")
