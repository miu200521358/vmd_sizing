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
import utils
from typing import Union

logger = logging.getLogger("VmdSizing").getChild(__name__)


def exec(motion, trace_model, replace_model, output_vmd_path, org_motion_frames):
    print("■■ 移動補正 -----------------")

    # 移植先のセンターとグルーブは、作成元の比率に合わせる
    adjust_center(trace_model, replace_model, "センター")
    adjust_center(trace_model, replace_model, "グルーブ")

    # 足IKのXYZの比率
    xz_ratio, y_ratio, leg_ik_stance = calc_leg_ik_ratio(trace_model, replace_model)

    # センターのZ軸オフセットを計算
    cal_center_z_offset(trace_model, replace_model, "センター")

    # 足IKのオフセットを計算
    calc_ik_offset(trace_model, replace_model, xz_ratio)
    
    # 全ての親をコピー
    copy_root_parent(trace_model)
    copy_root_parent(replace_model)

    # サイズ比較
    # lengths = compare_length(trace_model, replace_model)

    # 足IKまでの位置(変換先モデル)
    global_ik_links = {}
    if "左足ＩＫ" in trace_model.bones and "左足ＩＫ" in replace_model.bones and "右足ＩＫ" in trace_model.bones and "右足ＩＫ" in replace_model.bones:
        all_rep_leg_ik_links, all_rep_leg_ik_indexes = replace_model.create_link_2_top_lr("つま先ＩＫ", "足ＩＫ")
        all_org_leg_ik_links, all_org_leg_ik_indexes = trace_model.create_link_2_top_lr("つま先ＩＫ", "足ＩＫ")
        global_ik_links["右足ＩＫ"] = {"rep_link": all_rep_leg_ik_links["右"], "rep_index": all_rep_leg_ik_indexes["右"], \
            "org_link": all_org_leg_ik_links["右"], "org_index": all_org_leg_ik_indexes["右"], "toe": "右つま先ＩＫ"}
        global_ik_links["左足ＩＫ"] = {"rep_link": all_rep_leg_ik_links["左"], "rep_index": all_rep_leg_ik_indexes["左"], \
            "org_link": all_org_leg_ik_links["左"], "org_index": all_org_leg_ik_indexes["左"], "toe": "左つま先ＩＫ"}

    if motion.motion_cnt > 0:
        # -----------------------------------------------------------------
        # 移動ボーン縮尺
        for k in ["右足ＩＫ" ,"左足ＩＫ", "右つま先ＩＫ" ,"左つま先ＩＫ", "右足ＩＫ親" ,"左足ＩＫ親", "右足IK親" ,"左足IK親", "センター", "グルーブ", "全ての親"]:
            if k in motion.frames and k in replace_model.bones:
                for bf in motion.frames[k]:
                    # IK比率をそのまま掛ける
                    bf.position.setX( bf.position.x() * xz_ratio )
                    bf.position.setY( bf.position.y() * y_ratio )
                    bf.position.setZ( bf.position.z() * xz_ratio )

                    if replace_model.bones[k].local_offset != QVector3D():
                        # ローカルZオフセットが入っている場合、オフセット調整
                        bf.position += replace_model.bones[k].local_offset
                    
                    if replace_model.bones[k].global_ik_offset != QVector3D() and k in global_ik_links:
                        # グローバルIKオフセットが入っている場合、オフセット調整
                        # つま先までのグローバル位置
                        _, _, _, _, rep_ik_global_3ds = utils.create_matrix_global(replace_model, global_ik_links[k]["rep_link"], motion.frames, bf, None)
                        # 先モデルの足IKが向いている回転量
                        rep_leg_direction_qq = bf.rotation
                        if "つま先ＩＫ" in global_ik_links[k]["index"]:
                            # つま先IKがある場合、つま先IKの向きも保持する
                            toe_ik_pos = rep_ik_global_3ds[len(rep_ik_global_3ds) - global_ik_links[k]["rep_index"]["つま先ＩＫ"] - 1]
                            leg_ik_pos = rep_ik_global_3ds[len(rep_ik_global_3ds) - global_ik_links[k]["rep_index"]["足ＩＫ"] - 1]
                            logger.debug("toe_ik_pos: %s", toe_ik_pos)
                            logger.debug("leg_ik_pos: %s", leg_ik_pos)
                            toe_initial_pos = (replace_model.bones[global_ik_links[k]["toe"]].position - replace_model.bones[k].position).normalized()
                            toe_initial_pos.setY(0)
                            toe_now_pos = (toe_ik_pos - leg_ik_pos).normalized()
                            toe_now_pos.setY(0)

                            rep_leg_direction_qq = QQuaternion.rotationTo(toe_initial_pos, toe_now_pos)
                        logger.debug("f: %s, k: %s, rot: %s", bf.frame, k, rep_leg_direction_qq.toEulerAngles())
                        # 正面向きにオフセット加算
                        rep_front_ik = utils.create_direction_pos(rep_leg_direction_qq.inverted(), bf.position)
                        rep_front_ik += replace_model.bones[k].global_ik_offset
                        # 元の向きに戻した時のセンター位置
                        rep_ik = utils.create_direction_pos(rep_leg_direction_qq, rep_front_ik)
                        logger.debug("bf.position: %s", bf.position)
                        logger.debug("rep_ik: %s", rep_ik)
                        bf.position = rep_ik

                print("移動補正: %s" % k)

        if "左足ＩＫ" in trace_model.bones and "右足ＩＫ" in trace_model.bones and  "左足ＩＫ" in replace_model.bones and "右足ＩＫ" in replace_model.bones \
            and  "左つま先ＩＫ" in trace_model.bones and "右つま先ＩＫ" in trace_model.bones and  "左つま先ＩＫ" in replace_model.bones and "右つま先ＩＫ" in replace_model.bones:
            # 足IKまでの位置(作成元モデル)
            all_org_toe_ik_links, all_org_toe_ik_indexes = trace_model.create_link_2_top_lr("つま先ＩＫ実体")
            # logger.debug("all_org_leg_links: %s", [ "{0}: {1}\n".format(x.name, x.position) for x in all_org_leg_links["左"]])    
            # logger.debug("all_org_leg_indexes: %s", [ x for x in all_org_leg_indexes["左"].keys()])    

            # 足IKまでの位置(トレース先モデル)
            all_rep_toe_ik_links, all_rep_toe_ik_indexes = replace_model.create_link_2_top_lr("つま先ＩＫ実体")
            # logger.debug("all_rep_leg_links: %s", all_rep_leg_indexes["右"].keys())

            # 足の長さの比率
            trace_leg_length, leg_ik_rate, leg_length_rate, ankle_qq_diff = calc_leg_rate(trace_model, replace_model)

            # 極端に小さい子は小さい方。普通・大きい子はそのまま
            leg_ik_ratio = y_ratio if y_ratio < leg_ik_rate * 0.8 else leg_ik_rate
            leg_length_ratio = y_ratio if y_ratio < leg_length_rate * 0.8 else leg_length_rate

            print("つま先補正用 - 足IK比率: %s, 足の大きさ比率: %s" % (leg_ik_ratio, leg_length_ratio) )
            # print("つま先補正用 - 足先EX比率: %s" % leg_ex_length_rate )

            for direction in ["右" ,"左"]:
                for link_name in ["{0}足ＩＫ".format(direction), "{0}足IK親".format(direction)]:
                    if link_name in motion.frames and link_name in replace_model.bones:
                        for bf_idx, bf in enumerate(motion.frames[link_name]):
                            if org_motion_frames[link_name][bf_idx].position.y() != 0:
                                # 該当キーの足IKの位置
                                # 元モデルの足IKまでの情報
                                _, _, _, _, org_toe_ik_global_3ds = utils.create_matrix_global(trace_model, all_org_toe_ik_links[direction], org_motion_frames, bf, None)
                                # 元モデルの足IKのY位置
                                org_leg_ik_y = org_toe_ik_global_3ds[len(org_toe_ik_global_3ds) - all_org_toe_ik_indexes[direction]["足ＩＫ"] - 1].y()
                                # 元モデルのつま先IKのY位置
                                org_toe_ik_y = org_toe_ik_global_3ds[len(org_toe_ik_global_3ds) - all_org_toe_ik_indexes[direction]["つま先ＩＫ実体"] - 1].y()

                                if 0 <= org_leg_ik_y <= trace_leg_length * 1.2:
                                    # 足IKのY位置が足の長さ＊αより小さい場合、つま先立ちの可能性あり
                                    # # 該当フレームの足先EXの角度
                                    # leg_ex_bone = utils.calc_bone_by_complement(org_motion_frames, "{0}足先EX".format(direction), bf.frame)

                                    # if leg_ex_bone.rotation == QQuaternion():
                                    #     print("%sフレーム: %sつま先補正: %s足IK: 高さ: %s, y: %s" % (bf.frame, link_name, direction, org_leg_ik_y, org_motion_frames[link_name][bf_idx].position.y()))
                                    #     # 足先EXが入ってない場合、つま先までの長さで補正
                                    #     leg_ratio = leg_length_rate
                                    # else:
                                    #     print("%sフレーム: %s足先EX補正: %s足IK: 高さ: %s, y: %s" % (bf.frame, link_name, direction, org_leg_ik_y, org_motion_frames[link_name][bf_idx].position.y()))
                                    #     # 足先EXが入っている場合、足先EXまでの長さで補正
                                    #     leg_ratio = leg_ex_length_rate

                                    # 先モデルの足IKまでの情報
                                    _, _, _, _, rep_toe_ik_global_3ds = utils.create_matrix_global(replace_model, all_rep_toe_ik_links[direction], motion.frames, bf, None)
                                    # 先モデルの足IKのY位置
                                    rep_leg_ik_y = rep_toe_ik_global_3ds[len(rep_toe_ik_global_3ds) - all_rep_toe_ik_indexes[direction]["足ＩＫ"] - 1].y()

                                    # 足IKの差分
                                    leg_ik_diff = ((org_leg_ik_y - trace_model.bones["{0}足ＩＫ".format(direction)].position.y()) * leg_ik_ratio) - (rep_leg_ik_y - replace_model.bones["{0}足ＩＫ".format(direction)].position.y())
                                    logger.debug("%s%s: org_leg_ik_y: %s, rep_leg_ik_y: %s, leg_ik_diff: %s, y: %s", direction, bf.frame, org_leg_ik_y, rep_leg_ik_y, leg_ik_diff, bf.position.y())

                                    bf.position.setY( bf.position.y() + leg_ik_diff )

                                    toe_ik_diff = 0
                                    if bf.rotation.toEulerAngles().x() <= -15:
                                        # つま先立っている場合、足IK回転
                                        bf.rotation = bf.rotation * ankle_qq_diff

                                        # 先モデルの足IKまでの情報
                                        _, _, _, _, rep_toe_ik_global_3ds = utils.create_matrix_global(replace_model, all_rep_toe_ik_links[direction], motion.frames, bf, None)
                                        # 先モデルの足IKのY位置
                                        rep_leg_ik_y = rep_toe_ik_global_3ds[len(rep_toe_ik_global_3ds) - all_rep_toe_ik_indexes[direction]["足ＩＫ"] - 1].y()
                                        # 先モデルのつま先IKのY位置
                                        rep_toe_ik_y = rep_toe_ik_global_3ds[len(rep_toe_ik_global_3ds) - all_rep_toe_ik_indexes[direction]["つま先ＩＫ実体"] - 1].y()

                                        # つま先IKの差分
                                        if rep_leg_ik_y > rep_toe_ik_y:
                                            if org_toe_ik_y > 0.3:
                                                # つま先IKの方が下の場合、つま先IKでも調整する
                                                toe_ik_diff = max(0, (org_toe_ik_y * min(leg_length_ratio, 1))) - rep_toe_ik_y
                                            else:
                                                # 0.3未満なら床接地
                                                toe_ik_diff = -rep_toe_ik_y
                                        logger.debug("%s%s: org_toe_ik_y: %s, max: %s, rep_toe_ik_y: %s, toe_ik_diff: %s, y: %s", direction, bf.frame, org_toe_ik_y, max(0, (org_toe_ik_y * min(leg_length_ratio, 1))), rep_toe_ik_y, toe_ik_diff, bf.position.y())

                                        # つま先ＩＫの位置で再補正
                                        bf.position.setY( bf.position.y() + toe_ik_diff )

                                    # print("%sフレーム: %sつま先補正: %s足IK: 高さ: %s, 補正値: %s,%s" % (bf.frame, link_name, direction, org_leg_ik_y, leg_ik_diff, toe_ik_diff))
                                    logger.debug("%sフレーム: %sつま先補正: %s足IK: 高さ: %s, 補正値: %s,%s", bf.frame, link_name, direction, org_leg_ik_y, leg_ik_diff, toe_ik_diff)
                                else:
                                    # print("%sフレーム: %s範囲外: %s足IK: 高さ: %s, y: %s" % (bf.frame, link_name, direction, org_leg_ik_y, org_motion_frames[link_name][bf_idx].position.y()))
                                    logger.debug("%sフレーム: %s範囲外: %s足IK: 高さ: %s, y: %s", bf.frame, link_name, direction, org_leg_ik_y, org_motion_frames[link_name][bf_idx].position.y())
                                    pass

                    print("つま先補正: %s" % link_name)

    return True

def calc_leg_rate(trace_model, replace_model):
    # 作成元左足ＩＫ
    trace_ankle_pos = trace_model.bones["左足ＩＫ"].position
    logger.debug("trace_ankle_pos: %s", trace_ankle_pos)
    # 作成元つま先
    trace_toe_pos = trace_model.get_toe_front_vertex_position()
    logger.debug("trace_toe_pos: %s", trace_toe_pos)
    # # 作成元左足ＩＫ
    # trace_toe_ik_pos = trace_model.bones["左つま先ＩＫ"].position
    # 作成元の足の長さ(つま先まで)
    # trace_leg_length = trace_ankle_pos.distanceToPoint(QVector3D(trace_ankle_pos.x(), 0, trace_toe_pos.z()))
    trace_leg_length = trace_ankle_pos.z() - trace_toe_pos.z()
    logger.debug("trace_leg_length: %s", trace_leg_length)
    # 作成元のつま先から足IKへの傾き
    trace_ankle_qq = calc_ankle_rotation(trace_ankle_pos, QVector3D(trace_ankle_pos.x(), 0, trace_toe_pos.z()))
    logger.debug("trace_ankle_qq: %s", trace_ankle_qq.toEulerAngles())
    # # 作成元足先EX（ある場合）
    # trace_toe_ex_pos = trace_toe_pos
    # trace_leg_ex_length = 1
    # if "左足先EX" in trace_model.bones:
    #     trace_toe_ex_pos = trace_model.bones["左足先EX"].position
    #     # 作成元の足の長さ(つま先~足先EXまで)
    #     trace_leg_ex_length = trace_toe_ex_pos.distanceToPoint(trace_toe_pos)
    #     logger.debug("trace_leg_ex_length: %s", trace_leg_ex_length)

    # 変換先左足ＩＫ
    replace_ankle_pos = replace_model.bones["左足ＩＫ"].position
    logger.debug("replace_ankle_pos: %s", replace_ankle_pos)
    # 変換先つま先
    replace_toe_pos = replace_model.get_toe_front_vertex_position()
    logger.debug("replace_toe_pos: %s", replace_toe_pos)
    # # 変換先左足ＩＫ
    # replace_toe_ik_pos = replace_model.bones["左つま先ＩＫ"].position
    # 変換先の足の長さ(つま先まで)
    # replace_leg_length = replace_ankle_pos.distanceToPoint(QVector3D(replace_ankle_pos.x(), 0, replace_toe_pos.z()))
    replace_leg_length = replace_ankle_pos.z() - replace_toe_pos.z()
    logger.debug("replace_leg_length: %s", replace_leg_length)
    # # 変換先足先EX（ある場合）
    # replace_toe_ex_pos = replace_toe_pos
    # replace_leg_ex_length = 1
    # if "左足先EX" in replace_model.bones:
    #     replace_toe_ex_pos = replace_model.bones["左足先EX"].position
    #     # 変換先の足の長さ(つま先~足先EXまで)
    #     replace_leg_ex_length = replace_toe_ex_pos.distanceToPoint(replace_toe_pos)
    #     logger.debug("replace_leg_ex_length: %s", replace_leg_ex_length)
    # 変換先のつま先から足IKへの傾き
    replace_ankle_qq = calc_ankle_rotation(replace_ankle_pos, QVector3D(replace_ankle_pos.x(), 0, replace_toe_pos.z()))
    logger.debug("replace_ankle_qq: %s", replace_ankle_qq.toEulerAngles())

    # 足IKの比率(つま先まで)
    leg_ik_rate = replace_ankle_pos.y() / trace_ankle_pos.y()
    logger.debug("leg_ik_rate: %s", leg_ik_rate)
    # # 足の大きさの比率(足先EXまで)
    # 足の大きさの比率(つま先まで)
    leg_length_rate = replace_leg_length / trace_leg_length
    logger.debug("leg_length_rate: %s", leg_length_rate)
    # # 足の大きさの比率(足先EXまで)
    # leg_ex_length_rate = (replace_leg_ex_length / replace_leg_length) / (trace_leg_ex_length / trace_leg_length)
    # logger.debug("leg_ex_length_rate: %s", leg_ex_length_rate)
    # 足首までの角度の差
    ankle_qq_diff = replace_ankle_qq.inverted() * trace_ankle_qq
    logger.debug("ankle_qq_diff: %s", ankle_qq_diff.toEulerAngles())

    return trace_leg_length, leg_ik_rate, leg_length_rate, ankle_qq_diff


def calc_ankle_rotation(from_pos, to_pos):
    from_qq = QQuaternion()
    if from_pos != QVector3D() and to_pos != QVector3D():

        to_pos = to_pos - from_pos
        to_pos.normalize()
        logger.debug("to_pos: %s", to_pos)        

        # 水平からTOボーンまでの回転量
        from_qq = QQuaternion.rotationTo(QVector3D(to_pos.x(), 1, -1), to_pos)
        logger.debug("from_pos: %s, to_pos: %s, from_qq: %s", from_pos, to_pos, from_qq.toEulerAngles())

    return from_qq


def calc_ik_offset(trace_model, replace_model, xz_ratio):
    if "左足" in trace_model.bones and "左足" in replace_model.bones and "左足ＩＫ" in trace_model.bones and "左足ＩＫ" in replace_model.bones and "右足ＩＫ" in trace_model.bones and "右足ＩＫ" in replace_model.bones:
        leg_ratio = replace_model.bones["左足"].position.y() / trace_model.bones["左足"].position.y()

        # 足IKの上限
        IK_RATE = xz_ratio * 1.2
        org_left_leg_ik_pos = trace_model.bones["左足ＩＫ"].position
        rep_left_leg_ik_pos = replace_model.bones["左足ＩＫ"].position
        org_left_leg_pos = trace_model.bones["左足"].position
        rep_left_leg_pos = replace_model.bones["左足"].position
        left_leg_ik_offset = QVector3D(((org_left_leg_ik_pos.x() - org_left_leg_pos.x()) * leg_ratio) - (rep_left_leg_ik_pos.x() - rep_left_leg_pos.x()), 0, (org_left_leg_ik_pos.z() * leg_ratio) - rep_left_leg_ik_pos.z())
        logger.info("left_leg_ik_offset before: %s", left_leg_ik_offset)
        logger.info("rep_left_leg_ik_pos: %s", rep_left_leg_ik_pos)
        logger.info("rep_left_leg_ik_pos*IK: %s", rep_left_leg_ik_pos * IK_RATE)
        if abs(left_leg_ik_offset.x()) > abs(rep_left_leg_ik_pos.x() * IK_RATE):
            re_x = rep_left_leg_ik_pos.x() * IK_RATE
            left_leg_ik_offset.setX( re_x * ( 1 if utils.sign(left_leg_ik_offset.x()) == utils.sign(rep_left_leg_ik_pos.x()) else -1 ) )
        # if abs(left_leg_ik_offset.z()) > abs(rep_left_leg_ik_pos.z() * IK_RATE):
        #     re_z = rep_left_leg_ik_pos.z() * IK_RATE
        #     left_leg_ik_offset.setZ( re_z * ( 1 if utils.sign(left_leg_ik_offset.z()) == utils.sign(rep_left_leg_ik_pos.z()) else -1 ) )
        logger.info("left_leg_ik_offset after: %s", left_leg_ik_offset)

        org_right_leg_ik_pos = trace_model.bones["右足ＩＫ"].position
        rep_right_leg_ik_pos = replace_model.bones["右足ＩＫ"].position
        org_right_leg_pos = trace_model.bones["右足"].position
        rep_right_leg_pos = replace_model.bones["右足"].position
        right_leg_ik_offset = QVector3D(((org_right_leg_ik_pos.x() - org_right_leg_pos.x()) * leg_ratio) - (rep_right_leg_ik_pos.x() - rep_right_leg_pos.x()), 0, (org_right_leg_ik_pos.z() * leg_ratio) - rep_right_leg_ik_pos.z())
        logger.info("right_leg_ik_offset before: %s", right_leg_ik_offset)
        logger.info("rep_right_leg_ik_pos: %s", rep_right_leg_ik_pos)
        logger.info("rep_right_leg_ik_pos*IK: %s", rep_right_leg_ik_pos * IK_RATE)
        if abs(right_leg_ik_offset.x()) > abs(rep_right_leg_ik_pos.x() * IK_RATE):
            re_x = rep_right_leg_ik_pos.x() * IK_RATE
            right_leg_ik_offset.setX( re_x * ( 1 if utils.sign(right_leg_ik_offset.x()) == utils.sign(rep_right_leg_ik_pos.x()) else -1 ) )
        # if abs(right_leg_ik_offset.z()) > abs(rep_right_leg_ik_pos.z() * IK_RATE):
        #     re_z = rep_right_leg_ik_pos.z() * IK_RATE
        #     right_leg_ik_offset.setZ( re_z * ( 1 if utils.sign(right_leg_ik_offset.z()) == utils.sign(rep_right_leg_ik_pos.z()) else -1 ) )
        logger.info("right_leg_ik_offset after: %s", right_leg_ik_offset)

        print("左足IKオフセット: x: %s, z: %s" % ( left_leg_ik_offset.x(), left_leg_ik_offset.z()))
        print("右足IKオフセット: x: %s, z: %s" % ( right_leg_ik_offset.x(), right_leg_ik_offset.z()))

        replace_model.bones["左足ＩＫ"].local_offset = left_leg_ik_offset
        replace_model.bones["右足ＩＫ"].local_offset = right_leg_ik_offset

        # replace_model.bones["左足ＩＫ"].global_ik_offset = QVector3D(((trace_model.bones["左足"].position.x() * leg_ratio) - replace_model.bones["左足"].position.x()), 0, 0)
        # replace_model.bones["右足ＩＫ"].global_ik_offset = QVector3D(((trace_model.bones["右足"].position.x() * leg_ratio) - replace_model.bones["右足"].position.x()), 0, 0)

        return True
    
    return False

def cal_center_z_offset(trace_model, replace_model, bone_name):
    if bone_name in trace_model.bones and bone_name in replace_model.bones and "センター" in trace_model.bones and "センター" in replace_model.bones and "左足首" in trace_model.bones and "左足首" in replace_model.bones and "左足" in trace_model.bones and "左足" in replace_model.bones and "左つま先ＩＫ" in trace_model.bones and "左つま先ＩＫ" in replace_model.bones:
        # 移植元にも移植先にも対象ボーンがある場合
        # 作成元センターのZ位置
        trace_center_z = trace_model.bones["センター"].position.z()
        logger.debug("trace_center_z: %s", trace_center_z)
        # 作成元左足首のZ位置
        trace_ankle_z = trace_model.bones["左足首"].position.z()
        logger.debug("trace_ankle_z: %s", trace_ankle_z)
        # 作成元左足のZ位置
        trace_leg_z = trace_model.bones["左足"].position.z()
        logger.debug("trace_leg_z: %s", trace_leg_z)
        # 作成元つま先ＩＫのZ位置
        trace_toe_z = trace_model.get_toe_front_vertex_position().z()
        # trace_toe_z = trace_model.bones["左つま先ＩＫ"].position.z()
        logger.debug("trace_toe_z: %s", trace_toe_z)

        # トレース変換先センターのZ位置
        replace_center_z = replace_model.bones["センター"].position.z()
        logger.debug("replace_center_z: %s", replace_center_z)
        # トレース変換先左足首のZ位置
        replace_ankle_z = replace_model.bones["左足首"].position.z()
        logger.debug("replace_ankle_z: %s", replace_ankle_z)
        # トレース変換先左足のZ位置
        replace_leg_z = replace_model.bones["左足"].position.z()
        logger.debug("replace_leg_z: %s", replace_leg_z)
        # トレース変換先つま先ＩＫのZ位置
        replace_toe_z = replace_model.get_toe_front_vertex_position().z()
        # replace_toe_z = replace_model.bones["左つま先ＩＫ"].position.z()
        logger.debug("replace_toe_z: %s", replace_toe_z)

        # 作成元の足の長さ
        trace_leg_zlength = trace_ankle_z - trace_toe_z
        # 作成元の重心
        trace_center_gravity = (trace_ankle_z - trace_leg_z) / (trace_ankle_z - trace_toe_z)
        logger.debug("trace_center_gravity %s, trace_leg_zlength: %s", trace_center_gravity, trace_leg_zlength)
        
        # トレース変換先の足の長さ
        replace_leg_zlength = replace_ankle_z - replace_toe_z
        # トレース変換先の重心
        replace_center_gravity = (replace_ankle_z - replace_leg_z) / (replace_ankle_z - replace_toe_z)
        logger.debug("replace_center_gravity %s, replace_leg_zlength: %s", replace_center_gravity, replace_leg_zlength)
        
        # if replace_center_gravity != trace_center_gravity:
        #     # 生成元と同じ重心で、変換先モデルのサイズに合わせて算出
        #     replace_model.bones[bone_name].offset_z = (replace_ankle_z - replace_center_z) - (trace_center_gravity * replace_leg_zlength)
        #     logger.debug("trace_center_gravity * (replace_leg_zlength - replace_ankle_z) %s", trace_center_gravity * (replace_leg_zlength - replace_ankle_z))
       
        replace_model.bones[bone_name].local_offset = QVector3D(0, 0, (replace_center_gravity - trace_center_gravity) * ( replace_leg_zlength / trace_leg_zlength ))
        logger.debug("local_offset %s", replace_model.bones[bone_name].local_offset)

        # if replace_leg_zlength < trace_leg_zlength:
        #     # 小さい子は、オフセットを小さくする
            # replace_model.bones[bone_name].local_offset *= ( replace_leg_zlength / trace_leg_zlength )

        print("Zオフセット: %s: %s" % ( bone_name, replace_model.bones[bone_name].local_offset.z()))

        return True
    else:
        print("Zオフセットなし: %s" % ( bone_name ))

        return False

def calc_leg_ik_ratio(trace_model, replace_model, is_print=True):
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

        if is_print:
            print("足の長さの比率: xz: %s, y: %s" % (xz_ratio, y_ratio))

        # # 左足のスタンス距離比
        # l_stance = ((replace_model.bones["左足ＩＫ"].position - replace_model.bones["センター"].position).x()) - ((trace_model.bones["左足ＩＫ"].position - trace_model.bones["センター"].position).x() * xz_ratio)
        # r_stance = ((replace_model.bones["右足ＩＫ"].position - replace_model.bones["センター"].position).x()) - ((trace_model.bones["右足ＩＫ"].position - trace_model.bones["センター"].position).x() * xz_ratio)

        # logger.debug("replace: %s", (replace_model.bones["左足ＩＫ"].position - replace_model.bones["センター"].position).x())
        # logger.debug("trace: %s", (trace_model.bones["左足ＩＫ"].position - trace_model.bones["センター"].position).x())
        # logger.debug("trace2: %s", ((trace_model.bones["左足ＩＫ"].position - trace_model.bones["センター"].position).x() * xz_ratio))

        # # print("足のスタンス補正値: l: %s, r: %s" % (l_stance, r_stance))

        return xz_ratio, y_ratio, {"左": 1, "右": 1}

    if is_print:
        print("「足」「ひざ」「足首」「センター」のいずれかのボーンが不足しているため、足の長さの比率が測れませんでした")

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

# ------------------------------------------------------------
# モデル間の目ボーンの高さを求める
#
#  シンメトリとは限らないので、左右の目の中間の高さ
#  (高さの平均)を採用する。
#  @todo 片目だけある場合をスマートに書けていない。
# ------------------------------------------------------------
def calc_eye_level(model: PmxModel) -> Union[float, None]:
    if "左目" not in model.bones and "右目" not in model.bones:
        # 両目共にボーンがない場合はNone
        return None

    left_eye_level = right_eye_level = 0 # type: float
    if "左目" not in model.bones:
        # 左目がなければ右目の値を採用できるか
        if "右目" in model.bones:
            left_eye_level = right_eye_level = model.bones["右目"].position.y()
        # 両目がないパターンは最初にチェック済み
    else :
        # 素直に左目の値を採用できる
        left_eye_level = model.bones["左目"].position.y()

    if "右目" not in model.bones:
        # 右目がなければ左目の値を採用する(ここに来る時は左目の値は確定している)
        right_eye_level = left_eye_level
    else :
        # 素直に右目の値を採用できる
        right_eye_level = model.bones["右目"].position.y()

    # 右目左目の高さの平均を求める
    # どちらか片方しかない場合は同値が入ってくるので略
    eye_average_level = (left_eye_level + right_eye_level) / 2 # type: float

    print("モデル: %s 両目の中間の高さ: %s" % (model.name, eye_average_level))

    return eye_average_level

# ------------------------------------------------------------
# モデル間の目ボーンの高さ比率を求める
# ------------------------------------------------------------
def calc_eye_level_ratio(trace_model: PmxModel, replace_model: PmxModel) -> Union[float, None]:
    replace_eye_level = calc_eye_level(replace_model) # type: float
    trace_eye_level = calc_eye_level(trace_model) # type: float

    # 両モデルまたは片方に目ボーンがない場合は倍率を求められない
    if replace_eye_level is None or trace_eye_level is None:
        print("どちらかのモデルに目ボーンがないので目線での高さの調節ができません")
        return None

    # Y比率(目ボーン中間の高さ比率)
    eye_level_ratio = replace_eye_level / trace_eye_level # type: float

    print("目の高さ比率: %s" % eye_level_ratio)

    return eye_level_ratio

# ------------------------------------------------------------
# モデル間の頭ボーンの高さ比率を求める
# ------------------------------------------------------------
def calc_head_ratio(trace_model, replace_model) -> float:
    if "頭" not in trace_model.bones or "頭" not in replace_model.bones:
        # 頭ボーンがない場合は倍率を求められない
        return None

    # Y比率(頭ボーンのY差)
    replace_head_height = replace_model.bones["頭"].position.y() # type: float
    trace_head_height = trace_model.bones["頭"].position.y() # type: float
    y_ratio = replace_head_height / trace_head_height #type: float

    logger.debug("y_ratio replace_head_height: %s, trace_head_height: %s", replace_head_height, trace_head_height)

    return y_ratio
