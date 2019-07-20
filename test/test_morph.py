# -*- coding: utf-8 -*-
# モーフ
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

from VmdWriter import VmdWriter, VmdMorphFrame
from VmdReader import VmdReader, VmdMotion
from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader
import sub_morph, utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestSubMorph(unittest.TestCase):

    def test_create_replace_morphs_01(self):
        logger.info("-------------------------")
        motion = VmdMotion()
        motion.morphs["あ"] = []
        
        m = VmdMorphFrame()
        m.name = "あ".encode('shift-jis')
        m.frame = 0
        m.ratio = 10
        motion.morphs["あ"].append(m)


        vmd_choice_values = ["あ"]
        rep_choice_values = ["い"]
        rep_rate_values = [1]

        replace_morphs = sub_morph.create_replace_morphs(motion, vmd_choice_values, rep_choice_values, rep_rate_values)

        self.assertEqual(1, len(replace_morphs))
        self.assertEqual("い", list(replace_morphs.keys())[0])
        self.assertEqual("あ", list(replace_morphs["い"].keys())[0])
        
        m = replace_morphs["い"]["あ"][0]
        self.assertEqual("い".encode('shift-jis'), m.name)
        self.assertEqual(0, m.frame)
        self.assertEqual(10, m.ratio)

    def test_create_replace_morphs_02(self):
        logger.info("-------------------------")
        motion = VmdMotion()
        motion.morphs["あ"] = []
        
        m = VmdMorphFrame()
        m.name = "あ".encode('shift-jis')
        m.frame = 0
        m.ratio = 10
        motion.morphs["あ"].append(m)


        vmd_choice_values = ["あ"]
        rep_choice_values = ["い"]
        rep_rate_values = [0.55]

        replace_morphs = sub_morph.create_replace_morphs(motion, vmd_choice_values, rep_choice_values, rep_rate_values)

        self.assertEqual(1, len(replace_morphs))
        self.assertEqual("い", list(replace_morphs.keys())[0])
        self.assertEqual("あ", list(replace_morphs["い"].keys())[0])
        
        m = replace_morphs["い"]["あ"][0]
        self.assertEqual("い".encode('shift-jis'), m.name)
        self.assertEqual(0, m.frame)
        self.assertEqual(5.5, m.ratio)

    def test_create_replace_morphs_03(self):
        logger.info("-------------------------")
        motion = VmdMotion()
        motion.morphs["あ"] = []
        motion.morphs["い"] = []
        
        m = VmdMorphFrame()
        m.name = "あ".encode('shift-jis')
        m.frame = 0
        m.ratio = 10
        motion.morphs["あ"].append(m)

        m = VmdMorphFrame()
        m.name = "い".encode('shift-jis')
        m.frame = 3
        m.ratio = 20
        motion.morphs["い"].append(m)

        vmd_choice_values = ["あ"]
        rep_choice_values = ["い"]
        rep_rate_values = [0.55]

        replace_morphs = sub_morph.create_replace_morphs(motion, vmd_choice_values, rep_choice_values, rep_rate_values)

        self.assertEqual(1, len(replace_morphs))
        self.assertEqual("い", list(replace_morphs.keys())[0])
        self.assertEqual("あ", list(replace_morphs["い"].keys())[0])
        
        m = replace_morphs["い"]["あ"][0]
        self.assertEqual("い".encode('shift-jis'), m.name)
        self.assertEqual(0, m.frame)
        self.assertEqual(5.5, m.ratio)

    def test_create_replace_morphs_04(self):
        logger.info("-------------------------")
        motion = VmdMotion()
        motion.morphs["あ"] = []
        motion.morphs["う"] = []
        
        m = VmdMorphFrame()
        m.name = "あ".encode('shift-jis')
        m.frame = 0
        m.ratio = 10
        motion.morphs["あ"].append(m)

        m = VmdMorphFrame()
        m.name = "あ".encode('shift-jis')
        m.frame = 4
        m.ratio = 20
        motion.morphs["あ"].append(m)

        m = VmdMorphFrame()
        m.name = "う".encode('shift-jis')
        m.frame = 10
        m.ratio = 30
        motion.morphs["う"].append(m)

        vmd_choice_values = ["あ", "う"]
        rep_choice_values = ["い", "い"]
        rep_rate_values = [0.6, 0.3]

        replace_morphs = sub_morph.create_replace_morphs(motion, vmd_choice_values, rep_choice_values, rep_rate_values)
        # logger.info("replace_morphs: %s, ", replace_morphs)    

        self.assertEqual(1, len(replace_morphs))
        self.assertEqual("い", list(replace_morphs.keys())[0])
        self.assertEqual(2, len(replace_morphs["い"].keys()))   

        self.assertEqual("あ", list(replace_morphs["い"].keys())[0])

        m = replace_morphs["い"]["あ"][0]
        self.assertEqual("い".encode('shift-jis'), m.name)
        self.assertEqual(0, m.frame)
        self.assertEqual(6, m.ratio)

        m = replace_morphs["い"]["あ"][1]
        self.assertEqual("い".encode('shift-jis'), m.name)
        self.assertEqual(4, m.frame)
        self.assertEqual(12, m.ratio)

        self.assertEqual("う", list(replace_morphs["い"].keys())[1])
        
        m = replace_morphs["い"]["う"][0]
        self.assertEqual("い".encode('shift-jis'), m.name)
        self.assertEqual(10, m.frame)
        self.assertEqual(9, m.ratio)

    def test_regist_morphs_01(self):
        logger.info("-------------------------")
        motion = VmdMotion()
        motion.morphs["あ"] = []
        
        m = VmdMorphFrame()
        m.name = "あ".encode('shift-jis')
        m.frame = 0
        m.ratio = 10
        motion.morphs["あ"].append(m)

        vmd_choice_values = ["あ"]
        rep_choice_values = ["い"]
        rep_rate_values = [1]

        replace_morphs = {}
        replace_morphs["い"] = {}
        replace_morphs["い"]["あ"] = []

        m = VmdMorphFrame()
        m.name = "い".encode('shift-jis')
        m.frame = 0
        m.ratio = 6
        replace_morphs["い"]["あ"].append(m)

        sub_morph.regist_morphs(motion, vmd_choice_values, rep_choice_values, rep_rate_values, replace_morphs)

        self.assertEqual(2, len(motion.morphs))

        self.assertEqual("あ", list(motion.morphs.keys())[0])
        self.assertEqual(1, len(motion.morphs["あ"]))

        m = motion.morphs["あ"][0]
        self.assertEqual("あ".encode('shift-jis'), m.name)
        self.assertEqual(0, m.frame)
        self.assertEqual(10, m.ratio)

        self.assertEqual("い", list(motion.morphs.keys())[1])
        self.assertEqual(1, len(motion.morphs["い"]))

        m = motion.morphs["い"][0]
        self.assertEqual("い".encode('shift-jis'), m.name)
        self.assertEqual(0, m.frame)
        self.assertEqual(6, m.ratio)

    def test_regist_morphs_02(self):
        logger.info("-------------------------")
        motion = VmdMotion()
        motion.morphs["あ"] = []
        motion.morphs["い"] = []
        
        m = VmdMorphFrame()
        m.name = "あ".encode('shift-jis')
        m.frame = 0
        m.ratio = 10
        motion.morphs["あ"].append(m)

        m = VmdMorphFrame()
        m.name = "い".encode('shift-jis')
        m.frame = 3
        m.ratio = 20
        motion.morphs["い"].append(m)

        vmd_choice_values = ["あ"]
        rep_choice_values = ["い"]
        rep_rate_values = [1]

        replace_morphs = {}
        replace_morphs["い"] = {}
        replace_morphs["い"]["あ"] = []

        m = VmdMorphFrame()
        m.name = "い".encode('shift-jis')
        m.frame = 0
        m.ratio = 6
        replace_morphs["い"]["あ"].append(m)

        sub_morph.regist_morphs(motion, vmd_choice_values, rep_choice_values, rep_rate_values, replace_morphs)

        self.assertEqual(2, len(motion.morphs))

        self.assertEqual("あ", list(motion.morphs.keys())[0])
        self.assertEqual(1, len(motion.morphs["あ"]))

        m = motion.morphs["あ"][0]
        self.assertEqual("あ".encode('shift-jis'), m.name)
        self.assertEqual(0, m.frame)
        self.assertEqual(10, m.ratio)

        self.assertEqual("い", list(motion.morphs.keys())[1])
        self.assertEqual(2, len(motion.morphs["い"]))

        m = motion.morphs["い"][0]
        self.assertEqual("い".encode('shift-jis'), m.name)
        self.assertEqual(3, m.frame)
        self.assertEqual(20, m.ratio)

        m = motion.morphs["い"][1]
        self.assertEqual("い".encode('shift-jis'), m.name)
        self.assertEqual(0, m.frame)
        self.assertEqual(6, m.ratio)

    def test_regist_morphs_03(self):
        logger.info("-------------------------")
        motion = VmdMotion()
        motion.morphs["あ"] = []
        motion.morphs["い"] = []
        motion.morphs["う"] = []
        
        m = VmdMorphFrame()
        m.name = "あ".encode('shift-jis')
        m.frame = 0
        m.ratio = 10
        motion.morphs["あ"].append(m)

        m = VmdMorphFrame()
        m.name = "い".encode('shift-jis')
        m.frame = 3
        m.ratio = 20
        motion.morphs["い"].append(m)

        m = VmdMorphFrame()
        m.name = "う".encode('shift-jis')
        m.frame = 15
        m.ratio = 50
        motion.morphs["う"].append(m)

        vmd_choice_values = ["あ", "あ"]
        rep_choice_values = ["い", "う"]
        rep_rate_values = [1, 0.5]

        replace_morphs = {}
        replace_morphs["い"] = {}
        replace_morphs["い"]["あ"] = []
        replace_morphs["う"] = {}
        replace_morphs["う"]["あ"] = []

        m = VmdMorphFrame()
        m.name = "い".encode('shift-jis')
        m.frame = 0
        m.ratio = 6
        replace_morphs["い"]["あ"].append(m)

        m = VmdMorphFrame()
        m.name = "う".encode('shift-jis')
        m.frame = 5
        m.ratio = 25
        replace_morphs["う"]["あ"].append(m)

        sub_morph.regist_morphs(motion, vmd_choice_values, rep_choice_values, rep_rate_values, replace_morphs)

        self.assertEqual(3, len(motion.morphs))

        self.assertEqual("あ", list(motion.morphs.keys())[0])
        self.assertEqual(1, len(motion.morphs["あ"]))

        m = motion.morphs["あ"][0]
        self.assertEqual("あ".encode('shift-jis'), m.name)
        self.assertEqual(0, m.frame)
        self.assertEqual(10, m.ratio)

        self.assertEqual("い", list(motion.morphs.keys())[1])
        self.assertEqual(2, len(motion.morphs["い"]))

        m = motion.morphs["い"][0]
        self.assertEqual("い".encode('shift-jis'), m.name)
        self.assertEqual(3, m.frame)
        self.assertEqual(20, m.ratio)

        m = motion.morphs["い"][1]
        self.assertEqual("い".encode('shift-jis'), m.name)
        self.assertEqual(0, m.frame)
        self.assertEqual(6, m.ratio)

        self.assertEqual("う", list(motion.morphs.keys())[2])
        self.assertEqual(2, len(motion.morphs["う"]))

        m = motion.morphs["う"][0]
        self.assertEqual("う".encode('shift-jis'), m.name)
        self.assertEqual(15, m.frame)
        self.assertEqual(50, m.ratio)

        m = motion.morphs["う"][1]
        self.assertEqual("う".encode('shift-jis'), m.name)
        self.assertEqual(5, m.frame)
        self.assertEqual(25, m.ratio)


    def test_regist_morphs_04(self):
        logger.info("-------------------------")
        motion = VmdMotion()
        motion.morphs["あ"] = []
        motion.morphs["い"] = []
        motion.morphs["う"] = []
        
        m = VmdMorphFrame()
        m.name = "あ".encode('shift-jis')
        m.frame = 0
        m.ratio = 10
        motion.morphs["あ"].append(m)

        m = VmdMorphFrame()
        m.name = "い".encode('shift-jis')
        m.frame = 3
        m.ratio = 20
        motion.morphs["い"].append(m)

        m = VmdMorphFrame()
        m.name = "う".encode('shift-jis')
        m.frame = 5
        m.ratio = 3
        motion.morphs["う"].append(m)

        m = VmdMorphFrame()
        m.name = "う".encode('shift-jis')
        m.frame = 15
        m.ratio = 50
        motion.morphs["う"].append(m)

        vmd_choice_values = ["あ", "あ"]
        rep_choice_values = ["い", "う"]
        rep_rate_values = [1, 0.5]

        replace_morphs = {}
        replace_morphs["い"] = {}
        replace_morphs["い"]["あ"] = []
        replace_morphs["う"] = {}
        replace_morphs["う"]["あ"] = []

        m = VmdMorphFrame()
        m.name = "い".encode('shift-jis')
        m.frame = 0
        m.ratio = 6
        replace_morphs["い"]["あ"].append(m)

        m = VmdMorphFrame()
        m.name = "う".encode('shift-jis')
        m.frame = 5
        m.ratio = 25
        replace_morphs["う"]["あ"].append(m)

        sub_morph.regist_morphs(motion, vmd_choice_values, rep_choice_values, rep_rate_values, replace_morphs)

        self.assertEqual(3, len(motion.morphs))

        self.assertEqual("あ", list(motion.morphs.keys())[0])
        self.assertEqual(1, len(motion.morphs["あ"]))

        m = motion.morphs["あ"][0]
        self.assertEqual("あ".encode('shift-jis'), m.name)
        self.assertEqual(0, m.frame)
        self.assertEqual(10, m.ratio)

        self.assertEqual("い", list(motion.morphs.keys())[1])
        self.assertEqual(2, len(motion.morphs["い"]))

        m = motion.morphs["い"][0]
        self.assertEqual("い".encode('shift-jis'), m.name)
        self.assertEqual(3, m.frame)
        self.assertEqual(20, m.ratio)

        m = motion.morphs["い"][1]
        self.assertEqual("い".encode('shift-jis'), m.name)
        self.assertEqual(0, m.frame)
        self.assertEqual(6, m.ratio)

        self.assertEqual("う", list(motion.morphs.keys())[2])
        self.assertEqual(2, len(motion.morphs["う"]))

        m = motion.morphs["う"][0]
        self.assertEqual("う".encode('shift-jis'), m.name)
        self.assertEqual(5, m.frame)
        self.assertEqual(28, m.ratio)

        m = motion.morphs["う"][1]
        self.assertEqual("う".encode('shift-jis'), m.name)
        self.assertEqual(15, m.frame)
        self.assertEqual(50, m.ratio)


if __name__ == "__main__":
    unittest.main()
