# -*- coding: utf-8 -*-
#
import numpy as np
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
            if data_set.motion.motion_cnt <= 0:
                # モーションデータが無い場合、処理スキップ
                return True

            logger.info("移動補正　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)

            # センターのZ軸オフセットを計算
            self.set_center_z_offset(data_set)

            # 足IKのオフセットを計算
            self.set_leg_ik_offset(data_set)

            for k in ["右足ＩＫ", "左足ＩＫ", "右つま先ＩＫ", "左つま先ＩＫ", "右足IK親", "左足IK親", "センター", "グルーブ", "全ての親"]:
                if k in data_set.motion.bones and k in data_set.rep_model.bones:
                    for fno in data_set.motion.get_bone_fnos(k):
                        bf = data_set.motion.bones[k][fno]
                        # IK比率をそのまま掛ける
                        bf.position.setX(bf.position.x() * data_set.xz_ratio)
                        bf.position.setY(bf.position.y() * data_set.y_ratio)
                        bf.position.setZ(bf.position.z() * data_set.xz_ratio)

                        # オフセット調整
                        bf.position += data_set.rep_model.bones[k].local_offset

                    if len(data_set.motion.bones[k].keys()) > 0:
                        logger.info("移動補正: %s", k)

            logger.info("つま先補正　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)

            org_toe_links = data_set.org_model.create_link_2_top_lr("つま先実体")
            rep_toe_links = data_set.rep_model.create_link_2_top_lr("つま先実体")

            logger.debug("元：左つま先：%s", data_set.org_model.left_toe_vertex)
            logger.debug("元：右つま先：%s", data_set.org_model.right_toe_vertex)
            logger.debug("先：左つま先：%s", data_set.rep_model.left_toe_vertex)
            logger.debug("先：右つま先：%s", data_set.rep_model.right_toe_vertex)

            for k in ["右足ＩＫ", "左足ＩＫ", "右足IK親", "左足IK親"]:
                if k in data_set.motion.bones and k in data_set.rep_model.bones and rep_toe_links:
                    for fno in data_set.motion.get_bone_fnos(k):
                        bf = data_set.motion.bones[k][fno]
                        org_toe_3ds = MServiceUtils.calc_global_pos(data_set.org_model, org_toe_links[k[0]], data_set.org_motion, bf.fno)
                        # [logger.test("%s: %s", k, v) for k, v in org_toe_3ds.items()]
                        org_toe_pos = org_toe_3ds["{0}つま先実体".format(k[0])]
                        logger.test("f: %s, %s - 作成元つま先: %s", bf.fno, k[0], org_toe_pos)

                        rep_toe_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, rep_toe_links[k[0]], data_set.motion, bf.fno)
                        rep_toe_pos = rep_toe_3ds["{0}つま先実体".format(k[0])]
                        # [logger.test("%s: %s", k, v) for k, v in org_toe_3ds.items()]
                        logger.test("f: %s, %s - 変換先つま先: %s", bf.fno, k[0], rep_toe_pos)
                        
                        # つま先が元モデルの上にある場合、つま先を合わせて下に下ろす
                        toe_diff = rep_toe_pos.y() - (org_toe_pos.y() * data_set.original_y_ratio)
                        if org_toe_pos.y() < 0.5 and toe_diff > 0:
                            bf.position.setY(bf.position.y() - toe_diff)
                            logger.debug("f: %s, %sつま先元補正: %s", bf.fno, k[0], -toe_diff)

                        # ----------

                        rep_toe_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, rep_toe_links[k[0]], data_set.motion, bf.fno)
                        rep_toe_pos = rep_toe_3ds["{0}つま先実体".format(k[0])]
                        # [logger.test("%s: %s", k, v) for k, v in org_toe_3ds.items()]
                        logger.test("f: %s, %s - 変換先つま先re: %s", bf.fno, k[0], rep_toe_pos)
                        
                        # つま先がマイナス位置にある場合、床に戻す
                        if rep_toe_pos.y() < 0:
                            bf.position.setY(bf.position.y() - rep_toe_pos.y())
                            logger.debug("f: %s, %sつま先床補正: %s", bf.fno, k[0], -rep_toe_pos.y())

                    if len(data_set.motion.bones[k].keys()) > 0:
                        logger.info("つま先補正: %s", k)
                        
        return True
    
    def set_leg_ik_offset(self, data_set: MOptionsDataSet):
        target_bones = ["左足", "左足ＩＫ", "右足ＩＫ"]

        if set(target_bones).issubset(data_set.org_model.bones) and set(target_bones).issubset(data_set.rep_model.bones):
            # 足ボーンのY差
            leg_ratio = data_set.rep_model.bones["左足"].position.y() / data_set.org_model.bones["左足"].position.y()

            # 足IKのオフセット上限
            leg_ik_offset = {"左": MVector3D(), "右": MVector3D()}
            IK_RATE = data_set.original_xz_ratio * 1.2
            for direction in ["左", "右"]:
                org_leg_ik_pos = data_set.org_model.bones["{0}足ＩＫ".format(direction)].position
                rep_leg_ik_pos = data_set.rep_model.bones["{0}足ＩＫ".format(direction)].position
                org_leg_pos = data_set.org_model.bones["{0}足".format(direction)].position
                rep_leg_pos = data_set.rep_model.bones["{0}足".format(direction)].position
                # IKオフセット
                leg_ik_offset[direction] = ((org_leg_ik_pos - org_leg_pos) * leg_ratio) - (rep_leg_ik_pos - rep_leg_pos)
                leg_ik_offset[direction].effective()
                leg_ik_offset[direction].setY(0)
                logger.test("leg_ik_offset(%s): %s", direction, leg_ik_offset[direction])

                if abs(leg_ik_offset[direction].x()) > abs(rep_leg_ik_pos.x() * IK_RATE):
                    # IKオフセットが、元々の足の位置の一定以上に広がっている場合、縮める
                    re_x = rep_leg_ik_pos.x() * IK_RATE
                    # オフセットの広がり具合が、元々と同じ場合は正、反対の場合、負
                    leg_ik_offset[direction].setX(re_x * (1 if np.sign(leg_ik_offset[direction].x()) == np.sign(rep_leg_ik_pos.x()) else -1))

            logger.info("IKオフセット(%s): x: %s, z: %s", "左足", leg_ik_offset["左"].x(), leg_ik_offset["左"].z())
            logger.info("IKオフセット(%s): x: %s, z: %s", "右足", leg_ik_offset["右"].x(), leg_ik_offset["右"].z())

            data_set.rep_model.bones["左足ＩＫ"].local_offset = leg_ik_offset["左"]
            data_set.rep_model.bones["右足ＩＫ"].local_offset = leg_ik_offset["右"]

            return

        logger.info("IKオフセットなし")

    # センターZオフセット計算
    def set_center_z_offset(self, data_set: MOptionsDataSet):
        target_bones = ["左つま先ＩＫ", "左足", "左足首", "センター"]

        if set(target_bones).issubset(data_set.org_model.bones) and set(target_bones).issubset(data_set.rep_model.bones):
            # 作成元センターのZ位置
            org_center_z = data_set.org_model.bones["センター"].position.z()
            logger.test("org_center_z: %s", org_center_z)
            # 作成元左足首のZ位置
            org_ankle_z = data_set.org_model.bones["左足首"].position.z()
            logger.test("org_ankle_z: %s", org_ankle_z)
            # 作成元左足のZ位置
            org_leg_z = data_set.org_model.bones["左足"].position.z()
            logger.test("org_leg_z: %s", org_leg_z)
            # 作成元つま先のZ位置
            org_toe_z = data_set.org_model.left_toe_vertex.position.z()
            logger.test("org_toe_z: %s", org_toe_z)

            # 変換先センターのZ位置
            rep_center_z = data_set.rep_model.bones["センター"].position.z()
            logger.test("rep_center_z: %s", rep_center_z)
            # 変換先左足首のZ位置
            rep_ankle_z = data_set.rep_model.bones["左足首"].position.z()
            logger.test("rep_ankle_z: %s", rep_ankle_z)
            # 変換先左足のZ位置
            rep_leg_z = data_set.rep_model.bones["左足"].position.z()
            logger.test("rep_leg_z: %s", rep_leg_z)
            # 変換先つま先のZ位置
            rep_toe_z = data_set.rep_model.left_toe_vertex.position.z()
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
            data_set.rep_model.bones["センター"].local_offset = local_offset
            logger.test("local_offset %s", data_set.rep_model.bones["センター"].local_offset)

            logger.info("Zオフセット: %s: %s", "センター", local_offset.z())

            return

        logger.info("Zオフセットなし")



