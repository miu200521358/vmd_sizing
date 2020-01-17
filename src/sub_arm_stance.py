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
import utils, sub_arm_ik, sub_move

logger = logging.getLogger("VmdSizing").getChild(__name__)

is_print1 = True

def exec(motion, trace_model, replace_model, output_vmd_path, org_motion_frames, error_file_logger, test_param):
    if motion.motion_cnt > 0:
        # センタースタンス補正
        adjust_center_stance(motion, trace_model, replace_model, org_motion_frames)

        if trace_model.can_upper_sizing and replace_model.can_upper_sizing:
            # 上半身補正
            adjust_upper_stance(motion, trace_model, replace_model, output_vmd_path, org_motion_frames, error_file_logger, test_param)

        # if trace_model.can_arm_sizing and replace_model.can_arm_sizing:
        #     # 肩補正
        #     adjust_shoulder_stance(motion, trace_model, replace_model, output_vmd_path, org_motion_frames, error_file_logger, test_param)
        #     # 腕補正
        #     adjust_arm_stance(motion, trace_model, replace_model, org_motion_frames, test_param)

    return True

# ボーン回転の分散
def spread_rotation(motion, org_motion_frames, replace_model):

    print("■■ 回転分散 -----------------")

    # 左腕の分散
    for target_bones, end_bone_name in [(["左肩", "左腕", "左ひじ", "左手首"], "左手首"), (["右肩", "右腕", "右ひじ", "右手首"], "右手首")]:

        if set(target_bones).issubset(replace_model.bones):
        
            # 手首から親までのボーンリンク
            links, indexes = replace_model.create_link_2_top_one(end_bone_name)
            arm_links = links[:indexes["肩"]+1]

            bone_framenos = []

            # 末端から肩までの有効なキーをすべて対象とする
            for b in arm_links:
                if b.name in motion.frames:
                    for x in motion.frames[b.name]:
                        if x.key == True and x.frame not in bone_framenos:
                            bone_framenos.append(x.frame)

            if len(bone_framenos) == 0:
                continue

            bone_framenos.sort()

            for b in arm_links:
                for fno in bone_framenos:
                    # まず一旦登録する
                    fill_frame_for_spread(motion, b.name, fno)
            
            for b in arm_links:
                for bf_idx, bf in enumerate(motion.frames[b.name]):
                    # 補間曲線を分割する
                    sub_arm_ik.reset_complement_frame(motion, b.name, bf_idx, utils.R_x1_idxs, utils.R_y1_idxs, utils.R_x2_idxs, utils.R_y2_idxs)

            # 親から子までのボーンリンクに変換
            arm_links.reverse()

            for bone_idx, bone in enumerate(arm_links):
                if bone.fixed_axis != QVector3D():
                    # 親ボーン
                    parent_bone = replace_model.bones[replace_model.bone_indexes[bone.parent_index]]

                    if (parent_bone.name, bone.name) in utils.BORN_ROTATION_LIMIT:
                        # 上限が決められているボーンの組合せの場合

                        for bf in motion.frames[bone.name]:
                            parent_bf = fill_frame_for_spread(motion, parent_bone.name, bf.frame)

                            # 回転を分散する
                            parent_result_qq, child_result_qq = utils.spread_qq(bf.frame, parent_bf.rotation, bf.rotation, utils.BORN_ROTATION_LIMIT[(parent_bone.name, bone.name)], bone.fixed_axis)

                            # 自身の回転量を再設定
                            parent_bf.rotation = parent_result_qq
                            bf.rotation = child_result_qq

                        print("分散: %s → %s" % (parent_bone.name, bone.name))
                    
                # if bone.name in motion.frames and bone_idx == len(arm_links) - 1:
                #     # 末端ボーンは、回転分をキャンセルして、元の向きに戻す
                #     for bf in motion.frames[bone.name]:
                #         if bf.key == True:
                #             # 自身の回転量
                #             self_qq = utils.calc_bone_by_complement(motion.frames, bone.name, bf.frame, False).rotation
                #             # 元々の回転量
                #             org_self_qq = utils.calc_bone_by_complement(org_motion_frames, bone.name, bf.frame, False).rotation

                #             bf.rotation = self_qq.inverted() * org_self_qq * bf.rotation

# 分散用のbf取得処理
def fill_frame_for_spread(motion, link_name, fno):
    if not link_name in motion.frames:
        fillbf = VmdBoneFrame()
        fillbf.frame = fno
        fillbf.key = True
        fillbf.name = link_name.encode('cp932').decode('shift_jis').encode('shift_jis')
        fillbf.format_name = link_name
        motion.frames[link_name] = [fillbf]

        return fillbf
    
    for tbf_idx, tbf in enumerate(motion.frames[link_name]):
        if tbf.frame == fno:
            tbf.key = True
            # とりあえず登録対象のキーが既存なので終了
            logger.debug("fill 既存あり: %s, i: %s, f: %s", link_name, tbf_idx, fno)
            return tbf

        elif tbf.frame > fno:
            # 対象のキーがなくて次に行ってしまった場合、挿入
            
            # 補間曲線込みでキーフレーム生成
            fillbf = utils.calc_bone_by_complement(motion.frames, link_name, fno, is_calc_complement=True)
            # キーを登録する
            fillbf.key = True

            motion.frames[link_name].insert(tbf_idx, fillbf)
            logger.debug("fill insert: %s, i: %s, f: %s, key: %s: p: %s", link_name, tbf_idx, fillbf.frame, fillbf.key, fillbf.position)

            return fillbf
    
    # 最後のフレームがなくてそのまま終了してしまった場合は、直前のキーを設定する
    fillbf = copy.deepcopy(tbf)
    # キーフレを現時点のに変える
    fillbf.frame = fno
    # 登録する
    fillbf.key = True
    logger.debug("fill 今回なし: %s, i: %s, f: %s", link_name, tbf_idx, fillbf.frame)
    motion.frames[link_name].append(fillbf)

    return fillbf

def adjust_center_stance(motion, trace_model, replace_model, org_motion_frames):
    # -----------------------------------------------------------------
    # センター位置補正

    print("■■ センタースタンス補正 -----------------")

    # センター調整に必要なボーン群
    center_target_bones = ["センター", "上半身", "下半身", "左足ＩＫ", "右足ＩＫ", "左足", "右足"]

    if set(center_target_bones).issubset(trace_model.bones) and set(center_target_bones).issubset(replace_model.bones) and "センター" in motion.frames:
        all_org_center_links, all_org_center_indexes = trace_model.create_link_2_top_one("下半身")
        all_org_upper_links, all_org_upper_indexes = trace_model.create_link_2_top_one("上半身")
        all_org_leg_ik_links, all_org_leg_ik_indexes = trace_model.create_link_2_top_lr("足ＩＫ")
        all_org_leg_links, all_org_leg_indexes = trace_model.create_link_2_top_lr("足")
        all_rep_center_links, all_rep_center_indexes = replace_model.create_link_2_top_one("下半身")
        all_rep_upper_links, all_rep_upper_indexes = replace_model.create_link_2_top_one("上半身")
        all_rep_leg_ik_links, all_rep_leg_ik_indexes = replace_model.create_link_2_top_lr("足ＩＫ")
        all_rep_leg_links, all_rep_leg_indexes = replace_model.create_link_2_top_lr("足")
        
        org_ik_length = (trace_model.bones["左足"].position - trace_model.bones["左足ＩＫ"].position).length
        rep_ik_length = (replace_model.bones["左足"].position - replace_model.bones["左足ＩＫ"].position).length

        center_trunk_links = {"rep_rilink": all_rep_leg_ik_links["右"], "rep_riindex": all_rep_leg_ik_indexes["右"], \
            "rep_lilink": all_rep_leg_ik_links["左"], "rep_liindex": all_rep_leg_ik_indexes["左"], \
            "org_rilink": all_org_leg_ik_links["右"], "org_riindex": all_org_leg_ik_indexes["右"], \
            "org_lilink": all_org_leg_ik_links["左"], "org_liindex": all_org_leg_ik_indexes["左"], \
            "rep_rlink": all_rep_leg_links["右"], "rep_rindex": all_rep_leg_indexes["右"], \
            "rep_llink": all_rep_leg_links["左"], "rep_lindex": all_rep_leg_indexes["左"], \
            "org_rlink": all_org_leg_links["右"], "org_rindex": all_org_leg_indexes["右"], \
            "org_llink": all_org_leg_links["左"], "org_lindex": all_org_leg_indexes["左"], \
            "rep_clink": all_rep_center_links, "rep_cindex": all_rep_center_indexes, \
            "rep_ulink": all_rep_upper_links, "rep_uindex": all_rep_upper_indexes, \
            "org_clink": all_org_center_links, "org_cindex": all_org_center_indexes, \
            "org_ulink": all_org_upper_links, "org_uindex": all_org_upper_indexes}
        center_ik_links = {"rep_rilink": all_rep_leg_ik_links["右"], "rep_riindex": all_rep_leg_ik_indexes["右"], \
            "rep_lilink": all_rep_leg_ik_links["左"], "rep_liindex": all_rep_leg_ik_indexes["左"], \
            "org_rilink": all_org_leg_ik_links["右"], "org_riindex": all_org_leg_ik_indexes["右"], \
            "org_lilink": all_org_leg_ik_links["左"], "org_liindex": all_org_leg_ik_indexes["左"], \
            "rep_rlink": all_rep_leg_links["右"], "rep_rindex": all_rep_leg_indexes["右"], \
            "rep_llink": all_rep_leg_links["左"], "rep_lindex": all_rep_leg_indexes["左"], \
            "org_rlink": all_org_leg_links["右"], "org_rindex": all_org_leg_indexes["右"], \
            "org_llink": all_org_leg_links["左"], "org_lindex": all_org_leg_indexes["左"], \
            "rep_clink": all_rep_center_links, "rep_cindex": all_rep_center_indexes, \
            "org_clink": all_org_center_links, "org_cindex": all_org_center_indexes, \
            "org_ik_rate": org_ik_length, "rep_ik_length": rep_ik_length}

        # 足IKのXYZの比率
        xz_ratio, y_ratio, leg_ik_stance = sub_move.calc_leg_ik_ratio(trace_model, replace_model, False)

        for bf in motion.frames["センター"]:
            if bf.key == True:
                # センターオフセット再計算
                utils.output_message("f: %s, ** : %s" % (bf.frame, bf.position))
                bf.position += calc_center_offset(org_motion_frames, motion, trace_model, replace_model, bf, xz_ratio, center_ik_links)
                utils.output_message("f: %s, ** ** : %s" % (bf.frame, bf.position))
                bf.position += calc_center_trunk_offset(org_motion_frames, motion, trace_model, replace_model, bf, xz_ratio, center_trunk_links)
                utils.output_message("f: %s, ** ** ** : %s" % (bf.frame, bf.position))

        print("センタースタンス補正終了")


def calc_center_offset(org_motion_frames, motion, trace_model, replace_model, center_bf, xz_ratio, center_ik_links):

    # 元モデルのグローバル位置
    _, _, _, _, org_center_global_3ds = utils.create_matrix_global(trace_model, center_ik_links["org_clink"], org_motion_frames, center_bf, None)
    # グルーブがある場合、こちらの方が子のはずなのでグローバル位置優先採用
    target_org_center_name = "グルーブ" if "グルーブ" in trace_model.bones else "センター"
    org_global_center_pos = org_center_global_3ds[len(org_center_global_3ds) - center_ik_links["org_cindex"][target_org_center_name] - 1]
    org_global_lower_pos = org_center_global_3ds[len(org_center_global_3ds) - center_ik_links["org_cindex"]["下半身"] - 1]    

    _, _, _, _, org_left_ik_global_3ds = utils.create_matrix_global(trace_model, center_ik_links["org_lilink"], org_motion_frames, center_bf, None)
    org_global_left_ik_pos = org_left_ik_global_3ds[len(org_left_ik_global_3ds) - center_ik_links["org_liindex"]["足ＩＫ"] - 1]
    _, _, _, _, org_right_ik_global_3ds = utils.create_matrix_global(trace_model, center_ik_links["org_rilink"], org_motion_frames, center_bf, None)
    org_global_right_ik_pos = org_right_ik_global_3ds[len(org_right_ik_global_3ds) - center_ik_links["org_riindex"]["足ＩＫ"] - 1]

    # 左右の足IKとセンターの差分からセンターのオフセット位置を求める
    org_center_ik_offset = ((org_global_left_ik_pos + org_global_right_ik_pos) / 2 - org_global_center_pos)
    org_center_ik_offset.setX(utils.get_effective_value(org_center_ik_offset.x()))
    org_center_ik_offset.setY(0)
    org_center_ik_offset.setZ(utils.get_effective_value(org_center_ik_offset.z()))
    utils.output_message("f: %s, org_center_ik_offset: %s" % (center_bf.frame, org_center_ik_offset))

    org_center_offset = org_center_ik_offset * xz_ratio
    utils.set_effective_value_vec3(org_center_offset)
    utils.output_message("f: %s, org_center_offset: %s" % (center_bf.frame, org_center_offset))

    # --------

    # 先モデルのグローバル位置
    _, _, _, _, rep_center_global_3ds = utils.create_matrix_global(replace_model, center_ik_links["rep_clink"], motion.frames, center_bf, None)
    # グルーブがある場合、こちらの方が子のはずなのでグローバル位置優先採用
    target_rep_center_name = "グルーブ" if "グルーブ" in replace_model.bones else "センター"
    rep_global_center_pos = rep_center_global_3ds[len(rep_center_global_3ds) - center_ik_links["rep_cindex"][target_rep_center_name] - 1]
    rep_global_lower_pos = rep_center_global_3ds[len(rep_center_global_3ds) - center_ik_links["rep_cindex"]["下半身"] - 1]    

    _, _, _, _, rep_left_ik_global_3ds = utils.create_matrix_global(replace_model, center_ik_links["rep_lilink"], motion.frames, center_bf, None)
    rep_global_left_ik_pos = rep_left_ik_global_3ds[len(rep_left_ik_global_3ds) - center_ik_links["rep_liindex"]["足ＩＫ"] - 1]
    _, _, _, _, rep_right_ik_global_3ds = utils.create_matrix_global(replace_model, center_ik_links["rep_rilink"], motion.frames, center_bf, None)
    rep_global_right_ik_pos = rep_right_ik_global_3ds[len(rep_right_ik_global_3ds) - center_ik_links["rep_riindex"]["足ＩＫ"] - 1]

    # --------------

    # 左右の足IKとセンターの差分からセンターのオフセット位置を求める
    rep_center_ik_offset = ((rep_global_left_ik_pos + rep_global_right_ik_pos) / 2 - rep_global_center_pos)
    utils.set_effective_value_vec3(rep_center_ik_offset)
    rep_center_ik_offset.setY(0)
    utils.output_message("f: %s, rep_center_ik_offset: %s" % (center_bf.frame, rep_center_ik_offset))

    rep_center_offset = rep_center_ik_offset - org_center_offset
    utils.set_effective_value_vec3(rep_center_offset)
    utils.output_message("f: %s, rep_center_offset: %s" % (center_bf.frame, rep_center_offset))

    return rep_center_offset

def calc_center_trunk_offset(org_motion_frames, motion, trace_model, replace_model, center_bf, xz_ratio, center_trunk_links):
    # 元モデルのグローバル位置
    _, _, _, _, org_normal_center_global_3ds = utils.create_matrix_global(trace_model, center_trunk_links["org_clink"], org_motion_frames, center_bf, None)
    org_global_normal_center_pos = org_normal_center_global_3ds[len(org_normal_center_global_3ds) - center_trunk_links["org_cindex"]["センター"] - 1]

    # --------

    # 上半身正面向き
    org_normal_upper_direction_all_qq = utils.calc_upper_direction_qq(trace_model, center_trunk_links["org_ulink"], org_motion_frames, center_bf)
    org_normal_upper_direction_qq = QQuaternion.fromEulerAngles(0, org_normal_upper_direction_all_qq.toEulerAngles().y(), 0)
    org_front_global_normal_upper_center_pos = utils.create_direction_pos(org_normal_upper_direction_qq.inverted(), org_global_normal_center_pos)

    org_upper_motion_frames = {}
    for e, l in enumerate(center_trunk_links["org_ulink"]):
        bone = utils.calc_bone_by_complement(org_motion_frames, l.name, center_bf.frame)
        if e == len(center_trunk_links["org_ulink"]) - 1:
            #一番親に上半身の位置を追加する
            bone.position += QVector3D(trace_model.bones["上半身"].position.x() - trace_model.bones["センター"].position.x(), 0, trace_model.bones["上半身"].position.z() - trace_model.bones["センター"].position.z())
        org_upper_motion_frames[bone.format_name] = [bone]

    # 上半身位置に基づく元モデルのグローバル位置
    _, _, _, _, org_upper_center_global_3ds = utils.create_matrix_global(trace_model, center_trunk_links["org_ulink"], org_upper_motion_frames, center_bf, None)
    org_global_upper_center_pos = org_upper_center_global_3ds[len(org_upper_center_global_3ds) - center_trunk_links["org_uindex"]["センター"] - 1]

    # 上半身位置に基づく上半身正面向き
    org_upper_upper_direction_all_qq = utils.calc_upper_direction_qq(trace_model, center_trunk_links["org_ulink"], org_upper_motion_frames, center_bf)
    org_upper_upper_direction_qq = QQuaternion.fromEulerAngles(0, org_upper_upper_direction_all_qq.toEulerAngles().y(), 0)
    org_front_global_upper_upper_center_pos = utils.create_direction_pos(org_upper_upper_direction_qq.inverted(), org_global_upper_center_pos)
    org_front_global_upper_upper_center_pos -= QVector3D(trace_model.bones["上半身"].position.x() - trace_model.bones["センター"].position.x(), 0, trace_model.bones["上半身"].position.z() - trace_model.bones["センター"].position.z())

    # ------------

    # 下半身正面向き
    org_normal_lower_direction_all_qq = utils.calc_upper_direction_qq(trace_model, center_trunk_links["org_clink"], org_motion_frames, center_bf)
    org_normal_lower_direction_qq = QQuaternion.fromEulerAngles(0, org_normal_lower_direction_all_qq.toEulerAngles().y(), 0)
    org_front_global_normal_lower_center_pos = utils.create_direction_pos(org_normal_lower_direction_qq.inverted(), org_global_normal_center_pos)

    org_lower_motion_frames = {}
    for e, l in enumerate(center_trunk_links["org_ulink"]):
        bone = utils.calc_bone_by_complement(org_motion_frames, l.name, center_bf.frame)
        if e == len(center_trunk_links["org_ulink"]) - 1:
            #一番親に下半身の位置を追加する
            bone.position += QVector3D(trace_model.bones["下半身"].position.x() - trace_model.bones["センター"].position.x(), 0, trace_model.bones["下半身"].position.z() - trace_model.bones["センター"].position.z())
        org_lower_motion_frames[bone.format_name] = [bone]

    # 下半身位置に基づく元モデルのグローバル位置
    _, _, _, _, org_lower_center_global_3ds = utils.create_matrix_global(trace_model, center_trunk_links["org_clink"], org_lower_motion_frames, center_bf, None)
    org_global_lower_center_pos = org_lower_center_global_3ds[len(org_lower_center_global_3ds) - center_trunk_links["org_cindex"]["センター"] - 1]

    # 下半身位置に基づく下半身正面向き
    org_lower_lower_direction_all_qq = utils.calc_upper_direction_qq(trace_model, center_trunk_links["org_ulink"], org_lower_motion_frames, center_bf)
    org_lower_lower_direction_qq = QQuaternion.fromEulerAngles(0, org_lower_lower_direction_all_qq.toEulerAngles().y(), 0)
    org_front_global_lower_lower_center_pos = utils.create_direction_pos(org_lower_lower_direction_qq.inverted(), org_global_lower_center_pos)
    org_front_global_lower_lower_center_pos -= QVector3D(trace_model.bones["下半身"].position.x() - trace_model.bones["センター"].position.x(), 0, trace_model.bones["下半身"].position.z() - trace_model.bones["センター"].position.z())

    # ---------------------------------

    # 先モデルのグローバル位置
    _, _, _, _, rep_normal_center_global_3ds = utils.create_matrix_global(replace_model, center_trunk_links["rep_clink"], motion.frames, center_bf, None)
    rep_global_normal_center_pos = rep_normal_center_global_3ds[len(rep_normal_center_global_3ds) - center_trunk_links["rep_cindex"]["センター"] - 1]

    # --------

    # 上半身正面向き
    rep_normal_upper_direction_all_qq = utils.calc_upper_direction_qq(replace_model, center_trunk_links["rep_ulink"], motion.frames, center_bf)
    rep_normal_upper_direction_qq = QQuaternion.fromEulerAngles(0, rep_normal_upper_direction_all_qq.toEulerAngles().y(), 0)
    rep_front_global_normal_upper_center_pos = utils.create_direction_pos(rep_normal_upper_direction_qq.inverted(), rep_global_normal_center_pos)

    rep_upper_motion_frames = {}
    for e, l in enumerate(center_trunk_links["rep_ulink"]):
        bone = utils.calc_bone_by_complement(motion.frames, l.name, center_bf.frame)
        if e == len(center_trunk_links["rep_ulink"]) - 1:
            #一番親に上半身の位置を追加する
            bone.position += QVector3D(replace_model.bones["上半身"].position.x() - replace_model.bones["センター"].position.x(), 0, replace_model.bones["上半身"].position.z() - replace_model.bones["センター"].position.z())
        rep_upper_motion_frames[bone.format_name] = [bone]

    # 上半身位置に基づく元モデルのグローバル位置
    _, _, _, _, rep_upper_center_global_3ds = utils.create_matrix_global(replace_model, center_trunk_links["rep_ulink"], rep_upper_motion_frames, center_bf, None)
    rep_global_upper_center_pos = rep_upper_center_global_3ds[len(rep_upper_center_global_3ds) - center_trunk_links["rep_uindex"]["センター"] - 1]

    # 上半身位置に基づく上半身正面向き
    rep_upper_upper_direction_all_qq = utils.calc_upper_direction_qq(replace_model, center_trunk_links["rep_ulink"], rep_upper_motion_frames, center_bf)
    rep_upper_upper_direction_qq = QQuaternion.fromEulerAngles(0, rep_upper_upper_direction_all_qq.toEulerAngles().y(), 0)
    rep_front_global_upper_upper_center_pos = utils.create_direction_pos(rep_upper_upper_direction_qq.inverted(), rep_global_upper_center_pos)
    rep_front_global_upper_upper_center_pos -= QVector3D(replace_model.bones["上半身"].position.x() - replace_model.bones["センター"].position.x(), 0, replace_model.bones["上半身"].position.z() - replace_model.bones["センター"].position.z())

    # ------------

    # 下半身正面向き
    rep_normal_lower_direction_all_qq = utils.calc_upper_direction_qq(replace_model, center_trunk_links["rep_clink"], motion.frames, center_bf)
    rep_normal_lower_direction_qq = QQuaternion.fromEulerAngles(0, rep_normal_lower_direction_all_qq.toEulerAngles().y(), 0)
    rep_front_global_normal_lower_center_pos = utils.create_direction_pos(rep_normal_lower_direction_qq.inverted(), rep_global_normal_center_pos)

    rep_lower_motion_frames = {}
    for e, l in enumerate(center_trunk_links["rep_ulink"]):
        bone = utils.calc_bone_by_complement(motion.frames, l.name, center_bf.frame)
        if e == len(center_trunk_links["rep_ulink"]) - 1:
            #一番親に下半身の位置を追加する
            bone.position += QVector3D(replace_model.bones["下半身"].position.x() - replace_model.bones["センター"].position.x(), 0, replace_model.bones["下半身"].position.z() - replace_model.bones["センター"].position.z())
        rep_lower_motion_frames[bone.format_name] = [bone]

    # 下半身位置に基づく元モデルのグローバル位置
    _, _, _, _, rep_lower_center_global_3ds = utils.create_matrix_global(replace_model, center_trunk_links["rep_clink"], rep_lower_motion_frames, center_bf, None)
    rep_global_lower_center_pos = rep_lower_center_global_3ds[len(rep_lower_center_global_3ds) - center_trunk_links["rep_cindex"]["センター"] - 1]

    # 下半身位置に基づく下半身正面向き
    rep_lower_lower_direction_all_qq = utils.calc_upper_direction_qq(replace_model, center_trunk_links["rep_ulink"], rep_lower_motion_frames, center_bf)
    rep_lower_lower_direction_qq = QQuaternion.fromEulerAngles(0, rep_lower_lower_direction_all_qq.toEulerAngles().y(), 0)
    rep_front_global_lower_lower_center_pos = utils.create_direction_pos(rep_lower_lower_direction_qq.inverted(), rep_global_lower_center_pos)
    rep_front_global_lower_lower_center_pos -= QVector3D(replace_model.bones["下半身"].position.x() - replace_model.bones["センター"].position.x(), 0, replace_model.bones["下半身"].position.z() - replace_model.bones["センター"].position.z())

    # --------------------
    
    # センターの上半身回転差分
    front_center_upper_diff = (rep_front_global_normal_upper_center_pos - rep_front_global_upper_upper_center_pos) \
        - ((org_front_global_normal_upper_center_pos - org_front_global_upper_upper_center_pos) * xz_ratio)
    utils.set_effective_value_vec3(front_center_upper_diff)
    front_center_upper_diff.setY(0)
    utils.output_message("f: %s, front_center_upper_diff: %s" % (center_bf.frame, front_center_upper_diff))

    # センターの下半身回転差分
    front_center_lower_diff = (rep_front_global_normal_lower_center_pos - rep_front_global_lower_lower_center_pos) \
        - ((org_front_global_normal_lower_center_pos - org_front_global_lower_lower_center_pos) * xz_ratio)
    utils.set_effective_value_vec3(front_center_lower_diff)
    front_center_lower_diff.setY(0)
    utils.output_message("f: %s, front_center_lower_diff: %s" % (center_bf.frame, front_center_lower_diff))

    # ----------

    # 元々の方向に向かせる
    center_upper_diff = utils.create_direction_pos(rep_normal_upper_direction_qq, front_center_upper_diff)
    center_lower_diff = utils.create_direction_pos(rep_normal_lower_direction_qq, front_center_lower_diff)

    # 比率差分の平均
    center_trunk_offset = (center_upper_diff + center_lower_diff) / 2
    utils.output_message("f: %s, center_trunk_offset: %s" % (center_bf.frame, center_trunk_offset))

    return center_trunk_offset

# ------------------------
def adjust_upper_stance(motion, trace_model, replace_model, output_vmd_path, org_motion_frames, error_file_logger, test_param):
    # -----------------------------------------------------------------
    # 上半身の角度補正

    print("■■ 上半身スタンス補正 -----------------")

    # 上半身調整に必要なボーン群
    upper_target_bones = ["上半身", "頭", "首", "左腕", "右腕"]

    # エラーを一度でも出力しているか
    is_error_outputed = False

    if set(upper_target_bones).issubset(trace_model.bones) and set(upper_target_bones).issubset(replace_model.bones) and "上半身" in motion.frames:
        target_bone_name = "上半身2" if "上半身2" in trace_model.bones and "上半身2" in replace_model.bones else "頭"

        # 元モデルのリンク生成
        org_head_links, org_head_indexes = trace_model.create_link_2_top_one("頭")
        org_upper_links, org_upper_indexes = trace_model.create_link_2_top_one("上半身")
        org_arm_links, org_arm_indexes = trace_model.create_link_2_top_lr("腕")
        # 変換先モデルのリンク生成
        rep_head_links, rep_head_indexes = replace_model.create_link_2_top_one("頭")
        rep_upper_links, rep_upper_indexes = replace_model.create_link_2_top_one("上半身")
        rep_arm_links, rep_arm_indexes = replace_model.create_link_2_top_lr("腕")

        # 上半身から上半身2への傾き
        org_upper_slope = (trace_model.bones["頭"].position - trace_model.bones["上半身"].position).normalized()
        rep_upper_slope = (replace_model.bones["頭"].position - replace_model.bones["上半身"].position).normalized()

        # test_tareget = rep_upper_slope
        # rot_params = {"x": test_tareget.x(), "y": test_tareget.y(), "z": test_tareget.z(), \
        #                 "x-": -test_tareget.x(), "y-": -test_tareget.y(), "z-": -test_tareget.z(), \
        #                 "1": 1, "1-": -1, "1.75": 1.75, "1.75-": -1.75, "0": 0}
        # rep_upper_slope_up = QVector3D(rot_params[test_param[0]], rot_params[test_param[1]], rot_params[test_param[2]]).normalized()

        rep_upper_slope_up = QVector3D(-1, 0, 0)

        # 四つん這いモデル
        # rep_target_slope_up = QVector3D.crossProduct(org_target_slope, rep_target_slope)
        # if rep_target_slope_up == QVector3D():
        #     # 元モデルと先モデルが同じ場合、初期値に戻る
        #     rep_target_slope_up = QVector3D(-1, 0, 0)
        # rep_target_slope_cross = QVector3D.crossProduct(rep_target_slope, rep_target_slope_up).normalized()

        rep_upper_slope_cross = QVector3D.crossProduct(rep_upper_slope, rep_upper_slope_up).normalized()
        logger.debug("上半身 slope: %s", rep_upper_slope)
        logger.debug("上半身 cross: %s", rep_upper_slope_cross)

        rep_upper_initial_slope_qq = QQuaternion.fromDirection(rep_upper_slope, rep_upper_slope_cross)

        # print("up: %s" % QVector3D.crossProduct(org_target_slope, rep_target_slope))

        # 準備（細分化）
        prepare_split_stance(motion, "上半身")

        print("上半身スタンス準備終了")

        for bf in motion.frames["上半身"]:
            if bf.key == True:
                calc_rotation_stance(org_motion_frames, motion, trace_model, org_upper_links, org_upper_indexes, org_head_links, org_head_indexes, org_arm_links, org_arm_indexes, \
                    replace_model, rep_upper_links, rep_upper_indexes, rep_head_links, rep_head_indexes, rep_arm_links, rep_arm_indexes, "", "上半身", "上半身", "頭", "上半身", \
                    rep_upper_initial_slope_qq, is_error_outputed, error_file_logger, output_vmd_path, bf, define_is_rotation_no_check_upper, \
                    define_calc_up_from_upper, define_calc_up_to_upper, 0.9, QVector3D(0, 1, 1), True)

        # 子の角度調整
        # adjust_rotation_by_parent(org_motion_frames, motion, trace_model, replace_model, "首", "上半身", test_param)
        # adjust_rotation_by_parent(org_motion_frames, motion, trace_model, replace_model, "上半身2", "上半身", test_param)
        # adjust_rotation_by_parent(org_motion_frames, motion, trace_model, replace_model, "右肩", "上半身", test_param)
        # adjust_rotation_by_parent(org_motion_frames, motion, trace_model, replace_model, "右肩", "上半身", test_param)

        print("上半身スタンス補正終了")

        # 上半身2調整に必要なボーン群
        upper2_target_bones = ["上半身", "上半身2", "頭", "首", "左腕", "右腕"]

        if set(upper2_target_bones).issubset(trace_model.bones) and set(upper2_target_bones).issubset(replace_model.bones) and "上半身2" in motion.frames:
            # リンク生成
            org_head_links, org_head_indexes = trace_model.create_link_2_top_one("頭")
            rep_head_links, rep_head_indexes = replace_model.create_link_2_top_one("頭")

            # 頭,上半身2,0,0,0,首,上半身,x-,y-,z,1,d2,1,首,上半身2_True,True,False,False,False,False_ 0.89#-0.00# 0.00,-13.09# 5.63#-0.06,-4.60#-14.79#-15.53
            # 頭,上半身2,0,0,0,首,上半身,x-,z,y,1,d2,1,首,上半身2_True,True,False,False,False,False_ 0.89#-0.00# 0.00,-13.09# 5.63#-0.06,-4.60#-14.79#-15.53
            # 頭,上半身2,0,0,0,首,上半身,x,z-,y,d2,1,1,首,上半身2_True,True,False,False,False,False_ 0.89#-0.00# 0.00,-13.09# 5.63#-0.06,-4.60#-14.79#-15.53
            # 頭,上半身2,0,0,0,首,上半身,z,x,y,1,d2i,1,首,上半身2_False,True,False,False,False,False_ 0.89# 0.00#-6.11,-13.09# 5.63#-6.17,-4.60#-14.79#-21.64
            # 上半身2,首,1-,0,1,d3i,d3i,d2,0,1,1-_False,False,False,False,True,False_ 1.26# 0.13# 3.60,-5.71# 0.15# 4.08,-0.44# 0.07#-0.77
            # test_param = ["頭","上半身2","0","0","0","首","上半身","z","x","y","1","d2i","1","首","上半身2"]
            # test_param = ["上半身2","頭","0","0","0","首","上半身2","0","1","0","首","上半身"]
            # upper_direction_qq = utils.calc_upper_direction_qq(replace_model, rep_upper_links, motion.frames, bf)
            # test_param = ["上半身2","首","1-","0","1","d3i","d3i","d2","0","1","1-"]

            # rep_upper2_initial_slope2_to = replace_model.bones[test_param[5]].position
            # rep_upper2_initial_slope2_from = replace_model.bones[test_param[6]].position
            # rep_upper2_initial_slope2 = (rep_upper2_initial_slope1_to - rep_upper2_initial_slope1_from).normalized()

            # number_params = {"1": 1, "1-": -1, "1.75": 1.75, "1.75-": -1.75, "0": 0,
            #     "x": rep_upper2_initial_slope2.x(), "x-": -rep_upper2_initial_slope2.x(), 
            #     "y": rep_upper2_initial_slope2.y(), "y-": -rep_upper2_initial_slope2.y(), 
            #     "z": rep_upper2_initial_slope2.z(), "z-": -rep_upper2_initial_slope2.z()}
            # rep_upper2_initial_slope2_up = QVector3D(number_params[test_param[7]], number_params[test_param[8]], number_params[test_param[9]]).normalized()
            # test_param1 = [test_param[5], test_param[6]]

            # number_params = {"1": 1, "1-": -1, "1.75": 1.75, "1.75-": -1.75, "0": 0}
            # rep_upper2_initial_slope2_up = QVector3D(number_params[test_param[7]], number_params[test_param[8]], number_params[test_param[9]]).normalized()

            # # number_params = {"1": 1, "1-": -1, "1.75": 1.75, "1.75-": -1.75, "0": 0}
            # # test_param3 = [number_params[test_param[0]], number_params[test_param[1]], number_params[test_param[2]]]
            # # rep_upper2_initial_slope1_up = QVector3D(test_param3[0], test_param3[1], test_param3[2]).normalized()

            # # test_param2 = [test_param[2], test_param[3]]
            # rep_upper2_initial_slope2_to = replace_model.bones["右腕"].position
            # rep_upper2_initial_slope2_from = replace_model.bones["左腕"].position
            # rep_upper2_initial_slope2 = (rep_upper2_initial_slope2_to - rep_upper2_initial_slope2_from).normalized()
            # rep_upper2_initial_slope2_up = QVector3D(0, 0, -1).normalized()

            # number_params = {"1": 1, "1-": -1, "1.75": 1.75, "1.75-": -1.75, "0": 0}
            # test_param3 = [number_params[test_param[5]], number_params[test_param[6]], number_params[test_param[7]]]
            # rep_upper2_initial_slope2_up = QVector3D(test_param3[0], test_param3[1], test_param3[2]).normalized()

            # # direction_params = {"s1": rep_upper2_initial_slope1, "u1": rep_upper2_initial_slope1_up}
            # # test_param4 = [direction_params[test_param[3]], direction_params[test_param[4]]]

            # rep_upper2_initial_slope3_to = replace_model.bones[test_param[0]].position
            # rep_upper2_initial_slope3_from = replace_model.bones[test_param[1]].position
            # rep_upper2_initial_slope3 = (rep_upper2_initial_slope1_to - rep_upper2_initial_slope1_from).normalized()

            # rep_upper2_initial_slope4_to = replace_model.bones[test_param[2]].position
            # rep_upper2_initial_slope4_from = replace_model.bones[test_param[3]].position
            # rep_upper2_initial_slope4 = (rep_upper2_initial_slope1_to - rep_upper2_initial_slope1_from).normalized()

            # rep_upper2_initial_slope5_qq = QQuaternion.fromDirection(rep_upper2_initial_slope3, rep_upper2_initial_slope4)

            # direction_params = {"n": rep_upper2_initial_slope5_qq, "i": rep_upper2_initial_slope5_qq.inverted()}  

            # rep_upper2_initial_slope_qq = QQuaternion.fromDirection(QVector3D.crossProduct(rep_upper2_initial_slope2_up, rep_upper2_initial_slope2), rep_upper2_initial_slope1) * direction_params[test_param[4]]

            # # rep_upper2_initial_slope2_up = QVector3D(rot_params[test_param[3]], rot_params[test_param[4]], rot_params[test_param[5]]).normalized()

            # test_tareget = rep_upper2_initial_slope1
            # rot_params = {"x": test_tareget.x(), "y": test_tareget.y(), "z": test_tareget.z(), \
            #                 "x-": -test_tareget.x(), "y-": -test_tareget.y(), "z-": -test_tareget.z(), \
            #                 "1": 1, "1-": -1, "1.75": 1.75, "1.75-": -1.75, "0": 0}
            # rep_upper2_initial_slope1_up = QVector3D(rot_params[test_param[2]], rot_params[test_param[3]], rot_params[test_param[4]]).normalized()

            # # rep_upper2_initial_slope1_qq = QQuaternion.fromDirection(rep_upper2_initial_slope1, rep_upper2_initial_slope1_up)

            # # --------------

            # # -------------------

            # rot_params = {"1": rep_upper2_initial_slope1_qq, "1-": rep_upper2_initial_slope1_qq.inverted(), \
            #     "2": rep_upper2_initial_slope2_qq, "2-": rep_upper2_initial_slope2_qq.inverted(), 
            #     "3": rep_upper_initial_slope_qq, "3-": rep_upper_initial_slope_qq.inverted(), }

            # rep_upper2_initial_slope_qq = rot_params[test_param[6]] * rot_params[test_param[7]]

            # rep_upper2_slope_up_to = replace_model.bones[test_param[2]].position
            # rep_upper2_slope_up_from = replace_model.bones[test_param[3]].position
            # rep_upper2_slope_up_direction = rep_upper2_slope_up_to - rep_upper2_slope_up_from


            # rep_upper2_slope_up = QVector3D.crossProduct(rep_upper2_slope_up_direction, rep_upper2_slope_up_up)

            # rep_upper2_initial_slope = QQuaternion.fromDirection(rep_upper2_slope, rep_upper2_slope_up)


            # # 上半身2から頭への傾き
            # rep_upper2_slope_to = replace_model.bones[test_param[0]].position
            # rep_upper2_slope_from = replace_model.bones[test_param[1]].position
            # rep_upper2_slope = (rep_upper2_slope_to - rep_upper2_slope_from).normalized()



            # rep_upper2_slope_up = QVector3D.crossProduct(rep_upper2_slope_up_direction, rep_upper2_slope_up_up)

            # rep_upper2_initial_slope = QQuaternion.fromDirection(rep_upper2_slope, rep_upper2_slope_up)


            # rep_upper2_slope_up_up_to = replace_model.bones[test_param[4]].position
            # rep_upper2_slope_up_up_from = replace_model.bones[test_param[5]].position
            # rep_upper2_slope_up_up_direction = rep_upper2_slope_up_up_to - rep_upper2_slope_up_up_from





            # rep_upper2_slope_up_direction = (replace_model.bones["頭"].position - replace_model.bones["首"].position).normalized()
            # rep_upper2_slope_up_direction = (replace_model.bones["左腕"].position - replace_model.bones["右腕"].position).normalized()


            # # rep_upper2_slope_up_up = QVector3D(0, -1, -1)
            # # rep_upper2_slope_up = QVector3D.crossProduct(rep_upper2_slope_up_direction, rep_upper2_slope_up_up)
            # # rep_upper2_slope_up = QVector3D(-1, 0, 0)

            # rep_upper2_slope_up_direction_to = replace_model.bones[test_param[0]].position
            # rep_upper2_slope_up_direction_from = replace_model.bones[test_param[1]].position
            # rep_upper2_slope_up_direction_direction = rep_upper2_slope_up_direction_to - rep_upper2_slope_up_direction_from

            # test_tareget = rep_upper2_slope
            # rot_params = {"x": test_tareget.x(), "y": test_tareget.y(), "z": test_tareget.z(), \
            #                 "x-": -test_tareget.x(), "y-": -test_tareget.y(), "z-": -test_tareget.z(), \
            #                 "1": 1, "1-": -1, "1.75": 1.75, "1.75-": -1.75, "0": 0}
            # rep_upper2_slope_up_direction_up = QVector3D(rot_params[test_param[2]], rot_params[test_param[3]], rot_params[test_param[4]]).normalized()
            # rep_upper2_slope_up_direction = QVector3D.crossProduct(rep_upper2_slope_up_direction_direction, rep_upper2_slope_up_direction_up)

            # rep_upper2_slope_up_up_to = replace_model.bones[test_param[5]].position
            # rep_upper2_slope_up_up_from = replace_model.bones[test_param[6]].position
            # rep_upper2_slope_up_up_direction = rep_upper2_slope_up_up_to - rep_upper2_slope_up_up_from

            # test_tareget = rep_upper2_slope
            # rot_params = {"x": test_tareget.x(), "y": test_tareget.y(), "z": test_tareget.z(), \
            #                 "x-": -test_tareget.x(), "y-": -test_tareget.y(), "z-": -test_tareget.z(), \
            #                 "1": 1, "1-": -1, "1.75": 1.75, "1.75-": -1.75, "0": 0}
            # rep_upper2_slope_up_up_up = QVector3D(rot_params[test_param[7]], rot_params[test_param[8]], rot_params[test_param[9]]).normalized()
            # rep_upper2_slope_up_up = QVector3D.crossProduct(rep_upper2_slope_up_up_direction, rep_upper2_slope_up_up_up)

            # rep_upper2_slope_up = QVector3D.crossProduct(rep_upper2_slope_up_direction, rep_upper2_slope_up_up)

            # rep_upper2_slope_cross = QVector3D.crossProduct(rep_upper2_slope, rep_upper2_slope_up)

            # logger.debug("上半身2 slope: %s", rep_upper2_slope)
            # logger.debug("上半身2 cross: %s", rep_upper2_slope_cross)

            


            # 首,上半身,右腕,左腕,0,0,1-,u1,s2,s1_False,False,False_ 3.37#-0.00# 3.61,-3.60# 0.00# 4.09, 1.63#-0.37#-0.74
            # 上半身2から頭への傾き
            rep_upper2_initial_slope1_to = replace_model.bones[test_param[0]].position
            rep_upper2_initial_slope1_from = replace_model.bones[test_param[1]].position
            rep_upper2_initial_slope1 = (rep_upper2_initial_slope1_to - rep_upper2_initial_slope1_from).normalized()

            number_params = {"1": 1, "1-": -1, "1.75": 1.75, "1.75-": -1.75, "0": 0,
                "x": rep_upper_slope.x(), "x-": -rep_upper_slope.x(), 
                "y": rep_upper_slope.y(), "y-": -rep_upper_slope.y(), 
                "z": rep_upper_slope.z(), "z-": -rep_upper_slope.z()}
            rep_upper1_initial_slope1_up = QVector3D(number_params[test_param[2]], number_params[test_param[3]], number_params[test_param[4]]).normalized()

            rep_upper2_initial_slope1_to = replace_model.bones[test_param[5]].position
            rep_upper2_initial_slope1_from = replace_model.bones[test_param[6]].position
            rep_upper2_initial_slope3 = (rep_upper2_initial_slope1_to - rep_upper2_initial_slope1_from).normalized()

            rep_upper2_initial_slope3_up = QVector3D(number_params[test_param[7]], number_params[test_param[8]], number_params[test_param[9]]).normalized()

            direction_params = { \
                "d1": QQuaternion.fromDirection(rep_upper2_initial_slope1, rep_upper1_initial_slope1_up), \
                "d1i": QQuaternion.fromDirection(rep_upper2_initial_slope1, rep_upper1_initial_slope1_up).inverted(), \
                "d2": QQuaternion.fromDirection(rep_upper2_initial_slope3, rep_upper2_initial_slope3_up), \
                "d2i": QQuaternion.fromDirection(rep_upper2_initial_slope3, rep_upper2_initial_slope3_up).inverted(), \
                "d3": QQuaternion.fromDirection(rep_upper2_initial_slope1, rep_upper_slope), \
                "d3i": QQuaternion.fromDirection(rep_upper2_initial_slope1, rep_upper_slope).inverted(), \
                "d4": QQuaternion.fromDirection(rep_upper2_initial_slope3, rep_upper_slope), \
                "d4i": QQuaternion.fromDirection(rep_upper2_initial_slope3, rep_upper_slope).inverted(), \
                "d5": rep_upper_initial_slope_qq, \
                "d5i": rep_upper_initial_slope_qq.inverted(), \
                "00": QQuaternion(), "01": QQuaternion(), "02": QQuaternion()}

            rep_upper2_initial_slope_qq = direction_params[test_param[10]] * direction_params[test_param[11]] * direction_params[test_param[12]] * direction_params[test_param[13]]

            # 準備
            prepare_split_stance(motion, "上半身2")

            print("上半身2スタンス準備終了")

            for bf in motion.frames["上半身2"]:
                if bf.key == True:
                    calc_rotation_stance(org_motion_frames, motion, trace_model, org_head_links, org_head_indexes, org_head_links, org_head_indexes, org_arm_links, org_arm_indexes, \
                        replace_model, rep_head_links, rep_head_indexes, rep_head_links, rep_head_indexes, rep_arm_links, rep_arm_indexes, "", "上半身2", "上半身2", "頭", "上半身2", \
                        rep_upper2_initial_slope_qq, is_error_outputed, error_file_logger, output_vmd_path, bf, define_is_rotation_no_check_upper, \
                        define_calc_up_from_upper2, define_calc_up_to_upper2, 0.9, QVector3D(0, 1, 1), True)

            # # 子の角度調整
            # adjust_rotation_by_parent(org_motion_frames, motion, trace_model, replace_model, "首", "上半身2", test_param)
            # adjust_rotation_by_parent(org_motion_frames, motion, trace_model, replace_model, "右肩", "上半身2", test_param)
            # adjust_rotation_by_parent(org_motion_frames, motion, trace_model, replace_model, "左肩", "上半身2", test_param)

            print("上半身2スタンス補正終了")

# 定義: 回転チェック不要条件（上半身）
def define_is_rotation_no_check_upper(rep_from_slope):
    return rep_from_slope.z() < -0.4    

# 定義: 傾きを求める方向のFROM位置計算（上半身）
def define_calc_up_from_upper(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param):

    return calc_up_arm(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
        replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
        rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, "左")

# 定義: 傾きを求める方向のTO位置計算（上半身）
def define_calc_up_to_upper(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param):

    return calc_up_arm(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
        replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
        rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, "右")

# 腕の位置計算
def calc_up_arm(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, arm_direction_name):

    return recalc_to_pos(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
        replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
        rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, \
        rot_bone_name, "腕", org_rot_motion_frames, org_rot_direction_qq, org_arm_links[arm_direction_name], org_arm_indexes[arm_direction_name], rep_rot_motion_frames, rep_rot_direction_qq, rep_arm_links[arm_direction_name], rep_arm_indexes[arm_direction_name])

# 定義: 傾きを求める方向のFROM位置計算（上半身2）
def define_calc_up_from_upper2(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param):

    rep_up_from_arm_pos, rep_up_from_arm_initial_pos = calc_up_arm(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
        replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
        rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, "左")
    
    return rep_up_from_arm_pos, rep_up_from_arm_initial_pos 

    # _, _, _, _, rep_from_global_3ds = utils.create_matrix_global(replace_model, rep_target_links, rep_rot_motion_frames, bf, None)
    # rep_up_from_pos = rep_from_global_3ds[len(rep_from_global_3ds) - rep_base_indexes[base_bone_name] - 1]

    # return rep_up_from_pos, rep_up_from_pos

    # rep_up_from_arm_pos, rep_up_from_arm_initial_pos = calc_up_arm(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    #     replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    #     rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, "左")

    # rep_up_to_arm_pos, rep_up_to_arm_initial_pos = calc_up_arm(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    #     replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, to_bone_name, to_bone_name, rot_bone_name, \
    #     rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, "右")

    # return QVector3D.crossProduct(rep_up_to_arm_pos, rep_up_from_arm_pos), QVector3D.crossProduct(rep_up_to_arm_initial_pos, rep_up_from_arm_initial_pos)

    # # 腕の位置を取得する
    # arm_pos, arm_initial_pos = calc_up_arm(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    #     replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    #     rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, "左")

    # # 上半身の位置を取得する
    # _, _, _, _, rep_target_global_3ds = utils.create_matrix_global(replace_model, rep_target_links, rep_rot_motion_frames, bf, None)
    # rep_upper_pos = rep_target_global_3ds[len(rep_target_global_3ds) - rep_target_indexes[] - 1]

    # return QVector3D.crossProduct(arm_pos, rep_upper_pos), QVector3D.crossProduct(arm_initial_pos, rep_upper_pos)

# 定義: 傾きを求める方向のTO位置計算（上半身2）
def define_calc_up_to_upper2(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param):

    rep_up_to_arm_pos, rep_up_to_arm_initial_pos = calc_up_arm(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
        replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, to_bone_name, to_bone_name, rot_bone_name, \
        rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, "右")

    return rep_up_to_arm_pos, rep_up_to_arm_initial_pos

    # _, _, _, _, rep_to_global_3ds = utils.create_matrix_global(replace_model, rep_target_links, rep_rot_motion_frames, bf, None)
    # rep_up_to_pos = rep_to_global_3ds[len(rep_to_global_3ds) - rep_base_indexes[to_bone_name] - 1]

    # return rep_up_to_pos, rep_up_to_pos

    # rep_up_to_pos, rep_up_to_initial_pos = recalc_to_pos(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    #     replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    #     rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, \
    #     base_bone_name, to_bone_name, org_rot_motion_frames, org_rot_direction_qq, org_target_links, org_target_indexes, rep_rot_motion_frames, rep_rot_direction_qq, rep_target_links, rep_target_indexes)

    # rep_up_from_pos, rep_up_from_initial_pos = recalc_to_pos(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    #     replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    #     rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, \
    #     base_bone_name, to_bone_name, org_rot_motion_frames, org_rot_direction_qq, org_target_links, org_target_indexes, rep_rot_motion_frames, rep_rot_direction_qq, rep_target_links, rep_target_indexes)

    # return QVector3D.crossProduct(rep_up_to_pos, rep_up_from_pos), QVector3D.crossProduct(rep_up_to_initial_pos, rep_up_from_initial_pos)

    # _, _, _, _, rep_to_global_3ds = utils.create_matrix_global(replace_model, rep_base_links, rep_rot_motion_frames, bf, None)
    # rep_up_to_pos = rep_to_global_3ds[len(rep_to_global_3ds) - rep_base_indexes[rot_bone_name] - 1]

    # return rep_up_to_pos, rep_up_to_pos

    # # 腕の位置を取得する
    # arm_pos, arm_initial_pos = calc_up_arm(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    #     replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    #     rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_   rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, "右")

    # # 上半身の位置を取得する
    # _, _, _, _, rep_target_global_3ds = utils.create_matrix_global(replace_model, rep_target_links, rep_rot_motion_frames, bf, None)
    # rep_upper_pos = rep_target_global_3ds[len(rep_target_global_3ds) - rep_target_indexes["上半身"] - 1]

    # return QVector3D.crossProduct(arm_pos, rep_upper_pos), QVector3D.crossProduct(arm_initial_pos, rep_upper_pos)

    # return calc_up_arm(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    #     replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    #     rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, "右")

# ------------------------
def adjust_shoulder_stance(motion, trace_model, replace_model, output_vmd_path, org_motion_frames, error_file_logger, test_param):
    # -----------------------------------------------------------------
    # 肩の角度補正

    print("■■ 肩スタンス補正 -----------------")

    adjust_shoulder_stance_direction(motion, trace_model, replace_model, output_vmd_path, org_motion_frames, error_file_logger, "左", test_param)
    adjust_shoulder_stance_direction(motion, trace_model, replace_model, output_vmd_path, org_motion_frames, error_file_logger, "右", test_param)

    adjust_rotation_by_parent(org_motion_frames, motion, trace_model, replace_model, "右腕", "右肩", test_param)
    adjust_rotation_by_parent(org_motion_frames, motion, trace_model, replace_model, "左腕", "左肩", test_param)

def adjust_shoulder_stance_direction(motion, trace_model, replace_model, output_vmd_path, org_motion_frames, error_file_logger, direction, test_param):
    # -----------------------------------------------------------------
    # 肩の角度補正

    shoulder_name = "{0}肩".format(direction)
    arm_name = "{0}腕".format(direction)

    # 肩調整に必要なボーン群
    shoulder_target_bones = ["頭", "首", shoulder_name, arm_name, "上半身"]

    # エラーを一度でも出力しているか
    is_error_outputed = False

    if set(shoulder_target_bones).issubset(trace_model.bones) and set(shoulder_target_bones).issubset(replace_model.bones) and shoulder_name in motion.frames:
        # 元モデルのリンク生成
        org_shoulder_links, org_shoulder_indexes = trace_model.create_link_2_top_one(arm_name)
        org_neck_links, org_neck_indexes = trace_model.create_link_2_top_one("首")
        org_arm_links, org_arm_indexes = trace_model.create_link_2_top_lr("腕")
        # 変換先モデルのリンク生成
        rep_shoulder_links, rep_shoulder_indexes = replace_model.create_link_2_top_one(arm_name)
        rep_neck_links, rep_neck_indexes = replace_model.create_link_2_top_one("首")
        rep_arm_links, rep_arm_indexes = replace_model.create_link_2_top_lr("腕")

        rot_bone_name = "上半身2" if "上半身2" in trace_model.bones and "上半身2" in replace_model.bones else "上半身"

        # # 肩から腕への傾き
        # org_base_slope = (trace_model.bones["首"].position - trace_model.bones[arm_name].position).normalized()
        # rep_base_slope = (replace_model.bones["首"].position - replace_model.bones[arm_name].position).normalized()
        # target_base_slope = QVector3D.crossProduct(org_base_slope, rep_base_slope).normalized()

        # rep_target_slope_cross = QVector3D.crossProduct(QVector3D(-1, 0, 0), QVector3D.crossProduct(rep_target_slope, org_target_slope))

        # rep_target_slope_cross = QVector3D.crossProduct(rep_target_slope, QVector3D.crossProduct(org_target_slope, QVector3D(0, 1, 0)))
        # if direction == "左":
        #     # rep_target_slope_cross = QVector3D.crossProduct(QVector3D(-1, 0, 0), QVector3D.crossProduct(rep_target_slope, org_target_slope))
        #     rep_target_slope_cross = QVector3D.crossProduct(org_target_slope, rep_target_slope)
        # else:
        #     rep_target_slope_cross = QVector3D.crossProduct(rep_target_slope, org_target_slope)

        # 準備（細分化）
        prepare_split_stance(motion, shoulder_name)

        print("{0}スタンス準備終了".format(shoulder_name))

        # start_bf = utils.calc_bone_by_complement({}, "ルート", 0)

        # # 直立姿勢のグローバル位置生成
        # _, _, _, _, org_neck_global_3ds = utils.create_matrix_global(trace_model, org_neck_links, {}, start_bf, None)
        # _, _, _, _, rep_neck_global_3ds = utils.create_matrix_global(replace_model, rep_neck_links, {}, start_bf, None)

        # _, _, _, _, org_arm_global_3ds = utils.create_matrix_global(trace_model, org_arm_links[direction], {}, start_bf, None)
        # _, _, _, _, rep_arm_global_3ds = utils.create_matrix_global(replace_model, rep_arm_links[direction], {}, start_bf, None)

        # org_initial_slope = (trace_model.bones[arm_name].position - trace_model.bones[shoulder_name].position).normalized()
        rep_initial_slope_qq = (replace_model.bones[arm_name].position - replace_model.bones[shoulder_name].position).normalized()

        # org_initial_upper_slope = (trace_model.bones["首"].position - trace_model.bones[rot_bone_name].position).normalized()
        # rep_initial_upper_slope_direction = (replace_model.bones["首"].position - replace_model.bones[rot_bone_name].position).normalized()

        # test_tareget = rep_initial_slope_qq
        # rot_params = {"x": test_tareget.x(), "y": test_tareget.y(), "z": test_tareget.z(), \
        #                 "x-": -test_tareget.x(), "y-": -test_tareget.y(), "z-": -test_tareget.z(), \
        #                 "1": 1, "1-": -1, "1.75": 1.75, "1.75-": -1.75, "0": 0}
        # rep_initial_slope_qq_cross = QVector3D(rot_params[test_param[0]], rot_params[test_param[1]], rot_params[test_param[2]]).normalized()

        # rep_initial_slope_qq_cross = QVector3D(-1, 0, 1) if direction == "左" else QVector3D(1, 0, -1)
        rep_initial_slope_qq_cross = QVector3D(-1, 0, -1)
        # rep_initial_slope_qq_cross = QVector3D.crossProduct(rep_initial_slope_qq, QVector3D.crossProduct(rep_initial_upper_slope_direction, rep_initial_upper_slope_up))

        for bf in motion.frames[shoulder_name]:
            if bf.key == True:

                # # 元モデルの向いている回転量
                # org_rot_direction_qq = utils.calc_upper_direction_qq(trace_model, org_neck_links, org_motion_frames, bf)
                # # 先モデルの向いている回転量
                # rep_rot_direction_qq = utils.calc_upper_direction_qq(replace_model, rep_neck_links, motion.frames, bf)

                # org_rot_neck_global_3ds = utils.create_direction_pos_all(org_rot_direction_qq, org_neck_global_3ds)
                # rep_rot_neck_global_3ds = utils.create_direction_pos_all(rep_rot_direction_qq, rep_neck_global_3ds)

                # org_rot_arm_global_3ds = utils.create_direction_pos_all(org_rot_direction_qq, org_arm_global_3ds)
                # rep_rot_arm_global_3ds = utils.create_direction_pos_all(rep_rot_direction_qq, rep_arm_global_3ds)

                # org_rot_neck_pos = org_rot_neck_global_3ds[len(org_rot_neck_global_3ds) - org_neck_indexes["首"] - 1]
                # rep_rot_neck_pos = rep_rot_neck_global_3ds[len(rep_rot_neck_global_3ds) - rep_neck_indexes["首"] - 1]

                # org_rot_shoulder_pos = org_rot_arm_global_3ds[len(org_rot_arm_global_3ds) - org_arm_indexes[direction]["肩"] - 1]
                # rep_rot_shoulder_pos = rep_rot_arm_global_3ds[len(rep_rot_arm_global_3ds) - rep_arm_indexes[direction]["肩"] - 1]

                # org_rot_arm_pos = org_rot_arm_global_3ds[len(org_rot_arm_global_3ds) - org_arm_indexes[direction]["腕"] - 1]
                # rep_rot_arm_pos = rep_rot_arm_global_3ds[len(rep_rot_arm_global_3ds) - rep_arm_indexes[direction]["腕"] - 1]

                # org_rot_upper_pos = org_rot_neck_global_3ds[len(org_rot_neck_global_3ds) - org_neck_indexes[rot_bone_name] - 1]
                # rep_rot_upper_pos = rep_rot_neck_global_3ds[len(rep_rot_neck_global_3ds) - rep_neck_indexes[rot_bone_name] - 1]

                # org_rot_slope = (org_rot_arm_pos - org_rot_neck_pos).normalized()
                # rep_rot_slope = (rep_rot_arm_pos - rep_rot_neck_pos).normalized()

                # org_rot_slope_upper = (org_rot_neck_pos - org_rot_upper_pos).normalized()
                # rep_rot_slope_upper = (rep_rot_neck_pos - rep_rot_upper_pos).normalized()

                # org_rot_slope_shoulder = (org_rot_shoulder_pos - org_rot_arm_pos).normalized()
                # rep_rot_slope_shoulder = (rep_rot_shoulder_pos - rep_rot_arm_pos).normalized()                

                # # # --------------

                # # test_tareget = rep_rot_slope_shoulder
                # # rot_params = {"x": test_tareget.x(), "y": test_tareget.y(), "z": test_tareget.z(), \
                # #                 "x-": -test_tareget.x(), "y-": -test_tareget.y(), "z-": -test_tareget.z(), \
                # #                 "1": 1, "1-": -1, "1.75": 1.75, "1.75-": -1.75, "0": 0}
                # # base_cross = QVector3D(rot_params[test_param[0]], rot_params[test_param[1]], rot_params[test_param[2]]).normalized()

                # # rep_rot_target_slope_up = QVector3D.crossProduct(base_cross, QVector3D.crossProduct(org_rot_slope_upper, rep_rot_slope_upper))
                # # rep_rot_target_slope_up = QVector3D.crossProduct(org_rot_slope_upper, rep_rot_slope_upper)
                # # rep_rot_target_slope_cross = QVector3D.crossProduct(rep_rot_slope_shoulder, rep_rot_target_slope_up).normalized()

                # # 右肩あがってる
                # # rep_rot_target_slope_cross = QVector3D.crossProduct(rep_rot_slope_upper, QVector3D.crossProduct(org_rot_slope, rep_rot_slope)).normalized()
                
                # rep_rot_target_slope_cross = QVector3D.crossProduct(rep_rot_slope, QVector3D.crossProduct(org_rot_slope, rep_rot_slope)).normalized()

                # # rep_rot_target_slope_cross = base_cross
                # # # rep_rot_target_slope_cross = QVector3D.crossProduct(QVector3D.crossProduct(org_rot_slope, rep_rot_slope), rep_rot_slope)
                # # # rep_rot_target_slope_cross = QVector3D.crossProduct(QVector3D.crossProduct(rep_rot_slope, org_rot_slope), rep_rot_slope)
                # # # rep_rot_target_slope_cross = QVector3D.crossProduct(rep_rot_slope, QVector3D.crossProduct(rep_rot_slope, org_rot_slope))
                # # # rep_rot_target_slope_cross = QVector3D.crossProduct(org_rot_slope, base_cross)
                # # # rep_rot_target_slope_cross = QVector3D.crossProduct(rep_rot_slope, QVector3D.crossProduct(org_rot_slope, base_cross))
                # # # rep_rot_slope_cross = QVector3D.crossProduct(rep_rot_slope, rep_rot_target_slope).normalized()

                # # # rep_rot_slope_cross = QVector3D.crossProduct(org_rot_slope, rep_rot_slope).normalized()
                # # # test_tareget = rep_rot_direction_qq
                # # # rot_params = {"x": test_tareget.x(), "y": test_tareget.y(), "z": test_tareget.z(), "scalar": test_tareget.scalar(), \
                # # #                 "-x": -test_tareget.x(), "-y": -test_tareget.y(), "-z": -test_tareget.z(), "scalar-": -test_tareget.scalar(), \
                # # #                 "1": 1, "-1": -1, "0": 0}

                # # # target_rot_slope = QVector3D(rep_rot_direction_qq.y(), -rep_rot_direction_qq.y(), -rep_rot_direction_qq.scalar()).normalized()
                # # # target_rot_slope = QVector3D(rot_params[test_param[0]], rot_params[test_param[1]], rot_params[test_param[2]]).normalized()

                # # # rep_rot_slope_cross = QVector3D.crossProduct(rep_rot_slope, target_rot_slope).normalized()
                # # # rep_rot_slope_cross = QVector3D.crossProduct(rep_rot_slope, QVector3D.crossProduct(org_base_slope, rep_base_slope)).normalized()

                # # # rep_rot_slope_cross = QVector3D.crossProduct(rep_rot_slope, QVector3D.crossProduct(org_rot_slope, rep_rot_slope)).normalized()

                # # # logger.debug("f: %s, %s, org_rot_direction_qq: %s", bf.frame, shoulder_name, org_rot_direction_qq)
                # # # logger.debug("f: %s, %s, rep_rot_direction_qq: %s", bf.frame, shoulder_name, rep_rot_direction_qq)

                # # # # logger.debug("f: %s, %s, target_rot_slope: %s", bf.frame, shoulder_name, target_rot_slope)
                # # # logger.debug("f: %s, %s, rep_rot_slope_cross: %s", bf.frame, shoulder_name, rep_rot_slope_cross)

                # calc_shoulder_rotation(org_motion_frames, motion, trace_model, org_neck_links, org_neck_indexes, org_shoulder_links, org_shoulder_indexes, org_arm_links, org_arm_indexes, \
                #     replace_model, rep_neck_links, rep_neck_indexes, rep_shoulder_links, rep_shoulder_indexes, rep_arm_links, rep_arm_indexes, direction, "首", "肩", "腕", rot_bone_name, \
                #     rep_initial_slope_qq, rep_initial_slope_qq_cross, is_error_outputed, error_file_logger, output_vmd_path, bf, 0.7, test_param)

                calc_rotation_stance(org_motion_frames, motion, trace_model, org_neck_links, org_neck_indexes, org_shoulder_links, org_shoulder_indexes, org_arm_links, org_arm_indexes, \
                    replace_model, rep_neck_links, rep_neck_indexes, rep_shoulder_links, rep_shoulder_indexes, rep_arm_links, rep_arm_indexes, direction, "首", "肩", "腕", rot_bone_name, \
                    rep_initial_slope_qq, is_error_outputed, error_file_logger, output_vmd_path, bf, define_is_rotation_no_check_shoulder, define_calc_up_from_shoulder, \
                    define_calc_up_to_shoulder, 0.7, QVector3D(1, 1, 1), True, test_param)

        print("{0}スタンス補正終了".format(shoulder_name))


# 肩スタンス補正
def calc_shoulder_rotation(org_motion_frames, motion, trace_model, org_base_links, org_base_indexes, org_shoulder_links, org_shoulder_indexes, org_arm_links, org_arm_indexes, \
    replace_model, rep_base_links, rep_base_indexes, rep_shoulder_links, rep_shoulder_indexes, rep_arm_links, rep_arm_indexes, direction, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    rep_initial_slope_qq, is_error_outputed, error_file_logger, output_vmd_path, bf, dot_limit, test_param):

    calc_rotation_stance(org_motion_frames, motion, trace_model, org_base_links, org_base_indexes, org_shoulder_links, org_shoulder_indexes, org_arm_links, org_arm_indexes, \
        replace_model, rep_base_links, rep_base_indexes, rep_shoulder_links, rep_shoulder_indexes, rep_arm_links, rep_arm_indexes, direction, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
        rep_initial_slope_qq, is_error_outputed, error_file_logger, output_vmd_path, bf, define_is_rotation_no_check_shoulder, define_calc_up_from_shoulder, define_calc_up_to_shoulder, dot_limit, QVector3D(1, 1, 1), True, test_param)

# 定義: 回転チェック不要条件（肩）
def define_is_rotation_no_check_shoulder(rep_from_slope):
    return rep_from_slope.z() < -0.4    

# 定義: 傾きを求める方向のFROM位置計算（肩）
def define_calc_up_from_shoulder(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param):

    _, _, _, _, rep_from_global_3ds = utils.create_matrix_global(replace_model, rep_base_links, rep_rot_motion_frames, bf, None)
    rep_up_from_pos = rep_from_global_3ds[len(rep_from_global_3ds) - rep_base_indexes[base_bone_name] - 1]

    return rep_up_from_pos, rep_up_from_pos

    # return calc_up_trunk_by_shoulder(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    #     replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    #     rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, base_bone_name, "上半身")

# 定義: 傾きを求める方向のTO位置計算（肩）
def define_calc_up_to_shoulder(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param):

    _, _, _, _, rep_to_global_3ds = utils.create_matrix_global(replace_model, rep_base_links, rep_rot_motion_frames, bf, None)
    rep_up_to_pos = rep_to_global_3ds[len(rep_to_global_3ds) - rep_base_indexes[rot_bone_name] - 1]

    return rep_up_to_pos, rep_up_to_pos

    # return calc_up_trunk_by_shoulder(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    #     replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    #     rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, rot_bone_name, "上半身")

# 定義: 傾きを求める方向の指定位置計算（体幹）
def calc_up_trunk_by_shoulder(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, trunk_from_name, trunk_to_name):

    return recalc_to_pos(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
        replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
        rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, \
        trunk_from_name, trunk_to_name, org_rot_motion_frames, org_rot_direction_qq, org_base_links, org_base_indexes, rep_rot_motion_frames, rep_rot_direction_qq, rep_base_links, rep_base_indexes)

# TO位置の再計算処理
def recalc_to_pos(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param, \
    recalc_from_name, recalc_to_name, org_recalc_motion_frames, org_recalc_direction_qq, org_to_links, org_to_indexes, rep_recalc_motion_frames, rep_recalc_direction_qq, rep_to_links, rep_to_indexes):

    _, _, _, _, org_to_global_3ds = utils.create_matrix_global(trace_model, org_to_links, org_recalc_motion_frames, bf, None)
    _, _, _, _, rep_to_global_3ds = utils.create_matrix_global(replace_model, rep_to_links, rep_recalc_motion_frames, bf, None)

    # 正面向きの体幹指定ボーンまでの位置
    org_front_to_global_3ds = utils.create_direction_pos_all(org_recalc_direction_qq.inverted(), org_to_global_3ds)
    rep_front_to_global_3ds = utils.create_direction_pos_all(rep_recalc_direction_qq.inverted(), rep_to_global_3ds)

    # 体幹指定ボーンの位置
    org_front_to_pos = org_front_to_global_3ds[len(org_front_to_global_3ds) - org_to_indexes[recalc_to_name] - 1]
    rep_front_to_pos = rep_front_to_global_3ds[len(rep_front_to_global_3ds) - rep_to_indexes[recalc_to_name] - 1]

    # 長さ比率
    org_to_diff = (org_to_links[org_to_indexes[recalc_to_name]].position - org_to_links[org_to_indexes[recalc_from_name]].position)
    rep_to_diff = (rep_to_links[rep_to_indexes[recalc_to_name]].position - rep_to_links[rep_to_indexes[recalc_from_name]].position)
    to_diff_length = rep_to_diff.length() / org_to_diff.length()
    to_diff = rep_to_diff / org_to_diff
    utils.set_effective_value_vec3(to_diff)

    # ---------------
    
    rep_front_to_x = rep_front_to_pos.x() + (rep_to_diff.x() * diff_fill_ratio.x()) \
        + ( org_front_to_pos.x() - org_front_to_pos.x() - (org_to_diff.x() * diff_fill_ratio.x()) ) * arm_diff_length

    rep_front_to_y = rep_front_to_pos.y() + (rep_to_diff.y() * diff_fill_ratio.y()) \
        + ( org_front_to_pos.y() - org_front_to_pos.y() - (org_to_diff.y() * diff_fill_ratio.y()) ) * to_diff_length

    rep_front_to_z = rep_front_to_pos.z() + (rep_to_diff.z() * diff_fill_ratio.z())  \
        + ( org_front_to_pos.z() - org_front_to_pos.z() - (org_to_diff.z() * diff_fill_ratio.z()) ) * arm_diff_length

    new_rep_front_to_pos = QVector3D(rep_front_to_x, rep_front_to_y, rep_front_to_z)
    logger.debug("f: %s, new_rep_front_to_pos: %s", bf.frame, new_rep_front_to_pos)
    logger.debug("f: %s, rep_to_pos: %s", bf.frame, rep_front_to_pos)

    # 回転を元に戻した位置
    new_rep_front_to_global_3ds = copy.deepcopy(rep_front_to_global_3ds)
    new_rep_front_to_global_3ds[len(new_rep_front_to_global_3ds) - rep_to_indexes[recalc_to_name] - 1] = new_rep_front_to_pos

    rotated_to_3ds = utils.create_direction_pos_all(rep_recalc_direction_qq, new_rep_front_to_global_3ds)
    rep_to_pos = rotated_to_3ds[len(rotated_to_3ds) - rep_to_indexes[recalc_to_name] - 1]

    return rep_to_pos, rep_to_global_3ds[len(rep_to_global_3ds) - rep_to_indexes[recalc_to_name] - 1]


# def define_from_orientation_shoulder(rep_from_pos, rep_to_pos, rep_base_pos, rep_initial_slope_qq, rep_left_arm_pos, rep_right_arm_pos, direction_name, rep_base_rot_pos, rep_to_rot_pos, test_param=None):
#     direction = rep_to_pos - rep_from_pos
#     up = QVector3D.crossProduct(direction, rep_to_pos - rep_from_pos).normalized()
#     return QQuaternion.fromDirection(direction, up) * QQuaternion.fromDirection(rep_from_slope, rep_from_slope_cross)

    # direction = rep_to_pos - rep_from_pos

    # if direction_name == "左":
    #     rep_arm_slope = rep_left_arm_pos - rep_right_arm_pos
    #     rep_target_initial_slope = rep_to_rot_pos - rep_base_rot_pos
    # else:
    #     rep_arm_slope = rep_right_arm_pos - rep_left_arm_pos
    #     rep_target_initial_slope = rep_to_rot_pos - rep_base_rot_pos

    # test_tareget = rep_target_initial_slope
    # rot_params = {"x": test_tareget.x(), "y": test_tareget.y(), "z": test_tareget.z(), \
    #                 "x-": -test_tareget.x(), "y-": -test_tareget.y(), "z-": -test_tareget.z(), \
    #                 "1": 1, "1-": -1, "0": 0}
    # base_cross = QVector3D(rot_params[test_param[0]], rot_params[test_param[1]], rot_params[test_param[2]]).normalized()
    # rep_target_slope_cross = QVector3D.crossProduct(rep_target_initial_slope, base_cross).normalized()

    # # logger.info("rep_target_slope_cross: %s", rep_target_slope_cross)
    # # QVector3D.crossProduct(rep_target_slope, rep_target_slope_cross).normalized()

    # return QVector3D.crossProduct(rep_target_initial_slope, rep_target_slope_cross).normalized()

def calc_rotation_stance(org_motion_frames, motion, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
    replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
    rep_initial_slope_qq, is_error_outputed, error_file_logger, output_vmd_path, bf, define_is_rotation_no_check, define_calc_up_from, define_calc_up_to, dot_limit, diff_fill_ratio, is_x_diff_shoulder, test_param=None):
    target_from_bone_name = "{0}{1}".format(direction_name, from_bone_name)
    target_to_bone_name = "{0}{1}".format(direction_name, to_bone_name)
    is_print = False

    utils.output_message("f: %s, target_from_bone_name: %s -------------" % (bf.frame, target_from_bone_name), is_print)

    dot_limit = 0
    start_bf = utils.calc_bone_by_complement({}, "ルート", 0)

    # 処理対象までのモーション情報(処理対象以上のモーション情報を含まない)
    org_base_motion_frames = {}
    for l in org_base_links[org_base_indexes[base_bone_name]:]:
        bone = utils.calc_bone_by_complement(org_motion_frames, l.name, bf.frame)
        org_base_motion_frames[bone.format_name] = [bone]

    org_from_motion_frames = {}
    for l in org_target_links[org_target_indexes[from_bone_name]:]:
        bone = utils.calc_bone_by_complement(org_motion_frames, l.name, bf.frame)
        org_from_motion_frames[bone.format_name] = [bone]

    org_rot_motion_frames = {}
    for l in org_target_links[org_target_indexes[rot_bone_name]:]:
        bone = utils.calc_bone_by_complement(org_motion_frames, l.name, bf.frame)
        org_rot_motion_frames[bone.format_name] = [bone]

    rep_base_motion_frames = {}
    for l in rep_base_links[rep_base_indexes[base_bone_name]:]:
        bone = utils.calc_bone_by_complement(motion.frames, l.name, bf.frame)
        rep_base_motion_frames[bone.format_name] = [bone]

    rep_from_motion_frames = {}
    for l in rep_target_links[rep_target_indexes[from_bone_name]:]:
        bone = utils.calc_bone_by_complement(motion.frames, l.name, bf.frame)
        rep_from_motion_frames[bone.format_name] = [bone]

    rep_rot_motion_frames = {}
    for l in rep_target_links[rep_target_indexes[rot_bone_name]:]:
        bone = utils.calc_bone_by_complement(motion.frames, l.name, bf.frame)
        rep_rot_motion_frames[bone.format_name] = [bone]

    # FROMより親の回転量
    parent_rotation = utils.calc_upper_direction_qq(replace_model, rep_base_links[rep_base_indexes[base_bone_name]+1:], motion.frames, bf)

    # 元モデルの向いている回転量
    org_rot_direction_qq = utils.calc_upper_direction_qq(trace_model, org_base_links, org_rot_motion_frames, bf)
    # 先モデルの向いている回転量
    rep_rot_direction_qq = utils.calc_upper_direction_qq(replace_model, rep_base_links, rep_rot_motion_frames, bf)

    # -------------

    # 基準ボーンまでの位置
    _, _, _, _, org_base_global_3ds = utils.create_matrix_global(trace_model, org_base_links[org_base_indexes[rot_bone_name]:], org_base_motion_frames, bf, None)
    _, _, _, _, rep_base_global_3ds = utils.create_matrix_global(replace_model, rep_base_links[rep_base_indexes[rot_bone_name]:], rep_base_motion_frames, bf, None)

    # 基準位置
    org_base_pos = org_base_global_3ds[len(org_base_global_3ds) - org_base_indexes[base_bone_name] - 1]
    rep_base_pos = rep_base_global_3ds[len(rep_base_global_3ds) - rep_base_indexes[base_bone_name] - 1]

    # 正面向きの基準ボーンまでの位置
    org_front_base_global_3ds = utils.create_direction_pos_all(org_rot_direction_qq.inverted(), org_base_global_3ds)
    rep_front_base_global_3ds = utils.create_direction_pos_all(rep_rot_direction_qq.inverted(), rep_base_global_3ds)

    # 基準位置
    org_front_base_pos = org_front_base_global_3ds[len(org_front_base_global_3ds) - org_base_indexes[base_bone_name] - 1]
    rep_front_base_pos = rep_front_base_global_3ds[len(rep_front_base_global_3ds) - rep_base_indexes[base_bone_name] - 1]

    # -------------

    # TOボーンまでの位置
    _, _, _, _, org_to_global_3ds = utils.create_matrix_global(trace_model, org_target_links[org_target_indexes[to_bone_name]:], org_from_motion_frames, bf, None)
    _, _, _, _, rep_to_global_3ds = utils.create_matrix_global(replace_model, rep_target_links[rep_target_indexes[to_bone_name]:], rep_from_motion_frames, bf, None)

    # 正面向きのTOボーンまでの位置
    org_front_to_global_3ds = utils.create_direction_pos_all(org_rot_direction_qq.inverted(), org_to_global_3ds)
    rep_front_to_global_3ds = utils.create_direction_pos_all(rep_rot_direction_qq.inverted(), rep_to_global_3ds)

    # TOボーン正面位置
    org_front_to_pos = org_front_to_global_3ds[len(org_front_to_global_3ds) - org_target_indexes[to_bone_name] - 1]
    rep_front_to_pos = rep_front_to_global_3ds[len(rep_front_to_global_3ds) - rep_target_indexes[to_bone_name] - 1]

    # -------------
    
    # 肩幅比率
    org_arm_diff = (org_arm_links["左"][org_arm_indexes["左"]["腕"]].position - org_arm_links["右"][org_arm_indexes["右"]["腕"]].position)
    rep_arm_diff = (rep_arm_links["左"][rep_arm_indexes["左"]["腕"]].position - rep_arm_links["右"][rep_arm_indexes["右"]["腕"]].position)
    arm_diff_length = rep_arm_diff.length() / org_arm_diff.length()

    # 結果用
    new_rep_front_to_global_3ds = copy.deepcopy(rep_front_to_global_3ds)

    # ------------------
    # TOボーンの位置再設定

    # 長さ比率
    org_to_diff = (org_target_links[org_target_indexes[to_bone_name]].position - org_base_links[org_base_indexes[base_bone_name]].position)
    rep_to_diff = (rep_target_links[rep_target_indexes[to_bone_name]].position - rep_base_links[rep_base_indexes[base_bone_name]].position)
    to_diff_length = rep_to_diff.length() / org_to_diff.length()
    to_diff = rep_to_diff / org_to_diff
    utils.set_effective_value_vec3(to_diff)

    rep_front_to_x = rep_front_base_pos.x() + (rep_to_diff.x() * diff_fill_ratio.x()) \
        + ( org_front_to_pos.x() - org_front_base_pos.x() - (org_to_diff.x() * diff_fill_ratio.x()) ) * (arm_diff_length if is_x_diff_shoulder else to_diff.x())

    rep_front_to_y = rep_front_base_pos.y() + (rep_to_diff.y() * diff_fill_ratio.y()) \
        + ( org_front_to_pos.y() - org_front_base_pos.y() - (org_to_diff.y() * diff_fill_ratio.y()) ) * to_diff_length

    rep_front_to_z = rep_front_base_pos.z() + (rep_to_diff.z() * diff_fill_ratio.z()) \
        + ( org_front_to_pos.z() - org_front_base_pos.z() - (org_to_diff.z() * diff_fill_ratio.z()) ) * (arm_diff_length if is_x_diff_shoulder else to_diff.z())

    new_rep_front_to_pos = QVector3D(rep_front_to_x, rep_front_to_y, rep_front_to_z)
    logger.debug("f: %s, new_rep_front_to_pos: %s", bf.frame, new_rep_front_to_pos)
    logger.debug("f: %s, rep_to_pos: %s", bf.frame, rep_front_to_pos)

    new_rep_front_to_global_3ds = copy.deepcopy(rep_front_to_global_3ds)
    new_rep_front_to_global_3ds[len(new_rep_front_to_global_3ds) - rep_target_indexes[to_bone_name] - 1] = new_rep_front_to_pos

    # 回転を元に戻した位置
    rotated_to_3ds = utils.create_direction_pos_all(rep_rot_direction_qq, new_rep_front_to_global_3ds)
    rep_to_pos = rotated_to_3ds[len(rotated_to_3ds) - rep_target_indexes[to_bone_name] - 1]

    # ---------------

    # UP方向のFROM位置
    rep_up_from_pos, rep_up_from_initial_pos = define_calc_up_from(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
        replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
        rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param)

    # UP方向のTO位置
    rep_up_to_pos, rep_up_to_initial_pos = define_calc_up_to(org_rot_motion_frames, rep_rot_motion_frames, trace_model, org_base_links, org_base_indexes, org_target_links, org_target_indexes, org_arm_links, org_arm_indexes, \
        replace_model, rep_base_links, rep_base_indexes, rep_target_links, rep_target_indexes, rep_arm_links, rep_arm_indexes, direction_name, base_bone_name, from_bone_name, to_bone_name, rot_bone_name, \
        rep_initial_slope_qq, bf, diff_fill_ratio, is_x_diff_shoulder, org_rot_direction_qq, rep_rot_direction_qq, rep_front_base_pos, org_front_base_pos, arm_diff_length, test_param)

    # ---------------
    # FROMの回転量を再計算する
    direction = rep_to_pos - rep_base_pos
    up = QVector3D.crossProduct(direction, rep_up_to_pos - rep_up_from_pos).normalized()
    from_orientation = QQuaternion.fromDirection(direction, up)
    initial = rep_initial_slope_qq
    from_rotation = parent_rotation.inverted() * from_orientation * initial.inverted()
    logger.debug("f: %s, parent: %s", bf.frame, parent_rotation.toEulerAngles())
    logger.debug("f: %s, initial: %s", bf.frame, initial.toEulerAngles())
    logger.debug("f: %s, orientation: %s", bf.frame, from_orientation.toEulerAngles())
    logger.debug("f: %s, bf: %s", bf.frame, from_rotation.toEulerAngles())

    utils.output_message("rep_base_pos(%s): %s" % (base_bone_name, rep_base_pos), is_print)
    utils.output_message("rep_to_pos(%s): %s: 元: %s" % (target_to_bone_name, rep_to_pos, rep_to_global_3ds[len(rep_front_to_global_3ds) - rep_target_indexes[to_bone_name] - 1]), is_print)
    utils.output_message("rep_up_from_pos: %s 元: %s" % (rep_up_from_pos, rep_up_from_initial_pos), is_print)
    utils.output_message("rep_up_to_pos: %s 元: %s" % (rep_up_to_pos, rep_up_to_initial_pos), is_print)

    if define_is_rotation_no_check and define_is_rotation_no_check(rep_initial_slope_qq):
        # チェックなし条件に合致する場合、チェックなしで適用
        bf.rotation = from_rotation
    else:
        org_bfs = [x for x in org_motion_frames[target_from_bone_name] if x.frame == bf.frame]
        if len(org_bfs) > 0:
            # 元にもあるキーである場合、内積チェック
            uad = abs(QQuaternion.dotProduct(from_rotation, org_bfs[0].rotation))
            if uad < dot_limit:
                print("%sフレーム目%sスタンス補正失敗: 角度:%s, uad: %s" % (bf.frame, target_from_bone_name, from_rotation.toEulerAngles(), uad))

                # 失敗時のみエラーログ出力
                if not is_error_outputed:
                    is_error_outputed = True
                    if not error_file_logger:
                        error_file_logger = utils.create_error_file_logger(motion, trace_model, replace_model, output_vmd_path)

                error_file_logger.warning("%sフレーム目%sスタンス補正失敗: 角度:%s, uad: %s" , bf.frame, target_from_bone_name, from_rotation.toEulerAngles(), uad)
            else:
                # 内積の差が小さい場合、回転適用
                bf.rotation = from_rotation
    # bf.rotation = from_rotation


def adjust_rotation_by_parent(org_motion_frames, motion, trace_model, replace_model, target_bone_name, target_parent_name, test_param):
    if target_bone_name in motion.frames:
        for bf in motion.frames[target_bone_name]:
            if bf.key == True:

                # 元々の親の回転量
                org_parent_rot = utils.calc_bone_by_complement(org_motion_frames, target_parent_name, bf.frame, False).rotation
                # 修正後の親の回転量
                rep_parent_rot = utils.calc_bone_by_complement(motion.frames, target_parent_name, bf.frame, False).rotation

                logger.debug("---------")
                logger.debug("f: %s, %s, %s, org_parent_rot: %s", bf.frame, target_bone_name, target_parent_name, org_parent_rot.toEulerAngles())
                logger.debug("f: %s, %s, %s, rep_parent_rot: %s", bf.frame, target_bone_name, target_parent_name, rep_parent_rot.toEulerAngles())
                logger.debug("---------")

                # bf.rotation = rot_params[test_param[0]] * rot_params[test_param[1]] * rot_params[test_param[2]] * rot_params[test_param[3]] * rot_params[test_param[4]]

                bf.rotation = rep_parent_rot.inverted() * org_parent_rot * bf.rotation

def prepare_split_stance(motion, bone_name):
    for bf_idx in range(len(motion.frames[bone_name])):
        if bf_idx == 0:
            continue

        prev_bf = motion.frames[bone_name][bf_idx - 1]
        bf = motion.frames[bone_name][bf_idx]

        rot_diff_euler = (prev_bf.rotation * bf.rotation.inverted()).toEulerAngles()
        if abs(rot_diff_euler.x()) > 170 or abs(rot_diff_euler.y()) > 170 or abs(rot_diff_euler.z()) > 170:
            # 回転量が半分近い場合、半分に分割しておく
            split_stance(motion, bone_name, prev_bf, bf, bf_idx)         

# 補間曲線分割処理
def split_stance(motion, bone_name, prev_bf, bf, bf_idx):
    frame_no = prev_bf.frame + round((bf.frame - prev_bf.frame) / 2)

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


def adjust_arm_stance(motion, trace_model, replace_model, org_motion_frames, test_param):
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

            # if dlist["肩"] in motion.frames:
            #     # 腕
            #     for bf in motion.frames[dlist["肩"]]:
            #         if bf.key == True:

            if dlist["腕"] in motion.frames:
                # 腕
                for bf in motion.frames[dlist["腕"]]:
                    if bf.key == True:
                        # adjust_rotation_by_parent(org_motion_frames, motion, trace_model, replace_model, dlist["腕"], dlist["肩"], test_param)

                        # # 元々の上半身回転量
                        # org_upper_bone = utils.calc_bone_by_complement(org_motion_frames, "上半身", bf.frame)
                        # # 修正後の上半身回転量
                        # rep_upper_bone = utils.calc_bone_by_complement(motion.frames, "上半身", bf.frame)

                        # # 元々の上半身2回転量
                        # org_upper2_bone = utils.calc_bone_by_complement(org_motion_frames, "上半身2", bf.frame)
                        # # 修正後の上半身2回転量
                        # rep_upper2_bone = utils.calc_bone_by_complement(motion.frames, "上半身2", bf.frame)

                        # # 元々の肩回転量
                        # org_shoulder_bone = utils.calc_bone_by_complement(org_motion_frames, dlist["肩"], bf.frame)
                        # # 修正後の肩回転量
                        # rep_shoulder_bone = utils.calc_bone_by_complement(motion.frames, dlist["肩"], bf.frame)

                        # rot_params = {"ou": org_upper_bone.rotation, "ru": rep_upper_bone.rotation.inverted(), \
                        #                 "o2": org_upper2_bone.rotation, "r2": rep_upper2_bone.rotation.inverted(), \
                        #                 "os": org_shoulder_bone.rotation, "rs": rep_shoulder_bone.rotation.inverted(), \
                        #                 "b": bf.rotation * arm_stance_qqs[dlist["腕"]]}

                        # bf.rotation = rot_params[test_param[0]] * rot_params[test_param[1]] * rot_params[test_param[2]] * rot_params[test_param[3]] * rot_params[test_param[4]] * rot_params[test_param[5]] * rot_params[test_param[6]]

                        bf.rotation = bf.rotation * arm_stance_qqs[dlist["腕"]]

            print("腕スタンス補正終了")

            if dlist["ひじ"] in motion.frames:
                # ひじ
                for bf in motion.frames[dlist["ひじ"]]:
                    if bf.key == True:
                        bf.rotation = arm_stance_qqs[dlist["腕"]].inverted() * bf.rotation * arm_stance_qqs[dlist["ひじ"]]

            print("ひじスタンス補正終了")

            if dlist["手首"] in motion.frames:
                # 手首
                for bf in motion.frames[dlist["手首"]]:
                    if bf.key == True:
                        # arm_stance_qqs[dlist["腕"]].inverted() * 
                        bf.rotation = arm_stance_qqs[dlist["ひじ"]].inverted() * bf.rotation * arm_stance_qqs[dlist["手首"]]

            print("手首スタンス補正終了")

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
