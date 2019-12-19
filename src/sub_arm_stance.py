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

def exec(motion, trace_model, replace_model, output_vmd_path, org_motion_frames):
    if motion.motion_cnt > 0:
        # 上半身補正
        adjust_upper_stance(motion, trace_model, replace_model, output_vmd_path, org_motion_frames)

        if not trace_model.can_arm_sizing or not replace_model.can_arm_sizing:
            # 腕構造チェックがFALSEの場合、スタンス補正なし
            return False

        # 腕補正
        adjust_arm_stance(motion, trace_model, replace_model, org_motion_frames)

    return True

def adjust_upper_stance(motion, trace_model, replace_model, output_vmd_path, org_motion_frames):
    # -----------------------------------------------------------------
    # 上半身の角度補正

    print("■■ 上半身スタンス補正 -----------------")

    # 上半身調整に必要なボーン群
    upper_target_bones = ["上半身", "頭", "首", "左腕", "右腕"]

    # エラーを一度でも出力しているか(腕IK)
    is_error_outputed = False
    error_file_logger = None

    if set(upper_target_bones).issubset(trace_model.bones) and set(upper_target_bones).issubset(replace_model.bones) and "上半身" in motion.frames:
        # 元モデルのリンク生成
        org_head_links, org_head_indexes = trace_model.create_link_2_top_one("頭")
        # 変換先モデルのリンク生成
        rep_head_links, rep_head_indexes = replace_model.create_link_2_top_one("頭")

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

        # 上半身から上半身2への傾き
        rep_target_slope = (replace_model.bones[target_bone_name].position - replace_model.bones["上半身"].position).normalized()
        logger.debug("rep_upper_slope: %s", rep_target_slope)

        prepare_upper_stance(motion, "上半身")

        print("上半身スタンス準備終了")

        for bf in motion.frames["上半身"]:
            if bf.key == True:
                # 元モデルの向いている回転量
                org_upper_direction_all_qq = utils.calc_upper_direction_qq(trace_model, org_head_links[org_head_indexes["上半身"]:], org_motion_frames, bf)
                # 先モデルの向いている回転量
                rep_upper_direction_all_qq = utils.calc_upper_direction_qq(replace_model, rep_head_links[rep_head_indexes["上半身"]:], motion.frames, bf)
                org_upper_direction_qq = QQuaternion.fromEulerAngles(0, org_upper_direction_all_qq.toEulerAngles().y(), 0)
                rep_upper_direction_qq = QQuaternion.fromEulerAngles(0, rep_upper_direction_all_qq.toEulerAngles().y(), 0)
                logger.debug("f: %s, rep_upper_direction_qq: %s", bf.frame, rep_upper_direction_qq.toEulerAngles())

                # 頭までの位置
                _, _, _, _, org_head_global_3ds = utils.create_matrix_global(trace_model, org_head_links, org_motion_frames, bf, None)
                _, _, _, _, rep_head_global_3ds = utils.create_matrix_global(replace_model, rep_head_links, motion.frames, bf, None)

                # 正面向きの頭までの位置
                org_front_head_global_3ds = utils.create_direction_pos_all(org_upper_direction_qq.inverted(), org_head_global_3ds)
                rep_front_head_global_3ds = utils.create_direction_pos_all(rep_upper_direction_qq.inverted(), rep_head_global_3ds)

                # 頭 or 上半身2の位置
                org_front_upper_pos = org_front_head_global_3ds[len(org_front_head_global_3ds) - org_head_indexes["上半身"] - 1]
                org_front_target_pos = org_front_head_global_3ds[len(org_front_head_global_3ds) - org_head_indexes[target_bone_name] - 1]
                logger.debug("f: %s, org_front_upper_pos: %s", bf.frame, org_front_upper_pos)
                logger.debug("f: %s, org_front_target_pos: %s", bf.frame, org_front_target_pos)

                rep_front_upper_pos = rep_front_head_global_3ds[len(rep_front_head_global_3ds) - rep_head_indexes["上半身"] - 1]
                rep_front_target_pos = rep_front_head_global_3ds[len(rep_front_head_global_3ds) - rep_head_indexes[target_bone_name] - 1]
                logger.debug("f: %s, rep_front_target_pos: %s", bf.frame, rep_front_target_pos)
                logger.debug("f: %s, rep_front_upper_pos: %s", bf.frame, rep_front_upper_pos)

                rep_target_x = rep_front_upper_pos.x() \
                    + ( org_front_target_pos.x() - org_front_upper_pos.x() ) * shoulder_diff_length
                rep_front_target_pos.setX(rep_target_x)
                logger.debug("f: %s, rep_front_upper_pos: %s", bf.frame, rep_front_upper_pos.x())
                logger.debug("f: %s, org_front_target_pos: %s", bf.frame, org_front_target_pos.x())
                logger.debug("f: %s, org_front_upper_pos: %s", bf.frame, org_front_upper_pos.x())
                logger.debug("f: %s, rep_target_x: %s", bf.frame, rep_target_x)

                rep_target_y = rep_front_upper_pos.y() \
                    + ( org_front_target_pos.y() - org_front_upper_pos.y() ) * upper_diff_length
                rep_front_target_pos.setY(rep_target_y)

                rep_target_z = rep_front_upper_pos.z() + rep_target_upper_z_diff  \
                    + ( org_front_target_pos.z() - org_front_upper_pos.z() - org_target_upper_z_diff ) * upper_diff_length
                rep_front_target_pos.setZ(rep_target_z)
                logger.debug("f: %s, rep_front_upper_pos: %s", bf.frame, rep_front_upper_pos.z())
                logger.debug("f: %s, org_front_target_pos: %s", bf.frame, org_front_target_pos.z())
                logger.debug("f: %s, org_front_upper_pos: %s", bf.frame, org_front_upper_pos.z())
                logger.debug("f: %s, rep_target_z: %s", bf.frame, rep_target_z)

                # 上半身の傾き再算出
                rep_upper_qq = QQuaternion.rotationTo(rep_target_slope, (rep_front_target_pos - rep_front_upper_pos).normalized())
                logger.debug("f: %s, rep_front_target_pos: %s", bf.frame, rep_front_target_pos)
                logger.debug("f: %s, rep_front_upper_pos: %s", bf.frame, rep_front_upper_pos)
                logger.debug("f: %s, rep_target_slope: %s", bf.frame, rep_target_slope)
                logger.debug("f: %s, front: %s", bf.frame, rep_upper_qq.toEulerAngles())

                # 上半身の傾き再設定
                rep_upper_qq = QQuaternion.fromEulerAngles(0, bf.rotation.toEulerAngles().y(), 0) * rep_upper_qq
                logger.debug("f: %s, bf: %s", bf.frame, bf.rotation.toEulerAngles())

                org_bfs = [x for x in org_motion_frames["上半身"] if x.frame == bf.frame]
                if len(org_bfs) > 0:
                    # 元にもあるキーである場合、内積チェック
                    uad = abs(QQuaternion.dotProduct(rep_upper_qq, org_bfs[0].rotation))
                    if uad < 0.90:
                        print("%sフレーム目上半身スタンス補正失敗: 角度:%s, uad: %s" % (bf.frame, rep_upper_qq.toEulerAngles(), uad))

                        # 失敗時のみエラーログ出力
                        if not is_error_outputed:
                            is_error_outputed = True
                            if not error_file_logger:
                                error_file_logger = utils.create_error_file_logger(motion, trace_model, replace_model, output_vmd_path)

                        error_file_logger.warning("%sフレーム目上半身スタンス補正失敗: 角度:%s, uad: %s" , bf.frame, rep_upper_qq.toEulerAngles(), uad)
                    else:
                        # 内積の差が小さい場合、回転適用
                        bf.rotation = rep_upper_qq

        if "首" in motion.frames:
            for bf in motion.frames["首"]:
                if bf.key == True:
                    # 元々の上半身回転量
                    org_upper_bone = utils.calc_bone_by_complement(org_motion_frames, "上半身", bf.frame)
                    # 修正後の上半身回転量
                    rep_upper_bone = utils.calc_bone_by_complement(motion.frames, "上半身", bf.frame)

                    bf.rotation = rep_upper_bone.rotation.inverted() * org_upper_bone.rotation * bf.rotation
    
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

            prepare_upper_stance(motion, "上半身2")

            print("上半身2スタンス準備終了")

            for bf in motion.frames["上半身2"]:
                if bf.key == True:
                    # 元モデルの向いている回転量
                    org_upper_direction_qq = utils.calc_upper_direction_qq(trace_model, org_head_links[org_head_indexes["上半身"]:], org_motion_frames, bf)
                    # 先モデルの向いている回転量
                    rep_upper_direction_qq = utils.calc_upper_direction_qq(replace_model, rep_head_links[rep_head_indexes["上半身"]:], motion.frames, bf)
                    logger.debug("f: %s, rep_upper_direction_qq: %s", bf.frame, rep_upper_direction_qq.toEulerAngles())

                    # 頭までの位置
                    _, _, _, _, org_head_global_3ds = utils.create_matrix_global(trace_model, org_head_links, org_motion_frames, bf, None)
                    _, _, _, _, rep_head_global_3ds = utils.create_matrix_global(replace_model, rep_head_links, motion.frames, bf, None)

                    # 正面向きの頭までの位置
                    org_front_head_global_3ds = utils.create_direction_pos_all(org_upper_direction_qq.inverted(), org_head_global_3ds)
                    rep_front_head_global_3ds = utils.create_direction_pos_all(rep_upper_direction_qq.inverted(), rep_head_global_3ds)

                    # 頭の位置
                    org_front_head_pos = org_front_head_global_3ds[len(org_front_head_global_3ds) - org_head_indexes["頭"] - 1]
                    org_front_upper_pos = org_front_head_global_3ds[len(org_front_head_global_3ds) - org_head_indexes["上半身"] - 1]
                    org_front_upper2_pos = org_front_head_global_3ds[len(org_front_head_global_3ds) - org_head_indexes["上半身2"] - 1]

                    rep_front_head_pos = rep_front_head_global_3ds[len(rep_front_head_global_3ds) - rep_head_indexes["頭"] - 1]
                    rep_front_upper_pos = rep_front_head_global_3ds[len(rep_front_head_global_3ds) - rep_head_indexes["上半身"] - 1]
                    rep_front_upper2_pos = rep_front_head_global_3ds[len(rep_front_head_global_3ds) - rep_head_indexes["上半身2"] - 1]
                    logger.debug("f: %s, rep_front_head_pos: %s", bf.frame, rep_front_head_pos)
                    logger.debug("f: %s, rep_front_upper_pos: %s", bf.frame, rep_front_upper_pos)
                    logger.debug("f: %s, rep_front_upper2_pos: %s", bf.frame, rep_front_upper2_pos)

                    rep_head_x = rep_front_upper_pos.x() \
                        + ( org_front_head_pos.x() - org_front_upper_pos.x() ) * shoulder_diff_length
                    rep_front_head_pos.setX(rep_head_x)
                    logger.debug("f: %s, rep_front_upper_pos: %s", bf.frame, rep_front_upper_pos.x())
                    logger.debug("f: %s, org_front_head_pos: %s", bf.frame, org_front_head_pos.x())
                    logger.debug("f: %s, org_front_upper_pos: %s", bf.frame, org_front_upper_pos.x())
                    logger.debug("f: %s, rep_head_x: %s", bf.frame, rep_head_x)

                    rep_head_y = rep_front_upper_pos.y() \
                        + ( org_front_head_pos.y() - org_front_upper_pos.y() ) * upper_diff_length
                    rep_front_head_pos.setY(rep_head_y)

                    rep_head_z = rep_front_upper_pos.z() + rep_head_upper_z_diff  \
                        + ( org_front_head_pos.z() - org_front_upper_pos.z() - org_head_upper_z_diff ) * upper_diff_length
                    rep_front_head_pos.setZ(rep_head_z)
                    logger.debug("f: %s, rep_front_upper_pos: %s", bf.frame, rep_front_upper_pos.z())
                    logger.debug("f: %s, org_front_head_pos: %s", bf.frame, org_front_head_pos.z())
                    logger.debug("f: %s, org_front_upper_pos: %s", bf.frame, org_front_upper_pos.z())
                    logger.debug("f: %s, rep_head_z: %s", bf.frame, rep_head_z)

                    # 上半身2の傾き再算出
                    rep_upper2_qq = QQuaternion.rotationTo(rep_head_slope, (rep_front_head_pos - rep_front_upper2_pos).normalized())
                    logger.debug("f: %s, rep_front_upper2_pos: %s", bf.frame, rep_front_upper2_pos)
                    logger.debug("f: %s, rep_front_head_pos: %s", bf.frame, rep_front_head_pos)
                    logger.debug("f: %s, rep_head_slope: %s", bf.frame, rep_head_slope)
                    logger.debug("f: %s, front: %s", bf.frame, rep_upper2_qq.toEulerAngles())

                    # 上半身の傾き再設定
                    rep_upper2_qq = QQuaternion.fromEulerAngles(0, bf.rotation.toEulerAngles().y(), 0) * rep_upper2_qq
                    logger.debug("f: %s, bf: %s", bf.frame, bf.rotation.toEulerAngles())

                    org_bfs = [x for x in org_motion_frames["上半身2"] if x.frame == bf.frame]
                    if len(org_bfs) > 0:
                        # 元にもあるキーである場合、内積チェック
                        uad = abs(QQuaternion.dotProduct(rep_upper2_qq, org_bfs[0].rotation))
                        if uad < 0.90:
                            print("%sフレーム目上半身2スタンス補正失敗: 角度:%s, uad: %s" % (bf.frame, rep_upper_qq.toEulerAngles(), uad))

                            # 失敗時のみエラーログ出力
                            if not is_error_outputed:
                                is_error_outputed = True
                                if not error_file_logger:
                                    error_file_logger = utils.create_error_file_logger(motion, trace_model, replace_model, output_vmd_path)

                            error_file_logger.warning("%sフレーム目上半身2スタンス補正失敗: 角度:%s, uad: %s" , bf.frame, rep_upper_qq.toEulerAngles(), uad)
                        else:
                            # 内積の差が小さい場合、回転適用
                            bf.rotation = rep_upper2_qq

            if "首" in motion.frames:
                for bf in motion.frames["首"]:
                    if bf.key == True:
                        # 元々の上半身2回転量
                        org_upper2_bone = utils.calc_bone_by_complement(org_motion_frames, "上半身2", bf.frame)
                        # 修正後の上半身2回転量
                        rep_upper2_bone = utils.calc_bone_by_complement(motion.frames, "上半身2", bf.frame)

                        bf.rotation = rep_upper2_bone.rotation.inverted() * org_upper2_bone.rotation * bf.rotation

        print("上半身2スタンス補正終了")


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

    return org_qq, rep_qq, QQuaternion.rotationTo(org_diff_pos, rep_diff_pos)

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
