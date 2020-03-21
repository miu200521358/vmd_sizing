# -*- coding: utf-8 -*-
#

import module.MOptions as MOptions
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


def calc_leg_ik_ratio(options: MOptions):
    target_bones = ["左足", "左ひざ", "左足首", "センター"]

    if set(target_bones).issubset(options.org_model_data.bones) and set(target_bones).issubset(options.rep_model_data.bones):
        # XZ比率(足の長さ)
        org_leg_length = ((options.org_model_data.bones["左足首"].position - options.org_model_data.bones["左ひざ"].position) + (options.org_model_data.bones["左ひざ"].position - options.org_model_data.bones["左足"].position)).length()
        rep_leg_length = ((options.rep_model_data.bones["左足首"].position - options.rep_model_data.bones["左ひざ"].position) + (options.rep_model_data.bones["左ひざ"].position - options.rep_model_data.bones["左足"].position)).length()
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

