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
import utils_arm_ik

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestUtilsArmIK(unittest.TestCase):

    def test_cleanup_none(self):
        # モーションの宣言
        motion = VmdMotion()

        bf = VmdBoneFrame()
        bf.format_name = "左手首"
        bf.frame = 0
        bf.read = True
        bf.key = True
        motion.frames["左手首"] = []
        motion.frames["左手首"].append(bf)
        

        # 腕リストの宣言
        arm_links = self.create_arm_links()

        utils_arm_ik.cleanup(motion, arm_links)

        self.assertEqual(1, len(motion.frames))

    def create_arm_links(self):
        arm_links = {"左": [ \
            PmxModel().Bone("左手首", "", QVector3D(0,0,0), -1, None, None, )
        ], "右": []}

        return arm_links

if __name__ == "__main__":
    unittest.main()
