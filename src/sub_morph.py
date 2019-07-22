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
        # モーフの大きさ変更処理
        replace_morphs = create_replace_morphs(motion, vmd_choice_values, rep_choice_values, rep_rate_values)

        # モーフのクリア処理
        clear_morphs(motion, vmd_choice_values)

        # モーフのブレンド処理
        blended_morphs = blend_morphs(motion, vmd_choice_values, rep_choice_values, rep_rate_values, replace_morphs)

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
            rcv_encode = rcv.encode('shift-jis')
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
def blend_morphs(motion, vmd_choice_values, rep_choice_values, rep_rate_values, replace_morphs):

    # ブレンドしたモーフ情報　キー：置換後モーフ、値：モーフリスト
    blended_morphs = {}

    # モーフの登録処理
    for (rcv, vcv), mlist in replace_morphs.items():
        # 変換したモーフを登録
        if not rcv in motion.morphs.keys():
            # 既存キーがまったくない場合、そのまま設定
            blended_morphs[rcv] = mlist
        else:
            # 変換先のモーフが、変換元にもある場合
            if rcv == vcv:
                # 変換元と変換先のモーフ名がまったく同じ場合、上書き
                blended_morphs[rcv] = mlist
            else:
                # 変換元と変換先のモーフ名が違う場合、既存のを変換先に加算する

                # 変換元と変換先をブレンドしたモーフリスト キー：フレーム番号, 値: モーフオブジェクト
                brend_morphs = {}

                for _, om in enumerate(motion.morphs[rcv]):
                    # 既存のをフレーム番号をキーに登録していく
                    brend_morphs[om.frame] = om

                for _, rm in enumerate(mlist):
                    # 変換後のをフレーム番号をキーに登録していく
                    if not rm.frame in brend_morphs.keys():
                        # まだないフレームの場合、そのまま追加
                        brend_morphs[rm.frame] = rm
                    else:
                        # フレームがある場合、加算
                        brend_morphs[rm.frame].ratio += rm.ratio
                
                # 合わせた結果を設定
                if not rcv in blended_morphs.keys():
                    blended_morphs[rcv] = []
                    
                for n, bm in enumerate(blended_morphs[rcv]):
                    if not bm.frame in brend_morphs.keys():
                        blended_morphs[rcv].append(brend_morphs[bm.frame])
                    else:
                        blended_morphs[rcv][n].ratio += brend_morphs[bm.frame].ratio

    return blended_morphs

# モーフのクリア処理
def clear_morphs(motion, vmd_choice_values):
    for vcv in vmd_choice_values:
        motion.morphs[vcv] = []

# モーフの登録処理
def regist_morphs(motion, blended_morphs):
    for bmk, bmv in blended_morphs.items():
        motion.morphs[bmk] = bmv
    