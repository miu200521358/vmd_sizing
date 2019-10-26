# -*- coding: utf-8 -*-
# カメラ処理テスト
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
import sub_camera2, utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestSubCamera2(unittest.TestCase):

    def test_calc_camera_pos_01(self):
        op1 = QVector3D(10,10,10)
        op2 = QVector3D(10,20,10)
        op3 = QVector3D(30,20,10)
        rp1 = QVector3D(15,15,15)
        rp2 = QVector3D(30,15,35)

        camera_pos = sub_camera2.calc_camera_pos(op1, op2, op3, rp1, rp2)

        self.assertEqual(15, camera_pos.x())


if __name__ == "__main__":
    unittest.main()
