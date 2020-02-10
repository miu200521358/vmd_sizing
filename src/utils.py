# -*- coding: utf-8 -*-
# ユーティリティ系
# 
import re
import logging
import copy
from datetime import datetime
from math import atan2, acos, asin, cos, sin, degrees, isnan, isclose, sqrt, pi, isinf
from statistics import median, mean
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
        print("{0} <{1}>".format(text, datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')))
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

# 指定されたクォータニオンの指定方向のみの回転量
# http://gamemakerlearning.blog.fc2.com/blog-entry-205.html
# http://www.sousakuba.com/Programming/gs_two_vector_angle.html
def calc_split_qq(target_qq, bone_name):
    # 回転角度
    target_degree = degrees(2 * acos(min(1, max(-1, target_qq.scalar()))))
    # 回転軸
    target_axis = target_qq.vector().normalized()
    
    # グローバル軸
    global_x_axis = QVector3D(1, 0, 0)
    global_y_axis = QVector3D(0, 1, 0)
    global_z_axis = QVector3D(0, 0, 1)

    # 各軸の成分回転量
    part_x_degree, part_x_dot = calc_part_degree(target_qq, target_degree, target_axis, global_x_axis)
    part_y_degree, part_y_dot = calc_part_degree(target_qq, target_degree, target_axis, global_y_axis)
    part_z_degree, part_z_dot = calc_part_degree(target_qq, target_degree, target_axis, global_z_axis)

    # 各ローカル軸に沿った回転
    part_x_qq = QQuaternion.fromAxisAndAngle(global_x_axis, part_x_degree)
    part_y_qq = QQuaternion.fromAxisAndAngle(global_y_axis, part_y_degree)
    part_z_qq = QQuaternion.fromAxisAndAngle(global_z_axis, part_z_degree)

    return part_x_qq, part_y_qq, part_z_qq, part_x_degree, part_y_degree, part_z_degree

# 処理対称軸から余計な回転量を抽出する
def calc_delegate_extra_qq(target_qq, target_axis, local_axis, bone_name, fno):
    # 回転角度
    target_degree = degrees(2 * acos(min(1, max(-1, target_qq.scalar()))))
    # 任意軸の回転に変換
    target_local_qq = QQuaternion.fromAxisAndAngle(target_axis, target_degree)
    # 回転軸
    target_axis = (target_qq.vector() / sin(acos(min(1, max(-1, target_qq.scalar()))))).normalized()

    # Y-Z平面上の回転量（X軸周りの回転量）
    part_x_degree, part_x_dot = calc_part_degree(target_qq, target_degree, target_axis, QVector3D(0, 1, 1))
    # X-Z平面上の回転量（Y軸周りの回転量）
    part_y_degree, part_y_dot = calc_part_degree(target_qq, target_degree, target_axis, QVector3D(1, 0, 1))
    # X-Y平面上の回転量（Z軸周りの回転量）
    part_z_degree, part_z_dot = calc_part_degree(target_qq, target_degree, target_axis, QVector3D(1, 1, 0))

    # 最も大きい（差の小さい）内積を採用
    part_axis = ""
    part_degree = 0
    part_dot = 0
    for deg, dot, axis in [(part_x_degree, part_x_dot, "x"), (part_y_degree, part_y_dot, "y"), (part_z_degree, part_z_dot, "z")]:
        if dot > part_dot:
            part_axis = axis
            part_dot = dot
            part_degree = deg
    
    # if "左" in bone_name:
    #     part_degree *= -1

    # logger.info("extra fno: %s, xdot: %s, xdeg: %s", fno, part_x_dot, part_x_degree)
    # logger.info("extra fno: %s, ydot: %s, ydeg: %s", fno, part_y_dot, part_y_degree)
    # logger.info("extra fno: %s, zdot: %s, zdeg: %s", fno, part_z_dot, part_z_degree)
    # logger.info("extra fno: %s, axis: %s, dot: %s, deg: %s", fno, part_axis, part_dot, part_degree)

    part_qq = QQuaternion.fromAxisAndAngle(local_axis, part_degree)

    return part_qq, part_degree


# http://yuki-koyama.hatenablog.com/entry/2013/01/19/163421
def calc_part_degree(target_qq, target_degree, target_axis, one_vec3):
    # 任意軸
    one_axis = (target_axis * one_vec3).normalized()
    # 任意軸周りのqq
    one_qq = QQuaternion.fromAxisAndAngle(one_axis, target_degree)
    # 軸周りベクトルとの内積
    one_dot = QQuaternion.dotProduct(target_qq, one_qq)
    # 角度
    one_theta = acos(min(1, max(-1, one_dot)))
    # 任意軸周りの回転量
    one_degree = degrees(one_theta)
    # # 変化量を加味した分離回転量
    # if one_dot > 0:
    #     part_qq = QQuaternion.slerp(target_qq, one_qq, one_theta)
    # else:
    #     # 負数の場合、短い距離を選ぶように指定
    #     part_qq = QQuaternion.slerp(target_qq, -one_qq, one_theta)
    # # 内積から求めた角度
    # part_cos_theta = one_dot / ( local_axis.length() * one_axis.length() )
    # # degree に変換
    # part_degree = degrees(acos(min(1, max(-1, part_cos_theta))))
    # # # 内積から求めた角度
    # # part_degree = target_degree * one_dot
    # # 指定ローカル軸に合わせたqq
    # part_qq = QQuaternion.fromAxisAndAngle(local_axis, one_degree)
    # # 任意軸周りの回転量
    # one_degree = degrees(2 * acos(min(1, max(-1, one_qq.scalar()))))
    # part_degree = degrees(2 * acos(min(1, max(-1, one_dot))))
    # # 1方向のベクトルの長さ
    # part_degree = target_degree * one_radian

    return one_degree, one_dot

# v2にマッチするようにv1を回転させるようなクォータニオン
# http://www.opengl-tutorial.org/jp/intermediate-tutorials/tutorial-17-quaternions/#二つのベクトル間の回転の見つけ方
def calc_match_qq(v1, v2):
    v1 = v1.normalized()
    v2 = v2.normalized()

    # 元々のqqと指定ローカル軸qqの内積
    cos_theta = QVector3D.dotProduct(v1, v2)

    if cos_theta < -1.0001:
        # ベクトルが反対方向を向いている特殊なケース
        # 単位回転軸はないので、垂直なものを見つけます。
        rotation_axis = QVector3D.crossProduct(QVector3D(0, 0, 1), v1)
        if rotation_axis.lengthSquared() < 0.01:
            # 平行なのでもう一度計算
            rotation_axis = QVector3D.crossProduct(QVector3D(1, 0, 0), rotation_axis)
        
        return QQuaternion.fromAxisAndAngle(rotation_axis, 180)
    
    rotation_axis = QVector3D.crossProduct(v1, v2)

    s = sqrt((1 + cos_theta) * 2)
    invs = 1 / s

    local_qq = QQuaternion( s * 0.5, rotation_axis.x() * invs, rotation_axis.y() * invs, rotation_axis.z() * invs )
    local_degree = degrees(2 * acos(min(1, max(-1, local_qq.scalar()))))

    return local_qq, local_degree

# 行列をクォータニオンに変化する
# https://www.euclideanspace.com/maths/geometry/rotations/conversions/matrixToQuaternion/
def calc_mat_2_qq(mat):
    a = [[mat.row(0).x(), mat.row(0).y(), mat.row(0).z(), mat.row(0).w()]
        , [mat.row(1).x(), mat.row(1).y(), mat.row(1).z(), mat.row(1).w()]
        , [mat.row(2).x(), mat.row(2).y(), mat.row(2).z(), mat.row(2).w()]
        , [mat.row(3).x(), mat.row(3).y(), mat.row(3).z(), mat.row(3).w()]]
    q = QQuaternion()
    
    # I removed + 1
    trace = a[0][0] + a[1][1] + a[2][2]
    # I changed M_EPSILON to 0
    if  trace > 0:
        s = 0.5 / sqrt(trace+ 1)
        q.setScalar( 0.25 / s )
        q.setX(( a[2][1] - a[1][2] ) * s)
        q.setY(( a[0][2] - a[2][0] ) * s)
        q.setZ(( a[1][0] - a[0][1] ) * s)
    else:
        if a[0][0] > a[1][1] and a[0][0] > a[2][2]:
            s = 2 * sqrt( 1 + a[0][0] - a[1][1] - a[2][2])
            q.setScalar((a[2][1] - a[1][2] ) / s)
            q.setX(0.25 * s)
            q.setY((a[0][1] + a[1][0] ) / s)
            q.setZ((a[0][2] + a[2][0] ) / s)
        elif a[1][1] > a[2][2]:
            s = 2 * sqrt( 1 + a[1][1] - a[0][0] - a[2][2])
            q.setScalar((a[0][2] - a[2][0] ) / s)
            q.setX((a[0][1] + a[1][0] ) / s)
            q.setY(0.25 * s)
            q.setZ((a[1][2] + a[2][1] ) / s)
        else:
            s = 2 * sqrt( 1 + a[2][2] - a[0][0] - a[1][1] )
            q.setScalar((a[1][0] - a[0][1] ) / s)
            q.setX((a[0][2] + a[2][0] ) / s)
            q.setY((a[1][2] + a[2][1] ) / s)
            q.setZ(0.25 * s)

    return q

# 子の回転を親に分散させる
# https://ch.nicovideo.jp/HOPHEAD/blomaga/ar805999 MMDではYXZ型
def delegate_qq(model, frames, bf, arm2root_links, arm2root_indexes, delegate_dic, target_qq, delegate_qq, target_local_x_axis, delegate_local_x_axis, fno, test_param):
    target_result_qq = copy.deepcopy(target_qq)
    delegate_result_qq = copy.deepcopy(delegate_qq)
    v_qq_dic = {}

    target_degree = degrees(2 * acos(min(1, max(-1, target_qq.scalar()))))
    delegate_degree = degrees(2 * acos(min(1, max(-1, delegate_qq.scalar()))))

    target_local_qq = QQuaternion.fromAxisAndAngle(target_local_x_axis, target_degree)
    delegate_local_qq = QQuaternion.fromAxisAndAngle(delegate_local_x_axis, delegate_degree)

    # 垂直なローカルZ
    local_z_axis = QVector3D(0, 0, -1)

    # ローカルY軸 
    delegate_local_y_axis = QVector3D.crossProduct(delegate_local_x_axis, local_z_axis).normalized()
    target_local_y_axis = QVector3D.crossProduct(target_local_x_axis, local_z_axis).normalized()

    # ローカルZ軸
    delegate_local_z_axis = QVector3D.crossProduct(delegate_local_x_axis, delegate_local_y_axis).normalized()
    target_local_z_axis = QVector3D.crossProduct(target_local_x_axis, target_local_y_axis).normalized()

    if delegate_dic["is_elbow"] == True:
        elbow_initial_axis = delegate_local_x_axis  # ひじ初期向き
        elbow_global_axis = QVector3D(1, 0, 0)      # ひじグローバル向き

        elbow_all_mat = QMatrix4x4()
        elbow_all_mat.rotate(delegate_qq)            # ひじの回転量
        # ひじベクトル
        elbow_original_vector = elbow_all_mat * elbow_initial_axis

        # ひじからX成分を除去する
        elbow_yz_qq, elbow_yz_degree = calc_match_qq(elbow_initial_axis, elbow_original_vector)

        # YZ回転からZ成分だけ取り出す -------------

        # 除去されたひじX成分
        elbow_yz_mat = QMatrix4x4()
        elbow_yz_mat.rotate(elbow_yz_qq)    # ひじYZの回転量
        elbow_x_qq = calc_mat_2_qq(elbow_all_mat * elbow_yz_mat.inverted()[0])

        elbow_local_all_qq, elbow_local_all_degree = calc_match_qq(elbow_initial_axis, elbow_global_axis)
        elbow_local_all_mat = QMatrix4x4()
        elbow_local_all_mat.rotate(elbow_local_all_qq)

        elbow_global_all_qq, elbow_global_all_degree = calc_match_qq(elbow_global_axis, elbow_initial_axis)
        elbow_global_all_mat = QMatrix4x4()
        elbow_global_all_mat.rotate(elbow_global_all_qq)

        elbow_local_mat = QMatrix4x4()
        elbow_local_mat.rotate(elbow_yz_qq)
        elbow_local_qq = calc_mat_2_qq(elbow_local_mat * elbow_local_all_mat)

        # <--- ここまでで肘ローカルに回転を持ってこれている。

        #  YZ回転からZ成分を抽出する。
        p_mat = QMatrix4x4()
        p_mat.rotate(elbow_local_all_qq)
        p_mat.translate(elbow_global_axis)
        p = (p_mat * QVector3D())
        p.setZ(0)
        p.normalized()

        elbow_local_z_qq, elbow_local_z_degree = calc_match_qq(elbow_global_axis, p)

        elbow_z_mat = QMatrix4x4()
        elbow_z_mat.rotate(elbow_local_z_qq)
        elbow_z_qq = calc_mat_2_qq(elbow_z_mat * elbow_global_all_mat)

        # YZ回転からY成分だけ取り出す。
        elbow_yz_mat = QMatrix4x4()
        elbow_yz_mat.rotate(elbow_yz_qq)
        elbow_z_mat = QMatrix4x4()
        elbow_z_mat.rotate(elbow_z_qq)
        elbow_y_mat = elbow_yz_mat * elbow_z_mat.inverted()[0]
        elbow_y_qq = calc_mat_2_qq(elbow_y_mat)

        # X成分の捻れが混入したので、XY回転からYZ回転を取り出すことでXキャンセルをかける。
        m = QMatrix4x4()
        m.translate(elbow_initial_axis)
        m = m * elbow_y_mat
        v = m * QVector3D()
        v.normalized()
        elbow_x_qq = calc_match_qq(elbow_initial_axis, v)

        # 腕
        target_result_qq = target_qq

        # ひじ
        delegate_result_qq = elbow_y_qq

        return target_result_qq, delegate_result_qq, v_qq_dic
    else:
        # 処理対象の余分な角度
        delegate_work_qq = delegate_local_qq

        if delegate_dic["is_twist"] == True:
            # 捩りの場合は子である捩りの回転を加算する
            delegate_work_qq = delegate_work_qq * target_qq

        # 余計な回転量
        delegate_extra_degree = degrees(2 * acos(min(1, max(-1, delegate_work_qq.scalar()))))

        # 余計な回転量を委譲先のローカル軸に合わせた回転量
        target_local_extra_qq, target_local_extra_degree = calc_delegate_extra_qq(delegate_qq, delegate_local_x_axis, target_local_x_axis, delegate_dic["delegate"], fno)

        if delegate_dic["is_twist"] == True:
            # 委譲元が親である場合
            target_extra_qq = target_local_extra_qq * target_qq.inverted()

            # 委譲先に、余分な角度を加算する
            target_result_qq = target_extra_qq * target_qq

            # 委譲元は、余分な角度を除く
            delegate_result_qq = delegate_qq * target_local_extra_qq.inverted()
        else:
            # 委譲元が親でない場合
            target_extra_qq = target_local_extra_qq

            # 委譲先に、余分な角度を加算する
            target_result_qq = target_qq * target_extra_qq

            # 委譲元は、余分な角度を除く
            delegate_result_qq = target_extra_qq.inverted() * delegate_qq

            logger.debug(delegate_result_qq)

    return target_result_qq, delegate_result_qq, v_qq_dic

# 委譲リスト
DELEGATE_BORN_LIST = {
    "左手首": [
        {"target":"左腕", "delegate": "左ひじ", "is_twist": False, "is_elbow": True}
        # {"target":"左ひじ", "delegate": "左手首", "is_twist": False, "is_elbow": False}
        # , {"target":"左腕", "delegate": "左ひじ", "is_twist": False, "is_elbow": False}
        # # , {"target":"左肩", "delegate": "左腕", "is_twist": False, "is_elbow": False}
        # , {"target":"左手捩", "delegate": "左ひじ", "is_twist": True, "is_elbow": False}
        # , {"target":"左腕捩", "delegate": "左腕", "is_twist": True, "is_elbow": False}
    ], 
    "右手首": [
        {"target":"右腕", "delegate": "右ひじ", "is_twist": False, "is_elbow": True}
        # {"target":"右ひじ", "delegate": "右手首", "is_twist": False, "is_elbow": False}
        # , {"target":"右腕", "delegate": "右ひじ", "is_twist": False, "is_elbow": False}
        # # , {"target":"右肩", "delegate": "右腕", "is_twist": False, "is_elbow": False}
        # , {"target":"右手捩", "delegate": "右ひじ", "is_twist": True, "is_elbow": False}
        # , {"target":"右腕捩", "delegate": "右腕", "is_twist": True, "is_elbow": False}
    ]
}

def get_local_axis_4delegate_qq(model, bone):
    if bone.fixed_axis != QVector3D():
        # 軸制限がある場合、それを優先させる
        x_axis = bone.fixed_axis
        z_axis = bone.local_z_vector
    else:
        from_pos = model.bones[bone.name].position
        if bone.tail_position != QVector3D():
            # 表示先が相対パスの場合、保持
            to_pos = from_pos + bone.tail_position
        elif bone.tail_index >= 0 and bone.tail_index in model.bone_indexes and model.bones[model.bone_indexes[bone.tail_index]].position != bone.position:
            # 表示先が指定されているの場合、保持
            to_pos = model.bones[model.bone_indexes[bone.tail_index]].position
        else:
            # 表示先がない場合、とりあえず子ボーンのどれかを選択
            for b in model.bones:
                if b.parent_index == bone.index and model.bones[b.index].position != bone.position:
                    to_pos = model.bones[b.index].position
                    break

        # 軸制限の指定が無い場合、子の方向
        x_axis = (to_pos - from_pos).normalized()

    return x_axis

# 指定ボーンの最終的なローカル軸の向きを返す
def calc_local_axis(model, bone_name, is_rotation=False):
    # そのボーンの最終的な向き先を取得
    links, indexes = model.create_link_2_top_all(bone_name)

    # 行列生成(センター起点)
    _, _, _, org_matrixs, org_global_3ds = create_matrix_global(model, links, {}, VmdBoneFrame())

    # 該当ボーンの局所座標系変換
    mat = QMatrix4x4()

    # ローカル座標軸を求める為の行列
    for n, (v, l) in enumerate(zip(org_matrixs, reversed(links))):
        if n == 0:
            # 最初は行列
            mat = copy.deepcopy(org_matrixs[0])
        else:
            # 2番目以降は行列をかける
            mat *= copy.deepcopy(org_matrixs[n])
        
        # ローカル軸が設定されていない場合、設定        
        if n > 0:
            local_x_matrix = QMatrix4x4()
            local_axis_qq = QQuaternion()

            if l.local_x_vector == QVector3D():
                local_axis = l.position - links[len(links) - n].position

                # if direction in ["左", "右"]:
                #     direction_x = 1 if direction == "左" else -1
                #     local_axis_qq = QQuaternion.rotationTo(QVector3D(direction_x, 0, 0), local_axis)
                #     # local_axis_qq = QQuaternion.fromDirection(QVector3D(direction_x, 0, 0), local_axis.normalized())
                # else:
                local_axis_qq = QQuaternion.fromDirection(local_axis.normalized(), QVector3D(0, 0, 1))
            else:
                local_axis_qq = QQuaternion.fromDirection(l.local_x_vector.normalized(), QVector3D(0, 0, 1))

            local_x_matrix.rotate(local_axis_qq)           
        
            mat *= local_x_matrix

    # ワールド座標系から注目ノードの局所座標系への変換
    inv_coord = mat.inverted()[0]

    # とりあえず自身のボーンからの向き先を取得
    axis = calc_local_axis_pos(model, bone_name)

    local_axis = (inv_coord * axis).normalized()

    return local_axis

def calc_local_axis_pos(model, bone_name):
    from_pos = QVector3D()
    to_pos = QVector3D()

    if bone_name in model.bones:
        fv = model.bones[bone_name]
        from_pos = fv.position
        if fv.tail_position != QVector3D():
            # 表示先が相対パスの場合、保持
            to_pos = from_pos + fv.tail_position
        elif fv.tail_index >= 0:
            to_pos = model.bones[model.bone_indexes[fv.tail_index]].position
 
    # とりあえず自身のボーンからの向き先を取得
    axis = (to_pos - from_pos).normalized()

    return axis


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



# 回転用ベジェ曲線 - 指定された3点を通るベジェ曲線を返す
def calc_smooth_bezier_rot(x1, y1r, x2, y2r, x3, y3r, offset, is_comp_circle):

    if y1r == y2r == y3r:
        # 回転量が同じ場合、線形補間      
        return False, True, [QVector2D(0, 0), QVector2D(20, 20), QVector2D(107, 107), QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)]  

    t = (x2 - x1) / (x3 - x1)

    if (x1 >= x2 or x1 >= x3 or x2 >= x3) or t <= 0 or t >= 1:
        # 正常に計算できない場合、計算対象外
        return False, False, \
            [QVector2D(0, 0), QVector2D(20, 20), QVector2D(107, 107), QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)]

    y1e = y1r.toEulerAngles()
    y1e = QVector3D(round(y1e.x(), 1), round(y1e.y(), 1), round(y1e.z(), 1))
    y2e = y2r.toEulerAngles()
    y2e = QVector3D(round(y2e.x(), 1), round(y2e.y(), 1), round(y2e.z(), 1))
    y3e = y3r.toEulerAngles()
    y3e = QVector3D(round(y3e.x(), 1), round(y3e.y(), 1), round(y3e.z(), 1))

    # 各回転の補間曲線
    xresult, is_xfit, xbz = calc_smooth_bezier_pos(x1, y1e.x(), x2, y2e.x(), x3, y3e.x(), offset, is_comp_circle)
    yresult, is_yfit, ybz = calc_smooth_bezier_pos(x1, y1e.y(), x2, y2e.y(), x3, y3e.y(), offset, is_comp_circle)
    zresult, is_zfit, zbz = calc_smooth_bezier_pos(x1, y1e.z(), x2, y2e.z(), x3, y3e.z(), offset, is_comp_circle)

    offset_bz = [QVector2D(0, 0), QVector2D(20, 20), QVector2D(107, 107), QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)]        

    if is_xfit == is_yfit == is_zfit:
        # ③軸とも補間曲線の範囲内である場合

        # 半径は3点間の距離の最長の半分
        r = max(y1e.distanceToPoint(y2e), y1e.distanceToPoint(y3e),  y2e.distanceToPoint(y3e)) / 2

        if round(r, 3) == 0:
            # 半径が取れなかった場合、そもそもまったく移動がないので、線分移動
            return True, True, \
                [QVector2D(0, 0), QVector2D(20, 20), QVector2D(107, 107), QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)]

        # 3点を通る球体の原点を求める
        c, radius = calc_sphere_center(y1e, y2e, y3e, r)

        if round(radius, 3) == 0:
            # 半径がない場合、線形補間
            return True, True, \
                [QVector2D(0, 0), QVector2D(20, 20), QVector2D(107, 107), QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)]

        # prev -> next の t分の回転量
        p1_qq = QQuaternion.rotationTo((y1e - c).normalized(), (c - c).normalized())
        p2_qq = QQuaternion.rotationTo((y1e - c).normalized(), (y2e - c).normalized())
        p3_qq = QQuaternion.rotationTo((y1e - c).normalized(), (y3e - c).normalized())
        
        y1p = p1_qq * (y1e - c) + c

        # 球形補間の移動量
        cx1 = t * 0.5
        cy1_qq = QQuaternion.slerp(p1_qq, p2_qq, 0.5)
        cy1p = cy1_qq * (y1e - c) + c

        y2p = p2_qq * (y1e - c) + c

        # 球形補間の移動量
        cx2 = t + ((1 - t) * 0.5)
        cy2_qq = QQuaternion.slerp(p2_qq, p3_qq, 0.5)
        cy2p = cy2_qq * (y1e - c) + c

        y3p = p3_qq * (y1e - c) + c

        # # 開始フレームと中間フレームの交点
        # cx1, cy1 = calc_circle_polar(ctr_x, ctr_y, radius, x1, y1, x2, y2)

        # # 中間フレームと終点フレームの交点
        # cx2, cy2 = calc_circle_polar(ctr_x, ctr_y, radius, x2, y2, x3, y3)

        # # 交点を制御点とする三次ベジェ曲線
        # bz = calc_quadratic_bezier_curve(x1/(x3 - x1), y1/y3, cx1/(x3 - x1), cy1/y3, cx2/(x3 - x1), cy2/y3, x3/(x3 - x1), y3/y3, t)

        if y1p == QVector3D():
            y1p = QVector3D(1, 0, 0)

        y1v = 1 - QVector3D.dotProduct(y1p.normalized(), y1p.normalized())
        cy1v = 1 - QVector3D.dotProduct(y1p.normalized(), cy1p.normalized())
        y2v = 1 - QVector3D.dotProduct(y1p.normalized(), y2p.normalized())
        cy2v = 1 - QVector3D.dotProduct(y1p.normalized(), cy2p.normalized())
        y3v = 1 - QVector3D.dotProduct(y1p.normalized(), y3p.normalized())

        diffy = 1 if (y3v == y1v) else (y3v - y1v)

        y1 = (y1v - y1v) #/ diffy
        cy1 = (cy1v - y1v) #/ diffy
        cy2 = (cy2v - y1v) #/ diffy
        y3 = (y3v - y1v) #/ diffy

        # 円形補間の場合、円周上の座標で繋ぐ

        # 中間フレームで繋いだ開始フレームと終端フレームの三次ベジェ曲線
        bz = calc_cubic_bezier_4point(0, y1v, cx1, cy1v, cx2, cy2v, 1, y3v, t)

        # オフセット許容する
        offset_bz[0] = fit_bezier_mmd_join(bz[0], offset)
        offset_bz[1] = fit_bezier_mmd_join(bz[1], offset)
        offset_bz[2] = fit_bezier_mmd_join(bz[2], offset)
        offset_bz[3] = fit_bezier_mmd_join(bz[3], offset)

        return True, is_fit_bezier_mmd(bz), bz

        # # 線形補間
        # return calc_smooth_bezier_pos(x1, y1v, x2, y2v, x3, y3v, offset, is_comp_circle)

    # ③軸のどれかがズレている場合、登録対象外
    return True, False, offset_bz

# 円の極を返す
def calc_circle_polar(ctr_x, ctr_y, radius, x1, y1, x2, y2):
    # 2つの点と原点との直交直線
    a, b = calc_line_cross(x1, y1, x2, y2, ctr_x, ctr_y)

    # 片方の点と原点からその点に向かう直線との直交直線
    c, d = calc_line_cross(x1, y1, ctr_x, ctr_y, x1, y1)

    mx1 = ctr_x
    my1 = ctr_y
    mx2 = ctr_x+1
    my2 = a * mx2 + b
    mx3 = x1
    my3 = y1
    mx4 = x1 + 1
    my4 = c * mx4 + d

    x, y = calc_2line_cross(mx1, my1, mx2, my2, mx3, my3, mx4, my4)

    return x, y


# 2直線の交点座標を求めるプログラム    
# 二点 (x1, y1) と (x2, y2) を通る直線と，もう二組みの点 (x3,y3) と (x4,y4) を通る直線の交点の座標 （x，y）
# https://blog.goo.ne.jp/r-de-r/e/e81316c26c521b31e9d47526f9bd5861
def calc_2line_cross(x1, y1, x2, y2, x3, y3, x4, y4):

    a1 = (y2-y1)/(x2-x1)
    a3 = (y4-y3)/(x4-x3)

    x = (a1*x1-y1-a3*x3+y3)/(a1-a3)
    y = (y2-y1)/(x2-x1)*(x-x1)+y1

    return x, y
    
# 直線と垂直に交わる直線の切片と傾き
# (x1, y1) と (x2, y2) を通る直線と垂直に交わり，(x3, y3) を通る直線の切片と傾き
# https://blog.goo.ne.jp/r-de-r/e/b96f7c949faceeefb0c1d1a34aa799e8
def calc_line_cross(x1, y1, x2, y2, x3, y3):
    if y1 == y2:
        y2 += 1

    a = -(x2-x1)/(y2-y1)
    b = y3-a*x3
    
    return a, b

def fit_bezier_mmd_join(b, offset):
    x = b.x()
    y = b.y()

    if 0 - offset <= b.x() <= COMPLEMENT_MMD_MAX + offset:
        x = 0 if 0 > b.x() else COMPLEMENT_MMD_MAX if COMPLEMENT_MMD_MAX < b.x() else b.x()

    if 0 - offset <= b.y() <= COMPLEMENT_MMD_MAX + offset:
        y = 0 if 0 > b.y() else COMPLEMENT_MMD_MAX if COMPLEMENT_MMD_MAX < b.y() else b.y()

    return QVector2D(int(x), int(y))


# 移動用ベジェ曲線 - 指定された3点を通るベジェ曲線を返す
def calc_smooth_bezier_pos(x1, y1v, x2, y2v, x3, y3v, offset, is_comp_circle):
    t = (x2 - x1) / (x3 - x1)

    if (x1 >= x2 or x1 >= x3 or x2 >= x3) or t <= 0 or t >= 1:
        # 正常に計算できない場合、計算対象外
        return False, False, \
            [QVector2D(0, 0), QVector2D(20, 20), QVector2D(107, 107), QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)]
    
    y1 = round(y1v, 2)
    y2 = round(y2v, 2)
    y3 = round(y3v, 2)

    # 3点を通る二次曲線
    a, b, c = calc_quadratic_param(x1, y1, x2, y2, x3, y3)
    output_message("calc_smooth_bezier calc_quadratic_param finish now: %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), is_print)

    if round(a, 3) == 0:
        # 曲線がなく、等間隔に変化する場合、線形補間
        return False, True, \
            [QVector2D(0, 0), QVector2D(20, 20), QVector2D(107, 107), QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)]

    # 開始フレームと中間フレームの交点
    cx1, cy1 = calc_quadratic_cross(a, b, c, x1, y1, x2, y2)

    # 中間フレームと終点フレームの交点
    cx2, cy2 = calc_quadratic_cross(a, b, c, x2, y2, x3, y3)

    t = (x2 - x1) / (x3 - x1)

    diffx = 1 if x3 == x1 else (x3 - x1)
    diffy = 1 if y3 == y1 else (y3 - y1)

    tx1 = (x1 - x1) /diffx
    ty1 = (y1 - y1) / diffy
    tcx1 = (cx1 - x1) / diffx
    tcy1 = (cy1 - y1) / diffy
    tcx2 = (cx2 - x1) / diffx
    tcy2 = (cy2 - y1) / diffy
    tx3 = (x3 - x1) / diffx
    ty3 = (y3 - y1) / diffy

    # # 交点を制御点とする三次ベジェ曲線
    # bz = calc_quadratic_bezier_curve(x1, y1, cx1, cy1, cx2, cy2, x3, y3, t)

    # 中間フレームで繋いだ開始フレームと終端フレームの三次ベジェ曲線
    bz = calc_cubic_bezier_4point(tx1, ty1, tcx1, tcy1, tcx2, tcy2, tx3, ty3, t)

    # オフセット許容する
    offset_bz = [QVector2D(0, 0), QVector2D(20, 20), QVector2D(107, 107), QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)]        

    offset_bz[0] = fit_bezier_mmd_join(bz[0], offset)
    offset_bz[1] = fit_bezier_mmd_join(bz[1], offset)
    offset_bz[2] = fit_bezier_mmd_join(bz[2], offset)
    offset_bz[3] = fit_bezier_mmd_join(bz[3], offset)

    return True, is_fit_bezier_mmd(offset_bz), offset_bz


# linear equation solver utility for ai + bj = c and di + ej = f
def calc_quadratic_bezier_curve_solvexy(a, b, c, d, e, f):
    j = (c - a / d * f) / (b - a * e / d)
    i = (c - (b * j)) / a

    return i, j

def calc_quadratic_bezier_curve_b0(t):
    return pow(1 - t, 3)

def calc_quadratic_bezier_curve_b1(t):
    return t * (1 - t) * (1 - t) * 3

def calc_quadratic_bezier_curve_b2(t):
    return (1 - t) * t * t * 3

def calc_quadratic_bezier_curve_b3(t):
    return pow(t, 3)

# 指定された2点（x1, x3）と制御点（cx1, cx2）を通過点（x2）を通過する三次ベジェ曲線
# https://stackoverflow.com/questions/2315432/how-to-find-control-points-for-a-beziersegment-given-start-end-and-2-intersect/2316440#2316440
def calc_quadratic_bezier_curve(x0, y0, x4, y4, x5, y5, x3, y3, t):
    # find chord lengths
    c1 = sqrt((x4 - x0) * (x4 - x0) + (y4 - y0) * (y4 - y0))
    c2 = sqrt((x5 - x4) * (x5 - x4) + (y5 - y4) * (y5 - y4))
    c3 = sqrt((x3 - x5) * (x3 - x5) + (y3 - y5) * (y3 - y5))
    # guess "best" t
    t1 = c1 / (c1 + c2 + c3)
    t2 = (c1 + c2) / (c1 + c2 + c3)
    
    # transform x1 and x2
    x1, x2 = calc_quadratic_bezier_curve_solvexy(\
        calc_quadratic_bezier_curve_b1(t1), \
        calc_quadratic_bezier_curve_b2(t1), \
        x4 - (x0 * calc_quadratic_bezier_curve_b0(t1)) - (x3 * calc_quadratic_bezier_curve_b3(t1)), \
        calc_quadratic_bezier_curve_b1(t2), calc_quadratic_bezier_curve_b2(t2), \
        x5 - (x0 * calc_quadratic_bezier_curve_b0(t2)) - (x3 * calc_quadratic_bezier_curve_b3(t2)))

    #  transform y1 and y2
    y1, y2 = calc_quadratic_bezier_curve_solvexy(calc_quadratic_bezier_curve_b1(t1), \
        calc_quadratic_bezier_curve_b2(t1), \
        y4 - (y0 * calc_quadratic_bezier_curve_b0(t1)) - (y3 * calc_quadratic_bezier_curve_b3(t1)), \
        calc_quadratic_bezier_curve_b1(t2), calc_quadratic_bezier_curve_b2(t2), \
        y5 - (y0 * calc_quadratic_bezier_curve_b0(t2)) - (y3 * calc_quadratic_bezier_curve_b3(t2)))

    # スケーリング
    A = QVector2D(x0, y0)
    B = QVector2D(x1, y1)
    C = QVector2D(x2, y2)
    D = QVector2D(x3, y3)

    # スケーリング
    bA, bB, bC, bD = scale_bezier(A, B, C, D)

    cA = round_bezier_mmd(bA)
    cB = round_bezier_mmd(bB)
    cC = round_bezier_mmd(bC)
    cD = round_bezier_mmd(bD)

    return [cA, cB, cC, cD]


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
    d = 1 if d == 0 else d

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
    A = QVector2D(x1, y1)
    B = out_tangent_1
    C = out_tangent_2
    D = QVector2D(x3, y3)

    # スケーリング
    bA, bB, bC, bD = scale_bezier(A, B, C, D)

    cA = round_bezier_mmd(bA)
    cB = round_bezier_mmd(bB)
    cC = round_bezier_mmd(bC)
    cD = round_bezier_mmd(bD)

    return [cA, cB, cC, cD]

def calc_cubic_bezier_4point_vec2_dist(a, b):
    return sqrt((a.x() - b.x()) * (a.x() - b.x()) + (a.y() - b.y()) * (a.y() - b.y()))

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

    m = (pv + wv + nv) / 3

    try:
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
        xq1=(-tmb+sqrt(abs(tmb**2-4*tma*tmc)))/2/tma
        xq2=(-tmb-sqrt(abs(tmb**2-4*tma*tmc)))/2/tma
        yq1=-tm13/tm12-tm11/tm12*xq1
        yq2=-tm13/tm12-tm11/tm12*xq2
        zq1=-tm23/tm22-tm21/tm22*xq1
        zq2=-tm23/tm22-tm21/tm22*xq2

        c1 = QVector3D(xq1, yq1, zq1)
        c2 = QVector3D(xq2, yq2, zq2)

        if c1 == c2:
            # 重解
            return c1, r

        if c1.distanceToPoint(m) < c2.distanceToPoint(m):
            # 3点の中間に近い方を返す
            return c1, r

        return c2, r
    except ZeroDivisionError as e:

        if round(x1,1) == round(x2,1) == round(x3,1):
            # 同じ値の場合、2次元円として求める
            cx, cy, r = calc_circle_center(y1, z1, y2, z2, y3, z3)
            return QVector3D(x1, cx, cy), r
        
        if round(y1,1) == round(y2,1) == round(y3,1):
            cx, cy, r = calc_circle_center(x1, z1, x2, z2, x3, z3)
            return QVector3D(cx, y1, cy), r
        
        if round(z1,1) == round(z2,1) == round(z3,1):
            cx, cy, r = calc_circle_center(x1, y1, x2, y2, x3, y3)
            return QVector3D(cx, cy, z1), r
    
    return QVector3D(), 0

# http://www.iot-kyoto.com/satoh/2016/01/29/tangent-003/
# http://nobutina.blog86.fc2.com/blog-entry-674.html
def calc_circle_center(x1, y1, x2, y2, x3, y3):

    G=( y2*x1-y1*x2 +y3*x2-y2*x3 +y1*x3-y3*x1 )

    try:
        Xc= ((x1*x1+y1*y1)*(y2-y3)+(x2*x2+y2*y2)*(y3-y1)+(x3*x3+y3*y3)*(y1-y2))/(2*G)
        Yc=-((x1*x1+y1*y1)*(x2-x3)+(x2*x2+y2*y2)*(x3-x1)+(x3*x3+y3*y3)*(x1-x2))/(2*G)

        Xd=(((x1*x1+y1*y1)-(x2*x2+y2*y2))*(y2-y3)-((x2*x2+y2*y2)-(x3*x3+y3*y3))*(y1-y2))/(2*((x1-x2)*(y2-y3)-(x2-x3)*(y1-y2)))
        Yd=(((y1*y1+x1*x1)-(y2*y2+x2*x2))*(x2-x3)-((y2*y2+x2*x2)-(y3*y3+x3*x3))*(x1-x2))/(2*((y1-y2)*(x2-x3)-(y2-y3)*(x1-x2)))

        G=2 * sqrt( (x1 - Xc) * (x1 - Xc) + (y1 - Yc) * (y1 - Yc) )

        return Xd, Yd, G/2
    except ZeroDivisionError as e:

        if round(x1,1) == round(x2,1) == round(x3,1):
            G = sqrt((y1 + y2 + y3) ** 2)
            return (x1 + x2 + x3) / 3, (y1 + y2 + y3) / 3, G

        G = sqrt((x1 + x2 + x3) ** 2)
        return (x1 + x2 + x3) / 3, (y1 + y2 + y3) / 3, G

    return 0, 0, 0


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




# # https://stackoverflow.com/questions/8989440/joining-two-bezier-curves
# def join_smooth_bezier(bz1, bz2, offset, t):

    # # 一旦無理やりつなぐ
    # A = QVector2D(0, 0)
    # B = ((bz1[1] * t) + bz2[1] * (1 - t))
    # C = ((bz1[2] * t) + bz2[2] * (1 - t))
    # D = QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)
    
    # sA, sB, sC, sD = scale_bezier(A, B, C, D)

    # # オフセット許容する
    # offset_bz = [QVector2D(0, 0), QVector2D(20, 20), QVector2D(107, 107), QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)]        

    # offset_bz[0] = fit_bezier_mmd_join(round_bezier_mmd(sA), 5)
    # offset_bz[1] = fit_bezier_mmd_join(round_bezier_mmd(sB), 5)
    # offset_bz[2] = fit_bezier_mmd_join(round_bezier_mmd(sC), 5)
    # offset_bz[3] = fit_bezier_mmd_join(round_bezier_mmd(sD), 5)
    
    # if offset_bz[1].x() == offset_bz[1].y():
    #     # 同じ値の場合、線形補間
    #     offset_bz[1] = QVector2D(20, 20)

    # if offset_bz[2].x() == offset_bz[2].y():
    #     # 同じ値の場合、線形補間
    #     offset_bz[2] = QVector2D(107, 107)
    
    # if not is_fit_bezier_mmd(offset_bz):
    #     return False, offset_bz

    # # 繋いだのを再分割してみる
    # t, x, y, beforebz, afterbz = calc_bezier_split_offset(offset_bz[1].x(), offset_bz[1].y(), offset_bz[2].x(), offset_bz[2].y(), 0, 1, t, "")

    # # 前後に分割できるかと、オフセットを加味したbzを返す
    # return is_fit_bezier_mmd(beforebz) and is_fit_bezier_mmd(afterbz), offset_bz

    # A2x = bz1[2].x() / COMPLEMENT_MMD_MAX * t
    # A2y = bz1[2].y() / COMPLEMENT_MMD_MAX * t
    # A3x = bz1[3].x() / COMPLEMENT_MMD_MAX * t
    # A3y = bz1[3].y() / COMPLEMENT_MMD_MAX * t

    # C0x = bz2[0].x() / COMPLEMENT_MMD_MAX * (1 - t) + 0.5
    # C0y = bz2[0].y() / COMPLEMENT_MMD_MAX * (1 - t) + 0.5
    # C1x = bz2[1].x() / COMPLEMENT_MMD_MAX * (1 - t) + 0.5
    # C1y = bz2[1].y() / COMPLEMENT_MMD_MAX * (1 - t) + 0.5

    # B1x = 2 * A3x - A2x
    # B1y = 2 * A3y - A2y

    # B2x = 2 * C0x - C1x
    # B2y = 2 * C0y - C1y

    # A = QVector2D(0, 0)
    # B = QVector2D(B1x, B1y)
    # C = QVector2D(B2x, B2y)
    # D = QVector2D(1, 1)

    # # スケーリング
    # bA, bB, bC, bD = scale_bezier(A, B, C, D)

    # cA = round_bezier_mmd(bA)
    # cB = round_bezier_mmd(bB)
    # cC = round_bezier_mmd(bC)
    # cD = round_bezier_mmd(bD)

    # bz = [cA, cB, cC, cD] 

    # # オフセット許容する
    # offset_bz = [QVector2D(0, 0), QVector2D(20, 20), QVector2D(107, 107), QVector2D(COMPLEMENT_MMD_MAX, COMPLEMENT_MMD_MAX)]        

    # offset_bz[0] = fit_bezier_mmd_join(bz[0], offset)
    # offset_bz[1] = fit_bezier_mmd_join(bz[1], offset)
    # offset_bz[2] = fit_bezier_mmd_join(bz[2], offset)
    # offset_bz[3] = fit_bezier_mmd_join(bz[3], offset)

