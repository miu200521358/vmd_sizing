# -*- coding: utf-8 -*-
# 腕IK処理テスト
# 
import sys
import pathlib
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
import sub_arm_ik, utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestSubArmIK(unittest.TestCase):

    def test_reset_complement_01(self):
        # モーションの宣言
        motion = VmdMotion()
        motion.frames["左手首"] = []

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 0
        bf.read = True
        bf.key = True
        bf.complement = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
        motion.frames["左手首"].append(bf)

        # 腕リストの宣言
        arm_links = self.create_arm_links()

        # 処理実施
        sub_arm_ik.reset_complement(motion, arm_links)

        for c in motion.frames["左手首"][0].complement:
            self.assertEqual(10, c)

    def test_reset_complement_02(self):
        # モーションの宣言
        motion = VmdMotion()
        motion.frames["左手首"] = []

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 0
        bf.read = True
        bf.key = True
        bf.complement = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
        motion.frames["左手首"].append(bf)

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 30
        bf.read = True
        bf.key = True
        bf.complement = [20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20]
        motion.frames["左手首"].append(bf)

        # 腕リストの宣言
        arm_links = self.create_arm_links()

        # 処理実施
        sub_arm_ik.reset_complement(motion, arm_links)

        for c in motion.frames["左手首"][0].complement:
            self.assertEqual(10, c)

        for c in motion.frames["左手首"][1].complement:
            self.assertEqual(20, c)

    def test_reset_complement_03(self):
        # モーションの宣言
        motion = VmdMotion()
        motion.frames["左手首"] = []

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 0
        bf.read = True
        bf.key = True
        bf.complement = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
        motion.frames["左手首"].append(bf)

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 5
        bf.read = True
        # 間に有効キーなし
        bf.key = False
        bf.complement = [30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]
        motion.frames["左手首"].append(bf)

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 30
        bf.read = True
        bf.key = True
        bf.complement = [20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20]
        motion.frames["左手首"].append(bf)

        # 腕リストの宣言
        arm_links = self.create_arm_links()

        # 処理実施
        sub_arm_ik.reset_complement(motion, arm_links)

        for c in motion.frames["左手首"][0].complement:
            self.assertEqual(10, c)

        for c in motion.frames["左手首"][1].complement:
            self.assertEqual(30, c)

        for c in motion.frames["左手首"][2].complement:
            self.assertEqual(20, c)

    def test_reset_complement_04(self):
        # モーションの宣言
        motion = VmdMotion()
        motion.frames["左手首"] = []

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 0
        bf.read = True
        bf.key = True
        for r in utils.R_x1_idxs:
            bf.complement[r] = 10
        for r in utils.R_y1_idxs:
            bf.complement[r] = 10
        for r in utils.R_x2_idxs:
            bf.complement[r] = 10
        for r in utils.R_y2_idxs:
            bf.complement[r] = 10
        motion.frames["左手首"].append(bf)

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 5
        bf.read = True
        # 間に有効キーあり
        bf.key = True
        for r in utils.R_x1_idxs:
            bf.complement[r] = 30
        for r in utils.R_y1_idxs:
            bf.complement[r] = 30
        for r in utils.R_x2_idxs:
            bf.complement[r] = 30
        for r in utils.R_y2_idxs:
            bf.complement[r] = 30
        motion.frames["左手首"].append(bf)

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 30
        bf.read = True
        bf.key = True
        for r in utils.R_x1_idxs:
            bf.complement[r] = 10
        for r in utils.R_y1_idxs:
            bf.complement[r] = 10
        for r in utils.R_x2_idxs:
            bf.complement[r] = 20
        for r in utils.R_y2_idxs:
            bf.complement[r] = 20
        motion.frames["左手首"].append(bf)

        # 腕リストの宣言
        arm_links = self.create_arm_links()

        # 処理実施
        sub_arm_ik.reset_complement(motion, arm_links)

        # ---------------------------------
        # 前回の開始X
        for r in utils.R_x1_idxs:
            self.assertEqual(10, motion.frames["左手首"][0].complement[r])

        # 前回の開始Y
        for r in utils.R_y1_idxs:
            self.assertEqual(10, motion.frames["左手首"][0].complement[r])

        # 前回の終了X
        for r in utils.R_x2_idxs:
            self.assertEqual(10, motion.frames["左手首"][0].complement[r])

        # 前回の終了Y
        for r in utils.R_y2_idxs:
            self.assertEqual(10, motion.frames["左手首"][0].complement[r])

        # ---------------------------------
        # 今回の開始X
        for r in utils.R_x1_idxs:
            self.assertEqual(30, motion.frames["左手首"][1].complement[r])

        # 今回の開始Y
        for r in utils.R_y1_idxs:
            self.assertEqual(30, motion.frames["左手首"][1].complement[r])

        # 今回の終了X
        for r in utils.R_x2_idxs:
            self.assertEqual(30, motion.frames["左手首"][1].complement[r])

        # 今回の終了Y
        for r in utils.R_y2_idxs:
            self.assertEqual(30, motion.frames["左手首"][1].complement[r])

        # ---------------------------------
        # 次回の開始X
        for r in utils.R_x1_idxs:
            self.assertEqual(10, motion.frames["左手首"][2].complement[r])

        # 次回の開始Y
        for r in utils.R_y1_idxs:
            self.assertEqual(10, motion.frames["左手首"][2].complement[r])

        # 次回の終了X
        for r in utils.R_x2_idxs:
            self.assertEqual(20, motion.frames["左手首"][2].complement[r])

        # 次回の終了Y
        for r in utils.R_y2_idxs:
            self.assertEqual(20, motion.frames["左手首"][2].complement[r])

    def test_reset_complement_05(self):
        # モーションの宣言
        motion = VmdMotion()
        motion.frames["左手首"] = []

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 0
        bf.read = True
        bf.key = True
        for r in utils.R_x1_idxs:
            bf.complement[r] = 10
        for r in utils.R_y1_idxs:
            bf.complement[r] = 10
        for r in utils.R_x2_idxs:
            bf.complement[r] = 10
        for r in utils.R_y2_idxs:
            bf.complement[r] = 10
        motion.frames["左手首"].append(bf)

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 5
        bf.read = True
        # 間に有効キーあり
        bf.key = True
        for r in utils.R_x1_idxs:
            bf.complement[r] = 30
        for r in utils.R_y1_idxs:
            bf.complement[r] = 30
        for r in utils.R_x2_idxs:
            bf.complement[r] = 30
        for r in utils.R_y2_idxs:
            bf.complement[r] = 30
        motion.frames["左手首"].append(bf)

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 10
        bf.read = False
        # 有効キーの次に無効キー
        bf.key = False
        for r in utils.R_x1_idxs:
            bf.complement[r] = 30
        for r in utils.R_y1_idxs:
            bf.complement[r] = 30
        for r in utils.R_x2_idxs:
            bf.complement[r] = 30
        for r in utils.R_y2_idxs:
            bf.complement[r] = 30
        motion.frames["左手首"].append(bf)

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 30
        bf.read = True
        bf.key = True
        for r in utils.R_x1_idxs:
            bf.complement[r] = 10
        for r in utils.R_y1_idxs:
            bf.complement[r] = 10
        for r in utils.R_x2_idxs:
            bf.complement[r] = 20
        for r in utils.R_y2_idxs:
            bf.complement[r] = 20
        motion.frames["左手首"].append(bf)

        # 腕リストの宣言
        arm_links = self.create_arm_links()

        # 処理実施
        sub_arm_ik.reset_complement(motion, arm_links)

        # ---------------------------------
        # 前回の開始X
        for r in utils.R_x1_idxs:
            self.assertEqual(10, motion.frames["左手首"][0].complement[r])

        # 前回の開始Y
        for r in utils.R_y1_idxs:
            self.assertEqual(10, motion.frames["左手首"][0].complement[r])

        # 前回の終了X
        for r in utils.R_x2_idxs:
            self.assertEqual(10, motion.frames["左手首"][0].complement[r])

        # 前回の終了Y
        for r in utils.R_y2_idxs:
            self.assertEqual(10, motion.frames["左手首"][0].complement[r])

        # ---------------------------------
        # 今回の開始X
        for r in utils.R_x1_idxs:
            self.assertEqual(30, motion.frames["左手首"][1].complement[r])

        # 今回の開始Y
        for r in utils.R_y1_idxs:
            self.assertEqual(30, motion.frames["左手首"][1].complement[r])

        # 今回の終了X
        for r in utils.R_x2_idxs:
            self.assertEqual(30, motion.frames["左手首"][1].complement[r])

        # 今回の終了Y
        for r in utils.R_y2_idxs:
            self.assertEqual(30, motion.frames["左手首"][1].complement[r])

        # ---------------------------------
        # 無効次回の開始X
        for r in utils.R_x1_idxs:
            self.assertEqual(30, motion.frames["左手首"][2].complement[r])

        # 無効次回の開始Y
        for r in utils.R_y1_idxs:
            self.assertEqual(30, motion.frames["左手首"][2].complement[r])

        # 無効次回の終了X
        for r in utils.R_x2_idxs:
            self.assertEqual(30, motion.frames["左手首"][2].complement[r])

        # 無効次回の終了Y
        for r in utils.R_y2_idxs:
            self.assertEqual(30, motion.frames["左手首"][2].complement[r])

        # ---------------------------------
        # 次回の開始X
        for r in utils.R_x1_idxs:
            self.assertEqual(10, motion.frames["左手首"][3].complement[r])

        # 次回の開始Y
        for r in utils.R_y1_idxs:
            self.assertEqual(10, motion.frames["左手首"][3].complement[r])

        # 次回の終了X
        for r in utils.R_x2_idxs:
            self.assertEqual(20, motion.frames["左手首"][3].complement[r])

        # 次回の終了Y
        for r in utils.R_y2_idxs:
            self.assertEqual(20, motion.frames["左手首"][3].complement[r])

    def test_reset_complement_06(self):
        # モーションの宣言
        motion = VmdMotion()
        motion.frames["左手首"] = []

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 0
        bf.read = True
        bf.key = True
        for r in utils.R_x1_idxs:
            bf.complement[r] = 10
        for r in utils.R_y1_idxs:
            bf.complement[r] = 10
        for r in utils.R_x2_idxs:
            bf.complement[r] = 10
        for r in utils.R_y2_idxs:
            bf.complement[r] = 10
        motion.frames["左手首"].append(bf)

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 5
        bf.read = True
        # 間に有効キーあり
        bf.key = True
        for r in utils.R_x1_idxs:
            bf.complement[r] = 30
        for r in utils.R_y1_idxs:
            bf.complement[r] = 30
        for r in utils.R_x2_idxs:
            bf.complement[r] = 30
        for r in utils.R_y2_idxs:
            bf.complement[r] = 30
        motion.frames["左手首"].append(bf)

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 10
        bf.read = False
        # 有効キーの次に無効キー
        bf.key = False
        for r in utils.R_x1_idxs:
            bf.complement[r] = 30
        for r in utils.R_y1_idxs:
            bf.complement[r] = 30
        for r in utils.R_x2_idxs:
            bf.complement[r] = 30
        for r in utils.R_y2_idxs:
            bf.complement[r] = 30
        motion.frames["左手首"].append(bf)

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 15
        bf.read = False
        # 2つ目の有効キー
        bf.key = True
        for r in utils.R_x1_idxs:
            bf.complement[r] = 30
        for r in utils.R_y1_idxs:
            bf.complement[r] = 30
        for r in utils.R_x2_idxs:
            bf.complement[r] = 30
        for r in utils.R_y2_idxs:
            bf.complement[r] = 30
        motion.frames["左手首"].append(bf)

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 30
        bf.read = True
        bf.key = True
        for r in utils.R_x1_idxs:
            bf.complement[r] = 10
        for r in utils.R_y1_idxs:
            bf.complement[r] = 10
        for r in utils.R_x2_idxs:
            bf.complement[r] = 20
        for r in utils.R_y2_idxs:
            bf.complement[r] = 20
        motion.frames["左手首"].append(bf)

        # 腕リストの宣言
        arm_links = self.create_arm_links()

        # 処理実施
        sub_arm_ik.reset_complement(motion, arm_links)

        # ---------------------------------
        # 前回の開始X
        for r in utils.R_x1_idxs:
            self.assertEqual(10, motion.frames["左手首"][0].complement[r])

        # 前回の開始Y
        for r in utils.R_y1_idxs:
            self.assertEqual(10, motion.frames["左手首"][0].complement[r])

        # 前回の終了X
        for r in utils.R_x2_idxs:
            self.assertEqual(10, motion.frames["左手首"][0].complement[r])

        # 前回の終了Y
        for r in utils.R_y2_idxs:
            self.assertEqual(10, motion.frames["左手首"][0].complement[r])

        # ---------------------------------
        # 今回の開始X
        for r in utils.R_x1_idxs:
            self.assertEqual(30, motion.frames["左手首"][1].complement[r])

        # 今回の開始Y
        for r in utils.R_y1_idxs:
            self.assertEqual(30, motion.frames["左手首"][1].complement[r])

        # 今回の終了X
        for r in utils.R_x2_idxs:
            self.assertEqual(30, motion.frames["左手首"][1].complement[r])

        # 今回の終了Y
        for r in utils.R_y2_idxs:
            self.assertEqual(30, motion.frames["左手首"][1].complement[r])

        # ---------------------------------
        # 無効次回の開始X
        for r in utils.R_x1_idxs:
            self.assertEqual(30, motion.frames["左手首"][2].complement[r])

        # 無効次回の開始Y
        for r in utils.R_y1_idxs:
            self.assertEqual(30, motion.frames["左手首"][2].complement[r])

        # 無効次回の終了X
        for r in utils.R_x2_idxs:
            self.assertEqual(30, motion.frames["左手首"][2].complement[r])

        # 無効次回の終了Y
        for r in utils.R_y2_idxs:
            self.assertEqual(30, motion.frames["左手首"][2].complement[r])

        # ---------------------------------
        # 有効次回の開始X
        for r in utils.R_x1_idxs:
            self.assertEqual(17, motion.frames["左手首"][3].complement[r])

        # 有効次回の開始Y
        for r in utils.R_y1_idxs:
            self.assertEqual(17, motion.frames["左手首"][3].complement[r])

        # 有効次回の終了X
        for r in utils.R_x2_idxs:
            self.assertEqual(34, motion.frames["左手首"][3].complement[r])

        # 有効次回の終了Y
        for r in utils.R_y2_idxs:
            self.assertEqual(34, motion.frames["左手首"][3].complement[r])

        # ---------------------------------
        # 次回の開始X
        for r in utils.R_x1_idxs:
            self.assertEqual(29, motion.frames["左手首"][4].complement[r])

        # 次回の開始Y
        for r in utils.R_y1_idxs:
            self.assertEqual(29, motion.frames["左手首"][4].complement[r])

        # 次回の終了X
        for r in utils.R_x2_idxs:
            self.assertEqual(70, motion.frames["左手首"][4].complement[r])

        # 次回の終了Y
        for r in utils.R_y2_idxs:
            self.assertEqual(70, motion.frames["左手首"][4].complement[r])


    def test_reset_complement_07(self):
        # モーションの宣言
        motion = VmdMotion()
        motion.frames["左手首"] = []

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 0
        bf.read = True
        bf.key = True
        bf.complement = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
        motion.frames["左手首"].append(bf)

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 30
        bf.read = False
        bf.key = False
        bf.complement = [20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20]
        motion.frames["左手首"].append(bf)

        # 腕リストの宣言
        arm_links = self.create_arm_links()

        # 処理実施
        sub_arm_ik.reset_complement(motion, arm_links)

        for c in motion.frames["左手首"][0].complement:
            self.assertEqual(10, c)

        for c in motion.frames["左手首"][1].complement:
            self.assertEqual(20, c)







    def create_arm_links(self):
        arm_links = {"左": [ \
            PmxModel().Bone("左手首", "", QVector3D(), -1, None, None, )
        ], "右": []}

        return arm_links



if __name__ == "__main__":
    unittest.main()
