# -*- coding: utf-8 -*-
#

import wx
from form.worker.BaseWorkerThread import BaseWorkerThread


class LoadWorkerThread(BaseWorkerThread):

    def __init__(self, frame: wx.Frame, result_event: wx.Event, is_exec: bool):
        self.is_exec = is_exec
        self.frame = frame
        self.result_event = result_event

        super().__init__(frame, self.result_event)

    def thread_event(self):
        self.result = self.frame.file_panel_ctrl.file_set.load() and self.result

        for file_set in self.frame.multi_panel_ctrl.file_set_list:
            self.result = file_set.load() and self.result

    def post_event(self):
        wx.PostEvent(self.frame, self.result_event(result=self.result, is_exec=self.is_exec))
