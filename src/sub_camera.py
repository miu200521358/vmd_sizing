# -*- coding: utf-8 -*-
# カメラ縮尺処理
# 
import logging
import copy
import os
from pathlib import Path
from math import acos, degrees, sin, isnan
from PyQt5.QtGui import QQuaternion, QVector3D, QVector2D, QMatrix4x4, QVector4D
from PyQt5.QtCore import QRect

from VmdWriter import VmdWriter, VmdBoneFrame, VmdCameraFrame
from VmdReader import VmdReader
from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader
import utils, sub_move

logger = logging.getLogger("VmdSizing").getChild(__name__)

# 標準ボーン＋上半身2のボーン名と対応縮尺の辞書
# 足FKは位置が算出できないので、とりあえず対象外
# つま先IKは位置がモデルによって違うのでとりあえず除外
STANDARD_BONE_RATIOS = {
    "上半身2": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "上半身": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "下半身": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "首": {"x":"head", "y":"head", "z":"head", "l":"head"},
    "頭": {"x":"head", "y":"head", "z":"head", "l":"head"},
    "左目": {"x":"head", "y":"head", "z":"head", "l":"head"},
    "右目": {"x":"head", "y":"head", "z":"head", "l":"head"},
    "両目": {"x":"head", "y":"head", "z":"head", "l":"head"},
    "左肩": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "左腕": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "左ひじ": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "左手首": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "左親指１": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "左親指２": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "左人指１": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "左人指２": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "左人指３": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "左中指１": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "左中指２": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "左中指３": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "左薬指１": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "左薬指２": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "左薬指３": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "左小指１": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "左小指２": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "左小指３": {"x":"body", "y":"body", "z":"body", "l":"body"},
    # "左足",
    # "左ひざ",
    # "左足首",
    "右肩": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "右腕": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "右ひじ": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "右手首": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "右親指１": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "右親指２": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "右人指１": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "右人指２": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "右人指３": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "右中指１": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "右中指２": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "右中指３": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "右薬指１": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "右薬指２": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "右薬指３": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "右小指１": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "右小指２": {"x":"body", "y":"body", "z":"body", "l":"body"},
    "右小指３": {"x":"body", "y":"body", "z":"body", "l":"body"},
    # "右足",
    # "右ひざ",
    # "右足首",
    # "左つま先",
    # "右つま先",
    "左足ＩＫ": {"x":"legxz", "y":"body", "z":"body", "l":"body"},
    # "左つま先ＩＫ": {"x":"leg", "y":"body", "z":"leg", "l":"body"},
    "右足ＩＫ": {"x":"legxz", "y":"body", "z":"body", "l":"body"},
    # "右つま先ＩＫ": {"x":"leg", "y":"body", "z":"leg", "l":"body"},
}
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

    # 足IKの比率
    leg_xz_ratio, _, _ = sub_move.calc_leg_ik_ratio(trace_model, replace_model)
    
    # 身体の比率
    body_ratio, head_ratio, _ = calc_body_head_ratio(trace_model, replace_model)

    arm_ratio = calc_arm_ratio(trace_model, replace_model)

    # 比率辞書
    ratio_dict = {
        "body": body_ratio,
        "legxz": leg_xz_ratio,
        "head": head_ratio,
        "arm": arm_ratio
    }

    # 情報提供
    print("カメラ補正: 全長=%s, 頭=%s, 腕=%s, 足=%s" % (body_ratio, head_ratio, arm_ratio, leg_xz_ratio))

    # 作成元モデル：全身のリンク
    org_body_links, org_link_names = create_body_links(trace_model)

    # 変換先モデル：全身のリンク
    rep_body_links, rep_link_names = create_body_links(replace_model)

    # 移動縮尺
    prev_cf_pos = None
    prev_org_nearest_bone_name = None
    for cf_idx, cf in enumerate(camera_motion.cameras):

        logger.info("cf.frame: %s, l: %s, a: %s ---------------------", cf.frame, cf.length, cf.angle )
        logger.debug("cf.p: %s", cf.position )
        if prev_cf_pos:
            logger.debug("prev_cf_pos: %s", prev_cf_pos )
        logger.debug("cf.e: %s", cf.euler )

        if cf_idx > 0 and prev_cf_pos is not None and cf.position == prev_cf_pos:
            # 前回と同じカメラ位置の場合、カメラ位置コピー
            logger.debug("カメラ位置コピー")
            # 実際にコピーするのは、サイジングした位置情報
            cf.position = copy.deepcopy(camera_motion.cameras[cf_idx - 1].position)
            # 距離は変わっている可能性があるので、再計算
            cf.length = cf.length * ratio_dict[STANDARD_BONE_RATIOS[prev_org_nearest_bone_name]["l"]]

            continue

        # 作成元モデルの各ボーングローバル位置
        org_body_global_3ds = create_body_global_3ds(trace_model, org_motion_frames, org_body_links, cf.frame, rep_link_names)

        # 作成元モデルのどのボーンに最も近いか
        org_nearest_bone_name, org_nearest_global_pos, org_nearest_project_pos = calc_nearest_bone(org_body_global_3ds, cf)

        # 作成元モデルの最も近いボーン名と同じボーンの位置を、変換先モデルから取得する
        rep_bone_global_pos = create_bone_global_3ds(replace_model, motion.frames, rep_body_links, cf.frame, rep_link_names, org_nearest_bone_name)

        # 前回カメラ位置として保持（カメラ位置変えるので、コピー保持）
        prev_cf_pos = copy.deepcopy(cf.position)

        # 新しいカメラを生成
        create_camera_frame(org_nearest_bone_name, org_nearest_global_pos, org_nearest_project_pos, rep_bone_global_pos, ratio_dict, cf )

        # 前回の注視点を保持
        prev_org_nearest_bone_name = org_nearest_bone_name

        logger.debug("[after] cf.frame: %s", cf.frame )
        logger.debug("[after] cf.position: %s", cf.position )
        logger.debug("[after] cf.euler: %s", cf.euler )
        logger.debug("[after] cf.length: %s", cf.length )

        # if cf.frame > 540:
        #     break

    print("カメラ調整終了")

    return True

# 腕の比率算出
def calc_arm_ratio(trace_model, replace_model):
    if "左肩" in trace_model.bones and "左肩" in replace_model.bones:
        if "左中指３" in trace_model.bones and "左中指３" in replace_model.bones:
            # 指がある場合、指までの長さ

            replace_arm_length = (replace_model.bones["左中指３"].position - replace_model.bones["左肩"].position).length()
            trace_arm_length = (trace_model.bones["左中指３"].position - trace_model.bones["左肩"].position).length()
            logger.debug("arm_ratio replace_arm_length: %s, trace_arm_length: %s", replace_arm_length, trace_arm_length)
            arm_ratio = 1 if trace_arm_length == 0 else ( replace_arm_length / trace_arm_length )

            return arm_ratio
        elif "左手首" in trace_model.bones and "左手首" in replace_model.bones:
            # 指がない場合、手首までの長さ

            replace_arm_length = (replace_model.bones["左手首"].position - replace_model.bones["左肩"].position).length()
            trace_arm_length = (trace_model.bones["左手首"].position - trace_model.bones["左肩"].position).length()
            logger.debug("arm_ratio replace_arm_length: %s, trace_arm_length: %s", replace_arm_length, trace_arm_length)
            arm_ratio = 1 if trace_arm_length == 0 else ( replace_arm_length / trace_arm_length )

            return arm_ratio

    # ボーンがない場合、比率１
    return 1

# 身体の比率算出
def calc_body_head_ratio(trace_model, replace_model):
    trace_head_ratio, trace_face_length, trace_total_height, trace_head_height, trace_neck_height = get_head_height(trace_model)
    logger.debug("trace_head_ratio: %s", trace_head_ratio)
    logger.debug("trace_face_length: %s", trace_face_length)
    logger.debug("trace_total_height: %s", trace_total_height)
    logger.debug("trace_head_height: %s", trace_head_height)

    replace_head_ratio, replace_face_length, replace_total_height, replace_head_height, replace_neck_height = get_head_height(replace_model)
    logger.debug("replace_head_ratio: %s", replace_head_ratio)
    logger.debug("replace_face_length: %s", replace_face_length)
    logger.debug("replace_total_height: %s", replace_total_height)
    logger.debug("replace_head_height: %s", replace_head_height)

    # 全身比率
    body_ratio = replace_total_height / trace_total_height
    logger.debug("body_ratio: %s", body_ratio)

    # 頭身比率
    # 作成元の頭の大きさで、変換先の頭身に合わせて全長を計算
    # head_ratio = trace_head_ratio / replace_head_ratio
    head_ratio = (replace_face_length * trace_head_ratio) / trace_total_height
    logger.debug("head_ratio: %s", head_ratio)

    # 首までの身長比率
    neck_ratio = replace_neck_height / trace_neck_height

    return body_ratio, head_ratio, neck_ratio

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
        logger.debug("head_tail_pos: %s", head_tail_pos)

        # 顔の大きさ
        face_length = head_tail_pos.y() - model.bones["頭"].position.y()
        if face_length == 0:
            # 顔の大きさが0の場合、とりあえず首位置で再算出
            face_length = head_tail_pos.y() - model.bones["首"].position.y()
        # 全身の高さ
        total_height = head_tail_pos.y()

        logger.debug("face_length: %s, total_height: %s", face_length, total_height)
        
        # 顔の大きさ / 全身の高さ　で頭身算出
        return total_height / face_length, face_length, total_height, model.bones["頭"].position.y(), model.bones["首"].position.y()
    
    return 1, 1, 1, 1, 1


# 全身のリンク作成
def create_body_links(model):
    # logger.debug("------------------------------")
    # logger.debug("create_body_links: %s", model.name)
    # 左目までのリンク生成
    left_eye_links, _ = model.create_link_2_top_one("左目", "頭")
    # 右目までのリンク生成
    right_eye_links, _ = model.create_link_2_top_one("右目", "頭")
    # logger.debug("head_links: %s", [ "{0}: {1}\n".format(x.name, x.position) for x in head_links])    
    # 左人差し指までのリンク
    left_finger_links, _ = model.create_link_2_top_one("左人指３", "左手首")
    # logger.debug("finger_links: %s", [ "{0}: {1}\n".format(x.name, x.position) for x in left_finger_links])    
    # 右人差し指までのリンク
    right_finger_links, _ = model.create_link_2_top_one("右人指３", "右手首")
    # logger.debug("finger_links: %s", [ "{0}: {1}\n".format(x.name, x.position) for x in right_finger_links])    
    # 左つま先IKまでのリンク
    left_toe_ik_all_links, _ = model.create_link_2_top_one("左つま先ＩＫ", "左足ＩＫ")
    # 右つま先IKまでのリンク
    right_toe_ik_all_links, _ = model.create_link_2_top_one("右つま先ＩＫ", "右足ＩＫ")

    # ボーン名のリスト（全身）
    link_names = {}
    for lidx, links in enumerate([left_eye_links, right_eye_links, left_finger_links, right_finger_links, left_toe_ik_all_links, right_toe_ik_all_links]):
        for l in links:
            # 該当ボーンを含んでいるリンクのINDEXを保持
            # 標準＋上半身2のみ判定対象とする
            if l.name in STANDARD_BONE_RATIOS.keys():
                link_names[l.name] = lidx

    logger.debug("link_names: %s", link_names)

    return [left_eye_links, right_eye_links, left_finger_links, right_finger_links, left_toe_ik_all_links, right_toe_ik_all_links], link_names

# ----------------------------------

# 全身のグローバル位置を算出
def create_body_global_3ds(model, motion_frames, body_links, frame, link_names=None):
    # bf生成
    bf = VmdBoneFrame()
    bf.frame = frame

    # 全身のグローバル位置
    # キー：ボーン名、値：ボーングローバル位置
    body_global_3ds = {}

    for limb_links in body_links:
        # リンクからグローバル位置を算出
        _, _, _, _, global_3ds = utils.create_matrix_global(model, limb_links, motion_frames, bf)
        for l, g in zip(reversed(limb_links), global_3ds):
            if link_names is None or ( link_names and l.name in link_names ):
                # 指定リンク名リストがないか、ある場合、ボーン名がリンク名リストにある場合、登録
                body_global_3ds[l.name] = g
    
    logger.debug("m: %s, frame: %s ---------------------", model.name, frame)
    for k, v in body_global_3ds.items():
        logger.debug("%s: %s", k, v)

    return body_global_3ds



# 指定ボーンのグローバル位置を算出
def create_bone_global_3ds(model, motion_frames, body_links, frame, link_names, bone_name):
    # bf生成
    bf = VmdBoneFrame()
    bf.frame = frame

    # 指定されたボーンを含むリンクのグローバル位置を算出
    logger.debug("replace_model: %s", model.name)
    logger.debug("bone_name: %s", bone_name)
    logger.debug("link_names[bone_name]: %s", link_names[bone_name])
    logger.debug("body_links[link_names[bone_name]]: %s", body_links[link_names[bone_name]])
    _, _, _, _, global_3ds = utils.create_matrix_global(model, body_links[link_names[bone_name]], motion_frames, bf)
    
    for l, g in zip(reversed(body_links[link_names[bone_name]]), global_3ds):
        if l.name == bone_name:
            # 該当ボーンに相当するグローバル位置を取得
            logger.debug("pos: %s: %s", bone_name, g)
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
    nearest_project_pos = QVector3D()

    # # カメラ座標
    # camera_matrix = calc_camera_matrix(cf)
    # logger.info("camera_matrix: %s", camera_matrix)

    for idx, (k, v) in enumerate(body_global_3ds.items()):
        # 正規化デバイス座標系の位置を算出
        project_pos = calc_project_pos(v, cf)

        # カメラの位置は見た目上2D
        # 中央からの距離
        dp = QVector2D().distanceToPoint(QVector2D(project_pos.x(), project_pos.y()))

        if cf.frame <= 1177:
            logger.info("%s (%s) ------------", k, cf.frame)
            logger.info("cf.position: %s", cf.position)
            # logger.info("camera_world_pos: %s", camera_world_pos)
            logger.info("v: %s", v)
            logger.info("project_pos: %s", project_pos)
            logger.info("dp: %s", dp)
            # logger.info("image_coordinate_pos: %s", image_coordinate_pos)

        if dp < nearest_distance or not nearest_bone_name:
            # logger.debug("dp: %s", dp)
            # カメラの位置により近いボーン位置である場合、上書き
            nearest_distance = dp
            nearest_bone_name = k
            nearest_project_pos = project_pos # プロジェクション座標系の位置を保持する
            nearest_global_pos = v # グローバル座標系の位置を保持する

    # logger.info("nearest: b: %s, d: %s", nearest_bone_name, nearest_distance)
    # logger.info("nearest: g: %s", nearest_project_pos)
    
    return nearest_bone_name, nearest_global_pos, nearest_project_pos

def calc_unproject_pos(project_pos, cf):
    # モデル座標系
    model_view = create_model_view(cf)

    # プロジェクション座標系
    projection_view = create_projection_view(cf)

    # viewport
    viewport_rect = QRect(-1, -1, 2, 2)

    global_pos = project_pos.unproject(model_view, projection_view, viewport_rect)

    return global_pos

def calc_project_pos(global_pos, cf):
    # モデル座標系
    model_view = create_model_view(cf)

    # プロジェクション座標系
    projection_view = create_projection_view(cf)

    # viewport
    viewport_rect = QRect(-1, -1, 2, 2)

    project_pos = global_pos.project(model_view, projection_view, viewport_rect)

    return project_pos


def create_model_view(cf):
    # モデル座標系（原点を見るため、単位行列）
    model_view = QMatrix4x4()
    model_view.setToIdentity()

    # カメラ角度
    camera_qq = QQuaternion.fromEulerAngles(degrees(cf.euler.x()), degrees(cf.euler.y()), degrees(cf.euler.z()))

    # カメラの原点（グローバル座標）
    mat_origin = QMatrix4x4()
    mat_origin.rotate(camera_qq.inverted())
    mat_origin.translate(QVector3D(0, 0, -cf.length))
    mat_origin.translate(cf.position)
    camera_origin = mat_origin * QVector3D()

    if cf.frame <= 500:
        logger.info("camera_origin: %s", camera_origin)

    # カメラ座標系の行列
    # eye: カメラの原点（グローバル座標）
    # center: カメラの注視点（グローバル座標）
    # up: カメラの上方向ベクトル
    model_view.lookAt(camera_origin, cf.position, QVector3D(0,1,0))

    return model_view

def create_projection_view(cf):
    mat = QMatrix4x4()
    mat.perspective(cf.angle, 16/9, 0.1, 100)

    return mat

# カメラ座標系の位置を算出
def calc_camera_coordinate_pos(cf, global_pos):
    camera_qq = QQuaternion.fromEulerAngles(degrees(cf.euler.x()), degrees(cf.euler.y()), degrees(cf.euler.z()))

    # カメラ座標系
    mat = QMatrix4x4()

    # カメラの姿勢(回転行列)
    mat.rotate(camera_qq)
    mat.translate(QVector3D(0, 0, cf.length))
    mat.translate(cf.position)

    # 世界座標点に回転行列を掛ける
    camera_mat_pos = mat * global_pos

    # 世界座標系の原点とカメラ座標系の原点を揃える
    camera_coordinate_pos = camera_mat_pos - cf.position - QVector3D(0, 0, cf.length)

    return camera_coordinate_pos


# ----------------------------------


# 変換先用カメラを作成する
def create_camera_frame( org_nearest_bone_name, org_nearest_global_pos, org_nearest_project_pos, rep_bone_global_pos, ratio_dict, cf ):
    
    logger.debug("camera %s ----------------", cf.frame)

    logger.info("cf.position: %s", cf.position)
    logger.info("b: %s, p: %s", org_nearest_bone_name, org_nearest_global_pos)
    logger.info("l: %s, r: %s", cf.length, rep_bone_global_pos)

    # camera_pos = calc_camera_pos(cf)
    # logger.info("camera_pos: %s", camera_pos)

    org_nearest_relative_pos = cf.position - org_nearest_global_pos
    logger.debug("org_nearest_relative_pos: %s", org_nearest_relative_pos)

    # # カメラ座標系の位置を算出
    # org_camera_coordinate_pos = calc_camera_coordinate_pos(cf, org_nearest_global_pos)
    # logger.debug("org_camera_coordinate_pos: %s", org_camera_coordinate_pos)

    # org_nearest_relative_pos = cf.position - org_camera_coordinate_pos
    # logger.debug("org_nearest_relative_pos: %s", org_nearest_relative_pos)

    # rep_camera_pos = calc_camera_coordinate_pos(cf, rep_bone_global_pos)
    # logger.debug("rep_camera_pos: %s", rep_camera_pos)

    if cf.length > 0:
        # 距離が0未満の場合、カメラ位置に縮尺をかける
        cf.position.setX(cf.position.x() * ratio_dict[STANDARD_BONE_RATIOS[org_nearest_bone_name]["x"]])
        cf.position.setY(cf.position.y() * ratio_dict[STANDARD_BONE_RATIOS[org_nearest_bone_name]["y"]])
        cf.position.setZ(cf.position.z() * ratio_dict[STANDARD_BONE_RATIOS[org_nearest_bone_name]["z"]])

        cf.length = cf.length * ratio_dict[STANDARD_BONE_RATIOS[org_nearest_bone_name]["l"]]
    else:
        # 最も近いボーンの相対位置を、変換先モデルの縮尺に合わせる
        cf.position.setX( rep_bone_global_pos.x() + (org_nearest_relative_pos.x() * ratio_dict[STANDARD_BONE_RATIOS[org_nearest_bone_name]["x"]]) )        
        cf.position.setY( rep_bone_global_pos.y() + (org_nearest_relative_pos.y() * ratio_dict[STANDARD_BONE_RATIOS[org_nearest_bone_name]["y"]]) )        
        cf.position.setZ( rep_bone_global_pos.z() + (org_nearest_relative_pos.z() * ratio_dict[STANDARD_BONE_RATIOS[org_nearest_bone_name]["z"]]) )        
        
        # cf.position.setX( rep_camera_pos.x() + (org_nearest_relative_pos.x() * ratio_dict[STANDARD_BONE_RATIOS[org_nearest_bone_name]["x"]]) )
        # cf.position.setY( rep_camera_pos.y() + (org_nearest_relative_pos.y() * ratio_dict[STANDARD_BONE_RATIOS[org_nearest_bone_name]["y"]]) )
        # cf.position.setZ( rep_camera_pos.z() + (org_nearest_relative_pos.z() * ratio_dict[STANDARD_BONE_RATIOS[org_nearest_bone_name]["z"]]) )
        
        # # Zは相対位置ではなく、元々の位置の比率
        # cf.position.setZ(cf.position.z() * ratio_dict[STANDARD_BONE_RATIOS[org_nearest_bone_name]["z"]])
            
        cf.length = cf.length * ratio_dict[STANDARD_BONE_RATIOS[org_nearest_bone_name]["l"]]

def calc_camera_relative_pos(org_nearest_bone_global_pos, cf):
    # カメラの角度
    camera_qq = QQuaternion.fromEulerAngles(degrees(cf.euler.x()), degrees(cf.euler.y()), degrees(cf.euler.z()))

    camera_pos = calc_camera_pos(cf)
    logger.info("camera_pos: %s", camera_pos)
    
    mat = QMatrix4x4()
    
    # カメラの逆回転で正面に
    mat.rotate(camera_qq.inverted())
    # 相対位置
    mat.translate(camera_pos - org_nearest_bone_global_pos)
    # カメラの回転を再設定
    mat.rotate(camera_qq)

    return mat * QVector3D()

# カメラの位置（Z位置調整）
def calc_camera_pos(cf):
    camera_pos = cf.position
    if cf.length > 0:
        # 距離マイナスの場合、Z位置を調整する

        # カメラの角度
        camera_qq = QQuaternion.fromEulerAngles(degrees(cf.euler.x()), degrees(cf.euler.y()), degrees(cf.euler.z()))
        logger.debug("cf.euler: %s", cf.euler)
        logger.debug("camera_qq: %s", camera_qq.toEulerAngles())
        logger.debug("cf.position: %s", cf.position)
        logger.debug("cf.length: %s", cf.length)

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
        logger.debug("camera_pos mat: %s", camera_pos)

    logger.debug("camera_pos: %s", camera_pos)
    return camera_pos







# #
# # カメラ縮尺処理を実行
# #
# # 現在のアルゴリズムは以下のようになっている。
# # X   : モデルのxz補正値
# # Y   : モデルの左右目ボーン高さの平均値、または頭ボーンの高さのある方(目優先)
# # Z   : モデルのxz補正値 + モデルのZオフセット(必要か未知数)
# # 距離: モデルのxz補正値
# #
# def exec(motion, trace_model, replace_model, output_vmd_path):

#     if motion.camera_cnt == 0:
#         # カメラフレームがなかったら処理しない
#         return True

#     # 足IKのXYZの比率
#     # 横と前後方向の移動はこれと同じ幅に補正されるので。
#     xz_ratio, dummy, leg_ik_stance = sub_move.calc_leg_ik_ratio(trace_model, replace_model)

#     # 目ボーンの高さ比率
#     #
#     # 本当は頭の一番上にある頂点のY座標の邦画いいが、発見する方法が難しい。
#     # ウェイトでは「頭についた大きな装飾品」(BASARAの毛利元就とかわかりやすい)に問題がある。
#     # それでもボーンウェイトでやる場合は弱参照を採用せず、一番Yの高い位置にある頭ボーン100%を採用すべきか。
#     y_ratio = sub_move.calc_eye_level_ratio(trace_model, replace_model)
#     if y_ratio is None:
#         # 目ボーンでの比率が求められなかった場合は頭ボーンでの比率を求める
#         y_ratio = sub_move.calc_head_ratio(trace_model, replace_model)
#         if y_ratio is None:
#             # 頭まで取れなかった場合は高さを弄らないことにする
#             print("どちらかのモデルに左右目、頭のボーンがなかったので高さの補正を行いません")
#             y_ratio = 1.0

#     # センターのZ軸オフセットを計算
#     offset_target_bone = "センター"
#     sub_move.cal_center_z_offset(trace_model, replace_model, offset_target_bone)

#     # 情報提供
#     print("カメラ補正: x=%s, y=%s, z=%s + %s 距離=%s" % (xz_ratio, y_ratio, xz_ratio, replace_model.bones[offset_target_bone].offset_z, xz_ratio))

#     # 移動縮尺
#     for cf in motion.cameras:
#         # IK比率をそのまま掛ける
#         cf.position.setX( cf.position.x() * xz_ratio )
#         cf.position.setY( cf.position.y() * y_ratio )
#         cf.position.setZ( cf.position.z() * xz_ratio + replace_model.bones[offset_target_bone].offset_z)
#         cf.length = cf.length * xz_ratio

#     print("カメラ調整終了")

#     return True
