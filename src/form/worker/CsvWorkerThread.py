# -*- coding: utf-8 -*-
#

import wx
import time
from form.worker.BaseWorkerThread import BaseWorkerThread
from service.ConvertCsvService import ConvertCsvService
from module.MOptions import MCsvOptions


class CsvWorkerThread(BaseWorkerThread):

    def __init__(self, frame: wx.Frame, result_event: wx.Event):
        self.elapsed_time = 0
        self.frame = frame
        self.result_event = result_event

        super().__init__(frame, self.result_event, frame.csv_panel_ctrl.console_ctrl)

    def thread_event(self):
        start = time.time()

        self.result = self.frame.csv_panel_ctrl.vmd_file_ctrl.load() and self.result

        if self.result:
            options = MCsvOptions(\
                version_name=self.frame.version_name, \
                logging_level=self.frame.logging_level, \
                motion=self.frame.csv_panel_ctrl.vmd_file_ctrl.data)
            
            self.result = ConvertCsvService(options).execute() and self.result

        self.elapsed_time = time.time() - start

    def post_event(self):
        wx.PostEvent(self.frame, self.result_event(result=self.result, elapsed_time=self.elapsed_time))
