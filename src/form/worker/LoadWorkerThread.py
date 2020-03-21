# -*- coding: utf-8 -*-
#

import wx
from form.worker.BaseWorkerThread import BaseWorkerThread


class LoadWorkerThread(BaseWorkerThread):

    def __init__(self, form, result_event, parent, is_exec):
        self.parent = parent
        self.is_exec = is_exec

        super().__init__(form, result_event)

    def thread_event(self):
        self.result = self.parent.motion_vmd_file_ctrl.load() and self.result
        self.result = self.parent.org_model_file_ctrl.load() and self.result
        self.result = self.parent.rep_model_file_ctrl.load() and self.result

    def post_event(self):
        wx.PostEvent(self.form, self.result_event(result=self.result, is_exec=self.is_exec))
