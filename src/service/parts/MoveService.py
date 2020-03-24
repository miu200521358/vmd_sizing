# -*- coding: utf-8 -*-
#

from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MOptions, MOptionsDataSet
from utils import MUtils, MServiceUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__, level=1)


class MoveService():
    def __init__(self, options: MOptions):
        self.options = options

    def execute(self):
        for data_set_idx, data_set in enumerate(self.options.data_set_list):
            if data_set.motion_vmd_data.motion_cnt <= 0:
                # モーションデータが無い場合、処理スキップ
                return True

            logger.info("移動補正　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)

            # センターのZ軸オフセットを計算
            self.set_center_z_offset(data_set)

            for k in ["右足ＩＫ", "左足ＩＫ", "右つま先ＩＫ", "左つま先ＩＫ", "右足ＩＫ親", "左足ＩＫ親", "右足IK親", "左足IK親", "センター", "グルーブ", "全ての親"]:
                if k in data_set.motion_vmd_data.frames and k in data_set.rep_model_data.bones:
                    for bf in data_set.motion_vmd_data.frames[k].values():
                        # IK比率をそのまま掛ける
                        bf.position.setX(bf.position.x() * data_set.xz_ratio)
                        bf.position.setY(bf.position.y() * data_set.y_ratio)
                        bf.position.setZ(bf.position.z() * data_set.xz_ratio)

                        # オフセット調整
                        bf.position += data_set.rep_model_data.bones[k].local_offset

                    if len(data_set.motion_vmd_data.frames[k].keys()) > 0:
                        logger.info("移動補正: %s", k, decoration=MLogger.DECORATION_SIMPLE)

        return True

    # センターZオフセット計算
    def set_center_z_offset(self, data_set: MOptionsDataSet):
        target_bones = ["左つま先ＩＫ", "左足", "左足首", "センター"]

        if set(target_bones).issubset(data_set.org_model_data.bones) and set(target_bones).issubset(data_set.rep_model_data.bones):
            # 作成元センターのZ位置
            org_center_z = data_set.org_model_data.bones["センター"].position.z()
            logger.test("org_center_z: %s", org_center_z)
            # 作成元左足首のZ位置
            org_ankle_z = data_set.org_model_data.bones["左足首"].position.z()
            logger.test("org_ankle_z: %s", org_ankle_z)
            # 作成元左足のZ位置
            org_leg_z = data_set.org_model_data.bones["左足"].position.z()
            logger.test("org_leg_z: %s", org_leg_z)
            # 作成元つま先のZ位置
            org_toe_z = data_set.org_model_data.left_toe_vertex.position.z()
            logger.test("org_toe_z: %s", org_toe_z)

            # 変換先センターのZ位置
            rep_center_z = data_set.rep_model_data.bones["センター"].position.z()
            logger.test("rep_center_z: %s", rep_center_z)
            # 変換先左足首のZ位置
            rep_ankle_z = data_set.rep_model_data.bones["左足首"].position.z()
            logger.test("rep_ankle_z: %s", rep_ankle_z)
            # 変換先左足のZ位置
            rep_leg_z = data_set.rep_model_data.bones["左足"].position.z()
            logger.test("rep_leg_z: %s", rep_leg_z)
            # 変換先つま先のZ位置
            rep_toe_z = data_set.rep_model_data.left_toe_vertex.position.z()
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

            local_offset = MVector3D(0, 0, (rep_center_gravity - org_center_gravity) * (rep_leg_zlength / org_leg_zlength))
            data_set.rep_model_data.bones["センター"].local_offset = local_offset
            logger.test("local_offset %s", data_set.rep_model_data.bones["センター"].local_offset)

            logger.info("Zオフセット: %s: %s", "センター", local_offset.z(), decoration=MLogger.DECORATION_SIMPLE)

            return

        logger.info("Zオフセットなし", decoration=MLogger.DECORATION_SIMPLE)



