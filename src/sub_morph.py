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

logger = logging.getLogger("VmdSizing").getChild(__name__)

def exec(motion, trace_model, replace_model, output_vmd_path, vmd_choice_values, rep_choice_values, rep_rate_values):

    # モーフ置換
    if len(vmd_choice_values) > 0 and len(rep_choice_values) > 0 and len(rep_rate_values) > 0 and len(vmd_choice_values) == len(rep_choice_values) == len(rep_rate_values):
        print("■■ モーフ補正 -----------------")

        # モーフの大きさ変更処理
        replace_morphs = create_replace_morphs(motion, vmd_choice_values, rep_choice_values, rep_rate_values)

        # モーフのクリア処理
        clear_morphs(motion, vmd_choice_values)

        # モーフのブレンド処理
        blended_morphs = blend_morphs(motion, replace_morphs)

        # モーフの登録処理
        regist_morphs(motion, blended_morphs)

    return True

# モーフの置き換え処理を実行する
def create_replace_morphs(motion, vmd_choice_values, rep_choice_values, rep_rate_values):
    # 変換後のモーフリスト　キー：変換後モーフ、値：モーフリスト
    replace_morphs = {}
    
    # VMDのオリジナルモーフと変換後のモーフをまとめてまわす
    for vcv, rcv, rcr in zip(vmd_choice_values, rep_choice_values, rep_rate_values):
        # VMDの該当キーがある場合
        if vcv in motion.morphs.keys():
            print("モーフ置換 %s → %s (%s)" % (vcv, rcv, rcr))
            # Shift-JISでエンコード
            rcv_encode = rcv.encode('cp932').decode('shift_jis').encode('shift_jis')
            # モーフを組合せで保持
            replace_morphs[(rcv,vcv)] = copy.deepcopy(motion.morphs[vcv])

            # そのキーの名前は全部変換後のモーフ名とする
            for morph in replace_morphs[(rcv,vcv)]:
                morph.name = rcv_encode
                morph.format_name = rcv
                # モーフの大きさを補正する
                morph.ratio *= rcr
    
    return replace_morphs

# モーフの登録処理
def blend_morphs(motion, replace_morphs):

    # ブレンドしたモーフ情報　キー：置換後モーフ、値：モーフリスト
    blended_morphs = {}

    # 最終的に登録する置換後モーフのリストを生成しておく
    for (rcv, vcv) in replace_morphs.keys():
        logger.debug("rcv: %s, vcv: %s, keys: %s", rcv, vcv, motion.morphs.keys())
        if rcv in motion.morphs.keys():
            logger.debug("モーションデータにキーがある場合それを保持")
            # モーションデータにキーがある場合それを保持
            blended_morphs[rcv] = copy.deepcopy(motion.morphs[rcv])
        else:
            # キーがない場合、新規配列
            blended_morphs[rcv] = []

    # モーフの登録処理
    for (rcv, vcv), mlist in replace_morphs.items():
        # 既存のを変換先に合算する
        for _, rm in enumerate(mlist):
            logger.debug("enumerate: rm: %s", rm.frame)
            is_blended = False

            logger.debug("blended_morphs[rcv]: %s", [x.frame for x in blended_morphs[rcv]])
            for bdm in blended_morphs[rcv]:
                logger.debug("check: bdm: %s, rm: %s", bdm.frame, rm.frame)
                if bdm.frame == rm.frame:
                    logger.debug("add: bdm: %s(%s), rm: %s(%s)", bdm.frame, bdm.ratio, rm.frame, rm.ratio)
                    # 既存のフレームと同じ番号のフレームにモーフを追加する場合、合算
                    is_blended = True
                    bdm.ratio += rm.ratio
                    logger.debug("add after: bdm: %s(%s), rm: %s(%s)", bdm.frame, bdm.ratio, rm.frame, rm.ratio)
                    break

            if not is_blended:
                logger.debug("既存のリストにない場合、そのまま設定: rm: %s", rm.frame)
                # 既存のリストにない場合、そのまま設定
                blended_morphs[rcv].append(rm)

    return blended_morphs

# モーフのクリア処理
def clear_morphs(motion, vmd_choice_values):
    for vcv in vmd_choice_values:
        if vcv in motion.morphs.keys():
            motion.morphs[vcv] = []

# モーフの登録処理
def regist_morphs(motion, blended_morphs):
    for bmk, bmv in blended_morphs.items():
        logger.debug("bmk: %s", bmk)
        motion.morphs[bmk] = bmv
    