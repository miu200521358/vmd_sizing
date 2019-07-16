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
        self.assertEqual(39, beforebz[1].x())
        self.assertEqual(39, beforebz[1].y())
        self.assertEqual(78, beforebz[2].x())
        self.assertEqual(78, beforebz[2].y())
        self.assertEqual(127, beforebz[3].x())
        self.assertEqual(127, beforebz[3].y())

        self.assertEqual(0, afterbz[0].x())
        self.assertEqual(0, afterbz[0].y())
        self.assertEqual(11, afterbz[1].x())
        self.assertEqual(11, afterbz[1].y())
        self.assertEqual(34, afterbz[2].x())
        self.assertEqual(34, afterbz[2].y())
        self.assertEqual(127, afterbz[3].x())
        self.assertEqual(127, afterbz[3].y())

    def test_calc_bezier_split_02(self):
        beforebz, afterbz = utils.calc_bezier_split(11, 11, 34, 34, 5, 30, 15, "左手首")

        self.assertEqual(0, beforebz[0].x())
        self.assertEqual(0, beforebz[0].y())
        self.assertEqual(25, beforebz[1].x())
        self.assertEqual(25, beforebz[1].y())
        self.assertEqual(60, beforebz[2].x())
        self.assertEqual(60, beforebz[2].y())
        self.assertEqual(127, beforebz[3].x())
        self.assertEqual(127, beforebz[3].y())

        self.assertEqual(0, afterbz[0].x())
        self.assertEqual(0, afterbz[0].y())
        self.assertEqual(22, afterbz[1].x())
        self.assertEqual(22, afterbz[1].y())
        self.assertEqual(59, afterbz[2].x())
        self.assertEqual(59, afterbz[2].y())
        self.assertEqual(127, afterbz[3].x())
        self.assertEqual(127, afterbz[3].y())

    def test_calc_bezier_split_03(self):
        beforebz, afterbz = utils.calc_bezier_split(127, 0, 70, 122, 5112, 5122, 5117, "左手首")

        self.assertEqual(0, beforebz[0].x())
        self.assertEqual(0, beforebz[0].y())
        self.assertEqual(39, beforebz[1].x())
        self.assertEqual(39, beforebz[1].y())
        self.assertEqual(78, beforebz[2].x())
        self.assertEqual(78, beforebz[2].y())
        self.assertEqual(127, beforebz[3].x())
        self.assertEqual(127, beforebz[3].y())

        self.assertEqual(0, afterbz[0].x())
        self.assertEqual(0, afterbz[0].y())
        self.assertEqual(11, afterbz[1].x())
        self.assertEqual(11, afterbz[1].y())
        self.assertEqual(34, afterbz[2].x())
        self.assertEqual(34, afterbz[2].y())
        self.assertEqual(127, afterbz[3].x())
        self.assertEqual(127, afterbz[3].y())



if __name__ == "__main__":
    unittest.main()
