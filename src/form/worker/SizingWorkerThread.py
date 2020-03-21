# -*- coding: utf-8 -*-
#

import logging
import os
import glob
import time
import wx
import _pickle as cPickle
from form.worker.BaseWorkerThread import BaseWorkerThread
from module.MOptions import MOptions
from service.SizingService import SizingService
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class SizingWorkerThread(BaseWorkerThread):

    def __init__(self, form, result_event):
        self.elapsed_time = 0
        super().__init__(form, result_event)

    def thread_event(self):
        try:
            start = time.time()
            file_path_list = [p for p in sorted(glob.glob(self.form.file_panel_ctrl.motion_vmd_file_ctrl.file_ctrl.GetPath())) if os.path.isfile(p)]

            for file_idx in range(len(file_path_list)):
                if self.form.file_panel_ctrl.motion_vmd_file_ctrl.load(file_idx):
                    options = MOptions(\
                        version_name=self.form.version_name, \
                        logging_level=self.form.logging_level, \
                        motion_vmd_data=cPickle.loads(cPickle.dumps(self.form.file_panel_ctrl.motion_vmd_file_ctrl.data, -1)), \
                        org_model_data=self.form.file_panel_ctrl.org_model_file_ctrl.data, \
                        rep_model_data=self.form.file_panel_ctrl.rep_model_file_ctrl.data, \
                        output_vmd_path=self.form.file_panel_ctrl.output_vmd_file_ctrl.file_ctrl.GetPath(), \
                        substitute_model_flg=self.form.file_panel_ctrl.org_model_file_ctrl.title_parts_ctrl.GetValue(), \
                        twist_flg=self.form.file_panel_ctrl.rep_model_file_ctrl.title_parts_ctrl.GetValue())
                    
                    self.result = SizingService(options).execute() and self.result

            self.elapsed_time = time.time() - start
        except Exception as e:
            logger.critical("VMDサイジング処理が意図せぬエラーで終了しました。\n\n%s", e, decoration=MLogger.DECORATION_BOX)
        finally:
            logging.shutdown()

    def post_event(self):
        wx.PostEvent(self.form, self.result_event(result=self.result, elapsed_time=self.elapsed_time))

