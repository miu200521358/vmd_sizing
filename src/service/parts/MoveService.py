# -*- coding: utf-8 -*-
#

from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
import module.MOptions as MOptions

from utils import MUtils, MServiceUtils # noqa
import utils.MLogger as MLogger # noqa

logger = MLogger(__name__)


class MoveService():
    def __init__(self, options: MOptions):
        self.options = options

    def execute(self, org_motion_frames):
        if self.options.motion_vmd_data.motion_cnt <= 0:
            # モーションデータが無い場合、処理スキップ
            return True

        logger.info("移動補正", decoration=MLogger.DECORATION_LINE)

        # 足IKのXYZの比率
        xz_ratio, y_ratio = MServiceUtils.calc_leg_ik_ratio(self.options)
        
        # センターのZ軸オフセットを計算
        self.cal_center_z_offset()

        for k in ["右足ＩＫ", "左足ＩＫ", "右つま先ＩＫ", "左つま先ＩＫ", "右足ＩＫ親", "左足ＩＫ親", "右足IK親", "左足IK親", "センター", "グルーブ", "全ての親"]:
            if k in self.options.motion_vmd_data.frames and k in self.options.rep_model_data.bones:
                for bf in self.options.motion_vmd_data.frames[k].values():
                    # IK比率をそのまま掛ける
                    bf.position.setX(bf.position.x() * xz_ratio)
                    bf.position.setY(bf.position.y() * y_ratio)
                    bf.position.setZ(bf.position.z() * xz_ratio)

                if self.options.rep_model_data.bones[k].local_offset != MVector3D():
                    # ローカルZオフセットが入っている場合、オフセット調整
                    bf.position += self.options.rep_model_data.bones[k].local_offset

        return True

    # センターZオフセット計算
    def cal_center_z_offset(self):
        target_bones = ["左つま先ＩＫ", "左足", "左足首", "センター"]

        if set(target_bones).issubset(self.options.org_model_data.bones) and set(target_bones).issubset(self.options.rep_model_data.bones):
            # 作成元センターのZ位置
            org_center_z = self.options.org_model_data.bones["センター"].position.z()
            logger.test("org_center_z: %s", org_center_z)
            # 作成元左足首のZ位置
            org_ankle_z = self.options.org_model_data.bones["左足首"].position.z()
            logger.test("org_ankle_z: %s", org_ankle_z)
            # 作成元左足のZ位置
            org_leg_z = self.options.org_model_data.bones["左足"].position.z()
            logger.test("org_leg_z: %s", org_leg_z)
            # 作成元つま先のZ位置
            org_toe_z = self.options.org_model_data.get_toe_vertex_position().z()
            # org_toe_z = self.options.org_model_data.bones["左つま先ＩＫ"].position.z()
            logger.test("org_toe_z: %s", org_toe_z)

            # 変換先センターのZ位置
            rep_center_z = self.options.rep_model_data.bones["センター"].position.z()
            logger.test("rep_center_z: %s", rep_center_z)
            # 変換先左足首のZ位置
            rep_ankle_z = self.options.rep_model_data.bones["左足首"].position.z()
            logger.test("rep_ankle_z: %s", rep_ankle_z)
            # 変換先左足のZ位置
            rep_leg_z = self.options.rep_model_data.bones["左足"].position.z()
            logger.test("rep_leg_z: %s", rep_leg_z)
            # 変換先つま先のZ位置
            rep_toe_z = self.options.rep_model_data.get_toe_vertex_position().z()
            # rep_toe_z = self.options.rep_model_data.bones["左つま先ＩＫ"].position.z()
            logger.test("rep_toe_z: %s", rep_toe_z)

            # 作成元の足の長さ
            org_leg_zlength = org_ankle_z - org_toe_z
            # 作成元の重心
            org_center_gravity = (org_ankle_z - org_leg_z) / (org_ankle_z - org_toe_z)
            logger.test("org_center_gravity %s, org_leg_zlength: %s", org_center_gravity, org_leg_zlength)

            # 変換先の足の長さ
            rep_leg_zlength = rep_ankle_z - rep_toe_z
            # 変換先の重心
            rep_center_gravity = (rep_ankle_z - rep_leg_z) / (rep_ankle_z - rep_toe_z)
            logger.test("rep_center_gravity %s, rep_leg_zlength: %s", rep_center_gravity, rep_leg_zlength)

            self.options.rep_model_data.bones["センター"].local_offset = MVector3D(0, 0, (rep_center_gravity - org_center_gravity) * (rep_leg_zlength / org_leg_zlength))
            logger.test("local_offset %s", self.options.rep_model_data.bones["センター"].local_offset)





