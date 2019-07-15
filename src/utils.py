# -*- coding: utf-8 -*-
# ユーティリティ系
# 
import logging
import copy
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
            if frameno == 605:
                logger.debug("calc_bone_by_complement 同一キーあり: %s, %s", frameno, bone_name)
            # 同一フレームのキーがある場合、それを返す
            fillbf = copy.deepcopy(bf)
            return fillbf
        elif bf.frame > frameno:
            if frameno == 605:
                logger.debug("calc_bone_by_complement 同一キーなし: %s, %s", frameno, bone_name)
            # 同一フレームのキーがない場合、前のキーIDXを0に見立てて、その間の補間曲線を埋める
            fillbf.name = bf.name
            fillbf.format_name = bone_name
            fillbf.frame = frameno
            # 実際に登録はしない
            fillbf.key = False

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
                _, rn = calc_interpolate_bezier(comp[R_x1_idxs[3]], comp[R_y1_idxs[3]], comp[R_x2_idxs[3]], comp[R_y2_idxs[3]], prev_bf.frame, bf.frame, fillbf.frame)
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
                _, xn = calc_interpolate_bezier(comp[0], comp[4], comp[8], comp[12], prev_bf.frame, bf.frame, fillbf.frame)
                # Y移動補間曲線
                _, yn = calc_interpolate_bezier(comp[16], comp[20], comp[24], comp[28], prev_bf.frame, bf.frame, fillbf.frame)
                # Z移動補間曲線
                _, zn = calc_interpolate_bezier(comp[32], comp[36], comp[40], comp[44], prev_bf.frame, bf.frame, fillbf.frame)

                fillbf.position.setX(prev_bf.position.x() + (( bf.position.x() - prev_bf.position.x()) * xn))
                fillbf.position.setY(prev_bf.position.y() + (( bf.position.y() - prev_bf.position.y()) * yn))
                fillbf.position.setZ(prev_bf.position.z() + (( bf.position.z() - prev_bf.position.z()) * zn))
                # logger.debug("key: %s, n: %s, xn: %s, yn: %s, zn: %s, xa: %s", k, prev_frame + n, xn, yn, zn, ( bf.position.x() - prev_bf.position.x()) * xn )
                # logger.debug("position: prev: %s, fill: %s ", prev_bf.position, fillbf.position )
            else:
                fillbf.position = copy.deepcopy(prev_bf.position)
                # logger.debug("position stop: %s,%s prev: %s, fill: %s ", prev_frame + n, k, prev_bf.position, bf.position )
            
            if is_calc_complement:
                # 指定されたフレーム直前のキーを再設定
                prev_bf = frames[bone_name][bidx - 1]

                # 補間曲線を計算する場合、現在の補間曲線から分割する
                next_x1v = bf.complement[R_x1_idxs[3]]
                next_y1v = bf.complement[R_y1_idxs[3]]
                next_x2v = bf.complement[R_x2_idxs[3]]
                next_y2v = bf.complement[R_y2_idxs[3]]
                
                # # ベジェ曲線の実値を求める
                # rx, rn = calc_interpolate_bezier(next_x1v, next_y1v, next_x2v, next_y2v, prev_bf.frame, bf.frame, fillbf.frame)
                # # ベジェ曲線の接線を求める
                # rx, v = calc_bezier_line_tangent(next_x1v, next_y1v, next_x2v, next_y2v, prev_bf.frame, bf.frame, fillbf.frame)
                # ベジェ曲線を分割して新しい制御点を求める
                before_bz, after_bz = calc_bezier_split(next_x1v, next_y1v, next_x2v, next_y2v, prev_bf.frame, bf.frame, fillbf.frame, bone_name)

                logger.debug("bone: %s, prev: %s, bf: %s, fillbf: %s", bone_name, prev_bf.frame, bf.frame, fillbf.frame)
                if 2440 <= fillbf.frame <= 2440:
                    logger.debug("next_x1v: %s, next_y1v: %s, next_x2v: %s, next_y2v: %s", next_x1v, next_y1v, next_x2v, next_y2v)
                    logger.debug("before_bz: %s", before_bz)
                    logger.debug("after_bz: %s", after_bz)

                # オリジナルの補間曲線として先の元々の補間曲線を保持しておく
                fillbf.org_complement = copy.deepcopy(bf.org_complement)
                # 補間曲線を元々の補間曲線からコピーする
                fillbf.complement = copy.deepcopy(bf.complement)

                # 分割の始点は、前半のB
                fillbf.complement[R_x1_idxs[0]] = fillbf.complement[R_x1_idxs[1]] = fillbf.complement[R_x1_idxs[2]] = fillbf.complement[R_x1_idxs[3]] = int(before_bz[1].x())
                fillbf.complement[R_y1_idxs[0]] = fillbf.complement[R_y1_idxs[1]] = fillbf.complement[R_y1_idxs[2]] = fillbf.complement[R_y1_idxs[3]] = int(before_bz[1].y())

                # 分割の終点は、後半のC
                fillbf.complement[R_x2_idxs[0]] = fillbf.complement[R_x2_idxs[1]] = fillbf.complement[R_x2_idxs[2]] = fillbf.complement[R_x2_idxs[3]] = int(before_bz[2].x())
                fillbf.complement[R_y2_idxs[0]] = fillbf.complement[R_y2_idxs[1]] = fillbf.complement[R_y2_idxs[2]] = fillbf.complement[R_y2_idxs[3]] = int(before_bz[2].y())

                # 今回の始点は、後半のB
                bf.complement[R_x1_idxs[0]] = bf.complement[R_x1_idxs[1]] = bf.complement[R_x1_idxs[2]] = bf.complement[R_x1_idxs[3]] = int(after_bz[1].x())
                bf.complement[R_y1_idxs[0]] = bf.complement[R_y1_idxs[1]] = bf.complement[R_y1_idxs[2]] = bf.complement[R_y1_idxs[3]] = int(after_bz[1].y())

                # 今回の終点は、後半のC
                bf.complement[R_x2_idxs[0]] = bf.complement[R_x2_idxs[1]] = bf.complement[R_x2_idxs[2]] = bf.complement[R_x2_idxs[3]] = int(after_bz[2].x())
                bf.complement[R_y2_idxs[0]] = bf.complement[R_y2_idxs[1]] = bf.complement[R_y2_idxs[2]] = bf.complement[R_y2_idxs[3]] = int(after_bz[2].y())

                if 2440 <= fillbf.frame <= 2440:
                    logger.debug("fillbf.complement[R_x2_idxs[0]]: %s, fillbf.complement[R_y2_idxs[0]]: %s", fillbf.complement[R_x2_idxs[0]], fillbf.complement[R_y2_idxs[0]])
                    logger.debug("bf.complement[R_x1_idxs[0]]: %s, bf.complement[R_y1_idxs[0]]: %s", bf.complement[R_x1_idxs[0]], bf.complement[R_y1_idxs[0]])

            return fillbf

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

    t = (now - start) / (end - start)

    # return calc_bezier_split_range(x1v, y1v, x2v, y2v, 0, t), calc_bezier_split_range(x1v, y1v, x2v, y2v, t, 1)

    A = QVector2D(0, 0)
    B = QVector2D(x1v/127, y1v/127)
    C = QVector2D(x2v/127, y2v/127)
    D = QVector2D(1, 1)

    E = (1-t)*A + t*B
    F = (1-t)*B + t*C
    G = (1-t)*C + t*D
    H = (1-t)*E + t*F
    I = (1-t)*F + t*G
    J = (1-t)*H + t*I

    # 新たな4つのベジェ曲線の制御点は、A側がAEHJ、C側がJIGDとなる。
    before_diff = (J-A)
    after_diff = (D-J)

    bA = (A / before_diff)
    bE = (E / before_diff)
    bH = (H / before_diff)
    bJ = (J / before_diff)

    aJ = ((J-J) / after_diff)
    aI = ((I-J) / after_diff)
    aG = ((G-J) / after_diff)
    aD = ((D-J) / after_diff)

    bA2 = round_bezier_mmd(bA)
    bE2 = round_bezier_mmd(bE)
    bH2 = round_bezier_mmd(bH)
    bJ2 = round_bezier_mmd(bJ)
    aJ2 = round_bezier_mmd(aJ)
    aI2 = round_bezier_mmd(aI)
    aG2 = round_bezier_mmd(aG)
    aD2 = round_bezier_mmd(aD)
    
    # error_file_logger.info("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s", bone_name,start,now,end,t,x1v,y1v,x2v,y2v,A.x(),A.y(),E.x(),E.y(),H.x(),H.y(),J.x(),J.y(),I.x(),I.y(),G.x(),G.y(),D.x(),D.y(),before_diff.x(),before_diff.y(),after_diff.x(),after_diff.y(),bA.x(),bA.y(),bE.x(),bE.y(),bH.x(),bH.y(),bJ.x(),bJ.y(),aJ.x(),aJ.y(),aI.x(),aI.y(),aG.x(), aG.y(),aD.x(),aD.y(),bA6.x(),bA6.y(),bE6.x(),bE6.y(),bH6.x(),bH6.y(),bJ6.x(),bJ6.y(),aJ6.x(),aJ6.y(),aI6.x(),aI6.y(),aG6.x(),aG6.y(),aD6.x(),aD6.y() ,bA2.x(),bA2.y(),bE2.x(),bE2.y(),bH2.x(),bH2.y(),bJ2.x(),bJ2.y(),aJ2.x(),aJ2.y(),aI2.x(),aI2.y(),aG2.x(),aG2.y(),aD2.x(),aD2.y())

    return [bA2, bE2, bH2, bJ2], [aJ2, aI2, aG2, aD2]

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

    return x, y
