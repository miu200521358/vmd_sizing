# -*- coding: utf-8 -*-
#

import copy

from mmd.PmxData import PmxModel # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MOptions, MOptionsDataSet
from module.MParams import BoneLinks
from utils import MUtils, MServiceUtils, MBezierUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__, level=1)


class StanceService():
    def __init__(self, options: MOptions):
        self.options = options

    def execute(self):
        for data_set_idx, data_set in enumerate(self.options.data_set_list):
            if data_set.motion_vmd_data.motion_cnt <= 0:
                # モーションデータが無い場合、処理スキップ
                return True
            
            # # 代替モデルでない場合、上半身スタンス補正
            # if not data_set.substitute_model_flg:
            #     self.adjust_upper_stance()

            # 腕スタンス補正
            self.adjust_arm_stance(data_set_idx, data_set)

            return True
        
    # 上半身スタンス補正
    def adjust_upper_stance(self):
        logger.info("上半身スタンス補正", decoration=MLogger.DECORATION_LINE)
        motion = self.options.motion_vmd_data

        # 上半身調整に必要なボーン群
        upper_target_bones = ["上半身", "頭", "首", "左腕", "右腕"]

        # 上半身2調整に必要なボーン群
        upper2_target_bones = ["上半身", "上半身2", "頭", "首", "左腕", "右腕"]

        # モデルとモーション全部に上半身2がある場合、TRUE
        is_upper2_existed = set(upper2_target_bones).issubset(self.options.org_model_data.bones) and set(upper2_target_bones).issubset(self.options.rep_model_data.bones) \
            and "上半身2" in self.options.motion_vmd_data.bones and len(self.options.motion_vmd_data.bones["上半身2"]) > 1

        if set(upper_target_bones).issubset(self.options.org_model_data.bones) and set(upper_target_bones).issubset(self.options.rep_model_data.bones) and "上半身" in motion.bones:
            # TOボーン名
            to_bone_name = "上半身2" if is_upper2_existed else "頭"

            # 元モデルのリンク生成
            org_head_links = self.options.org_model_data.create_link_2_top_one(to_bone_name)
            org_upper_links = self.options.org_model_data.create_link_2_top_one("上半身")
            org_neck_links = self.options.org_model_data.create_link_2_top_one("首")
            org_arm_links = self.options.org_model_data.create_link_2_top_lr("腕")

            # 変換先モデルのリンク生成
            rep_head_links = self.options.rep_model_data.create_link_2_top_one(to_bone_name)
            rep_upper_links = self.options.rep_model_data.create_link_2_top_one("上半身")
            rep_neck_links = self.options.rep_model_data.create_link_2_top_one("首")
            rep_arm_links = self.options.rep_model_data.create_link_2_top_lr("腕")

            # 上半身からTO_BONEへの傾き
            rep_upper_slope = (self.options.rep_model_data.bones[to_bone_name].position - self.options.rep_model_data.bones["上半身"].position).normalized()
            rep_upper_slope_up = MVector3D(-1, 0, 0)
            rep_upper_slope_cross = MVector3D.crossProduct(rep_upper_slope, rep_upper_slope_up).normalized()
            
            logger.test("上半身 slope: %s", rep_upper_slope)
            logger.test("上半身 cross: %s", rep_upper_slope_cross)

            rep_upper_initial_slope_qq = MQuaternion.fromDirection(rep_upper_slope, rep_upper_slope_cross)

            # 準備（細分化）
            self.prepare_split_stance("上半身")

            logger.info("上半身スタンス準備終了", decoration=MLogger.DECORATION_SIMPLE)

            for fno in motion.get_bone_fnos("上半身"):
                bf = motion.bones["上半身"][fno]
                if bf.key:
                    self.calc_rotation_stance(bf, org_motion, motion, org_upper_links, org_head_links, org_neck_links, org_arm_links, \
                                              rep_upper_links, rep_head_links, rep_neck_links, rep_arm_links, \
                                              "", "上半身", "上半身", to_bone_name, rep_upper_initial_slope_qq, self.def_is_rotation_no_check_upper, self.def_calc_up_upper, 0.9)

            # # 子の角度調整
            # adjust_rotation_by_parent(org_motion, motion, self.options.org_model_data, self.options.rep_model_data, "首", "上半身", test_param)
            # adjust_rotation_by_parent(org_motion, motion, self.options.org_model_data, self.options.rep_model_data, "左腕", "上半身", test_param)
            # adjust_rotation_by_parent(org_motion, motion, self.options.org_model_data, self.options.rep_model_data, "右腕", "上半身", test_param)

            # utils.output_file_logger(file_logger, "上半身スタンス補正終了")

            # if set(upper2_target_bones).issubset(self.options.org_model_data.bones) and set(upper2_target_bones).issubset(self.options.rep_model_data.bones) and "上半身2" in motion.bones:
            #     # 元モデルのリンク生成
            #     org_head_links, org_head_indexes = self.options.org_model_data.create_link_2_top_one("頭")
            #     org_upper2_links, org_upper2_indexes = self.options.org_model_data.create_link_2_top_one("上半身2")
            #     org_arm_links, org_arm_indexes = self.options.org_model_data.create_link_2_top_lr("腕")
            #     # 変換先モデルのリンク生成
            #     rep_head_links, rep_head_indexes = self.options.rep_model_data.create_link_2_top_one("頭")
            #     rep_upper2_links, rep_upper2_indexes = self.options.rep_model_data.create_link_2_top_one("上半身2")
            #     rep_arm_links, rep_arm_indexes = self.options.rep_model_data.create_link_2_top_lr("腕")

            #     # 上半身2から頭への傾き
            #     rep_upper2_slope = (self.options.rep_model_data.bones["頭"].position - self.options.rep_model_data.bones["上半身2"].position).normalized()
            #     rep_upper2_slope_up = MVector3D(-1, 0, 0)
            #     rep_upper2_slope_cross = MVector3D.crossProduct(rep_upper2_slope, rep_upper2_slope_up).normalized()
                
            #     logger.debug("上半身2 slope: %s", rep_upper2_slope)
            #     logger.debug("上半身2 cross: %s", rep_upper2_slope_cross)

            #     rep_upper2_initial_slope_qq = QQuaternion.fromDirection(rep_upper2_slope, rep_upper2_slope_cross)

            #     # 準備（細分化）
            #     prepare_split_stance(motion, "上半身2", file_logger)

            #     utils.output_file_logger(file_logger, "上半身2スタンス準備終了")

            #     for bf in motion.bones["上半身2"]:
            #         if bf.key == True:
            #             calc_rotation_stance(org_motion, motion, self.options.org_model_data, org_upper2_links, org_upper2_indexes, org_head_links, org_head_indexes, org_arm_links, org_arm_indexes, \
            #                 self.options.rep_model_data, rep_upper2_links, rep_upper2_indexes, rep_head_links, rep_head_indexes, rep_arm_links, rep_arm_indexes, "", "上半身2", "上半身2", "頭", "上半身2", \
            #                 rep_upper2_initial_slope_qq, is_error_outputed, file_logger, output_vmd_path, bf, define_is_rotation_no_check_upper, \
            #                 define_calc_up_from_upper2, define_calc_up_to_upper2, 0.9, MVector3D(), True)

            #     # 子の角度調整
            #     adjust_rotation_by_parent(org_motion, motion, self.options.org_model_data, self.options.rep_model_data, "首", "上半身2", test_param)
            #     adjust_rotation_by_parent(org_motion, motion, self.options.org_model_data, self.options.rep_model_data, "左腕", "上半身2", test_param)
            #     adjust_rotation_by_parent(org_motion, motion, self.options.org_model_data, self.options.rep_model_data, "右腕", "上半身2", test_param)

            #     utils.output_file_logger(file_logger, "上半身2スタンス補正終了")
    
    # 定義: 回転チェック不要条件（上半身）
    def def_is_rotation_no_check_upper(self, qq: MQuaternion):
        return False
    
    # 定義: 傾きを求める方向の位置計算（上半身）
    def def_calc_up_upper(self, bf: VmdBoneFrame, rep_motion: VmdMotion, rep_neck_links: BoneLinks, rep_arm_links: BoneLinks):

        # 左腕ボーンまでの位置
        rep_left_arm_global_3ds = MServiceUtils.calc_global_pos(self.options.rep_model_data, rep_arm_links["左"], rep_motion, bf)
        rep_left_arm_pos = rep_left_arm_global_3ds["左腕"]

        # 右腕ボーンまでの位置
        rep_right_arm_global_3ds = MServiceUtils.calc_global_pos(self.options.rep_model_data, rep_arm_links["右"], rep_motion, bf)
        rep_right_arm_pos = rep_right_arm_global_3ds["右腕"]
        
        return rep_left_arm_pos - rep_right_arm_pos

    # スタンス補正
    def calc_rotation_stance(self, bf: VmdBoneFrame, org_motion: VmdMotion, motion: VmdMotion, \
                             org_base_links: BoneLinks, org_to_links: BoneLinks, org_neck_links: BoneLinks, org_arm_links: BoneLinks, \
                             rep_base_links: BoneLinks, rep_to_links: BoneLinks, rep_neck_links: BoneLinks, rep_arm_links: BoneLinks, \
                             direction_name: str, base_bone_name: str, from_bone_name: str, to_bone_name: str, rep_initial_slope_qq: MQuaternion, \
                             def_is_rotation_no_check, def_calc_up, dot_limit):

        target_base_bone_name = "{0}{1}".format(direction_name, base_bone_name)
        target_from_bone_name = "{0}{1}".format(direction_name, from_bone_name)
        target_to_bone_name = "{0}{1}".format(direction_name, to_bone_name)

        # 基準の親ボーン
        base_parent_bone_name = [lbone_name for lidx, lbone_name in enumerate(org_to_links.links) if org_to_links.index(target_base_bone_name) < lidx][0]
        # 基準より親の回転量
        parent_qq = MServiceUtils.calc_direction_qq(self.options.rep_model_data, rep_base_links.from_links(base_parent_bone_name), motion, bf)
        logger.test("f: %s, parent_qq: %s", bf.fno, parent_qq)

        # -------------

        # 処理対象までのモーション情報(処理対象以上のモーション情報を含まない)
        org_base_motion = org_to_links.take_out_frames(org_motion, base_parent_bone_name, bf.fno)
        rep_base_motion = rep_to_links.take_out_frames(motion, base_parent_bone_name, bf.fno)

        # -------------

        # TO位置の再計算
        new_rep_to_pos, rep_to_pos, rep_base_pos = self.recalc_to_pos(bf, org_base_motion, rep_base_motion, org_base_motion, rep_base_motion, \
                                                                      org_to_links, org_base_links, org_arm_links, \
                                                                      rep_to_links, rep_base_links, rep_arm_links, base_bone_name, to_bone_name)

        # UP方向の再計算
        up_pos = def_calc_up(bf, motion, rep_neck_links, rep_arm_links)

        # ---------------
        # FROMの回転量を再計算する
        direction = rep_to_pos - rep_base_pos
        up = MVector3D.crossProduct(direction.normalized(), up_pos.normalized())
        from_orientation = MQuaternion.fromDirection(direction, up)
        initial = rep_initial_slope_qq
        from_rotation = parent_qq.inverted() * from_orientation * initial.inverted()
        logger.test("f: %s, parent: %s", bf.fno, parent_qq.toEulerAngles())
        logger.test("f: %s, initial: %s", bf.fno, initial.toEulerAngles())
        logger.test("f: %s, orientation: %s", bf.fno, from_orientation.toEulerAngles())
        logger.test("f: %s, bf: %s", bf.fno, from_rotation.toEulerAngles())

        logger.debug("f: %s, rep_base_pos(%s): %s", bf.fno, base_bone_name, rep_base_pos, decoration=MLogger.DECORATION_SIMPLE)
        logger.debug("f: %s, rep_to_pos(%s): %s: 元: %s", bf.fno, target_to_bone_name, new_rep_to_pos, rep_to_pos, decoration=MLogger.DECORATION_SIMPLE)
        logger.debug("f: %s, rep_up_pos: %s", bf.fno, up_pos, decoration=MLogger.DECORATION_SIMPLE)

        if def_is_rotation_no_check and def_is_rotation_no_check(rep_initial_slope_qq):
            # チェックなし条件に合致する場合、チェックなしで適用
            bf.rotation = from_rotation
        else:
            if bf.fno in motion.bones[target_from_bone_name]:
                # 元にもあるキーである場合、内積チェック
                uad = abs(MQuaternion.dotProduct(from_rotation, motion.bones[target_from_bone_name][bf.fno].rotation))
                if uad < dot_limit:
                    logger.warning("%sフレーム目%sスタンス補正失敗: 角度:%s, uad: %s", bf.fno, target_from_bone_name, from_rotation.toEulerAngles(), uad)
                else:
                    # 内積の差が小さい場合、回転適用
                    bf.rotation = from_rotation
            else:
                # 元にもない場合（ないはず）、はそのまま設定
                bf.rotation = from_rotation

    # TO位置の再計算処理
    def recalc_to_pos(self, bf: VmdBoneFrame, org_base_motion: VmdMotion, rep_base_motion: VmdMotion, org_to_motion: VmdMotion, rep_to_motion: VmdMotion, \
                      org_to_links: BoneLinks, org_base_links: BoneLinks, org_arm_links: BoneLinks, \
                      rep_to_links: BoneLinks, rep_base_links: BoneLinks, rep_arm_links: BoneLinks, base_bone_name: str, to_bone_name: str):

        # 基準ボーンまでの位置
        # org_base_global_3ds = MServiceUtils.calc_global_pos(self.options.org_model_data, org_to_links.from_links(base_bone_name), org_base_motion, bf)
        rep_base_global_3ds = MServiceUtils.calc_global_pos(self.options.rep_model_data, rep_to_links.from_links(base_bone_name), rep_base_motion, bf)

        # 基準ボーンまでの向いている回転量
        # org_base_direction_qq = MServiceUtils.calc_direction_qq(self.options.org_model_data, org_to_links.from_links(base_bone_name), org_base_motion, bf)
        rep_base_direction_qq = MServiceUtils.calc_direction_qq(self.options.rep_model_data, rep_to_links.from_links(base_bone_name), rep_base_motion, bf)

        # # 基準ボーンの位置
        # org_base_pos = org_base_global_3ds[base_bone_name]
        rep_base_pos = rep_base_global_3ds[base_bone_name]

        # 正面向きの基準ボーンまでの位置
        # org_front_base_global_3ds = MServiceUtils.calc_global_position_by_direction(org_base_direction_qq.inverted(), org_base_global_3ds)
        rep_front_base_global_3ds = MServiceUtils.calc_global_position_by_direction(rep_base_direction_qq.inverted(), rep_base_global_3ds)

        # 正面向きの基準ボーンの位置
        # org_front_base_pos = org_front_base_global_3ds[base_bone_name]
        rep_front_base_pos = rep_front_base_global_3ds[base_bone_name]

        # -------------

        # TOボーンまでの位置（フレームはFROMまでで、TO自身は初期値として求める）
        org_to_global_3ds = MServiceUtils.calc_global_pos(self.options.org_model_data, org_to_links.from_links(to_bone_name), org_to_motion, bf)
        rep_to_global_3ds = MServiceUtils.calc_global_pos(self.options.rep_model_data, rep_to_links.from_links(to_bone_name), rep_to_motion, bf)

        # TOボーンまでの向いている回転量
        org_to_direction_qq = MServiceUtils.calc_direction_qq(self.options.org_model_data, org_to_links.from_links(to_bone_name), org_to_motion, bf)
        rep_to_direction_qq = MServiceUtils.calc_direction_qq(self.options.rep_model_data, rep_to_links.from_links(to_bone_name), rep_to_motion, bf)

        # 正面向きのTOボーンまでの位置
        org_front_to_global_3ds = MServiceUtils.calc_global_position_by_direction(org_to_direction_qq.inverted(), org_to_global_3ds)
        rep_front_to_global_3ds = MServiceUtils.calc_global_position_by_direction(rep_to_direction_qq.inverted(), rep_to_global_3ds)

        # 体幹指定ボーンの位置
        org_front_to_pos = org_front_to_global_3ds[to_bone_name]
        rep_front_to_pos = rep_front_to_global_3ds[to_bone_name]

        # -------------

        # 肩幅比率
        org_arm_diff = (org_arm_links["左"].get("左腕").position - org_arm_links["右"].get("右腕").position)
        rep_arm_diff = (rep_arm_links["左"].get("左腕").position - rep_arm_links["右"].get("右腕").position)
        arm_diff_length = rep_arm_diff.length() / org_arm_diff.length()

        # TOの長さ比率
        org_to_diff = (org_to_links.get(to_bone_name).position - org_base_links.get(base_bone_name).position)
        org_to_diff.effective()
        rep_to_diff = (rep_to_links.get(to_bone_name).position - rep_base_links.get(base_bone_name).position)
        rep_to_diff.effective()
        to_diff_length = rep_to_diff.length() / org_to_diff.length()
        to_diff = rep_to_diff / org_to_diff
        to_diff.effective()

        # ---------------
        
        rep_front_to_x = rep_front_base_pos.x() + ((org_front_to_pos.x() - org_to_diff.x()) * arm_diff_length)
        rep_front_to_y = rep_front_base_pos.y() + ((org_front_to_pos.y() - org_to_diff.y()) * to_diff_length)
        rep_front_to_z = rep_front_base_pos.z() + ((org_front_to_pos.z() - org_to_diff.z()) * arm_diff_length)

        new_rep_front_to_pos = MVector3D(rep_front_to_x, rep_front_to_y, rep_front_to_z)
        logger.test("f: %s, new_rep_front_to_pos: %s", bf.fno, new_rep_front_to_pos)
        logger.test("f: %s, rep_to_pos: %s", bf.fno, rep_front_to_pos)

        # 正面向きの新しいTO位置
        new_rep_front_to_global_3ds = copy.deepcopy(rep_front_to_global_3ds)
        new_rep_front_to_global_3ds[to_bone_name] = new_rep_front_to_pos

        # 回転を元に戻した位置
        rotated_to_3ds = MServiceUtils.calc_global_position_by_direction(rep_to_direction_qq, new_rep_front_to_global_3ds)

        return rotated_to_3ds[to_bone_name], rep_to_global_3ds[to_bone_name], rep_base_pos

    # スタンス用細分化
    def prepare_split_stance(self, target_bone_name):
        motion = self.options.motion_vmd_data
        fnos = motion.get_bone_fnos(target_bone_name)

        for fidx, fno in enumerate(fnos):
            if fidx == 0:
                continue

            prev_bf = motion.bones[target_bone_name][fnos[fidx - 1]]
            bf = motion.bones[target_bone_name][fno]

            # 内積で離れ具合をチェック
            dot = prev_bf.rotation.dotProduct(bf)
            if abs(dot) < 0.17:
                # 回転量が160度以上の場合、半分に分割しておく
                half_fno = prev_bf.fno + round((bf.fno - prev_bf.fno) / 2)

                if bf.fno < half_fno < prev_bf.fno:
                    # キーが追加できる状態であれば、追加
                    # 補間曲線込みでキーフレーム生成
                    fill_bf = motion.calc_bf(target_bone_name, half_fno)
                    fill_bf.key = True

                    motion.bones[target_bone_name][half_fno] = fill_bf
        
                    # モーション再設定
                    MBezierUtils.reset_interpolation_by_rot(motion, target_bone_name, prev_bf, fill_bf, bf)
    
    # 腕スタンス補正
    def adjust_arm_stance(self, data_set_idx: int, data_set: MOptionsDataSet):
        logger.info("腕スタンス補正　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)
        
        # 腕のスタンス差
        arm_diff_qq_dic = self.calc_arm_stance(data_set)

        for direction in ["左", "右"]:
            for bone_type in ["腕", "ひじ", "手首"]:
                bone_name = "{0}{1}".format(direction, bone_type)

                if bone_name in arm_diff_qq_dic and bone_name in data_set.motion_vmd_data.bones:
                    # スタンス補正値がある場合
                    for bf in data_set.motion_vmd_data.bones[bone_name].values():
                        if bf.key:
                            if arm_diff_qq_dic[bone_name]["from"] == MQuaternion():
                                bf.rotation = bf.rotation * arm_diff_qq_dic[bone_name]["to"]
                            else:
                                bf.rotation = arm_diff_qq_dic[bone_name]["from"].inverted() * bf.rotation * arm_diff_qq_dic[bone_name]["to"]
                    
                    logger.info("スタンス補正: %s", bone_name, decoration=MLogger.DECORATION_SIMPLE)
                    logger.test("from: %s", arm_diff_qq_dic[bone_name]["from"].toEulerAngles())
                    logger.test("to: %s", arm_diff_qq_dic[bone_name]["to"].toEulerAngles())

    def calc_arm_stance(self, data_set: MOptionsDataSet):
        arm_diff_qq_dic = {}

        for direction in ["左", "右"]:
            for from_bone_type, target_bone_type, to_bone_type in [(None, "腕", "ひじ"), ("腕", "ひじ", "手首"), ("ひじ", "手首", "中指１")]:
                from_bone_name = "{0}{1}".format(direction, from_bone_type) if from_bone_type else None
                target_bone_name = "{0}{1}".format(direction, target_bone_type)
                to_bone_name = "{0}{1}".format(direction, to_bone_type)

                if from_bone_name:
                    bone_names = [from_bone_name, target_bone_name, to_bone_name]
                else:
                    bone_names = [target_bone_name, to_bone_name]

                if set(bone_names).issubset(data_set.org_model_data.bones) and set(bone_names).issubset(data_set.rep_model_data.bones):
                    # 対象ボーンが揃っている場合（念のためバラバラにチェック）

                    # 揃ってたら辞書登録
                    arm_diff_qq_dic[target_bone_name] = {}

                    if from_bone_name:
                        # FROM-TARGETの傾き
                        _, org_from_qq = MServiceUtils.calc_arm_stance_diff(data_set.org_model_data, from_bone_name, target_bone_name)
                        _, rep_from_qq = MServiceUtils.calc_arm_stance_diff(data_set.rep_model_data, from_bone_name, target_bone_name)

                        arm_diff_qq_dic[target_bone_name]["from"] = rep_from_qq.inverted() * org_from_qq
                    else:
                        arm_diff_qq_dic[target_bone_name]["from"] = MQuaternion()

                    # TARGET-TOの傾き
                    _, org_to_qq = MServiceUtils.calc_arm_stance_diff(data_set.org_model_data, target_bone_name, to_bone_name)
                    _, rep_to_qq = MServiceUtils.calc_arm_stance_diff(data_set.rep_model_data, target_bone_name, to_bone_name)

                    arm_diff_qq_dic[target_bone_name]["to"] = rep_to_qq.inverted() * org_to_qq
        
        return arm_diff_qq_dic


