# -*- coding: utf-8 -*-
# カメラ縮尺処理
# 
import logging
import copy
import os
from pathlib import Path
from math import acos, degrees, sin, isnan
from PyQt5.QtGui import QQuaternion, QVector3D, QVector2D, QMatrix4x4, QVector4D

from VmdWriter import VmdWriter, VmdBoneFrame, VmdCameraFrame
from VmdReader import VmdReader
from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader
import utils, sub_move

logger = logging.getLogger("VmdSizing").getChild(__name__)

#
# カメラ縮尺処理を実行
# 
def exec(motion, trace_model, replace_model, output_vmd_path, org_motion_frames, camera_motion):

    if not camera_motion:
        # カメラモーションが未指定の場合、処理しない
        return True

    if camera_motion.camera_cnt == 0:
        # カメラフレームがなかったら処理しない
        return True

    # 足IKのXYZの比率
    # 横と前後方向の移動はこれと同じ幅に補正されるので。
    xz_ratio, _, _ = sub_move.calc_leg_ik_ratio(trace_model, replace_model)
    
    # 全身比率、頭身比率
    height_ratio, head_ratio = calc_head_ratio(trace_model, replace_model)

    # 情報提供
    # print("カメラ補正: x=%s, y=%s, z=%s + %s 距離=%s" % (xz_ratio, y_ratio, xz_ratio, replace_model.bones[offset_target_bone].offset_z, xz_ratio))
    print("カメラ補正: x=%s, y=%s, z=%s" % (xz_ratio, height_ratio, xz_ratio))
    print("カメラ補正: 全身比率=%s, 頭身比率=%s" % (height_ratio, head_ratio))

    # 作成元モデル：全身のリンク
    org_body_links, org_link_names = create_body_links(trace_model)

    # 変換先モデル：全身のリンク
    rep_body_links, rep_link_names = create_body_links(replace_model)

    # 移動縮尺
    for cf in camera_motion.cameras:
        logger.debug("cf.frame: %s, l: %s, a: %s", cf.frame, cf.length, cf.angle )
        logger.debug("cf.p: %s", cf.position )
        logger.debug("cf.e: %s", cf.euler )

        # 作成元モデルの各ボーングローバル位置
        org_body_global_3ds = create_body_global_3ds(trace_model, org_motion_frames, org_body_links, cf.frame, rep_link_names)

        # 作成元モデルのどのボーンに最も近いか
        org_nearest_bone_name, org_nearest_bone_global_pos, org_nearest_parent_bone_name, org_nearest_global_parent_pos = calc_nearest_bone(org_body_global_3ds, cf)

        # 作成元モデルの最も近いボーン名と同じボーンの位置を、変換先モデルから取得する
        rep_bone_global_pos, rep_bone_global_parent_pos = create_bone_global_3ds(replace_model, motion.frames, rep_body_links, cf.frame, rep_link_names, org_nearest_bone_name, org_nearest_parent_bone_name)

        # 新しいカメラを生成
        create_camera_frame( org_nearest_bone_name, org_nearest_bone_global_pos, org_nearest_global_parent_pos, rep_bone_global_pos, rep_bone_global_parent_pos, xz_ratio, height_ratio, head_ratio, cf )

        logger.info("[after] cf.frame: %s", cf.frame )
        logger.info("[after] cf.position: %s", cf.position )
        logger.info("[after] cf.euler: %s", cf.euler )
        logger.info("[after] cf.length: %s", cf.length )

        # if cf.frame > 350:
        #     break

    print("カメラ調整終了")

    return True

# 作成元とカメラの三角から、変換先の三角を作成
def create_camera_frame( org_nearest_bone_name, org_nearest_bone_global_pos, org_nearest_global_parent_pos, rep_bone_global_pos, rep_bone_global_parent_pos, xz_ratio, height_ratio, head_ratio, cf ):
    logger.info("camera %s ----------------", cf.frame)

    # # 変換先に適したカメラの位置
    # cf.position = calc_camera_pos( org_nearest_bone_name, org_nearest_bone_global_pos, org_nearest_global_parent_pos, rep_bone_global_pos, rep_bone_global_parent_pos, xz_ratio, height_ratio, head_ratio, cf )

    # # 変換先に適した距離
    # cf.length = calc_camera_length(cf, height_ratio, head_ratio)

    logger.info("cf.position: %s", cf.position)
    logger.info("rep_bone_global_pos: %s", rep_bone_global_pos)
    logger.info("org_nearest_bone_global_pos: %s", org_nearest_bone_global_pos)

    camera_pos = calc_camera_pos(cf)
    logger.info("camera_pos: %s", camera_pos)

    org_nearest_bone_relative_pos = camera_pos - org_nearest_bone_global_pos
    logger.info("org_nearest_bone_relative_pos: %s", org_nearest_bone_relative_pos)

    if cf.length > 0:   
        # 距離が0未満の場合、カメラ位置に縮尺をかける
        if height_ratio < 1:
            if head_ratio >= height_ratio:
                # 小さくて通常頭身の子は縮尺を合わせる
                cf.position.setX(cf.position.x() * height_ratio)
                cf.position.setY(cf.position.y() * height_ratio)
                cf.position.setZ(cf.position.z() * height_ratio)
                cf.length = cf.length * height_ratio
            else:
                # 小さくて頭身が違う場合、縮尺を変える
                cf.position.setX(cf.position.x() * height_ratio)
                cf.position.setY(cf.position.y() * (head_ratio if cf.position.y() >= 0 else height_ratio))                    
                cf.position.setZ(cf.position.z() * height_ratio)
                cf.length = cf.length * head_ratio
        else:
            # 大きい子は元のカメラ位置から縮尺
            cf.position.setX(cf.position.x() * height_ratio)
            cf.position.setY(cf.position.y() * height_ratio)
            cf.position.setZ(cf.position.z() * height_ratio)
            cf.length = cf.length * height_ratio
    else:
        calc_ratio = height_ratio if height_ratio > 1 else max(height_ratio, head_ratio)

        # 最も近いボーンの相対位置を、変換先モデルの縮尺に合わせる
        cf.position.setX( rep_bone_global_pos.x() + (org_nearest_bone_relative_pos.x() * calc_ratio) )
        cf.position.setY( rep_bone_global_pos.y() + (org_nearest_bone_relative_pos.y() * calc_ratio) )
        cf.position.setZ( rep_bone_global_pos.z() + (org_nearest_bone_relative_pos.z() * calc_ratio) )
        cf.length = cf.length * calc_ratio

    # # 距離の行列計算
    # mat = QMatrix4x4()
    # # カメラの中心位置に移動
    # mat.translate(camera_pos)
    # logger.debug("camera_pos: %s", camera_pos)
    # # カメラの中心位置から回転
    # camera_qq = QQuaternion.fromEulerAngles(degrees(cf.euler.x()), degrees(cf.euler.y()), degrees(cf.euler.z()))
    # mat.rotate(camera_qq)
    # # ローカルZ方向に離れる
    # logger.debug("cf.length: %s", cf.length)
    # logger.debug("cf.length * max(head_ratio, height_ratio): %s", cf.length * max(head_ratio, height_ratio))
    # camera_length_pos = mat * QVector3D(0, 0, (cf.length * max(head_ratio, height_ratio)))
    # logger.debug("camera_length_pos: %s", camera_length_pos)
    # # # if cf.length >= 0:
    # # #     if head_ratio < 1 and height_ratio < 1:
    # # #         # マイナス距離で、頭身が小さい場合、符号を逆転させた倍率で距離を調整する
    # # #         minus_length_ratio = height_ratio - head_ratio if head_ratio > height_ratio else head_ratio - height_ratio
    # # #         logger.debug("minus_length_ratio: %s", minus_length_ratio)
    # # #         camera_pos = mat.mapVector(QVector3D(0, 0, cf.length * minus_length_ratio))
    # # #     else:
    # # #         # マイナス距離で頭身が大きい場合、距離は変えない
    # # #         camera_pos = mat.mapVector(QVector3D(0, 0, cf.length * max(head_ratio, height_ratio)))
    # # # else:
    # # #     # プラス距離の場合、もっとも大きい比率で調整する

    # if cf.length > 0:
    #     # マイナス距離の場合
    #     cf.length = cf.length * min(head_ratio, height_ratio)
    # else:
    #     # プラス距離の場合
    #     cf.length = cf.length * max(head_ratio, height_ratio)

# 指定ボーンのグローバル位置を算出
def create_bone_global_3ds(model, motion_frames, body_links, frame, link_names, bone_name, parent_bone_name):
    # bf生成
    bf = VmdBoneFrame()
    bf.frame = frame

    # 指定されたボーンを含むリンクのグローバル位置を算出
    logger.info("replace_model: %s", model.name)
    logger.info("bone_name: %s", bone_name)
    logger.debug("link_names[bone_name]: %s", link_names[bone_name])
    logger.debug("body_links[link_names[bone_name]]: %s", body_links[link_names[bone_name]])
    _, _, _, _, global_3ds = utils.create_matrix_global(model, body_links[link_names[bone_name]], motion_frames, bf)
    
    pgpos = QVector3D()
    for l, g in zip(reversed(body_links[link_names[bone_name]]), global_3ds):
        if l.name == parent_bone_name:
            # 該当親ボーンに相当するグローバル位置を取得
            pgpos = g

        if l.name == bone_name:
            # 該当ボーンに相当するグローバル位置を取得
            logger.info("parent: %s", pgpos)
            logger.info("pos: %s: %s", bone_name, g)
            return g, pgpos

    # 指定されたボーンのグローバル位置が取得できなかった場合
    logger.warn("指定ボーンのグローバル位置取得失敗 %s", bone_name)
    return QVector3D(), QVector3D()

def calc_camera_pos(cf):
    camera_pos = cf.position
    if cf.length > 0:
        # 距離マイナスの場合、Z位置を調整する

        # カメラの角度
        camera_qq = QQuaternion.fromEulerAngles(degrees(cf.euler.x()), degrees(cf.euler.y()), degrees(cf.euler.z()))
        logger.info("cf.euler: %s", cf.euler)
        logger.info("camera_qq: %s", camera_qq.toEulerAngles())
        logger.info("cf.position: %s", cf.position)
        logger.info("cf.length: %s", cf.length)

        mat = QMatrix4x4()
        # 初期位置
        mat.translate(cf.position)
        # カメラの回転
        mat.rotate(camera_qq.inverted())
        # カメラの距離を0にしてみる
        mat.translate(QVector3D(0,0,-cf.position.z()))

        camera_pos = mat * QVector3D()
        # # とりあえずZ距離はなし
        # camera_pos.setZ(0)
        # if cf.position.y() < 0 and camera_pos.y() > 0:
        #     # 元々のY位置がマイナスで、計算後符号が反転した場合、減算
        #     camera_pos.setY( cf.position.y() - camera_pos.y() )
        logger.info("camera_pos mat: %s", camera_pos)

    logger.info("camera_pos: %s", camera_pos)
    return camera_pos

# 最も近いボーン名とボーン位置を返す
def calc_nearest_bone(body_global_3ds, cf):
    logger.info("frame: %s ---------------------", cf.frame)

    nearest_distance = 0
    nearest_bone_name = None
    nearest_global_pos = QVector3D()
    nearest_parent_bone_name = None
    nearest_global_parent_pos = QVector3D()

    camera_pos = calc_camera_pos(cf)

    for idx, (k, v) in enumerate(body_global_3ds.items()):
        dp = camera_pos.distanceToPoint(v)
        logger.debug("k: %s, dp: %s", k, dp)
        logger.debug("camera_pos: %s", camera_pos)
        logger.debug("v: %s", v)
        logger.debug("camera_pos - v: %s", camera_pos - v)
        if dp < nearest_distance or not nearest_bone_name:
            # logger.debug("dp: %s", dp)
            # カメラの位置により近いボーン位置である場合、上書き

            nearest_distance = dp
            nearest_bone_name = k
            nearest_global_pos = v
            if idx == 0:
                # 親がない場合は、とりあえず初期値
                nearest_parent_bone_name = ""
                nearest_global_parent_pos = QVector3D()
            else:
                # 親ボーンはひとつ上のボーン
                nearest_parent_bone_name = list(body_global_3ds.keys())[idx-1]
                nearest_global_parent_pos = list(body_global_3ds.values())[idx-1]

    logger.info("nearest: b: %s, d: %s", nearest_bone_name, nearest_distance)
    logger.info("nearest: g: %s", nearest_global_pos)
    logger.info("nearest: p: %s", nearest_global_parent_pos)
    
    return nearest_bone_name, nearest_global_pos, nearest_parent_bone_name, nearest_global_parent_pos


# 全身のリンク作成
def create_body_links(model):
    # logger.debug("------------------------------")
    # logger.debug("create_body_links: %s", model.name)
    # 頭までのリンク生成
    head_links, _ = model.create_link_2_top("頭")
    # logger.debug("head_links: %s", [ "{0}: {1}\n".format(x.name, x.position) for x in head_links])    
    # 左人差し指までのリンク
    left_finger_links, _ = model.create_link_2_top_one("左人指先", "左手首")
    # logger.debug("finger_links: %s", [ "{0}: {1}\n".format(x.name, x.position) for x in left_finger_links])    
    # 右人差し指までのリンク
    right_finger_links, _ = model.create_link_2_top_one("右人指先", "右手首")
    # logger.debug("finger_links: %s", [ "{0}: {1}\n".format(x.name, x.position) for x in right_finger_links])    
    # 左つま先IKまでのリンク
    left_toe_ik_all_links, _ = model.create_link_2_top_one("左つま先ＩＫ", "左足ＩＫ")
    # 右つま先IKまでのリンク
    right_toe_ik_all_links, _ = model.create_link_2_top_one("右つま先ＩＫ", "右足ＩＫ")

    # ボーン名のリスト（全身）
    link_names = {}
    for lidx, links in enumerate([head_links, left_finger_links, right_finger_links, left_toe_ik_all_links, right_toe_ik_all_links]):
        for l in links:
            # 該当ボーンを含んでいるリンクのINDEXを保持
            # 標準＋上半身2のみ判定対象とする
            if l.name in utils.STANDARD_BONE_NAMES:
                link_names[l.name] = lidx

    logger.info("link_names: %s", link_names)

    return [head_links, left_finger_links, right_finger_links, left_toe_ik_all_links, right_toe_ik_all_links], link_names


# 全身のグローバル位置を算出
def create_body_global_3ds(model, motion_frames, body_links, frame, link_names=None):
    # bf生成
    bf = VmdBoneFrame()
    bf.frame = frame

    # 全身のグローバル位置
    # キー：ボーン名、値：ボーングローバル位置
    body_global_3ds = {}

    for limb_links in body_links:
        # 頭と腕のリンクからグローバル位置を算出
        _, _, _, _, global_3ds = utils.create_matrix_global(model, limb_links, motion_frames, bf)
        for l, g in zip(reversed(limb_links), global_3ds):
            if link_names is None or ( link_names and l.name in link_names ):
                # 指定リンク名リストがないか、ある場合、ボーン名がリンク名リストにある場合、登録
                body_global_3ds[l.name] = g
    
    logger.info("m: %s, frame: %s ---------------------", model.name, frame)
    for k, v in body_global_3ds.items():
        logger.info("%s: %s", k, v)

    return body_global_3ds

# 頭身比率
def calc_head_ratio(trace_model, replace_model):
    trace_head_ratio, trace_face_length, trace_total_height, trace_head_height = get_head_height(trace_model)
    logger.info("trace_head_ratio: %s", trace_head_ratio)
    logger.info("trace_face_length: %s", trace_face_length)
    logger.info("trace_total_height: %s", trace_total_height)
    logger.info("trace_head_height: %s", trace_head_height)

    replace_head_ratio, replace_face_length, replace_total_height, replace_head_height = get_head_height(replace_model)
    logger.info("replace_head_ratio: %s", replace_head_ratio)
    logger.info("replace_face_length: %s", replace_face_length)
    logger.info("replace_total_height: %s", replace_total_height)
    logger.info("replace_head_height: %s", replace_head_height)

    # 全身比率
    height_ratio = replace_total_height / trace_total_height
    logger.info("height_ratio: %s", height_ratio)

    # # 頭身比率
    # # 変換先の顔の大きさで、作成元モデルの頭身に合わせて全長を測った場合に、変換先モデルとの全長の差
    # # head_ratio = ( replace_total_height / (replace_head_ratio * trace_face_length) )
    # head_ratio = (replace_face_length * trace_head_ratio) / (trace_face_length * replace_head_ratio)
    # logger.info("head_ratio: %s", head_ratio)
    
    # 頭ボーンまでの比率
    head_ratio = replace_head_height / trace_head_height

    return height_ratio, head_ratio

# 頭身取得
def get_head_height(model):
    if "頭" in model.bones and "首" in model.bones:
        # 頭の頂点を取得する
        head_tail_pos = model.get_head_upper_vertex_position()
        # # 頭ボーンの先を取得する
        # head_tail_pos = model.bones["頭"].position
        # if model.bones["頭"].tail_index >= 0:
        #     # ボーンINDEXが指定されている場合
        #     head_tail_pos = model.bones[model.bone_indexes[model.bones["頭"].tail_index]].position
        # else:
        #     # ボーン相対位置が指定されている場合
        #     head_tail_pos += model.bones["頭"].tail_position
        logger.info("head_tail_pos: %s", head_tail_pos)

        # 顔の大きさ
        face_length = head_tail_pos.y() - model.bones["頭"].position.y()
        if face_length == 0:
            # 顔の大きさが0の場合、とりあえず首位置で再算出
            face_length = head_tail_pos.y() - model.bones["首"].position.y()
        # 全身の高さ
        total_height = head_tail_pos.y()

        logger.info("face_length: %s, total_height: %s", face_length, total_height)
        
        # 顔の大きさ / 全身の高さ　で頭身算出
        return total_height / face_length, face_length, total_height, model.bones["頭"].position.y()
    
    return 1, 1, 1, 1
