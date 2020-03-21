# -*- coding: utf-8 -*-
#


class MOptions():

    def __init__(self, version_name, logging_level, motion_vmd_data, org_model_data, rep_model_data, output_vmd_data, alternative_model_flg, twist_flg):
        self.version_name = version_name
        self.logging_level = logging_level
        self.motion_vmd_data = motion_vmd_data
        self.org_model_data = org_model_data
        self.rep_model_data = rep_model_data
        self.output_vmd_data = output_vmd_data
        self.alternative_model_flg = alternative_model_flg
        self.twist_flg = twist_flg


