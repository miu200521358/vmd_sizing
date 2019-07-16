# -*- coding: utf-8 -*-
# モーフ処理
# 
import logging
import copy
from PyQt5.QtGui import QQuaternion, QVector3D, QVector2D, QMatrix4x4, QVector4D

from VmdWriter import VmdWriter, VmdBoneFrame
from VmdReader import VmdReader
from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader
import utils

logger = logging.getLogger("__main__").getChild(__name__)

def exec(motion, trace_model, replace_model, vmd_choice_values, rep_choice_values, rep_rate_values, error_path, error_file_logger):

    # モーフ置換
    if len(vmd_choice_values) > 0 and len(rep_choice_values) > 0 and len(rep_rate_values) > 0 and len(vmd_choice_values) == len(rep_choice_values) == len(rep_rate_values):
        # VMDのオリジナルモーフと変換後のモーフをまとめてまわす
        for vcv, rcv, rcr in zip(vmd_choice_values, rep_choice_values, rep_rate_values):
            # VMDの該当キーがある場合
            if vcv in motion.morphs.keys():
                print("モーフ置換 %s → %s (%s)" % (vcv, rcv, rcr))
                # Shift-JISでエンコード
                rcv_encode = rcv.encode('shift-jis')
                # そのキーの名前は全部変換後のモーフ名とする
                for morph in motion.morphs[vcv]:
                    morph.name = rcv_encode
                    # モーフの大きさを補正する
                    morph.ratio *= rcr

    return True
