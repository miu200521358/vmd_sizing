# -*- coding: utf-8 -*-
#

import os
import glob
import copy
from form.worker.BaseWorkerThread import BaseWorkerThread
from service.SizingService import SizingService
from module.MOptions import MOptions


class SizingWorkerThread(BaseWorkerThread):

    def __init__(self, form, result_event):
        super().__init__(form, result_event)

    def thread_event(self):
        file_path_list = [p for p in sorted(glob.glob(self.form.file_panel_ctrl.motion_vmd_file_ctrl.file_ctrl.GetPath())) if os.path.isfile(p)]

        for file_idx in range(len(file_path_list)):
            if self.form.file_panel_ctrl.motion_vmd_file_ctrl.load(file_idx):
                options = MOptions(\
                    version_name=self.form.version_name, \
                    logging_level=self.form.logging_level, \
                    motion_vmd_data=copy.deepcopy(self.form.file_panel_ctrl.motion_vmd_file_ctrl.data), \
                    org_model_data=self.form.file_panel_ctrl.org_model_file_ctrl.data, \
                    rep_model_data=self.form.file_panel_ctrl.rep_model_file_ctrl.data, \
                    output_vmd_data=self.form.file_panel_ctrl.output_vmd_file_ctrl.data, \
                    alternative_model_flg=self.form.file_panel_ctrl.org_model_file_ctrl.title_parts_ctrl.GetValue(), \
                    twist_flg=self.form.file_panel_ctrl.rep_model_file_ctrl.title_parts_ctrl.GetValue())

                self.result = SizingService(options).execute() and self.result

