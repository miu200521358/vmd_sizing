# -*- coding: utf-8 -*-
# ユーティリティ系
# 
import re
import logging
import copy
from datetime import datetime
from math import atan2, acos, cos, sin, degrees, isnan, isclose, sqrt, pi, isinf
from PyQt5.QtGui import QQuaternion, QVector3D, QVector2D, QMatrix4x4, QVector4D

from VmdWriter import VmdWriter, VmdBoneFrame
from VmdReader import VmdReader
from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader

logger = logging.getLogger("VmdSizing").getChild(__name__)

# MMDでの補間曲線の最大値
COMPLEMENT_MMD_MAX = 127
is_print = False

loggers = {}

def sign(x):
    return (x > 0) - (x < 0)

def output_message(text, is_print=False):
    if is_print == True:
        print(text)
    else:
        pass

def create_custom_logger(name, handler):
    global loggers

    if loggers.get(name):
        logger.debug("loggerあり")
        new_logger = loggers.get(name)
    else:
        logger.debug("loggerなし")
        new_logger = logging.getLogger(name)
        new_logger.setLevel(logging.INFO)

        loggers[name] = new_logger
    
    for f in new_logger.handlers:
        # 既存のハンドラはすべて削除
        logger.debug("before f: %s", f)
        new_logger.removeHandler(f)
    
    # 指定されたハンドラを紐付ける
    new_logger.addHandler(handler)

    # for f in new_logger.handlers:
    #     logger.debug("after f: %s", f)
    
    return new_logger

# ログを生成する
def create_error_file_logger(motion, trace_model, replace_model, output_vmd_path):
    global loggers

    error_path = re.sub(r'\.vmd$', ".log", output_vmd_path)
    logger.debug("error_path: %s", error_path)
    error_file_handler = logging.FileHandler(error_path)

    error_file_logger = create_custom_logger("VmdSizingError", error_file_handler)
    error_file_logger.debug("モーション: %s" , motion.path)
    error_file_logger.debug("作成元: %s" , trace_model.path)
    error_file_logger.debug("変換先: %s" , replace_model.path)

    return error_file_logger

def close_error_file_logger(error_file_logger, error_file_handler):
    if error_file_logger:
        error_file_handler.close()
        error_file_logger.removeHandler(error_file_handler)
    error_file_logger = None

# 指定されたフレームより前のキーを返す
def get_prev_bf(frames, bone_name, frameno):
    for bidx, bf in enumerate(frames[bone_name]):
        if bf.frame >= frameno:
            # 指定されたフレーム以降の一つ前で、前のキーを取る
            return bidx, frames[bone_name][bidx - 1]

    # 最後まで取れなければ、最終項目
    return len(frames[bone_name]) - 1, frames[bone_name][-1]


# グローバル座標計算行列のための情報を生成する
def create_matrix_parts(model, links, frames, bf, scales):
    # ローカル位置
    trans_vs = [QVector3D() for i in range(len(links))]
    # 加算用クォータニオン
    add_qs = [QQuaternion() for i in range(len(links))]
    # 比率
    scale_l = [1 for i in range(len(links))]

    for lidx, lbone in enumerate(reversed(links)):
        comp_bone = calc_bone_by_complement(frames, lbone.name, bf.frame)

        # 位置
        if lidx == 0:
            # 一番親は、グローバル座標を考慮
            trans_vs[lidx] = lbone.position + comp_bone.position
        else:
            # 位置：自身から親の位置を引いた値
            trans_vs[lidx] = lbone.position + comp_bone.position - links[len(links) - lidx].position

        if bf.frame == 279:
            logger.debug("f: %s, lbone: %s, trans_vs: %s, comp_bone: %s", bf.frame, lbone.name, trans_vs[lidx], comp_bone.position)

        # 回転
        rot = comp_bone.rotation
        # rot.setX( rot.x() * -1 )
        # rot.setScalar( rot.scalar() * -1 )

        if lbone.fixed_axis != QVector3D():
            if 0 <= bf.frame <= 20:
                logger.debug("軸固定before: %s: %s  %s, fixed_axis:%s, rot: %s, euler: %s", bf.frame, model.name, lbone.name, lbone.fixed_axis, rot, rot.toEulerAngles())
                
            # 回転角度を求める
            if rot == QQuaternion():
                # 回転なしの場合、角度なし
                degree = 0
            else:
                # 回転補正
                if "右" in lbone.name and rot.x() > 0 and lbone.fixed_axis.x() <= 0:
                    rot.setX(rot.x() * -1)
                    # rot.setY(rot.y() * -1)
                    rot.setScalar(rot.scalar() * -1)
                    # rot.setZ(abs(rot.z()))
                elif "左" in lbone.name and rot.x() < 0 and lbone.fixed_axis.x() >= 0:
                    rot.setX(rot.x() * -1)
                    rot.setScalar(rot.scalar() * -1)
                    # rot.setX(rot.x() * -1)
                    # rot.setScalar(rot.scalar() * -1)
                # 回転補正（コロン式ミクさん等軸反転パターン）
                elif "右" in lbone.name and rot.x() < 0 and lbone.fixed_axis.x() > 0:
                    logger.debug("右回転補正")
                    rot.setX(rot.x() * -1)
                    # rot.setY(rot.y() * -1)
                    rot.setScalar(rot.scalar() * -1)
                    # rot.setZ(abs(rot.z()))
                elif "左" in lbone.name and rot.x() > 0 and lbone.fixed_axis.x() < 0:
                    logger.debug("左回転補正")
                    rot.setX(rot.x() * -1)
                    rot.setScalar(rot.scalar() * -1)
                    # rot.setX(rot.x() * -1)
                    # rot.setScalar(rot.scalar() * -1)
                
                rot.normalize()

                degree = degrees(2 * acos(rot.scalar()))

            if 0 <= bf.frame <= 20:
                logger.debug("軸固定after: %s: %s  %s, fixed_axis:%s, rot: %s, euler: %s, degree: %s", bf.frame, model.name, lbone.name, lbone.fixed_axis, rot, rot.toEulerAngles(), degree)
            
            # 軸固定の場合、回転を制限する
            rot = QQuaternion.fromAxisAndAngle(lbone.fixed_axis, degree)
        
        if lbone.getExternalRotationFlag() and lbone.effect_index in model.bone_indexes:
            # 付与回転ありの場合
            logger.debug("付与回転＋: %s: %s  %s, idx: %s(%s), fac: %s", bf.frame, model.name, lbone.name, lbone.effect_index, model.bone_indexes[lbone.effect_index], lbone.effect_factor)

            # 該当する付与親の回転を取得する
            effect_comp_bone = calc_bone_by_complement(frames, model.bone_indexes[lbone.effect_index], bf.frame)

            # 自身の回転量に付与親の回転量を付与率を加味して付与する
            rot = rot * effect_comp_bone.rotation
            rot.setX(rot.x() * lbone.effect_factor)
            rot.setY(rot.y() * lbone.effect_factor)
            rot.setZ(rot.z() * lbone.effect_factor)

            logger.debug("付与回転＋after: rot: %s: euler: %s", rot, rot.toEulerAngles())

        add_qs[lidx] = rot
    
        if 0 <= bf.frame <= 20:
            logger.debug("f: %s, m: %s, lbone: %s, rot: %s", bf.frame, model.name, lbone.name, rot.toEulerAngles())

        # 大きさ
        if scales is not None:
            for lkey, lval in scales.items():
                if lkey == lbone.name:
                    # 同じ名前がボーン比率リストにある場合採用(デフォルトで１なので、なければ１)
                    scale_l[lidx] = lval
                    # logger.debug("lidx: %s, lval: %s", lidx, lval)

    return trans_vs, add_qs, scale_l

# グローバル座標計算用行列生成
def create_matrix(model, links, frames, bf, scales=None):
    trans_vs, add_qs, scale_l = create_matrix_parts(model, links, frames, bf, scales)
    
    # 行列
    matrixs = [QMatrix4x4() for i in range(len(links))]

    for n, l in enumerate(reversed(links)):
        # 行列を生成
        matrixs[n] = QMatrix4x4()
        # 移動
        matrixs[n].translate(trans_vs[n])
        # 回転
        matrixs[n].rotate(add_qs[n])
        # # スケール
        # matrixs[n].scale(scale_l[n])

        if 260 <= bf.frame <= 270:
            logger.debug("n: %s, l: %s, trans_vs[n]: %s", n, l.name, trans_vs[n])
            logger.debug("n: %s, l: %s, add_qs[n]: %s", n, l.name, add_qs[n].toEulerAngles())
        
        # if scale_l[n] != 1:
        #     logger.debug("matrixs n: %s, l: %s, s: %s, %s", n, l.name, scale_l[n], matrixs[n])
    
    return trans_vs, add_qs, scale_l, matrixs

def split_qq(model, links, frames, bf, bone_name, min_qq, max_qq, parent_qq, scales=None):
    trans_vs, add_qs, scale_l = create_matrix_parts(model, links, frames, bf, scales)
    
    chicl_qq = QQuaternion()
    remaining_qq = QQuaternion()

    # 親の回転から捩り分を抽出
    

    parent_euler = parent_qq.toEulerAngles()
    if parent_euler.x() > 45:
        chicl_qq = QQuaternion.fromEulerAngles(parent_euler.x() - 45, 0, 0)
    elif parent_euler.x() < -45:
        chicl_qq = QQuaternion.fromEulerAngles(360 - abs(parent_euler.x() + 45), 0, 0)
    
    total_add_qs = QQuaternion()
    for e, q in enumerate(add_qs):
        if e == 0:
            total_add_qs = copy.deepcopy(q)
        else:
            total_add_qs *= copy.deepcopy(q)
    
    total_add_qs *= chicl_qq

    degree = degrees(2 * acos(total_add_qs.scalar()))

    # 軸固定の場合、回転を制限する
    result_qq = QQuaternion.fromAxisAndAngle(links[0].fixed_axis, degree)

    # 残りは捩り分を除いて再設定
    remaining_qq = parent_qq * result_qq.inverted()
     
    return result_qq, remaining_qq

# グローバル座標リスト生成
def create_matrix_global(model, links, frames, bf, scales=None):
    trans_vs, add_qs, scale_l, matrixs = create_matrix(model, links, frames, bf, scales)

    # 各関節の位置
    global_4ds = [QVector4D() for i in range(len(links))]

    global_3ds = [QVector3D() for i in range(len(links))]
    
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

        global_3ds[n] = global_4ds[n].toVector3D()

        # if 260 <= bf.frame <= 270:
            # logger.debug("global_4ds %s, %s, %s", n, links[len(links) - n - 1].name, global_4ds[n].toVector3D())
    
    return trans_vs, add_qs, scale_l, matrixs, global_3ds

# 指定されたボーンの先の位置を取得する
def create_matrix_global_tail(model, links, frames, bf, scales=None):
    if links[0].name not in model.bones:
        # 末端を除いたリンクでグローバル位置を生成
        trans_vs, add_qs, scale_l, matrixs, global_3ds = create_matrix_global(model, links[1:], frames, bf, scales)

        # 現時点の上半身までの回転量
        direction_qq = QQuaternion()
        for aq, l in zip(add_qs, reversed(links)):
            direction_qq *= aq
            if l.name == "上半身":
                break

        to_global_3ds = copy.deepcopy(global_3ds)

        # 末端直前のグローバル位置を正面向きで取得
        mat = QMatrix4x4()
        mat.rotate(direction_qq.inverted())
        to_end_fornt_pos = mat.mapVector(to_global_3ds[-1])

        # 末端位置を生成
        tail_pos, _ = calc_tail_pos(model, links[1].name)
        tail_front_pos = to_end_fornt_pos + tail_pos

        # 末端位置を元に戻す
        mat = QMatrix4x4()
        mat.rotate(direction_qq)
        to_end_pos = mat.mapVector(tail_front_pos)

        # グローバル位置に追加
        to_global_3ds.append(to_end_pos)
    else:
        # 末端ボーンがある場合、そのまま取得
        trans_vs, add_qs, scale_l, matrixs, global_3ds = create_matrix_global(model, links, frames, bf, scales)
        to_global_3ds = copy.deepcopy(global_3ds)

    return trans_vs, add_qs, scale_l, matrixs, global_3ds, to_global_3ds


# 指定されたボーンの先を取得する
def calc_tail_pos(model, fbone):
    from_pos = QVector3D()
    tail_pos = QVector3D()
    to_pos = QVector3D()

    if fbone in model.bones:
        fv = model.bones[fbone]
        from_pos = fv.position
        if fv.tail_position != QVector3D():
            # 表示先が相対パスの場合、保持
            tail_pos = fv.tail_position
            to_pos = from_pos + tail_pos
        elif fv.tail_index >= 0:
            to_pos = model.bones[model.bone_indexes[fv.tail_index]].position
            tail_pos = to_pos - from_pos
    
    return tail_pos, to_pos



# 現在向いている回転量を取得する
def calc_upper_direction_qq(model, links, frames, bf):
    # 合計クォータニオン
    total_qq = QQuaternion()

    for lidx, lbone in enumerate(reversed(links)):
        # 回転
        rot = calc_bone_by_complement(frames, lbone.name, bf.frame).rotation
        if lbone.fixed_axis != QVector3D():
            # 回転角度を求める
            if rot == QQuaternion():
                # 回転なしの場合、角度なし
                degree = 0
            else:
                # 回転補正
                if "右" in lbone.name and rot.x() > 0 and lbone.fixed_axis.x() <= 0:
                    rot.setX(rot.x() * -1)
                    # rot.setY(rot.y() * -1)
                    rot.setScalar(rot.scalar() * -1)
                    # rot.setZ(abs(rot.z()))
                elif "左" in lbone.name and rot.x() < 0 and lbone.fixed_axis.x() >= 0:
                    rot.setX(rot.x() * -1)
                    rot.setScalar(rot.scalar() * -1)
                    # rot.setX(rot.x() * -1)
                    # rot.setScalar(rot.scalar() * -1)
                # 回転補正（コロン式ミクさん等軸反転パターン）
                elif "右" in lbone.name and rot.x() < 0 and lbone.fixed_axis.x() > 0:
                    logger.debug("右回転補正")
                    rot.setX(rot.x() * -1)
                    # rot.setY(rot.y() * -1)
                    rot.setScalar(rot.scalar() * -1)
                    # rot.setZ(abs(rot.z()))
                elif "左" in lbone.name and rot.x() > 0 and lbone.fixed_axis.x() < 0:
                    logger.debug("左回転補正")
                    rot.setX(rot.x() * -1)
                    rot.setScalar(rot.scalar() * -1)
                    # rot.setX(rot.x() * -1)
                    # rot.setScalar(rot.scalar() * -1)
                
                rot.normalize()

                degree = degrees(2 * acos(rot.scalar()))
            
            # 軸固定の場合、回転を制限する
            rot = QQuaternion.fromAxisAndAngle(lbone.fixed_axis, degree)
    
        logger.debug("lbone: %s, rot: %s", lbone.name, rot.toEulerAngles())

        total_qq *= rot

    # XYZ全方向の回転を参照するため、そのまま返す
    return total_qq





# 回転補間曲線のインデックス
R_x1_idxs = [3, 18, 33, 48]
R_y1_idxs = [7, 22, 37, 52]
R_x2_idxs = [11, 26, 41, 56]
R_y2_idxs = [15, 30, 45, 60]

# X移動補間曲線のインデックス
MX_x1_idxs = [0, 0, 0, 0]
MX_y1_idxs = [4, 19, 34, 49]
MX_x2_idxs = [8, 23, 38, 53]
MX_y2_idxs = [12, 27, 42, 57]

# Y移動補間曲線のインデックス
MY_x1_idxs = [1, 16, 16, 16]
MY_y1_idxs = [5, 20, 36, 50]
MY_x2_idxs = [9, 24, 39, 54]
MY_y2_idxs = [13, 28, 43, 58]

# Z移動補間曲線のインデックス
MZ_x1_idxs = [2, 17, 33, 32]
MZ_y1_idxs = [6, 21, 36, 51]
MZ_x2_idxs = [10, 25, 40, 55]
MZ_y2_idxs = [14, 29, 44, 59]


# 補間曲線を考慮した指定フレーム番号の位置
# https://www55.atwiki.jp/kumiho_k/pages/15.html
# https://harigane.at.webry.info/201103/article_1.html
def calc_bone_by_complement(frames, bone_name, frameno, is_calc_complement=False, is_read=False):
    fillbf = VmdBoneFrame()

    # ボーン登録がなければ初期値
    if bone_name not in frames:
        fillbf.name = bone_name.encode('cp932').decode('shift_jis').encode('shift_jis')
        fillbf.format_name = bone_name
        fillbf.frame = frameno
        return fillbf

    prev_bf = None

    for bidx, bf in enumerate(frames[bone_name]):
        if bf.frame == frameno:
            # 同一フレームのキーがある場合、それを返す
            fillbf = copy.deepcopy(bf)
            if frameno == 5217:
                logger.debug("calc_bone_by_complement 同一キーあり: %s, %s, read: %s", frameno, bone_name, fillbf.read)
            return fillbf
        elif (not is_calc_complement and bf.frame > frameno) or (is_calc_complement and bf.frame > frameno and bf.read):
            # 同一フレームのキーがなく、読み込みキーのみ欲しい場合、前のキーを返す
            if is_read and bidx > 0:
                return copy.deepcopy(frames[bone_name][bidx - 1])

            # 補間曲線の再計算がない場合、そのまま次の。再計算ありの場合、読み込みキーのみチェック対象とする
            # 同一フレームのキーがない場合、挿入
            fillbf.name = bf.name
            fillbf.format_name = bone_name
            fillbf.frame = frameno
            # 実際に登録はしない
            fillbf.key = False
            # 読み込みキーではない
            fillbf.read = False

            if frameno == 5217:
                logger.debug("calc_bone_by_complement 同一キーなし: %s, %s, read: %s", frameno, bone_name, fillbf.read)

            if is_calc_complement:
                # 補間曲線の計算し直しの場合

                # 前の読み込んだキー
                for pbf_idx in range(bidx - 1, -1, -1):
                    if frames[bone_name][pbf_idx].read == True:
                        prev_bf = frames[bone_name][pbf_idx]
                        break
                
                if not prev_bf:
                    # 前キーが取れなかった場合、暫定的に現在フレームの値を保持する
                    prev_bf = copy.deepcopy(bf)
                
                # 処理対象補間曲線（処理前の補間曲線）
                comp = bf.org_complement
                # 処理対象前回転
                prev_rot = prev_bf.org_rotation
                # 処理対象回転
                rot = bf.org_rotation
                # 処理対象前移動(センター等の移動は既に修正されているので、orgじゃなく自身の値)
                prev_pos = prev_bf.position
                # 処理対象移動
                pos = bf.position
            else:
                # 補間曲線は弄らない場合
                
                if bidx <= 0:
                    # 前キーが取れない場合、暫定的に現在フレームの値を保持する
                    prev_bf = copy.deepcopy(bf)
                else:
                    # 指定されたフレーム直前のキー
                    prev_bf = frames[bone_name][bidx - 1]

                # 処理対象補間曲線
                comp = bf.complement
                # 処理対象前回転
                prev_rot = prev_bf.rotation
                # 処理対象回転
                rot = bf.rotation
                # 処理対象前移動
                prev_pos = prev_bf.position
                # 処理対象移動
                pos = bf.position

            logger.debug("bone_name: %s, bf: %s, bidx: %s", bone_name, bf.frame, bidx)

            if prev_rot != rot:
                # 回転補間曲線
                _, _, rn = calc_interpolate_bezier(comp[R_x1_idxs[3]], comp[R_y1_idxs[3]], comp[R_x2_idxs[3]], comp[R_y2_idxs[3]], prev_bf.frame, bf.frame, fillbf.frame)
                fillbf.rotation = QQuaternion.slerp(prev_rot, rot, rn)

                # if 1070 <= fillbf.frame <= 1090:
                logger.debug(", f: %s, k: %s, rn: %s, r: %s ", frameno, bone_name, rn, fillbf.rotation.toEulerAngles() )
                logger.debug(", rotation: prev: %s, bf: %s ", prev_rot.toEulerAngles(), rot.toEulerAngles() )
            else:
                fillbf.rotation = copy.deepcopy(prev_rot)

            # 補間曲線を元に間を埋める
            if prev_pos != pos:
                # http://rantyen.blog.fc2.com/blog-entry-65.html
                # X移動補間曲線
                _, _, xn = calc_interpolate_bezier(comp[0], comp[4], comp[8], comp[12], prev_bf.frame, bf.frame, fillbf.frame)
                # Y移動補間曲線
                _, _, yn = calc_interpolate_bezier(comp[16], comp[20], comp[24], comp[28], prev_bf.frame, bf.frame, fillbf.frame)
                # Z移動補間曲線
                _, _, zn = calc_interpolate_bezier(comp[32], comp[36], comp[40], comp[44], prev_bf.frame, bf.frame, fillbf.frame)

                fillbf.position.setX(prev_pos.x() + (( pos.x() - prev_pos.x()) * xn))
                fillbf.position.setY(prev_pos.y() + (( pos.y() - prev_pos.y()) * yn))
                fillbf.position.setZ(prev_pos.z() + (( pos.z() - prev_pos.z()) * zn))
                # logger.debug("key: %s, n: %s, xn: %s, yn: %s, zn: %s, xa: %s", k, prev_frame + n, xn, yn, zn, ( pos.x() - prev_pos.x()) * xn )
                # logger.debug("position: prev: %s, fill: %s ", prev_pos, fillbf.position )
            else:
                fillbf.position = copy.deepcopy(prev_pos)
                # logger.debug("position stop: %s,%s prev: %s, fill: %s ", prev_frame + n, k, prev_pos, pos )
            
            return fillbf

    logger.debug("calc_bone_by_complement 見つからなかった: %s, %s", frameno, bone_name)

    # 最後まで行っても見つからなければ、最終項目を該当フレーム用に設定して返す
    fillbf = copy.deepcopy(frames[bone_name][-1])
    fillbf.name = bone_name.encode('cp932').decode('shift_jis').encode('shift_jis')
    fillbf.format_name = bone_name
    fillbf.frame = frameno
    return fillbf


# 3次ベジェ曲線の分割
# http://geom.web.fc2.com/geometry/bezier/cut-cb.html
def calc_bezier_split(x1v, y1v, x2v, y2v, start, end, now, bone_name):
    if (now - start) == 0 or (end - start) == 0:
        return 0, 0, 0, False, False, [QVector2D(),QVector2D(),QVector2D(),QVector2D()], [QVector2D(),QVector2D(),QVector2D(),QVector2D()]

    # 3次ベジェ曲線を分割する
    t, x, y, beforebz, afterbz = calc_bezier_split_offset(x1v, y1v, x2v, y2v, start, end, now, bone_name)

    # ベジェ曲線の値がMMD用に合っているかを加味して返す
    return t, x, y, is_fit_bezier_mmd(beforebz), is_fit_bezier_mmd(afterbz), beforebz, afterbz


# ベジェ曲線の値がMMD用に合っているか
def is_fit_bezier_mmd(bz, offset=0):
    for b in bz:
        # # 1割以下は誤差として吸収してしまう
        # b.setX( 0 if COMPLEMENT_MMD_MAX-1 <= b.x() < 0 else b.x() )
        # b.setY( COMPLEMENT_MMD_MAX if COMPLEMENT_MMD_MAX < b.x() <= COMPLEMENT_MMD_MAX+1 else b.y() )

        if not (0 - offset <= b.x() <= COMPLEMENT_MMD_MAX + offset) or not (0 - offset <= b.y() <= COMPLEMENT_MMD_MAX + offset):
            # MMD用の範囲内でなければNG
            return False

    return True

def fit_bezier_mmd(b):
    if not (0 <= b.x() <= COMPLEMENT_MMD_MAX) or not (0 <= b.y() <= COMPLEMENT_MMD_MAX):
        x = 0 if 0 > b.x() else COMPLEMENT_MMD_MAX if COMPLEMENT_MMD_MAX < b.x() else int(b.x())
        y = 0 if 0 > b.y() else COMPLEMENT_MMD_MAX if COMPLEMENT_MMD_MAX < b.y() else int(b.y())

        return int(x), int(y)

    return int(b.x()), int(b.y())

# オフセット込みの3次ベジェ曲線の分割
def calc_bezier_split_offset(x1v, y1v, x2v, y2v, start, end, now, bone_name):
    # 補間曲線の進んだ時間分を求める
    t, x, y = calc_interpolate_bezier(x1v, y1v, x2v, y2v, start, end, now)

    A = QVector2D(0.0, 0.0)
    B = QVector2D(x1v/COMPLEMENT_MMD_MAX, y1v/COMPLEMENT_MMD_MAX)
    C = QVector2D(x2v/COMPLEMENT_MMD_MAX, y2v/COMPLEMENT_MMD_MAX)
    D = QVector2D(1.0, 1.0)

    E = (1-t)*A + t*B
    F = (1-t)*B + t*C
    G = (1-t)*C + t*D
    H = (1-t)*E + t*F
    I = (1-t)*F + t*G
    J = (1-t)*H + t*I

    # 新たな4つのベジェ曲線の制御点は、A側がAEHJ、C側がJIGDとなる。

    # スケーリング
    bA, bE, bH, bJ = scale_bezier(A, E, H, J)
    aJ, aI, aG, aD = scale_bezier(J, I, G, D)

    bA2 = round_bezier_mmd(bA)
    bE2 = round_bezier_mmd(bE)
    bH2 = round_bezier_mmd(bH)
    bJ2 = round_bezier_mmd(bJ)
    aJ2 = round_bezier_mmd(aJ)
    aI2 = round_bezier_mmd(aI)
    aG2 = round_bezier_mmd(aG)
    aD2 = round_bezier_mmd(aD)

    logger.debug("bone_name,start,now,end,t,x1v,y1v,x2v,y2v,A.x(),A.y(),B.x(),B.y(),C.x(),C.y(),D.x(),D.y(),E.x(),E.y(),F.x(),F.y(),G.x(),G.y(),H.x(),H.y(),I.x(),I.y(),J.x(),J.y(),bA.x(),bA.y(),bE.x(),bE.y(),bH.x(),bH.y(),bJ.x(),bJ.y(),aJ.x(),aJ.y(),aI.x(),aI.y(),aG.x(), aG.y(),aD.x(),aD.y() ,bA2.x(),bA2.y(),bE2.x(),bE2.y(),bH2.x(),bH2.y(),bJ2.x(),bJ2.y(),aJ2.x(),aJ2.y(),aI2.x(),aI2.y(),aG2.x(),aG2.y(),aD2.x(),aD2.y()")    
    logger.debug("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s", bone_name,start,now,end,t,x1v,y1v,x2v,y2v,A.x(),A.y(),B.x(),B.y(),C.x(),C.y(),D.x(),D.y(),E.x(),E.y(),F.x(),F.y(),G.x(),G.y(),H.x(),H.y(),I.x(),I.y(),J.x(),J.y(),bA.x(),bA.y(),bE.x(),bE.y(),bH.x(),bH.y(),bJ.x(),bJ.y(),aJ.x(),aJ.y(),aI.x(),aI.y(),aG.x(), aG.y(),aD.x(),aD.y() ,bA2.x(),bA2.y(),bE2.x(),bE2.y(),bH2.x(),bH2.y(),bJ2.x(),bJ2.y(),aJ2.x(),aJ2.y(),aI2.x(),aI2.y(),aG2.x(),aG2.y(),aD2.x(),aD2.y())

    return t, x, y, [bA2, bE2, bH2, bJ2], [aJ2, aI2, aG2, aD2]

# 分割したベジェのスケーリング
def scale_bezier(p1, p2, p3, p4):
    diff = p4 - p1

    # nan対策
    s1 = scale_bezier_point(p1, p1, diff)
    s2 = scale_bezier_point(p2, p1, diff)
    s3 = scale_bezier_point(p3, p1, diff)
    s4 = scale_bezier_point(p4, p1, diff)

    return s1, s2, s3, s4

# nan対策を加味したベジェ曲線の点算出
def scale_bezier_point(pn, p1, diff):
    s = (pn-p1) / diff

    # logger.debug("diff: %s", diff)
    # logger.debug("(pn-p1): %s", (pn-p1))
    # logger.debug("s: %s", s)

    # nanになったら0決め打ち
    s.setX(get_effective_value(s.x()))
    s.setY(get_effective_value(s.y()))

    return s

def get_effective_value(v):
    if isnan(v):
        return 0
    
    if isinf(v):
        return 0
    
    return v


def set_effective_value_vec3(vec3):
    vec3.setX(get_effective_value(vec3.x()))
    vec3.setY(get_effective_value(vec3.y()))
    vec3.setZ(get_effective_value(vec3.z()))


# ベジェ曲線をMMD用の数値に丸める
def round_bezier_mmd(target):
    t2 = QVector2D()

    # XとYをそれぞれ整数(0-127)に丸める
    t2.setX(round_integer(target.x() * COMPLEMENT_MMD_MAX))
    t2.setY(round_integer(target.y() * COMPLEMENT_MMD_MAX))

    return t2

def round_integer(t):
    # 一旦整数部にまで持ち上げる
    t2 = t * 1000000
    
    # pythonは偶数丸めなので、整数部で丸めた後、元に戻す
    return round(round(t2, -6) / 1000000)


# 補間曲線を求める
# http://d.hatena.ne.jp/edvakf/20111016/1318716097
# https://pomax.github.io/bezierinfo
# https://shspage.hatenadiary.org/entry/20140625/1403702735
def calc_interpolate_bezier(x1v, y1v, x2v, y2v, start, end, now):
    if (now - start) == 0 or (end - start) == 0:
        return 0, 0, 0
        
    x = (now - start) / (end - start)
    x1 = x1v / COMPLEMENT_MMD_MAX
    x2 = x2v / COMPLEMENT_MMD_MAX
    y1 = y1v / COMPLEMENT_MMD_MAX
    y2 = y2v / COMPLEMENT_MMD_MAX

    t = 0.5
    s = 0.5

    # logger.debug("x1: %s, x2: %s, y1: %s, y2: %s, x: %s", x1, x2, y1, y2, x)

    for i in range(15):
        ft = (3 * (s * s) * t * x1) + (3 * s * (t * t) * x2) + (t * t * t) - x
        # logger.debug("i: %s, 4 << i: %s, ft: %s(%s), t: %s, s: %s", i, (4 << i), ft, abs(ft) < 0.00001, t, s)

        # lessさんのご指摘によりコメントアウト
        # if abs(ft) < 0.00001:
        #     break

        if ft > 0:
            t -= 1 / (4 << i)
        else:
            t += 1 / (4 << i)
        
        s = 1 - t

    y = (3 * (s * s) * t * y1) + (3 * s * (t * t) * y2) + (t * t * t)

    # logger.debug("y: %s, t: %s, s: %s", y, t, s)

    return t, x, y

# 指定されたtに相当するx(フレーム番号)とy(0-1)を返す
def calc_interpolate_bezier_by_t(x1v, y1v, x2v, y2v, start, end, t):
    x1 = x1v / COMPLEMENT_MMD_MAX
    x2 = x2v / COMPLEMENT_MMD_MAX
    y1 = y1v / COMPLEMENT_MMD_MAX
    y2 = y2v / COMPLEMENT_MMD_MAX

    s = 1 - t 

    x = (3 * (s * s) * t * x1) + (3 * s * (t * t) * x2) + (t * t * t)
    y = (3 * (s * s) * t * y1) + (3 * s * (t * t) * y2) + (t * t * t)

    # 開始から終了までの区間に広げる(yは広げない？)
    x2 = start + ((end - start) * x)

    # 整数に丸める
    x3 = round_integer(x2)

    # 開始と被ってたらずらす
    x3 = start + 1 if x3 == start else x3

    # 終了と被ってたらずらす
    x3 = end - 1 if x3 == end else x3

    logger.debug(",calc_interpolate_bezier_by_t,x1v,%s, y1v,%s, x2v,%s, y2v,%s, y,%s,x,%s,t,%s,x2,%s,x3,%s",x1v, y1v, x2v, y2v, y, x, t,x2,x3)

    return x3, x, y

# 指定された3点を通るベジェ曲線を返す
def calc_smooth_bezier(x1, y1, x2, y2, x3, y3):
    t = (x2 - x1) / (x3 - x1)

    if (x1 >= x2 or x1 >= x3 or x2 >= x3) or t <= 0 or t >= 1:
        # 正常に計算できない場合、計算対象外
        return False, False, \
            [QVector2D(0, 0), QVector2D(20, 20), QVector2D(107, 107), QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)]

    # if (y1 == y2 == y3): # or (y1 / x1 == y2 / x2 == y3 / x3):
    #     # 値の変化がない場合、線形補間
    #     return True, [QVector2D(0, 0), QVector2D(20, 20), QVector2D(107, 107), QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)], \
    #         [QVector2D(0, 0), QVector2D(20, 20), QVector2D(107, 107), QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)], \
    #         [QVector2D(0, 0), QVector2D(20, 20), QVector2D(107, 107), QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)]

    # 3点を通る二次曲線
    a, b, c = calc_quadratic_param(x1, y1, x2, y2, x3, y3)
    output_message("calc_smooth_bezier calc_quadratic_param finish now: %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), is_print)

    if a == 0:
        # 曲線がなく、等間隔に変化する場合、線形補間(補間曲線は設定する)
        return True, True, \
            [QVector2D(0, 0), QVector2D(20, 20), QVector2D(107, 107), QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)]

    
    # 開始フレームと中間フレームの交点
    cx1, cy1 = calc_quadratic_cross(a, b, c, x1, y1, x2, y2)

    # 中間フレームと終点フレームの交点
    cx2, cy2 = calc_quadratic_cross(a, b, c, x2, y2, x3, y3)

    # 中間フレームで繋いだ開始フレームと終端フレームの三次ベジェ曲線
    bz = calc_cubic_bezier_4point(x1, y1, cx1, cy1, cx2, cy2, x3, y3, (x2 - x1) / (x3 - x1))

    return True, is_fit_bezier_mmd(bz), bz

    # # # 始点と終点のベジェ曲線
    # # bz = calc_bezier_by_cross(x1, y1, cx1, cy1, x2, y2, cx2, cy2, x3, y3)

    # # 中間点で分割する
    # t, x, y, bresult, aresult, before_bz, after_bz = calc_bezier_split(bz[1].x(), bz[1].y(), bz[2].x(), bz[2].y(), x1, x3, x2, "")

    # return True, bresult and aresult, [before_bz[0], before_bz[1], after_bz[2], after_bz[3]]

# http://apoorvaj.io/cubic-bezier-through-four-points.html
def calc_cubic_bezier_4point(x1, y1, cx1, cy1, cx2, cy2, x3, y3, alpha):

    passthru_0 = QVector2D(x1, y1)
    passthru_1 = QVector2D(cx1, cy1)
    passthru_2 = QVector2D(cx2, cy2)
    passthru_3 = QVector2D(x3, y3)

    out_tangent_1 = QVector2D()
    out_tangent_2 = QVector2D()

    d1 = pow(calc_cubic_bezier_4point_vec2_dist(passthru_1, passthru_0), alpha)
    d2 = pow(calc_cubic_bezier_4point_vec2_dist(passthru_2, passthru_1), alpha)
    d3 = pow(calc_cubic_bezier_4point_vec2_dist(passthru_3, passthru_2), alpha)

    # Modify tangent 1 ------------
    a = d1 * d1
    b = d2 * d2
    c = (2 * d1 * d1) + (3 * d1 * d2) + (d2 * d2)
    d = 3 * d1 * (d1 + d2)

    out_tangent_1.setX((a * passthru_2.x() - b * passthru_0.x() + c * passthru_1.x()) / d)
    out_tangent_1.setY((a * passthru_2.y() - b * passthru_0.y() + c * passthru_1.y()) / d)

    # Modify tangent 2 ------------
    a = d3 * d3
    b = d2 * d2
    c = (2 * d3 * d3) + (3 * d3 * d2) + (d2 * d2)
    d = 3 * d3 * (d3 + d2)

    out_tangent_2.setX((a * passthru_1.x() - b * passthru_3.x() + c * passthru_2.x()) / d)
    out_tangent_2.setY((a * passthru_1.y() - b * passthru_3.y() + c * passthru_2.y()) / d)

    # スケーリング
    A = passthru_0
    B = out_tangent_1
    C = out_tangent_2
    D = passthru_3

    # スケーリング
    bA, bB, bC, bD = scale_bezier(A, B, C, D)

    cA = round_bezier_mmd(bA)
    cB = round_bezier_mmd(bB)
    cC = round_bezier_mmd(bC)
    cD = round_bezier_mmd(bD)

    return [cA, cB, cC, cD]

def calc_cubic_bezier_4point_vec2_dist(a, b):
    return sqrt((a.x() - b.x()) * (a.x() - b.x()) + (a.y() - b.y()) * (a.y() - b.y()))

# # 2つの二次ベジェ曲線を繋ぐ
# # https://nowokay.hatenablog.com/entry/20070623/1182556929
# def calc_bezier_concat2(bz2a, bz2b):
# # 中間フレームが0となるようにベジェ曲線を繋ぐ
# A = bz2a[0]
# B = QVector2D(bz2a[1].x(), bz2a[1].y() + COMPLEMENT_MMD_MAX)
# C = QVector2D(bz2b[1].x() + COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX) + bz2b[1]
# D = QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX) + bz2b[2]

# # スケーリング
# bA, bB, bC, bD = scale_bezier(A, B, C, D)

# cA = round_bezier_mmd(bA)
# cB = round_bezier_mmd(bB)
# cC = round_bezier_mmd(bC)
# cD = round_bezier_mmd(bD)

# return [cA, cB, cC, cD]

# # 二次ベジェ曲線を返す
# # https://stackoverflow.com/questions/6711707/draw-a-quadratic-b%C3%A9zier-curve-through-three-given-points
# def calc_bezier_by2(x1, y1, cx1, cy1, x2, y2):
#     A = QVector2D(x1, y1)
#     B = QVector2D(cx1, cy1)
#     C = QVector2D(x2, y2)

#     P = A*t^2 + B*2*t*(1-t) + C*(1-t)^2

#     # スケーリング
#     diff = C - A

#     # nan対策
#     bA = scale_bezier_point(A, A, diff)
#     bB = scale_bezier_point(B, A, diff)
#     bC = scale_bezier_point(C, A, diff)

#     # MMD用に纏める
#     cA = round_bezier_mmd(bA)
#     cB = round_bezier_mmd(bB)
#     cC = round_bezier_mmd(bC)

#     return [cA, cB, cC]

# # 3点と交点(制御点)から、二次のベジェ曲線の制御点を返す
# def calc_bezier_by_cross(x1, y1, cx1, cy1, x2, y2, cx2, cy2, x3, y3):
#     A = QVector2D(x1, y1)
#     B = QVector2D(cx1, cy1)
#     C = QVector2D(cx2, cy2)
#     D = QVector2D(x3, y3)
    
#     # スケーリング
#     bA, bB, bC, bD = scale_bezier(A, B, C, D)

#     cA = round_bezier_mmd(bA)
#     cB = round_bezier_mmd(bB)
#     cC = round_bezier_mmd(bC)
#     cD = round_bezier_mmd(bD)

#     return [cA, cB, cC, cD]

    # max_y = max(abs(y1), abs(y2), abs(y3))

    # # 前半制御点
    # bx = cx1 / x3
    # by = cy1 / max_y

    # bxv = round_integer(bx * COMPLEMENT_MMD_MAX)
    # byv = round_integer(by * COMPLEMENT_MMD_MAX)

    # # 後半制御点
    # ax = cx2 / x3
    # ay = cy2 / max_y

    # axv = round_integer(ax * COMPLEMENT_MMD_MAX)
    # ayv = round_integer(ay * COMPLEMENT_MMD_MAX)

    # return [QVector2D(0, 0), QVector2D(bxv, byv), QVector2D(axv, ayv), QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)]

# #2点と交点(制御点)から、二次のベジェ曲線の制御点を返す
# def calc_bezier_control_point(x1, y1, cx1, cy1, x2, y2, x3, y3, is_reverse):
#     # 制御点を、1～2の割合で取る
#     fxv = cx1 * ((x2 - x1) / (x3 - x1))
#     fyv = cy1 * ((y2 - y1) / (y3 - y1))

#     bxv = round_integer(fxv * COMPLEMENT_MMD_MAX)
#     byv = round_integer(fyv * COMPLEMENT_MMD_MAX)

#     if is_reverse:
#         bxv = COMPLEMENT_MMD_MAX - bxv

#     return QVector2D(bxv, byv)


# def calc_bezier_split_by_cross2(x1, y1, cx1, cy1, cx2, cy2, x2, y2, t):

#     # まず、補間曲線を求める
#     beforebz, afterbz = calc_bezier_split_simple(x1, y1, cx1, cy1, cx2, cy2, x2, y2, t)
    
#     # # 補間曲線がMMD範囲内か調べる
#     # if not is_fit_bezier_mmd(beforebz):
#     #     # MMD範囲内ではない場合、ゆがめて納める
#     #     beforebz = fit_bezier_split(beforebz)

#     # if not is_fit_bezier_mmd(afterbz):
#     #     # MMD範囲内ではない場合、ゆがめて納める
#     #     afterbz = fit_bezier_split(afterbz)
    
#     return beforebz, afterbz

# # https://seizan.blog.ss-blog.jp/2011-11-06
# # ラグランジェ補間で4点を通る3次ベジェ曲線のx時点のY値を返す
# def lagrange_interpolation(t, x1, y1, x2, y2, x3, y3, x4, y4):
#     size = (x4 - x1)
#     x1v = x1 / size
#     x2v = x2 / size
#     x3v = x3 / size
#     x4v = x4 / size
#     y1v = y1 / size
#     y2v = y2 / size
#     y3v = y3 / size
#     y4v = y4 / size

#     y = y4v*(t-x1v/(x4v-x1v) * (t-x2v/(x4v-x2v) * (t-x3v/(x4v-x3v) \
#         + y1v*(t-x2v/(x1v-x2v) * (t-x3v/(x1v-x3v) * (t-x4v/(x1v-x4v) \
#         + y2v*(t-x2v/(x2v-x3v) * (t-x4v/(x2v-x4v) * (t-x1v/(x2v-x1v) \
#         + y3v*(t-x2v/(x3v-x4v) * (t-x1v/(x3v-x1v) * (t-x2v/(x3v-x2v) 

#     return y

# def fit_bezier_split_mmd(org_bz):
#     bz1 = QVector2D(0, 0)
#     bz2 = org_bz[1]
#     bz3 = org_bz[2]
#     bz4 = QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)

#     if bz2.y() != 0 and bz2.x() / bz2.y() == 1:
#         bz2.setX(20)
#         bz2.setY(20)

#     if bz3.y() != 0 and bz3.x() / bz3.y() == 1:
#         bz3.setX(107)
#         bz3.setY(107)

#     if not is_fit_bezier_mmd([bz1, bz2, bz3, bz4]):
#         bz1 = fit_bezier_split(bz1)
#         bz2 = fit_bezier_split(bz2)
#         bz3 = fit_bezier_split(bz3)
#         bz4 = fit_bezier_split(bz4)

#     bz = [bz1, bz2, bz3, bz4]

#     return bz

# # 補間曲線が合わない場合、無理矢理に合わせる
# def fit_bezier_split(xy):
#     if xy.x() < 0:
#         xy.setX(0)
#     elif xy.x() > COMPLEMENT_MMD_MAX:
#         xy.setX(COMPLEMENT_MMD_MAX)

#     if xy.y() < 0:
#         xy.setY(0)
#     elif xy.y() > COMPLEMENT_MMD_MAX:
#         xy.setY(COMPLEMENT_MMD_MAX)

# # オフセットなしの3次ベジェ曲線の分割
# def calc_bezier_split_simple(x1, y1, cx1, cy1, cx2, cy2, x2, y2, t):

#     A = QVector2D(x1/COMPLEMENT_MMD_MAX, y1/COMPLEMENT_MMD_MAX)
#     B = QVector2D(cx1/COMPLEMENT_MMD_MAX, cy1/COMPLEMENT_MMD_MAX)
#     C = QVector2D(cx2/COMPLEMENT_MMD_MAX, cy2/COMPLEMENT_MMD_MAX)
#     D = QVector2D(x2/COMPLEMENT_MMD_MAX, y2/COMPLEMENT_MMD_MAX)

#     # A = QVector2D(x1, y1)
#     # B = QVector2D(cx1, cy1)
#     # C = QVector2D(cx2, cy2)
#     # D = QVector2D(x2, y2)

#     E = (1-t)*A + t*B
#     F = (1-t)*B + t*C
#     G = (1-t)*C + t*D
#     H = (1-t)*E + t*F
#     I = (1-t)*F + t*G
#     J = (1-t)*H + t*I

#     # 新たな4つのベジェ曲線の制御点は、A側がAEHJ、C側がJIGDとなる。

#     # スケーリング
#     bA, bE, bH, bJ = scale_bezier(A, E, H, J)
#     aJ, aI, aG, aD = scale_bezier(J, I, G, D)

#     bA2 = round_bezier_mmd(bA)
#     bE2 = round_bezier_mmd(bE)
#     bH2 = round_bezier_mmd(bH)
#     bJ2 = round_bezier_mmd(bJ)
#     aJ2 = round_bezier_mmd(aJ)
#     aI2 = round_bezier_mmd(aI)
#     aG2 = round_bezier_mmd(aG)
#     aD2 = round_bezier_mmd(aD)

#     return [bA2, bE2, bH2, bJ2], [aJ2, aI2, aG2, aD2]


# 指定された2次曲線の交点を求める
def calc_quadratic_cross(a, b, c, x1, y1, x2, y2):

    # 開始フレームの接線
    x1_tan1, x1_tan2 = inclinate(a, b, c, x1)

    # 中間フレームの接線
    x2_tan1, x2_tan2 = inclinate(a, b, c, x2)

    # x1の直線上の点
    p1 = x1 + 1
    q1 = (p1 * x1_tan1) + x1_tan2

    # nearの直線上の点
    p2 = x2 + 1
    q2 = (p2 * x2_tan1) + x2_tan2

    # x1の接線とnearの接線の交点
    s1 = (q1-y1)/(p1-x1)
    s3 = (q2-y2)/(p2-x2)

    cx1 = (s1*x1-y1-s3*x2+y2)/(s1-s3)
    cy1 = (q1-y1)/(p1-x1)*(cx1-x1)+y1    

    return cx1, cy1


# y = ax^2 + bx + c である場合の、xの接線の傾きを求める
def inclinate(a, b, c, x):
    return 2*a*x + b, -a*x*x+c

# y = ax^2 + bx + c 
# 指定された3点を通る二次曲線を返す
# https://blog.goo.ne.jp/kano08/e/9354000c0311e9a7a0ab01cca34033a3
def calc_quadratic_param(x1, y1, x2, y2, x3, y3):
    a = ((y1 - y2) * (x1 - x3) - (y1 - y3) * (x1 - x2)) / ((x1 - x2) * (x1 - x3) * (x2 - x3))
    b = (y1 - y2) / (x1 - x2) - a * (x1 + x2)
    c = y1 - a * x1 * x1 - b * x1

    return a, b, c


# 指定された3点と半径を通る球の中心点を求める
# https://oshiete.goo.ne.jp/qa/195295.html
# https://okwave.jp/qa/q9467739.html
def calc_sphere_center(pv, wv, nv, r):
    x1 = pv.x()
    y1 = pv.y()
    z1 = pv.z()
    x2 = wv.x()
    y2 = wv.y()
    z2 = wv.z()
    x3 = nv.x()
    y3 = nv.y()
    z3 = nv.z()

    if x1 == x2 == x3:
        # 同じ値の場合、2次元円として求める
        cx, cy, r = calc_circle_center(y1, z1, y2, z2, y3, z3)
        return QVector3D(x1, cx, cy), r
    
    if y1 == y2 == y3:
        cx, cy, r = calc_circle_center(x1, z1, x2, z2, x3, z3)
        return QVector3D(cx, y1, cy), r
    
    if z1 == z2 == z3:
        cx, cy, r = calc_circle_center(x1, y1, x2, y2, x3, y3)
        return QVector3D(cx, cy, z1), r
    
    tm01=x1**2-x2**2+y1**2-y2**2+z1**2-z2**2
    tm02=x1**2-x3**2+y1**2-y3**2+z1**2-z3**2
    tm11=-2*(x1-x2)*(z1-z3)+2*(x1-x3)*(z1-z2)
    tm12=-2*(y1-y2)*(z1-z3)+2*(y1-y3)*(z1-z2)
    tm13=tm01*(z1-z3)-tm02*(z1-z2)
    tm21=-2*(x1-x2)*(y1-y3)+2*(x1-x3)*(y1-y2)
    tm22=-2*(z1-z2)*(y1-y3)+2*(z1-z3)*(y1-y2)
    tm23=tm01*(y1-y3)-tm02*(y1-y2)
    tma=1+tm11**2/tm12**2+tm21**2/tm22**2
    tmb=-2*x1+2*(y1+tm13/tm12)*tm11/tm12+2*(z1+tm23/tm22)*tm21/tm22
    tmc=x1**2+(y1+tm13/tm12)**2+(z1+tm23/tm22)**2-r**2
    xq1=(-tmb+sqrt(tmb**2-4*tma*tmc))/2/tma
    xq2=(-tmb-sqrt(tmb**2-4*tma*tmc))/2/tma
    yq1=-tm13/tm12-tm11/tm12*xq1
    yq2=-tm13/tm12-tm11/tm12*xq2
    zq1=-tm23/tm22-tm21/tm22*xq1
    zq2=-tm23/tm22-tm21/tm22*xq2

    c1 = QVector3D(xq1, yq1, zq1)
    c2 = QVector3D(xq2, yq2, zq2)

    if c1 == c2:
        # 重解
        return c1, r

    if c1.distanceToPoint(QVector3D()) > c2.distanceToPoint(QVector3D()):
        # 原点に近い方を返す
        return c1, r

    return c2, r

# http://www.iot-kyoto.com/satoh/2016/01/29/tangent-003/
# http://nobutina.blog86.fc2.com/blog-entry-674.html
def calc_circle_center(x1, y1, x2, y2, x3, y3):

    G=( y2*x1-y1*x2 +y3*x2-y2*x3 +y1*x3-y3*x1 )

    if G == 0:
        if x1 == x2 == x3:
            G = sqrt((y1 + y2 + y3) ** 2)
        else:
            G = sqrt((x1 + x2 + x3) ** 2)

        return (x1 + x2 + x3) / 3, (y1 + y2 + y3) / 3, G

    Xc= ((x1*x1+y1*y1)*(y2-y3)+(x2*x2+y2*y2)*(y3-y1)+(x3*x3+y3*y3)*(y1-y2))/(2*G)
    Yc=-((x1*x1+y1*y1)*(x2-x3)+(x2*x2+y2*y2)*(x3-x1)+(x3*x3+y3*y3)*(x1-x2))/(2*G)

    Xd=(((x1*x1+y1*y1)-(x2*x2+y2*y2))*(y2-y3)-((x2*x2+y2*y2)-(x3*x3+y3*y3))*(y1-y2))/(2*((x1-x2)*(y2-y3)-(x2-x3)*(y1-y2)))
    Yd=(((y1*y1+x1*x1)-(y2*y2+x2*x2))*(x2-x3)-((y2*y2+x2*x2)-(y3*y3+x3*x3))*(x1-x2))/(2*((y1-y2)*(x2-x3)-(y2-y3)*(x1-x2)))

    G=2 * sqrt( (x1 - Xc) * (x1 - Xc) + (y1 - Yc) * (y1 - Yc) )

    return Xd, Yd, G/2

    # a = x2 - x1
    # b = y2 - y1
    # c = x3 - x1
    # d = y3 - y1
    # cx = 0
    # cy = 0
    # r = 0

    # if  ((a and d) or (b and c)):
    #     ox = x1 + (d * (a * a + b * b) - b * (c * c + d * d)) / (a * d - b * c) / 2
    #     if b:
    #         oy = (a * (x1 + x2 - ox - ox) + b * (y1 + y2)) / b / 2
    #     else:
    #         oy = (c * (x1 + x3 - ox - ox) + d * (y1 + y3)) / d / 2

    #     r1   = sqrt((ox - x1) * (ox - x1) + (oy - y1) * (oy - y1))
    #     r2   = sqrt((ox - x2) * (ox - x2) + (oy - y2) * (oy - y2))
    #     r3   = sqrt((ox - x3) * (ox - x3) + (oy - y3) * (oy - y3))

    #     cx = ox
    #     cy = oy
    #     r  = (r1 + r2 + r3) / 3

    # return cx, cy, r    



# y = ax^2 + bx + c である場合の、xに対するyを返す
def calc_quadratic_curve(a, b, c, x):
    return 2*a*x + b * x + c


# 指定された方向に向いた場合の位置情報を返す
def create_direction_pos_all(direction_qq, target_pos_3ds):
    direction_pos_3ds = []

    for target_pos in target_pos_3ds:
        direction_pos_3ds.append(create_direction_pos(direction_qq, target_pos))
    
    return direction_pos_3ds

# 指定された方向に向いた場合の位置情報を返す
def create_direction_pos(direction_qq, target_pos):
    mat = QMatrix4x4()
    mat.rotate(direction_qq)
    return mat.mapVector(target_pos)





# # 指定フレームのX軸とグラフの交点の位置を求める
# # http://kaerouka.hatenablog.com/entry/2013/12/21/212809
# def sqrt_newton_method(value, cnt):
# 	 # x切片
# 	preval = value

# 	for i in range(cnt):
# 		preval = 1/2 * (preval + value/preval)

# 	return preval



# # 補間曲線（ベジェ曲線）の接線を求める
# def calc_bezier_line_tangent(vx1, vy1, vx2, vy2, vx3, vy3, vx4, vy4, t):

#     bz1 = QVector2D(0, 0)
#     bz4 = QVector2D(2, 2)



#     if x2 < x4:
#         # farよりnowの方が後の場合
#         bz2 = QVector2D(x2, y2)
#         bz3 = QVector2D(x4, y4)
#     else:
#         # farよりnowの方が前の場合
#         bz2 = QVector2D(x4, y4)
#         bz3 = QVector2D(x2, y2)
#         bz4 = QVector2D(x3, y3)

#     # https://stackoverflow.com/questions/4089443/find-the-tangent-of-a-point-on-a-cubic-bezier-curve
#     # dP(t) / dt =  -3(1-t)^2 * P0 + 3(1-t)^2 * P1 - 6t(1-t) * P1 - 3t^2 * P2 + 6t(1-t) * P2 + 3t^2 * P3
#     # v = -3*(1-t)**2*bz1 + 3*(1-t)**2*bz2 - 6*t*(1-t)*bz2 - 3*t**2*bz3 + 6*t*(1-t)*bz3 * 3*t**2*bz4

#     # http://geom.web.fc2.com/geometry/bezier/cut-cb.html
#     v = (1-t)**3*bz1 + 3*(1-t)**2*t*bz2 + 3*(1-t)*t**2*bz3 + t**3*bz4

#     # http://junosoft.sblo.jp/article/92871518.html
#     # v = 3*(-1*bz1 + 3*bz2 - 3*bz3 + bz4)*t**2 + 6*(bz1-2*bz2+bz3)*t + 3*(-1*bz1 + bz2)

#     # https://forum.shade3d.jp/t/09-bezier-line-shade-labo/249/2
#     # v = (-3*(1 - t)**2)*bz1 + 3*(1 - t)*(1 - 3*t)*bz2 + 3*t*(2 - 3*t)*bz3 + (3*t**2)*bz4

#     v.normalize()

#     return t, v


# # 指定された3点を通る二次曲線に従い、指定されたxのyを返す
# # https://blog.goo.ne.jp/kano08/e/9354000c0311e9a7a0ab01cca34033a3
# def calc_quadratic_by_x(x1, y1, x2, y2, x3, y3, x):
#     a, b, c = calc_quadratic_param(x1, y1, x2, y2, x3, y3)

#     y = a * (x ** 2) + b * x + c

#     return a, b, c, y

# # 指定された3点を通る二次曲線に従い、指定されたyのxを返す
# # https://oshiete.goo.ne.jp/qa/5308458.html
# def calc_quadratic_by_y(x1, y1, x2, y2, x3, y3, y):
#     a, b, c = calc_quadratic_param(x1, y1, x2, y2, x3, y3)

#     x = int(abs((-b + sqrt((b ** 2) - ( 4 * a * ( c - y )) )) / (2 * a)))

#     return a, b, c, x

# # https://stackoverflow.com/questions/9600801/evenly-distributing-n-points-on-a-sphere
# def fibonacci_sphere(samples=1,randomize=True):
#     rnd = 1.
#     if randomize:
#         rnd = random.random() * samples

#     points = []
#     offset = 2./samples
#     increment = math.pi * (3. - math.sqrt(5.))

#     for i in range(samples):
#         y = ((i * offset) - 1) + (offset / 2)
#         r = math.sqrt(1 - pow(y,2))

#         phi = ((i + rnd) % samples) * increment

#         x = math.cos(phi) * r
#         z = math.sin(phi) * r

#         points.append([x,y,z])

#     return points
