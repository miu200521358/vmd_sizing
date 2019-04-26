# -*- coding: utf-8 -*-
#

import io
import struct
import logging
import re
import numpy as np
from PyQt5.QtGui import QQuaternion, QVector3D
from VmdWriter import VmdBoneFrame, VmdMorphFrame

logger = logging.getLogger("__main__").getChild(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

class ModelBole():
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
