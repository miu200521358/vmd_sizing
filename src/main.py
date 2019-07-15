# -*- coding: utf-8 -*-
#
import argparse
import os.path
import logging
import copy
import traceback
import re
from math import acos, degrees
from datetime import datetime
from pathlib import Path
from PyQt5.QtGui import QQuaternion, QVector3D, QVector2D, QMatrix4x4, QVector4D

from VmdWriter import VmdWriter, VmdBoneFrame
from VmdReader import VmdReader
from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
error_file_logger = logging.getLogger("error")

level = {0:logging.ERROR,
            1:logging.WARNING,
            2:logging.INFO,
            3:logging.DEBUG}

def main(motion, trace_model, replace_model, output_vmd_path, is_avoidance, is_avoidance_finger, is_hand_ik, hand_distance, vmd_choice_values, rep_choice_values, rep_rate_values, error_file_logger=None):   
    # エラーログ出力用
    error_path = re.sub(r'\.vmd$', ".log", output_vmd_path.lower())
    logger.debug("error_path: %s", error_path)
    # エラーを一度でも出力しているか(腕IK)
    is_hand_ik_error_outputed = False

    print("モーション: %s" % motion.path)
    print("作成元: %s" % trace_model.path)
    print("変換先: %s" % replace_model.path)

    # 移植先のセンターとグルーブは、作成元の比率に合わせる
    adjust_center(trace_model, replace_model, "センター")
    adjust_center(trace_model, replace_model, "グルーブ")

    # 足IKのXYZの比率
    xz_ratio, y_ratio, leg_ik_stance = calc_leg_ik_ratio(trace_model, replace_model)

    # センターのZ軸オフセットを計算
    cal_center_z_offset(trace_model, replace_model, "センター")
    
    # 全ての親をコピー
    copy_root_parent(trace_model)
    copy_root_parent(replace_model)

    # サイズ比較
    # lengths = compare_length(trace_model, replace_model)

    if motion.motion_cnt > 0:

        # 変換前のオリジナルモーションを保持
        org_motion_frames = copy.deepcopy(motion.frames)

        # 足までのリンク(作成元モデル)
        # all_org_leg_links, all_org_leg_indexes = trace_model.create_link_2_top_lr("足", "足")

        # # 足までのリンク(変換先モデル)
        # all_rep_leg_links, all_rep_leg_indexes = replace_model.create_link_2_top_lr("足", "足")

        # # 足IKまでのリンク(作成元モデル)
        # all_org_leg_ik_links, all_org_leg_ik_indexes = trace_model.create_link_2_top_lr("足ＩＫ", "足ＩＫ")

        # # 足IKまでのリンク(変換先モデル)
        # all_rep_leg_ik_links, all_rep_leg_ik_indexes = replace_model.create_link_2_top_lr("足ＩＫ", "足ＩＫ")

        # -----------------------------------------------------------------
        # 移動ボーン縮尺
        for k in ["右足ＩＫ親" ,"左足ＩＫ親", "右足ＩＫ" ,"左足ＩＫ", "右つま先ＩＫ" ,"左つま先ＩＫ", "センター", "グルーブ", "全ての親"]:
            if k in motion.frames and k in replace_model.bones:
                for bf in motion.frames[k]:
                    # IK比率をそのまま掛ける
                    bf.position.setX( bf.position.x() * xz_ratio )
                    bf.position.setY( bf.position.y() * y_ratio )
                    bf.position.setZ( bf.position.z() * xz_ratio )

                    if replace_model.bones[k].offset_z != 0:
                        # Zオフセットが入っている場合、オフセット調整
                        bf.position.setZ(bf.position.z() + replace_model.bones[k].offset_z) 

                print("調整終了: %s" % k)

        # -----------------------------------------------------------------
        # 腕の角度補正
                    
        # センターから手首までの位置(作成元モデル)
        all_org_wrist_links, _ = trace_model.create_link_2_top_lr("手首")

        # センターから手首までの位置(トレース先モデル)
        all_rep_wrist_links, _ = replace_model.create_link_2_top_lr("手首")
        logger.debug("all_rep_wrist_links: %s", [ "{0}: {1}\n".format(x.name, x.position) for x in all_rep_wrist_links["左"]])    

        all_d_list = [{"肩":"左肩", "腕":"左腕", "ひじ":"左ひじ", "手首":"左手首"}, {"肩":"右肩", "腕":"右腕", "ひじ":"右ひじ", "手首":"右手首"}]
        if set(all_d_list[0].values()).issubset(trace_model.bones) and set(all_d_list[0].values()).issubset(replace_model.bones) and \
            set(all_d_list[1].values()).issubset(trace_model.bones) and set(all_d_list[1].values()).issubset(replace_model.bones):

            # 腕の各パーツの補正角度（キー：ボーン名、値：補正クォータニオン）
            left_arm_stance_qqs = calc_arm_stance(trace_model, all_org_wrist_links, replace_model, all_rep_wrist_links, "左")
            right_arm_stance_qqs = calc_arm_stance(trace_model, all_org_wrist_links, replace_model, all_rep_wrist_links, "右")

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

                if dlist["腕"] in motion.frames:
                    # 腕
                    for bf in motion.frames[dlist["腕"]]:
                        if bf.key == True:
                            bf.rotation = bf.rotation * arm_stance_qqs["腕"]

                if dlist["ひじ"] in motion.frames:
                    # ひじ
                    for bf in motion.frames[dlist["ひじ"]]:
                        if bf.key == True:
                            bf.rotation = arm_stance_qqs["腕"].inverted() * bf.rotation * arm_stance_qqs["ひじ"]

                if dlist["手首"] in motion.frames:
                    # 手首
                    for bf in motion.frames[dlist["手首"]]:
                        if bf.key == True:
                            bf.rotation = bf.rotation * arm_stance_qqs["手首"]

        # -----------------------------------------------------------------
        # 頭部と腕の接触回避処理        
        if is_avoidance:
            # 頭までのリンク生成
            head_links, _ = replace_model.create_link_2_top( "頭")

            # 人差し指までのリンク生成
            if "左人指先" in replace_model.bones and is_avoidance_finger:
                all_rep_finger_links, _ = replace_model.create_link_2_top_lr("人指先")
            else:
                # 指のないモデルは手首で代用。もしくは手首を明示的に選択した場合
                all_rep_finger_links, _ = replace_model.create_link_2_top_lr("手首")

            # for l in left_wrist_links:
            #     logger.debug("left_wrist_links: %s", l)
            
            # 上半身～頭部の頂点の抽出
            upper_vertices = replace_model.get_upper_vertices(head_links)

            for f in range(motion.last_motion_frame + 1):
                for k in ["左腕", "左ひじ", "右腕", "右ひじ"]:
                    if k in motion.frames:
                        for bf in motion.frames[k]:
                            if bf.key == True and bf.frame == f:

                                # 方向
                                direction = "左" if "左" in k else "右"

                                # 現時点の上半身の位置
                                upper_vertex_pos = calc_upper_vertex(upper_vertices, replace_model, head_links, motion.frames, bf)

                                # 回転調整
                                adjust_by_hand(replace_model, direction, all_rep_finger_links[direction], motion.frames, bf, upper_vertex_pos)

                            elif bf.frame > f:
                                break

        # -----------------------------------------------------------------
        # 腕IK
        elif is_hand_ik:
            # 腕IKによる位置調整を行う場合

            # 指の先までの位置(作成元モデル)
            all_org_finger_links, all_org_finger_indexes = trace_model.create_link_2_top_lr("人指３", "手首")
            logger.debug("all_org_finger_links: %s", [ "{0}: {1}\n".format(x.name, x.position) for x in all_org_finger_links["左"]])    
            logger.debug("all_org_finger_indexes: %s", [ x for x in all_org_finger_indexes["左"].keys()])    

            # 指の先までの位置(トレース先モデル)
            all_rep_finger_links, all_rep_finger_indexes = replace_model.create_link_2_top_lr("人指３", "手首")
            logger.debug("all_rep_finger_links: %s", all_rep_finger_indexes["右"].keys())

            # 肩から手首までのリンク生成(トレース先)
            arm_links = {
                "左": create_arm_links(replace_model, all_rep_wrist_links, "左"), 
                "右": create_arm_links(replace_model, all_rep_wrist_links, "右")
            }
            logger.debug("left_arm_links: %s", [ x.name for x in arm_links["左"]])    
            
            for d in ["左", "右"]:
                for al in arm_links[d]:
                    if not al.name in motion.frames:
                        # キーがまったくない場合、とりあえず初期値で登録する
                        logger.debug("キー登録: %s" % al.name)
                        motion.frames[al.name] = [calc_bone_by_complement(motion.frames, al.name, 0)]

            # 手首から指までのリンク生成(トレース先)
            finger_links = None
            if "左人指３" in replace_model.bones:
                # 指があるモデルのみ生成
                finger_links = {
                    "左": create_finger_links(replace_model, all_rep_finger_links, "左"), 
                    "右": create_finger_links(replace_model, all_rep_finger_links, "右")
                }
                logger.debug("left_finger_links: %s", [ x.name for x in finger_links["左"]])    

            # 作成元モデルの手のひらの大きさ（手首から人指３までの長さ）
            org_palm_length = 1
            if "左人指３" in trace_model.bones and "左手首" in trace_model.bones:
                org_palm_length = (trace_model.bones["左手首"].position - trace_model.bones["左人指３"].position).length()
                print("作成元モデルの手の大きさ: %s" % org_palm_length)

            # # 変換先モデルの手のひらの大きさ（手首から人指３までの長さ）
            rep_palm_length = 1
            if "左人指３" in replace_model.bones and "左手首" in replace_model.bones:
                rep_palm_length = (replace_model.bones["左手首"].position - replace_model.bones["左人指３"].position).length()
                print("変換先モデルの手の大きさ: %s" % rep_palm_length)
            
            # 手のひらの大きさ差
            palm_diff_length = rep_palm_length / org_palm_length
            logger.debug("palm_diff_length: %s", palm_diff_length)

            # 元モデルの上半身までのリンク生成
            org_upper_links, _ = trace_model.create_link_2_top_one( "上半身2", "上半身" )
            logger.debug("org_upper_links: %s", org_upper_links)

            # 変換先モデルの上半身までのリンク生成
            rep_upper_links, _ = replace_model.create_link_2_top_one( "上半身2", "上半身" )

            # 腕の長さの差（始点：腕, 終点：手首）
            org_arm_length = (trace_model.bones["右手首"].position - trace_model.bones["右腕"].position).length()
            logger.debug("org_arm_length: %s", org_arm_length)

            rep_arm_length = (replace_model.bones["右手首"].position - replace_model.bones["右腕"].position).length()
            logger.debug("rep_arm_length: %s", rep_arm_length)

            # if rep_arm_length > org_arm_length:
            # arm_diff_length = (org_arm_length / rep_arm_length)
            # else:
            arm_diff_length = rep_arm_length / org_arm_length

            # 腕の長さと手の大きさで小さい方を採用
            arm_palm_diff_length = arm_diff_length if arm_diff_length < palm_diff_length else palm_diff_length

            # 比率が1以上の場合、とりあえず1で固定
            arm_palm_diff_length = 1 if arm_palm_diff_length > 1 else arm_palm_diff_length

            print("腕/手の長さ比率(上限1): %s" % arm_palm_diff_length)

            # 作成元モデルの手首の厚み
            org_wrist_thickness = trace_model.get_wrist_thickness_lr()
            logger.debug("org_wrist_thickness: l: %s, r: %s", org_wrist_thickness["左"], org_wrist_thickness["右"])
            
            # 変換先モデルの手首の厚み
            rep_wrist_thickness = replace_model.get_wrist_thickness_lr()
            logger.debug("rep_wrist_thickness: l: %s, r: %s", rep_wrist_thickness["左"], rep_wrist_thickness["右"])

            # 左右の手首の厚み
            if rep_wrist_thickness["左"] == 0 or org_wrist_thickness["左"] == 0 or rep_wrist_thickness["右"] == 0 or org_wrist_thickness["右"] == 0:
                print("手首の厚みが正常に測れなかったため、厚みを考慮できません。")
                # 手首の厚みが取得できなかった場合、0で固定
                wrist_thickness = {
                    "左": 0,
                    "右": 0
                }
            else:
                wrist_thickness = {
                    "左": abs(rep_wrist_thickness["左"] - org_wrist_thickness["左"]) * arm_palm_diff_length,
                    "右": abs(rep_wrist_thickness["右"] - org_wrist_thickness["右"]) * arm_palm_diff_length
                }

            print("手首の厚み差: l: %s, r: %s" % ( wrist_thickness["左"], wrist_thickness["右"]))
            
            # error_file_logger.info("bone_name,start,now,end,t,x1v,y1v,x2v,y2v,A.x(),A.y(),E.x(),E.y(),H.x(),H.y(),J.x(),J.y(),I.x(),I.y(),G.x(),G.y(),D.x(),D.y(),before_diff.x(),before_diff.y(),after_diff.x(),after_diff.y(),bA.x(),bA.y(),bE.x(),bE.y(),bH.x(),bH.y(),bJ.x(),bJ.y(),aJ.x(),aJ.y(),aI.x(),aI.y(),aG.x(), aG.y(),aD.x(),aD.y(),bA6.x(),bA6.y(),bE6.x(),bE6.y(),bH6.x(),bH6.y(),bJ6.x(),bJ6.y(),aJ6.x(),aJ6.y(),aI6.x(),aI6.y(),aG6.x(),aG6.y(),aD6.x(),aD6.y() ,bA2.x(),bA2.y(),bE2.x(),bE2.y(),bH2.x(),bH2.y(),bJ2.x(),bJ2.y(),aJ2.x(),aJ2.y(),aI2.x(),aI2.y(),aG2.x(),aG2.y(),aD2.x(),aD2.y()")

            for f in range(motion.last_motion_frame + 1):
                is_checked = False

                for k in ["左腕", "左ひじ", "左手首", "右腕", "右ひじ", "右手首"]:
                    for bf_idx, bf in enumerate(motion.frames[k]):
                        if bf.frame == f:
                            # 該当フレームの場合
                            for direction in ["左", "右"]:
                                for al in arm_links[direction]:
                                    if al.name in motion.frames:
                                        is_added = False
                                        for tbf_idx, tbf in enumerate(motion.frames[al.name]):
                                            if tbf.frame == bf.frame:
                                                # とりあえず登録対象のキーが既存なので終了
                                                logger.debug("fill 既存あり: %s, i: %s, f: %s", al.name, tbf_idx, bf.frame)
                                                is_checked = True
                                                is_added = True
                                                break
                                            elif tbf.frame > bf.frame:
                                                # 対象のキーがなくて次に行ってしまった場合、挿入
                                                
                                                # 補間曲線込みでキーフレーム生成
                                                fillbf = calc_bone_by_complement(motion.frames, al.name, bf.frame, True)
                                                # 手首間の距離がマイナスの場合（デバッグ機能）で有効
                                                # 普通の場合、とりあえず実際に登録はしない
                                                fillbf.key = True if hand_distance < 0 else False

                                                motion.frames[al.name].insert(tbf_idx, fillbf)
                                                logger.debug("fill insert: %s, i: %s, f: %s, key: %s", al.name, tbf_idx, fillbf.frame, fillbf.key)

                                                is_checked = True
                                                is_added = True
                                                break
                                        
                                        if not is_added:
                                            # 最後のフレームがなくてそのまま終了してしまった場合は、直前のキーを設定する
                                            fillbf = copy.deepcopy(tbf)
                                            # とりあえず実際に登録はしない
                                            fillbf.key = False
                                            logger.debug("fill 今回なし: %s, i: %s, f: %s", al.name, tbf_idx, fillbf.frame)
                                            motion.frames[al.name].insert(tbf_idx, fillbf)

                            if is_checked:
                                # 両手が終わっててチェック済みならブレイク
                                break
                        
                        if is_checked:
                            # 両手が終わっててチェック済みならブレイク
                            break

                    if is_checked:
                        if f % 100 == 0:
                            print("腕合わせ事前調整 f: %s" % f)

                        # 両手が終わっててチェック済みならブレイク
                        break

            print("腕合わせ事前調整終了")

            if hand_distance >= 0:

                # キーフレーム分割済みのフレーム情報を別保持
                org_fill_motion_frames = copy.deepcopy(motion.frames)

                # 直前のキー
                prev_bf = None
                # 空白を挟んだ直前のキー
                prev_space_bf = None
                for f in range(motion.last_motion_frame + 1):
                    for k in ["左腕", "左ひじ", "左手首", "右腕", "右ひじ", "右手首"]:
                        is_ik_adjust = False

                        if k in motion.frames:
                            for bf_idx, bf in enumerate(motion.frames[k]):
                                if bf.key == True and bf.frame == f:
                                    if prev_bf and bf.frame - prev_bf.frame >= 2:
                                        # 直前キーがあり、かつ現在キーと2フレーム以上離れている場合、保持
                                        prev_space_bf = prev_bf
                                    
                                    # 方向
                                    org_direction = "左" if "左" in k else "右"
                                    # 逆方向
                                    reverse_org_direction = "右" if "左" in k else "左"
                                    
                                    # 元モデルのIK計算前指までの情報
                                    logger.debug("元モデルのIK計算前指までの情報")
                                    logger.debug("all_org_finger_links[org_direction]: %s(%s)", all_org_finger_links[org_direction][all_org_finger_indexes[org_direction]["肩"]], all_org_finger_indexes[org_direction]["肩"])
                                    _, _, _, _, org_finger_global_3ds = create_matrix_global(trace_model, all_org_finger_links[org_direction], org_motion_frames, bf, None)
                                    logger.debug("org_finger_global_3ds ------------------------")
                                    for n in range(len(all_org_finger_links[org_direction])):
                                        logger.debug("f: %s, org_finger_global_3ds %s, %s, %s", bf.frame, n, all_org_finger_links[org_direction][len(all_org_finger_links[org_direction]) - n - 1].name, org_finger_global_3ds[n])
                                    logger.debug("org 手首 index: %s", len(org_finger_global_3ds) - all_org_finger_indexes[org_direction]["手首"] - 1)
                                    logger.debug("元モデルの反対側の手の指までの情報")
                                    # 元モデルの反対側の手の指までの情報
                                    _, _, _, _, org_reverse_finger_global_3ds = create_matrix_global(trace_model, all_org_finger_links[reverse_org_direction], org_motion_frames, bf, None)
                                    logger.debug("org_reverse_finger_global_3ds ------------------------")
                                    for n in range(len(all_org_finger_links[reverse_org_direction])):
                                        logger.debug("f: %s, org_reverse_finger_global_3ds %s, %s, %s", bf.frame, n, all_org_finger_links[reverse_org_direction][len(all_org_finger_links[reverse_org_direction]) - n - 1].name, org_reverse_finger_global_3ds[n])
                                
                                    # 変換先モデルのIK計算前指までの情報
                                    _, _, _, _, rep_finger_global_3ds = create_matrix_global(replace_model, all_rep_finger_links[org_direction], motion.frames, bf, None)
                                    logger.debug("rep_finger_global_3ds ------------------------")
                                    for n in range(len(all_rep_finger_links[org_direction])):
                                        logger.debug("f: %s, rep_finger_global_3ds %s, %s, %s", bf.frame, n, all_rep_finger_links[org_direction][len(all_rep_finger_links[org_direction]) - n - 1].name, rep_finger_global_3ds[n])
                                    # 変換先モデルの反対側IK計算前指までの情報
                                    _, _, _, _, rep_reverse_finger_global_3ds = create_matrix_global(replace_model, all_rep_finger_links[reverse_org_direction], motion.frames, bf, None)
                                    logger.debug("rep_reverse_finger_global_3ds ------------------------")
                                    for n in range(len(all_rep_finger_links[reverse_org_direction])):
                                        logger.debug("f: %s, rep_reverse_finger_global_3ds %s, %s, %s", bf.frame, n, all_rep_finger_links[reverse_org_direction][len(all_rep_finger_links[reverse_org_direction]) - n - 1].name, rep_reverse_finger_global_3ds[n])

                                    logger.debug("d: %s", [org_direction, reverse_org_direction])

                                    logger.debug("all_org_finger_indexes[org_direction]: %s", all_org_finger_indexes[org_direction])
                                    logger.debug("org_wrist: %s", org_finger_global_3ds[len(org_finger_global_3ds) - all_org_finger_indexes[org_direction]["手首"] - 1])
                                    # # logger.debug("all_org_finger_indexes: %s", [ "{0}\n".format(x) for x in org_finger_global_3ds])    
                                    logger.debug("reverse_wrist: %s", org_reverse_finger_global_3ds[len(org_reverse_finger_global_3ds) - all_org_finger_indexes[reverse_org_direction]["手首"] - 1])
                                    logger.debug("org_wrist_diff_3d: %s", (org_finger_global_3ds[len(org_finger_global_3ds) - all_org_finger_indexes[org_direction]["手首"] - 1] - org_reverse_finger_global_3ds[len(org_reverse_finger_global_3ds) - all_org_finger_indexes[reverse_org_direction]["手首"] - 1]))

                                    # 手首の距離
                                    org_wrist_diff = (org_finger_global_3ds[len(org_finger_global_3ds) - all_org_finger_indexes[org_direction]["手首"] - 1]).distanceToPoint(org_reverse_finger_global_3ds[len(org_reverse_finger_global_3ds) - all_org_finger_indexes[reverse_org_direction]["手首"] - 1])
                                    logger.debug("org_wrist_diff: %s", org_wrist_diff)

                                    # 手首の距離
                                    rep_wrist_diff = (rep_finger_global_3ds[len(rep_finger_global_3ds) - all_rep_finger_indexes[org_direction]["手首"] - 1] - rep_reverse_finger_global_3ds[len(rep_reverse_finger_global_3ds) - all_rep_finger_indexes[reverse_org_direction]["手首"] - 1]).length()
                                    logger.debug("rep_wrist_diff: %s", rep_wrist_diff)

                                    # 手首間の距離
                                    org_wrist_diff_rate = (org_wrist_diff / org_palm_length)

                                    # 手首の距離が手のひらの大きさより大きいか(ハート型とかあるので、可変)
                                    is_over_org_palm_length = hand_distance <= org_wrist_diff_rate

                                    logger.debug("org_wrist_diff_rate: %s, org_palm_length: %s, org_wrist_diff: %s", org_wrist_diff_rate, org_palm_length, org_wrist_diff)

                                    if not is_over_org_palm_length or hand_distance == 10:
                                        # if prev_bf and bf.frame - prev_bf.frame < 2:
                                        #     # 前回が調整なしで前回フレームと1Fしか離れていない場合、前回をOFF
                                        #     continue
                                        
                                        for direction in [org_direction, reverse_org_direction]:
                                            # 逆方向
                                            reverse_direction = "右" if "左" == direction else "左"

                                            # 手首が近接している場合のみ、腕IK処理実施
                                            print("○手首近接あり: f: %s(%s), 手首間の距離: %s" % (bf.frame, direction, org_wrist_diff_rate ))

                                            # 元モデルの向いている回転量
                                            org_upper_direction_qq = calc_upper_direction_qq(trace_model, org_upper_links, org_motion_frames, bf)
                                            logger.debug("org_upper_direction_qq: %s", org_upper_direction_qq.toEulerAngles())

                                            # 元モデルの向きを逆転させて、正面向きの位置を計算する
                                            org_front_finger_global_3ds = create_direction_pos_all(org_upper_direction_qq.inverted(), org_finger_global_3ds)
                                            # 元モデルの向きを逆転させて、正面向きの位置を計算する(反対側)
                                            org_reverse_front_finger_global_3ds = create_direction_pos_all(org_upper_direction_qq.inverted(), org_reverse_finger_global_3ds)

                                            # 元モデルの正面向き上半身の位置
                                            org_front_upper_pos = org_front_finger_global_3ds[len(org_finger_global_3ds) - all_org_finger_indexes[direction]["上半身"] - 1]
                                            # 元モデルの正面向き手首の位置
                                            org_front_wrist_pos = org_front_finger_global_3ds[len(org_finger_global_3ds) - all_org_finger_indexes[direction]["手首"] - 1]
                                            # 元モデルの正面向き手首の位置（反対側）
                                            org_reverse_front_wrist_pos = org_reverse_front_finger_global_3ds[len(org_reverse_front_finger_global_3ds) - all_org_finger_indexes[reverse_direction]["手首"] - 1]

                                            # 元モデルの正面向き指の位置
                                            org_front_finger_pos = org_front_finger_global_3ds[len(org_front_finger_global_3ds) - all_org_finger_indexes[direction]["人指３"] - 1]
                                            # 元モデルの正面向き指の位置(反対側)
                                            org_reverse_front_finger_pos = org_reverse_front_finger_global_3ds[len(org_reverse_front_finger_global_3ds) - all_org_finger_indexes[reverse_direction]["人指３"] - 1]

                                            logger.debug("frame: %s, org_front_upper_pos before: %s", bf.frame, org_front_upper_pos)
                                            logger.debug("frame: %s, org_front_wrist_pos before: %s", bf.frame, org_front_wrist_pos)
                                            logger.debug("frame: %s, org_reverse_front_wrist_pos before: %s", bf.frame, org_reverse_front_wrist_pos)

                                            # 変換先モデルの手首位置
                                            rep_wrist_pos = rep_finger_global_3ds[len(rep_finger_global_3ds) - all_rep_finger_indexes[direction]["手首"] - 1]
                                            logger.debug("frame: %s, rep_wrist_pos before: %s", bf.frame, rep_wrist_pos)
                                            # 変換先モデルの手首位置
                                            rep_reverse_wrist_pos = rep_reverse_finger_global_3ds[len(rep_reverse_finger_global_3ds) - all_rep_finger_indexes[reverse_direction]["手首"] - 1]
                                            logger.debug("frame: %s, rep_reverse_wrist_pos before: %s", bf.frame, rep_reverse_wrist_pos)

                                            # 変換先モデルの向いている回転量
                                            rep_upper_direction_qq = calc_upper_direction_qq(replace_model, rep_upper_links, motion.frames, bf)
                                            logger.debug("rep_upper_direction_qq: %s", rep_upper_direction_qq.toEulerAngles())

                                            # 変換先モデルの向きを逆転させて、正面向きの手首の位置を計算する
                                            rep_front_finger_global_3ds = create_direction_pos_all(rep_upper_direction_qq.inverted(), rep_finger_global_3ds)
                                            # 変換先モデルの向きを逆転させて、正面向きの手首の位置を計算する
                                            rep_reverse_front_finger_global_3ds = create_direction_pos_all(rep_upper_direction_qq.inverted(), rep_reverse_finger_global_3ds)

                                            # 変換先モデルの正面向き上半身の位置
                                            rep_front_upper_pos = rep_front_finger_global_3ds[len(rep_finger_global_3ds) - all_rep_finger_indexes[direction]["上半身"] - 1]
                                            # 変換先モデルの正面向き手首の位置
                                            rep_front_wrist_pos = rep_front_finger_global_3ds[len(rep_finger_global_3ds) - all_rep_finger_indexes[direction]["手首"] - 1]
                                            # 変換先モデルの正面向き反対側手首の位置
                                            rep_reverse_front_wrist_pos = rep_reverse_front_finger_global_3ds[len(rep_reverse_front_finger_global_3ds) - all_rep_finger_indexes[reverse_direction]["手首"] - 1]

                                            logger.debug("frame: %s, rep_front_upper_pos before: %s", bf.frame, rep_front_upper_pos)
                                            logger.debug("frame: %s, rep_front_wrist_pos before: %s", bf.frame, rep_front_wrist_pos)
                                            logger.debug("frame: %s, rep_reverse_front_wrist_pos before: %s", bf.frame, rep_reverse_front_wrist_pos)
                                            
                                            logger.debug("org_front_upper_pos before: %s", org_front_upper_pos)
                                            logger.debug("org_front_wrist_pos before: %s", org_front_wrist_pos)
                                            logger.debug("org_reverse_front_wrist_pos before: %s", org_reverse_front_wrist_pos)
                                            logger.debug("rep_front_upper_pos before: %s", rep_front_upper_pos)
                                            logger.debug("rep_front_wrist_pos before: %s", rep_front_wrist_pos)
                                            logger.debug("rep_reverse_front_wrist_pos before: %s", rep_reverse_front_wrist_pos)

                                            # 手首の位置を元モデルとだいたい同じ位置にする
                                            # 1. 自分自身の上半身X位置
                                            # 2: 元モデルの上半身と手首位置の差
                                            rep_wrist_x = rep_front_upper_pos.x() \
                                                + ( org_front_wrist_pos.x() - org_front_upper_pos.x() ) * arm_palm_diff_length
                                            rep_wrist_x_diff = rep_front_wrist_pos.x() - rep_wrist_x
                                            logger.debug("rep_wrist_x_diff: %s", rep_wrist_x_diff)
                                            rep_front_wrist_pos.setX(rep_wrist_x)
                                                
                                            # 手首の位置を元モデルとだいたい同じ位置にする(反対側)
                                            rep_reverse_wrist_x = rep_front_upper_pos.x() \
                                                + ( org_reverse_front_wrist_pos.x() - org_front_upper_pos.x() ) * arm_palm_diff_length
                                            rep_reverse_wrist_x_diff = rep_reverse_front_wrist_pos.x() - rep_reverse_wrist_x
                                            logger.debug("rep_reverse_wrist_x_diff: %s", rep_reverse_wrist_x_diff)
                                            rep_reverse_front_wrist_pos.setX( rep_reverse_wrist_x )

                                            logger.debug("rep_front_wrist_pos x after: %s", rep_front_wrist_pos)
                                            logger.debug("rep_reverse_front_wrist_pos x after: %s", rep_reverse_front_wrist_pos)

                                            # 手首の厚みを考慮
                                            wrist_diff_sign = 1 if direction == "左" else -1
                                            wrist_reverse_diff_sign = -1 if reverse_direction == "右" else 1
                                            
                                            if org_wrist_diff_rate < 0.5:
                                                # 手のひらがピタッとくっついているような場合、手のひらの厚み補正
                                                rep_front_wrist_pos.setX( rep_front_wrist_pos.x() + (wrist_thickness[direction] * wrist_diff_sign))
                                                rep_reverse_front_wrist_pos.setX( rep_reverse_front_wrist_pos.x() + (wrist_thickness[reverse_direction] * wrist_reverse_diff_sign))

                                            if arm_palm_diff_length >= 1 and org_wrist_diff_rate >= 1 \
                                                and ((org_front_wrist_pos.x() <= org_front_finger_pos.x() <= org_reverse_front_wrist_pos.x() \
                                                        and org_front_wrist_pos.x() <= org_reverse_front_finger_pos.x() <= org_reverse_front_wrist_pos.x()) \
                                                    or (org_front_wrist_pos.x() >= org_front_finger_pos.x() >= org_reverse_front_wrist_pos.x() \
                                                        and org_front_wrist_pos.x() >= org_reverse_front_finger_pos.x() >= org_reverse_front_wrist_pos.x())) :
                                                # 変換先の方が大きくて、ある程度離れていて、かつ指が両手首の間にある場合、手の大きさを考慮する

                                                # 元モデルの手首から指３までで最も手首から離れている距離
                                                org_farer_finger_length = calc_farer_finger_length(org_front_finger_global_3ds, all_org_finger_indexes, direction)
                                                logger.debug("org_farer_finger_length: %s", org_farer_finger_length)

                                                # 元モデルの手の大きさとの差
                                                org_farer_finger_diff = org_farer_finger_length - org_palm_length
                                                logger.debug("org_farer_finger_diff: %s", org_farer_finger_diff)

                                                # 元モデルの手首から指３までで最も手首から離れている距離（反対側）
                                                org_reverse_farer_finger_length = calc_farer_finger_length(org_reverse_front_finger_global_3ds, all_org_finger_indexes, reverse_direction)
                                                logger.debug("org_farer_finger_length: %s", org_farer_finger_length)

                                                # 元モデルの手の大きさとの差（反対側）
                                                org_reverse_farer_finger_diff = org_reverse_farer_finger_length - org_palm_length
                                                logger.debug("org_reverse_farer_finger_diff: %s", org_reverse_farer_finger_diff)

                                                # 手首から指３までで最も手首から離れている距離
                                                rep_farer_finger_length = calc_farer_finger_length(rep_front_finger_global_3ds, all_rep_finger_indexes, direction)
                                                logger.debug("rep_farer_finger_length: %s", rep_farer_finger_length)

                                                # 手の大きさとの差
                                                rep_farer_finger_diff = rep_farer_finger_length - rep_palm_length
                                                logger.debug("rep_farer_finger_diff: %s", rep_farer_finger_diff)

                                                logger.debug("手の大きさ: %s", ( rep_farer_finger_diff - org_farer_finger_length ))

                                                # 手首から指３までで最も手首から離れている距離
                                                rep_reverse_farer_finger_length = calc_farer_finger_length(rep_reverse_front_finger_global_3ds, all_rep_finger_indexes, reverse_direction)
                                                logger.debug("rep_reverse_farer_finger_length: %s", rep_reverse_farer_finger_length)

                                                # 手の大きさとの差
                                                rep_reverse_farer_finger_diff = rep_reverse_farer_finger_length - rep_palm_length
                                                logger.debug("rep_reverse_farer_finger_diff: %s", rep_reverse_farer_finger_diff)

                                                rep_front_wrist_pos.setX( rep_front_wrist_pos.x() \
                                                    + ( rep_farer_finger_length - org_farer_finger_length ) * wrist_diff_sign
                                                )

                                                rep_reverse_front_wrist_pos.setX( rep_reverse_front_wrist_pos.x() \
                                                    + ( rep_reverse_farer_finger_length - org_reverse_farer_finger_length ) * wrist_reverse_diff_sign
                                                )

                                            logger.debug("frame: %s, rep_front_wrist_pos after: %s", bf.frame, rep_front_wrist_pos)
                                            logger.debug("frame: %s, rep_reverse_front_wrist_pos after: %s", bf.frame, rep_reverse_front_wrist_pos)

                                            # 変換先モデルの向きを元に戻して、正面向きの手首を回転させた位置に合わせる
                                            rep_wrist_pos = create_direction_pos(rep_upper_direction_qq, rep_front_wrist_pos)
                                            logger.debug("frame: %s, rep_wrist_pos after: %s", bf.frame, rep_wrist_pos)

                                            # ---------
                                            wrist_ik_bone = "{0}偽IK".format(direction)
                                            if not wrist_ik_bone in motion.frames:
                                                motion.frames[wrist_ik_bone] = []
                                            
                                            wikbf = VmdBoneFrame(bf.frame)
                                            wikbf.name = wrist_ik_bone.encode('shift-jis')
                                            wikbf.format_name = wrist_ik_bone
                                            wikbf.frame = bf.frame
                                            wikbf.key = True
                                            wikbf.position = rep_wrist_pos
                                            motion.frames[wrist_ik_bone].append(wikbf)
                                            # ---------

                                            # 変換先モデルの向きを元に戻して、正面向きの手首を回転させた位置に合わせる(反対側)
                                            rep_reverse_wrist_pos = create_direction_pos(rep_upper_direction_qq, rep_reverse_front_wrist_pos)
                                            logger.debug("frame: %s, rep_reverse_wrist_pos after: %s", bf.frame, rep_reverse_wrist_pos)

                                            # ---------
                                            reverse_wrist_ik_bone = "{0}偽IK".format(reverse_direction)
                                            if not reverse_wrist_ik_bone in motion.frames:
                                                motion.frames[reverse_wrist_ik_bone] = []
                                            
                                            rwikbf = VmdBoneFrame(bf.frame)
                                            rwikbf.name = reverse_wrist_ik_bone.encode('shift-jis')
                                            rwikbf.format_name = reverse_wrist_ik_bone
                                            rwikbf.frame = bf.frame
                                            rwikbf.key = True
                                            rwikbf.position = rep_reverse_wrist_pos
                                            motion.frames[reverse_wrist_ik_bone].append(rwikbf)
                                            # ---------

                                            # 手首位置から角度を求める
                                            calc_arm_IK2FK(rep_wrist_pos, replace_model, arm_links[direction], all_rep_wrist_links[direction], direction, motion.frames, bf, prev_space_bf)
                                            # 反対側の手首位置から角度を求める
                                            calc_arm_IK2FK(rep_reverse_wrist_pos, replace_model, arm_links[reverse_direction], all_rep_wrist_links[reverse_direction], reverse_direction, motion.frames, bf, prev_space_bf)

                                            # # 指位置調整-----------------

                                            if finger_links:
                                                # 指があるモデルの場合、手首角度調整

                                                # 手首の位置が変わっているので再算出

                                                # 変換先モデルのIK計算前指までの情報
                                                _, _, _, _, rep_finger_global_3ds = create_matrix_global(replace_model, all_rep_finger_links[org_direction], motion.frames, bf, None)
                                                logger.debug("rep_finger_global_3ds ------------------------")
                                                for n in range(len(all_rep_finger_links[org_direction])):
                                                    logger.debug("rep_finger_global_3ds %s, %s, %s", n, all_rep_finger_links[org_direction][len(all_rep_finger_links[org_direction]) - n - 1].name, rep_finger_global_3ds[n])
                                                # 変換先モデルの反対側IK計算前指までの情報
                                                _, _, _, _, rep_reverse_finger_global_3ds = create_matrix_global(replace_model, all_rep_finger_links[reverse_org_direction], motion.frames, bf, None)
                                                logger.debug("rep_reverse_finger_global_3ds ------------------------")
                                                for n in range(len(all_rep_finger_links[reverse_org_direction])):
                                                    logger.debug("rep_finger_global_3ds %s, %s, %s", n, all_rep_finger_links[reverse_org_direction][len(all_rep_finger_links[reverse_org_direction]) - n - 1].name, rep_reverse_finger_global_3ds[n])

                                                # 変換先モデルの手首位置
                                                rep_wrist_pos = rep_finger_global_3ds[len(rep_finger_global_3ds) - all_rep_finger_indexes[direction]["手首"] - 1]
                                                logger.debug("frame: %s, rep_wrist_pos before: %s", bf.frame, rep_wrist_pos)
                                                # 変換先モデルの手首位置
                                                rep_reverse_wrist_pos = rep_reverse_finger_global_3ds[len(rep_reverse_finger_global_3ds) - all_rep_finger_indexes[reverse_direction]["手首"] - 1]
                                                logger.debug("frame: %s, rep_reverse_wrist_pos before: %s", bf.frame, rep_reverse_wrist_pos)

                                                # 変換先モデルの向いている回転量
                                                rep_upper_direction_qq = calc_upper_direction_qq(replace_model, rep_upper_links, motion.frames, bf)
                                                logger.debug("rep_upper_direction_qq: %s", rep_upper_direction_qq.toEulerAngles())

                                                # 変換先モデルの向きを逆転させて、正面向きの手首の位置を計算する
                                                rep_front_finger_global_3ds = create_direction_pos_all(rep_upper_direction_qq.inverted(), rep_finger_global_3ds)
                                                # 変換先モデルの向きを逆転させて、正面向きの手首の位置を計算する
                                                rep_reverse_front_finger_global_3ds = create_direction_pos_all(rep_upper_direction_qq.inverted(), rep_reverse_finger_global_3ds)

                                                # 変換先モデルの正面向き上半身の位置
                                                rep_front_upper_pos = rep_front_finger_global_3ds[len(rep_finger_global_3ds) - all_rep_finger_indexes[direction]["上半身"] - 1]
                                                # 変換先モデルの正面向き手首の位置
                                                rep_front_wrist_pos = rep_front_finger_global_3ds[len(rep_finger_global_3ds) - all_rep_finger_indexes[direction]["手首"] - 1]
                                                # 変換先モデルの正面向き反対側手首の位置
                                                rep_reverse_front_wrist_pos = rep_reverse_front_finger_global_3ds[len(rep_reverse_front_finger_global_3ds) - all_rep_finger_indexes[reverse_direction]["手首"] - 1]

                                                # 変換先モデルの正面向き指３の位置
                                                rep_front_finger_pos = rep_front_finger_global_3ds[len(rep_front_finger_global_3ds) - all_rep_finger_indexes[direction]["人指３"] - 1]
                                                # 変換先モデルの正面向き指３の位置
                                                rep_reverse_front_finger_pos = rep_reverse_front_finger_global_3ds[len(rep_reverse_front_finger_global_3ds) - all_rep_finger_indexes[reverse_direction]["人指３"] - 1]

                                                # if (org_front_wrist_pos.x() <= org_front_finger_pos.x() <= org_reverse_front_wrist_pos.x() \
                                                #     and org_front_wrist_pos.x() <= org_reverse_front_finger_pos.x() <= org_reverse_front_wrist_pos.x()) \
                                                #     or (org_front_wrist_pos.x() >= org_front_finger_pos.x() >= org_reverse_front_wrist_pos.x() \
                                                #     and org_front_wrist_pos.x() >= org_reverse_front_finger_pos.x() >= org_reverse_front_wrist_pos.x()) :
                                                logger.debug("指位置調整: ow: %s, of: %s, orf: %s, orw: %s", org_front_wrist_pos.x(), org_front_finger_pos.x(), org_reverse_front_finger_pos.x(), org_reverse_front_wrist_pos.x() )
                                                    
                                                # 指の位置を元モデルとだいたい同じ位置にする
                                                # 1. 自分自身の上半身X位置
                                                # 2: 元モデルの上半身と手首位置の差
                                                rep_front_finger_pos.setX( rep_front_wrist_pos.x() \
                                                    + (( org_front_finger_pos.x() - org_front_wrist_pos.x() ) * arm_palm_diff_length )
                                                )
                                                logger.debug("(( org_front_finger_pos.x() - org_front_upper_pos.x() ) * arm_diff_length): %s", (( org_front_finger_pos.x() - org_front_upper_pos.x() ) * arm_diff_length))
                                                    
                                                # 指の位置を元モデルとだいたい同じ位置にする(反対側)
                                                rep_reverse_front_finger_pos.setX( rep_reverse_front_wrist_pos.x() \
                                                    + (( org_reverse_front_finger_pos.x() - org_reverse_front_wrist_pos.x() ) * arm_palm_diff_length)
                                                )
                                                logger.debug("(( org_reverse_front_finger_pos.x() - org_front_upper_pos.x() )  * arm_diff_length): %s", (( org_reverse_front_finger_pos.x() - org_front_upper_pos.x() )  * arm_diff_length))

                                                # 変換先モデルの向きを元に戻して、正面向きの指３を回転させた位置に合わせる
                                                rep_finger_pos = create_direction_pos(rep_upper_direction_qq, rep_front_finger_pos)
                                                logger.debug("frame: %s, rep_finger_pos after: %s", bf.frame, rep_finger_pos)

                                                # 変換先モデルの向きを元に戻して、正面向きの指３を回転させた位置に合わせる(反対側)
                                                rep_reverse_finger_pos = create_direction_pos(rep_upper_direction_qq, rep_reverse_front_finger_pos)
                                                logger.debug("frame: %s, rep_reverse_finger_pos after: %s", bf.frame, rep_reverse_finger_pos)

                                                # 指３位置から角度を求める
                                                calc_arm_IK2FK(rep_finger_pos, replace_model, finger_links[direction], all_rep_finger_links[direction], direction, motion.frames, bf, prev_space_bf)
                                                # 反対側の指３位置から角度を求める
                                                calc_arm_IK2FK(rep_reverse_finger_pos, replace_model, finger_links[reverse_direction], all_rep_finger_links[reverse_direction], reverse_direction, motion.frames, bf, prev_space_bf)

                                            break

                                        # 手首位置合わせ結果判定 ------------

                                        logger.debug("bf: %s, 右腕: %s", bf.frame, motion.frames["左腕"][bf_idx].frame)

                                        # d = QQuaternion.dotProduct(bf.rotation, org_bf.rotation)
                                        # rk_name = bf.format_name.replace(direction, reverse_direction)
                                        logger.debug("bf.name: %s, bf_idx: %s, 右肩: %s", bf.format_name, bf_idx, len(motion.frames["右肩"]))
                                        # lsd = abs(QQuaternion.dotProduct(motion.frames["左肩"][bf_idx].rotation, org_fill_motion_frames["左肩"][bf_idx].rotation))
                                        # rsd = abs(QQuaternion.dotProduct(motion.frames["右肩"][bf_idx].rotation, org_fill_motion_frames["右肩"][bf_idx].rotation))
                                        lad = abs(QQuaternion.dotProduct(motion.frames["左腕"][bf_idx].rotation, org_fill_motion_frames["左腕"][bf_idx].rotation))
                                        rad = abs(QQuaternion.dotProduct(motion.frames["右腕"][bf_idx].rotation, org_fill_motion_frames["右腕"][bf_idx].rotation))
                                        if lad < 0.85 or rad < 0.85:
                                            print("%sフレーム目手首位置合わせ失敗: 手首間: %s, 左腕:%s, 右腕:%s" % (bf.frame, org_wrist_diff_rate, lad, rad))
                                            # 失敗時のみエラーログ出力
                                            if not is_hand_ik_error_outputed:
                                                is_hand_ik_error_outputed = True
                                                if not error_file_logger:
                                                    error_file_logger.addHandler(logging.FileHandler(error_path))

                                                error_file_logger.info("モーション: %s" , motion.path)
                                                error_file_logger.info("作成元: %s" , trace_model.path)
                                                error_file_logger.info("変換先: %s" , replace_model.path)
                                                error_file_logger.info("作成元モデルの手の大きさ: %s", org_palm_length)
                                                error_file_logger.info("変換先モデルの手の大きさ: %s", rep_palm_length)
                                                error_file_logger.info("手首の厚み: l: %s, r: %s", wrist_thickness["左"], wrist_thickness["右"])
                                                # error_file_logger.debug("作成元の上半身の厚み: %s", org_upper_thickness_diff)
                                                # error_file_logger.debug("変換先の上半身の厚み: %s", rep_upper_thickness_diff)
                                                # error_file_logger.debug("肩幅の差: %s" , showlder_diff_length)

                                            error_file_logger.warning("%sフレーム目手首位置合わせ失敗: 手首間: %s, 左腕:%s, 右腕:%s" , bf.frame, org_wrist_diff_rate, lad, rad)
                                        else:
                                            logger.info("手首位置合わせ成功: f: %s, 左腕:%s, 右腕:%s", bf.frame, lad, rad)

                                        for cfk, cflist in org_fill_motion_frames.items():
                                            for dd in [direction, reverse_direction]:
                                                # 指位置調整は実際には手首のみ角度調整で、arm_linksに含まれている
                                                for al in arm_links[dd]:
                                                    if al.name == cfk:
                                                        if lad >= 0.85 and rad >= 0.85:
                                                            # 角度調整が既定内である場合
                                                            motion.frames[cfk][bf_idx].key = True
                                                            logger.debug("採用: cfk: %s, bf: %s, f: %s, rot: %s", cfk, bf.frame, motion.frames[cfk][bf_idx].frame, motion.frames[cfk][bf_idx].rotation.toEulerAngles())

                                                            # 前のキーが1つより多く離れていたら有効化
                                                            if bf_idx - 1 >= 0 and motion.frames[cfk][bf_idx].frame > motion.frames[cfk][bf_idx - 1].frame + 1:
                                                                motion.frames[cfk][bf_idx - 1].key = True

                                                            # for cfk2, cflist2 in motion.frames.items():
                                                            #     for cfv2 in cflist2:
                                                            #         if cfv2.frame == 605:
                                                            #             logger.debug("採用派生チェック %s: al: %s, key: %s", cfv2.frame, cfv2.format_name, cfv2.key)

                                                        else:
                                                            # 角度調整が既定外である場合、クリア
                                                            motion.frames[cfk][bf_idx] = copy.deepcopy(cflist[bf_idx])
                                                            logger.debug("クリア: cfk: %s, bf_idx: %s, rot: %s", cfk, bf_idx, motion.frames[cfk][bf_idx].rotation.toEulerAngles())
                                                        break

                                    else:
                                        print("－手首近接なし: f: %s(%s), 手首間の距離: %s" % (bf.frame, direction, org_wrist_diff_rate ))

                                    # 前回登録キーとして保持
                                    prev_bf = copy.deepcopy(bf)
                                        
                                    # とりえあずチェックは済んでるのでFLG=ON
                                    is_ik_adjust = True

                                    # 片手が終わってたら両手済み
                                    break
                            
                                if is_ik_adjust:
                                    # 既にIK調整終了していたら片手分のループを抜ける
                                    break
                        
                        if is_ik_adjust:
                            # 既にIK調整終了していたら片手分のループを抜ける
                            break

                # 補間曲線を有効なキーだけに揃える
                prev_bf = next_bf = None
                next_added_bfs = prev_added_bfs = []
                
                for direction in ["左", "右"]:
                    for al in arm_links[direction]:
                        for bf_idx, bf in enumerate(motion.frames[al.name]):
                            now_bf = motion.frames[al.name][bf_idx]

                            if len(next_added_bfs) > 0 and next_added_bfs[0].frame >= now_bf.frame:
                                # 前回、次回の有効キーを算出していて、それが現在キーより先の場合、処理スキップ
                                continue

                            # 前回のキー情報をクリア
                            prev_bf = next_bf = None
                            next_added_bfs = prev_added_bfs = []

                            # 読み込んだ時の次のキー
                            for nbf_idx in range(bf_idx + 1, len(motion.frames[al.name])):
                                if motion.frames[al.name][nbf_idx].read == True and motion.frames[al.name][nbf_idx].frame > now_bf.frame:
                                    next_bf = motion.frames[al.name][nbf_idx]
                                    break

                            # 次の追加した有効なキー（読み込み次回キーの前のを全部見る）
                            if next_bf:
                                for nbf_idx in range(bf_idx + 1, len(motion.frames[al.name])):
                                    if motion.frames[al.name][nbf_idx].read == False and motion.frames[al.name][nbf_idx].key == True and motion.frames[al.name][nbf_idx].frame < next_bf.frame:
                                        next_added_bfs.append(motion.frames[al.name][nbf_idx])

                                    if motion.frames[al.name][nbf_idx].frame > next_bf.frame:
                                        break
                                
                            # 有効な前のキー
                            for pbf_idx in range(bf_idx - 1, -1, -1):
                                if motion.frames[al.name][pbf_idx].read == True and motion.frames[al.name][pbf_idx].frame < now_bf.frame:
                                    prev_bf = motion.frames[al.name][pbf_idx]
                                    break
                            
                            # 前の追加した有効なキー（読み込み前回キーの以降のを全部見る）
                            if prev_bf:
                                for nbf_idx in range(bf_idx - 1, -1, -1):
                                    if motion.frames[al.name][nbf_idx].read == False and motion.frames[al.name][nbf_idx].key == True and motion.frames[al.name][nbf_idx].frame > prev_bf.frame:
                                        prev_added_bfs.append(motion.frames[al.name][nbf_idx])

                                    if motion.frames[al.name][nbf_idx].frame < prev_bf.frame:
                                        break
                                
                            if prev_bf and next_bf:
                                if 5260 <= bf.frame <= 5290:
                                    logger.debug("補間曲線再設定: %s: %s, p: %s, n: %s", al.name, now_bf.frame, prev_bf.frame, next_bf.frame)
                                    logger.debug("now: x: %s, y: %s", now_bf.complement[R_x1_idxs[3]], now_bf.complement[R_y1_idxs[3]])
                                    logger.debug("prev: %s", prev_bf.complement)
                                    logger.debug("next: %s", next_bf.complement)
                                
                                # 計算用の前キーフレ・今キーフレ・次キーフレ
                                c_now_bf = None
                                if prev_bf and next_bf:
                                    if now_bf.read == True:
                                        if len(next_added_bfs) == 0 and len(prev_added_bfs) == 0:
                                            # 読み込みキーで、前も後もまったくない場合、補間曲線をクリアする
                                            if al.name == "左ひじ":
                                                logger.info("[A]読み込みキーで、前も後もまったくない場合: %s, b: %s, p: %s, n: %s", now_bf.frame, al.name, prev_bf.frame, next_bf.frame )

                                            # 次回読み込みキーの始点を元に戻す
                                            next_bf.complement[R_x1_idxs[0]] = next_bf.complement[R_x1_idxs[1]] = next_bf.complement[R_x1_idxs[2]] = next_bf.complement[R_x1_idxs[3]] = next_bf.org_complement[R_x1_idxs[3]]
                                            next_bf.complement[R_y1_idxs[0]] = next_bf.complement[R_y1_idxs[1]] = next_bf.complement[R_y1_idxs[2]] = next_bf.complement[R_y1_idxs[3]] = next_bf.org_complement[R_y1_idxs[3]]

                                            # 次回読み込みキーの終点を元に戻す
                                            next_bf.complement[R_x2_idxs[0]] = next_bf.complement[R_x2_idxs[1]] = next_bf.complement[R_x2_idxs[2]] = next_bf.complement[R_x2_idxs[3]] = next_bf.org_complement[R_x2_idxs[3]]
                                            next_bf.complement[R_y2_idxs[0]] = next_bf.complement[R_y2_idxs[1]] = next_bf.complement[R_y2_idxs[2]] = next_bf.complement[R_y2_idxs[3]] = next_bf.org_complement[R_y2_idxs[3]]                                    
                                        else:
                                            # 読み込みキーで、前後どちらかある場合、処理スルー
                                            if al.name == "左ひじ":
                                                logger.info("[B]読み込みキーで、前後どちらかある場合、処理スルー: %s, b: %s, p: %s, n: %s", now_bf.frame, al.name, prev_bf.frame, next_bf.frame )
                                            pass
                                    else:
                                        # 追加キー
                                        if now_bf.key == True:
                                            # 追加キーが有効
                                            if len(next_added_bfs) == 0:
                                                # 追加キーで、後がまったくない場合
                                                if al.name == "左ひじ":
                                                    logger.info("[C]追加キーで、後がまったくない場合: %s, b: %s, p: %s, n: %s", now_bf.frame, al.name, prev_bf.frame, next_bf.frame )
                                                c_now_bf = now_bf
                                            else:
                                                # 追加キーで、後がある場合
                                                if al.name == "左ひじ":
                                                    logger.info("[D]追加キーで、後がある場合: %s, b: %s, p: %s, n: %s", now_bf.frame, al.name, prev_bf.frame, next_bf.frame )
                                                pass
                                        else:
                                            # 追加キーが無効
                                            if len(next_added_bfs) == 0 and len(prev_added_bfs) == 0:
                                                # 追加キーが無効で、前も後もまったくない場合
                                                if al.name == "左ひじ":
                                                    logger.info("[E]追加キーが無効で、前も後もまったくない場合: %s, b: %s, p: %s, n: %s", now_bf.frame, al.name, prev_bf.frame, next_bf.frame )

                                                # 次回読み込みキーの始点を元に戻す
                                                next_bf.complement[R_x1_idxs[0]] = next_bf.complement[R_x1_idxs[1]] = next_bf.complement[R_x1_idxs[2]] = next_bf.complement[R_x1_idxs[3]] = next_bf.org_complement[R_x1_idxs[3]]
                                                next_bf.complement[R_y1_idxs[0]] = next_bf.complement[R_y1_idxs[1]] = next_bf.complement[R_y1_idxs[2]] = next_bf.complement[R_y1_idxs[3]] = next_bf.org_complement[R_y1_idxs[3]]

                                                # 次回読み込みキーの終点を元に戻す
                                                next_bf.complement[R_x2_idxs[0]] = next_bf.complement[R_x2_idxs[1]] = next_bf.complement[R_x2_idxs[2]] = next_bf.complement[R_x2_idxs[3]] = next_bf.org_complement[R_x2_idxs[3]]
                                                next_bf.complement[R_y2_idxs[0]] = next_bf.complement[R_y2_idxs[1]] = next_bf.complement[R_y2_idxs[2]] = next_bf.complement[R_y2_idxs[3]] = next_bf.org_complement[R_y2_idxs[3]]                                    
                                            else:
                                                if len(next_added_bfs) > 0:
                                                    # 追加キーが無効で、後がある場合
                                                    if al.name == "左ひじ":
                                                        logger.info("[F]追加キーが無効で、後がある場合: %s, b: %s, p: %s, n: %s", now_bf.frame, al.name, prev_bf.frame, next_bf.frame )
                                                    c_now_bf = next_added_bfs[0]
                                                else:
                                                    # 追加キーが無効で後がない場合
                                                    if al.name == "左ひじ":
                                                        logger.info("[G]追加キーが無効で後がない場合: %s, b: %s, p: %s, n: %s", now_bf.frame, al.name, prev_bf.frame, next_bf.frame )
                                                    pass

                                    if c_now_bf:
                                        # 現在キーが設定されている場合、補間曲線再計算

                                        # 補間曲線を計算する場合、以前の補間曲線から分割する
                                        next_x1v = next_bf.org_complement[R_x1_idxs[3]]
                                        next_y1v = next_bf.org_complement[R_y1_idxs[3]]
                                        next_x2v = next_bf.org_complement[R_x2_idxs[3]]
                                        next_y2v = next_bf.org_complement[R_y2_idxs[3]]
                                        
                                        # ベジェ曲線を分割して新しい制御点を求める
                                        before_bz, after_bz = calc_bezier_split(next_x1v, next_y1v, next_x2v, next_y2v, prev_bf.frame, next_bf.frame, c_now_bf.frame, al.name)

                                        # 分割（今回キー）の始点は、前半のB
                                        c_now_bf.complement[R_x1_idxs[0]] = c_now_bf.complement[R_x1_idxs[1]] = c_now_bf.complement[R_x1_idxs[2]] = c_now_bf.complement[R_x1_idxs[3]] = int(before_bz[1].x())
                                        c_now_bf.complement[R_y1_idxs[0]] = c_now_bf.complement[R_y1_idxs[1]] = c_now_bf.complement[R_y1_idxs[2]] = c_now_bf.complement[R_y1_idxs[3]] = int(before_bz[1].y())

                                        # 分割（今回キー）の終点は、後半のC
                                        c_now_bf.complement[R_x2_idxs[0]] = c_now_bf.complement[R_x2_idxs[1]] = c_now_bf.complement[R_x2_idxs[2]] = c_now_bf.complement[R_x2_idxs[3]] = int(before_bz[2].x())
                                        c_now_bf.complement[R_y2_idxs[0]] = c_now_bf.complement[R_y2_idxs[1]] = c_now_bf.complement[R_y2_idxs[2]] = c_now_bf.complement[R_y2_idxs[3]] = int(before_bz[2].y())

                                        # 次回読み込みキーの始点は、後半のB
                                        next_bf.complement[R_x1_idxs[0]] = next_bf.complement[R_x1_idxs[1]] = next_bf.complement[R_x1_idxs[2]] = next_bf.complement[R_x1_idxs[3]] = int(after_bz[1].x())
                                        next_bf.complement[R_y1_idxs[0]] = next_bf.complement[R_y1_idxs[1]] = next_bf.complement[R_y1_idxs[2]] = next_bf.complement[R_y1_idxs[3]] = int(after_bz[1].y())

                                        # 次回読み込みキーの終点は、後半のC
                                        next_bf.complement[R_x2_idxs[0]] = next_bf.complement[R_x2_idxs[1]] = next_bf.complement[R_x2_idxs[2]] = next_bf.complement[R_x2_idxs[3]] = int(after_bz[2].x())
                                        next_bf.complement[R_y2_idxs[0]] = next_bf.complement[R_y2_idxs[1]] = next_bf.complement[R_y2_idxs[2]] = next_bf.complement[R_y2_idxs[3]] = int(after_bz[2].y())

                        print("腕合わせ事後調整 b: %s" % al.name)

                                    


    # モーフ置換
    if len(vmd_choice_values) > 0 and len(rep_choice_values) > 0 and len(rep_rate_values) > 0 and len(vmd_choice_values) == len(rep_choice_values) == len(rep_rate_values):
        # VMDのオリジナルモーフと変換後のモーフをまとめてまわす
        for vcv, rcv, rcr in zip(vmd_choice_values, rep_choice_values, rep_rate_values):
            # VMDの該当キーがある場合
            if vcv in motion.morphs.keys():
                print("モーフ置換 %s → %s (%s)" % (vcv, rcv, rcr))
                # Shift-JISでエンコード
                rcv_encode = rcv.encode('shift-jis')
                # そのキーの名前は全部変換後のモーフ名とする
                for morph in motion.morphs[vcv]:
                    morph.name = rcv_encode
                    # モーフの大きさを補正する
                    morph.ratio *= rcr

    if motion.camera_cnt > 0:
        print("カメラ調整未対応")

    # ディクショナリ型の疑似二次元配列から、一次元配列に変換
    bone_frames = []
    for k,v in motion.frames.items():
        for bf in v:
            # if bf.frame == 605:
            #     logger.debug("check: %s, %s, %s, %s, %s, %s", k, bf.name, bf.frame, bf.key, bf.position, bf.rotation)

            if bf.key == True:
                # logger.debug("regist: %s, %s, %s, %s, %s", k, bf.name, bf.frame, bf.position, bf.rotation)
                bone_frames.append(bf)
    
    morph_frames = []
    for k,v in motion.morphs.items():
        for mf in v:
            # logger.debug("k: %s, mf: %s, %s", k, mf.frame, mf.ratio)
            morph_frames.append(mf)

    logger.debug("bone_frames: %s", len(bone_frames))
    logger.debug("morph_frames: %s", len(morph_frames))
    logger.debug("motion.cameras: %s", len(motion.cameras))

    writer = VmdWriter()
    writer.write_vmd_file(output_vmd_path, replace_model.name, bone_frames, morph_frames, motion.cameras, motion.lights, motion.shadows, motion.showiks)

    
    if is_hand_ik_error_outputed:
        print("■■■■■■■■■■■■■■■■■")
        print("■　サイジングに失敗している箇所があります。")
        print("■　ログ: %s" % error_path)
        print("■■■■■■■■■■■■■■■■■")
        print("")
    print("■■■■■■■■■■■■■■■■■")
    print("■　変換出力完了: %s" % output_vmd_path)
    print("■■■■■■■■■■■■■■■■■")

# 手首から指３までで最も離れている関節の距離
def calc_farer_finger_length(finger_global_3ds, all_finger_indexes, direction):
    # 手首の位置
    wrist_pos = finger_global_3ds[len(finger_global_3ds) - all_finger_indexes[direction]["手首"] - 1]
    # 最も離れている指の位置（初期値は手首）
    farer_finger_pos = wrist_pos

    for n in range(len(finger_global_3ds) - all_finger_indexes[direction]["手首"] - 1, len(finger_global_3ds)):
        # 手首から指までの位置情報
        # logger.debug("n: %s, pos: %s", n, finger_global_3ds[n])
        
        if (wrist_pos - finger_global_3ds[n]).length() > (wrist_pos - farer_finger_pos).length():
            # 手首から指３までの距離が、これまでの最長距離より長い場合、保持
            farer_finger_pos = finger_global_3ds[n]
    
    # 最終的に最も遠い関節との距離を返す
    return (wrist_pos - farer_finger_pos).length()

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

# IK計算
# https://mukai-lab.org/content/CcdParticleInverseKinematics.pdf
def calc_arm_IK2FK(target_pos, model, joint_links, all_joint_links, direction, frames, bf, prev_bf, maxc=10):
    local_target_pos = QVector3D()
    local_effector_pos = QVector3D()

    logger.debug("model: %s", model.name)

    for idx in range(maxc):   
        for eidx, effector in enumerate(joint_links):
            # if idx == 3 and eidx == 1:
            #     return

            logger.debug("idx: %s, eidx: %s, effector: %s ----------------------------------", idx, eidx, effector.name)

            if eidx == len(joint_links) - 1:
                # 一番親は計算外
                break

            # 末端からのINDEX保持
            for afli, afl in enumerate(all_joint_links):
                logger.debug("afli: %s, afl: %s, joint: %s", afli, afl.name, joint_links[0].name)
                if afl.name == joint_links[0].name:
                    # エフェクターのインデックス
                    effector_idx = afli
                    # logger.debug("afli: %s, eidx: %s, joint_links[eidx].name: %s", afli, eidx, joint_links[eidx].name)
                if afl.name == joint_links[eidx+1].name:
                    # ジョイントのインデックス
                    joint_idx = afli

            # logger.debug("effector_idx: %s, joint_idx: %s, target_pos: %s", effector_idx, joint_idx, target_pos)

            # 腕関節のグローバル位置と局所座標系
            matrixs_global_reversed, global_3d_reversed = calc_arm_matrixs(model, all_joint_links, direction, frames, bf)
            
            for k, v in zip(all_joint_links, global_3d_reversed):
                logger.debug("**GROBAL %s pos: %s", k.name, v)
            
            # ジョイント(親)
            joint_name = all_joint_links[joint_idx].name
            joint = None
            if joint_name in frames:
                for jidx, jbf in enumerate(frames[joint_name]):
                    if jbf.frame == bf.frame:
                        # logger.debug("補間不要 bf.frame: %s %s", bf.frame, joint_name)
                        # 既存の場合は、それを選ぶ
                        joint = frames[joint_name][jidx]
                        # # 登録対象
                        # joint.key = True
                        break
                        
            if joint == None:
                # ない場合は、補間曲線込みで生成
                joint = calc_bone_by_complement(frames, joint_name, bf.frame)
                if joint_name in frames:
                    for jidx, jbf in enumerate(frames[joint_name]):
                        # logger.debug("補間チェック: jbf: %s, joint: %s", jbf.frame, joint.frame)
                        if jbf.frame > joint.frame:
                            # logger.debug("要補間 bf.frame: %s %s, jidx: %s, jbf: %s, jf: %s", bf.frame, joint_name, jidx, jbf.frame, joint.frame)
                            # # 現時点では登録対象としない
                            # joint.key = False
                            # フレームを越えたトコで、その直前に挿入
                            frames[joint_name].insert( jidx, joint )
                            break

                    for jidx, jbf in enumerate(frames[joint_name]):
                        # logger.debug("補間後: jbf: %s, joint: %s", jbf.frame, joint.frame)
                        if jbf.frame == joint.frame:
                            break
                else:
                    frames[joint_name] = []
                    frames[joint_name].append(joint)
                
            # エフェクタのグローバル位置
            global_effector_pos = global_3d_reversed[effector_idx]
            # 注目ノードのグローバル位置
            global_joint_pos = global_3d_reversed[joint_idx]
            
            logger.debug("%s %s: global_effector_pos: %s", effector_idx, all_joint_links[effector_idx].name, global_effector_pos)
            logger.debug("%s %s: global_joint_pos: %s", effector_idx, all_joint_links[joint_idx].name, global_joint_pos)
            
            # ワールド座標系から注目ノードの局所座標系への変換
            inv_coord = matrixs_global_reversed[joint_idx].inverted()[0]
            
            logger.debug("%s %s: inv_coord:  %s", joint_idx, all_joint_links[joint_idx].name, inv_coord)

            # 注目ノードを起点とした、エフェクタのローカル位置
            local_effector_pos = inv_coord * global_effector_pos
            local_target_pos = inv_coord * target_pos
            
            logger.debug("%s %s: local_effector_pos:  %s", effector_idx, all_joint_links[effector_idx].name, local_effector_pos)
            logger.debug("%s %s: local_target_pos: %s", effector_idx, all_joint_links[effector_idx].name, local_target_pos)

            #  (1) 基準関節→エフェクタ位置への方向ベクトル
            basis2_effector = local_effector_pos.normalized()
            #  (2) 基準関節→目標位置への方向ベクトル
            basis2_target = local_target_pos.normalized()

            logger.debug("%s %s: basis2_effector: %s", effector_idx, all_joint_links[effector_idx].name, basis2_effector)
            logger.debug("%s %s: basis2_target: %s", effector_idx, all_joint_links[effector_idx].name, basis2_target)
            
            # ベクトル (1) を (2) に一致させるための最短回転量（Axis-Angle）
            # 回転角
            rotation_dot_product = QVector3D.dotProduct(basis2_effector, basis2_target)
            rotation_dot_product = 1 if rotation_dot_product > 1 else rotation_dot_product
            rotation_dot_product = 0 if rotation_dot_product < 0 else rotation_dot_product
            rotation_angle = acos(rotation_dot_product)
            
            logger.debug("%s %s: rotation_angle: %s", joint_idx, all_joint_links[joint_idx].name, rotation_angle)

            if abs(rotation_angle) > 0.0001:
                # 一定角度以上の場合
                # 回転軸
                rotation_axis = QVector3D.crossProduct(basis2_effector, basis2_target)
                if bf.frame == 390:
                    logger.debug("[B-1]joint.name: %s, axis: %s", joint.format_name, rotation_axis)

                rotation_axis.normalize()
                rotation_degree = degrees(rotation_angle)
                logger.debug("[B-2]joint.name: %s, axis: %s", joint.format_name, rotation_axis)

                # 関節回転量の補正
                correct_qq = QQuaternion.fromAxisAndAngle(rotation_axis, rotation_degree)
                logger.debug("f: %s, joint: %s, correct_qq: %s", bf.frame, joint.format_name, correct_qq.toEulerAngles())

                # エフェクタのローカル軸
                logger.debug("joint: %s, joint before: %s", all_joint_links[joint_idx].name, joint.rotation.toEulerAngles())
                logger.debug("joint: %s, correct_qq: %s", all_joint_links[joint_idx].name, correct_qq.toEulerAngles())

                joint.rotation = correct_qq * joint.rotation

                logger.debug("joint: %s, joint after: %s", joint.format_name, joint.rotation.toEulerAngles())

                if bf.frame == 390:
                    logger.debug("[A]joint.name: %s, rotation: %s, correct_qq: %s", joint.format_name, joint.rotation.toEulerAngles(), correct_qq.toEulerAngles())
            else:
                logger.debug("[X]回転なし: %s %s", joint.format_name, rotation_angle)
            
        logger.debug("IK: sq: %s, local_effector_pos: %s, local_target_pos: %s", (local_effector_pos - local_target_pos).lengthSquared(), local_effector_pos, local_target_pos)
        if (local_effector_pos - local_target_pos).lengthSquared() < 0.0001:
            logger.debug("IK break: sq: %s, local_effector_pos: %s, local_target_pos: %s", (local_effector_pos - local_target_pos).lengthSquared(), local_effector_pos, local_target_pos)
            return

# 行列とグローバル位置を反転させて返す（末端が0）
def calc_arm_matrixs(model, all_wrist_links, direction, frames, bf):
    # 行列生成(センター起点)
    _, _, _, org_matrixs, org_global_3ds = create_matrix_global(model, all_wrist_links, frames, bf)

    # 該当ボーンの局所座標系変換
    matrixs = [QMatrix4x4() for i in range(len(all_wrist_links))]
    matrixs_global_reversed = [QMatrix4x4() for i in range(len(all_wrist_links))]  

    # グローバル座標
    for n, (v, l) in enumerate(zip(org_matrixs, reversed(all_wrist_links))):
        for m in range(n):
            if m == 0:
                # 最初は行列
                matrixs[n] = copy.deepcopy(org_matrixs[0])
            else:
                # 2番目以降は行列をかける
                matrixs[n] *= copy.deepcopy(org_matrixs[m])
        
        # ローカル軸が設定されていない場合、設定
        local_x_matrix = QMatrix4x4()
        if l.local_x_vector == QVector3D() and l.name in ["左肩", "右肩"]:
            local_axis = all_wrist_links[len(all_wrist_links) - n].position - l.position
            direction_x = -1 if direction == "左" else 1
            local_axis_qq = QQuaternion.rotationTo(QVector3D(direction_x, 0, 0), local_axis)
            # logger.debug("l.name: %s -> %s, %s", all_wrist_links[len(all_wrist_links) - n - 1].name, all_wrist_links[len(all_wrist_links) - n].name, local_axis_qq.toEulerAngles())
            local_x_matrix.rotate(local_axis_qq)
        
        matrixs[n] *= local_x_matrix

    # 末端からとして収め直す
    for n, m in enumerate(reversed(matrixs)):
        # グローバル座標行列
        matrixs_global_reversed[n] = m

    # グローバル座標(ルート反転)
    global_3ds_reversed = [QVector3D() for i in range(len(org_global_3ds))]
        
    for n, g in enumerate(reversed(org_global_3ds)):
        global_3ds_reversed[n] = g
    
    return matrixs_global_reversed, global_3ds_reversed


# 指ジョイントリスト生成
def create_finger_links(model, links, direction):

    # 関節リストを末端から生成する
    finger_links = []

    finger_links.append(get_bone_in_links_4_joint(model, links, direction, "人指３", "人指３"))

    finger_links.append(get_bone_in_links_4_joint(model, links, direction, "手首", "人指３"))
    
    return finger_links
    

# 腕ジョイントリスト生成
def create_arm_links(model, links, direction):
    
    # 関節リストを末端から生成する
    arm_links = []
    
    # if "{0}人指１".format(direction) in model.bones:
    #     arm_links.append(model.bones["{0}人指１".format(direction)])

    arm_links.append(get_bone_in_links_4_joint(model, links, direction, "手首", "手首"))
    
    # if "{0}手捩".format(direction) in model.bones:
    #     arm_links.append(model.bones["{0}手捩".format(direction)])

    arm_links.append(get_bone_in_links_4_joint(model, links, direction, "ひじ", "手首"))
    
    # if "{0}腕捩".format(direction) in model.bones:
    #     arm_links.append(model.bones["{0}腕捩".format(direction)])

    arm_links.append(get_bone_in_links_4_joint(model, links, direction, "腕", "手首"))
    # arm_links.append(get_bone_in_links_4_joint(model, links, direction, "肩", "手首"))
    
    # logger.debug([x.name for x in arm_links])

    return arm_links

# ジョイント用：リンクからボーン情報を取得して返す
def get_bone_in_links_4_joint(model, links, direction, bone_type_name, start_bone_type_name):
    target_bone_name = "{0}{1}".format(direction, bone_type_name)

    for l in links[direction]:
        # logger.debug("l: %s, target_bone_name:%s", l, target_bone_name)
        if l.name == target_bone_name:
            # ちゃんとリンクの中にボーンがあれば、それを返す
            return model.bones[target_bone_name]

    # リストの中に対象ボーンがない場合、エラー
    raise SizingException("ジョイントリストに{0}が登録できません。\n{1}からセンターに向けての親ボーンの繋がりの中に{0}が含まれていません。\nボーンリンク: {2}".format(target_bone_name, "{0}{1}".format(direction, start_bone_type_name), [ x.name for x in links[direction]]))

# 手の調整
def adjust_by_hand(replace_model, direction, wrist_links, frames, bf, upper_vertex_pos, cnt=0):
    # logger.debug("adjust_by_hand: %s, %s ------------------", cnt, bf.frame )

    # 手の位置
    upper_pos, elbow_pos, finger_pos = calc_hand_pos(replace_model, wrist_links, frames, bf)
    # logger.debug("upper_pos: %s", upper_pos)
    # logger.debug("elbow_pos: %s", elbow_pos)
    # logger.debug("finger_pos: %s", finger_pos)

    if is_inner_upper(upper_pos, elbow_pos, finger_pos, replace_model, upper_vertex_pos, direction, bf) == False:
        logger.debug("接触無し frame: %s, finger: %s", bf.frame, finger_pos)
        return

    # 腕調整
    adjust_by_arm_bone(replace_model, direction, wrist_links, frames, bf, upper_vertex_pos, "{0}腕".format(direction))
    if cnt % 3 == 0:
        # ひじ調整
        adjust_by_elbow_bone(replace_model, direction, wrist_links, frames, bf, upper_vertex_pos, "{0}ひじ".format(direction))

    if cnt < 10:
        # 調整してもまだ頭の中に入っていたら、自分を再呼び出し
        return adjust_by_hand(replace_model, direction, wrist_links, frames, bf, upper_vertex_pos, cnt+1)
    else:
        # 10回呼び出してもダメならその時点のを返す
        print("接触解消失敗 frame: %s, finger: %s" % (bf.frame, finger_pos))
        return

def adjust_by_arm_bone(replace_model, direction, wrist_links, frames, bf, upper_vertex_pos, bone_name):
    # 調整値
    av = 0.9

    # ボーン -------------
    bone_idx, _ = get_prev_bf(frames, bone_name, bf.frame)

    # 全体を減らす
    rot = frames[bone_name][bone_idx].rotation
    frames[bone_name][bone_idx].rotation.setX( rot.x() * av )
    frames[bone_name][bone_idx].rotation.setY( rot.y() * av )
    frames[bone_name][bone_idx].rotation.setZ( rot.z() * av )
    frames[bone_name][bone_idx].rotation.normalize()

    upper_pos, elbow_pos, finger_pos = calc_hand_pos(replace_model, wrist_links, frames, bf)
    if is_inner_upper(upper_pos, elbow_pos, finger_pos, replace_model, upper_vertex_pos, direction, bf) == False:
        print("接触解消-%s frame: %s, finger: %s" % (bone_name, bf.frame, finger_pos))
        return

def adjust_by_elbow_bone(replace_model, direction, wrist_links, frames, bf, upper_vertex_pos, bone_name):
    # 調整値
    av = 0.9

    # ボーン -------------
    bone_idx, _ = get_prev_bf(frames, bone_name, bf.frame)

    # 全体を減らす
    rot = frames[bone_name][bone_idx].rotation
    frames[bone_name][bone_idx].rotation.setX( rot.x() * av )
    frames[bone_name][bone_idx].rotation.setY( rot.y() * av )
    frames[bone_name][bone_idx].rotation.setZ( rot.z() * av )
    frames[bone_name][bone_idx].rotation.normalize()

    upper_pos, elbow_pos, finger_pos = calc_hand_pos(replace_model, wrist_links, frames, bf)
    if is_inner_upper(upper_pos, elbow_pos, finger_pos, replace_model, upper_vertex_pos, direction, bf) == False:
        print("接触解消-%s frame: %s, finger: %s" % (bone_name, bf.frame, finger_pos))
        return

# 指定されたフレームより前のキーを返す
def get_prev_bf(frames, bone_name, frameno):
    for bidx, bf in enumerate(frames[bone_name]):
        if bf.frame >= frameno:
            # 指定されたフレーム以降の一つ前で、前のキーを取る
            return bidx, frames[bone_name][bidx - 1]

    # 最後まで取れなければ、最終項目
    return len(frames[bone_name]) - 1, frames[bone_name][-1]

# 頭の中に入っているか
def is_inner_upper(upper_pos, elbow_pos, finger_pos, replace_model, upper_vertex_pos, direction, bf):

    logger.debug("is_inner_upper sh: %s, el: %s, fi: %s", upper_pos.y(), elbow_pos.y(), finger_pos.y() )

    # if upper_pos.y() > finger_pos.y():
    #     # 上半身Yより指が下ならとりあえずFalse
    #     return False
    
    # 小数点第一で丸めた範囲内でチェック
    round_finger_pos = round(finger_pos.y(), 1)

    for rfp in [round_finger_pos - 0.2, round_finger_pos - 0.1, round_finger_pos, round_finger_pos + 0.1, round_finger_pos + 0.2]:
        if rfp in upper_vertex_pos.keys():

            # if direction == "左" and bf.frame == 0:
            #     logger.debug("指Z: d: %s, rfp:%s, vmin: %s, vmax: %s, wf: %s:", direction, rfp, upper_vertex_pos[rfp]["min"].z(), upper_vertex_pos[rfp]["max"].z(), finger_pos)

            if upper_vertex_pos[rfp]["min"].z() - 0.1 <= finger_pos.z() <= upper_vertex_pos[rfp]["max"].z() + 0.1:                
                for uv in upper_vertex_pos[rfp]["values"]:
                    
                    # if direction == "左" and bf.frame == 0:
                    #     logger.debug("指Z接触: d: %s, u: %s, wf: %s", direction, uv.x(), finger_pos.x())

                    if direction == "左" and finger_pos.x() <= uv.x() + 0.2:
                        logger.debug("左頭-指接触: v: %s, f: %s", uv, finger_pos)
                        # 左手で上半身より内側ならTrue
                        return True
                    if direction == "右" and uv.x() - 0.2 <= finger_pos.x():
                        # 右手で上半身より内側ならTrue
                        logger.debug("右頭-指接触: v: %s, wf: %s", uv, finger_pos)
                        return True

                    # ひじを除外対象にするとガクッとなるので保留。
                    # if direction == "左" and elbow_pos.x() <= uv.x():
                    #     logger.debug("左頭-ひじ接触: v: %s, f: %s", uv, elbow_pos)
                    #     # 左手で上半身より内側ならTrue
                    #     return True
                    # if direction == "右" and uv.x() <= elbow_pos.x():
                    #     # 右手で上半身より内側ならTrue
                    #     logger.debug("右頭-ひじ接触: v: %s, wf: %s", uv, elbow_pos)
                    #     return True

                # if bf.frame == 338:
                #     logger.debug("指接触なし: d: %s, v: %s, wf: %s", direction, uv, finger_pos)

    # どれもヒットしなければFalse
    return False            


# 人指の位置の計算
def calc_hand_pos(model, wrist_links, frames, bf):

    # グローバル行列算出
    _, _, _, _, global_3ds = create_matrix_global(model, wrist_links, frames, bf)

    upper_pos = QVector3D()
    elbow_pos = QVector3D()
    finger_pos = QVector3D()

    logger.debug("--------------")
    for lidx, lbone in enumerate(reversed(wrist_links)):
        logger.debug("frame: %s: lidx: %s, %s, %s", bf.frame, lidx, lbone.name, global_3ds[lidx])

        if "上半身" == lbone.name:
            # 上半身固定
            upper_pos = global_3ds[lidx]

        if "ひじ" in lbone.name:
            elbow_pos = global_3ds[lidx]

        if lidx == len(wrist_links) - 1:
            # 先端を指とする
            finger_pos = global_3ds[lidx]

    return upper_pos, elbow_pos, finger_pos


# 頭の頂点の位置の計算
def calc_upper_vertex(upper_vertices, model, head_links, frames, bf):
    # キー：頂点Y位置小数点第一位まるめ
    upper_vertex_pos = {}

    # グローバル行列算出
    _, _, _, matrixs = create_matrix(model, head_links, frames, bf)

    # 該当ボーンのグローバル行列まで求める
    upper_matrixes = [QMatrix4x4() for i in range(len(head_links))]

    for n in range(len(matrixs)):
        for m in range(n+1):
            if n == 0:
                # 最初は行列そのもの
                upper_matrixes[n] = copy.deepcopy(matrixs[0])
            else:
                # 2番目以降は行列をかける
                upper_matrixes[n] *= copy.deepcopy(matrixs[m])

            # logger.debug("**u_matrixes[%s]: %s %s -> %s", n, m, matrixs[m], upper_matrixes[n])
        
        # logger.debug("upper_matrixes[%s]: %s", n, upper_matrixes[n])

    # 該当リンクボーンのリンクINDEX取得
    head_links_indexes = {}
    for lidx, l in enumerate(reversed(head_links)):
        head_links_indexes[l.index] = lidx

    # 上半身の頂点位置
    for uv in upper_vertices:
        # 頂点が乗っているウェイトボーン情報取得
        deform_bone = model.bones[model.bone_indexes[uv.deform.index0]]

        # 頂点初期位置
        uv_diff = uv.position - deform_bone.position

        # 上半身の頂点の位置を算出する
        upper_pos = upper_matrixes[head_links_indexes[deform_bone.index]] * QVector4D(uv_diff, 1)
        # logger.debug("upper_matrixes0 : %s, upper_pos: %s", upper_matrixes[0], upper_pos)
        # logger.debug("upper_matrixes1 : %s, upper_pos: %s", upper_matrixes[1], upper_pos)

        # 3Dに変換
        uv_pos = upper_pos.toVector3D()
        uv_round = round(uv_pos.y(), 1)
        # logger.debug("uv_pos.y: %s -> %s: 0:%s, -1:%s, 1:%s", uv_pos.y(), uv_round, round(uv_pos.y(), 0), round(uv_pos.y(), -1), round(uv_pos.y(), 1))
        if uv_round not in upper_vertex_pos.keys():
            upper_vertex_pos[uv_round] = {}
            # 最小値
            upper_vertex_pos[uv_round]["min"] = QVector3D(99999, 99999, 99999)
            # 最大値
            upper_vertex_pos[uv_round]["max"] = QVector3D(-99999, -99999, -99999)
            # 実値
            upper_vertex_pos[uv_round]["values"] = []

        # if round(uv.position.y(),2) == 8.01:
        #     logger.debug("v: %s %s, uv_pos: %s", uv.index, uv.position, uv_pos)

        if upper_vertex_pos[uv_round]["min"].z() > uv_pos.z():
            # 最小値より小さい場合、上書き
            upper_vertex_pos[uv_round]["min"] = uv_pos

        if upper_vertex_pos[uv_round]["max"].z() < uv_pos.z():
            # 最大値より小さい場合、上書き
            upper_vertex_pos[uv_round]["max"] = uv_pos
        
        # 実値追加
        upper_vertex_pos[uv_round]["values"].append(uv_pos)
    
    # if bf.frame == 0:
    #     for uvkey in upper_vertex_pos.keys():
    #         logger.debug("upper_vertex_pos key: %s, min: %s, max: %s, len: %s", uvkey, upper_vertex_pos[uv_round]["min"], upper_vertex_pos[uv_round]["max"], len(upper_vertex_pos[uvkey]["values"]))

    return upper_vertex_pos

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

def cal_center_z_offset(trace_model, replace_model, bone_name):
    if bone_name in trace_model.bones and bone_name in replace_model.bones and "左足首" in trace_model.bones and "左足首" in replace_model.bones and "左足" in trace_model.bones and "左足" in replace_model.bones and "左つま先ＩＫ" in trace_model.bones and "左つま先ＩＫ" in replace_model.bones:
        # 移植元にも移植先にも対象ボーンがある場合
        # 作成元左足首のZ位置
        trace_ankle_z = trace_model.bones["左足首"].position.z()
        # 作成元左足のZ位置
        trace_leg_z = trace_model.bones["左足"].position.z()
        # 作成元つま先IKのZ位置
        trace_toe_z = trace_model.bones["左つま先ＩＫ"].position.z()

        # トレース変換先左足首のZ位置
        replace_ankle_z = replace_model.bones["左足首"].position.z()
        # トレース変換先左足のZ位置
        replace_leg_z = replace_model.bones["左足"].position.z()
        # トレース変換先つま先IKのZ位置
        replace_toe_z = replace_model.bones["左つま先ＩＫ"].position.z()

        # 作成元の足の長さ
        trace_leg_zlength = trace_ankle_z - trace_toe_z
        # 作成元の重心
        trace_center_gravity = (trace_leg_z - trace_ankle_z) / (trace_toe_z - trace_ankle_z)
        logger.debug("trace_center_gravity %s, trace_leg_zlength: %s", trace_center_gravity, trace_leg_zlength)
        
        # トレース変換先の足の長さ
        replace_leg_zlength = replace_ankle_z - replace_toe_z
        # トレース変換先の重心
        replace_center_gravity = (replace_leg_z - replace_ankle_z) / (replace_toe_z - replace_ankle_z)
        logger.debug("replace_center_gravity %s, replace_leg_zlength: %s", replace_center_gravity, replace_leg_zlength)
        
        replace_model.bones[bone_name].offset_z = (replace_center_gravity - trace_center_gravity) * ( replace_leg_zlength / trace_leg_zlength )

        print("Zオフセット: %s: %s" % ( bone_name, replace_model.bones[bone_name].offset_z))
    else:
        print("Zオフセットなし: %s: %s" % ( bone_name, replace_model.bones[bone_name].offset_z))

def calc_leg_ik_ratio(trace_model, replace_model):
    if "左足" in trace_model.bones and "左足" in replace_model.bones and "左ひざ" in trace_model.bones and "左ひざ" in replace_model.bones and "左足首" in trace_model.bones and "左足首" in replace_model.bones and "センター" in trace_model.bones and "センター" in replace_model.bones:
        # XZ比率(足の長さ)
        replace_leg_length = ( (replace_model.bones["左足首"].position - replace_model.bones["左ひざ"].position) + (replace_model.bones["左ひざ"].position - replace_model.bones["左足"].position) ).length()
        trace_leg_length = ( (trace_model.bones["左足首"].position - trace_model.bones["左ひざ"].position) + (trace_model.bones["左ひざ"].position - trace_model.bones["左足"].position) ).length()
        logger.debug("xz_ratio replace_leg_length: %s, trace_leg_length: %s", replace_leg_length, trace_leg_length)
        xz_ratio = 1 if trace_leg_length == 0 else ( replace_leg_length / trace_leg_length )

        # Y比率(股下のY差)
        replace_leg_length = (replace_model.bones["左足首"].position - replace_model.bones["左足"].position).y()
        trace_leg_length = (trace_model.bones["左足首"].position - trace_model.bones["左足"].position).y()        
        logger.debug("y_ratio replace_leg_length: %s, trace_leg_length: %s", replace_leg_length, trace_leg_length)
        y_ratio = 1 if trace_leg_length == 0 else ( replace_leg_length / trace_leg_length )

        print("足の長さの比率: xz: %s, y: %s" % (xz_ratio, y_ratio))

        # # 左足のスタンス距離比
        # l_stance = ((replace_model.bones["左足ＩＫ"].position - replace_model.bones["センター"].position).x()) - ((trace_model.bones["左足ＩＫ"].position - trace_model.bones["センター"].position).x() * xz_ratio)
        # r_stance = ((replace_model.bones["右足ＩＫ"].position - replace_model.bones["センター"].position).x()) - ((trace_model.bones["右足ＩＫ"].position - trace_model.bones["センター"].position).x() * xz_ratio)

        # logger.debug("replace: %s", (replace_model.bones["左足ＩＫ"].position - replace_model.bones["センター"].position).x())
        # logger.debug("trace: %s", (trace_model.bones["左足ＩＫ"].position - trace_model.bones["センター"].position).x())
        # logger.debug("trace2: %s", ((trace_model.bones["左足ＩＫ"].position - trace_model.bones["センター"].position).x() * xz_ratio))

        # # print("足のスタンス補正値: l: %s, r: %s" % (l_stance, r_stance))

        return xz_ratio, y_ratio, {"左": 1, "右": 1}

    print("足、ひざ、足首、センターのいずれかのボーンが不足しているため、足の長さの比率が測れませんでした")
    return 1, 1, {"左": 1, "右": 1}


def adjust_center(trace_model, replace_model, bone_name):
    if bone_name in trace_model.bones and bone_name in replace_model.bones and "左足" in trace_model.bones and "左足" in replace_model.bones:
        # 移植元にも移植先にも対象ボーンがある場合
        # 左足付け根のY位置
        leg_y = trace_model.bones["左足"].position.y()
        # センター（もしくはグルーブ）のY位置
        center_y = trace_model.bones[bone_name].position.y()
        # 足のどの辺りにセンターがあるか判定
        ratio_y = center_y / leg_y
        
        # 作成元と同じ比率の位置にセンターを置く
        replace_model.bones[bone_name].len = replace_model.bones["左足"].position.y() * ratio_y

        # logger.debug("len: %s, center_y: %s, leg_y: %s, ratio_y:%s, pos: %s", replace_model.bones[bone_name].len, center_y, leg_y, ratio_y, replace_model.bones["下半身"].position.y())

def copy_root_parent(model):
    if "全ての親" in model.bones.keys() and "センター" in model.bones.keys():
        # 全ての親がある場合、センターの長さをコピーする
        logger.debug("全ての親: %s <- %s", model.bones["全ての親"].len, model.bones["センター"].len)
        model.bones["全ての親"].len = model.bones["センター"].len

def compare_length(trace_model, replace_model):
    lengths = {}

    for k, v in replace_model.bones.items():
        # 移植先モデルのボーン構造チェック
        if k in trace_model.bones:
            # 同じ項目が作成元にもある場合
            trace_bone_length = trace_model.bones[k].len
            replace_bone_length = replace_model.bones[k].len

            # print("k: %s, len: %s" % (k, replace_model.bones[k].len) )

            # 0割対策を入れて、倍率取得
            length = 1 if trace_bone_length == 0 else replace_bone_length / trace_bone_length

            # length.setX(length.x() if np.isnan(length.x()) == False and np.isinf(length.x()) == False else 0)
            # length.setY(length.y() if np.isnan(length.y()) == False and np.isinf(length.y()) == False else 0)
            # length.setZ(length.z() if np.isnan(length.z()) == False and np.isinf(length.z()) == False else 0)
            # if k in ["右足ＩＫ親" ,"左足ＩＫ親", "右足ＩＫ" ,"左足ＩＫ", "右つま先ＩＫ" ,"左つま先ＩＫ", "センター", "グルーブ", "全ての親"]:
            #     print("%s, 比率: %s, 生成元の長さ: %s, 変換先の長さ: %s" % (k, length, trace_bone_length, replace_bone_length))

            lengths[k] = length
    
    return lengths

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


def calc_arm_stance(trace_model, all_org_wrist_links, replace_model, all_replace_wrist_links, direction):
    from_bone = ["肩", "腕", "ひじ", "手首"]
    to_bone = ["腕", "ひじ", "手首", "手先"]
    arm_stance_qqs = {}
    for f, t in zip(from_bone, to_bone):
        org_qq = calc_arm_stance_rotation(trace_model, all_org_wrist_links[direction], f, t, direction)
        rep_qq = calc_arm_stance_rotation(replace_model, all_replace_wrist_links[direction], f, t, direction)

        arm_stance_qqs[f] = rep_qq.inverted() * org_qq

        logger.debug("f: %s, org_qq: %s", f, org_qq.toEulerAngles())
        logger.debug("f: %s, rep_qq: %s", f, rep_qq.toEulerAngles())
        logger.debug("d: %s, f: %s, arm_stance_qqs: %s", direction, f, arm_stance_qqs[f].toEulerAngles())

    return arm_stance_qqs

def calc_arm_stance_rotation(model, wrist_links, fbone, tbone, direction):
    from_pos = QVector3D()
    to_pos = QVector3D()
    tail_pos = QVector3D()

    for fk, fv in enumerate(wrist_links):
        if fv.name.endswith(fbone):
            from_pos = fv.position
            if fv.tail_position != QVector3D:
                # 表示先が相対パスの場合、保持
                tail_pos = fv.tail_position
        if fv.name.endswith(tbone):
            to_pos = fv.position
    
    if to_pos == QVector3D() and tail_pos != QVector3D():
        to_pos = tail_pos
        logger.debug("to_pos 置換: %s", to_pos)

    from_qq = QQuaternion()
    if from_pos != QVector3D and to_pos != QVector3D:
        logger.debug("from_pos: %s", from_pos)        
        logger.debug("to_pos: %s", to_pos)        

        to_pos = to_pos - from_pos
        to_pos.normalize()
        logger.debug("to_pos: %s", to_pos)        

        # 水平からTOボーンまでの回転量
        direction_x = 1 if direction == "左" else -1
        from_qq = QQuaternion.rotationTo(QVector3D(direction_x, 0, 0), to_pos)
        logger.debug("[z] d: %s, fbone: %s, from_qq: %s", direction, fbone, from_qq.toEulerAngles())

    return from_qq

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

if __name__=="__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--vmd_path', dest='vmd_path', help='input vmd', type=str)
    parser.add_argument('--trace_pmx_path', dest='trace_pmx_path', help='input trace pmx', type=str)
    parser.add_argument('--replace_pmx_path', dest='replace_pmx_path', help='replace trace pmx', type=str)
    parser.add_argument('--avoidance', dest='avoidance', help='upper hand avoidance', type=int)
    parser.add_argument('--hand_ik', dest='hand_ik', help='hand ik', type=int)
    parser.add_argument('--hand_distance', dest='hand_distance', help='hand distance', type=float)
    parser.add_argument('--verbose', dest='verbose', help='verbose', type=int)
    args = parser.parse_args()

    logger.setLevel(level[args.verbose])

    try:
        # VMD読み込み
        motion = VmdReader().read_vmd_file(args.vmd_path)

        # 作成元モデル
        logger.info("trace_pmx_path: %s", args.trace_pmx_path)
        org_pmx = PmxReader().read_pmx_file(args.trace_pmx_path)

        # 変換先モデル
        logger.info("replace_pmx_path: %s", args.replace_pmx_path)
        rep_pmx = PmxReader().read_pmx_file(args.replace_pmx_path)

        # 出力ファイルパス
        bone_filename, _ = os.path.splitext(os.path.basename(args.replace_pmx_path))
        output_vmd_path = os.path.join(str(Path(args.vmd_path).resolve().parents[0]), os.path.basename(args.vmd_path).replace(".vmd", "_{1}_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now(), bone_filename)))

        # 接触回避処理
        is_avoidance = True if args.avoidance == 1 else False

        # 腕IKによる位置調整
        is_hand_ik = True if args.hand_ik == 1 else False

        main(motion, org_pmx, rep_pmx, output_vmd_path, is_avoidance, True, is_hand_ik, args.hand_distance, [], [], []) 

    except SizingException as e:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMDサイジング処理が処理できないデータで終了しました。")
        print("■■■■■■■■■■■■■■■■■")
        print("")
        print(e.message)

    except Exception as e:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMDサイジング処理が意図せぬエラーで終了しました。")
        print("■■■■■■■■■■■■■■■■■")

        print(traceback.format_exc())

