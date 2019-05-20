# -*- coding: utf-8 -*-
#

import logging
import copy
from PyQt5.QtGui import QQuaternion, QVector3D
from VmdWriter import VmdBoneFrame, VmdMorphFrame

logger = logging.getLogger("__main__").getChild(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

class ModelBone():
    def __init__(self):
        # 1列目
        self.name = ""
        # 13列目
        self.parent = None
        # IK系の2列目
        self.links = []
        # 5,6,7列目
        self.position = QVector3D(0, 0, 0)
        # 親ボーンからの長さ(計算）
        self.len = 0
        # 軸制限
        self.axis_limit = QVector3D(0, 0, 0)

class ModelBoneJoint():
    def __init__(self, mb, rotation):
        # 名前を引き継ぐ
        self.name = mb.name
        # 位置を引き継ぐ
        self.position = copy.deepcopy(mb.position)
        # 回転は指定された値
        self.rotation = rotation
