# -*- coding: utf-8 -*-
#

import wx
import time
from form.worker.BaseWorkerThread import BaseWorkerThread
from service.ConvertVmdService import ConvertVmdService
from module.MOptions import MVmdOptions


class VmdWorkerThread(BaseWorkerThread):

    def __init__(self, frame: wx.Frame, result_event: wx.Event):
        self.elapsed_time = 0
        self.frame = frame
        self.result_event = result_event

        super().__init__(frame, self.result_event, frame.vmd_panel_ctrl.console_ctrl)

    def thread_event(self):
        start = time.time()

        options = MVmdOptions(\
            version_name=self.frame.version_name, \
            logging_level=self.frame.logging_level, \
            bone_csv_path=self.frame.vmd_panel_ctrl.bone_csv_file_ctrl.path(), \
            morph_csv_path=self.frame.vmd_panel_ctrl.morph_csv_file_ctrl.path(), \
            camera_csv_path=self.frame.vmd_panel_ctrl.camera_csv_file_ctrl.path(), \
        )
        
        self.result = ConvertVmdService(options).execute() and self.result

        self.elapsed_time = time.time() - start

    def post_event(self):
        wx.PostEvent(self.frame, self.result_event(result=self.result, elapsed_time=self.elapsed_time))
