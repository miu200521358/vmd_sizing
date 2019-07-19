# -*- coding: utf-8 -*-
# 腕IK処理
# 
import logging
import copy
from math import acos, degrees
from PyQt5.QtGui import QQuaternion, QVector3D, QVector2D, QMatrix4x4, QVector4D

from VmdWriter import VmdWriter, VmdBoneFrame
from VmdReader import VmdReader
from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader
import utils

logger = logging.getLogger("__main__").getChild(__name__)

# file_logger = logging.getLogger("message")
# file_logger.addHandler(logging.FileHandler("test.csv"))

def exec(motion, trace_model, replace_model, is_avoidance, is_hand_ik, hand_distance, org_motion_frames, error_path, error_file_logger):
    is_error_outputed = False

    # -----------------------------------------------------------------
    # 手首位置合わせ処理
    if motion.motion_cnt > 0 and not is_avoidance and is_hand_ik:
        # センターから手首までの位置(トレース先モデル)
        all_rep_wrist_links, _ = replace_model.create_link_2_top_lr("手首")

        # 肩から手首までのリンク生成(トレース先)
        arm_links = {
            "左": create_arm_links(replace_model, all_rep_wrist_links, "左"), 
            "右": create_arm_links(replace_model, all_rep_wrist_links, "右")
        }
        logger.debug("left_arm_links: %s", [ x.name for x in arm_links["左"]])    
        
        # 事前準備
        prepare(motion, arm_links, hand_distance)

        if hand_distance >= 0:
            # 手首位置合わせ処理実行
            is_error_outputed = exec_arm_ik(motion, trace_model, replace_model, hand_distance, org_motion_frames, all_rep_wrist_links, arm_links, error_path, error_file_logger)

            # 補間曲線再設定
            reset_complement(motion, arm_links)

    return not is_error_outputed


# 腕IK調整後始末
def reset_complement(motion, arm_links):
    # 補間曲線を有効なキーだけに揃える
    
    for direction in ["左", "右"]:
        for al in arm_links[direction]:
            for bf_idx, bf in enumerate(motion.frames[al.name]):
                now_bf = motion.frames[al.name][bf_idx]

                if now_bf.key == False or now_bf.read == True or now_bf.split_complement == True:
                    # 現在キーが無効もしくは、読み込みキーか再分割追加キーの場合、処理スルー
                    if 5210 <= now_bf.frame <= 5240:
                        logger.debug("処理スルー: %s, key: %s, read: %s", now_bf.frame, now_bf.key, now_bf.read)
                    continue

                # 前回のキー情報をクリア
                prev_bf = next_bf = None
                
                # 読み込んだ時か補間曲線分割で追加した次のキー
                for nbf_idx in range(bf_idx + 1, len(motion.frames[al.name])):
                    if (motion.frames[al.name][nbf_idx].read == True or motion.frames[al.name][nbf_idx].split_complement == True) and motion.frames[al.name][nbf_idx].frame > now_bf.frame:
                        next_bf = motion.frames[al.name][nbf_idx]
                        break

                # 有効な前のキー
                for pbf_idx in range(bf_idx - 1, -1, -1):
                    if motion.frames[al.name][pbf_idx].key == True and motion.frames[al.name][pbf_idx].frame < now_bf.frame:
                        prev_bf = motion.frames[al.name][pbf_idx]
                        break
                
                if prev_bf and next_bf:
                    # 前後がある場合、補間曲線を分割する
                    next_x1v = next_bf.complement[utils.R_x1_idxs[3]]
                    next_y1v = next_bf.complement[utils.R_y1_idxs[3]]
                    next_x2v = next_bf.complement[utils.R_x2_idxs[3]]
                    next_y2v = next_bf.complement[utils.R_y2_idxs[3]]
                    
                    split_complement(motion, next_x1v, next_y1v, next_x2v, next_y2v, prev_bf, next_bf, now_bf, al, ",")

            print("手首位置合わせ事後調整 b: %s" % al.name)


# 補間曲線を分割する
def split_complement(motion, next_x1v, next_y1v, next_x2v, next_y2v, prev_bf, next_bf, now_bf, al, indent, resplit=True):
    # 区切りキー位置
    before_fill_bf = after_fill_bf = None

    logger.debug("%s,【分割開始】: , %s, prev: %s, now: %s, next: %s, next_x1v: %s, next_y1v: %s, next_x2v: %s, next_y2v: %s", indent, al.name, prev_bf.frame, now_bf.frame, next_bf.frame, next_x1v, next_y1v, next_x2v, next_y2v)
    
    # ベジェ曲線を分割して新しい制御点を求める
    t, x, y, bresult, aresult, before_bz, after_bz = utils.calc_bezier_split(next_x1v, next_y1v, next_x2v, next_y2v, prev_bf.frame, next_bf.frame, now_bf.frame, al.name)

    logger.debug(",%s, next_x1v: %s, next_y1v: %s, next_x2v: %s, next_y2v: %s, start: %s, now: %s, end: %s", indent, next_x1v, next_y1v, next_x2v, next_y2v, prev_bf.frame, now_bf.frame, next_bf.frame)
    logger.debug(",%s, before_bz: %s", indent, before_bz)
    logger.debug(",%s, after_bz: %s", indent, after_bz)

    # 分割（今回キー）の始点は、前半のB
    now_bf.complement[utils.R_x1_idxs[0]] = now_bf.complement[utils.R_x1_idxs[1]] = now_bf.complement[utils.R_x1_idxs[2]] = now_bf.complement[utils.R_x1_idxs[3]] = int(before_bz[1].x())
    now_bf.complement[utils.R_y1_idxs[0]] = now_bf.complement[utils.R_y1_idxs[1]] = now_bf.complement[utils.R_y1_idxs[2]] = now_bf.complement[utils.R_y1_idxs[3]] = int(before_bz[1].y())

    # 分割（今回キー）の終点は、後半のC
    now_bf.complement[utils.R_x2_idxs[0]] = now_bf.complement[utils.R_x2_idxs[1]] = now_bf.complement[utils.R_x2_idxs[2]] = now_bf.complement[utils.R_x2_idxs[3]] = int(before_bz[2].x())
    now_bf.complement[utils.R_y2_idxs[0]] = now_bf.complement[utils.R_y2_idxs[1]] = now_bf.complement[utils.R_y2_idxs[2]] = now_bf.complement[utils.R_y2_idxs[3]] = int(before_bz[2].y())

    # 次回読み込みキーの始点は、後半のB
    next_bf.complement[utils.R_x1_idxs[0]] = next_bf.complement[utils.R_x1_idxs[1]] = next_bf.complement[utils.R_x1_idxs[2]] = next_bf.complement[utils.R_x1_idxs[3]] = int(after_bz[1].x())
    next_bf.complement[utils.R_y1_idxs[0]] = next_bf.complement[utils.R_y1_idxs[1]] = next_bf.complement[utils.R_y1_idxs[2]] = next_bf.complement[utils.R_y1_idxs[3]] = int(after_bz[1].y())

    # 次回読み込みキーの終点は、後半のC
    next_bf.complement[utils.R_x2_idxs[0]] = next_bf.complement[utils.R_x2_idxs[1]] = next_bf.complement[utils.R_x2_idxs[2]] = next_bf.complement[utils.R_x2_idxs[3]] = int(after_bz[2].x())
    next_bf.complement[utils.R_y2_idxs[0]] = next_bf.complement[utils.R_y2_idxs[1]] = next_bf.complement[utils.R_y2_idxs[2]] = next_bf.complement[utils.R_y2_idxs[3]] = int(after_bz[2].y())

    if bresult and aresult:
        logger.info("%s, 【分割成功】: , %s,prev: %s, now: %s, next: %s", indent, al.name, prev_bf.frame, now_bf.frame, next_bf.frame)
        
        return
    else:
        # 分割に失敗している場合、さらに分割する

        if not bresult:
            logger.info("%s, 【分割前半失敗開始】: ,%s, prev: %s, now: %s, next: %s", indent, al.name, prev_bf.frame, now_bf.frame, next_bf.frame)

            # 前半用補間曲線
            next_x1v = now_bf.complement[utils.R_x1_idxs[3]]
            next_y1v = now_bf.complement[utils.R_y1_idxs[3]]
            next_x2v = now_bf.complement[utils.R_x2_idxs[3]]
            next_y2v = now_bf.complement[utils.R_y2_idxs[3]]

            # 前半を区切る位置を求める(t=0.5で曲線を半分に分割する位置)
            now, _ = utils.calc_interpolate_bezier_by_t(next_x1v, next_y1v, next_x2v, next_y2v, prev_bf.frame, now_bf.frame, 0.5)
            logger.info("%s, 【前半】, now: %s", indent, now)

            if now > prev_bf.frame:
                # ちゃんとキーが打てるような状態の場合、前半を再分割
                before_fill_bf = recalc_bone_by_complement(motion, al, now)

            if before_fill_bf:
                # 分割キーが取得できた場合、前半の補間曲線を分割して求めなおす
                split_complement(motion, next_x1v, next_y1v, next_x2v, next_y2v, prev_bf, now_bf, before_fill_bf, al, "{0},".format(indent))
            else:
                # 分割キーが取得できなかった場合、既にキーがあるので、さらに分割する


                # 分割キーが取得できなかった場合、念のため補間曲線を0-127の間に収め直す
                # 分割（今回キー）の始点は、前半のB
                r_x1 = 0 if 0 > before_bz[1].x() else utils.COMPLEMENT_MMD_MAX if utils.COMPLEMENT_MMD_MAX < before_bz[1].x() else int(before_bz[1].x())
                now_bf.complement[utils.R_x1_idxs[0]] = now_bf.complement[utils.R_x1_idxs[1]] = now_bf.complement[utils.R_x1_idxs[2]] = now_bf.complement[utils.R_x1_idxs[3]] = r_x1
                r_y1 = 0 if 0 > before_bz[1].y() else utils.COMPLEMENT_MMD_MAX if utils.COMPLEMENT_MMD_MAX < before_bz[1].y() else int(before_bz[1].y())
                now_bf.complement[utils.R_y1_idxs[0]] = now_bf.complement[utils.R_y1_idxs[1]] = now_bf.complement[utils.R_y1_idxs[2]] = now_bf.complement[utils.R_y1_idxs[3]] = r_y1

                # 分割（今回キー）の終点は、後半のC
                r_x2 = now_bf.complement[utils.R_x2_idxs[3]] = 0 if 0 > before_bz[2].x() else utils.COMPLEMENT_MMD_MAX if utils.COMPLEMENT_MMD_MAX < before_bz[2].x() else int(before_bz[2].x())
                now_bf.complement[utils.R_x2_idxs[0]] = now_bf.complement[utils.R_x2_idxs[1]] = now_bf.complement[utils.R_x2_idxs[2]] = now_bf.complement[utils.R_x2_idxs[3]] = r_x2
                r_y2 = 0 if 0 > before_bz[2].y() else utils.COMPLEMENT_MMD_MAX if utils.COMPLEMENT_MMD_MAX < before_bz[2].y() else int(before_bz[2].y())
                now_bf.complement[utils.R_y2_idxs[0]] = now_bf.complement[utils.R_y2_idxs[1]] = now_bf.complement[utils.R_y2_idxs[2]] = now_bf.complement[utils.R_y2_idxs[3]] = r_y2

                logger.info("%s,前半分割キー取得失敗,R_x1_idxs,%s,R_y1_idxs,%s,R_x2_idxs,%s,R_y2_idxs,%s,before_bz,%s", indent, now_bf.complement[utils.R_x1_idxs[3]], now_bf.complement[utils.R_y1_idxs[3]], now_bf.complement[utils.R_x2_idxs[3]], now_bf.complement[utils.R_x2_idxs[3]],before_bz)

        if not aresult:
            logger.debug("%s, 【分割後半失敗開始】: ,%s, prev: %s, now: %s, next: %s", indent, al.name, prev_bf.frame, now_bf.frame, next_bf.frame)

            # 後半用補間曲線
            next_x1v = next_bf.complement[utils.R_x1_idxs[3]]
            next_y1v = next_bf.complement[utils.R_y1_idxs[3]]
            next_x2v = next_bf.complement[utils.R_x2_idxs[3]]
            next_y2v = next_bf.complement[utils.R_y2_idxs[3]]

            # 後半を区切る位置を求める
            now, _ = utils.calc_interpolate_bezier_by_t(next_x1v, next_y1v, next_x2v, next_y2v, now_bf.frame, next_bf.frame, 0.5)
            logger.info("%s, 【後半】, now: %s", indent, now)

            if now > now_bf.frame:
                # ちゃんとキーが打てるような状態の場合、後半を再分割
                after_fill_bf = recalc_bone_by_complement(motion, al, now)

            if after_fill_bf:
                # 分割キーが取得できた場合、後半の補間曲線を分割して求めなおす
                split_complement(motion, next_x1v, next_y1v, next_x2v, next_y2v, now_bf, next_bf, after_fill_bf, al, "{0},".format(indent))
            else:
                # 分割キーが取得できなかった場合、念のため補間曲線を0-127の間に収め直す

                # 次回読み込みキーの始点は、後半のB
                r_x1 = 0 if 0 > after_bz[1].x() else utils.COMPLEMENT_MMD_MAX if utils.COMPLEMENT_MMD_MAX < after_bz[1].x() else int(after_bz[1].x())
                next_bf.complement[utils.R_x1_idxs[0]] = next_bf.complement[utils.R_x1_idxs[1]] = next_bf.complement[utils.R_x1_idxs[2]] = next_bf.complement[utils.R_x1_idxs[3]] = r_x1
                r_y1 = 0 if 0 > after_bz[1].y() else utils.COMPLEMENT_MMD_MAX if utils.COMPLEMENT_MMD_MAX < after_bz[1].y() else int(after_bz[1].y())
                next_bf.complement[utils.R_y1_idxs[0]] = next_bf.complement[utils.R_y1_idxs[1]] = next_bf.complement[utils.R_y1_idxs[2]] = next_bf.complement[utils.R_y1_idxs[3]] = r_y1

                # 次回読み込みキーの終点は、後半のC
                r_x2 = 0 if 0 > after_bz[2].x() else utils.COMPLEMENT_MMD_MAX if utils.COMPLEMENT_MMD_MAX < after_bz[2].x() else int(after_bz[2].x())
                next_bf.complement[utils.R_x2_idxs[0]] = next_bf.complement[utils.R_x2_idxs[1]] = next_bf.complement[utils.R_x2_idxs[2]] = next_bf.complement[utils.R_x2_idxs[3]] = r_x2
                r_y2 = 0 if 0 > after_bz[2].y() else utils.COMPLEMENT_MMD_MAX if utils.COMPLEMENT_MMD_MAX < after_bz[2].y() else int(after_bz[2].y())
                next_bf.complement[utils.R_y2_idxs[0]] = next_bf.complement[utils.R_y2_idxs[1]] = next_bf.complement[utils.R_y2_idxs[2]] = next_bf.complement[utils.R_y2_idxs[3]] = r_y2

                logger.info("%s,後半分割キー取得失敗,R_x1_idxs,%s,R_y1_idxs,%s,R_x2_idxs,%s,R_y2_idxs,%s,after_bz,%s", indent, next_bf.complement[utils.R_x1_idxs[3]], next_bf.complement[utils.R_y1_idxs[3]], next_bf.complement[utils.R_x2_idxs[3]], next_bf.complement[utils.R_x2_idxs[3]],after_bz)

        logger.info("%s, 【分割失敗終了】: ,%s, prev: %s, now: %s, next: %s", indent, al.name, prev_bf.frame, now_bf.frame, next_bf.frame)
        return
    
    logger.info("%s, 【分割終了】: ,%s, prev: %s, now: %s, next: %s, next_x1v: %s, next_y1v: %s, next_x2v: %s, next_y2v: %s", indent, al.name, prev_bf.frame, now_bf.frame, next_bf.frame, next_x1v, next_y1v, next_x2v, next_y2v)
    return

# キーの分割を再設定する
def recalc_bone_by_complement(motion, al, now):    
    for tbf_idx, tbf in enumerate(motion.frames[al.name]):
        if tbf.frame == now:
            # とりあえず登録対象のキーが既存なのでそのキーを有効にして返す
            logger.info(",追加のトコに既にキーあり,now, %s,%s", now,al.name)

            tbf.key = True
            # 再分割キー明示
            tbf.split_complement = True

            return tbf
        elif tbf.frame > now:
            # 対象のキーがなくて次に行ってしまった場合、挿入

            # 補間曲線込みでキーフレーム生成
            fill_bf = utils.calc_bone_by_complement(motion.frames, al.name, now, True)
            # 必ずキーは登録する
            fill_bf.key = True
            # 再分割キー明示
            fill_bf.split_complement = True
            logger.debug("fill_bf f:%s, rotation: %s", fill_bf.frame, fill_bf.rotation.toEulerAngles())
            # 見つかった場所に挿入
            motion.frames[al.name].insert(tbf_idx, fill_bf)

            # 分割点のフレームを返す
            return fill_bf

    return None

# 腕IK調整事前準備
def prepare(motion, arm_links, hand_distance):

    for d in ["左", "右"]:
        for al in arm_links[d]:
            if not al.name in motion.frames:
                # キーがまったくない場合、とりあえず初期値で登録する
                logger.debug("キー登録: %s" % al.name)
                motion.frames[al.name] = [utils.calc_bone_by_complement(motion.frames, al.name, 0)]

    for f in range(motion.last_motion_frame + 1):
        is_checked = False

        for k in ["左腕", "左ひじ", "左手首", "右腕", "右ひじ", "右手首"]:
            for _, bf in enumerate(motion.frames[k]):
                if bf.frame == f:
                    # 該当フレームの場合
                    for direction in ["左", "右"]:
                        for al in arm_links[direction]:
                            if al.name in motion.frames:
                                is_added = False
                                for tbf_idx, tbf in enumerate(motion.frames[al.name]):
                                    if tbf.frame == bf.frame:
                                        # とりあえず登録対象のキーが既存なので終了
                                        if bf.frame == 5117:
                                            logger.debug("fill 既存あり: %s, i: %s, f: %s", al.name, tbf_idx, bf.frame)
                                        is_checked = True
                                        is_added = True
                                        break
                                    elif tbf.frame > bf.frame:
                                        # 対象のキーがなくて次に行ってしまった場合、挿入
                                        
                                        # 補間曲線込みでキーフレーム生成
                                        fillbf = utils.calc_bone_by_complement(motion.frames, al.name, bf.frame, True)
                                        # 手首間の距離がマイナスの場合（デバッグ機能）で有効
                                        # 普通の場合、とりあえず実際に登録はしない
                                        fillbf.key = True if hand_distance < 0 else False

                                        motion.frames[al.name].insert(tbf_idx, fillbf)
                                        if bf.frame == 5117:
                                            logger.debug("fill insert: %s, i: %s, f: %s, key: %s", al.name, tbf_idx, fillbf.frame, fillbf.key)

                                        is_checked = True
                                        is_added = True
                                        break
                                
                                if not is_added:
                                    # 最後のフレームがなくてそのまま終了してしまった場合は、直前のキーを設定する
                                    fillbf = copy.deepcopy(tbf)
                                    # とりあえず実際に登録はしない
                                    fillbf.key = False
                                    # 読み込みキーではない
                                    fillbf.read = False
                                    if bf.frame == 5117:
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
                    print("手首位置合わせ事前調整 f: %s" % f)

                # 両手が終わっててチェック済みならブレイク
                break

    print("手首位置合わせ事前調整終了")

# 手首位置合わせ実行
def exec_arm_ik(motion, trace_model, replace_model, hand_distance, org_motion_frames, all_rep_wrist_links, arm_links, error_path, error_file_logger):
    # 腕IKによる位置調整を行う場合

    # エラーを一度でも出力しているか(腕IK)
    is_error_outputed = False

    # 指の先までの位置(作成元モデル)
    all_org_finger_links, all_org_finger_indexes = trace_model.create_link_2_top_lr("人指３", "手首")
    logger.debug("all_org_finger_links: %s", [ "{0}: {1}\n".format(x.name, x.position) for x in all_org_finger_links["左"]])    
    logger.debug("all_org_finger_indexes: %s", [ x for x in all_org_finger_indexes["左"].keys()])    

    # 指の先までの位置(トレース先モデル)
    all_rep_finger_links, all_rep_finger_indexes = replace_model.create_link_2_top_lr("人指３", "手首")
    logger.debug("all_rep_finger_links: %s", all_rep_finger_indexes["右"].keys())

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
                        _, _, _, _, org_finger_global_3ds = utils.create_matrix_global(trace_model, all_org_finger_links[org_direction], org_motion_frames, bf, None)
                        logger.debug("org_finger_global_3ds ------------------------")
                        for n in range(len(all_org_finger_links[org_direction])):
                            logger.debug("f: %s, org_finger_global_3ds %s, %s, %s", bf.frame, n, all_org_finger_links[org_direction][len(all_org_finger_links[org_direction]) - n - 1].name, org_finger_global_3ds[n])
                        logger.debug("org 手首 index: %s", len(org_finger_global_3ds) - all_org_finger_indexes[org_direction]["手首"] - 1)
                        logger.debug("元モデルの反対側の手の指までの情報")
                        # 元モデルの反対側の手の指までの情報
                        _, _, _, _, org_reverse_finger_global_3ds = utils.create_matrix_global(trace_model, all_org_finger_links[reverse_org_direction], org_motion_frames, bf, None)
                        logger.debug("org_reverse_finger_global_3ds ------------------------")
                        for n in range(len(all_org_finger_links[reverse_org_direction])):
                            logger.debug("f: %s, org_reverse_finger_global_3ds %s, %s, %s", bf.frame, n, all_org_finger_links[reverse_org_direction][len(all_org_finger_links[reverse_org_direction]) - n - 1].name, org_reverse_finger_global_3ds[n])
                    
                        # 変換先モデルのIK計算前指までの情報
                        _, _, _, _, rep_finger_global_3ds = utils.create_matrix_global(replace_model, all_rep_finger_links[org_direction], motion.frames, bf, None)
                        logger.debug("rep_finger_global_3ds ------------------------")
                        for n in range(len(all_rep_finger_links[org_direction])):
                            logger.debug("f: %s, rep_finger_global_3ds %s, %s, %s", bf.frame, n, all_rep_finger_links[org_direction][len(all_rep_finger_links[org_direction]) - n - 1].name, rep_finger_global_3ds[n])
                        # 変換先モデルの反対側IK計算前指までの情報
                        _, _, _, _, rep_reverse_finger_global_3ds = utils.create_matrix_global(replace_model, all_rep_finger_links[reverse_org_direction], motion.frames, bf, None)
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
                                print("○手首近接あり: f: %s(%s), 手首間の距離: %s" % (bf.frame, org_direction, org_wrist_diff_rate ))

                                # 元モデルの向いている回転量
                                org_upper_direction_qq = utils.calc_upper_direction_qq(trace_model, org_upper_links, org_motion_frames, bf)
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
                                rep_upper_direction_qq = utils.calc_upper_direction_qq(replace_model, rep_upper_links, motion.frames, bf)
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

                                # # ---------
                                # wrist_ik_bone = "{0}偽IK".format(direction)
                                # if not wrist_ik_bone in motion.frames:
                                #     motion.frames[wrist_ik_bone] = []
                                
                                # wikbf = VmdBoneFrame(bf.frame)
                                # wikbf.name = wrist_ik_bone.encode('shift-jis')
                                # wikbf.format_name = wrist_ik_bone
                                # wikbf.frame = bf.frame
                                # wikbf.key = True
                                # wikbf.position = rep_wrist_pos
                                # motion.frames[wrist_ik_bone].append(wikbf)
                                # # ---------

                                # 変換先モデルの向きを元に戻して、正面向きの手首を回転させた位置に合わせる(反対側)
                                rep_reverse_wrist_pos = create_direction_pos(rep_upper_direction_qq, rep_reverse_front_wrist_pos)
                                logger.debug("frame: %s, rep_reverse_wrist_pos after: %s", bf.frame, rep_reverse_wrist_pos)

                                # # ---------
                                # reverse_wrist_ik_bone = "{0}偽IK".format(reverse_direction)
                                # if not reverse_wrist_ik_bone in motion.frames:
                                #     motion.frames[reverse_wrist_ik_bone] = []
                                
                                # rwikbf = VmdBoneFrame(bf.frame)
                                # rwikbf.name = reverse_wrist_ik_bone.encode('shift-jis')
                                # rwikbf.format_name = reverse_wrist_ik_bone
                                # rwikbf.frame = bf.frame
                                # rwikbf.key = True
                                # rwikbf.position = rep_reverse_wrist_pos
                                # motion.frames[reverse_wrist_ik_bone].append(rwikbf)
                                # # ---------

                                # 手首位置から角度を求める
                                calc_arm_IK2FK(rep_wrist_pos, replace_model, arm_links[direction], all_rep_wrist_links[direction], direction, motion.frames, bf, prev_space_bf)
                                # 反対側の手首位置から角度を求める
                                calc_arm_IK2FK(rep_reverse_wrist_pos, replace_model, arm_links[reverse_direction], all_rep_wrist_links[reverse_direction], reverse_direction, motion.frames, bf, prev_space_bf)

                                # 指位置調整-----------------

                                if finger_links and wrist_thickness["左"] != 0 and wrist_thickness["右"] != 0:
                                    # 指があるモデルの場合、手首角度調整。
                                    # ただし、手首の厚みが取れなかった場合、ボーン構造が通常と異なる可能性があるため、調整対象外

                                    # 手首の位置が変わっているので再算出

                                    # 変換先モデルのIK計算前指までの情報
                                    _, _, _, _, rep_finger_global_3ds = utils.create_matrix_global(replace_model, all_rep_finger_links[org_direction], motion.frames, bf, None)
                                    logger.debug("rep_finger_global_3ds ------------------------")
                                    for n in range(len(all_rep_finger_links[org_direction])):
                                        logger.debug("rep_finger_global_3ds %s, %s, %s", n, all_rep_finger_links[org_direction][len(all_rep_finger_links[org_direction]) - n - 1].name, rep_finger_global_3ds[n])
                                    # 変換先モデルの反対側IK計算前指までの情報
                                    _, _, _, _, rep_reverse_finger_global_3ds = utils.create_matrix_global(replace_model, all_rep_finger_links[reverse_org_direction], motion.frames, bf, None)
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
                                    rep_upper_direction_qq = utils.calc_upper_direction_qq(replace_model, rep_upper_links, motion.frames, bf)
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
                                if not is_error_outputed:
                                    is_error_outputed = True
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

                                                if bf.frame == 5117:
                                                    logger.debug("採用: cfk: %s, bf: %s, f: %s, read: %s, rot: %s", cfk, bf.frame, motion.frames[cfk][bf_idx].frame, motion.frames[cfk][bf_idx].read, motion.frames[cfk][bf_idx].rotation.toEulerAngles())

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
                            print("－手首近接なし: f: %s(%s), 手首間の距離: %s" % (bf.frame, org_direction, org_wrist_diff_rate ))

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

    return is_error_outputed

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
                joint = utils.calc_bone_by_complement(frames, joint_name, bf.frame)
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
    _, _, _, org_matrixs, org_global_3ds = utils.create_matrix_global(model, all_wrist_links, frames, bf)

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
