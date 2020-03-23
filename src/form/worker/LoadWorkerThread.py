# -*- coding: utf-8 -*-
#

import wx
from form.parts.SizingFileSet import SizingFileSet
from form.worker.BaseWorkerThread import BaseWorkerThread


class LoadWorkerThread(BaseWorkerThread):

    def __init__(self, frame: wx.Frame, file_set: SizingFileSet, result_event: wx.Event, is_exec: bool):
        self.is_exec = is_exec
        self.file_set = file_set

        super().__init__(frame, result_event)

    def thread_event(self):
        self.result = self.file_set.motion_vmd_file_ctrl.load() and self.result
        self.result = self.file_set.org_model_file_ctrl.load() and self.result
        self.result = self.file_set.rep_model_file_ctrl.load() and self.result

    def post_event(self):
        wx.PostEvent(self.frame, self.result_event(result=self.result, is_exec=self.is_exec))
