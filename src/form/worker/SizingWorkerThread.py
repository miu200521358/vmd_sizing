# -*- coding: utf-8 -*-
#

import logging
import os
import glob
import time
import wx
import re

from form.worker.BaseWorkerThread import BaseWorkerThread
from module.MOptions import MOptions, MOptionsDataSet, MArmProcessOptions
from service.SizingService import SizingService
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class SizingWorkerThread(BaseWorkerThread):

    def __init__(self, frame: wx.Frame, result_event: wx.Event, is_out_log: bool):
        self.elapsed_time = 0
        self.is_out_log = is_out_log
        super().__init__(frame, result_event, frame.file_panel_ctrl.console_ctrl)

    def thread_event(self):
        try:
            start = time.time()
            # データセットリスト
            data_set_list = []
            
            base_file_path = self.frame.file_panel_ctrl.file_set.motion_vmd_file_ctrl.file_ctrl.GetPath()
            if os.path.exists(base_file_path):
                file_path_list = [base_file_path]
            else:
                file_path_list = [p for p in glob.glob(base_file_path) if os.path.isfile(p)]

            for file_idx in range(len(file_path_list)):
                if self.frame.file_panel_ctrl.file_set.motion_vmd_file_ctrl.load(file_idx):
                    
                    # 1件目は必ず読み込む
                    first_data_set = MOptionsDataSet(
                        motion=self.frame.file_panel_ctrl.file_set.motion_vmd_file_ctrl.data.copy(), \
                        org_model=self.frame.file_panel_ctrl.file_set.org_model_file_ctrl.data, \
                        rep_model=self.frame.file_panel_ctrl.file_set.rep_model_file_ctrl.data, \
                        output_vmd_path=self.frame.file_panel_ctrl.file_set.output_vmd_file_ctrl.file_ctrl.GetPath(), \
                        detail_stance_flg=self.frame.file_panel_ctrl.file_set.org_model_file_ctrl.title_parts_ctrl.GetValue(), \
                        twist_flg=self.frame.file_panel_ctrl.file_set.rep_model_file_ctrl.title_parts_ctrl.GetValue(), \
                        morph_list=self.frame.morph_panel_ctrl.get_morph_list(1)
                    )
                    data_set_list.append(first_data_set)

                    # 2件目以降は有効なのだけ読み込む
                    for file_set in self.frame.multi_panel_ctrl.file_set_list:
                        if file_set.is_loaded():
                            multi_data_set = MOptionsDataSet(
                                motion=file_set.motion_vmd_file_ctrl.data.copy(), \
                                org_model=file_set.org_model_file_ctrl.data, \
                                rep_model=file_set.rep_model_file_ctrl.data, \
                                output_vmd_path=file_set.output_vmd_file_ctrl.file_ctrl.GetPath(), \
                                detail_stance_flg=file_set.org_model_file_ctrl.title_parts_ctrl.GetValue(), \
                                twist_flg=file_set.rep_model_file_ctrl.title_parts_ctrl.GetValue(), \
                                morph_list=self.frame.morph_panel_ctrl.get_morph_list(file_set.set_no)
                            )
                            data_set_list.append(multi_data_set)
            options = MOptions(\
                version_name=self.frame.version_name, \
                logging_level=self.frame.logging_level, \
                data_set_list=data_set_list, \
                arm_options=MArmProcessOptions( \
                    self.frame.arm_panel_ctrl.arm_process_flg_avoidance.GetValue(), \
                    list(map(str, [x.strip() for x in self.frame.arm_panel_ctrl.avoidance_target_txt_ctrl.GetValue().split(',')])), \
                    self.frame.arm_panel_ctrl.arm_process_flg_alignment.GetValue(), \
                    self.frame.arm_panel_ctrl.arm_alignment_finger_flg_ctrl.GetValue(), \
                    self.frame.arm_panel_ctrl.arm_alignment_floor_flg_ctrl.GetValue(), \
                    self.frame.arm_panel_ctrl.alignment_distance_wrist_slider.GetValue(), \
                    self.frame.arm_panel_ctrl.alignment_distance_finger_slider.GetValue(), \
                    self.frame.arm_panel_ctrl.alignment_distance_floor_slider.GetValue(), \
                    self.frame.arm_panel_ctrl.arm_check_skip_flg_ctrl.GetValue()
                ), \
                monitor=self.queue, \
                is_file=False, \
                outout_datetime=logger.outout_datetime)
            
            self.result = SizingService(options).execute() and self.result

            self.elapsed_time = time.time() - start
        except Exception as e:
            logger.critical("VMDサイジング処理が意図せぬエラーで終了しました。", e, decoration=MLogger.DECORATION_BOX)
        finally:
            try:
                if self.is_out_log or not self.result:
                    # ログパス生成
                    output_vmd_path = self.frame.file_panel_ctrl.file_set.output_vmd_file_ctrl.file_ctrl.GetPath()
                    output_log_path = re.sub(r'\.vmd$', '.log', output_vmd_path)

                    # 出力されたメッセージを全部出力
                    self.frame.file_panel_ctrl.console_ctrl.SaveFile(filename=output_log_path)

            except Exception:
                pass

            logging.shutdown()

    def post_event(self):
        wx.PostEvent(self.frame, self.result_event(result=self.result, elapsed_time=self.elapsed_time))

