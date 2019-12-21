# -*- coding: utf-8 -*-
# 移動系ボーン縮尺処理
# 
import logging
import copy
from PyQt5.QtGui import QQuaternion, QVector3D, QVector2D, QMatrix4x4, QVector4D

from VmdWriter import VmdWriter, VmdBoneFrame
from VmdReader import VmdReader
from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader
import utils, sub_arm_ik

logger = logging.getLogger("VmdSizing").getChild(__name__)

def exec(motion, trace_model, replace_model, output_vmd_path, org_motion_frames, error_file_logger):
    if motion.motion_cnt > 0:
        # 上半身補正
        adjust_upper_stance(motion, trace_model, replace_model, output_vmd_path, org_motion_frames, error_file_logger)

        if not trace_model.can_arm_sizing or not replace_model.can_arm_sizing:
            # 腕構造チェックがFALSEの場合、スタンス補正なし
            return False

        # 腕補正
        adjust_arm_stance(motion, trace_model, replace_model, org_motion_frames)

    return True

def adjust_upper_stance(motion, trace_model, replace_model, output_vmd_path, org_motion_frames, error_file_logger):
    # -----------------------------------------------------------------
    # 上半身の角度補正

    print("■■ 上半身スタンス補正 -----------------")

    # 上半身調整に必要なボーン群
    upper_target_bones = ["上半身", "頭", "首", "左腕", "右腕"]

    # エラーを一度でも出力しているか
    is_error_outputed = False

    if set(upper_target_bones).issubset(trace_model.bones) and set(upper_target_bones).issubset(replace_model.bones) and "上半身" in motion.frames:
        # 元モデルのリンク生成
        org_head_links, org_head_indexes = trace_model.create_link_2_top_one("頭")
        org_arm_links, org_arm_indexes = trace_model.create_link_2_top_lr("腕")
        # 変換先モデルのリンク生成
        rep_head_links, rep_head_indexes = replace_model.create_link_2_top_one("頭")
        rep_arm_links, rep_arm_indexes = replace_model.create_link_2_top_lr("腕")

        # 肩幅の差
        org_shoulder_length = (trace_model.bones["左腕"].position - trace_model.bones["右腕"].position).length()
        rep_shoulder_length = (replace_model.bones["左腕"].position - replace_model.bones["右腕"].position).length()
        shoulder_diff_length = rep_shoulder_length / org_shoulder_length
        print("肩幅比率: %s" % shoulder_diff_length)

        # 上半身の差
        org_upper_length = (trace_model.bones["頭"].position - trace_model.bones["上半身"].position).length()
        rep_upper_length = (replace_model.bones["頭"].position - replace_model.bones["上半身"].position).length()
        upper_diff_length = rep_upper_length / org_upper_length
        print("上半身比率: %s" % upper_diff_length)

        # 頭と上半身の差
        target_bone_name = "上半身2" if "上半身2" in trace_model.bones and "上半身2" in replace_model.bones else "頭"
        org_target_upper_z_diff = trace_model.bones[target_bone_name].position.z() - trace_model.bones["上半身"].position.z()
        rep_target_upper_z_diff = replace_model.bones[target_bone_name].position.z() - replace_model.bones["上半身"].position.z()
        logger.debug("org_upper_z_diff: %s", org_target_upper_z_diff)
        logger.debug("rep_upper_z_diff: %s", rep_target_upper_z_diff)

        # 左腕と上半身のZ差
        org_left_arm_z_diff = trace_model.bones["左腕"].position.z() - trace_model.bones["上半身"].position.z()
        rep_left_arm_z_diff = replace_model.bones["左腕"].position.z() - replace_model.bones["上半身"].position.z()
        logger.debug("org_left_arm_z_diff: %s", org_left_arm_z_diff)
        logger.debug("rep_left_arm_z_diff: %s", rep_left_arm_z_diff)

        # 右腕と上半身のZ差
        org_right_arm_z_diff = trace_model.bones["右腕"].position.z() - trace_model.bones["上半身"].position.z()
        rep_right_arm_z_diff = replace_model.bones["右腕"].position.z() - replace_model.bones["上半身"].position.z()
        logger.debug("org_right_arm_z_diff: %s", org_right_arm_z_diff)
        logger.debug("rep_right_arm_z_diff: %s", rep_right_arm_z_diff)

        # 上半身から上半身2への傾き
        rep_target_slope = (replace_model.bones[target_bone_name].position - replace_model.bones["上半身"].position).normalized()
        logger.debug("rep_target_slope: %s", rep_target_slope)
        logger.debug("rep_target_slope: %s", QVector3D.crossProduct(rep_target_slope, QVector3D(-1, 0, 0)))

        # 準備（細分化）
        prepare_upper_stance(motion, "上半身")

        print("上半身スタンス準備終了")

        for bf in motion.frames["上半身"]:
            if bf.key == True:
                rep_upper2_rotation = utils.calc_bone_by_complement(motion.frames, "上半身2", bf.frame).rotation if "上半身2" in trace_model.bones and "上半身2" in replace_model.bones else QQuaternion()

                calc_upper_rotation(org_motion_frames, motion, trace_model, org_head_links, org_head_indexes, org_arm_links, org_arm_indexes, \
                    replace_model, rep_head_links, rep_head_indexes, rep_arm_links, rep_arm_indexes, "上半身", target_bone_name, \
                    shoulder_diff_length, upper_diff_length, org_target_upper_z_diff, rep_target_upper_z_diff, \
                    org_left_arm_z_diff, rep_left_arm_z_diff, org_right_arm_z_diff, rep_right_arm_z_diff, rep_target_slope, \
                    is_error_outputed, error_file_logger, output_vmd_path, bf, QQuaternion())

        print("上半身スタンス補正終了")

        # 上半身2調整に必要なボーン群
        upper2_target_bones = ["上半身", "上半身2", "頭", "首", "左腕", "右腕"]

        if set(upper2_target_bones).issubset(trace_model.bones) and set(upper2_target_bones).issubset(replace_model.bones) and "上半身2" in motion.frames:
            # 頭と上半身の差
            org_head_upper_z_diff = trace_model.bones["頭"].position.z() - trace_model.bones["上半身"].position.z()
            rep_head_upper_z_diff = replace_model.bones["頭"].position.z() - replace_model.bones["上半身"].position.z()
            logger.debug("org_head_upper_z_diff: %s", org_head_upper_z_diff)
            logger.debug("rep_head_upper_z_diff: %s", rep_head_upper_z_diff)

            # 上半身から上半身2への傾き
            rep_head_slope = (replace_model.bones["頭"].position - replace_model.bones["上半身2"].position).normalized()
            logger.debug("rep_head_slope: %s", rep_head_slope)
            logger.debug("rep_head_slope_z: %s", QVector3D.crossProduct(rep_head_slope, QVector3D(-1, 0, 0)))

            # 準備
            prepare_upper_stance(motion, "上半身2")

            print("上半身2スタンス準備終了")

            for bf in motion.frames["上半身2"]:
                if bf.key == True:
                    # 同一フレームの上半身の回転量
                    rep_upper_bone = utils.calc_bone_by_complement(motion.frames, "上半身", bf.frame)
                    calc_upper_rotation(org_motion_frames, motion, trace_model, org_head_links, org_head_indexes, org_arm_links, org_arm_indexes, \
                        replace_model, rep_head_links, rep_head_indexes, rep_arm_links, rep_arm_indexes, "上半身2", "頭", \
                        shoulder_diff_length, upper_diff_length, org_head_upper_z_diff, rep_head_upper_z_diff, \
                        org_left_arm_z_diff, rep_left_arm_z_diff, org_right_arm_z_diff, rep_right_arm_z_diff, rep_head_slope, \
                        is_error_outputed, error_file_logger, output_vmd_path, bf, rep_upper_bone.rotation)

            print("上半身2スタンス補正終了")

        # 首の角度調整
        adjust_neck_rotation(org_motion_frames, motion, trace_model, replace_model)

def calc_upper_rotation(org_motion_frames, motion, trace_model, org_head_links, org_head_indexes, org_arm_links, org_arm_indexes, \
    replace_model, rep_head_links, rep_head_indexes, rep_arm_links, rep_arm_indexes, from_bone_name, to_bone_name, \
    shoulder_diff_length, from_diff_length, org_to_z_diff, rep_to_z_diff, org_left_arm_z_diff, rep_left_arm_z_diff, org_right_arm_z_diff, rep_right_arm_z_diff, rep_from_slope, \
    is_error_outputed, error_file_logger, output_vmd_path, bf, parent_rotation):

    # 処理対象までのモーション情報(処理対象以上のモーション情報を含まない)
    org_target_motion_frames = {}
    for l in org_head_links[org_head_indexes[from_bone_name]:]:
        bone = utils.calc_bone_by_complement(org_motion_frames, l.name, bf.frame)
        org_target_motion_frames[bone.format_name] = [bone]
    
    rep_target_motion_frames = {}
    for l in rep_head_links[rep_head_indexes[from_bone_name]:]:
        bone = utils.calc_bone_by_complement(motion.frames, l.name, bf.frame)
        rep_target_motion_frames[bone.format_name] = [bone]

    # 元モデルの向いている回転量
    org_from_direction_qq = utils.calc_upper_direction_qq(trace_model, org_head_links[org_head_indexes[from_bone_name]:], org_target_motion_frames, bf)
    # 先モデルの向いている回転量
    rep_from_direction_qq = utils.calc_upper_direction_qq(replace_model, rep_head_links[rep_head_indexes[from_bone_name]:], rep_target_motion_frames, bf)
    
    # 頭までの位置
    _, _, _, _, org_head_global_3ds = utils.create_matrix_global(trace_model, org_head_links, org_target_motion_frames, bf, None)
    _, _, _, _, rep_head_global_3ds = utils.create_matrix_global(replace_model, rep_head_links, rep_target_motion_frames, bf, None)

    # 正面向きの頭までの位置
    org_front_head_global_3ds = utils.create_direction_pos_all(org_from_direction_qq.inverted(), org_head_global_3ds)
    rep_front_head_global_3ds = utils.create_direction_pos_all(rep_from_direction_qq.inverted(), rep_head_global_3ds)

    # 上半身位置
    org_front_upper_pos = org_front_head_global_3ds[len(org_front_head_global_3ds) - org_head_indexes["上半身"] - 1]
    # TOボーン(上半身2 or 頭/頭)位置
    org_front_to_pos = org_front_head_global_3ds[len(org_front_head_global_3ds) - org_head_indexes[to_bone_name] - 1]

    rep_front_upper_pos = rep_front_head_global_3ds[len(rep_front_head_global_3ds) - rep_head_indexes["上半身"] - 1]
    rep_front_to_pos = rep_front_head_global_3ds[len(rep_front_head_global_3ds) - rep_head_indexes[to_bone_name] - 1]

    rep_from_pos = rep_head_global_3ds[len(rep_head_global_3ds) - rep_head_indexes[from_bone_name] - 1]

    # ---------------
    # TOボーンの位置再設定

    rep_to_x = rep_front_upper_pos.x() \
        + ( org_front_to_pos.x() - org_front_upper_pos.x() ) * shoulder_diff_length
    rep_front_to_pos.setX(rep_to_x)

    rep_to_y = rep_front_upper_pos.y() \
        + ( org_front_to_pos.y() - org_front_upper_pos.y() ) * from_diff_length
    rep_front_to_pos.setY(rep_to_y)

    rep_to_z = rep_front_upper_pos.z() + rep_to_z_diff \
        + ( org_front_to_pos.z() - org_front_upper_pos.z() - org_to_z_diff ) * shoulder_diff_length
    rep_front_to_pos.setZ(rep_to_z)
    logger.debug("f: %s, rep_to_pos: %s", bf.frame, rep_front_to_pos)

    # 回転を元に戻した位置
    rep_to_pos = utils.create_direction_pos(rep_from_direction_qq, rep_front_to_pos)

    # ---------------

    # 左腕までの位置
    _, _, _, _, org_left_arm_global_3ds = utils.create_matrix_global(trace_model, org_arm_links["左"], org_target_motion_frames, bf, None)
    _, _, _, _, rep_left_arm_global_3ds = utils.create_matrix_global(replace_model, rep_arm_links["左"], rep_target_motion_frames, bf, None)

    # 正面向きの左腕までの位置
    org_front_left_arm_global_3ds = utils.create_direction_pos_all(org_from_direction_qq.inverted(), org_left_arm_global_3ds)
    rep_front_left_arm_global_3ds = utils.create_direction_pos_all(rep_from_direction_qq.inverted(), rep_left_arm_global_3ds)

    # 左腕の位置
    org_front_left_arm_pos = org_front_left_arm_global_3ds[len(org_front_left_arm_global_3ds) - org_arm_indexes["左"]["腕"] - 1]
    rep_front_left_arm_pos = rep_front_left_arm_global_3ds[len(rep_front_left_arm_global_3ds) - rep_arm_indexes["左"]["腕"] - 1]

    rep_front_left_arm_x = rep_front_upper_pos.x() \
        + ( org_front_left_arm_pos.x() - org_front_upper_pos.x() ) * shoulder_diff_length
    rep_front_left_arm_pos.setX(rep_front_left_arm_x)

    rep_front_left_arm_y = rep_front_upper_pos.y() \
        + ( org_front_left_arm_pos.y() - org_front_upper_pos.y() ) * from_diff_length
    rep_front_left_arm_pos.setY(rep_front_left_arm_y)

    rep_front_left_arm_z = rep_front_upper_pos.z() + rep_left_arm_z_diff \
        + ( org_front_left_arm_pos.z() - org_front_upper_pos.z() - org_left_arm_z_diff ) * shoulder_diff_length
    rep_front_left_arm_pos.setZ(rep_front_left_arm_z)
    logger.debug("f: %s, rep_left_arm_pos: %s", bf.frame, rep_front_left_arm_pos)
    
    # 回転を元に戻した位置
    rep_left_arm_pos = utils.create_direction_pos(rep_from_direction_qq, rep_front_left_arm_pos)

    # ---------------

    # 右腕までの位置
    _, _, _, _, org_right_arm_global_3ds = utils.create_matrix_global(trace_model, org_arm_links["右"], org_target_motion_frames, bf, None)
    _, _, _, _, rep_right_arm_global_3ds = utils.create_matrix_global(replace_model, rep_arm_links["右"], rep_target_motion_frames, bf, None)

    # 正面向きの右腕までの位置
    org_front_right_arm_global_3ds = utils.create_direction_pos_all(org_from_direction_qq.inverted(), org_right_arm_global_3ds)
    rep_front_right_arm_global_3ds = utils.create_direction_pos_all(rep_from_direction_qq.inverted(), rep_right_arm_global_3ds)

    # 右腕の位置
    org_front_right_arm_pos = org_front_right_arm_global_3ds[len(org_front_right_arm_global_3ds) - org_arm_indexes["右"]["腕"] - 1]
    rep_front_right_arm_pos = rep_front_right_arm_global_3ds[len(rep_front_right_arm_global_3ds) - rep_arm_indexes["右"]["腕"] - 1]

    rep_front_right_arm_x = rep_front_upper_pos.x() \
        + ( org_front_right_arm_pos.x() - org_front_upper_pos.x() ) * shoulder_diff_length
    rep_front_right_arm_pos.setX(rep_front_right_arm_x)

    rep_front_right_arm_y = rep_front_upper_pos.y() \
        + ( org_front_right_arm_pos.y() - org_front_upper_pos.y() ) * from_diff_length
    rep_front_right_arm_pos.setY(rep_front_right_arm_y)

    rep_front_right_arm_z = rep_front_upper_pos.z() + rep_right_arm_z_diff \
        + ( org_front_right_arm_pos.z() - org_front_upper_pos.z() - org_right_arm_z_diff ) * shoulder_diff_length
    rep_front_right_arm_pos.setZ(rep_front_right_arm_z)
    logger.debug("f: %s, rep_right_arm_pos: %s", bf.frame, rep_front_right_arm_pos)
    
    # 回転を元に戻した位置
    rep_right_arm_pos = utils.create_direction_pos(rep_from_direction_qq, rep_front_right_arm_pos)

    # ---------------
    # FROMの回転量を再計算する
    direction = rep_to_pos - rep_from_pos
    up = QVector3D.crossProduct(direction, (rep_right_arm_pos - rep_left_arm_pos)).normalized()
    from_orientation = QQuaternion.fromDirection(direction, up)
    initial = QQuaternion.fromDirection(rep_from_slope, QVector3D.crossProduct(rep_from_slope, QVector3D(-1, 0, 0)).normalized())
    from_rotation = parent_rotation.inverted() * from_orientation * initial.inverted()
    logger.debug("f: %s, bf: %s", bf.frame, from_rotation.toEulerAngles())

    # org_bfs = [x for x in org_motion_frames[from_bone_name] if x.frame == bf.frame]
    # if len(org_bfs) > 0:
    #     # 元にもあるキーである場合、内積チェック
    #     uad = abs(QQuaternion.dotProduct(from_rotation, org_bfs[0].rotation))
    #     if uad < 0.90:
    #         print("%sフレーム目%sスタンス補正失敗: 角度:%s, uad: %s" % (bf.frame, from_bone_name, from_rotation.toEulerAngles(), uad))

    #         # 失敗時のみエラーログ出力
    #         if not is_error_outputed:
    #             is_error_outputed = True
    #             if not error_file_logger:
    #                 error_file_logger = utils.create_error_file_logger(motion, trace_model, replace_model, output_vmd_path)

    #         error_file_logger.warning("%sフレーム目%sスタンス補正失敗: 角度:%s, uad: %s" , bf.frame, from_bone_name, from_rotation.toEulerAngles(), uad)
    #     else:
    #         # 内積の差が小さい場合、回転適用
    #         bf.rotation = from_rotation
    bf.rotation = from_rotation


def adjust_neck_rotation(org_motion_frames, motion, trace_model, replace_model):
    if "首" in motion.frames:
        for bf in motion.frames["首"]:
            if bf.key == True:
                # 元々の上半身回転量
                org_upper_bone = utils.calc_bone_by_complement(org_motion_frames, "上半身", bf.frame)
                # 修正後の上半身回転量
                rep_upper_bone = utils.calc_bone_by_complement(motion.frames, "上半身", bf.frame)

                bf.rotation = rep_upper_bone.rotation.inverted() * org_upper_bone.rotation * bf.rotation

                if "上半身2" in trace_model.bones and "上半身2" in replace_model.bones:
                    # 元々の上半身2回転量
                    org_upper2_bone = utils.calc_bone_by_complement(org_motion_frames, "上半身2", bf.frame)
                    # 修正後の上半身2回転量
                    rep_upper2_bone = utils.calc_bone_by_complement(motion.frames, "上半身2", bf.frame)

                    bf.rotation = rep_upper2_bone.rotation.inverted() * org_upper2_bone.rotation * bf.rotation

def prepare_upper_stance(motion, bone_name):
    for bf_idx in range(len(motion.frames[bone_name])):
        if bf_idx == 0:
            continue

        prev_bf = motion.frames[bone_name][bf_idx - 1]
        bf = motion.frames[bone_name][bf_idx]

        rot_diff_euler = (prev_bf.rotation * bf.rotation.inverted()).toEulerAngles()
        if abs(rot_diff_euler.x()) > 170 or abs(rot_diff_euler.y()) > 170 or abs(rot_diff_euler.z()) > 170:
            # 回転量が半分近い場合、半分に分割しておく            
            frame_no = prev_bf.frame + round((bf.frame - prev_bf.frame) / 2)
            logger.info("bf: %s, 回転量over: %s, f: %s", bf.frame, rot_diff_euler, frame_no)

            if bf.frame != frame_no and prev_bf.frame != frame_no:
                # キーが追加できる状態であれば、追加
                # 補間曲線込みでキーフレーム生成
                fillbf = utils.calc_bone_by_complement(motion.frames, bone_name, frame_no, True)
                fillbf.key = True

                motion.frames[bone_name].insert(bf_idx, fillbf)

                # 前後がある場合、補間曲線を分割する
                x1_idxs = utils.R_x1_idxs
                y1_idxs = utils.R_y1_idxs
                x2_idxs = utils.R_x2_idxs
                y2_idxs = utils.R_y2_idxs
                next_x1v = bf.complement[x1_idxs[3]]
                next_y1v = bf.complement[y1_idxs[3]]
                next_x2v = bf.complement[x2_idxs[3]]
                next_y2v = bf.complement[y2_idxs[3]]
                
                sub_arm_ik.split_complement(motion, next_x1v, next_y1v, next_x2v, next_y2v, prev_bf, bf, fillbf, x1_idxs, y1_idxs, x2_idxs, y2_idxs, bone_name, ",")

def adjust_arm_stance(motion, trace_model, replace_model, org_motion_frames):
    # -----------------------------------------------------------------
    # 腕の角度補正
                
    print("■■ 腕スタンス補正 -----------------")

    all_d_list = [{"肩":"左肩", "腕":"左腕", "ひじ":"左ひじ", "手首":"左手首"}, {"肩":"右肩", "腕":"右腕", "ひじ":"右ひじ", "手首":"右手首"}]
    if set(all_d_list[0].values()).issubset(trace_model.bones) and set(all_d_list[0].values()).issubset(replace_model.bones) and \
        set(all_d_list[1].values()).issubset(trace_model.bones) and set(all_d_list[1].values()).issubset(replace_model.bones):

        # 腕の各パーツの補正角度（キー：ボーン名、値：補正クォータニオン）
        left_arm_stance_qqs = calc_arm_stance(trace_model, replace_model, "左")
        right_arm_stance_qqs = calc_arm_stance(trace_model, replace_model, "右")

        # for lak, lav in left_arm_stance_qqs.items():
        #     logger.debug("lak: %s, lav: %s", lak, lav.toEulerAngles())
        #     logger.debug("lak: %s,lavi: %s", lak, lav.inverted().toEulerAngles())

        for dlist in all_d_list:
            # 方向
            direction = "左" if "左肩" == dlist["肩"] else "右"

            # 方向別
            arm_stance_qqs = left_arm_stance_qqs if direction == "左" else right_arm_stance_qqs

            # # 肩ボーンの入り方はモデルによって異なるため保留
            # if dlist["肩"] in motion.frames:
            #     # 肩
            #     for bf in motion.frames[dlist["肩"]]:
            #         if bf.key == True:
            #             bf.rotation = bf.rotation * arm_stance_qqs["肩"].inverted()
            # if dlist["腕"] in motion.frames:
            #     # 腕
            #     for bf in motion.frames[dlist["腕"]]:
            #         if bf.key == True:
            #             bf.rotation = arm_stance_qqs["肩"] * bf.rotation * arm_stance_qqs["腕"].inverted()

            # 上半身/上半身2の回転量を吸収する
            if dlist["肩"] in motion.frames and "上半身" in trace_model.bones and "上半身" in replace_model.bones:
                for bf in motion.frames[dlist["肩"]]:
                    if bf.key == True:
                        # 元々の上半身回転量
                        org_upper_bone = utils.calc_bone_by_complement(org_motion_frames, "上半身", bf.frame)
                        # 修正後の上半身回転量
                        rep_upper_bone = utils.calc_bone_by_complement(motion.frames, "上半身", bf.frame)

                        bf.rotation = rep_upper_bone.rotation.inverted() * org_upper_bone.rotation * bf.rotation

                        if "上半身2" in trace_model.bones and "上半身2" in replace_model.bones:
                            # 元々の上半身2回転量
                            org_upper2_bone = utils.calc_bone_by_complement(org_motion_frames, "上半身2", bf.frame)
                            # 修正後の上半身2回転量
                            rep_upper2_bone = utils.calc_bone_by_complement(motion.frames, "上半身2", bf.frame)

                            bf.rotation = rep_upper2_bone.rotation.inverted() * org_upper2_bone.rotation * bf.rotation

            if dlist["腕"] in motion.frames:
                # 腕
                for bf in motion.frames[dlist["腕"]]:
                    if bf.key == True:
                        bf.rotation = bf.rotation * arm_stance_qqs[dlist["腕"]]

            if dlist["ひじ"] in motion.frames:
                # ひじ
                for bf in motion.frames[dlist["ひじ"]]:
                    if bf.key == True:
                        bf.rotation = arm_stance_qqs[dlist["腕"]].inverted() * bf.rotation * arm_stance_qqs[dlist["ひじ"]]

            if dlist["手首"] in motion.frames:
                # 手首
                for bf in motion.frames[dlist["手首"]]:
                    if bf.key == True:
                        # arm_stance_qqs[dlist["腕"]].inverted() * 
                        bf.rotation = arm_stance_qqs[dlist["ひじ"]].inverted() * bf.rotation * arm_stance_qqs[dlist["手首"]]

        # finger_bone_names = ["左人指１", "左人指２", "左人指３", "左中指１", "左中指２", "左中指３", "左薬指１", "左薬指２", "左薬指３", "左小指１", "左小指２", "左小指３" \
        #                         , "右人指１", "右人指２", "右人指３", "右中指１", "右中指２", "右中指３", "右薬指１", "右薬指２", "右薬指３", "右小指１", "右小指２", "右小指３"]

        # if set(finger_bone_names).issubset(trace_model.bones) and set(finger_bone_names).issubset(replace_model.bones):
            
        #     # 指の初期角度補正
        #     for direction in ["左", "右"]:

        #         # 方向別
        #         arm_stance_qqs = left_arm_stance_qqs if direction == "左" else right_arm_stance_qqs

        #         for finger_name in ["人指", "中指", "薬指", "小指"]:
        #             # , ("２", "３", "{0}１".format(finger_name), "{0}２".format(finger_name)), ("３", "先", "{0}２".format(finger_name), "{0}３".format(finger_name))
        #             for _fidx, finger_no in enumerate([("１", "２", "手首", "中指１")]):

        #                 from_joint_name = "{0}{1}{2}".format(direction, finger_name, finger_no[0])
        #                 to_joint_name = "{0}{1}{2}".format(direction, finger_name, finger_no[1])
        #                 prev_from_joint_name = "{0}{1}".format(direction, finger_no[2])
        #                 prev_to_joint_name = "{0}{1}".format(direction, finger_no[3])

        #                 finger_stance_qqs = calc_finger_stance(trace_model, replace_model, direction, from_joint_name, to_joint_name)
        #                 prev_finger_stance_qqs = calc_finger_stance(trace_model, replace_model, direction, prev_from_joint_name, prev_to_joint_name)

        #                 if from_joint_name in motion.frames:
        #                     for bf in motion.frames[from_joint_name]:
        #                         if bf.key == True:
        #                             # bf.rotation = arm_stance_qqs["{0}腕".format(direction)].inverted() * arm_stance_qqs["{0}ひじ".format(direction)].inverted() * prev_finger_stance_qqs[prev_from_joint_name].inverted() * bf.rotation * finger_stance_qqs[from_joint_name]
        #                             bf.rotation = prev_finger_stance_qqs[prev_from_joint_name].inverted() * bf.rotation * finger_stance_qqs[from_joint_name]

    print("腕スタンス補正終了")


def calc_upper_stance(trace_model, replace_model, upper_bone):
    org_diff_pos, org_qq = calc_upper_stance_diff(trace_model, upper_bone)
    rep_diff_pos, rep_qq = calc_upper_stance_diff(replace_model, upper_bone)

    return org_qq, rep_qq

def calc_upper_stance_diff(model, fbone):
    from_pos = QVector3D()
    to_pos = QVector3D()
    tail_pos = QVector3D()

    if fbone in model.bones:
        fv = model.bones[fbone]
        from_pos = fv.position
        if fv.tail_position != QVector3D():
            # 表示先が相対パスの場合、保持
            to_pos = from_pos + fv.tail_position
        elif fv.tail_index >= 0:
            to_pos = model.bones[model.bone_indexes[fv.tail_index]].position
    
    from_qq = QQuaternion()
    if from_pos != QVector3D and to_pos != QVector3D:
        logger.debug("from_pos: %s", from_pos)        
        logger.debug("to_pos: %s", to_pos)        

        diff_pos = to_pos - from_pos
        diff_pos.normalize()
        logger.debug("diff_pos: %s", diff_pos)        

        from_qq = QQuaternion.rotationTo(QVector3D(0, 1, 0), diff_pos)
        logger.debug("[z] fbone: %s, from_qq: %s", fbone, from_qq.toEulerAngles())

    return diff_pos, from_qq


def calc_arm_stance(trace_model, replace_model, direction):
    from_bones = ["{0}肩".format(direction), "{0}腕".format(direction), "{0}ひじ".format(direction), "{0}手首".format(direction)]
    to_bones = ["{0}腕".format(direction), "{0}ひじ".format(direction), "{0}手首".format(direction), "{0}中指１".format(direction)]

    return calc_stance(trace_model, replace_model, direction, from_bones, to_bones)


def calc_finger_stance(trace_model, replace_model, direction, from_bone, to_bone):
    return calc_stance(trace_model, replace_model, direction, [from_bone], [to_bone])


def calc_stance(trace_model, replace_model, direction, from_bone, to_bone):
    arm_stance_qqs = {}
    for f, t in zip(from_bone, to_bone):
        org_qq = calc_arm_stance_rotation(trace_model, f, t, direction)
        rep_qq = calc_arm_stance_rotation(replace_model, f, t, direction)

        arm_stance_qqs[f] = rep_qq.inverted() * org_qq

        logger.debug("f: %s, org_qq: %s", f, org_qq.toEulerAngles())
        logger.debug("f: %s, rep_qq: %s", f, rep_qq.toEulerAngles())
        logger.debug("d: %s, f: %s, arm_stance_qqs: %s", direction, f, arm_stance_qqs[f].toEulerAngles())

    return arm_stance_qqs

def calc_arm_stance_rotation(model, fbone, tbone, direction):
    from_pos = QVector3D()
    to_pos = QVector3D()
    tail_pos = QVector3D()

    if tbone in model.bones:
        tv = model.bones[tbone]
        to_pos = tv.position

    if fbone in model.bones:
        fv = model.bones[fbone]
        from_pos = fv.position
        if to_pos == QVector3D():
            if fv.tail_position != QVector3D():
                # 表示先が相対パスの場合、保持
                tail_pos = fv.tail_position
            elif fv.tail_index >= 0:
                to_pos = model.bones[model.bone_indexes[fv.tail_index]].position
    
    if to_pos == QVector3D() and tail_pos != QVector3D():
        to_pos = from_pos + tail_pos
        logger.debug("to_pos 置換: %s", to_pos)

    from_qq = QQuaternion()
    if from_pos != QVector3D and to_pos != QVector3D:
        logger.debug("from_pos: %s", from_pos)        
        logger.debug("to_pos: %s", to_pos)        

        diff_pos = to_pos - from_pos
        diff_pos.normalize()
        logger.debug("diff_pos: %s", diff_pos)        

        # 水平からTOボーンまでの回転量
        direction_x = 1 if direction == "左" else -1
        from_qq = QQuaternion.rotationTo(QVector3D(direction_x, 0, 0), diff_pos)
        logger.debug("[z] d: %s, fbone: %s, from_qq: %s", direction, fbone, from_qq.toEulerAngles())

    return from_qq
