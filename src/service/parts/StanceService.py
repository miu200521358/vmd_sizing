# -*- coding: utf-8 -*-
#

from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
import module.MOptions as MOptions

from utils import MUtils, MServiceUtils # noqa
import utils.MLogger as MLogger # noqa

logger = MLogger(__name__, level=1)


class StanceService():
    def __init__(self, options: MOptions):
        self.options = options

    def execute(self, org_motion_frames):
        if self.options.motion_vmd_data.motion_cnt <= 0:
            # モーションデータが無い場合、処理スキップ
            return True

        # 腕スタンス補正
        self.adjust_arm_stance()

        return True
    
    def adjust_arm_stance(self):
        logger.info("腕スタンス補正", decoration=MLogger.DECORATION_LINE)
        
        # 腕のスタンス差
        arm_diff_qq_dic = self.calc_arm_stance()

        for direction in ["左", "右"]:
            for bone_type in ["腕", "ひじ", "手首"]:
                bone_name = "{0}{1}".format(direction, bone_type)

                if bone_name in arm_diff_qq_dic and bone_name in self.options.motion_vmd_data.frames:
                    # スタンス補正値がある場合
                    for bf in self.options.motion_vmd_data.frames[bone_name].values():
                        if bf.key:
                            if arm_diff_qq_dic[bone_name]["from"] == MQuaternion():
                                bf.rotation = bf.rotation * arm_diff_qq_dic[bone_name]["to"]
                            else:
                                bf.rotation = arm_diff_qq_dic[bone_name]["from"].inverted() * bf.rotation * arm_diff_qq_dic[bone_name]["to"]
                    
                    logger.info("%sスタンス補正終了", bone_name, decoration=MLogger.DECORATION_SIMPLE)
                    logger.test("from: %s", arm_diff_qq_dic[bone_name]["from"].toEulerAngles(), decoration=MLogger.DECORATION_SIMPLE)
                    logger.test("to: %s", arm_diff_qq_dic[bone_name]["to"].toEulerAngles(), decoration=MLogger.DECORATION_SIMPLE)

    def calc_arm_stance(self):
        arm_diff_qq_dic = {}

        for direction in ["左", "右"]:
            for from_bone_type, target_bone_type, to_bone_type in [(None, "腕", "ひじ"), ("腕", "ひじ", "手首"), ("ひじ", "手首", "中指１")]:
                from_bone_name = "{0}{1}".format(direction, from_bone_type) if from_bone_type else None
                target_bone_name = "{0}{1}".format(direction, target_bone_type)
                to_bone_name = "{0}{1}".format(direction, to_bone_type)
                
                arm_diff_qq_dic[target_bone_name] = {}

                if from_bone_name:
                    bone_names = [from_bone_name, target_bone_name, to_bone_name]
                else:
                    bone_names = [target_bone_name, to_bone_name]

                if set(bone_names).issubset(self.options.org_model_data.bones) and set(bone_names).issubset(self.options.rep_model_data.bones):
                    # 対象ボーンが揃っている場合（念のためバラバラにチェック）

                    if from_bone_name:
                        # FROM-TARGETの傾き
                        _, org_from_qq = MServiceUtils.calc_arm_stance_diff(self.options.org_model_data, from_bone_name, target_bone_name)
                        _, rep_from_qq = MServiceUtils.calc_arm_stance_diff(self.options.rep_model_data, from_bone_name, target_bone_name)

                        arm_diff_qq_dic[target_bone_name]["from"] = rep_from_qq.inverted() * org_from_qq
                    else:
                        arm_diff_qq_dic[target_bone_name]["from"] = MQuaternion()

                    # TARGET-TOの傾き
                    _, org_to_qq = MServiceUtils.calc_arm_stance_diff(self.options.org_model_data, target_bone_name, to_bone_name)
                    _, rep_to_qq = MServiceUtils.calc_arm_stance_diff(self.options.rep_model_data, target_bone_name, to_bone_name)

                    arm_diff_qq_dic[target_bone_name]["to"] = rep_to_qq.inverted() * org_to_qq
        
        return arm_diff_qq_dic


