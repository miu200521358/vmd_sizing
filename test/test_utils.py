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
import utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestUtils(unittest.TestCase):

    def test_calc_bezier_split_01(self):
        beforebz, afterbz = utils.calc_bezier_split(10, 10, 20, 20, 0, 30, 5, "左手首")

        self.assertEqual(0, beforebz[0].x())
        self.assertEqual(0, beforebz[0].y())
        self.assertEqual(26, beforebz[1].x())
        self.assertEqual(26, beforebz[1].y())
        self.assertEqual(52, beforebz[2].x())
        self.assertEqual(52, beforebz[2].y())
        self.assertEqual(127, beforebz[3].x())
        self.assertEqual(127, beforebz[3].y())

        self.assertEqual(0, afterbz[0].x())
        self.assertEqual(0, afterbz[0].y())
        self.assertEqual(19, afterbz[1].x())
        self.assertEqual(19, afterbz[1].y())
        self.assertEqual(55, afterbz[2].x())
        self.assertEqual(55, afterbz[2].y())
        self.assertEqual(127, afterbz[3].x())
        self.assertEqual(127, afterbz[3].y())

    def test_calc_bezier_split_02(self):
        beforebz, afterbz = utils.calc_bezier_split(19, 19, 55, 55, 5, 30, 15, "左手首")

        self.assertEqual(0, beforebz[0].x())
        self.assertEqual(0, beforebz[0].y())
        self.assertEqual(26, beforebz[1].x())
        self.assertEqual(26, beforebz[1].y())
        self.assertEqual(66, beforebz[2].x())
        self.assertEqual(66, beforebz[2].y())
        self.assertEqual(127, beforebz[3].x())
        self.assertEqual(127, beforebz[3].y())

        self.assertEqual(0, afterbz[0].x())
        self.assertEqual(0, afterbz[0].y())
        self.assertEqual(32, afterbz[1].x())
        self.assertEqual(32, afterbz[1].y())
        self.assertEqual(74, afterbz[2].x())
        self.assertEqual(74, afterbz[2].y())
        self.assertEqual(127, afterbz[3].x())
        self.assertEqual(127, afterbz[3].y())

    def test_calc_bezier_split_03(self):
        beforebz, afterbz = utils.calc_bezier_split(127, 0, 0, 127, 10, 20, 15, "左手首")

        self.assertEqual(0, beforebz[0].x())
        self.assertEqual(0, beforebz[0].y())
        self.assertEqual(127, beforebz[1].x())
        self.assertEqual(0, beforebz[1].y())
        self.assertEqual(127, beforebz[2].x())
        self.assertEqual(64, beforebz[2].y())
        self.assertEqual(127, beforebz[3].x())
        self.assertEqual(127, beforebz[3].y())

        self.assertEqual(0, afterbz[0].x())
        self.assertEqual(0, afterbz[0].y())
        self.assertEqual(0, afterbz[1].x())
        self.assertEqual(64, afterbz[1].y())
        self.assertEqual(0, afterbz[2].x())
        self.assertEqual(127, afterbz[2].y())
        self.assertEqual(127, afterbz[3].x())
        self.assertEqual(127, afterbz[3].y())

    def test_calc_bezier_split_04(self):
        beforebz, afterbz = utils.calc_bezier_split(127, 0, 0, 127, 10, 20, 14, "左手首")

    def test_calc_bezier_split_05(self):
        beforebz, afterbz = utils.calc_bezier_split(127, 0, 0, 127, 10, 20, 13, "左手首")

    def test_calc_bezier_split_06(self):
        beforebz, afterbz = utils.calc_bezier_split(127, 0, 0, 127, 10, 20, 12, "左手首")

    def test_calc_bezier_split_07(self):
        beforebz, afterbz = utils.calc_bezier_split(127, 0, 0, 127, 10, 20, 11, "左手首")

    def test_calc_bezier_split_08(self):
        beforebz, afterbz = utils.calc_bezier_split(127, 0, 0, 127, 10, 20, 16, "左手首")

    def test_calc_bezier_split_09(self):
        beforebz, afterbz = utils.calc_bezier_split(127, 0, 0, 127, 10, 20, 17, "左手首")

    def test_calc_bezier_split_10(self):
        beforebz, afterbz = utils.calc_bezier_split(127, 0, 0, 127, 10, 20, 18, "左手首")

    def test_calc_bezier_split_11(self):
        beforebz, afterbz = utils.calc_bezier_split(127, 0, 0, 127, 10, 20, 19, "左手首")


if __name__ == "__main__":
    unittest.main()
