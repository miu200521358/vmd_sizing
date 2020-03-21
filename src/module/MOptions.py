# -*- coding: utf-8 -*-
#
import mmd.VmdMotion as VmdMotion
import mmd.PmxModel as PmxModel


class MOptions():

    def __init__(self, version_name, logging_level, motion_vmd_data: VmdMotion, org_model_data: PmxModel, rep_model_data: PmxModel, output_vmd_path, substitute_model_flg, twist_flg):
        self.version_name = version_name
        self.logging_level = logging_level
        self.motion_vmd_data = motion_vmd_data
        self.org_model_data = org_model_data
        self.rep_model_data = rep_model_data
        self.output_vmd_path = output_vmd_path
        self.substitute_model_flg = substitute_model_flg
        self.twist_flg = twist_flg


