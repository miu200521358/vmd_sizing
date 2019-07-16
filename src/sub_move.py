# -*- coding: utf-8 -*-
# 移動系ボーン縮尺処理
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


def exec(motion, trace_model, replace_model, error_path, error_file_logger):

    # 移植先のセンターとグルーブは、作成元の比率に合わせる
    adjust_center(trace_model, replace_model, "センター")
    adjust_center(trace_model, replace_model, "グルーブ")

    # 足IKのXYZの比率
    xz_ratio, y_ratio, leg_ik_stance = calc_leg_ik_ratio(trace_model, replace_model)

    # センターのZ軸オフセットを計算
    cal_center_z_offset(trace_model, replace_model, "センター")
    
    # 全ての親をコピー
    copy_root_parent(trace_model)
    copy_root_parent(replace_model)

    # サイズ比較
    # lengths = compare_length(trace_model, replace_model)

    if motion.motion_cnt > 0:
        # -----------------------------------------------------------------
        # 移動ボーン縮尺
        for k in ["右足ＩＫ親" ,"左足ＩＫ親", "右足ＩＫ" ,"左足ＩＫ", "右つま先ＩＫ" ,"左つま先ＩＫ", "センター", "グルーブ", "全ての親"]:
            if k in motion.frames and k in replace_model.bones:
                for bf in motion.frames[k]:
                    # IK比率をそのまま掛ける
                    bf.position.setX( bf.position.x() * xz_ratio )
                    bf.position.setY( bf.position.y() * y_ratio )
                    bf.position.setZ( bf.position.z() * xz_ratio )

                    if replace_model.bones[k].offset_z != 0:
                        # Zオフセットが入っている場合、オフセット調整
                        bf.position.setZ(bf.position.z() + replace_model.bones[k].offset_z) 

                print("調整終了: %s" % k)

    return True



def cal_center_z_offset(trace_model, replace_model, bone_name):
    if bone_name in trace_model.bones and bone_name in replace_model.bones and "左足首" in trace_model.bones and "左足首" in replace_model.bones and "左足" in trace_model.bones and "左足" in replace_model.bones and "左つま先ＩＫ" in trace_model.bones and "左つま先ＩＫ" in replace_model.bones:
        # 移植元にも移植先にも対象ボーンがある場合
        # 作成元左足首のZ位置
        trace_ankle_z = trace_model.bones["左足首"].position.z()
        # 作成元左足のZ位置
        trace_leg_z = trace_model.bones["左足"].position.z()
        # 作成元つま先IKのZ位置
        trace_toe_z = trace_model.bones["左つま先ＩＫ"].position.z()

        # トレース変換先左足首のZ位置
        replace_ankle_z = replace_model.bones["左足首"].position.z()
        # トレース変換先左足のZ位置
        replace_leg_z = replace_model.bones["左足"].position.z()
        # トレース変換先つま先IKのZ位置
        replace_toe_z = replace_model.bones["左つま先ＩＫ"].position.z()

        # 作成元の足の長さ
        trace_leg_zlength = trace_ankle_z - trace_toe_z
        # 作成元の重心
        trace_center_gravity = (trace_leg_z - trace_ankle_z) / (trace_toe_z - trace_ankle_z)
        logger.debug("trace_center_gravity %s, trace_leg_zlength: %s", trace_center_gravity, trace_leg_zlength)
        
        # トレース変換先の足の長さ
        replace_leg_zlength = replace_ankle_z - replace_toe_z
        # トレース変換先の重心
        replace_center_gravity = (replace_leg_z - replace_ankle_z) / (replace_toe_z - replace_ankle_z)
        logger.debug("replace_center_gravity %s, replace_leg_zlength: %s", replace_center_gravity, replace_leg_zlength)
        
        replace_model.bones[bone_name].offset_z = (replace_center_gravity - trace_center_gravity) * ( replace_leg_zlength / trace_leg_zlength )

        print("Zオフセット: %s: %s" % ( bone_name, replace_model.bones[bone_name].offset_z))
    else:
        print("Zオフセットなし: %s: %s" % ( bone_name, replace_model.bones[bone_name].offset_z))

def calc_leg_ik_ratio(trace_model, replace_model):
    if "左足" in trace_model.bones and "左足" in replace_model.bones and "左ひざ" in trace_model.bones and "左ひざ" in replace_model.bones and "左足首" in trace_model.bones and "左足首" in replace_model.bones and "センター" in trace_model.bones and "センター" in replace_model.bones:
        # XZ比率(足の長さ)
        replace_leg_length = ( (replace_model.bones["左足首"].position - replace_model.bones["左ひざ"].position) + (replace_model.bones["左ひざ"].position - replace_model.bones["左足"].position) ).length()
        trace_leg_length = ( (trace_model.bones["左足首"].position - trace_model.bones["左ひざ"].position) + (trace_model.bones["左ひざ"].position - trace_model.bones["左足"].position) ).length()
        logger.debug("xz_ratio replace_leg_length: %s, trace_leg_length: %s", replace_leg_length, trace_leg_length)
        xz_ratio = 1 if trace_leg_length == 0 else ( replace_leg_length / trace_leg_length )

        # Y比率(股下のY差)
        replace_leg_length = (replace_model.bones["左足首"].position - replace_model.bones["左足"].position).y()
        trace_leg_length = (trace_model.bones["左足首"].position - trace_model.bones["左足"].position).y()        
        logger.debug("y_ratio replace_leg_length: %s, trace_leg_length: %s", replace_leg_length, trace_leg_length)
        y_ratio = 1 if trace_leg_length == 0 else ( replace_leg_length / trace_leg_length )

        print("足の長さの比率: xz: %s, y: %s" % (xz_ratio, y_ratio))

        # # 左足のスタンス距離比
        # l_stance = ((replace_model.bones["左足ＩＫ"].position - replace_model.bones["センター"].position).x()) - ((trace_model.bones["左足ＩＫ"].position - trace_model.bones["センター"].position).x() * xz_ratio)
        # r_stance = ((replace_model.bones["右足ＩＫ"].position - replace_model.bones["センター"].position).x()) - ((trace_model.bones["右足ＩＫ"].position - trace_model.bones["センター"].position).x() * xz_ratio)

        # logger.debug("replace: %s", (replace_model.bones["左足ＩＫ"].position - replace_model.bones["センター"].position).x())
        # logger.debug("trace: %s", (trace_model.bones["左足ＩＫ"].position - trace_model.bones["センター"].position).x())
        # logger.debug("trace2: %s", ((trace_model.bones["左足ＩＫ"].position - trace_model.bones["センター"].position).x() * xz_ratio))

        # # print("足のスタンス補正値: l: %s, r: %s" % (l_stance, r_stance))

        return xz_ratio, y_ratio, {"左": 1, "右": 1}

    print("足、ひざ、足首、センターのいずれかのボーンが不足しているため、足の長さの比率が測れませんでした")
    return 1, 1, {"左": 1, "右": 1}

def adjust_center(trace_model, replace_model, bone_name):
    if bone_name in trace_model.bones and bone_name in replace_model.bones and "左足" in trace_model.bones and "左足" in replace_model.bones:
        # 移植元にも移植先にも対象ボーンがある場合
        # 左足付け根のY位置
        leg_y = trace_model.bones["左足"].position.y()
        # センター（もしくはグルーブ）のY位置
        center_y = trace_model.bones[bone_name].position.y()
        # 足のどの辺りにセンターがあるか判定
        ratio_y = center_y / leg_y
        
        # 作成元と同じ比率の位置にセンターを置く
        replace_model.bones[bone_name].len = replace_model.bones["左足"].position.y() * ratio_y

        # logger.debug("len: %s, center_y: %s, leg_y: %s, ratio_y:%s, pos: %s", replace_model.bones[bone_name].len, center_y, leg_y, ratio_y, replace_model.bones["下半身"].position.y())

def copy_root_parent(model):
    if "全ての親" in model.bones.keys() and "センター" in model.bones.keys():
        # 全ての親がある場合、センターの長さをコピーする
        logger.debug("全ての親: %s <- %s", model.bones["全ての親"].len, model.bones["センター"].len)
        model.bones["全ての親"].len = model.bones["センター"].len

def compare_length(trace_model, replace_model):
    lengths = {}

    for k, v in replace_model.bones.items():
        # 移植先モデルのボーン構造チェック
        if k in trace_model.bones:
            # 同じ項目が作成元にもある場合
            trace_bone_length = trace_model.bones[k].len
            replace_bone_length = replace_model.bones[k].len

            # print("k: %s, len: %s" % (k, replace_model.bones[k].len) )

            # 0割対策を入れて、倍率取得
            length = 1 if trace_bone_length == 0 else replace_bone_length / trace_bone_length

            # length.setX(length.x() if np.isnan(length.x()) == False and np.isinf(length.x()) == False else 0)
            # length.setY(length.y() if np.isnan(length.y()) == False and np.isinf(length.y()) == False else 0)
            # length.setZ(length.z() if np.isnan(length.z()) == False and np.isinf(length.z()) == False else 0)
            # if k in ["右足ＩＫ親" ,"左足ＩＫ親", "右足ＩＫ" ,"左足ＩＫ", "右つま先ＩＫ" ,"左つま先ＩＫ", "センター", "グルーブ", "全ての親"]:
            #     print("%s, 比率: %s, 生成元の長さ: %s, 変換先の長さ: %s" % (k, length, trace_bone_length, replace_bone_length))

            lengths[k] = length
    
    return lengths



