# -*- coding: utf-8 -*-
#

import logging
import os
import glob
import time
import wx
import _pickle as cPickle

from form.worker.BaseWorkerThread import BaseWorkerThread
from module.MOptions import MOptions, MOptionsDataSet
from service.SizingService import SizingService
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class SizingWorkerThread(BaseWorkerThread):

    def __init__(self, frame: wx.Frame, result_event: wx.Event):
        self.elapsed_time = 0
        super().__init__(frame, result_event)

    def thread_event(self):
        try:
            start = time.time()
            # データセットリスト
            data_set_list = []
            file_path_list = [p for p in sorted(glob.glob(self.frame.file_panel_ctrl.file_set.motion_vmd_file_ctrl.file_ctrl.GetPath())) if os.path.isfile(p)]

            for file_idx in range(len(file_path_list)):
                if self.frame.file_panel_ctrl.file_set.motion_vmd_file_ctrl.load(file_idx):
                    
                    # 1件目は必ず読み込む
                    first_data_set = MOptionsDataSet(
                        motion_vmd_data=cPickle.loads(cPickle.dumps(self.frame.file_panel_ctrl.file_set.motion_vmd_file_ctrl.data, -1)), \
                        org_model_data=self.frame.file_panel_ctrl.file_set.org_model_file_ctrl.data, \
                        rep_model_data=self.frame.file_panel_ctrl.file_set.rep_model_file_ctrl.data, \
                        output_vmd_path=self.frame.file_panel_ctrl.file_set.output_vmd_file_ctrl.file_ctrl.GetPath(), \
                        substitute_model_flg=self.frame.file_panel_ctrl.file_set.org_model_file_ctrl.title_parts_ctrl.GetValue(), \
                        twist_flg=self.frame.file_panel_ctrl.file_set.rep_model_file_ctrl.title_parts_ctrl.GetValue()
                    )
                    data_set_list.append(first_data_set)

                    # 2件目以降は有効なのだけ読み込む
                    for file_set in self.frame.multi_panel_ctrl.file_set_list:
                        if file_set.is_loaded():
                            multi_data_set = MOptionsDataSet(
                                motion_vmd_data=cPickle.loads(cPickle.dumps(file_set.motion_vmd_file_ctrl.data, -1)), \
                                org_model_data=file_set.org_model_file_ctrl.data, \
                                rep_model_data=file_set.rep_model_file_ctrl.data, \
                                output_vmd_path=file_set.output_vmd_file_ctrl.file_ctrl.GetPath(), \
                                substitute_model_flg=file_set.org_model_file_ctrl.title_parts_ctrl.GetValue(), \
                                twist_flg=file_set.rep_model_file_ctrl.title_parts_ctrl.GetValue()
                            )
                            data_set_list.append(multi_data_set)

                    options = MOptions(\
                        version_name=self.frame.version_name, \
                        logging_level=self.frame.logging_level, \
                        data_set_list=data_set_list)
                    
                    self.result = SizingService(options).execute() and self.result

            self.elapsed_time = time.time() - start
        except Exception as e:
            logger.critical("VMDサイジング処理が意図せぬエラーで終了しました。\n\n%s", e, decoration=MLogger.DECORATION_BOX)
        finally:
            logging.shutdown()

    def post_event(self):
        wx.PostEvent(self.frame, self.result_event(result=self.result, elapsed_time=self.elapsed_time))

