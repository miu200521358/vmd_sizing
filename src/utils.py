# -*- coding: utf-8 -*-
# ユーティリティ系
# 
import re
import logging
import copy
import datetime
from math import atan2, acos, cos, sin, degrees, isnan, isclose, sqrt, pi
from PyQt5.QtGui import QQuaternion, QVector3D, QVector2D, QMatrix4x4, QVector4D

from VmdWriter import VmdWriter, VmdBoneFrame
from VmdReader import VmdReader
from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader

logger = logging.getLogger("VmdSizing").getChild(__name__)

# MMDでの補間曲線の最大値
COMPLEMENT_MMD_MAX = 127


loggers = {}

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
MX_y1_idxs = [4, 4, 4, 4]
MX_x2_idxs = [8, 8, 8, 8]
MX_y2_idxs = [12, 12, 12, 12]

# Y移動補間曲線のインデックス
MY_x1_idxs = [16, 16, 16, 16]
MY_y1_idxs = [20, 20, 20, 20]
MY_x2_idxs = [24, 24, 24, 24]
MY_y2_idxs = [28, 28, 28, 28]

# Z移動補間曲線のインデックス
MZ_x1_idxs = [32, 32, 32, 32]
MZ_y1_idxs = [36, 36, 36, 36]
MZ_x2_idxs = [40, 40, 40, 40]
MZ_y2_idxs = [44, 44, 44, 44]


# 補間曲線を考慮した指定フレーム番号の位置
# https://www55.atwiki.jp/kumiho_k/pages/15.html
# https://harigane.at.webry.info/201103/article_1.html
def calc_bone_by_complement(frames, bone_name, frameno, is_calc_complement=False):
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
        return True, [QVector2D(),QVector2D(),QVector2D(),QVector2D()], [QVector2D(),QVector2D(),QVector2D(),QVector2D()]

    # 3次ベジェ曲線を分割する
    t, x, y, beforebz, afterbz = calc_bezier_split_offset(x1v, y1v, x2v, y2v, start, end, now, bone_name)

    # ベジェ曲線の値がMMD用に合っているかを加味して返す
    return t, x, y, is_fit_bezier_mmd(beforebz), is_fit_bezier_mmd(afterbz), beforebz, afterbz


# ベジェ曲線の値がMMD用に合っているか
def is_fit_bezier_mmd(bz):
    for b in bz:
        # # 1割以下は誤差として吸収してしまう
        # b.setX( 0 if COMPLEMENT_MMD_MAX-1 <= b.x() < 0 else b.x() )
        # b.setY( COMPLEMENT_MMD_MAX if COMPLEMENT_MMD_MAX < b.x() <= COMPLEMENT_MMD_MAX+1 else b.y() )

        if not (0 <= b.x() <= COMPLEMENT_MMD_MAX) or not (0 <= b.y() <= COMPLEMENT_MMD_MAX):
            # MMD用の範囲内でなければNG
            return False

    return True
    
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
    if isnan(s.x()):
        s.setX(0)

    if isnan(s.y()):
        s.setY(0)

    return s

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

    return x3, y
