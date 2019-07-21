# -*- coding: utf-8 -*-
# 接触回避処理
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

def exec(motion, trace_model, replace_model, is_avoidance, is_avoidance_finger, is_hand_ik, error_file_handler, error_file_logger):

    # -----------------------------------------------------------------
    # 頭部と腕の接触回避処理        
    if motion.motion_cnt > 0 and is_avoidance and not is_hand_ik:
        # 頭までのリンク生成
        head_links, _ = replace_model.create_link_2_top( "頭")

        # 人差し指までのリンク生成
        if "左人指先" in replace_model.bones and is_avoidance_finger:
            all_rep_finger_links, _ = replace_model.create_link_2_top_lr("人指先")
        else:
            # 指のないモデルは手首で代用。もしくは手首を明示的に選択した場合
            all_rep_finger_links, _ = replace_model.create_link_2_top_lr("手首")

        # for l in left_wrist_links:
        #     logger.debug("left_wrist_links: %s", l)
        
        # 上半身～頭部の頂点の抽出
        upper_vertices = replace_model.get_upper_vertices(head_links)

        for f in range(motion.last_motion_frame + 1):
            for k in ["左腕", "左ひじ", "右腕", "右ひじ"]:
                if k in motion.frames:
                    for bf in motion.frames[k]:
                        if bf.key == True and bf.frame == f:

                            # 方向
                            direction = "左" if "左" in k else "右"

                            # 現時点の上半身の位置
                            upper_vertex_pos = calc_upper_vertex(upper_vertices, replace_model, head_links, motion.frames, bf)

                            # 回転調整
                            adjust_by_hand(replace_model, direction, all_rep_finger_links[direction], motion.frames, bf, upper_vertex_pos)

                        elif bf.frame > f:
                            break

    return True


# 頭の中に入っているか
def is_inner_upper(upper_pos, elbow_pos, finger_pos, replace_model, upper_vertex_pos, direction, bf):

    logger.debug("is_inner_upper sh: %s, el: %s, fi: %s", upper_pos.y(), elbow_pos.y(), finger_pos.y() )

    # if upper_pos.y() > finger_pos.y():
    #     # 上半身Yより指が下ならとりあえずFalse
    #     return False
    
    # 小数点第一で丸めた範囲内でチェック
    round_finger_pos = round(finger_pos.y(), 1)

    for rfp in [round_finger_pos - 0.2, round_finger_pos - 0.1, round_finger_pos, round_finger_pos + 0.1, round_finger_pos + 0.2]:
        if rfp in upper_vertex_pos.keys():

            # if direction == "左" and bf.frame == 0:
            #     logger.debug("指Z: d: %s, rfp:%s, vmin: %s, vmax: %s, wf: %s:", direction, rfp, upper_vertex_pos[rfp]["min"].z(), upper_vertex_pos[rfp]["max"].z(), finger_pos)

            if upper_vertex_pos[rfp]["min"].z() - 0.1 <= finger_pos.z() <= upper_vertex_pos[rfp]["max"].z() + 0.1:                
                for uv in upper_vertex_pos[rfp]["values"]:
                    
                    # if direction == "左" and bf.frame == 0:
                    #     logger.debug("指Z接触: d: %s, u: %s, wf: %s", direction, uv.x(), finger_pos.x())

                    if direction == "左" and finger_pos.x() <= uv.x() + 0.2:
                        logger.debug("左頭-指接触: v: %s, f: %s", uv, finger_pos)
                        # 左手で上半身より内側ならTrue
                        return True
                    if direction == "右" and uv.x() - 0.2 <= finger_pos.x():
                        # 右手で上半身より内側ならTrue
                        logger.debug("右頭-指接触: v: %s, wf: %s", uv, finger_pos)
                        return True

                    # ひじを除外対象にするとガクッとなるので保留。
                    # if direction == "左" and elbow_pos.x() <= uv.x():
                    #     logger.debug("左頭-ひじ接触: v: %s, f: %s", uv, elbow_pos)
                    #     # 左手で上半身より内側ならTrue
                    #     return True
                    # if direction == "右" and uv.x() <= elbow_pos.x():
                    #     # 右手で上半身より内側ならTrue
                    #     logger.debug("右頭-ひじ接触: v: %s, wf: %s", uv, elbow_pos)
                    #     return True

                # if bf.frame == 338:
                #     logger.debug("指接触なし: d: %s, v: %s, wf: %s", direction, uv, finger_pos)

    # どれもヒットしなければFalse
    return False            


# 人指の位置の計算
def calc_hand_pos(model, wrist_links, frames, bf):

    # グローバル行列算出
    _, _, _, _, global_3ds = utils.create_matrix_global(model, wrist_links, frames, bf)

    upper_pos = QVector3D()
    elbow_pos = QVector3D()
    finger_pos = QVector3D()

    logger.debug("--------------")
    for lidx, lbone in enumerate(reversed(wrist_links)):
        logger.debug("frame: %s: lidx: %s, %s, %s", bf.frame, lidx, lbone.name, global_3ds[lidx])

        if "上半身" == lbone.name:
            # 上半身固定
            upper_pos = global_3ds[lidx]

        if "ひじ" in lbone.name:
            elbow_pos = global_3ds[lidx]

        if lidx == len(wrist_links) - 1:
            # 先端を指とする
            finger_pos = global_3ds[lidx]

    return upper_pos, elbow_pos, finger_pos


# 手の調整
def adjust_by_hand(replace_model, direction, wrist_links, frames, bf, upper_vertex_pos, cnt=0):
    # logger.debug("adjust_by_hand: %s, %s ------------------", cnt, bf.frame )

    # 手の位置
    upper_pos, elbow_pos, finger_pos = calc_hand_pos(replace_model, wrist_links, frames, bf)
    # logger.debug("upper_pos: %s", upper_pos)
    # logger.debug("elbow_pos: %s", elbow_pos)
    # logger.debug("finger_pos: %s", finger_pos)

    if is_inner_upper(upper_pos, elbow_pos, finger_pos, replace_model, upper_vertex_pos, direction, bf) == False:
        logger.debug("接触無し frame: %s, finger: %s", bf.frame, finger_pos)
        return

    # 腕調整
    adjust_by_arm_bone(replace_model, direction, wrist_links, frames, bf, upper_vertex_pos, "{0}腕".format(direction))
    if cnt % 3 == 0:
        # ひじ調整
        adjust_by_elbow_bone(replace_model, direction, wrist_links, frames, bf, upper_vertex_pos, "{0}ひじ".format(direction))

    if cnt < 10:
        # 調整してもまだ頭の中に入っていたら、自分を再呼び出し
        return adjust_by_hand(replace_model, direction, wrist_links, frames, bf, upper_vertex_pos, cnt+1)
    else:
        # 10回呼び出してもダメならその時点のを返す
        print("接触解消失敗 frame: %s, finger: %s" % (bf.frame, finger_pos))
        return

def adjust_by_arm_bone(replace_model, direction, wrist_links, frames, bf, upper_vertex_pos, bone_name):
    # 調整値
    av = 0.9

    # ボーン -------------
    bone_idx, _ = utils.get_prev_bf(frames, bone_name, bf.frame)

    # 全体を減らす
    rot = frames[bone_name][bone_idx].rotation
    frames[bone_name][bone_idx].rotation.setX( rot.x() * av )
    frames[bone_name][bone_idx].rotation.setY( rot.y() * av )
    frames[bone_name][bone_idx].rotation.setZ( rot.z() * av )
    frames[bone_name][bone_idx].rotation.normalize()

    upper_pos, elbow_pos, finger_pos = calc_hand_pos(replace_model, wrist_links, frames, bf)
    if is_inner_upper(upper_pos, elbow_pos, finger_pos, replace_model, upper_vertex_pos, direction, bf) == False:
        print("接触解消-%s frame: %s, finger: %s" % (bone_name, bf.frame, finger_pos))
        return

def adjust_by_elbow_bone(replace_model, direction, wrist_links, frames, bf, upper_vertex_pos, bone_name):
    # 調整値
    av = 0.9

    # ボーン -------------
    bone_idx, _ = utils.get_prev_bf(frames, bone_name, bf.frame)

    # 全体を減らす
    rot = frames[bone_name][bone_idx].rotation
    frames[bone_name][bone_idx].rotation.setX( rot.x() * av )
    frames[bone_name][bone_idx].rotation.setY( rot.y() * av )
    frames[bone_name][bone_idx].rotation.setZ( rot.z() * av )
    frames[bone_name][bone_idx].rotation.normalize()

    upper_pos, elbow_pos, finger_pos = calc_hand_pos(replace_model, wrist_links, frames, bf)
    if is_inner_upper(upper_pos, elbow_pos, finger_pos, replace_model, upper_vertex_pos, direction, bf) == False:
        print("接触解消-%s frame: %s, finger: %s" % (bone_name, bf.frame, finger_pos))
        return

# 頭の頂点の位置の計算
def calc_upper_vertex(upper_vertices, model, head_links, frames, bf):
    # キー：頂点Y位置小数点第一位まるめ
    upper_vertex_pos = {}

    # グローバル行列算出
    _, _, _, matrixs = utils.create_matrix(model, head_links, frames, bf)

    # 該当ボーンのグローバル行列まで求める
    upper_matrixes = [QMatrix4x4() for i in range(len(head_links))]

    for n in range(len(matrixs)):
        for m in range(n+1):
            if n == 0:
                # 最初は行列そのもの
                upper_matrixes[n] = copy.deepcopy(matrixs[0])
            else:
                # 2番目以降は行列をかける
                upper_matrixes[n] *= copy.deepcopy(matrixs[m])

            # logger.debug("**u_matrixes[%s]: %s %s -> %s", n, m, matrixs[m], upper_matrixes[n])
        
        # logger.debug("upper_matrixes[%s]: %s", n, upper_matrixes[n])

    # 該当リンクボーンのリンクINDEX取得
    head_links_indexes = {}
    for lidx, l in enumerate(reversed(head_links)):
        head_links_indexes[l.index] = lidx

    # 上半身の頂点位置
    for uv in upper_vertices:
        # 頂点が乗っているウェイトボーン情報取得
        deform_bone = model.bones[model.bone_indexes[uv.deform.index0]]

        # 頂点初期位置
        uv_diff = uv.position - deform_bone.position

        # 上半身の頂点の位置を算出する
        upper_pos = upper_matrixes[head_links_indexes[deform_bone.index]] * QVector4D(uv_diff, 1)
        # logger.debug("upper_matrixes0 : %s, upper_pos: %s", upper_matrixes[0], upper_pos)
        # logger.debug("upper_matrixes1 : %s, upper_pos: %s", upper_matrixes[1], upper_pos)

        # 3Dに変換
        uv_pos = upper_pos.toVector3D()
        uv_round = round(uv_pos.y(), 1)
        # logger.debug("uv_pos.y: %s -> %s: 0:%s, -1:%s, 1:%s", uv_pos.y(), uv_round, round(uv_pos.y(), 0), round(uv_pos.y(), -1), round(uv_pos.y(), 1))
        if uv_round not in upper_vertex_pos.keys():
            upper_vertex_pos[uv_round] = {}
            # 最小値
            upper_vertex_pos[uv_round]["min"] = QVector3D(99999, 99999, 99999)
            # 最大値
            upper_vertex_pos[uv_round]["max"] = QVector3D(-99999, -99999, -99999)
            # 実値
            upper_vertex_pos[uv_round]["values"] = []

        # if round(uv.position.y(),2) == 8.01:
        #     logger.debug("v: %s %s, uv_pos: %s", uv.index, uv.position, uv_pos)

        if upper_vertex_pos[uv_round]["min"].z() > uv_pos.z():
            # 最小値より小さい場合、上書き
            upper_vertex_pos[uv_round]["min"] = uv_pos

        if upper_vertex_pos[uv_round]["max"].z() < uv_pos.z():
            # 最大値より小さい場合、上書き
            upper_vertex_pos[uv_round]["max"] = uv_pos
        
        # 実値追加
        upper_vertex_pos[uv_round]["values"].append(uv_pos)
    
    # if bf.frame == 0:
    #     for uvkey in upper_vertex_pos.keys():
    #         logger.debug("upper_vertex_pos key: %s, min: %s, max: %s, len: %s", uvkey, upper_vertex_pos[uv_round]["min"], upper_vertex_pos[uv_round]["max"], len(upper_vertex_pos[uvkey]["values"]))

    return upper_vertex_pos
