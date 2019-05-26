# -*- coding: utf-8 -*-
#
import argparse
import os.path
import logging
import copy
import traceback
from datetime import datetime
from pathlib import Path
from PyQt5.QtGui import QQuaternion, QVector3D, QMatrix4x4, QVector4D

from VmdWriter import VmdWriter, VmdBoneFrame
from VmdReader import VmdReader
from PmxModel import PmxModel
from PmxReader import PmxReader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

level = {0:logging.ERROR,
            1:logging.WARNING,
            2:logging.INFO,
            3:logging.DEBUG}

def main(motion, trace_model, replace_model, output_vmd_path, is_avoidance):   
    print("vmd最終フレーム: %s" % motion.last_motion_frame)
    print("トレース元: %s" % trace_model.name)
    print("トレース先: %s" % replace_model.name)

    # 移植先のセンターとグルーブは、トレース元の比率に合わせる
    adjust_center(trace_model, replace_model, "センター")
    adjust_center(trace_model, replace_model, "グルーブ")
    
    # サイズ比較
    lengths = compare_length(trace_model, replace_model)

    # 変換サイズに合わせてモーション変換
    for k in ["右足ＩＫ" ,"左足ＩＫ", "右つま先ＩＫ" ,"左つま先ＩＫ", "センター", "グルーブ"]:
        if k in motion.frames and k in lengths:
            for bf in motion.frames[k]:
                # 移動量を倍率変換
                bf.position = bf.position * lengths[k]

    # 変換サイズに合わせてモーション変換
    if is_avoidance:

        # 頭までのIKリンク生成
        head_links = []
        replace_model.create_ik_link_2_top( "頭", head_links )

        # 人差し指までのIKリンク生成
        left_finger_links = []
        right_finger_links = []

        if "左人指３" in replace_model.bones:
            replace_model.create_ik_link_2_top("左人指３", left_finger_links )
            replace_model.create_ik_link_2_top("右人指３", right_finger_links )
        else:
            # 指のないモデルは手首で代用
            replace_model.create_ik_link_2_top("左手首", left_finger_links )
            replace_model.create_ik_link_2_top("右手首", right_finger_links )

        # for l in left_finger_links:
        #     logger.info("left_finger_links: %s", l)

        upper_vertices = replace_model.get_upper_vertices(head_links)

        for f in range(motion.last_motion_frame):
            for kidx, k in enumerate(["左腕", "左ひじ", "右腕", "右ひじ"]):
                if k in motion.frames:
                    for bf in motion.frames[k]:
                        if bf.key == True and bf.frame == f:

                            # 方向
                            direction = "左" if "左" in k else "右"

                            # 方向別リンク
                            finger_links = left_finger_links if direction == "左" else right_finger_links

                            # 現時点の上半身の位置
                            upper_vertex_pos = calc_upper_vertex(upper_vertices, replace_model, head_links, motion.frames, bf)

                            # 回転調整
                            adjust_by_hand(replace_model, direction, finger_links, motion.frames, bf, upper_vertex_pos)

                        elif bf.frame > f:
                            break

    # ディクショナリ型の疑似二次元配列から、一次元配列に変換
    bone_frames = []
    for k,v in motion.frames.items():
        for bf in v:
            if bf.key == True:
                # logger.debug("regist: %s, %s, %s, %s, %s", k, bf.name, bf.frame, bf.position, bf.rotation)
                bone_frames.append(bf)
    
    morph_frames = []
    for k,v in motion.morphs.items():
        for mf in v:
            # logger.debug("k: %s, mf: %s, %s", k, mf.frame, mf.ratio)
            morph_frames.append(mf)

    writer = VmdWriter()
    writer.write_vmd_file(output_vmd_path, bone_frames, morph_frames, None)

    print("■■■■■■■■■■■■■■■■■")
    print("■　変換出力完了: %s" % output_vmd_path)
    print("■■■■■■■■■■■■■■■■■")

# 手の調整
def adjust_by_hand(replace_model, direction, finger_links, frames, bf, upper_vertex_pos, cnt=0):
    # logger.info("adjust_by_hand: %s, %s ------------------", cnt, bf.frame )

    # 手の位置
    upper_pos, elbow_pos, finger_pos = calc_hand_pos(replace_model, finger_links, frames, bf)
    # logger.info("upper_pos: %s", upper_pos)
    # logger.info("elbow_pos: %s", elbow_pos)
    # logger.info("finger_pos: %s", finger_pos)

    if is_inner_upper(upper_pos, elbow_pos, finger_pos, replace_model, upper_vertex_pos, direction, bf) == False:
        logger.debug("接触無し frame: %s, finger: %s", bf.frame, finger_pos)
        return

    # 腕調整
    adjust_by_arm_bone(replace_model, direction, finger_links, frames, bf, upper_vertex_pos, "{0}腕".format(direction))
    if cnt % 2 == 0:
        # ひじ調整
        adjust_by_elbow_bone(replace_model, direction, finger_links, frames, bf, upper_vertex_pos, "{0}ひじ".format(direction))

    if cnt < 10:
        # 調整してもまだ頭の中に入っていたら、自分を再呼び出し
        return adjust_by_hand(replace_model, direction, finger_links, frames, bf, upper_vertex_pos, cnt+1)
    else:
        # 10回呼び出してもダメならその時点のを返す
        print("接触解消失敗 frame: %s, finger: %s" % (bf.frame, finger_pos))
        return

def adjust_by_arm_bone(replace_model, direction, finger_links, frames, bf, upper_vertex_pos, bone_name):
    # 調整値
    av = 0.9

    # ボーン -------------
    bone_idx, _ = get_prev_bf(frames, bone_name, bf.frame)
    ea = frames[bone_name][bone_idx].rotation.toEulerAngles()

    # ボーン - Z調整
    logger.debug("eav prev: %s, %s", ea, av)
    ea.setZ( ea.z() * av )
    logger.debug("eav after: %s, %s", ea, av)
    frames[bone_name][bone_idx].rotation = QQuaternion.fromEulerAngles(ea)
    upper_pos, elbow_pos, finger_pos = calc_hand_pos(replace_model, finger_links, frames, bf)
    logger.debug("bone-z bone: %s, finger: %s", frames[bone_name][bone_idx].rotation.toEulerAngles(), finger_pos )
    if is_inner_upper(upper_pos, elbow_pos, finger_pos, replace_model, upper_vertex_pos, direction, bf) == False:
        print("接触解消-z frame: %s %s, finger: %s" % (bone_name, bf.frame, finger_pos))
        return

    # ボーン - Y調整
    ea.setY( ea.y() * av )
    frames[bone_name][bone_idx].rotation = QQuaternion.fromEulerAngles(ea)
    upper_pos, elbow_pos, finger_pos = calc_hand_pos(replace_model, finger_links, frames, bf)
    logger.debug("bone-y bone: %s, finger: %s", frames[bone_name][bone_idx].rotation.toEulerAngles(), finger_pos )
    if is_inner_upper(upper_pos, elbow_pos, finger_pos, replace_model, upper_vertex_pos, direction, bf) == False:
        print("接触解消-y frame: %s %s, finger: %s" % (bone_name, bf.frame, finger_pos))
        return

def adjust_by_elbow_bone(replace_model, direction, finger_links, frames, bf, upper_vertex_pos, bone_name):
    # 調整値
    av = 0.9

    # ボーン -------------
    bone_idx, _ = get_prev_bf(frames, bone_name, bf.frame)
    ea = frames[bone_name][bone_idx].rotation.toEulerAngles()

    # ボーン - Y調整
    ea.setY( ea.y() * av )
    frames[bone_name][bone_idx].rotation = QQuaternion.fromEulerAngles(ea)
    upper_pos, elbow_pos, finger_pos = calc_hand_pos(replace_model, finger_links, frames, bf)
    logger.debug("bone-y bone: %s, finger: %s", frames[bone_name][bone_idx].rotation.toEulerAngles(), finger_pos )
    if is_inner_upper(upper_pos, elbow_pos, finger_pos, replace_model, upper_vertex_pos, direction, bf) == False:
        print("接触解消-y frame: %s %s, finger: %s" % (bone_name, bf.frame, finger_pos))
        return

    # ボーン - Z調整
    logger.debug("eav prev: %s, %s", ea, av)
    ea.setZ( ea.z() * av )
    logger.debug("eav after: %s, %s", ea, av)
    frames[bone_name][bone_idx].rotation = QQuaternion.fromEulerAngles(ea)
    upper_pos, elbow_pos, finger_pos = calc_hand_pos(replace_model, finger_links, frames, bf)
    logger.debug("bone-z bone: %s, finger: %s", frames[bone_name][bone_idx].rotation.toEulerAngles(), finger_pos )
    if is_inner_upper(upper_pos, elbow_pos, finger_pos, replace_model, upper_vertex_pos, direction, bf) == False:
        print("接触解消-z frame: %s %s, finger: %s" % (bone_name, bf.frame, finger_pos))
        return


# 指定されたフレームより前のキーを返す
def get_prev_bf(frames, bone_name, frameno):
    for bidx, bf in enumerate(frames[bone_name]):
        if bf.frame >= frameno:
            # 指定されたフレーム以降の一つ前で、前のキーを取る
            return bidx, frames[bone_name][bidx - 1]

    # 最後まで取れなければ、最終項目
    return len(frames[bone_name]) - 1, frames[bone_name][-1]

# 頭の中に入っているか
def is_inner_upper(upper_pos, elbow_pos, finger_pos, replace_model, upper_vertex_pos, direction, bf):

    # logger.info("is_inner_upper sh: %s fi: %s", upper_pos.y(), finger_pos.y() )

    # if upper_pos.y() > finger_pos.y():
    #     # 上半身Yより指が下ならとりあえずFalse
    #     return False
    
    # 小数点第一で丸めた範囲内でチェック
    round_finger_pos = round(finger_pos.y(), 1)

    for rfp in [round_finger_pos - 0.3, round_finger_pos, round_finger_pos + 0.1]:
        if rfp in upper_vertex_pos.keys():

            # logger.info("指Z: d: %s, rfp:%s, vmin: %s, vmax: %s, wf: %s:", direction, rfp, upper_vertex_pos[rfp]["min"].z(), upper_vertex_pos[rfp]["max"].z(), finger_pos)

            if upper_vertex_pos[rfp]["min"].z() - 0.1 <= finger_pos.z() <= upper_vertex_pos[rfp]["max"].z() + 0.1:
                for uv in upper_vertex_pos[rfp]["values"]:
                    if direction == "左" and finger_pos.x() <= uv.x() + 0.1:
                        logger.debug("左頭-指接触: v: %s, f: %s", uv, finger_pos)
                        # 左手で上半身より内側ならTrue
                        return True
                    if direction == "右" and uv.x() - 0.1 <= finger_pos.x():
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
def calc_hand_pos(model, finger_links, frames, bf):

    # グローバル行列算出
    _, _, _, global_4ds = create_matrix(model, finger_links, frames, bf)

    upper_pos = QVector3D()
    elbow_pos = QVector3D()
    finger_pos = QVector3D()

    for lidx, lbone in enumerate(reversed(finger_links)):
        if "上半身" == lbone.name:
            # 上半身固定
            upper_pos = global_4ds[lidx].toVector3D()

        if "ひじ" in lbone.name:
            elbow_pos = global_4ds[lidx].toVector3D()

        if lidx == len(finger_links) - 1:
            # 先端を指とする
            finger_pos = global_4ds[lidx].toVector3D()

    return upper_pos, elbow_pos, finger_pos


# 頭の頂点の位置の計算
def calc_upper_vertex(upper_vertices, model, head_links, frames, bf):
    # キー：頂点Y位置小数点第一位まるめ
    upper_vertex_pos = {}

    # グローバル行列算出
    _, _, matrixs, _ = create_matrix(model, head_links, frames, bf)

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

            # logger.info("**u_matrixes[%s]: %s %s -> %s", n, m, matrixs[m], upper_matrixes[n])
        
        # logger.info("upper_matrixes[%s]: %s", n, upper_matrixes[n])

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
        # logger.info("upper_matrixes0 : %s, upper_pos: %s", upper_matrixes[0], upper_pos)
        # logger.info("upper_matrixes1 : %s, upper_pos: %s", upper_matrixes[1], upper_pos)

        # 3Dに変換
        uv_pos = upper_pos.toVector3D()
        uv_round = round(uv_pos.y(), 1)
        # logger.info("uv_pos.y: %s -> %s: 0:%s, -1:%s, 1:%s", uv_pos.y(), uv_round, round(uv_pos.y(), 0), round(uv_pos.y(), -1), round(uv_pos.y(), 1))
        if uv_round not in upper_vertex_pos.keys():
            upper_vertex_pos[uv_round] = {}
            # 最小値
            upper_vertex_pos[uv_round]["min"] = QVector3D(99999, 99999, 99999)
            # 最大値
            upper_vertex_pos[uv_round]["max"] = QVector3D(-99999, -99999, -99999)
            # 実値
            upper_vertex_pos[uv_round]["values"] = []

        if upper_vertex_pos[uv_round]["min"].z() > uv_pos.z():
            # 最小値より小さい場合、上書き
            upper_vertex_pos[uv_round]["min"] = uv_pos

        if upper_vertex_pos[uv_round]["max"].z() < uv_pos.z():
            # 最大値より小さい場合、上書き
            upper_vertex_pos[uv_round]["max"] = uv_pos
        
        # 実値追加
        upper_vertex_pos[uv_round]["values"].append(uv_pos)

    # if bf.frame == 338:
    #     for uvkey in upper_vertex_pos.keys():
    #         logger.info("upper_vertex_pos key: %s, len: %s", uvkey, len(upper_vertex_pos[uvkey]))

    return upper_vertex_pos


# グローバル座標計算用行列生成
def create_matrix(model, links, frames, bf):

    # ローカル位置
    trans_vs = [QVector3D() for i in range(len(links))]
    # 加算用クォータニオン
    add_qs = [QQuaternion() for i in range(len(links))]

    for lidx, lbone in enumerate(reversed(links)):
        # 位置
        if lidx == 0:
            # 一番親は、グローバル座標を考慮
            trans_vs[lidx] = lbone.position - calc_bone_by_complement(frames, lbone.name, bf.frame).position
        else:
            # 位置：自身から親の位置を引いた値
            trans_vs[lidx] = lbone.position - links[len(links) - lidx].position

        # 回転
        rot = calc_bone_by_complement(frames, lbone.name, bf.frame).rotation
        if lbone.fixed_axis != QVector3D():
            # 軸固定の場合、回転を制限する
            rot = QQuaternion.fromAxisAndAngle(lbone.fixed_axis, rot.lengthSquared())
        add_qs[lidx] = rot

        # logger.info("trans_vs[%s]: %s", lidx, trans_vs[lidx])
        # logger.info("add_qs[%s]: %s", lidx, add_qs[lidx])

    # 行列
    matrixs = [QMatrix4x4() for i in range(len(links))]

    for n in range(len(matrixs)):
        # 行列を生成
        matrixs[n] = QMatrix4x4()
        # 移動
        matrixs[n].translate(trans_vs[n])
        # 回転
        matrixs[n].rotate(add_qs[n])
        
        # logger.info("matrixs n: %s, %s", n, matrixs[n])

    # 各関節の位置
    global_4ds = [QVector4D() for i in range(len(links))]
    
    for n in range(len(global_4ds)):
        for m in range(n):
            if m == 0:
                # 0番目の位置を初期値とする
                global_4ds[n] = copy.deepcopy(matrixs[0])
            else:
                # 自分より前の行列結果を掛け算する
                global_4ds[n] *= copy.deepcopy(matrixs[m])
        
        # 自分は、位置だけ掛ける
        global_4ds[n] *= QVector4D(trans_vs[n], 1)
        
        # logger.info("global_4ds %s, %s", n, global_4ds[n])
    
    return trans_vs, add_qs, matrixs, global_4ds


def adjust_center(trace_model, replace_model, bone_name):
    if bone_name in trace_model.bones and bone_name in replace_model.bones and "左足" in trace_model.bones and "左足" in replace_model.bones:
        # 移植元にも移植先にも対象ボーンがある場合
        # 左足付け根のY位置
        leg_y = trace_model.bones["左足"].position.y()
        # センター（もしくはグルーブ）のY位置
        center_y = trace_model.bones[bone_name].position.y()
        # 足のどの辺りにセンターがあるか判定
        ratio_y = center_y / leg_y
        
        # トレース元と同じ比率の位置にセンターを置く
        replace_model.bones[bone_name].len = replace_model.bones["左足"].position.y() * ratio_y

def compare_length(trace_model, replace_model):
    lengths = {}

    for k, v in replace_model.bones.items():
        # 移植先モデルのボーン構造チェック
        if k in trace_model.bones:
            # 同じ項目がトレース元にもある場合
            trace_bone_length = trace_model.bones[k].len
            replace_bone_length = replace_model.bones[k].len

            # 0割対策を入れて、倍率取得
            length = replace_bone_length if trace_bone_length == 0 else replace_bone_length / trace_bone_length

            # length.setX(length.x() if np.isnan(length.x()) == False and np.isinf(length.x()) == False else 0)
            # length.setY(length.y() if np.isnan(length.y()) == False and np.isinf(length.y()) == False else 0)
            # length.setZ(length.z() if np.isnan(length.z()) == False and np.isinf(length.z()) == False else 0)
            print("bone: %s, trace: %s, replace: %s, length: %s" % (k, trace_bone_length, replace_bone_length, length))

            lengths[k] = length
    
    return lengths



# 補間曲線を考慮した指定フレーム番号の位置
def calc_bone_by_complement(frames, bone_name, frameno):
    fillbf = VmdBoneFrame()

    # ボーン登録がなければ初期値
    if bone_name not in frames:
        return fillbf

    for bidx, bf in enumerate(frames[bone_name]):
        if bf.frame >= frameno:
            # 前のキーIDXを0に見立てて、その間の補間曲線を埋める
            fillbf.name = bf.name
            fillbf.frame = frameno
            # 実際に登録はしない
            fillbf.key = False

            # 指定されたフレーム以降
            prev_bf = frames[bone_name][bidx - 1]

            if prev_bf.rotation != bf.rotation:
                # 回転補間曲線
                rn = calc_interpolate_bezier(bf.complement[48], bf.complement[52], bf.complement[56], bf.complement[60], prev_bf.frame, bf.frame, fillbf.frame)
                fillbf.rotation = QQuaternion.nlerp(prev_bf.rotation, bf.rotation, rn)
                # logger.debug("key: %s, n: %s, rn: %s, r: %s ", k, prev_frame + n, rn, QQuaternion.nlerp(prev_bf.rotation, bf.rotation, rn) )
                # logger.debug("rotation: prev: %s, fill: %s ", prev_bf.rotation.toEulerAngles(), fillbf.rotation.toEulerAngles() )
            else:
                fillbf.rotation = prev_bf.rotation

            # 補間曲線を元に間を埋める
            if prev_bf.position != bf.position:
                # http://rantyen.blog.fc2.com/blog-entry-65.html
                # X移動補間曲線
                xn = calc_interpolate_bezier(bf.complement[0], bf.complement[4], bf.complement[8], bf.complement[12], prev_bf.frame, bf.frame, fillbf.frame)
                # Y移動補間曲線
                yn = calc_interpolate_bezier(bf.complement[16], bf.complement[20], bf.complement[24], bf.complement[28], prev_bf.frame, bf.frame, fillbf.frame)
                # Z移動補間曲線
                zn = calc_interpolate_bezier(bf.complement[32], bf.complement[36], bf.complement[40], bf.complement[44], prev_bf.frame, bf.frame, fillbf.frame)

                fillbf.position.setX(prev_bf.position.x() + (( bf.position.x() - prev_bf.position.x()) * xn))
                fillbf.position.setY(prev_bf.position.y() + (( bf.position.y() - prev_bf.position.y()) * yn))
                fillbf.position.setZ(prev_bf.position.z() + (( bf.position.z() - prev_bf.position.z()) * zn))
                # logger.debug("key: %s, n: %s, xn: %s, yn: %s, zn: %s, xa: %s", k, prev_frame + n, xn, yn, zn, ( bf.position.x() - prev_bf.position.x()) * xn )
                # logger.debug("position: prev: %s, fill: %s ", prev_bf.position, fillbf.position )
            else:
                fillbf.position = prev_bf.position
                # logger.debug("position stop: %s,%s prev: %s, fill: %s ", prev_frame + n, k, prev_bf.position, bf.position )

            return fillbf

    # 最後まで行っても見つからなければ、最終項目を返す
    return frames[bone_name][-1]


# 補間曲線を求める
# http://d.hatena.ne.jp/edvakf/20111016/1318716097
def calc_interpolate_bezier(x1v, y1v, x2v, y2v, start, end, now):
    x = (now - start) / (end - start)
    x1 = x1v / 127
    x2 = x2v / 127
    y1 = y1v / 127
    y2 = y2v / 127

    t = 0.5
    s = 0.5

    # logger.debug("x1: %s, x2: %s, y1: %s, y2: %s, x: %s", x1, x2, y1, y2, x)

    for i in range(15):
        ft = (3 * (s * s) * t * x1) + (3 * s * (t * t) * x2) + (t * t * t) - x
        # logger.debug("i: %s, 4 << i: %s, ft: %s(%s), t: %s, s: %s", i, (4 << i), ft, abs(ft) < 0.00001, t, s)

        if abs(ft) < 0.00001:
            break

        if ft > 0:
            t -= 1 / (4 << i)
        else:
            t += 1 / (4 << i)
        
        s = 1 - t

    y = (3 * (s * s) * t * y1) + (3 * s * (t * t) * y2) + (t * t * t)

    # logger.debug("y: %s, t: %s, s: %s", y, t, s)

    return y

if __name__=="__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--vmd_path', dest='vmd_path', help='input vmd', type=str)
    parser.add_argument('--trace_pmx_path', dest='trace_pmx_path', help='input trace pmx', type=str)
    parser.add_argument('--replace_pmx_path', dest='replace_pmx_path', help='replace trace pmx', type=str)
    parser.add_argument('--avoidance', dest='avoidance', help='upper hand avoidance', type=int)
    parser.add_argument('--verbose', dest='verbose', help='verbose', type=int)
    args = parser.parse_args()

    logger.setLevel(level[args.verbose])

    try:
        # VMD読み込み
        motion = VmdReader().read_vmd_file(args.vmd_path)

        # トレース元モデル
        logger.info("trace_pmx_path: %s", args.trace_pmx_path)
        org_pmx = PmxReader().read_pmx_file(args.trace_pmx_path)

        # 変換先モデル
        logger.info("replace_pmx_path: %s", args.replace_pmx_path)
        rep_pmx = PmxReader().read_pmx_file(args.replace_pmx_path)

        # 出力ファイルパス
        bone_filename, _ = os.path.splitext(os.path.basename(args.replace_pmx_path))
        output_vmd_path = os.path.join(str(Path(args.vmd_path).resolve().parents[0]), os.path.basename(args.vmd_path).replace(".vmd", "_{1}_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now(), bone_filename)))

        # 接触回避処理
        is_avoidance = True if args.avoidance == 1 else False

        main(motion, org_pmx, rep_pmx, output_vmd_path, is_avoidance) 

    except Exception as e:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMDサイジング処理が意図せぬエラーで終了しました。")
        print("■■■■■■■■■■■■■■■■■")

        print(traceback.format_exc())

