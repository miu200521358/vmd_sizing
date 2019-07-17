# -*- coding: utf-8 -*-
# ユーティリティ系
# 
import logging
import copy
import numpy as np
from math import acos, degrees
from PyQt5.QtGui import QQuaternion, QVector3D, QVector2D, QMatrix4x4, QVector4D

from VmdWriter import VmdWriter, VmdBoneFrame
from VmdReader import VmdReader
from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader

logger = logging.getLogger("__main__").getChild(__name__)

# ログを生成する
def create_error_logger(motion, trace_model, replace_model, error_path, error_file_logger):

    if not error_file_logger:
        error_file_logger = logging.getLogger("message")
        error_file_logger.addHandler(logging.FileHandler(error_path))

    error_file_logger.info("モーション: %s" , motion.path)
    error_file_logger.info("作成元: %s" , trace_model.path)
    error_file_logger.info("変換先: %s" , replace_model.path)

    return error_file_logger


# 指定されたフレームより前のキーを返す
def get_prev_bf(frames, bone_name, frameno):
    for bidx, bf in enumerate(frames[bone_name]):
        if bf.frame >= frameno:
            # 指定されたフレーム以降の一つ前で、前のキーを取る
            return bidx, frames[bone_name][bidx - 1]

    # 最後まで取れなければ、最終項目
    return len(frames[bone_name]) - 1, frames[bone_name][-1]
    

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
            if 1170 <= bf.frame <= 1190:
                logger.debug("軸固定before: %s, fixed_axis:%s, rot: %s, euler: %s", lbone.name, lbone.fixed_axis, rot, rot.toEulerAngles())
                
            # 回転角度を求める
            if rot == QQuaternion():
                # 回転なしの場合、角度なし
                degree = 0
            else:
                # 回転補正
                if "右" in lbone.name and rot.x() > 0:
                    rot.setX(rot.x() * -1)
                    # rot.setY(rot.y() * -1)
                    rot.setScalar(rot.scalar() * -1)
                    # rot.setZ(abs(rot.z()))
                elif "左" in lbone.name and rot.x() < 0:
                    rot.setX(rot.x() * -1)
                    rot.setScalar(rot.scalar() * -1)
                    # rot.setX(rot.x() * -1)
                    # rot.setScalar(rot.scalar() * -1)
                
                rot.normalize()

                degree = degrees(2 * acos(rot.scalar()))

            if 1070 <= bf.frame <= 1090:
                logger.debug("軸固定after: %s, fixed_axis:%s, rot: %s, degree: %s", lbone.name, lbone.fixed_axis, rot, degree)                
            
            # 軸固定の場合、回転を制限する
            rot = QQuaternion.fromAxisAndAngle(lbone.fixed_axis, degree)
        
        add_qs[lidx] = rot
    
        if bf.frame == 279:
            logger.debug("f: %s, lbone: %s, rot: %s", bf.frame, lbone.name, rot.toEulerAngles())

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
                if "右" in lbone.name and rot.x() > 0:
                    rot.setX(rot.x() * -1)
                    rot.setScalar(rot.scalar() * -1)
                elif "左" in lbone.name and rot.x() < 0:
                    rot.setX(rot.x() * -1)
                    rot.setScalar(rot.scalar() * -1)
                
                rot.normalize()

                degree = degrees(2 * acos(rot.scalar()))
            
            # 軸固定の場合、回転を制限する
            rot = QQuaternion.fromAxisAndAngle(lbone.fixed_axis, degree)
    
        logger.debug("lbone: %s, rot: %s", lbone.name, rot.toEulerAngles())

        total_qq *= rot

    # # Y軸の回転だけを抽出する
    # total_y_qq = QQuaternion.fromEulerAngles(0, total_qq.toEulerAngles().y(), 0)

    # logger.debug("total_y_qq: %s", total_y_qq.toEulerAngles())

    # XYZ全方向の回転を参照するため、そのまま返す
    return total_qq



# 回転補間曲線のインデックス
R_x1_idxs = [3, 18, 33, 48]
R_y1_idxs = [7, 22, 37, 52]
R_x2_idxs = [11, 26, 41, 56]
R_y2_idxs = [15, 30, 45, 60]
        
# 補間曲線を考慮した指定フレーム番号の位置
# https://www55.atwiki.jp/kumiho_k/pages/15.html
# https://harigane.at.webry.info/201103/article_1.html
def calc_bone_by_complement(frames, bone_name, frameno, is_calc_complement=False):
    fillbf = VmdBoneFrame()

    # ボーン登録がなければ初期値
    if bone_name not in frames:
        fillbf.name = bone_name.encode('shift-jis')
        fillbf.format_name = bone_name
        fillbf.frame = frameno
        return fillbf

    for bidx, bf in enumerate(frames[bone_name]):
        if bf.frame == frameno:
            # 同一フレームのキーがある場合、それを返す
            fillbf = copy.deepcopy(bf)
            if frameno == 5217:
                logger.info("calc_bone_by_complement 同一キーあり: %s, %s, read: %s", frameno, bone_name, fillbf.read)
            return fillbf
        elif bf.frame > frameno:
            # 同一フレームのキーがない場合、前のキーIDXを0に見立てて、その間の補間曲線を埋める
            fillbf.name = bf.name
            fillbf.format_name = bone_name
            fillbf.frame = frameno
            # 実際に登録はしない
            fillbf.key = False
            # 読み込みキーではない
            fillbf.read = False

            if frameno == 5217:
                logger.info("calc_bone_by_complement 同一キーなし: %s, %s, read: %s", frameno, bone_name, fillbf.read)

            if is_calc_complement:
                # 補間曲線の計算し直しの場合

                # 前の読み込んだキー
                for pbf_idx in range(bidx - 1, -1, -1):
                    if frames[bone_name][pbf_idx].read == True:
                        prev_bf = frames[bone_name][pbf_idx]
                        break
                
                # 処理対象補間曲線（処理前の補間曲線）
                comp = bf.org_complement
            else:
                # 補間曲線は弄らない場合

                # 指定されたフレーム直前のキー
                prev_bf = frames[bone_name][bidx - 1]

                # 処理対象補間曲線
                comp = bf.complement

            # logger.debug("bone_name: %s, bf: %s, bidx: %s", bone_name, bf.frame, bidx)

            if prev_bf.rotation != bf.rotation:
                # 回転補間曲線
                _, _, rn = calc_interpolate_bezier(comp[R_x1_idxs[3]], comp[R_y1_idxs[3]], comp[R_x2_idxs[3]], comp[R_y2_idxs[3]], prev_bf.frame, bf.frame, fillbf.frame)
                fillbf.rotation = QQuaternion.slerp(prev_bf.rotation, bf.rotation, rn)

                if 1070 <= fillbf.frame <= 1090:
                    logger.debug("f: %s, k: %s, rn: %s, r: %s ", frameno, bone_name, rn, fillbf.rotation.toEulerAngles() )
                    logger.debug("rotation: prev: %s, bf: %s ", prev_bf.rotation.toEulerAngles(), bf.rotation.toEulerAngles() )
            else:
                fillbf.rotation = copy.deepcopy(prev_bf.rotation)

            # 補間曲線を元に間を埋める
            if prev_bf.position != bf.position:
                # http://rantyen.blog.fc2.com/blog-entry-65.html
                # X移動補間曲線
                _, _, xn = calc_interpolate_bezier(comp[0], comp[4], comp[8], comp[12], prev_bf.frame, bf.frame, fillbf.frame)
                # Y移動補間曲線
                _, _, yn = calc_interpolate_bezier(comp[16], comp[20], comp[24], comp[28], prev_bf.frame, bf.frame, fillbf.frame)
                # Z移動補間曲線
                _, _, zn = calc_interpolate_bezier(comp[32], comp[36], comp[40], comp[44], prev_bf.frame, bf.frame, fillbf.frame)

                fillbf.position.setX(prev_bf.position.x() + (( bf.position.x() - prev_bf.position.x()) * xn))
                fillbf.position.setY(prev_bf.position.y() + (( bf.position.y() - prev_bf.position.y()) * yn))
                fillbf.position.setZ(prev_bf.position.z() + (( bf.position.z() - prev_bf.position.z()) * zn))
                # logger.debug("key: %s, n: %s, xn: %s, yn: %s, zn: %s, xa: %s", k, prev_frame + n, xn, yn, zn, ( bf.position.x() - prev_bf.position.x()) * xn )
                # logger.debug("position: prev: %s, fill: %s ", prev_bf.position, fillbf.position )
            else:
                fillbf.position = copy.deepcopy(prev_bf.position)
                # logger.debug("position stop: %s,%s prev: %s, fill: %s ", prev_frame + n, k, prev_bf.position, bf.position )
            
            # if is_calc_complement:
            #     # 指定されたフレーム直前のキーを再設定
            #     prev_bf = frames[bone_name][bidx - 1]

            #     # 補間曲線を計算する場合、現在の補間曲線から分割する
            #     next_x1v = bf.complement[R_x1_idxs[3]]
            #     next_y1v = bf.complement[R_y1_idxs[3]]
            #     next_x2v = bf.complement[R_x2_idxs[3]]
            #     next_y2v = bf.complement[R_y2_idxs[3]]
                
            #     # # ベジェ曲線の実値を求める
            #     # rx, rn = calc_interpolate_bezier(next_x1v, next_y1v, next_x2v, next_y2v, prev_bf.frame, bf.frame, fillbf.frame)
            #     # # ベジェ曲線の接線を求める
            #     # rx, v = calc_bezier_line_tangent(next_x1v, next_y1v, next_x2v, next_y2v, prev_bf.frame, bf.frame, fillbf.frame)
            #     # ベジェ曲線を分割して新しい制御点を求める
            #     before_bz, after_bz = calc_bezier_split(next_x1v, next_y1v, next_x2v, next_y2v, prev_bf.frame, bf.frame, fillbf.frame, bone_name)

            #     logger.debug("bone: %s, prev: %s, bf: %s, fillbf: %s", bone_name, prev_bf.frame, bf.frame, fillbf.frame)
            #     if 2440 <= fillbf.frame <= 2440:
            #         logger.debug("next_x1v: %s, next_y1v: %s, next_x2v: %s, next_y2v: %s", next_x1v, next_y1v, next_x2v, next_y2v)
            #         logger.debug("before_bz: %s", before_bz)
            #         logger.debug("after_bz: %s", after_bz)

            #     # オリジナルの補間曲線として先の元々の補間曲線を保持しておく
            #     fillbf.org_complement = copy.deepcopy(bf.org_complement)
            #     # 補間曲線を元々の補間曲線からコピーする
            #     fillbf.complement = copy.deepcopy(bf.complement)

            #     # 分割の始点は、前半のB
            #     fillbf.complement[R_x1_idxs[0]] = fillbf.complement[R_x1_idxs[1]] = fillbf.complement[R_x1_idxs[2]] = fillbf.complement[R_x1_idxs[3]] = int(before_bz[1].x())
            #     fillbf.complement[R_y1_idxs[0]] = fillbf.complement[R_y1_idxs[1]] = fillbf.complement[R_y1_idxs[2]] = fillbf.complement[R_y1_idxs[3]] = int(before_bz[1].y())

            #     # 分割の終点は、後半のC
            #     fillbf.complement[R_x2_idxs[0]] = fillbf.complement[R_x2_idxs[1]] = fillbf.complement[R_x2_idxs[2]] = fillbf.complement[R_x2_idxs[3]] = int(before_bz[2].x())
            #     fillbf.complement[R_y2_idxs[0]] = fillbf.complement[R_y2_idxs[1]] = fillbf.complement[R_y2_idxs[2]] = fillbf.complement[R_y2_idxs[3]] = int(before_bz[2].y())

            #     # 今回の始点は、後半のB
            #     bf.complement[R_x1_idxs[0]] = bf.complement[R_x1_idxs[1]] = bf.complement[R_x1_idxs[2]] = bf.complement[R_x1_idxs[3]] = int(after_bz[1].x())
            #     bf.complement[R_y1_idxs[0]] = bf.complement[R_y1_idxs[1]] = bf.complement[R_y1_idxs[2]] = bf.complement[R_y1_idxs[3]] = int(after_bz[1].y())

            #     # 今回の終点は、後半のC
            #     bf.complement[R_x2_idxs[0]] = bf.complement[R_x2_idxs[1]] = bf.complement[R_x2_idxs[2]] = bf.complement[R_x2_idxs[3]] = int(after_bz[2].x())
            #     bf.complement[R_y2_idxs[0]] = bf.complement[R_y2_idxs[1]] = bf.complement[R_y2_idxs[2]] = bf.complement[R_y2_idxs[3]] = int(after_bz[2].y())

            #     if 2440 <= fillbf.frame <= 2440:
            #         logger.debug("fillbf.complement[R_x2_idxs[0]]: %s, fillbf.complement[R_y2_idxs[0]]: %s", fillbf.complement[R_x2_idxs[0]], fillbf.complement[R_y2_idxs[0]])
            #         logger.debug("bf.complement[R_x1_idxs[0]]: %s, bf.complement[R_y1_idxs[0]]: %s", bf.complement[R_x1_idxs[0]], bf.complement[R_y1_idxs[0]])

            return fillbf

    if frameno == 5217:
        logger.info("calc_bone_by_complement 見つからなかった: %s, %s", frameno, bone_name)

    # 最後まで行っても見つからなければ、最終項目を返す
    return copy.deepcopy(frames[bone_name][-1])

# 補間曲線（ベジェ曲線）の接線を求める
def calc_bezier_line_tangent(x1v, y1v, x2v, y2v, start, end, now):
    if (now - start) == 0 or (end - start) == 0:
        return QVector2D()

    t = (now - start) / (end - start)

    bz1 = QVector2D(0, 0)
    bz2 = QVector2D(x1v, y1v)
    bz3 = QVector2D(x2v, y2v)
    bz4 = QVector2D(127, 127)

    # https://stackoverflow.com/questions/4089443/find-the-tangent-of-a-point-on-a-cubic-bezier-curve
    # dP(t) / dt =  -3(1-t)^2 * P0 + 3(1-t)^2 * P1 - 6t(1-t) * P1 - 3t^2 * P2 + 6t(1-t) * P2 + 3t^2 * P3
    # v = -3*(1-t)**2*bz1 + 3*(1-t)**2*bz2 - 6*t*(1-t)*bz2 - 3*t**2*bz3 + 6*t*(1-t)*bz3 * 3*t**2*bz4

    # http://geom.web.fc2.com/geometry/bezier/cut-cb.html
    v = (1-t)**3*bz1 + 3*(1-t)**2*t*bz2 + 3*(1-t)*t**2*bz3 + t**3*bz4

    # http://junosoft.sblo.jp/article/92871518.html
    # v = 3*(-1*bz1 + 3*bz2 - 3*bz3 + bz4)*t**2 + 6*(bz1-2*bz2+bz3)*t + 3*(-1*bz1 + bz2)

    # if 0 <= now <= 1000:
    #     logger.debug("v before: %s", v)

    # https://forum.shade3d.jp/t/09-bezier-line-shade-labo/249/2
    # v = (-3*(1 - t)**2)*bz1 + 3*(1 - t)*(1 - 3*t)*bz2 + 3*t*(2 - 3*t)*bz3 + (3*t**2)*bz4

    # if 0 <= now <= 1000:
    #     logger.debug("v after: %s", v)

    v.normalize()

    # if 0 <= now <= 1000:
    #     logger.debug("v normalized: %s", v)

    # if v.lengthSquared() < 0.5:
    #     if t < 0.5:				#  outhandle が出ていなくて t = 0
    #         v = bz3 - bz1
    #     else :						#  inhandle が出ていなくて t = 1
    #         v = bz4 - bz2
    #     v.normalize()

    #     if v.lengthSquared() < 0.5:
    #         v = bz4 - bz1
    #         v.normalize()
        
    return t, v

# 3次ベジェ曲線の分割
# http://geom.web.fc2.com/geometry/bezier/cut-cb.html
def calc_bezier_split(x1v, y1v, x2v, y2v, start, end, now, bone_name):
    if (now - start) == 0 or (end - start) == 0:
        return [QVector2D(),QVector2D(),QVector2D(),QVector2D()], [QVector2D(),QVector2D(),QVector2D(),QVector2D()]

    # t = (now - start) / (end - start)

    t, _, _ = calc_interpolate_bezier(x1v, y1v, x2v, y2v, start, end, now)

    # return calc_bezier_split_range(x1v, y1v, x2v, y2v, 0, t), calc_bezier_split_range(x1v, y1v, x2v, y2v, t, 1)

    # A = QVector2D(0.0, 0.0)
    # B = QVector2D(x1v, y1v)
    # C = QVector2D(x2v, y2v)
    # D = QVector2D(127.0, 127.0)

    A = QVector2D(0.0, 0.0)
    B = QVector2D(x1v/127, y1v/127)
    C = QVector2D(x2v/127, y2v/127)
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

    logger.info("bone_name,start,now,end,t,x1v,y1v,x2v,y2v,A.x(),A.y(),B.x(),B.y(),C.x(),C.y(),D.x(),D.y(),E.x(),E.y(),F.x(),F.y(),G.x(),G.y(),H.x(),H.y(),I.x(),I.y(),J.x(),J.y(),bA.x(),bA.y(),bE.x(),bE.y(),bH.x(),bH.y(),bJ.x(),bJ.y(),aJ.x(),aJ.y(),aI.x(),aI.y(),aG.x(), aG.y(),aD.x(),aD.y() ,bA2.x(),bA2.y(),bE2.x(),bE2.y(),bH2.x(),bH2.y(),bJ2.x(),bJ2.y(),aJ2.x(),aJ2.y(),aI2.x(),aI2.y(),aG2.x(),aG2.y(),aD2.x(),aD2.y()")    
    logger.info("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s", bone_name,start,now,end,t,x1v,y1v,x2v,y2v,A.x(),A.y(),B.x(),B.y(),C.x(),C.y(),D.x(),D.y(),E.x(),E.y(),F.x(),F.y(),G.x(),G.y(),H.x(),H.y(),I.x(),I.y(),J.x(),J.y(),bA.x(),bA.y(),bE.x(),bE.y(),bH.x(),bH.y(),bJ.x(),bJ.y(),aJ.x(),aJ.y(),aI.x(),aI.y(),aG.x(), aG.y(),aD.x(),aD.y() ,bA2.x(),bA2.y(),bE2.x(),bE2.y(),bH2.x(),bH2.y(),bJ2.x(),bJ2.y(),aJ2.x(),aJ2.y(),aI2.x(),aI2.y(),aG2.x(),aG2.y(),aD2.x(),aD2.y())

    return [bA2, bE2, bH2, bJ2], [aJ2, aI2, aG2, aD2]

def scale_bezier(p1, p2, p3, p4):
    diff = p4 - p1

    s1 = (p1-p1) / diff
    s2 = (p2-p1) / diff
    s3 = (p3-p1) / diff
    s4 = (p4-p1) / diff

    return s1, s2, s3, s4

# def scale_bezier(p1, p2, p3, p4):
#     # 起点を原点におく
#     sp1 = (p1-p1)
#     sp2 = (p2-p1)
#     sp3 = (p3-p1)
#     sp4 = (p4-p1)

#     # 底辺の単位ベクトル
#     bottom_vec = (sp4 - sp1)
#     # 底辺の法線ベクトル
#     bottom_normal_vec1 = QVector2D(-bottom_vec.y(), bottom_vec.x())
#     bottom_normal_vec2 = QVector2D(bottom_vec.y(), -bottom_vec.x())

#     logger.info("bottom_vec: %s", bottom_vec)
#     logger.info("bottom_normal_vec1: %s", bottom_normal_vec1)
#     logger.info("bottom_normal_vec2: %s", bottom_normal_vec2)

#     dsp2 = bottom_normal_vec1.distanceToPoint(sp2)
#     dsp3 = bottom_normal_vec1.distanceToPoint(sp3)
#     logger.info("dsp2: %s", dsp2)
#     logger.info("dsp3: %s", dsp3)



#     hp1 = QVector2D()
#     hp2 = QVector2D()
#     hp3 = QVector2D()
#     hp4 = QVector2D()

#     return hp1, hp2, hp3, hp4



# class BezierLength:
#     def __init__(self,node):
#         p = [] #始点，制御点１，制御点２，終点を入れるリスト
#         for i in range(4):
#             p.append(np.array([node[0][i],node[1][i]]))

#         self.p = p
        
#         ###########################################################
#         #
#         # P(t)=(1-t)^3*P0 + 3t(1-t)^2*P1 + 3t^2(1-t)*P2 + t^3*P3
#         #      =At^3 + Bt^2 + Ct + D
#         # とすると
#         # A=-P0 + 3P1 - 3P2 + P3
#         # B=3P0 - 6P1 + 3P2
#         # C=-3P0 + 3P1
#         # D=P0
#         # 微分すると，
#         # P'(t)=3At^2 + 2Bt + C
#         # これを二乗する
#         # (P'(t))^2 = 9A^2t^4 + 12ABt^3 + (6AC+4B^2)t^2 + 4BCt + C^2
#         #
#         ###########################################################
        
#         A = -p[0] + 3*p[1] - 3*p[2] + p[3] 
#         B = 3*p[0] - 6*p[1] + 3*p[2]
#         C = -3*p[0] + 3*p[1]
#         D = p[0]
#         self.A = A
#         self.B = B
#         self.C = C
#         self.D = D

#         coef = []
#         coef.append(9*np.sum(A**2))
#         coef.append(12*np.sum(A*B))
#         coef.append(6*np.sum(A*C) + 4*np.sum(B**2))
#         coef.append(4*np.sum(B*C))
#         coef.append(np.sum(C**2))
#         self.coef = coef
        
#     def get_points_on_beziercurve(self, num=100):
#         results = np.empty((2,0))
#         interval = np.linspace(0,1,num)
#         for t in interval:
#             results = np.concatenate([results,np.reshape(self.A*t**3 + self.B*t**2 + self.C*t + self.D, (2,1))],axis=1)
        
#         return results
        
#     def divf(self,s):
#         return np.sqrt(self.coef[0]*s**4 + self.coef[1]*s**3 + self.coef[2]*s**2 + self.coef[3]*s + self.coef[4])
    
#     def get_length_by_3rdRungeKutta(self, div=100):
#         length = 0
#         interval = np.linspace(0,1,div)
#         h = 1.0/div
#         for t in interval[1:]:
#             k1 = self.divf(t)
#             k2 = self.divf(t + (h/2))
#             k3 = self.divf(t + h)
#             y = h * (k1 + 4*k2 + k3) / 6.0
#             length = length + y

#         return length
    




# # 射影変換で制御点を正方形に直す
# # https://fermiumbay13.hatenablog.com/entry/2018/08/14/032643
# def scale_bezier(p1, p2, p3, p4):
#     min_x = min(p1.x(), p2.x(), p3.x(), p4.x())
#     min_y = min(p1.y(), p2.y(), p3.y(), p4.y())
#     max_x = max(p1.x(), p2.x(), p3.x(), p4.x())
#     max_y = max(p1.y(), p2.y(), p3.y(), p4.y())
    
#     # パラメーターを求める
#     a, b, c, d, e, f, g, h = calc_homography_param(p1, QVector2D(p1.x(), p2.y()), QVector2D(p4.x(), p3.y()), p4)

#     # 点を射影変換する
#     hp1 = calc_point_homography(p1, a, b, c, d, e, f, g, h)
#     hp2 = calc_point_homography(p2, a, b, c, d, e, f, g, h)
#     hp3 = calc_point_homography(p3, a, b, c, d, e, f, g, h)
#     hp4 = calc_point_homography(p4, a, b, c, d, e, f, g, h)

#     logger.info("p1.x(), p1.y(), p2.x(), p2.y(), p3.x(), p3.y(), p4.x(), p4.y(), a, b, c, d, e, f, g, h, hp1.x(), hp1.y(), hp2.x(), hp2.y(), hp3.x(), hp3.y(), hp4.x(), hp4.y()")
#     logger.info("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, %s, %s, %s, %s, %s, %s, %s", p1.x(), p1.y(), p2.x(), p2.y(), p3.x(), p3.y(), p4.x(), p4.y(), a, b, c, d, e, f, g, h, hp1.x(), hp1.y(), hp2.x(), hp2.y(), hp3.x(), hp3.y(), hp4.x(), hp4.y())

#     return hp1, hp2, hp3, hp4

# # 二次元の点を射影変換する
# def calc_point_homography(p, a, b, c, d, e, f, g, h):
#     x = (a * p.x() + b * p.y() + c) / ( g * p.x() + h * p.y() + 1 )
#     y = (d * p.x() + e * p.y() + f) / ( g * p.x() + h * p.y() + 1 )

#     logger.info("a:%s, p.x(): %s, a * p.x():%s, ", a, p.x(), a * p.x())
#     logger.info("b:%s, p.y(): %s, b * p.y():%s, ", b, p.y(), b * p.y())
#     logger.info("g:%s, p.x(): %s, g * p.x():%s, ", g, p.x(), g * p.x())
#     logger.info("h:%s, p.y(): %s, h * p.y():%s, ", h, p.y(), h * p.y())

#     return QVector2D(x, y)

# # 射影変換のパラメーターを取得する
# def calc_homography_param(p1, p2, p3, p4):
#     # 起点を原点におく
#     sp1 = check_zero(p1-p1)
#     sp2 = check_zero(p2-p1)
#     sp3 = check_zero(p3-p1)
#     sp4 = check_zero(p4-p1)

#     alpha = cross(sp4, sp2) - cross(sp3, sp2)
#     beta = cross(sp4, sp2) * p3.x() - cross(sp3, sp2) * p4.x()
#     gamma = cross(sp4, sp2) * p3.y() - cross(sp3, sp2) * p4.y()

#     # logger.info("sp1: %s, sp2: %s, sp3: %s, sp4: %s", sp1, sp2, sp3, sp4)
#     # logger.info("cross(sp4, sp2): %s, cross(sp3, sp2): %s", cross(sp4, sp2), cross(sp3, sp2))
#     # logger.info("cross(sp4, sp2) * p3.y(): %s, cross(sp3, sp2) * p4.y(): %s", cross(sp4, sp2) * p3.y(), cross(sp3, sp2) * p4.y())
#     # logger.info("alpha: %s, beta: %s, gamma: %s", alpha, beta, gamma)

#     g = ((cross(sp4, sp3) * ( sp3.y() * gamma - p2.y() * sp3.y() * alpha )) - (cross(sp2, sp3) * ( sp3.y() * gamma - p4.y() * sp3.y() * alpha ))) \
#         / ( (cross(sp4, sp3) * ( p2.y() * sp3.y() * beta - p2.x() * sp3.y() * gamma )) - (cross(sp2, sp3) * ( p4.y() * sp3.y() * beta - p4.x() * sp3.y() * gamma )) )

#     h = -(( alpha + beta * g ) / gamma)

#     a = (sp3.y() * gamma - p2.y() * sp3.y() * alpha - ( p2.y() * sp3.y() * beta - p2.x() * sp3.y() * gamma ) * g) \
#         / ( cross(sp2, sp3) * gamma )

#     d = (( cross(sp4, sp3) * sp2.y() ) / ( cross(sp4, sp2) * sp3.y() )) * a

#     b = -((sp3.x() / sp3.y()) * a)

#     e = -((sp2.x() / sp2.y()) * d)

#     c = (-a * p1.x()) - ( b * p1.y() )

#     f = (-d * p1.x()) - ( e * p1.y() )

#     return a, b, c, d, e, f, g, h

# # ゼロそのものだとゼロ割エラーが発生するのでとりあえず値設定
# def check_zero(a):
#     if a.x() == 0:
#         a.setX(0.000001)
#     if a.y() == 0:
#         a.setY(0.000001)
    
#     return a

# # 外積
# def cross(a, b):
#     return a.x() * b.y() - b.x() * a.y()











# # 射影変換で制御点を正方形に直す
# # https://github.com/fuqunaga/QuadWarp/blob/master/Assets/QuadWarp.cs
# # https://qiita.com/fuqunaga/items/f1534b50ba483e884715
# def scale_bezier(p0, p1, p2, p3):
#     # (0,0)(0,1)(1,1)(1,0)の逆行列
#     homography = calc_homography(p0, p1, p3, p2).inverted()[0]

#     hp0 = calc_point_homography(p0, homography)
#     hp1 = calc_point_homography(p1, homography)
#     hp2 = calc_point_homography(p2, homography)
#     hp3 = calc_point_homography(p3, homography)

#     logger.info("p0.x(), p0.y(), p1.x(), p1.y(), p2.x(), p2.y(), p3.x(), p3.y(), hp0.x(), hp0.y(), hp1.x(), hp1.y(), hp2.x(), hp2.y(), hp3.x(), hp3.y()")
#     logger.info("%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s", p0.x(), p0.y(), p1.x(), p1.y(), p2.x(), p2.y(), p3.x(), p3.y(), hp0.x(), hp0.y(), hp1.x(), hp1.y(), hp2.x(), hp2.y(), hp3.x(), hp3.y())

#     return hp0, hp1, hp2, hp3

# def calc_point_homography(p, mx):
#     v = QVector3D(p.x(), p.y(), 1)
#     v = v * mx

#     return QVector2D(v.x(), v.y())


# def calc_homography(p0, p1, p2, p3):
#     sx = p0.x() - p1.x() + p2.x() - p3.x()
#     sy = p0.y() - p1.y() + p2.y() - p3.y()

#     dx1 = p1.x() - p2.x()
#     dx2 = p3.x() - p2.x()
#     dy1 = p1.y() - p2.y()
#     dy2 = p3.y() - p2.y()

#     z = (dy1 * dx2) - (dx1 * dy2)
#     g = ((sx * dy1) - (sy * dx1)) / z
#     h = ((sy * dx2) - (sx * dy2)) / z

#     system = [
#         p3.x() * g - p0.x() + p3.x(),
#         p1.x() * h - p0.x() + p1.x(),
#         p0.x(),
#         p3.y() * g - p0.y() + p3.y(),
#         p1.y() * h - p0.y() + p1.y(),
#         p0.y(),
#         g,
#         h,
#     ]

#     mtx = QMatrix4x4()
#     mtx.row(0).setX(system[0])
#     mtx.row(0).setY(system[1])
#     mtx.row(0).setZ(system[2])
#     mtx.row(1).setX(system[3])
#     mtx.row(1).setY(system[4])
#     mtx.row(1).setZ(system[5])
#     mtx.row(2).setX(system[6])
#     mtx.row(2).setY(system[7])
#     mtx.row(2).setZ(1.0)
#     mtx.row(3).setZ(1.0)

#     return mtx






# # # 二次元の点を射影変換する
# # def calc_point_homography(p, mx):
# #     tmp = p.x() * mx.row(2).x() + p.y() * mx.row(2).y() + mx.row(2).z()
# #     tmpX = (p.x() * mx.row(0).x() + p.y() * mx.row(0).y() + mx.row(0).z()) / tmp
# #     tmpY = (p.x() * mx.row(1).x() + p.y() * mx.row(1).y() + mx.row(1).z()) / tmp

# #     return QVector2D( tmpX or 0, tmpY or 0 )


# # # 射影変換のパラメーターを取得する
# # # http://yaju3d.hatenablog.jp/entry/2013/08/04/152524
# # # http://yaju3d.hatenablog.jp/entry/2013/09/02/013609
# # def calc_homography_param(p1, p2, p3, p4):
# #     # 起点を原点にする
# #     sp1 = check_zero(p1-p1)
# #     sp2 = check_zero(p2-p1)
# #     sp3 = check_zero(p3-p1)
# #     sp4 = check_zero(p4-p1)

# #     X1 = check_zero(sp1.x())
# #     X2 = check_zero(sp2.x())
# #     X3 = check_zero(sp3.x())
# #     X4 = check_zero(sp4.x())
# #     Y1 = check_zero(sp1.y())
# #     Y2 = check_zero(sp2.y())
# #     Y3 = check_zero(sp3.y())
# #     Y4 = check_zero(sp4.y())
# #     x1 = check_zero(0)
# #     x2 = check_zero(0)
# #     x3 = check_zero(1)
# #     x4 = check_zero(1)
# #     y1 = check_zero(0)
# #     y2 = check_zero(1)
# #     y3 = check_zero(0)
# #     y4 = check_zero(1)

# #     # X座標
# #     tx = QMatrix4x4(X1, Y1, -X1 * x1, -Y1 * x1, X2, Y2, -X2 * x2, -Y2 * x2, X3, Y3, -X3 * x3, -Y3 * x3, X4, Y4, -X4 * x4, -Y4 * x4)
# #     tx = tx.inverted()[0]
# #     kx1 = tx.row(0).x() * x1 + tx.row(0).y() * x2 + tx.row(0).z() * x3 + tx.row(0).w() * x4
# #     kc1 = tx.row(0).x() + tx.row(0).y() + tx.row(0).z() + tx.row(0).w()
# #     kx2 = tx.row(1).x() * x1 + tx.row(1).y() * x2 + tx.row(1).z() * x3 + tx.row(1).w() * x4
# #     kc2 = tx.row(1).x() + tx.row(1).y() + tx.row(1).z() + tx.row(1).w()
# #     kx3 = tx.row(2).x() * x1 + tx.row(2).y() * x2 + tx.row(2).z() * x3 + tx.row(2).w() * x4
# #     kc3 = tx.row(2).x() + tx.row(2).y() + tx.row(2).z() + tx.row(2).w()
# #     kx4 = tx.row(3).x() * x1 + tx.row(3).y() * x2 + tx.row(3).z() * x3 + tx.row(3).w() * x4
# #     kc4 = tx.row(3).x() + tx.row(3).y() + tx.row(3).z() + tx.row(3).w()

# #     # Y座標
# #     ty = QMatrix4x4(X1, Y1, -X1 * y1, -Y1 * y1, X2, Y2, -X2 * y2, -Y2 * y2, X3, Y3, -X3 * y3, -Y3 * y3, X4, Y4, -X4 * y4, -Y4 * y4)
# #     ty = ty.inverted()[0]
# #     ky1 = ty.row(0).x() * y1 + ty.row(0).y() * y2 + ty.row(0).z() * y3 + ty.row(0).w() * y4
# #     kf1 = ty.row(0).x() + ty.row(0).y() + ty.row(0).z() + ty.row(0).w()
# #     ky2 = ty.row(1).x() * y1 + ty.row(1).y() * y2 + ty.row(1).z() * y3 + ty.row(1).w() * y4
# #     kf2 = ty.row(1).x() + ty.row(1).y() + ty.row(1).z() + ty.row(1).w()
# #     ky3 = ty.row(2).x() * y1 + ty.row(2).y() * y2 + ty.row(2).z() * y3 + ty.row(2).w() * y4
# #     kf3 = ty.row(2).x() + ty.row(2).y() + ty.row(2).z() + ty.row(2).w()
# #     ky4 = ty.row(3).x() * y1 + ty.row(3).y() * y2 + ty.row(3).z() * y3 + ty.row(3).w() * y4
# #     kf4 = ty.row(3).x() + ty.row(3).y() + ty.row(3).z() + ty.row(3).w()

# #     det_1 = 1 / check_zero(kc3 * (-kf4) - (-kf3) * kc4)

# #     param = [0 for x in range(8)]
# #     C = (-kf4 * det_1) * (kx3 - ky3) + (kf3 * det_1) * (kx4 - ky4)
# #     F = (-kc4 * det_1) * (kx3 - ky3) + (kc3 * det_1) * (kx4 - ky4)
# #     param[2] = C
# #     param[5] = F
# #     param[6] = kx3 - C * kc3
# #     param[7] = kx4 - C * kc4
# #     param[0] = kx1 - C * kc1
# #     param[1] = kx2 - C * kc2
# #     param[3] = ky1 - F * kf1
# #     param[4] = ky2 - F * kf2

# #     return param


# # # 射影変換のパラメーターを取得する
# # def calc_homography_param(p1, p2, p3, p4):
# #     # 起点を原点におく
# #     sp1 = (p1-p1)
# #     sp2 = (p2-p1)
# #     sp3 = (p3-p1)
# #     sp4 = (p4-p1)



    # # パラメーターを求める
    # param = calc_homography_param(p1, p2, p3, p4)

    # # 逆行列を求める
    # mx = QMatrix4x4(param[0], param[1], param[2], 0, param[3], param[4], param[5], 0, param[6], param[7], 1, 0, 0, 0, 0, 1)
    # mx = mx.inverted()[0]

    # # 点を射影変換する
    # hp1 = calc_point_homography(p1, mx)
    # hp2 = calc_point_homography(p2, mx)
    # hp3 = calc_point_homography(p3, mx)
    # hp4 = calc_point_homography(p4, mx)

    # logger.info("p1.x(), p1.y(), p2.x(), p2.y(), p3.x(), p3.y(), p4.x(), p4.y(), hp1.x(), hp1.y(), hp2.x(), hp2.y(), hp3.x(), hp3.y(), hp4.x(), hp4.y()")
    # logger.info("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s", p1.x(), p1.y(), p2.x(), p2.y(), p3.x(), p3.y(), p4.x(), p4.y(), hp1.x(), hp1.y(), hp2.x(), hp2.y(), hp3.x(), hp3.y(), hp4.x(), hp4.y())

























#     sp1 = (p1-p1)
#     sp2 = (p2-p1)
#     sp3 = (p3-p1)
#     sp4 = (p4-p1)

#     mat = [0 for x in range(9)]
#     # 射影変換の行列を求める
#     # mat[0][0]
#     mat[0] = (sp2.x()*sp1.y() - sp2.y()*sp1.x())*(sp4.x() - sp3.x()) - (sp4.x()*sp3.y() - sp4.y()*sp3.x())*(sp2.x() - sp1.x())
#     # mat[1][0]
#     mat[3] = (sp2.x()*sp1.y() - sp2.y()*sp1.x())*(sp4.y() - sp3.y()) - (sp4.x()*sp3.y() - sp4.y()*sp3.x())*(sp2.y() - sp1.y())
#     # mat[2][0]
#     mat[6] = (sp4.y() - sp3.y())*(sp2.x() - sp1.x()) + (sp3.x() - sp4.x())*(sp2.y() - sp1.y())
#     # mat[0][1]
#     mat[1] = (sp3.y()*sp1.x() - sp3.x()*sp1.y())*(sp4.x() - sp2.x()) - (sp4.y()*sp2.x() - sp4.x()*sp2.y())*(sp3.x() - sp1.x())
#     # mat[1][1]
#     mat[4] = (sp3.y()*sp1.x() - sp3.x()*sp1.y())*(sp4.y() - sp2.y()) - (sp4.y()*sp2.x() - sp4.x()*sp2.y())*(sp3.y() - sp1.y())
#     # mat[2][1]
#     mat[7] = (sp4.x() - sp2.x())*(sp3.y() - sp1.y()) - (sp4.y() - sp2.y())*(sp3.x() - sp1.x())
#     # mat[2][2]
#     mat[8] = sp4.x()*sp2.y() - sp4.y()*sp2.x() + sp2.x()*sp3.y() - sp2.y()*sp3.x() + sp3.x()*sp4.y() - sp3.y()*sp4.x()
#     # mat[0][2]
#     mat[2] = sp1.x() * mat[8]
#     # mat[1][2]
#     mat[5] = sp1.y() * mat[8]

#     # 逆行列を求める
#     invmat = calc_inv_mat3x3(mat)
#     logger.info("mat: %s", mat)
#     logger.info("invmat: %s", invmat)

#     # 3次元座標に変換した後、逆行列をかける
#     pp1 = calc_inv_mat3x3_mat3x1(invmat, [p1.x(), p1.y(), 1])
#     pp2 = calc_inv_mat3x3_mat3x1(invmat, [p2.x(), p2.y(), 1])
#     pp3 = calc_inv_mat3x3_mat3x1(invmat, [p3.x(), p3.y(), 1])
#     pp4 = calc_inv_mat3x3_mat3x1(invmat, [p4.x(), p4.y(), 1])

#     s1 = QVector2D(pp1[0], pp1[1])
#     s2 = QVector2D(pp2[0], pp2[1])
#     s3 = QVector2D(pp3[0], pp3[1])
#     s4 = QVector2D(pp4[0], pp4[1])

#     min_x = min(pp1[0], pp1[0], pp2[0], pp3[0])
#     min_y = min(pp1[1], pp1[1], pp2[1], pp3[1])
#     min_xy = QVector2D(min_x, min_y)

#     max_x = max(pp1[0], pp1[0], pp2[0], pp3[0])
#     max_y = max(pp1[1], pp1[1], pp2[1], pp3[1])
#     max_xy = QVector2D(max_x, max_y)

#     logger.info("[A], s1.x(), s1.y(), s2.x(), s2.y(), s3.x(), s3.y(), s4.x(), s4.y(), min_x, min_y, max_x, max_y")
#     logger.info("[A], %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s", s1.x(), s1.y(), s2.x(), s2.y(), s3.x(), s3.y(), s4.x(), s4.y(), min_x, min_y, max_x, max_y)

#     s1 -= s1
#     s2 -= s1
#     s3 -= s1
#     s4 -= s1

#     logger.info("[B], s1.x(), s1.y(), s2.x(), s2.y(), s3.x(), s3.y(), s4.x(), s4.y()")
#     logger.info("[B], %s,%s,%s,%s,%s,%s,%s,%s", s1.x(), s1.y(), s2.x(), s2.y(), s3.x(), s3.y(), s4.x(), s4.y())

#     s1 /= s4
#     s2 /= s4
#     s3 /= s4
#     s4 /= s4

#     logger.info("p1.x(), p1.y(), p2.x(), p2.y(), p3.x(), p3.y(), p4.x(), p4.y(), pp1[0], pp1[1], pp2[0], pp2[1], pp3[0], pp3[1], pp4[0], pp4[1], s1.x(), s1.y(), s2.x(), s2.y(), s3.x(), s3.y(), s4.x(), s4.y()")
#     logger.info("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s", p1.x(), p1.y(), p2.x(), p2.y(), p3.x(), p3.y(), p4.x(), p4.y(), pp1[0], pp1[1], pp2[0], pp2[1], pp3[0], pp3[1], pp4[0], pp4[1], s1.x(), s1.y(), s2.x(), s2.y(), s3.x(), s3.y(), s4.x(), s4.y())

#     return s1, s2, s3, s4


# # 3x3 と 3x1 の行列計算
# # http://apurvsaxena.blogspot.com/2012/09/matrix-multiplication-3x3-and-3x1.html
# def calc_inv_mat3x3_mat3x1(m3x3, m3x1):
#     rvec3 = [0 for x in range(3)]

#     rvec3[0] = m3x3[0]*m3x1[0] + m3x3[1]*m3x1[1] + m3x3[2]*m3x1[2] 
#     rvec3[1] = m3x3[3]*m3x1[0] + m3x3[4]*m3x1[1] + m3x3[5]*m3x1[2] 
#     rvec3[2] = m3x3[6]*m3x1[0] + m3x3[7]*m3x1[1] + m3x3[8]*m3x1[2] 

#     return rvec3

# # 3x3行列の逆行列の計算
# # http://apurvsaxena.blogspot.com/2012/09/matrix-inverse-3x3.html
# def calc_inv_mat3x3(mat):
#     invm = [0 for x in range(9)]    
#     invm[0] = mat[8] * mat[4] - mat[7] * mat[5]
#     invm[1] = mat[7] * mat[2] - mat[8] * mat[1]
#     invm[2] = mat[5] * mat[1] - mat[4] * mat[2]
#     invm[3] = mat[6] * mat[5] - mat[8] * mat[3]
#     invm[4] = mat[8] * mat[0] - mat[6] * mat[2]
#     invm[5] = mat[3] * mat[2] - mat[5] * mat[0]
#     invm[6] = mat[7] * mat[3] - mat[6] * mat[4]
#     invm[7] = mat[6] * mat[1] - mat[7] * mat[0]
#     invm[8] = mat[4] * mat[0] - mat[3] * mat[1] 

#     return invm


#     # diff = p4 - p1

#     # s1 = (p1-p1)
#     # s2 = (p2-p1)
#     # s3 = (p3-p1)
#     # s4 = (p4-p1)

#     # if diff.x() < diff.y():
#     #     diff2 = diff.x() / diff.y()
#     #     s1.setY( s1.y() * diff2 )
#     #     s2.setY( s2.y() * diff2 )
#     #     s3.setY( s3.y() * diff2 )
#     #     s4.setY( s4.y() * diff2 )

#     #     diff3 = 1 / diff.x()
#     #     s1 *= diff3
#     #     s2 *= diff3
#     #     s3 *= diff3
#     #     s4 *= diff3
#     # else:
#     #     diff2 = diff.y() / diff.x()
#     #     s1.setX( s1.x() * diff2 )
#     #     s2.setX( s2.x() * diff2 )
#     #     s3.setX( s3.x() * diff2 )
#     #     s4.setX( s4.x() * diff2 )

#     #     diff3 = 1 / diff.y()
#     #     s1 *= diff3
#     #     s2 *= diff3
#     #     s3 *= diff3
#     #     s4 *= diff3

#     # return s1, s2, s3, s4

#     # diff = p4 - p1

#     # s1 = s2 = s3 = s4 = 0

#     # if diff.x() < diff.y():
#     #     s1 = (p1-p1) / diff.x()
#     #     s2 = (p2-p1) / diff.x()
#     #     s3 = (p3-p1) / diff.x()
#     #     s4 = (p4-p1) / diff.x()

#     #     diff2 = diff.y() / diff.x()
#     #     s1.setY( s1.y() / diff2 )
#     #     s2.setY( s2.y() / diff2 )
#     #     s3.setY( s3.y() / diff2 )
#     #     s4.setY( s4.y() / diff2 )
#     # else:
#     #     s1 = (p1-p1) / diff.y()
#     #     s2 = (p2-p1) / diff.y()
#     #     s3 = (p3-p1) / diff.y()
#     #     s4 = (p4-p1) / diff.y()

#     #     diff2 = diff.x() / diff.y()
#     #     s1.setX( s1.x() / diff2 )
#     #     s2.setX( s2.x() / diff2 )
#     #     s3.setX( s3.x() / diff2 )
#     #     s4.setX( s4.x() / diff2 )

#     # return s1, s2, s3, s4

#     diff = p4 - p1

#     s1 = (p1-p1) / diff
#     s2 = (p2-p1) / diff
#     s3 = (p3-p1) / diff
#     s4 = (p4-p1) / diff

#     return s1, s2, s3, s4



# ベジェ曲線の任意の範囲を切り分ける処理
# def calc_bezier_split_range(x1v, y1v, x2v, y2v, t1, t2):
#     x1 = 0
#     y1 = 0
#     x2 = x1v/127.0
#     y2 = y1v/127.0
#     x3 = x2v/127.0
#     y3 = y2v/127.0
#     x4 = 1
#     y4 = 1

#     t1p = 1-t1
#     t2p = 1-t2
#     nx1 = t1p*t1p*t1p*x1 + 3*t1*t1p*t1p*x2 + 3*t1*t1*t1p*x3 + t1*t1*t1*x4
#     ny1 = t1p*t1p*t1p*y1 + 3*t1*t1p*t1p*y2 + 3*t1*t1*t1p*y3 + t1*t1*t1*y4
#     nx2 = t1p*t1p*(t2p*x1+t2*x2) + 2*t1p*t1*(t2p*x2+t2*x3) + t1*t1*(t2p*x3+t2*x4)
#     ny2 = t1p*t1p*(t2p*y1+t2*y2) + 2*t1p*t1*(t2p*y2+t2*y3) + t1*t1*(t2p*y3+t2*y4)
#     nx3 = t2p*t2p*(t1p*x1+t1*x2) + 2*t2p*t2*(t1p*x2+t1*x3) + t2*t2*(t1p*x3+t1*x4)
#     ny3 = t2p*t2p*(t1p*y1+t1*y2) + 2*t2p*t2*(t1p*y2+t1*y3) + t2*t2*(t1p*y3+t1*y4)
#     nx4 = t2p*t2p*t2p*x1 + 3*t2*t2p*t2p*x2 + 3*t2*t2*t2p*x3 + t2*t2*t2*x4
#     ny4 = t2p*t2p*t2p*y1 + 3*t2*t2p*t2p*y2 + 3*t2*t2*t2p*y3 + t2*t2*t2*y4

#     return [round_bezier_mmd(QVector2D(nx1, ny1)), round_bezier_mmd(QVector2D(nx2, ny2)), round_bezier_mmd(QVector2D(nx3, ny3)), round_bezier_mmd(QVector2D(nx4, ny4))]


def round_bezier_mmd(target):
    # 一旦整数部にまで持ち上げる
    t2 = target * 1000000 * 127

    # 偶数丸めなので、整数部で丸めた後元に戻す
    t2.setX(round(round(t2.x(), -6) / 1000000))
    t2.setY(round(round(t2.y(), -6) / 1000000))

    logger.debug("target: %s, t2: %s", target, t2)

    return t2


# 補間曲線を求める
# http://d.hatena.ne.jp/edvakf/20111016/1318716097
def calc_interpolate_bezier(x1v, y1v, x2v, y2v, start, end, now):
    if (now - start) == 0 or (end - start) == 0:
        return 0, 0
        
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
