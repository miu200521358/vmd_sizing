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

logger = logging.getLogger("VmdSizing").getChild(__name__)

def exec(motion, trace_model, replace_model, output_vmd_path):
    if motion.motion_cnt > 0:
        # -----------------------------------------------------------------
        # 腕の角度補正

        if not trace_model.can_arm_sizing or not replace_model.can_arm_sizing:
            # 腕構造チェックがFALSEの場合、スタンス補正なし
            return False
                    
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
                            # arm_stance_qqs[dlist["腕"]].inverted() *  * arm_stance_qqs[dlist["手首"]]
                            bf.rotation = arm_stance_qqs[dlist["ひじ"]].inverted() * bf.rotation

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
    return True


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
