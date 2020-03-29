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
            if data_set.motion.motion_cnt <= 0:
                # モーションデータが無い場合、処理スキップ
                continue
            
            # 代替モデルでない場合
            if not data_set.substitute_model_flg:
                # センタースタンス補正
                self.adjust_center_stance(data_set_idx, data_set)

                # 上半身スタンス補正
                self.adjust_upper_stance(data_set_idx, data_set)

            # 腕系サイジング可能であれば、腕スタンス補正
            if data_set.org_model.can_arm_sizing and data_set.rep_model.can_arm_sizing:
                self.adjust_arm_stance(data_set_idx, data_set)
            else:
                target_model_type = ""

                if not data_set.org_model.can_arm_sizing:
                    target_model_type = "作成元"

                if not data_set.rep_model.can_arm_sizing:
                    if len(target_model_type) > 0:
                        target_model_type = target_model_type + "/"
                    
                    target_model_type = target_model_type + "変換先"

                logger.warning("%sモデルの腕構造にサイジングが対応していない為、腕スタンス補正をスキップします。", target_model_type, decoration=MLogger.DECORATION_BOX)

        return True
        
    # センタースタンス補正
    def adjust_center_stance(self, data_set_idx: int, data_set: MOptionsDataSet):
        logger.info("センタースタンス補正　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)

        # センター調整に必要なボーン群
        center_target_bones = ["センター", "上半身", "下半身", "左足ＩＫ", "右足ＩＫ", "左足", "右足"]

        if set(center_target_bones).issubset(data_set.org_model.bones) and set(center_target_bones).issubset(data_set.rep_model.bones) and "センター" in data_set.motion.bones:
            # 判定用のセンターボーン名（グルーブがある場合、グルーブまでを対象とする）
            org_center_bone_name = "グルーブ" if "グルーブ" in data_set.org_model.bones else "センター"
            rep_center_bone_name = "グルーブ" if "グルーブ" in data_set.rep_model.bones else "センター"

            # 元モデルのリンク生成
            org_center_links = data_set.org_model.create_link_2_top_one(org_center_bone_name)
            org_leg_ik_links = data_set.org_model.create_link_2_top_lr("足ＩＫ")
            org_leg_links = data_set.org_model.create_link_2_top_lr("足")

            # 変換先モデルのリンク生成
            rep_center_links = data_set.rep_model.create_link_2_top_one(rep_center_bone_name)
            rep_leg_ik_links = data_set.rep_model.create_link_2_top_lr("足ＩＫ")
            rep_leg_links = data_set.rep_model.create_link_2_top_lr("足")

            # 準備（細分化）
            self.prepare_split_stance(data_set_idx, data_set, "センター")

            logger.info("センタースタンス準備終了")

            prev_fno = 0
            for fno in data_set.motion.get_bone_fnos("センター"):
                bf = data_set.motion.bones["センター"][fno]
                if bf.key:
                    logger.debug("f: %s, 調整前: %s", bf.fno, bf.position)
                    bf.position += self.calc_center_offset_by_leg_ik(bf, data_set_idx, data_set, \
                                                                     org_center_links, org_leg_ik_links, rep_center_links, rep_leg_ik_links, \
                                                                     org_center_bone_name, rep_center_bone_name)
                    logger.debug("f: %s, 足IKオフセット後: %s", bf.fno, bf.position)

                if fno // 500 > prev_fno:
                    logger.info("-- %sフレーム目完了", fno)
                    prev_fno = fno // 500

    # 足IKによるセンターオフセット値
    def calc_center_offset_by_leg_ik(self, bf: VmdBoneFrame, data_set_idx: int, data_set: MOptionsDataSet, \
                                     org_center_links: BoneLinks, org_leg_ik_links: BoneLinks, \
                                     rep_center_links: BoneLinks, rep_leg_ik_links: BoneLinks, \
                                     org_center_bone_name: str, rep_center_bone_name: str):

        # 元モデルのセンターオフセット
        org_center_ik_offset = self.calc_center_offset_by_leg_ik_parts(bf, data_set_idx, data_set, data_set.org_model, data_set.org_motion, \
                                                                       org_center_links, org_leg_ik_links, org_center_bone_name)
        logger.test("f: %s, org_center_ik_offset: %s", bf.fno, org_center_ik_offset)

        # 先モデルのセンターオフセット
        rep_center_ik_offset = self.calc_center_offset_by_leg_ik_parts(bf, data_set_idx, data_set, data_set.rep_model, data_set.motion, \
                                                                       rep_center_links, rep_leg_ik_links, rep_center_bone_name)
        logger.test("f: %s, rep_center_ik_offset: %s", bf.fno, rep_center_ik_offset)
        
        # 元モデルに本来のXZ比率をかけて、それと先モデルの差をオフセットとする
        center_ik_offset = rep_center_ik_offset - (org_center_ik_offset * data_set.original_xz_ratio)
        logger.debug("f: %s, center_ik_offset: %s", bf.fno, center_ik_offset)

        return center_ik_offset

    def calc_center_offset_by_leg_ik_parts(self, bf: VmdBoneFrame, data_set_idx: int, data_set: MOptionsDataSet, \
                                           model: PmxModel, motion: VmdMotion, \
                                           center_links: BoneLinks, leg_ik_links: BoneLinks, center_bone_name: str):

        # センターまでの位置
        center_global_3ds, front_center_global_3ds, center_direction_qq = \
            MServiceUtils.calc_front_global_pos(model, center_links, motion, bf.fno)

        # 左足IKまでの位置
        left_leg_ik_global_3ds, front_left_leg_ik_global_3ds, left_leg_ik_direction_qq = \
            MServiceUtils.calc_front_global_pos(model, leg_ik_links["左"], motion, bf.fno)

        # 右足IKまでの位置
        right_leg_ik_global_3ds, front_right_leg_ik_global_3ds, right_leg_ik_direction_qq = \
            MServiceUtils.calc_front_global_pos(model, leg_ik_links["右"], motion, bf.fno)
        
        global_center_pos = front_center_global_3ds[center_bone_name]
        global_left_ik_pos = front_left_leg_ik_global_3ds["左足ＩＫ"]
        global_right_ik_pos = front_right_leg_ik_global_3ds["右足ＩＫ"]

        # 足IKの中間とセンターの差分をオフセットとする
        center_ik_offset = ((global_left_ik_pos + global_right_ik_pos) / 2 - global_center_pos)
        center_ik_offset.effective()
        center_ik_offset.setY(0)

        return center_ik_offset

    # 上半身スタンス補正
    def adjust_upper_stance(self, data_set_idx: int, data_set: MOptionsDataSet):
        logger.info("上半身スタンス補正　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)

        # 上半身調整に必要なボーン群
        upper_target_bones = ["上半身", "頭", "首", "左腕", "右腕"]

        # 上半身2調整に必要なボーン群
        upper2_target_bones = ["上半身", "上半身2", "頭", "首", "左腕", "右腕"]

        # モデルとモーション全部に上半身2がある場合、TRUE
        is_upper2_existed = set(upper2_target_bones).issubset(data_set.org_model.bones) and set(upper2_target_bones).issubset(data_set.rep_model.bones) \
            and "上半身2" in data_set.motion.bones and len(data_set.motion.bones["上半身2"]) > 1

        if set(upper_target_bones).issubset(data_set.org_model.bones) and set(upper_target_bones).issubset(data_set.rep_model.bones) and "上半身" in data_set.motion.bones:
            # 元モデルのリンク生成
            org_head_links = data_set.org_model.create_link_2_top_one("頭")
            org_upper_links = data_set.org_model.create_link_2_top_one("上半身")
            org_arm_links = data_set.org_model.create_link_2_top_lr("腕")

            # 変換先モデルのリンク生成
            rep_head_links = data_set.rep_model.create_link_2_top_one("頭")
            rep_upper_links = data_set.rep_model.create_link_2_top_one("上半身")
            rep_arm_links = data_set.rep_model.create_link_2_top_lr("腕")

            # 元モデルの上半身の傾き
            org_upper_slope = (data_set.org_model.bones["頭"].position - data_set.org_model.bones["上半身"].position).normalized()

            # 上半身からTO_BONEへの傾き
            rep_upper_slope = (data_set.rep_model.bones["頭"].position - data_set.rep_model.bones["上半身"].position).normalized()
            rep_upper_slope_up = MVector3D(-1, 0, 0)
            rep_upper_slope_cross = MVector3D.crossProduct(rep_upper_slope, rep_upper_slope_up).normalized()
            
            logger.test("上半身 slope: %s", rep_upper_slope)
            logger.test("上半身 cross: %s", rep_upper_slope_cross)

            # 上半身の傾き度合い - 0.1 を変化量の上限とする
            dot_limit = MVector3D.dotProduct(org_upper_slope.normalized(), rep_upper_slope.normalized()) - 0.1

            rep_upper_initial_slope_qq = MQuaternion.fromDirection(rep_upper_slope, rep_upper_slope_cross)

            # 準備（細分化）
            self.prepare_split_stance(data_set_idx, data_set, "上半身")

            logger.info("上半身スタンス準備終了")

            prev_fno = 0
            for fno in data_set.motion.get_bone_fnos("上半身"):
                bf = data_set.motion.bones["上半身"][fno]
                if bf.key:
                    self.calc_rotation_stance(bf, data_set_idx, data_set, \
                                              org_upper_links, org_upper_links, org_head_links, org_head_links, org_arm_links, \
                                              rep_upper_links, rep_upper_links, rep_head_links, rep_head_links, rep_arm_links, \
                                              "", "上半身", "上半身", "頭", rep_upper_initial_slope_qq, self.def_calc_up_upper, dot_limit)
                if fno // 500 > prev_fno:
                    logger.info("-- %sフレーム目完了", fno)
                    prev_fno = fno // 500

            # 子の角度調整
            self.adjust_rotation_by_parent(data_set_idx, data_set, "首", "上半身")
            self.adjust_rotation_by_parent(data_set_idx, data_set, "左腕", "上半身")
            self.adjust_rotation_by_parent(data_set_idx, data_set, "右腕", "上半身")

            logger.info("上半身スタンス終了")

            if is_upper2_existed:
                # 上半身2がある場合
                # 元モデルのリンク生成
                org_head_links = data_set.org_model.create_link_2_top_one("頭")
                org_upper2_links = data_set.org_model.create_link_2_top_one("上半身2")

                # 変換先モデルのリンク生成
                rep_head_links = data_set.rep_model.create_link_2_top_one("頭")
                rep_upper2_links = data_set.rep_model.create_link_2_top_one("上半身2")

                # 元モデルの上半身2の傾き
                org_upper2_slope = (data_set.org_model.bones["頭"].position - data_set.org_model.bones["上半身2"].position).normalized()

                # 上半身からTO_BONEへの傾き
                rep_upper2_slope = (data_set.rep_model.bones["頭"].position - data_set.rep_model.bones["上半身2"].position).normalized()
                rep_upper2_slope_up = MVector3D(-1, 0, 0)
                rep_upper2_slope_cross = MVector3D.crossProduct(rep_upper2_slope, rep_upper2_slope_up).normalized()
                
                logger.test("上半身 slope: %s", rep_upper2_slope)
                logger.test("上半身 cross: %s", rep_upper2_slope_cross)

                # 上半身2の傾き度合い - 0.1 を変化量の上限とする
                dot2_limit = MVector3D.dotProduct(org_upper2_slope.normalized(), rep_upper2_slope.normalized()) - 0.1

                rep_upper2_initial_slope_qq = MQuaternion.fromDirection(rep_upper2_slope, rep_upper2_slope_cross)

                # 準備（細分化）
                self.prepare_split_stance(data_set_idx, data_set, "上半身2")

                logger.info("上半身2スタンス準備終了")

                prev_fno = 0
                for fno in data_set.motion.get_bone_fnos("上半身2"):
                    bf = data_set.motion.bones["上半身2"][fno]
                    if bf.key:
                        self.calc_rotation_stance(bf, data_set_idx, data_set, \
                                                  org_upper2_links, org_upper2_links, org_head_links, org_head_links, org_arm_links, \
                                                  rep_upper2_links, rep_upper2_links, rep_head_links, rep_head_links, rep_arm_links, \
                                                  "", "上半身2", "上半身2", "頭", rep_upper2_initial_slope_qq, self.def_calc_up_upper, dot2_limit)

                    if fno // 500 > prev_fno:
                        logger.info("-- %sフレーム目完了", fno)
                        prev_fno = fno // 500

                # 子の角度調整
                self.adjust_rotation_by_parent(data_set_idx, data_set, "首", "上半身2")
                self.adjust_rotation_by_parent(data_set_idx, data_set, "左腕", "上半身2")
                self.adjust_rotation_by_parent(data_set_idx, data_set, "右腕", "上半身2")

                logger.info("上半身2スタンス終了")

    # 指定したボーンを親ボーンの調整量に合わせてオフセット
    def adjust_rotation_by_parent(self, data_set_idx: int, data_set: MOptionsDataSet, target_bone_name: str, target_parent_name: str):
        for fno in data_set.motion.get_bone_fnos(target_bone_name):
            bf = data_set.motion.bones[target_bone_name][fno]
            if bf.key:
                # 元々の親bf
                org_parent_bf = data_set.org_motion.calc_bf(target_parent_name, fno)
                # 調整後の親bf
                rep_parent_bf = data_set.motion.calc_bf(target_parent_name, fno)

                bf.rotation = rep_parent_bf.rotation.inverted() * org_parent_bf.rotation * bf.rotation
    
    # 定義: 傾きを求める方向の位置計算（上半身）
    def def_calc_up_upper(self, bf: VmdBoneFrame, data_set_idx: int, data_set: MOptionsDataSet, org_from_links: BoneLinks, org_head_links: BoneLinks, org_arm_links: BoneLinks):
        # 左腕ボーンまでの位置
        org_left_arm_global_3ds = MServiceUtils.calc_global_pos(data_set.org_model, org_arm_links["左"], data_set.org_motion, bf.fno, org_from_links)
        org_left_arm_pos = org_left_arm_global_3ds["左腕"]
        logger.test("f: %s, org_left_arm_pos: %s", bf.fno, org_left_arm_pos)

        # 右腕ボーンまでの位置
        org_right_arm_global_3ds = MServiceUtils.calc_global_pos(data_set.org_model, org_arm_links["右"], data_set.org_motion, bf.fno, org_from_links)
        org_right_arm_pos = org_right_arm_global_3ds["右腕"]
        logger.test("f: %s, org_right_arm_pos: %s", bf.fno, org_right_arm_pos)
        
        return org_right_arm_pos - org_left_arm_pos

    # スタンス補正
    def calc_rotation_stance(self, bf: VmdBoneFrame, data_set_idx: int, data_set: MOptionsDataSet, \
                             org_base_links: BoneLinks, org_from_links: BoneLinks, org_to_links: BoneLinks, org_head_links: BoneLinks, org_arm_links: BoneLinks, \
                             rep_base_links: BoneLinks, rep_from_links: BoneLinks, rep_to_links: BoneLinks, rep_head_links: BoneLinks, rep_arm_links: BoneLinks, \
                             direction_name: str, base_bone_name: str, from_bone_name: str, to_bone_name: str, rep_initial_slope_qq: MQuaternion, \
                             def_calc_up, dot_limit):
        logger.test("f: %s -----------------------------", bf.fno)

        target_base_bone_name = "{0}{1}".format(direction_name, base_bone_name)
        target_from_bone_name = "{0}{1}".format(direction_name, from_bone_name)
        target_to_bone_name = "{0}{1}".format(direction_name, to_bone_name)

        # 基準の親ボーン
        base_parent_bone_name = rep_base_links.get(target_base_bone_name, offset=-1).name
        # 基準より親の回転量
        parent_qq = MServiceUtils.calc_direction_qq(data_set.rep_model, rep_base_links.from_links(base_parent_bone_name), data_set.motion, bf.fno)

        # -------------

        # TO位置の再計算
        new_rep_to_pos, rep_to_pos, rep_base_pos = self.recalc_to_pos(bf, data_set_idx, data_set, \
                                                                      org_base_links, org_from_links, org_to_links, org_arm_links, \
                                                                      rep_base_links, rep_from_links, rep_to_links, rep_arm_links, \
                                                                      base_bone_name, from_bone_name, to_bone_name)

        # UP方向の再計算（元モデルで計算する）
        up_pos = def_calc_up(bf, data_set_idx, data_set, org_from_links, org_head_links, org_arm_links)

        # ---------------
        # FROMの回転量を再計算する
        direction = new_rep_to_pos - rep_base_pos
        up = MVector3D.crossProduct(direction, up_pos)
        from_orientation = MQuaternion.fromDirection(direction.normalized(), up.normalized())
        initial = rep_initial_slope_qq
        from_rotation = parent_qq.inverted() * from_orientation * initial.inverted()
        from_rotation.normalize()
        logger.test("f: %s, rep_base_pos(%s): %s", bf.fno, target_base_bone_name, rep_base_pos)
        logger.test("f: %s, rep_to_pos(%s): %s", bf.fno, target_to_bone_name, new_rep_to_pos)
        logger.test("f: %s, 元rep_to_pos(%s): %s", bf.fno, target_to_bone_name, rep_to_pos)
        logger.test("f: %s, up_pos: %s", bf.fno, up_pos)
        logger.test("f: %s, parent: %s", bf.fno, parent_qq.toEulerAngles4MMD())
        logger.test("f: %s, initial: %s", bf.fno, initial.toEulerAngles4MMD())
        logger.test("f: %s, orientation: %s", bf.fno, from_orientation.toEulerAngles4MMD())
        logger.debug("f: %s, 補正回転: %s", bf.fno, from_rotation.toEulerAngles4MMD())

        org_bf = data_set.org_motion.calc_bf(target_from_bone_name, bf.fno)
        logger.debug("f: %s, 元の回転: %s", bf.fno, org_bf.rotation.toEulerAngles4MMD())

        if org_bf:
            # 元にもあるキーである場合、内積チェック
            uad = abs(MQuaternion.dotProduct(from_rotation, org_bf.rotation))
            logger.test("f: %s, uad: %s", bf.fno, uad)
            if uad < dot_limit:
                # 内積が離れすぎてたらNG
                logger.warning("%sフレーム目%sスタンス補正失敗: 角度:%s, uad: %s", bf.fno, target_from_bone_name, from_rotation.toEulerAngles(), uad)
            else:
                # 内積の差が小さい場合、回転適用
                bf.rotation = from_rotation
        else:
            # 元にもない場合（ないはず）、はそのまま設定
            bf.rotation = from_rotation

    # TO位置の再計算処理
    def recalc_to_pos(self, bf: VmdBoneFrame, data_set_idx: int, data_set: MOptionsDataSet, \
                      org_base_links: BoneLinks, org_from_links: BoneLinks, org_to_links: BoneLinks, org_arm_links: BoneLinks, \
                      rep_base_links: BoneLinks, rep_from_links: BoneLinks, rep_to_links: BoneLinks, rep_arm_links: BoneLinks, \
                      base_bone_name: str, from_bone_name: str, to_bone_name: str):

        # 基準ボーンまでの位置
        org_base_global_3ds, org_front_base_global_3ds, org_base_direction_qq = \
            MServiceUtils.calc_front_global_pos(data_set.org_model, org_base_links, data_set.org_motion, bf.fno, org_from_links)
        rep_base_global_3ds, rep_front_base_global_3ds, rep_base_direction_qq = \
            MServiceUtils.calc_front_global_pos(data_set.rep_model, rep_base_links, data_set.motion, bf.fno, rep_from_links)

        # # 基準ボーンの位置
        # org_base_pos = org_base_global_3ds[base_bone_name]
        rep_base_pos = rep_base_global_3ds[base_bone_name]

        # 正面向きの基準ボーンの位置
        org_front_base_pos = org_front_base_global_3ds[base_bone_name]
        rep_front_base_pos = rep_front_base_global_3ds[base_bone_name]

        # -------------

        # TOボーンまでの位置（フレームはFROMまでで、TO自身は初期値として求める）
        org_to_global_3ds, org_front_to_global_3ds, org_to_direction_qq = \
            MServiceUtils.calc_front_global_pos(data_set.org_model, org_to_links, data_set.org_motion, bf.fno, org_from_links)
        rep_to_global_3ds, rep_front_to_global_3ds, rep_to_direction_qq = \
            MServiceUtils.calc_front_global_pos(data_set.rep_model, rep_to_links, data_set.motion, bf.fno, rep_from_links)

        # TOボーンの正面位置
        org_front_to_pos = org_front_to_global_3ds[to_bone_name]
        rep_front_to_pos = rep_front_to_global_3ds[to_bone_name]

        # -------------

        # 肩幅比率
        org_arm_diff = (org_arm_links["左"].get("左腕").position - org_arm_links["右"].get("右腕").position)
        rep_arm_diff = (rep_arm_links["左"].get("左腕").position - rep_arm_links["右"].get("右腕").position)
        arm_diff_ratio = rep_arm_diff / org_arm_diff

        # TOの長さ比率
        org_to_diff = (org_to_links.get(to_bone_name).position - org_base_links.get(base_bone_name).position)
        org_to_diff.abs()
        rep_to_diff = (rep_to_links.get(to_bone_name).position - rep_base_links.get(base_bone_name).position)
        rep_to_diff.abs()
        to_diff_ratio = rep_to_diff.length() / org_to_diff.length()

        logger.test("f: %s, arm_diff_ratio: %s", bf.fno, arm_diff_ratio)
        logger.test("f: %s, to_diff_ratio: %s", bf.fno, to_diff_ratio)

        # ---------------
        
        rep_front_to_x = rep_front_base_pos.x() + ((org_front_to_pos.x() - org_front_base_pos.x()) * arm_diff_ratio.x())
        rep_front_to_y = rep_front_base_pos.y() + ((org_front_to_pos.y() - org_front_base_pos.y()) * to_diff_ratio)
        rep_front_to_z = rep_front_base_pos.z() + ((org_front_to_pos.z() - org_front_base_pos.z()) * to_diff_ratio)

        logger.test("f: %s, rep_front_base_pos: %s", bf.fno, rep_front_base_pos)
        logger.test("f: %s, org_front_to_pos: %s", bf.fno, org_front_to_pos)
        logger.test("f: %s, org_front_base_pos: %s", bf.fno, org_front_base_pos)

        new_rep_front_to_pos = MVector3D(rep_front_to_x, rep_front_to_y, rep_front_to_z)
        logger.test("f: %s, 計算new_rep_front_to_pos: %s", bf.fno, new_rep_front_to_pos)
        logger.test("f: %s, 元rep_front_to_pos: %s", bf.fno, rep_front_to_pos)

        # 正面向きの新しいTO位置
        new_rep_front_to_global_3ds = copy.deepcopy(rep_front_to_global_3ds)
        new_rep_front_to_global_3ds[to_bone_name] = new_rep_front_to_pos

        # 回転を元に戻した位置
        rotated_to_3ds = MServiceUtils.calc_global_pos_by_direction(rep_to_direction_qq, new_rep_front_to_global_3ds)

        return rotated_to_3ds[to_bone_name], rep_to_global_3ds[to_bone_name], rep_base_pos

    # スタンス用細分化
    def prepare_split_stance(self, data_set_idx: int, data_set: MOptionsDataSet, target_bone_name: str):
        motion = data_set.motion
        fnos = motion.get_bone_fnos(target_bone_name)

        for fidx, fno in enumerate(fnos):
            if fidx == 0:
                continue

            prev_bf = motion.bones[target_bone_name][fnos[fidx - 1]]
            bf = motion.bones[target_bone_name][fno]

            # 内積で離れ具合をチェック
            dot = MQuaternion.dotProduct(prev_bf.rotation, bf.rotation)
            if abs(dot) < 0.2:
                # 回転量が約150度以上の場合、半分に分割しておく
                half_fno = prev_bf.fno + round((bf.fno - prev_bf.fno) / 2)

                if bf.fno < half_fno < prev_bf.fno:
                    # キーが追加できる状態であれば、追加
                    motion.split_bf_by_fno(target_bone_name, prev_bf, bf, half_fno)

    # 腕スタンス補正
    def adjust_arm_stance(self, data_set_idx: int, data_set: MOptionsDataSet):
        logger.info("腕スタンス補正　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)
        
        # 腕のスタンス差
        arm_diff_qq_dic = self.calc_arm_stance(data_set)

        for direction in ["左", "右"]:
            for bone_type in ["腕", "ひじ", "手首"]:
                bone_name = "{0}{1}".format(direction, bone_type)

                if bone_name in arm_diff_qq_dic and bone_name in data_set.motion.bones:
                    # スタンス補正値がある場合
                    for bf in data_set.motion.bones[bone_name].values():
                        if bf.key:
                            if arm_diff_qq_dic[bone_name]["from"] == MQuaternion():
                                bf.rotation = bf.rotation * arm_diff_qq_dic[bone_name]["to"]
                            else:
                                bf.rotation = arm_diff_qq_dic[bone_name]["from"].inverted() * bf.rotation * arm_diff_qq_dic[bone_name]["to"]
                    
                    logger.info("スタンス補正: %s", bone_name)
                    logger.test("from: %s", arm_diff_qq_dic[bone_name]["from"].toEulerAngles())
                    logger.test("to: %s", arm_diff_qq_dic[bone_name]["to"].toEulerAngles())

    # 腕スタンス補正用傾き計算
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

                if set(bone_names).issubset(data_set.org_model.bones) and set(bone_names).issubset(data_set.rep_model.bones):
                    # 対象ボーンが揃っている場合（念のためバラバラにチェック）

                    # 揃ってたら辞書登録
                    arm_diff_qq_dic[target_bone_name] = {}

                    if from_bone_name:
                        # FROM-TARGETの傾き
                        _, org_from_qq = MServiceUtils.calc_arm_stance_diff(data_set.org_model, from_bone_name, target_bone_name)
                        _, rep_from_qq = MServiceUtils.calc_arm_stance_diff(data_set.rep_model, from_bone_name, target_bone_name)

                        arm_diff_qq_dic[target_bone_name]["from"] = rep_from_qq.inverted() * org_from_qq
                    else:
                        arm_diff_qq_dic[target_bone_name]["from"] = MQuaternion()

                    # TARGET-TOの傾き
                    _, org_to_qq = MServiceUtils.calc_arm_stance_diff(data_set.org_model, target_bone_name, to_bone_name)
                    _, rep_to_qq = MServiceUtils.calc_arm_stance_diff(data_set.rep_model, target_bone_name, to_bone_name)

                    arm_diff_qq_dic[target_bone_name]["to"] = rep_to_qq.inverted() * org_to_qq
        
        return arm_diff_qq_dic


