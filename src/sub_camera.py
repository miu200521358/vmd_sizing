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

# summary_file_logger = logging.getLogger("summary")
# summary_file_logger.addHandler(logging.FileHandler("summary.csv"))

# parts_file_logger = logging.getLogger("parts")
# parts_file_logger.addHandler(logging.FileHandler("parts.csv"))

# rep_file_logger = logging.getLogger("rep")
# rep_file_logger.addHandler(logging.FileHandler("rep.csv"))

# 標準ボーン＋上半身2のボーン名とねんどろ対応縮尺の辞書
# 足FKは位置が算出できないので、とりあえず対象外
# つま先IKは位置がモデルによって違うのでとりあえず除外
STANDARD_BONE_RATIOS = {
    "上半身2": "上半身2",
    "上半身": "上半身",
    "首": "首",
    "頭": "頭",
    "頭頂": "頭頂",
    "左目": "左目",
    "右目": "右目",
    "両目": "両目",
    "左肩": "左肩",
    "左腕": "左腕",
    "左ひじ": "左ひじ",
    "左手首": "左手首",
    "左親指１": "左親指１",
    "左親指２": "左親指２",
    "左人指１": "左人指１",
    "左人指２": "左人指２",
    "左人指３": "左人指３",
    "左中指１": "左中指１",
    "左中指２": "左中指２",
    "左中指３": "左中指３",
    "左薬指１": "左薬指１",
    "左薬指２": "左薬指２",
    "左薬指３": "左薬指３",
    "左小指１": "左小指１",
    "左小指２": "左小指２",
    "左小指３": "左小指３",
    "左足": "左足",
    # "左ひざ",
    # "左足首",
    "右肩": "右肩",
    "右腕": "右腕",
    "右ひじ": "右ひじ",
    "右手首": "右手首",
    "右親指１": "右親指１",
    "右親指２": "右親指２",
    "右人指１": "右人指１",
    "右人指２": "右人指２",
    "右人指３": "右人指３",
    "右中指１": "右中指１",
    "右中指２": "右中指２",
    "右中指３": "右中指３",
    "右薬指１": "右薬指１",
    "右薬指２": "右薬指２",
    "右薬指３": "右薬指３",
    "右小指１": "右小指１",
    "右小指２": "右小指２",
    "右小指３": "右小指３",
    "右足": "右足",
    # "右ひざ",
    # "右足首",
    # "左つま先",
    # "右つま先",
    "左足ＩＫ": "左足ＩＫ",
    # "左つま先ＩＫ": "左つま先ＩＫ",
    "右足ＩＫ": "右足ＩＫ",
    # "右つま先ＩＫ": "右つま先ＩＫ",
    "左足底辺": "左足底辺",
    "右足底辺": "右足底辺",
}

# 足系ボーン名
LEG_BONE_NAMES = ["左足ＩＫ", "右足ＩＫ", "左つま先ＩＫ", "右つま先ＩＫ", "左足底辺", "右足底辺", "左足", "右足"]
# 体幹系ボーン名
TRUNK_BONE_NAMES = ["頭頂", "首", "頭", "左目", "右目", "両目", "上半身", "上半身2", "下半身"]
# 頭系ボーン名
HEAD_BONE_NAMES = ["頭頂", "首", "頭", "左目", "右目", "両目"]
# 上半身系ボーン名
UPPER_BONE_NAMES = ["頭頂", "首", "頭", "左目", "右目", "両目", "上半身2"]
# 腕系ボーン名
ARM_BONE_NAMES = ["左肩", "左腕", "左ひじ", "左手首", "左親指１", "左親指２", "左人指１", "左人指２", "左人指３", "左中指１", "左中指２", "左中指３", "左薬指１", "左薬指２", "左薬指３", "左小指１", "左小指２", "左小指３"\
    "右肩", "右腕", "右ひじ", "右手首", "右親指１", "右親指２", "右人指１", "右人指２", "右人指３", "右中指１", "右中指２", "右中指３", "右薬指１", "右薬指２", "右薬指３", "右小指１", "右小指２", "右小指３"]

#
# カメラ縮尺処理を実行
# 
def exec(motion, trace_model, replace_model, output_vmd_path, org_motion_frames, camera_motion, camera_y_offset):

    if not camera_motion:
        # カメラモーションが未指定の場合、処理しない
        return True

    if camera_motion.camera_cnt == 0:
        # カメラフレームがなかったら処理しない
        return True

    # 足IKの比率
    # leg_xz_ratio, leg_y_ratio, _ = sub_move.calc_leg_ik_ratio(trace_model, replace_model)
    
    # 身体の比率
    body_ratio, head_ratio, head_ratio_small, org_face_length, replace_head_ratio = calc_body_head_ratio(trace_model, replace_model, camera_y_offset)

    # arm_ratio = calc_arm_ratio(trace_model, replace_model)

    # 比率辞書
    ratio_dict = {
        "body": body_ratio,
        # "legxz": leg_xz_ratio,
        # "legy": leg_y_ratio,
        "head": head_ratio,
        # "arm": arm_ratio,
        "head_small": head_ratio_small
    }

    # 情報提供
    print("カメラ補正値 全長: %s(Yオフセット: %s), 変換先頭身: %s" % (body_ratio, camera_y_offset, replace_head_ratio))
    # print("　足XZ: %s, 足Y: %s" % (leg_xz_ratio, leg_y_ratio))

    # 作成元モデル：全身のリンク
    org_body_links, _ = create_body_links(trace_model, 0)

    # 変換先モデル：全身のリンク
    rep_body_links, rep_link_names = create_body_links(replace_model, camera_y_offset)

    # 作成元のカメラ
    org_camera_motion = copy.deepcopy(camera_motion)

    # # ログ出力用商
    # prev_log_cnt = 0

    # summary_file_logger.info("frame,nearest,nearest.x,nearest.y,nearest.z,nearest_project.x,nearest_project.y,nearest_project_square.x,nearest_project_square.y," +
    # "top,top.x,top.y,top.z,top_project.x,top_project.y,top_project_square.x,top_project_square.y," +
    # "bottom,bottom.x,bottom.y,bottom.z,bottom_project.x,bottom_project.y,bottom_project_square.x,bottom_project_square.y"
    # )

    # parts_file_logger.info("frame,bone_name,global_pos.x,global_pos.y,global_pos.z,project_pos.x,project_pos.y,project_pos.z," +
    #     "project_square_pos.x,project_square_pos.y,dp")

    # rep_file_logger.info("frame,bone_name,ratio,global_pos.x,global_pos.y,global_pos.z,cf.position.x,cf.position.y,cf.position.z,cf.length")

    # 移動縮尺
    for cf_idx, cf in enumerate(camera_motion.cameras):
        if cf_idx > 0 and org_camera_motion.cameras[cf_idx - 1].position == org_camera_motion.cameras[cf_idx].position \
            and org_camera_motion.cameras[cf_idx - 1].euler == org_camera_motion.cameras[cf_idx].euler \
            and org_camera_motion.cameras[cf_idx - 1].length == org_camera_motion.cameras[cf_idx].length:
            # 前回と同じカメラ位置の場合、カメラ位置コピー
            logger.debug("カメラ位置コピー")
            # 実際にコピーするのは、サイジングした位置情報
            cf.position = copy.deepcopy(camera_motion.cameras[cf_idx - 1].position)
            cf.length = copy.deepcopy(camera_motion.cameras[cf_idx - 1].length)
            print("%sフレーム目 前位置・距離キーコピー" % (cf.frame))

            continue

        logger.info("cf.frame: %s, l: %s, a: %s ---------------------", cf.frame, cf.length, cf.angle )
        logger.info("cf.p: %s", cf.position )
        logger.info("cf.e: %s", cf.euler )
        logger.info("cf.d: %s, %s, %s", degrees(cf.euler.x()), degrees(cf.euler.y()), degrees(cf.euler.z()) )
        logger.info("qq: %s", calc_camera_qq(cf).toEulerAngles())

        # 作成元モデルの各ボーングローバル位置
        org_body_global_3ds = create_body_global_3ds(trace_model, org_motion_frames, org_body_links, cf.frame, rep_link_names)

        # 作成元モデルのどのボーンが最も注視点に近いか
        org_nearest_bone_name, org_nearest_global_pos, org_nearest_project_pos, \
            org_bottom_bone_name, org_bottom_global_pos, org_bottom_project_pos, \
            org_top_bone_name, org_top_global_pos, org_top_project_pos = calc_nearest_bone(org_body_global_3ds, ratio_dict, replace_head_ratio, cf)

        # 作成元モデルの最も近いボーン名と同じボーンの位置を、変換先モデルから取得する
        rep_nearest_global_pos = create_bone_global_3ds(replace_model, motion.frames, rep_body_links, cf.frame, rep_link_names, org_nearest_bone_name)
        rep_bottom_global_pos = create_bone_global_3ds(replace_model, motion.frames, rep_body_links, cf.frame, rep_link_names, org_bottom_bone_name)
        rep_top_global_pos = create_bone_global_3ds(replace_model, motion.frames, rep_body_links, cf.frame, rep_link_names, org_top_bone_name)

        # 新しいカメラを生成
        create_camera_frame(org_nearest_bone_name, org_nearest_global_pos, org_nearest_project_pos, \
            org_bottom_bone_name, org_bottom_global_pos, org_bottom_project_pos, \
            org_top_bone_name, org_top_global_pos, org_top_project_pos, \
             rep_nearest_global_pos, rep_bottom_global_pos, rep_top_global_pos, ratio_dict, org_face_length, replace_head_ratio, cf )

        # if 0 <= cf.frame <= 40:
        #     # 変換先モデルの各ボーングローバル位置
        #     rep_body_global_3ds = create_body_global_3ds(trace_model, motion.frames, rep_body_links, cf.frame, rep_link_names)

        #     # 変換先モデルのどのボーンが最も注視点に近いか
        #     rep_nearest_bone_name, rep_nearest_global_pos, rep_nearest_project_pos, \
        #         rep_bottom_bone_name, rep_bottom_global_pos, rep_bottom_project_pos, \
        #         rep_top_bone_name, rep_top_global_pos, rep_top_project_pos = calc_nearest_bone(rep_body_global_3ds, ratio_dict, replace_head_ratio, cf)


        logger.info("[after] cf.frame: %s", cf.frame )
        logger.info("[after] cf.position: %s", cf.position )
        logger.info("[after] cf.euler: %s, %s, %s", calc_camera_euler(cf.euler.x(), cf), calc_camera_euler(-cf.euler.y(), cf), calc_camera_euler(-cf.euler.z(), cf) )
        logger.info("[after] cf.length: %s", cf.length )

        # if cf.frame // 1000 > prev_log_cnt:
        #     print("カメラ調整: %s" % cf.frame)
        #     prev_log_cnt = cf.frame // 1000

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
def calc_body_head_ratio(trace_model, replace_model, camera_y_offset):
    trace_head_ratio, trace_face_length, trace_total_height, trace_head_height, trace_eye_length = get_head_height(trace_model, 0)
    logger.info("trace_head_ratio: %s", trace_head_ratio)
    logger.info("trace_face_length: %s", trace_face_length)
    logger.info("trace_total_height: %s", trace_total_height)
    logger.info("trace_head_height: %s", trace_head_height)

    replace_head_ratio, replace_face_length, replace_total_height, replace_head_height, replace_eye_length = get_head_height(replace_model, camera_y_offset)
    logger.info("replace_head_ratio: %s", replace_head_ratio)
    logger.info("replace_face_length: %s", replace_face_length)
    logger.info("replace_total_height: %s", replace_total_height)
    logger.info("replace_head_height: %s", replace_head_height)

    # 全身比率
    body_ratio = replace_total_height / trace_total_height
    logger.info("body_ratio: %s", body_ratio)

    # 頭身比率

    # head_ratio = (replace_face_length * trace_head_ratio) / (trace_face_length / replace_head_ratio)
    logger.info("replace_face_length * trace_head_ratio) / (trace_face_length / replace_head_ratio): %s", (replace_face_length * trace_head_ratio) / (trace_face_length / replace_head_ratio))

    # head_ratio = (replace_head_height * trace_head_ratio) / trace_head_height
    logger.info("replace_head_height * trace_head_ratio) / trace_head_height: %s", (replace_head_height * trace_head_ratio) / trace_head_height)

    # head_ratio = (trace_face_length * replace_head_ratio) / replace_total_height
    logger.info("replace_head_ratio / trace_head_ratio: %s", replace_head_ratio / trace_head_ratio)
    logger.info("trace_head_ratio / replace_head_ratio: %s", trace_head_ratio / replace_head_ratio)

    # 作成元の頭の大きさで、変換先の頭身に合わせて全長を計算
    head_ratio = (replace_face_length * trace_head_ratio) / trace_total_height
    logger.info("replace_face_length * trace_head_ratio) / trace_total_height: %s", (replace_face_length * trace_head_ratio) / trace_total_height)

    # 頭身低い用の顔アップ用(頭ボーンから目ボーンまでの長さの比率)
    head_ratio_small = replace_eye_length / trace_eye_length
    logger.info("replace_eye_length / trace_eye_length: %s", replace_eye_length / trace_eye_length)

    # # 首までの身長比率
    # neck_ratio = replace_neck_height / trace_neck_height

    # 情報提供
    print("作成元モデル 全長: %s, 頭身: %s, 顔の大きさ: %s" % (trace_total_height, trace_head_ratio, trace_face_length))
    print("変換先モデル 全長: %s, 頭身: %s, 顔の大きさ: %s" % (replace_total_height, replace_head_ratio, replace_face_length))

    return body_ratio, head_ratio, head_ratio_small, trace_face_length, replace_head_ratio

# 頭身取得
def get_head_height(model, camera_y_offset):
    if "頭" in model.bones and "首" in model.bones:
        # 頭の頂点を取得する
        head_tail_pos = model.get_head_upper_vertex_position()
        # 頭の頂点をオフセット調整する
        head_tail_pos.setY(head_tail_pos.y() + camera_y_offset)
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

        # 目から頭ボーンまでの長さ
        if "左目" in model.bones:
            eye_length = model.bones["左目"].position.y() - model.bones["頭"].position.y()
        elif "左目" in model.bones:
            eye_length = model.bones["右目"].position.y() - model.bones["頭"].position.y()
        else:
            eye_length = face_length
        
        # 顔の大きさ / 全身の高さ　で頭身算出
        return total_height / face_length, face_length, total_height, model.bones["頭"].position.y(), eye_length
    
    return 1, 1, 1, 1, 1


# 全身のリンク作成
def create_body_links(model, camera_y_offset):
    # logger.debug("------------------------------")
    # logger.debug("create_body_links: %s", model.name)
    # 左目までのリンク生成
    left_eye_links, _ = model.create_link_2_top_one("左目", "頭")
    # 右目までのリンク生成
    right_eye_links, _ = model.create_link_2_top_one("右目", "頭")
    # 頭頂までのリンク生成
    head_top_links, _ = model.create_link_2_top_one("頭頂", "頭")
    # 頭頂にもオフセットをかける
    if head_top_links[0].name == "頭頂":
        head_top_links[0].position.setY(head_top_links[0].position.y() + camera_y_offset)
    logger.info("head_top_links: %s", [ "{0}: {1}\n".format(x.name, x.position) for x in head_top_links])    
    # 左親指までのリンク
    left_thumb_finger_links, _ = model.create_link_2_top_one("左親指２", "左手首")
    # 左人差し指までのリンク
    left_fore_finger_links, _ = model.create_link_2_top_one("左人指３", "左手首")
    # 左中指までのリンク
    left_middle_finger_links, _ = model.create_link_2_top_one("左中指３", "左手首")
    # 左薬指までのリンク
    left_third_finger_links, _ = model.create_link_2_top_one("左薬指３", "左手首")
    # 左小指までのリンク
    left_little_finger_links, _ = model.create_link_2_top_one("左小指３", "左手首")
    # logger.debug("finger_links: %s", [ "{0}: {1}\n".format(x.name, x.position) for x in left_fore_finger_links])    
    # 右親指までのリンク
    right_thumb_finger_links, _ = model.create_link_2_top_one("右親指２", "右手首")
    # 右人差し指までのリンク
    right_fore_finger_links, _ = model.create_link_2_top_one("右人指３", "右手首")
    # 右中指までのリンク
    right_middle_finger_links, _ = model.create_link_2_top_one("右中指３", "右手首")
    # 右薬指までのリンク
    right_third_finger_links, _ = model.create_link_2_top_one("右薬指３", "右手首")
    # 右小指までのリンク
    right_little_finger_links, _ = model.create_link_2_top_one("右小指３", "右手首")
    # logger.debug("finger_links: %s", [ "{0}: {1}\n".format(x.name, x.position) for x in right_fore_finger_links])    
    # 左足底辺までのリンク
    left_leg_ik_links, _ = model.create_link_2_top_one("左足底辺", "左足ＩＫ")
    # 右足底辺までのリンク
    right_leg_ik_links, _ = model.create_link_2_top_one("右足底辺", "右足ＩＫ")
    # logger.info("right_leg_ik_links: %s", [ "{0}: {1}\n".format(x.name, x.position) for x in right_leg_ik_links])    
    # 左足までのリンク
    left_leg_links, _ = model.create_link_2_top_one("左足", "下半身")
    # 右足までのリンク
    right_leg_links, _ = model.create_link_2_top_one("右足", "下半身")

    # ボーン名のリスト（全身）
    link_names = {}
    for lidx, links in enumerate([head_top_links, left_eye_links, right_eye_links, left_leg_ik_links, right_leg_ik_links, left_leg_links, right_leg_links, \
        left_thumb_finger_links, left_fore_finger_links, left_middle_finger_links, left_third_finger_links, left_little_finger_links, \
        right_thumb_finger_links, right_fore_finger_links, right_middle_finger_links, right_third_finger_links, right_little_finger_links]):
        for l in links:
            # 該当ボーンを含んでいるリンクのINDEXを保持
            # 標準＋上半身2のみ判定対象とする
            if l.name in STANDARD_BONE_RATIOS.keys():
                link_names[l.name] = lidx

    logger.debug("link_names: %s", link_names)

    return [head_top_links, left_eye_links, right_eye_links, left_leg_ik_links, right_leg_ik_links, left_leg_links, right_leg_links, \
        left_thumb_finger_links, left_fore_finger_links, left_middle_finger_links, left_third_finger_links, left_little_finger_links, \
        right_thumb_finger_links, right_fore_finger_links, right_middle_finger_links, right_third_finger_links, right_little_finger_links], link_names

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
    if not bone_name:
        logger.info("画面に映ってない状態")
        return None

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
def calc_nearest_bone(body_global_3ds, ratio_dict, replace_head_ratio, cf):
    logger.debug("frame: %s ---------------------", cf.frame)

    nearest_distance = 0
    nearest_bone_name = None
    nearest_global_pos = QVector3D()
    nearest_project_pos = QVector3D(99999,99999,0)
    nearest_project_square_pos = QVector3D(99999,99999,0)
    bottom_bone_name = None
    bottom_global_pos = QVector3D(0,-99999,0)
    bottom_project_pos = QVector3D(0,-99999,0)
    bottom_project_square_pos = QVector3D(0,-99999,0)
    top_bone_name = None
    top_global_pos = QVector3D(0,99999,0)
    top_project_pos = QVector3D(0,99999,0)
    top_project_square_pos = QVector3D(0,99999,0)

    # # カメラ座標
    # camera_matrix = calc_camera_matrix(cf)
    # logger.info("camera_matrix: %s", camera_matrix)

    # 体幹と直近ボーンとの差分（頭身によって切り分け）
    trunk_diff = 1.5 if replace_head_ratio <= 3 else 1

    for idx, (k, v) in enumerate(body_global_3ds.items()):
        if 0 <= cf.frame <= 40:
            logger.info("%s (%s) ------------", k, cf.frame)

        # 正規化デバイス座標系の位置を算出
        project_pos = calc_project_pos(v, cf)

        project_square_pos = QVector2D()
        project_square_pos.setX((-project_pos.x() + 16) / 16)
        project_square_pos.setY((-project_pos.y() + 9) / 9)

        # カメラの位置は見た目上2D
        # 中央からの距離
        dp = QVector2D(16/2, 9/2).distanceToPoint(QVector2D(project_pos.x(), project_pos.y()))
        # dp = abs(project_pos.x()) + abs(project_pos.y())

        # parts_file_logger.info("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s", cf.frame,k,v.x(),v.y(),v.z(), \
        #     project_pos.x(),project_pos.y(),project_pos.z(), \
        #     project_square_pos.x(),project_square_pos.y(),dp)

        if 0 <= cf.frame <= 40:
            logger.info("project_square_pos: %s", project_square_pos)
            logger.info("dp: %s", dp)
            # logger.info("image_coordinate_pos: %s", image_coordinate_pos)

        if project_square_pos.y() > bottom_project_square_pos.y() and \
            ( project_square_pos.y() <= 1 or ( k in LEG_BONE_NAMES and project_square_pos.y() <= 1.2 )):
            
            if replace_head_ratio <= 3 and k in ARM_BONE_NAMES:
                # 腕系ボーンはBOTTOM判定に入れない（体型上計算対象にならない）
                continue

            # 画面内ちょっとはみ出るくらいに映っていて、かつ底辺ボーンより下の場合、保持
            bottom_bone_name = k
            bottom_project_pos = project_pos # プロジェクション座標系の位置を保持する
            bottom_project_square_pos = project_square_pos # プロジェクション座標系の位置を保持する
            bottom_global_pos = v # グローバル座標系の位置を保持する

        if project_square_pos.y() < top_project_square_pos.y() and \
            ( project_square_pos.y() >= 0 or ( k in HEAD_BONE_NAMES and project_square_pos.y() >= -0.2 )):
            
            if replace_head_ratio <= 3 and k in ARM_BONE_NAMES:
                # 腕系ボーンはTOP判定に入れない（体型上計算対象にならない）
                continue

            # 画面内に映っていて、かつ上辺ボーンより上の場合、保持
            top_bone_name = k
            top_project_pos = project_pos # プロジェクション座標系の位置を保持する
            top_project_square_pos = project_square_pos # プロジェクション座標系の位置を保持する
            top_global_pos = v # グローバル座標系の位置を保持する

        # 直近ボーンがXのずれが小さく、Yがより小さく、かつつま先IK以外であれば採用
        # つま先IKを注視点に合わせると、踵がズレるため
        # if (abs(project_pos.x()) < nearest_project_pos.x() + 0.1 and \
        #     abs(project_pos.y()) < nearest_project_pos.y() + 0.1 and \
        #     0 <= project_square_pos.x() <= 1 and \
        #     0 <= project_square_pos.y() <= 1 and \
        # if (dp < nearest_distance and \
        #     k not in ["左つま先ＩＫ", "右つま先ＩＫ"]) or not nearest_bone_name:
        # if (0 <= abs(project_square_pos.x()) < nearest_project_pos.x() + 0.1 and \
        #     abs(project_square_pos.y()) < nearest_project_pos.y()) or not nearest_bone_name:
        if dp < nearest_distance or not nearest_bone_name:
            # 頭と体幹が現在直近で、かつほとんど位置が変わらない場合、頭を優先
            if nearest_bone_name in TRUNK_BONE_NAMES and \
                k not in TRUNK_BONE_NAMES:
                if replace_head_ratio > 3 and abs(dp - nearest_distance) <= 1:
                    # 3頭身以上は、距離が一定以内なら体幹優先
                    if 0 <= cf.frame <= 40:
                        logger.info("3頭身以上、体幹付近を優先: n: %s, v: %s, d: %s, t: %s", nearest_distance, dp, dp - nearest_distance, trunk_diff)
                    continue
                elif replace_head_ratio <= 3 and (abs(dp - nearest_distance) <= 1.5 or (0 <= nearest_project_square_pos.x() <= 1 and 0 <= nearest_project_square_pos.y() <= 1)) :
                    # 3頭身以下は、近いか体幹が映っていたら体幹優先
                    if 0 <= cf.frame <= 40:
                        logger.info("3頭身以下、体幹付近を優先: n: %s, v: %s, d: %s, t: %s", nearest_distance, dp, dp - nearest_distance, trunk_diff)
                    continue

            if 0 <= cf.frame <= 40:
                logger.info("直近採用 k: %s, dp: %s", k, dp)

            # if k in ["左足ＩＫ", "右足ＩＫ"] and project_pos.y() < -0.5:
            #     logger.info("足IK直近スキップ: %s", project_pos)
            #     # 足は画面下1/4以下の場合、対象外とする
            #     continue

            # logger.debug("dp: %s", dp)
            # カメラの位置により近いボーン位置である場合、上書き
            nearest_distance = dp
            nearest_bone_name = k
            nearest_project_pos = project_pos # プロジェクション座標系の位置を保持する
            nearest_project_square_pos = project_square_pos # プロジェクション座標系の正方形位置を保持する
            nearest_global_pos = v # グローバル座標系の位置を保持する

    logger.info("nearest: b: %s, d: %s", nearest_bone_name, nearest_distance)
    logger.info("nearest: p: %s", nearest_project_pos)
    logger.info("nearest: s: %s", nearest_project_square_pos)
    logger.info("bottom: b: %s", bottom_bone_name)
    logger.info("bottom: p: %s", bottom_project_pos)
    logger.info("bottom: s: %s", bottom_project_square_pos)
    logger.info("top: b: %s", top_bone_name)
    logger.info("top: p: %s", top_project_pos)
    logger.info("top: s: %s", top_project_square_pos)

    # summary_file_logger.info("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s", cf.frame, \
    #     nearest_bone_name,nearest_global_pos.x(),nearest_global_pos.y(),nearest_global_pos.z(), \
    #     nearest_project_pos.x(),nearest_project_pos.y(), \
    #     nearest_project_square_pos.x(),nearest_project_square_pos.y(), \
    #     top_bone_name,top_global_pos.x(),top_global_pos.y(),top_global_pos.z(), \
    #     top_project_pos.x(),top_project_pos.y(), \
    #     top_project_square_pos.x(),top_project_square_pos.y(), \
    #     bottom_bone_name,bottom_global_pos.x(),bottom_global_pos.y(),bottom_global_pos.z(), \
    #     bottom_project_pos.x(),bottom_project_pos.y(), \
    #     bottom_project_square_pos.x(),bottom_project_square_pos.y())
    
    return nearest_bone_name, copy.deepcopy(nearest_global_pos), copy.deepcopy(nearest_project_pos), \
        bottom_bone_name, copy.deepcopy(bottom_global_pos), copy.deepcopy(bottom_project_pos), \
        top_bone_name, copy.deepcopy(top_global_pos), copy.deepcopy(top_project_pos)

def calc_unproject_pos(project_pos, cf):
    # モデル座標系
    model_view = create_model_view(cf)

    # プロジェクション座標系
    projection_view = create_projection_view(cf)

    # viewport
    # viewport_rect = QRect(-1, -1, 2, 2)
    viewport_rect = QRect(0, 0, 16, 9)

    global_pos = project_pos.unproject(model_view, projection_view, viewport_rect)

    return global_pos

# http://www.opengl-tutorial.org/jp/beginners-tutorials/tutorial-3-matrices/
# https://yttm-work.jp/gmpg/gmpg_0003.html
# https://blog.natade.net/2017/06/03/rendering-3dcg-coordinate/
def calc_project_pos(global_pos, cf):
    # モデル座標系
    model_view = create_model_view(cf)

    # プロジェクション座標系
    projection_view = create_projection_view(cf)

    # viewport
    viewport_rect = QRect(0, 0, 16, 9)

    project_pos = global_pos.project(model_view, projection_view, viewport_rect)

    if 0 <= cf.frame <= 40:
        logger.info("%s ------------", cf.frame)
        logger.info("l: %s, p: %s", cf.length, cf.position)
        logger.info("global_pos: %s", global_pos)
        logger.info("project_pos: %s", project_pos)

    return project_pos


def create_model_view(cf):
    # モデル座標系（原点を見るため、単位行列）
    model_view = QMatrix4x4()
    model_view.setToIdentity()

    # カメラ角度
    camera_qq = calc_camera_qq(cf)

    # カメラの原点（グローバル座標）
    mat_origin = QMatrix4x4()
    # mat_origin.translate(QVector3D(cf.position.x(), cf.position.y(), -cf.position.z()))
    mat_origin.translate(cf.position)
    mat_origin.rotate(camera_qq)
    mat_origin.translate(QVector3D(0, 0, cf.length))
    camera_origin = mat_origin * QVector3D()
    # camera_origin = mat_origin * cf.position
    # camera_origin = mat_origin * QVector3D(-cf.position.x(), cf.position.y(), -cf.position.z())

    mat_up = QMatrix4x4()
    mat_up.rotate(camera_qq)
    camera_up = mat_up * QVector3D(0, 1, 0)  

    # if 0 <= cf.frame <= 40:
    #     logger.info("camera_origin: %s", camera_origin)
    #     logger.info("camera_up: %s", camera_up)

    # カメラ座標系の行列
    # eye: カメラの原点（グローバル座標）
    # center: カメラの注視点（グローバル座標）
    # up: カメラの上方向ベクトル
    model_view.lookAt(camera_origin, cf.position, camera_up)

    return model_view

def create_projection_view(cf):
    # # 視野角が小さい時に映す範囲がより小さくなる？
    # angle_diff = 0 if abs(cf.length) >= 15 else (cf.length + 15) / 15
    
    # if 0 <= cf.frame <= 40:
    #     logger.info("angle_diff: %s", angle_diff)

    mat = QMatrix4x4()
    # MMDの縦の視野角。
    # https://ch.nicovideo.jp/t-ebiing/blomaga/ar510610
    mat.perspective(cf.angle * 0.95, 16/9, 0.1, 5000)

    return mat

# # カメラ座標系の位置を算出
# def calc_camera_coordinate_pos(cf, global_pos):
#     camera_qq = calc_camera_qq(cf)

#     # カメラ座標系
#     mat = QMatrix4x4()

#     # カメラの姿勢(回転行列)
#     mat.rotate(camera_qq)
#     mat.translate(QVector3D(0, 0, cf.length))
#     mat.translate(cf.position)

#     # 世界座標点に回転行列を掛ける
#     camera_mat_pos = mat * global_pos

#     # 世界座標系の原点とカメラ座標系の原点を揃える
#     camera_coordinate_pos = camera_mat_pos - cf.position - QVector3D(0, 0, cf.length)

#     return camera_coordinate_pos

def calc_camera_qq(cf):

    qq = QQuaternion.fromEulerAngles(calc_camera_euler(-cf.euler.x(), cf), calc_camera_euler(cf.euler.y(), cf), calc_camera_euler(cf.euler.z(), cf))

    # if 0 <= cf.frame <= 40:
    #     logger.info("qq: %s", qq)
    #     # logger.info("qq.inverted(): %s", qq.inverted())
    #     logger.info("qq.inverted().euler: %s", qq.inverted().toEulerAngles())
    #     # logger.info("calc_camera_qq: -z: %s, z: %s", calc_camera_euler(-cf.euler.z(), cf), calc_camera_euler(cf.euler.z(), cf))

    # if qq.y() < 0 or qq.z() < 0:
    qq.setX(qq.x() * -1)
    # qq.setY(qq.y() * -1)
    # qq.setZ(qq.z() * -1)
    qq.setScalar(qq.scalar() * -1)

    return qq

# 360以上のカメラ回転は、360度に収める
def calc_camera_euler(euler, cf):
    
    degree = degrees(euler)

    # if 0 <= cf.frame <= 40:
    #     logger.info("euler: %s, degree: %s", euler, degree)

    # if abs(degree) < 0.0001:
    #     # e対策
    #     return 0.0

    # while degree > 360:
    #     degree -= 360
    #     logger.info("minus: degree: %s", degree)

    # while degree < -360:
    #     degree += 360
    #     logger.info("add: degree: %s", degree)

    return degree

# ----------------------------------

# 変換先用カメラを作成する
def create_camera_frame( org_nearest_bone_name, org_nearest_global_pos, org_nearest_project_pos, \
    org_bottom_bone_name, org_bottom_global_pos, org_bottom_project_pos, \
    org_top_bone_name, org_top_global_pos, org_top_project_pos, \
    rep_nearest_global_pos, rep_bottom_global_pos, rep_top_global_pos, ratio_dict, org_face_length, replace_head_ratio, cf ):
    
    logger.debug("camera %s ----------------", cf.frame)

    # logger.info("l: %s, rg: %s", cf.length, rep_nearest_global_pos)
    # logger.info("e: %s, x: %s", cf.euler, degrees(cf.euler.x()))
    # logger.info("r: %s", STANDARD_BONE_RATIOS[org_nearest_bone_name])
    # logger.info("rd: %s", ratio_dict)

    # camera_pos = calc_camera_pos(cf)
    # logger.info("camera_pos: %s", camera_pos)

    # 最も近いボーンの相対位置を、変換先モデルの縮尺に合わせる
    org_nearest_relative_pos = cf.position - org_nearest_global_pos
    if 0 <= cf.frame <= 40:
        logger.info("org_nearest_relative_pos: %s", org_nearest_relative_pos)
        logger.info("rep_nearest_global_pos: %s", rep_nearest_global_pos)
        logger.info("rep_bottom_global_pos: %s", rep_bottom_global_pos)
        logger.info("rep_top_global_pos: %s", rep_top_global_pos)

    # # カメラ座標系の位置を算出
    # org_camera_coordinate_pos = calc_camera_coordinate_pos(cf, org_nearest_global_pos)
    # logger.debug("org_camera_coordinate_pos: %s", org_camera_coordinate_pos)

    # org_nearest_relative_pos = cf.position - org_camera_coordinate_pos
    # logger.debug("org_nearest_relative_pos: %s", org_nearest_relative_pos)

    # rep_camera_pos = calc_camera_coordinate_pos(cf, rep_nearest_global_pos)
    # logger.debug("rep_camera_pos: %s", rep_camera_pos)

    # 変換先モデルの縮尺（アップ時のみ顔比率）
    # if replace_head_ratio <= 3:


    # 元モデルの映っている領域の上から下まで
    org_y_diff = abs(org_top_global_pos.y() - org_bottom_global_pos.y())

    if rep_top_global_pos and rep_bottom_global_pos and ( org_bottom_bone_name not in LEG_BONE_NAMES ) :
        # 先モデルの同じ領域の上から下まで
        rep_y_diff = abs(rep_top_global_pos.y() - rep_bottom_global_pos.y())

        if rep_y_diff <= 0:
            # 差分が0という事は同じパーツのみが映っているということで、とりあえず全身比率
            # 差分がマイナスは、腕が上にあがってて、頭ボーンとの差がマイナスになってるとかなので、全身比率
            ratio = ratio_dict["body"]
        else:
            # 比率
            ratio = rep_y_diff / org_y_diff
    else:
        # それ以外の場合とりえあず全身比率（映ってないか足まで映っているため）
        ratio = ratio_dict["body"]

        # if org_nearest_bone_name in UPPER_BONE_NAMES or org_top_bone_name in HEAD_BONE_NAMES:
        #     if abs(cf.length) + cf.angle <= (13 * org_face_length):
        #         logger.info("head合致: a: %s, l: %s, s: %s, d: %s", cf.angle, cf.length, abs(cf.length) + cf.angle, (15 * org_face_length))

        #         ratio = ratio_dict["head"]
        #     elif abs(cf.length) + cf.angle <= (18 * org_face_length):
        #         logger.info("head_small合致: a: %s, l: %s, s: %s, d: %s", cf.angle, cf.length, abs(cf.length) + cf.angle, (20 * org_face_length))

        #         ratio = ratio_dict["head_small"]
        #     else:
        #         logger.info("head合致なし: a: %s, l: %s, s: %s, dh: %s, dhs: %s", cf.angle, cf.length, abs(cf.length) + cf.angle, (15 * org_face_length), (20 * org_face_length))

        #         ratio = ratio_dict["body"]
        # else:
        #     logger.info("nearest合致なし: a: %s, l: %s", cf.angle, cf.length)

        #     ratio = ratio_dict["body"]

        # ratio = ratio_dict["head"] if org_nearest_bone_name in ["首", "頭", "左目", "右目", "両目", "上半身2", "上半身"] and (cf.angle <= 20 and abs(cf.length) + cf.angle <= (30 / ratio_dict["head"]) ) else ratio_dict["body"]
    # else:
    #     # 3頭身より大きい
    #     ratio = ratio_dict["head"] if org_nearest_bone_name in HEAD_BONE_NAMES and (cf.angle <= 20 and abs(cf.length) + cf.angle <= (13 * org_face_length)) else ratio_dict["body"]

    logger.info("l: %s, p: %s", cf.length, cf.position)
    logger.info("b: %s, a: %s, r: %s", org_nearest_bone_name, cf.angle, ratio)

    # rep_file_logger.info("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s", cf.frame,org_nearest_bone_name,ratio,rep_nearest_global_pos.x(),rep_nearest_global_pos.y(),rep_nearest_global_pos.z(), \
    #     cf.position.x(),cf.position.y(),cf.position.z(),cf.length)

    print("%sフレーム目 縮尺比率: %s, 注視点: %s, 上辺: %s, 下辺: %s" % (cf.frame, ratio, org_nearest_bone_name, org_top_bone_name, org_bottom_bone_name))

    # if cf.length > 0:
    #     # 距離が0未満の場合、カメラ位置に縮尺をかける
    #     cf.position.setX(cf.position.x() * ratio)
    #     cf.position.setY(cf.position.y() * ratio)
    #     cf.position.setZ(cf.position.z() * ratio)

    #     cf.length = cf.length * ratio_dict[STANDARD_BONE_RATIOS[org_nearest_bone_name]["l"]]
    # else:
    if True:
        # if degrees(cf.euler.x()) <= -60:
        #     # 上から映すような場合、強制的に全身比率
        #     cf.position.setX( rep_nearest_global_pos.x() + (org_nearest_relative_pos.x() * ratio_dict["body"] ))        
        #     cf.position.setY( rep_nearest_global_pos.y() + (org_nearest_relative_pos.y() * ratio_dict["body"] ))        
        #     cf.position.setZ( rep_nearest_global_pos.z() + (org_nearest_relative_pos.z() * ratio_dict["body"] ))        
        
        #     cf.length = cf.length * ratio_dict["body"]
        # else:
        cf.position.setX( rep_nearest_global_pos.x() + (org_nearest_relative_pos.x() * ratio ))        
        cf.position.setY( rep_nearest_global_pos.y() + (org_nearest_relative_pos.y() * ratio ))        
        cf.position.setZ( rep_nearest_global_pos.z() + (org_nearest_relative_pos.z() * ratio ))        
    
        cf.length = cf.length * ratio

        # cf.position.setX( rep_camera_pos.x() + (org_nearest_relative_pos.x() * ratio_dict[STANDARD_BONE_RATIOS[org_nearest_bone_name]["x"]]) )
        # cf.position.setY( rep_camera_pos.y() + (org_nearest_relative_pos.y() * ratio_dict[STANDARD_BONE_RATIOS[org_nearest_bone_name]["y"]]) )
        # cf.position.setZ( rep_camera_pos.z() + (org_nearest_relative_pos.z() * ratio_dict[STANDARD_BONE_RATIOS[org_nearest_bone_name]["z"]]) )
        
        # # Zは相対位置ではなく、元々の位置の比率
        # cf.position.setZ(cf.position.z() * ratio_dict[STANDARD_BONE_RATIOS[org_nearest_bone_name]["z"]])
        # org_length = cf.length

        # # 全長が小さくて視野角が狭い場合、ちょっと離す
        # if ratio_dict["body"] < 1 and cf.angle <= 10:
        #     cf.length += cf.length * ( 1 - ratio_dict["body"] )
        logger.info("cf.position fixed: %s", cf.position)
        logger.info("cf.length fixed: %s", cf.length)

        # 上辺が顔系で下辺が足系ではない場合、位置合わせ
        if rep_top_global_pos and org_top_bone_name and org_top_bone_name in HEAD_BONE_NAMES \
            and org_bottom_bone_name and org_bottom_bone_name not in LEG_BONE_NAMES:

            rep_top_project_pos = calc_project_pos(rep_top_global_pos, cf)
            rep_start_top_project_pos = calc_project_pos(rep_top_global_pos, cf)

            if 0 <= cf.frame <= 40:
                logger.info("-----------")
                logger.info("org_top_project_pos: %s", org_top_project_pos)
                logger.info("rep_top_project_pos: %s", rep_top_project_pos)

            if rep_top_project_pos.y() >= org_top_project_pos.y():
                # 映っている領域の位置
                for _ in range(100):
                    # Yを動かす
                    cf.position.setY(cf.position.y() + 0.1)

                    # 変換先上辺ボーンのプロジェクション位置
                    rep_top_project_pos = calc_project_pos(rep_top_global_pos, cf)

                    if 0 <= cf.frame <= 40:
                        logger.info("rep > org -----------")
                        logger.info("org_top_project_pos: %s", org_top_project_pos)
                        logger.info("rep_top_project_pos: %s", rep_top_project_pos)
                        logger.info("cf.position while: %s", cf.position)

                    # 変換先上辺ボーン位置が元々の位置より上に行った場合、とりあえず変なので元に戻して終了
                    if rep_top_project_pos.y() >= rep_start_top_project_pos.y():
                        cf.position.setY(cf.position.y() - 0.1)
                        break

                    # 作成元のプロジェクション位置を下回った場合、ループ終了
                    if rep_top_project_pos.y() <= org_top_project_pos.y():
                        break

            else:
                # 映っている領域の位置
                for _ in range(100):
                    # Yを動かす
                    cf.position.setY(cf.position.y() - 0.1)

                    # 変換先上辺ボーンのプロジェクション位置
                    rep_top_project_pos = calc_project_pos(rep_top_global_pos, cf)

                    if 0 <= cf.frame <= 40:
                        logger.info("rep < org -----------")
                        logger.info("org_top_project_pos: %s", org_top_project_pos)
                        logger.info("rep_top_project_pos: %s", rep_top_project_pos)
                        logger.info("cf.position while: %s", cf.position)

                    # 変換先上辺ボーン位置が元々の位置より上に行った場合、とりあえず変なので元に戻して終了
                    if rep_top_project_pos.y() <= rep_start_top_project_pos.y():
                        cf.position.setY(cf.position.y() + 0.1)
                        break

                    # 作成元のプロジェクション位置を下回った場合、ループ終了
                    if rep_top_project_pos.y() >= org_top_project_pos.y():
                        break

            # else:
            #     # 映っている領域の位置
            #     for _ in range(100):
            #         if 0 <= cf.frame <= 40:
            #             logger.info("-----------")
            #             logger.info("org_top_project_pos: %s", org_top_project_pos)
            #             logger.info("rep_top_project_pos: %s", rep_top_project_pos)

            #         # Yを動かす
            #         cf.position.setY(cf.position.y() + 0.1)

            #         # 変換先上辺ボーンのプロジェクション位置
            #         rep_top_project_pos = calc_project_pos(rep_top_global_pos, cf)

            #         # 作成元のプロジェクション位置を上回った場合、ループ終了
            #         if rep_top_project_pos.y() >= org_top_project_pos.y():
            #             break

            #         if 0 <= cf.frame <= 40:
            #             logger.info("cf.position while: %s", cf.position)

        if rep_bottom_global_pos and org_bottom_bone_name and org_bottom_bone_name in LEG_BONE_NAMES:
            # and calc_camera_euler(cf.euler.x(), cf) > -25:
            rep_bottom_project_pos = calc_project_pos(rep_bottom_global_pos, cf)
            rep_start_bottom_project_pos = calc_project_pos(rep_bottom_global_pos, cf)

            # 下辺が足系の場合、位置合わせ（俯瞰時は位置合わせしない）
            if rep_bottom_project_pos.y() >= org_bottom_project_pos.y():
                if 0 <= cf.frame <= 40:
                    logger.info("下位置合わせ（下方向）-----------")
                    logger.info("org_bottom_project_pos: %s", org_bottom_project_pos)
                    logger.info("rep_bottom_project_pos: %s", rep_bottom_project_pos)
                # 映っている領域の位置
                for _ in range(100):
                    # Yを動かす
                    cf.position.setY(cf.position.y() + 0.1)

                    # 変換先下辺ボーンのプロジェクション位置
                    rep_bottom_project_pos = calc_project_pos(rep_bottom_global_pos, cf)

                    if 0 <= cf.frame <= 40:
                        logger.info("rep > org -----------")
                        logger.info("org_bottom_project_pos: %s", org_bottom_project_pos)
                        logger.info("rep_bottom_project_pos: %s", rep_bottom_project_pos)
                        logger.info("cf.position while: %s", cf.position)

                    # 変換先下辺ボーン位置が元々の位置より上に行った場合、とりあえず変なので終了
                    if rep_bottom_project_pos.y() >= rep_start_bottom_project_pos.y():
                        break

                    # 作成元のプロジェクション位置を下回った場合、ループ終了
                    if rep_bottom_project_pos.y() <= org_bottom_project_pos.y():
                        break

            elif rep_bottom_project_pos.y() <= org_bottom_project_pos.y() and org_nearest_bone_name in ["下半身"]:
                rep_bottom_project_pos = calc_project_pos(rep_bottom_global_pos, cf)
                rep_start_bottom_project_pos = calc_project_pos(rep_bottom_global_pos, cf)

                if 0 <= cf.frame <= 40:
                    logger.info("下位置合わせ（上方向）-----------")
                    logger.info("org_bottom_project_pos: %s", org_bottom_project_pos)
                    logger.info("rep_bottom_project_pos: %s", rep_bottom_project_pos)

                # 映っている領域の位置
                for _ in range(100):
                    # Yを動かす
                    cf.position.setY(cf.position.y() - 0.1)

                    # 変換先下辺ボーンのプロジェクション位置
                    rep_bottom_project_pos = calc_project_pos(rep_bottom_global_pos, cf)

                    if 0 <= cf.frame <= 40:
                        logger.info("rep < org -----------")
                        logger.info("org_bottom_project_pos: %s", org_bottom_project_pos)
                        logger.info("rep_bottom_project_pos: %s", rep_bottom_project_pos)
                        logger.info("cf.position while: %s", cf.position)

                    # 変換先下辺ボーン位置が元々の位置より下に行った場合、とりあえず変なので終了
                    if rep_bottom_project_pos.y() <= rep_start_bottom_project_pos.y():
                        break

                    # 作成元のプロジェクション位置を上回った場合、ループ終了
                    if rep_bottom_project_pos.y() >= org_bottom_project_pos.y():
                        break











            # else:
            #     # 映っている領域の位置
            #     for _ in range(100):
            #         if 0 <= cf.frame <= 40:
            #             logger.info("-----------")
            #             logger.info("org_bottom_project_pos: %s", org_bottom_project_pos)
            #             logger.info("rep_bottom_project_pos: %s", rep_bottom_project_pos)

            #         # Yを動かす
            #         cf.position.setY(cf.position.y() + 0.1)

            #         # 変換先下辺ボーンのプロジェクション位置
            #         rep_bottom_project_pos = calc_project_pos(rep_bottom_global_pos, cf)

            #         # 作成元のプロジェクション位置を下回った場合、ループ終了
            #         if rep_bottom_project_pos.y() >= org_bottom_project_pos.y():
            #             break

            #         if 0 <= cf.frame <= 40:
            #             logger.info("cf.position while: %s", cf.position)

            # # 映っている領域の大きさ
            # for _ in range(1000):
            #     # 変換先底辺ボーンのプロジェクション位置
            #     rep_bottom_project_pos = calc_project_pos(rep_bottom_global_pos, cf)
                
            #     # 変換先上辺ボーンのプロジェクション位置
            #     rep_top_project_pos = calc_project_pos(rep_top_global_pos, cf)

            #     # 変換先の底辺と上辺のボーンの距離
            #     rep_project_diff_pos = rep_top_project_pos - rep_bottom_project_pos

            #     if 0 <= cf.frame <= 40:
            #         logger.info("-----------")
            #         logger.info("rep_bottom_project_pos: %s", rep_bottom_project_pos)
            #         logger.info("rep_top_project_pos: %s", rep_top_project_pos)
            #         logger.info("rep_project_diff_pos: %s", rep_project_diff_pos)

            #     # 底辺と上辺のボーンの距離が同じくらいか
            #     if rep_project_diff_pos.y() >= org_project_diff_pos.y():
            #         logger.info("距離確定: %s", cf.length)
            #         break

            #     # 距離を動かす
            #     cf.length += 0.1

            #     if 0 <= cf.frame <= 40:
            #         logger.info("cf.length while: %s", cf.length)

            # if abs(1-org_top_project_pos.y()) < abs(-1+org_bottom_project_pos.y()):
            #     # 上辺のボーンの方が画面端に近い場合、上に合わせる
            #     # 映っている領域の位置
            #     for _ in range(1000):
            #         # 変換先上辺ボーンのプロジェクション位置
            #         rep_top_project_pos = calc_project_pos(rep_top_global_pos, cf)

            #         if 0 <= cf.frame <= 40:
            #             logger.info("-----------")
            #             logger.info("rep_top_project_pos: %s", rep_top_project_pos)

            #         # 作成元のプロジェクション位置を下回った場合、ループ終了
            #         if rep_top_project_pos.y() >= org_bottom_project_pos.y():
            #             break

            #         # Yを動かす
            #         cf.position.setY(cf.position.y() - 0.1)

            #         if 0 <= cf.frame <= 40:
            #             logger.info("cf.position while: %s", cf.position)
            # else:

            # # else:
            #     # 下にずれている場合
            #     for _ in range(1000):
            #         # 変換先下辺ボーンのプロジェクション位置
            #         rep_bottom_project_pos = calc_project_pos(rep_bottom_global_pos, cf)

            #         if 0 <= cf.frame <= 40:
            #             logger.info("-----------")
            #             logger.info("rep_bottom_project_pos: %s", rep_bottom_project_pos)

            #         # 作成元のプロジェクション位置を下回った場合、ループ終了
            #         if rep_bottom_project_pos.y() >= org_bottom_project_pos.y():
            #             break

            #         # Yを動かす
            #         cf.position.setY(cf.position.y() - 0.1)

            #         if 0 <= cf.frame <= 40:
            #             logger.info("cf.position while: %s", cf.position)



# def calc_camera_relative_pos(org_nearest_bone_global_pos, cf):
#     # カメラの角度
#     camera_qq = calc_camera_qq(cf)

#     camera_pos = calc_camera_pos(cf)
#     logger.info("camera_pos: %s", camera_pos)
    
#     mat = QMatrix4x4()
    
#     # カメラの逆回転で正面に
#     mat.rotate(camera_qq.inverted())
#     # 相対位置
#     mat.translate(camera_pos - org_nearest_bone_global_pos)
#     # カメラの回転を再設定
#     mat.rotate(camera_qq)

#     return mat * QVector3D()

# # カメラの位置（Z位置調整）
# def calc_camera_pos(cf):
#     camera_pos = cf.position
#     if cf.length > 0:
#         # 距離マイナスの場合、Z位置を調整する

#         # カメラの角度
#         camera_qq = calc_camera_qq(cf)
#         logger.debug("cf.euler: %s", cf.euler)
#         logger.debug("camera_qq: %s", camera_qq.toEulerAngles())
#         logger.debug("cf.position: %s", cf.position)
#         logger.debug("cf.length: %s", cf.length)

#         mat = QMatrix4x4()
#         # 初期位置
#         mat.translate(cf.position)
#         # カメラの回転
#         mat.rotate(camera_qq.inverted())
#         # カメラの距離を0にしてみる
#         mat.translate(QVector3D(0,0,-cf.position.z()))

#         camera_pos = mat * QVector3D()
#         # # とりあえずZ距離はなし
#         # camera_pos.setZ(0)
#         # if cf.position.y() < 0 and camera_pos.y() > 0:
#         #     # 元々のY位置がマイナスで、計算後符号が反転した場合、減算
#         #     camera_pos.setY( cf.position.y() - camera_pos.y() )
#         logger.debug("camera_pos mat: %s", camera_pos)

#     logger.debug("camera_pos: %s", camera_pos)
#     return camera_pos







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
