# -*- coding: utf-8 -*-
#

import mmd.PmxModel as PmxModel # noqa
import mmd.VmdMotion as VmdMotion # noqa
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
import module.MOptions as MOptions
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


# 上半身のスタンスの違い
def calc_upper_stance_diff(model, from_bone_name, to_bone_name=None):
    return calc_stance_diff(model, from_bone_name, to_bone_name, MVector3D(0, 1, 0))


# 腕のスタンスの違い
def calc_arm_stance_diff(model, from_bone_name, to_bone_name=None):
    default_pos = MVector3D(1, 0, 0) if "左" in from_bone_name else MVector3D(-1, 0, 0)
    return calc_stance_diff(model, from_bone_name, to_bone_name, default_pos)


def calc_stance_diff(model: PmxModel, from_bone_name, to_bone_name, default_pos):
    from_pos = MVector3D()
    to_pos = MVector3D()

    if from_bone_name in model.bones:
        fv = model.bones[from_bone_name]
        from_pos = fv.position
        
        if to_bone_name in model.bones:
            # TOが指定されている場合、ボーン位置を保持
            to_pos = model.bones[to_bone_name].position
        else:
            # TOの明示が無い場合、表示先からボーン位置取得
            if fv.tail_position != MVector3D():
                # 表示先が相対パスの場合、保持
                to_pos = from_pos + fv.tail_position
            elif fv.tail_index >= 0:
                # 表示先がボーンの場合、ボーン位置保持
                to_pos = model.bones[model.bone_indexes[fv.tail_index]].position
            else:
                # ここまで来たらデフォルト加算
                to_pos = from_pos + default_pos

    from_qq = MQuaternion()
    if from_pos != MVector3D() and to_pos != MVector3D():
        logger.test("from_pos: %s", from_pos)
        logger.test("to_pos: %s", to_pos)

        diff_pos = to_pos - from_pos
        diff_pos.normalize()
        logger.test("diff_pos: %s", diff_pos)

        from_qq = MQuaternion.rotationTo(default_pos, diff_pos)
        logger.test("[z] from_bone_name: %s, from_qq: %s", from_bone_name, from_qq.toEulerAngles())

    return diff_pos, from_qq


def calc_leg_ik_ratio(options: MOptions):
    target_bones = ["左足", "左ひざ", "左足首", "センター"]

    if set(target_bones).issubset(options.org_model_data.bones) and set(target_bones).issubset(options.rep_model_data.bones):
        # XZ比率(足の長さ)
        org_leg_length = ((options.org_model_data.bones["左足首"].position - options.org_model_data.bones["左ひざ"].position) \
                          + (options.org_model_data.bones["左ひざ"].position - options.org_model_data.bones["左足"].position)).length()
        rep_leg_length = ((options.rep_model_data.bones["左足首"].position - options.rep_model_data.bones["左ひざ"].position) \
                          + (options.rep_model_data.bones["左ひざ"].position - options.rep_model_data.bones["左足"].position)).length()
        logger.test("xz_ratio rep_leg_length: %s, org_leg_length: %s", rep_leg_length, org_leg_length)
        xz_ratio = 1 if org_leg_length == 0 else (rep_leg_length / org_leg_length)

        # Y比率(股下のY差)
        rep_leg_length = (options.rep_model_data.bones["左足首"].position - options.rep_model_data.bones["左足"].position).y()
        org_leg_length = (options.org_model_data.bones["左足首"].position - options.org_model_data.bones["左足"].position).y()
        logger.test("y_ratio rep_leg_length: %s, org_leg_length: %s", rep_leg_length, org_leg_length)
        y_ratio = 1 if org_leg_length == 0 else (rep_leg_length / org_leg_length)

        logger.info("足の長さの比率: xz: %s, y: %s", xz_ratio, y_ratio, decoration=MLogger.DECORATION_SIMPLE)

        return xz_ratio, y_ratio
    
    logger.warning("「左足」「左ひざ」「左足首」「センター」のいずれかのボーンが不足しているため、足の長さの比率が測れませんでした。", decoration=MLogger.DECORATION_BOX)

    return 1, 1

