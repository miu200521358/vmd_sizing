# -*- coding: utf-8 -*-
# 接触回避処理
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

DOT_LIMIT = 0.85

def exec(motion, trace_model, replace_model, output_vmd_path, is_avoidance, is_avoidance_finger, is_hand_ik, target_avoidance_rigids, target_avoidance_bones, org_motion_frames, error_file_logger):
    is_error_outputed = False

    # -----------------------------------------------------------------
    # 剛体接触回避処理
    if motion.motion_cnt > 0 and is_avoidance and not is_hand_ik:

        if not trace_model.can_arm_sizing or not replace_model.can_arm_sizing:
            # 腕構造チェックがFALSEの場合、接触回避補正なし
            return False
                
        print("■■ 剛体接触回避処理 -----------------")

        # 指定ボーンまでのリンク生成
        bone_ik_links = {}
        bone_all_links = {}
        bone_all_indexes = {}
        target_bones = []

        for bone_name in target_avoidance_bones:
            if bone_name in replace_model.bones:
                # 指定ボーンまでのリンク
                links, indexes = replace_model.create_link_2_top_one(bone_name)
                bone_all_links[bone_name] = links
                bone_all_indexes[bone_name] = indexes
                # IK用リンク
                ik_links, ik_names = create_ik_links(replace_model, links, bone_name)
                bone_ik_links[bone_name] = ik_links
                target_bones.extend(ik_names)

        # 剛体用の場所
        rigid_links = {}
        rigid_indexes = {}
        for target_rigid in target_avoidance_rigids:
            # 剛体の追従元ボーンの情報
            links, indexes = replace_model.create_link_2_top_one(replace_model.bones[replace_model.bone_indexes[replace_model.rigidbodies[target_rigid].bone_index]].name)
            rigid_links[target_rigid] = links
            rigid_indexes[target_rigid] = indexes

        # 事前準備
        for bone_name, links in bone_ik_links.items():
            if "左" in bone_name:
                arm_links = {"左": links, "右": []}
            elif "右" in bone_name:
                arm_links = {"左": [], "右": links}

            sub_arm_ik.prepare(motion, arm_links, 0, False, target_bones)

        # 剛体接触回避処理実行
        is_error_outputed = exec_avoidance(motion, trace_model, replace_model, output_vmd_path, org_motion_frames, bone_ik_links, bone_all_links, bone_all_indexes, target_avoidance_bones, target_avoidance_rigids, rigid_links, rigid_indexes, error_file_logger)

        for bone_name, links in bone_ik_links.items():
            if "左" in bone_name:
                arm_links = {"左": links, "右": []}
            elif "右" in bone_name:
                arm_links = {"左": [], "右": links}
                
            # # キー有効可否設定
            # sub_arm_ik.reset_activate(motion, arm_links, False)

            # 補間曲線再設定
            sub_arm_ik.reset_complement(motion, arm_links, False)

            # 必要なキーだけ残す
            sub_arm_ik.leave_valid_key_frames(motion, arm_links, False)

    return not is_error_outputed


# 腕ジョイントリスト生成
def create_ik_links(model, links, end_bone_name):
    
    # 関節リストを末端から生成する
    ik_links = []
    ik_names = []

    ik_links.append(links[0])
    ik_names.append(links[0].name)

    for l in links[1:]:
        if "肩" in l.name:
            break
            
        if l.fixed_axis == QVector3D() and l.getManipulatable() == True and "指" not in l.name:
            # 登録対象で捩りではない場合、登録
            ik_links.append(l)
            ik_names.append(l.name)

    return ik_links, ik_names


# 接触回避実行
def exec_avoidance(motion, trace_model, replace_model, output_vmd_path, org_motion_frames, bone_ik_links, bone_all_links, bone_all_indexes, target_avoidance_bones, target_avoidance_rigids, rigid_links, rigid_indexes, error_file_logger):
    # 腕IKによる位置調整を行う場合

    # エラーを一度でも出力しているか(腕IK)
    is_error_outputed = False

    # キーフレーム分割済みのフレーム情報を別保持
    org_fill_motion_frames = copy.deepcopy(motion.frames)

    # 直前のキー
    prev_bf = None
    # 空白を挟んだ直前のキー
    prev_space_bf = None
    for target_bone in target_avoidance_bones:
        target_bone_ik_links = bone_ik_links[target_bone]
        target_bone_all_links = bone_all_links[target_bone]
        target_bone_all_indexes = bone_all_indexes[target_bone]

        for f in range(motion.last_motion_frame + 1):
            is_ik_adjust = False

            now_bfs = [(e, x) for e, x in enumerate(motion.frames[target_bone]) if x.frame == f]
            if target_bone in motion.frames and len(now_bfs) > 0:
                bf_idx = now_bfs[0][0]
                bf = now_bfs[0][1]

                if bf.key == True and bf.frame == f:
                    if prev_bf and bf.frame - prev_bf.frame >= 2:
                        # 直前キーがあり、かつ現在キーと2フレーム以上離れている場合、保持
                        prev_space_bf = prev_bf
                    
                    direction = "左" if "左" in target_bone else "右"
                    
                    # 変換先モデルのIK計算前指までの情報
                    _, _, _, _, rep_bone_global_3ds = utils.create_matrix_global(replace_model, target_bone_all_links, motion.frames, bf, None)
                    # 先端ボーンの位置
                    rep_bone_pos = rep_bone_global_3ds[-1]
                    
                    # 剛体の表面位置情報
                    for target_rigid_name in target_avoidance_rigids:
                        target_rigid = replace_model.rigidbodies[target_rigid_name]

                        # 剛体の追従しているボーンまでの情報
                        rep_rigid_bone_trans_vs, rep_rigid_bone_add_qs, _, _, rep_rigid_bone_global_3ds = utils.create_matrix_global(replace_model, rigid_links[target_rigid_name], motion.frames, bf, None)

                        # OBB生成
                        target_rigid_obb = target_rigid.get_obb(rigid_links[target_rigid_name][0].position, rep_rigid_bone_trans_vs, rep_rigid_bone_add_qs)
                        # 接触回避対象ボーンとの距離
                        collision, return_pos = target_rigid_obb.judge_collision(rep_bone_pos)

                        if collision == True:
                            print("○剛体接触あり: f: {0}, {1} -> {2}, 差分: x: {3:02.3f}, y: {4:02.3f}, z: {5:02.3f}".format(bf.frame, target_bone, target_rigid_name, return_pos.x(), return_pos.y(), return_pos.z() ))
                            # 剛体にめり込んでいる場合、それを避ける
                    
                            # 手首の位置を差分分移動させる
                            new_rep_bone_pos = rep_bone_pos + return_pos

                            # ---------
                            wrist_ik_bone = "{0}偽IK".format(direction)
                            if not wrist_ik_bone in motion.frames:
                                motion.frames[wrist_ik_bone] = []
                            
                            wikbf = VmdBoneFrame(bf.frame)
                            wikbf.name = wrist_ik_bone.encode('shift-jis')
                            wikbf.format_name = wrist_ik_bone
                            wikbf.frame = bf.frame
                            wikbf.key = True
                            wikbf.position = new_rep_bone_pos
                            motion.frames[wrist_ik_bone].append(wikbf)
                            # ---------

                            # ---------
                            wrist_ik_bone = "{0}偽IK2".format(direction)
                            if not wrist_ik_bone in motion.frames:
                                motion.frames[wrist_ik_bone] = []
                            
                            wikbf = VmdBoneFrame(bf.frame)
                            wikbf.name = wrist_ik_bone.encode('shift-jis')
                            wikbf.format_name = wrist_ik_bone
                            wikbf.frame = bf.frame
                            wikbf.key = True
                            wikbf.position = rep_bone_pos
                            motion.frames[wrist_ik_bone].append(wikbf)
                            # ---------

                            # ボーン位置から角度を求める
                            sub_arm_ik.calc_arm_IK2FK(new_rep_bone_pos, replace_model, target_bone_ik_links, target_bone_all_links, direction, motion.frames, bf, prev_space_bf)

                            # 接触回避結果判定 ------------

                            # 最も上のボーンの内積チェック                                
                            dot = abs(QQuaternion.dotProduct(motion.frames[target_bone_ik_links[-1].name][bf_idx].rotation, org_fill_motion_frames[target_bone_ik_links[-1].name][bf_idx].rotation))
                            if dot < DOT_LIMIT:
                                print("接触回避失敗: f: {0}, {1} -> {2}, 差分: x: {3:02.3f}, y: {4:02.3f}, z: {5:02.3f}, dot: {6:02.3f}".format(bf.frame, target_bone, target_rigid_name, return_pos.x(), return_pos.y(), return_pos.z(), dot ))
                                # 失敗時のみエラーログ出力
                                if not is_error_outputed:
                                    is_error_outputed = True
                                    if not error_file_logger:
                                        error_file_logger = utils.create_error_file_logger(motion, trace_model, replace_model, output_vmd_path)

                                    error_file_logger.info("ボーン: %s", target_bone_all_links[0])
                                    error_file_logger.info("位置: %s", target_bone_all_links[0])
                                    error_file_logger.info("剛体: %s", target_rigid)
                                    error_file_logger.info("rep_bone_pos: %s", rep_bone_pos)
                                    error_file_logger.info("return_pos: %s", return_pos)
                                    error_file_logger.info("new_rep_bone_pos: %s", new_rep_bone_pos)

                                error_file_logger.warning("接触回避失敗: f: %s, %s -> %s, 差分: x: %s, y: %s, z: %s, dot: %s", bf.frame, target_bone, target_rigid_name, return_pos.x(), return_pos.y(), return_pos.z(), dot )
                            else:
                                # logger.debug("接触回避成功: f: %s, 左腕:%s, 右腕:%s", bf.frame, lad, rad)
                                pass

                            for al in target_bone_ik_links:
                                now_al_bf = [(e, x) for e, x in enumerate(motion.frames[al.name]) if x.frame == f][0]

                                if dot >= DOT_LIMIT:
                                    # 角度調整が既定内である場合
                                    motion.frames[al.name][now_al_bf[0]].key = True
                                else:
                                    # 角度調整が既定外である場合、クリア
                                    past_al_bf = [(e, x) for e, x in enumerate(org_fill_motion_frames[al.name]) if x.frame == f][0]
                                    motion.frames[al.name][now_al_bf[0]] = copy.deepcopy(past_al_bf[1])
                        else:
                            if 0 < return_pos.length() <= 1:
                                print("－剛体接触なし: f: {0}, {1} -> {2}, 差分: x: {3:02.3f}, y: {4:02.3f}, z: {5:02.3f}".format(bf.frame, target_bone, target_rigid_name, return_pos.x(), return_pos.y(), return_pos.z() ))

                        # 前回登録キーとして保持
                        prev_bf = copy.deepcopy(bf)
                            
    return is_error_outputed



