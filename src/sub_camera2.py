# -*- coding: utf-8 -*-
# カメラ縮尺処理
# 
import logging
import copy
from PyQt5.QtGui import QQuaternion, QVector3D, QVector2D, QMatrix4x4, QVector4D

from VmdWriter import VmdWriter, VmdBoneFrame
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
        org_nearest_bone_name, _, org_nearest_bone_relative_pos = calc_nearest_bone(org_body_global_3ds, cf)

        # 作成元モデルの最も近いボーン名と同じボーンの位置を、変換先モデルから取得する
        rep_bone_global_pos = create_bone_global_3ds(replace_model, motion.frames, rep_body_links, cf.frame, rep_link_names, org_nearest_bone_name)

        if cf.length == 0 and height_ratio < 1:
            # 距離０の場合、とりあえず比率をかけないで、距離を維持する
            cf.position.setX( rep_bone_global_pos.x() + org_nearest_bone_relative_pos.x() )
            cf.position.setY( rep_bone_global_pos.y() + org_nearest_bone_relative_pos.y() )
            cf.position.setZ( rep_bone_global_pos.z() + org_nearest_bone_relative_pos.z() )

            # 角度を調整する
            cf.euler.setX( cf.euler.x() * xz_ratio )
            cf.euler.setY( cf.euler.y() * height_ratio )
            cf.euler.setZ( cf.euler.z() * xz_ratio )
        else:
            # 最も近いボーンの相対位置を、変換先モデルの縮尺に合わせる
            cf.position.setX( rep_bone_global_pos.x() + (org_nearest_bone_relative_pos.x() * xz_ratio) )
            cf.position.setY( rep_bone_global_pos.y() + (org_nearest_bone_relative_pos.y() * height_ratio) )
            cf.position.setZ( rep_bone_global_pos.z() + (org_nearest_bone_relative_pos.z() * xz_ratio) )

        # 距離の行列計算
        mat = QMatrix4x4()
        # カメラの中心位置に移動
        mat.translate(cf.position)
        # カメラの中心位置から回転
        mat.rotate(QQuaternion.fromEulerAngles(cf.euler))
        # # Z方向に離れる
        # mat.translate(QVector3D(0, 0, cf.length))
        # # スケールを小さくする
        # mat.scale(y_ratio)
        # # カメラの位置
        # camera_pos = mat.map(QVector3D())
        # ローカルZ方向に離れる
        logger.info("cf.length: %s", cf.length)
        if cf.length >= 0 and head_ratio < 1 and height_ratio < 1:
            # マイナス距離で、頭身が小さい場合、符号を逆転させた倍率で距離を調整する
            minus_length_ratio = height_ratio - head_ratio if head_ratio > height_ratio else head_ratio - height_ratio
            logger.info("minus_length_ratio: %s", minus_length_ratio)
            camera_pos = mat.mapVector(QVector3D(0, 0, cf.length * minus_length_ratio))
        else:
            # もっとも大きい比率で調整する
            camera_pos = mat.mapVector(QVector3D(0, 0, (cf.length * max(head_ratio, height_ratio))))

        # 原点からのカメラの距離
        cf.length = camera_pos.z()

        logger.debug("[after] cf.p: %s", cf.position )
        logger.info("[after] camera_pos: %s, d: %s", camera_pos, cf.length)

    print("カメラ調整終了")

    return True


# 指定ボーンのグローバル位置を算出
def create_bone_global_3ds(model, motion_frames, body_links, frame, link_names, bone_name):
    # bf生成
    bf = VmdBoneFrame()
    bf.frame = frame

    # 指定されたボーンを含むリンクのグローバル位置を算出
    _, _, _, _, global_3ds = utils.create_matrix_global(model, body_links[link_names[bone_name]], motion_frames, bf)

    for l, g in zip(reversed(body_links[link_names[bone_name]]), global_3ds):
        if l.name == bone_name:
            # 該当ボーンに相当するグローバル位置を取得
            return g

    # 指定されたボーンのグローバル位置が取得できなかった場合
    logger.warn("指定ボーンのグローバル位置取得失敗 %s", bone_name)
    return QVector3D()


# 最も近いボーン名とボーン位置を返す
def calc_nearest_bone(body_global_3ds, cf):
    logger.debug("frame: %s ---------------------", cf.frame)

    nearest_distance = 0
    nearest_bone_name = None
    nearest_global_pos = QVector3D()

    for k, v in body_global_3ds.items():
        dp = cf.position.distanceToPoint(v)
        logger.debug("k: %s, dp: %s", k, dp)
        logger.debug("cf.position: %s", cf.position)
        logger.debug("v: %s", v)
        if dp < nearest_distance or not nearest_bone_name:
            # logger.debug("dp: %s", dp)
            # カメラの位置により近いボーン位置である場合、上書き
            nearest_distance = dp
            nearest_bone_name = k
            nearest_global_pos = v

    # 最も近いボーングローバル位置からのカメラ位置の相対位置
    nearest_relative_pos = cf.position - nearest_global_pos

    logger.debug("nearest: b: %s, d: %s", nearest_bone_name, nearest_distance)
    logger.debug("nearest: g: %s", nearest_global_pos)
    logger.debug("nearest: r: %s", nearest_relative_pos)

    return nearest_bone_name, nearest_global_pos, nearest_relative_pos


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
    # 左つま先までのリンク
    left_toe_links, _ = model.create_link_2_top_one("左つま先ＩＫ", "右足ＩＫ")
    # logger.debug("left_toe_links: %s", [ "{0}: {1}\n".format(x.name, x.position) for x in left_toe_links])
    # 右つま先までのリンク
    right_toe_links, _ = model.create_link_2_top_one("右つま先ＩＫ", "右足ＩＫ")
    # logger.debug("right_toe_links: %s", [ "{0}: {1}\n".format(x.name, x.position) for x in right_toe_links])

    # ボーン名のリスト
    link_names = {}
    for lidx, links in enumerate([head_links, left_finger_links, right_finger_links, left_toe_links, right_toe_links]):
        for l in links:
            # 該当ボーンを含んでいるリンクのINDEXを保持
            # 標準＋上半身2のみ判定対象とする
            if l.name in utils.STANDARD_BONE_NAMES:
                link_names[l.name] = lidx
    
    return [head_links, left_finger_links, right_finger_links, left_toe_links, right_toe_links], link_names

# 全身のグローバル位置を算出
def create_body_global_3ds(model, motion_frames, body_links, frame, link_names=None):
    # bf生成
    bf = VmdBoneFrame()
    bf.frame = frame

    # 全身のグローバル位置
    # キー：ボーン名、値：ボーングローバル位置
    body_global_3ds = {}

    for limb_links in body_links:
        # 四肢のリンクからグローバル位置を算出
        _, _, _, _, global_3ds = utils.create_matrix_global(model, limb_links, motion_frames, bf)
        for l, g in zip(reversed(limb_links), global_3ds):
            if link_names is None or ( link_names and l.name in link_names ):
                # 指定リンク名リストがないか、ある場合、ボーン名がリンク名リストにある場合、登録
                body_global_3ds[l.name] = g

    # logger.debug("m: %s, frame: %s ---------------------", model.name, frame)
    # for k, v in body_global_3ds.items():
    #     logger.debug("%s: %s", k, v)
    
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

    # 頭身比率
    head_ratio = ( replace_head_ratio / trace_head_ratio )
    logger.info("head_ratio: %s", head_ratio)

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