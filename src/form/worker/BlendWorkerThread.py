# -*- coding: utf-8 -*-
#

import gc
import wx
import time
from form.worker.BaseWorkerThread import BaseWorkerThread, task_takes_time
from service.MorphBlendService import MorphBlendService
from module.MOptions import MBlendOptions


class BlendWorkerThread(BaseWorkerThread):

    def __init__(self, frame: wx.Frame, result_event: wx.Event):
        self.elapsed_time = 0
        self.frame = frame
        self.result_event = result_event
        self.gauge_ctrl = frame.blend_panel_ctrl.gauge_ctrl
        self.options = None

        super().__init__(frame, self.result_event, frame.blend_panel_ctrl.console_ctrl)

    @task_takes_time
    def thread_event(self):
        start = time.time()

        self.result = self.frame.blend_panel_ctrl.pmx_file_ctrl.load() and self.result

        if self.result:
            eye_list = [self.frame.blend_panel_ctrl.morph_eye_list.GetString(idx) for idx in self.frame.blend_panel_ctrl.morph_eye_list.GetSelections()]
            eyebrow_list = [self.frame.blend_panel_ctrl.morph_eyebrow_list.GetString(idx) for idx in self.frame.blend_panel_ctrl.morph_eyebrow_list.GetSelections()]
            lip_list = [self.frame.blend_panel_ctrl.morph_lip_list.GetString(idx) for idx in self.frame.blend_panel_ctrl.morph_lip_list.GetSelections()]
            other_list = [self.frame.blend_panel_ctrl.morph_other_list.GetString(idx) for idx in self.frame.blend_panel_ctrl.morph_other_list.GetSelections()]

            self.options = MBlendOptions(\
                version_name=self.frame.version_name, \
                logging_level=self.frame.logging_level, \
                model=self.frame.blend_panel_ctrl.pmx_file_ctrl.data, \
                eye_list=eye_list, \
                eyebrow_list=eyebrow_list, \
                lip_list=lip_list, \
                other_list=other_list, \
                min_value=self.frame.blend_panel_ctrl.morph_spin_min.GetValue(), \
                max_value=self.frame.blend_panel_ctrl.morph_spin_max.GetValue(), \
                inc_value=self.frame.blend_panel_ctrl.morph_spin_inc.GetValue())
            
            self.result = MorphBlendService(self.options).execute() and self.result

        self.elapsed_time = time.time() - start

    def thread_delete(self):
        del self.options
        gc.collect()

    def post_event(self):
        wx.PostEvent(self.frame, self.result_event(result=self.result, elapsed_time=self.elapsed_time))
