# -*- coding: utf-8 -*-
#

import os
import wx
import time
import gc
from form.worker.BaseWorkerThread import BaseWorkerThread, task_takes_time
from service.ConvertSmoothService import ConvertSmoothService
from module.MOptions import MSmoothOptions
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class SmoothWorkerThread(BaseWorkerThread):

    def __init__(self, frame: wx.Frame, result_event: wx.Event, is_exec_saving: bool):
        self.elapsed_time = 0
        self.frame = frame
        self.result_event = result_event
        self.gauge_ctrl = frame.smooth_panel_ctrl.gauge_ctrl
        self.is_exec_saving = is_exec_saving
        self.options = None

        super().__init__(frame, self.result_event, frame.smooth_panel_ctrl.console_ctrl)

    @task_takes_time
    def thread_event(self):
        start = time.time()

        self.result = self.frame.smooth_panel_ctrl.smooth_vmd_file_ctrl.load() and self.result
        self.result = self.frame.smooth_panel_ctrl.smooth_model_file_ctrl.load(is_check=False) and self.result

        if self.result:
            self.options = MSmoothOptions(\
                version_name=self.frame.version_name, \
                logging_level=self.frame.logging_level, \
                motion=self.frame.smooth_panel_ctrl.smooth_vmd_file_ctrl.data, \
                model=self.frame.smooth_panel_ctrl.smooth_model_file_ctrl.data, \
                output_path=self.frame.smooth_panel_ctrl.output_smooth_vmd_file_ctrl.file_ctrl.GetPath(), \
                loop_cnt=self.frame.smooth_panel_ctrl.loop_cnt_ctrl.GetValue(), \
                interpolation=self.frame.smooth_panel_ctrl.interpolation_ctrl.GetSelection(), \
                monitor=self.frame.smooth_panel_ctrl.console_ctrl, \
                is_file=False, \
                outout_datetime=logger.outout_datetime, \
                max_workers=(1 if self.is_exec_saving else min(32, os.cpu_count() + 4)))
            
            self.result = ConvertSmoothService(self.options).execute() and self.result

        self.elapsed_time = time.time() - start

    def thread_delete(self):
        del self.options
        gc.collect()
        
    def post_event(self):
        wx.PostEvent(self.frame, self.result_event(result=self.result, elapsed_time=self.elapsed_time))
