# -*- coding: utf-8 -*-
#
import wx
import wx.lib.newevent
import sys
import csv
import re
import os
from datetime import datetime

from form.panel.BasePanel import BasePanel
from form.parts.HistoryFilePickerCtrl import HistoryFilePickerCtrl
from form.parts.ConsoleCtrl import ConsoleCtrl
from form.parts.SizingFileSet import SizingFileSet
from form.worker.SizingWorkerThread import SizingWorkerThread
from form.worker.LoadWorkerThread import LoadWorkerThread
from module.MOptions import MOptions, MOptionsDataSet, MArmProcessOptions
from utils import MFormUtils, MFileUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)
TIMER_ID = wx.NewId()

# イベント
(BulkSizingThreadEvent, EVT_BULK_SIZING_THREAD) = wx.lib.newevent.NewEvent()
(BulkLoadThreadEvent, EVT_BULK_LOAD_THREAD) = wx.lib.newevent.NewEvent()


class BulkPanel(BasePanel):
    
    def __init__(self, frame: wx.Frame, parent: wx.Notebook, tab_idx: int):
        super().__init__(frame, parent, tab_idx)

        self.description_txt = wx.StaticText(self, wx.ID_ANY, "設定を一括で指定して、連続して処理させる事ができます。", wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.description_txt, 0, wx.ALL, 5)

        self.static_line = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.sizer.Add(self.static_line, 0, wx.EXPAND | wx.ALL, 5)

        # バルクBULKファイルコントロール
        self.bulk_csv_file_ctrl = HistoryFilePickerCtrl(frame, self, u"一括処理用CSV", u"一括処理用CSVファイルを開く", ("csv"), wx.FLP_DEFAULT_STYLE, \
                                                        u"一括処理用のCSVを指定してください。\nフォーマットは、DLボタンから取得できます。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。", \
                                                        file_model_spacer=0, title_parts_ctrl=None, title_parts2_ctrl=None, \
                                                        file_histories_key="bulk_csv", is_change_output=False, is_aster=False, is_save=False, set_no=0)
        self.sizer.Add(self.bulk_csv_file_ctrl.sizer, 0, wx.EXPAND | wx.ALL, 0)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 一括サイジング保存ボタン
        self.save_btn_ctrl = wx.Button(self, wx.ID_ANY, u"一括サイジング保存", wx.DefaultPosition, wx.Size(150, 50), 0)
        self.save_btn_ctrl.SetToolTip(u"現在のサイジング設定をCSVに保存します")
        self.save_btn_ctrl.Bind(wx.EVT_LEFT_DCLICK, self.on_doubleclick)
        self.save_btn_ctrl.Bind(wx.EVT_LEFT_DOWN, self.on_save_click)
        btn_sizer.Add(self.save_btn_ctrl, 0, wx.ALL, 5)

        # 一括サイジング確認ボタン
        self.check_btn_ctrl = wx.Button(self, wx.ID_ANY, u"一括サイジング確認", wx.DefaultPosition, wx.Size(150, 50), 0)
        self.check_btn_ctrl.SetToolTip(u"指定されたCSVデータの設定を確認します。")
        self.check_btn_ctrl.Bind(wx.EVT_LEFT_DCLICK, self.on_doubleclick)
        self.check_btn_ctrl.Bind(wx.EVT_LEFT_DOWN, self.on_check_click)
        btn_sizer.Add(self.check_btn_ctrl, 0, wx.ALL, 5)

        # 一括サイジング実行ボタン
        self.bulk_btn_ctrl = wx.Button(self, wx.ID_ANY, u"一括サイジング実行", wx.DefaultPosition, wx.Size(150, 50), 0)
        self.bulk_btn_ctrl.SetToolTip(u"一括でサイジングを実行します")
        self.bulk_btn_ctrl.Bind(wx.EVT_LEFT_DCLICK, self.on_doubleclick)
        self.bulk_btn_ctrl.Bind(wx.EVT_LEFT_DOWN, self.on_bulk_click)
        btn_sizer.Add(self.bulk_btn_ctrl, 0, wx.ALL, 5)

        self.sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.SHAPED, 5)

        # コンソール
        self.console_ctrl = ConsoleCtrl(self, self.frame.logging_level, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(-1, 420), \
                                        wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_NONE | wx.HSCROLL | wx.VSCROLL | wx.WANTS_CHARS)
        self.console_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        self.console_ctrl.Bind(wx.EVT_CHAR, lambda event: MFormUtils.on_select_all(event, self.console_ctrl))
        self.sizer.Add(self.console_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        # ゲージ
        self.gauge_ctrl = wx.Gauge(self, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL)
        self.gauge_ctrl.SetValue(0)
        self.sizer.Add(self.gauge_ctrl, 0, wx.ALL | wx.EXPAND, 5)

        self.fit()

        # 変換完了処理バインド
        self.frame.Bind(EVT_BULK_LOAD_THREAD, self.on_load_result)
        self.frame.Bind(EVT_BULK_SIZING_THREAD, self.on_exec_result)

    # フォーム無効化
    def disable(self):
        self.bulk_csv_file_ctrl.disable()
        self.bulk_btn_ctrl.Disable()
        self.check_btn_ctrl.Disable()

    # フォーム無効化
    def enable(self):
        self.bulk_csv_file_ctrl.enable()
        self.bulk_btn_ctrl.Enable()
        self.check_btn_ctrl.Enable()
    
    def on_doubleclick(self, event: wx.Event):
        self.timer.Stop()
        logger.warning("ダブルクリックされました。", decoration=MLogger.DECORATION_BOX)
        event.Skip(False)
        return False
    
    def on_bulk_click(self, event: wx.Event):
        self.timer = wx.Timer(self, TIMER_ID)
        self.timer.Start(200)
        self.Bind(wx.EVT_TIMER, self.on_bulk, id=TIMER_ID)

    # サイジング一括実行
    def on_bulk(self, event: wx.Event):
        if self.timer:
            self.timer.Stop()
            self.Unbind(wx.EVT_TIMER, id=TIMER_ID)
            
        # 出力先をファイルパネルのコンソールに変更
        sys.stdout = self.console_ctrl

        if self.bulk_btn_ctrl.GetLabel() == "一括サイジング停止" and self.frame.worker:
            # フォーム無効化
            self.disable()
            # 停止状態でボタン押下時、停止
            self.frame.worker.stop()

            # タブ移動可
            self.release_tab()
            # フォーム有効化
            self.enable()
            # ワーカー終了
            self.frame.worker = None
            # プログレス非表示
            self.gauge_ctrl.SetValue(0)

            logger.warning("VMDサイジング一括処理を中断します。", decoration=MLogger.DECORATION_BOX)
            
            event.Skip(False)
        elif not self.frame.worker:
            # フォーム無効化
            self.disable()
            # タブ固定
            self.fix_tab()
            # コンソールクリア
            self.console_ctrl.Clear()

            # 履歴保持
            self.save()

            # サイジング可否チェックの後に実行
            self.check(event, True)
            
            event.Skip()
        else:
            logger.error("まだ処理が実行中です。終了してから再度実行してください。", decoration=MLogger.DECORATION_BOX)
            event.Skip(False)
    
    def on_save_click(self, event: wx.Event):
        self.timer = wx.Timer(self, TIMER_ID)
        self.timer.Start(200)
        self.Bind(wx.EVT_TIMER, self.on_save, id=TIMER_ID)

    # サイジング一括データ保存
    def on_save(self, event: wx.Event):
        if self.timer:
            self.timer.Stop()
            self.Unbind(wx.EVT_TIMER, id=TIMER_ID)
        
        # 一括タブのコンソール
        sys.stdout = self.console_ctrl

        if not self.frame.file_panel_ctrl.file_set.motion_vmd_file_ctrl.path():
            logger.warning("ファイルタブの「調整対象モーションVMD/VPD」が空欄のため、処理を中断します。", decoration=MLogger.DECORATION_BOX)
            return

        save_key = ["グループNo(複数人モーションは同じNo)", "調整対象モーションVMD/VPD(フルパス)", "モーション作成元モデルPMX(フルパス)", "モーション変換先モデルPMX(フルパス)", \
                    "センターXZ補正(0:無効、1:有効)", "上半身補正(0:無効、1:有効)", "下半身補正(0:無効、1:有効)", "足ＩＫ補正(0:無効、1:有効)", "つま先補正(0:無効、1:有効)", \
                    "つま先ＩＫ補正(0:無効、1:有効)", "肩補正(0:無効、1:有効)", "センターY補正(0:無効、1:有効)", "捩り分散(0:なし、1:あり)", "モーフ置換(元:先:大きさ;)", "接触回避(0:なし、1:あり)", \
                    "接触回避剛体(剛体名;)", "位置合わせ(0:なし、1:あり)", "指位置合わせ(0:なし、1:あり)", "床位置合わせ(0:なし、1:あり)", "手首の距離", "指の距離", "床との距離", \
                    "腕チェックスキップ(0:なし、1:あり)", "カメラモーションVMD(フルパス、グループ1件目のみ)", "距離可動範囲", "カメラ作成元モデルPMX(フルパス)", "全長Yオフセット"]
        
        output_path = os.path.join(os.path.dirname(self.frame.file_panel_ctrl.file_set.motion_vmd_file_ctrl.path()), f'一括サイジング用データ_{datetime.now():%Y%m%d_%H%M%S}.csv')

        with open(output_path, 'w', encoding='cp932', newline='') as f:
            writer = csv.DictWriter(f, save_key)
            writer.writeheader()
            writer.writerow(self.create_save_data(self.frame.file_panel_ctrl.file_set, 0, save_key))
        
            for multi_idx, file_set in enumerate(self.frame.multi_panel_ctrl.file_set_list):
                writer.writerow(self.create_save_data(file_set, multi_idx + 1, save_key))

        self.frame.sound_finish()
        event.Skip()

        logger.info("一括サイジング用データの保存に成功しました\n\n%s", output_path, decoration=MLogger.DECORATION_BOX)
        return

    def create_save_data(self, file_set: SizingFileSet, file_idx: int, save_key: list):

        save_data = {}
        for skey in save_key:
            save_data[skey] = ""
        
        save_data[save_key[0]] = "1"
        save_data[save_key[1]] = file_set.motion_vmd_file_ctrl.path()
        save_data[save_key[2]] = file_set.org_model_file_ctrl.path()
        save_data[save_key[3]] = file_set.rep_model_file_ctrl.path()
        save_data[save_key[4]] = "1" if 0 in file_set.selected_stance_details else "0"
        save_data[save_key[5]] = "1" if 1 in file_set.selected_stance_details else "0"
        save_data[save_key[6]] = "1" if 2 in file_set.selected_stance_details else "0"
        save_data[save_key[7]] = "1" if 3 in file_set.selected_stance_details else "0"
        save_data[save_key[8]] = "1" if 4 in file_set.selected_stance_details else "0"
        save_data[save_key[9]] = "1" if 5 in file_set.selected_stance_details else "0"
        save_data[save_key[10]] = "1" if 6 in file_set.selected_stance_details else "0"
        save_data[save_key[11]] = "1" if 7 in file_set.selected_stance_details else "0"
        save_data[save_key[12]] = "1" if file_set.rep_model_file_ctrl.title_parts_ctrl.GetValue() else "0"
        save_data[save_key[13]] = ";".join([f"{om}:{rm}:{r}" for (om, rm, r) in self.frame.morph_panel_ctrl.morph_set_dict[file_idx].get_morph_list()]) + ";" \
            if file_idx in self.frame.morph_panel_ctrl.morph_set_dict else ""
        save_data[save_key[14]] = "1" if self.frame.arm_panel_ctrl.arm_process_flg_avoidance.GetValue() else "0"
        save_data[save_key[15]] = ";".join(list(self.frame.arm_panel_ctrl.get_avoidance_target()[file_idx])) + ";" if file_idx in self.frame.arm_panel_ctrl.get_avoidance_target() else ""
        save_data[save_key[16]] = "1" if self.frame.arm_panel_ctrl.arm_process_flg_alignment.GetValue() else "0"
        save_data[save_key[17]] = "1" if self.frame.arm_panel_ctrl.arm_alignment_finger_flg_ctrl.GetValue() else "0"
        save_data[save_key[18]] = "1" if self.frame.arm_panel_ctrl.arm_alignment_floor_flg_ctrl.GetValue() else "0"
        save_data[save_key[19]] = self.frame.arm_panel_ctrl.alignment_distance_wrist_slider.GetValue()
        save_data[save_key[20]] = self.frame.arm_panel_ctrl.alignment_distance_finger_slider.GetValue()
        save_data[save_key[21]] = self.frame.arm_panel_ctrl.alignment_distance_floor_slider.GetValue()
        save_data[save_key[22]] = "1" if self.frame.arm_panel_ctrl.arm_check_skip_flg_ctrl.GetValue() else "0"
        save_data[save_key[23]] = self.frame.camera_panel_ctrl.camera_vmd_file_ctrl.file_ctrl.GetPath()
        save_data[save_key[24]] = self.frame.camera_panel_ctrl.camera_length_slider.GetValue()
        save_data[save_key[25]] = self.frame.camera_panel_ctrl.camera_set_dict[file_idx + 1].camera_model_file_ctrl.path() if file_idx + 1 in self.frame.camera_panel_ctrl.camera_set_dict else ""
        save_data[save_key[26]] = self.frame.camera_panel_ctrl.camera_set_dict[file_idx + 1].camera_offset_y_ctrl.GetValue() if file_idx + 1 in self.frame.camera_panel_ctrl.camera_set_dict else ""
        
        return save_data

    def on_check_click(self, event: wx.Event):
        self.timer = wx.Timer(self, TIMER_ID)
        self.timer.Start(200)
        self.Bind(wx.EVT_TIMER, self.on_check, id=TIMER_ID)

    # サイジング一括確認
    def on_check(self, event: wx.Event):
        if self.timer:
            self.timer.Stop()
            self.Unbind(wx.EVT_TIMER, id=TIMER_ID)
            
        # 出力先をファイルパネルのコンソールに変更
        sys.stdout = self.console_ctrl

        # サイジング可否チェックのみ
        self.check(event, False)
        return

    def save(self):
        # 履歴保持
        self.bulk_csv_file_ctrl.save()

        # JSON出力
        MFileUtils.save_history(self.frame.mydir_path, self.frame.file_hitories)
        
    # データチェック
    def check(self, event: wx.Event, is_exec: bool):
        # フォーム無効化
        self.disable()
        # タブ固定
        self.fix_tab()

        if not self.bulk_csv_file_ctrl.is_valid():
            # CSVパスが無効な場合、終了
            self.enable()
            self.release_tab()
            return

        result = True
        with open(self.bulk_csv_file_ctrl.path(), encoding='cp932', mode='r') as f:
            reader = csv.reader(f)
            next(reader)  # ヘッダーを読み飛ばす
            
            prev_group_no = -1
            now_model_no = -1
            service_data_txt = ""
            for ridx, rows in enumerate(reader):
                row_no = ridx
                group_no_result, group_no = self.read_csv_row(rows, row_no, 0, "グループNo", True, int, r"\d+", "数値のみ", None)
                org_motion_result, org_motion_path = self.read_csv_row(rows, row_no, 1, "調整対象モーションVMD/VPD", True, str, None, None, (".vmd", ".vpd"))
                org_model_result, org_model_path = self.read_csv_row(rows, row_no, 2, "モーション作成元モデルPMX", True, str, None, None, (".pmx"))
                rep_model_result, rep_model_path = self.read_csv_row(rows, row_no, 3, "モーション変換先モデルPMX", True, str, None, None, (".pmx"))
                stance_center_xz_result, stance_center_xz_datas = self.read_csv_row(rows, row_no, 4, "センターXZ補正", True, int, r"^(0|1)$", "0 もしくは 1", None)
                stance_upper_result, stance_upper_datas = self.read_csv_row(rows, row_no, 5, "上半身補正", True, int, r"^(0|1)$", "0 もしくは 1", None)
                stance_lower_result, stance_lower_datas = self.read_csv_row(rows, row_no, 6, "下半身補正", True, int, r"^(0|1)$", "0 もしくは 1", None)
                stance_leg_ik_result, stance_leg_ik_datas = self.read_csv_row(rows, row_no, 7, "足ＩＫ補正", True, int, r"^(0|1)$", "0 もしくは 1", None)
                stance_toe_result, stance_toe_datas = self.read_csv_row(rows, row_no, 8, "つま先補正", True, int, r"^(0|1)$", "0 もしくは 1", None)
                stance_toe_ik_result, stance_toe_ik_datas = self.read_csv_row(rows, row_no, 9, "つま先ＩＫ補正", True, int, r"^(0|1)$", "0 もしくは 1", None)
                stance_shoulder_result, stance_shoulder_datas = self.read_csv_row(rows, row_no, 10, "肩補正", True, int, r"^(0|1)$", "0 もしくは 1", None)
                stance_center_y_result, stance_center_y_datas = self.read_csv_row(rows, row_no, 11, "センターY補正", True, int, r"^(0|1)$", "0 もしくは 1", None)
                separate_twist_result, separate_twist_datas = self.read_csv_row(rows, row_no, 12, "捩り分散", True, int, r"^(0|1)$", "0 もしくは 1", None)
                morph_result, morph_datas = self.read_csv_row(rows, row_no, 13, "モーフ置換", False, str, r"[^\:]+\:[^\:]+\:\d+\.?\d*\;", "元:先:大きさ;", None)
                arm_avoidance_result, arm_avoidance_datas = self.read_csv_row(rows, row_no, 14, "接触回避", True, int, r"^(0|1)$", "0 もしくは 1", None)
                avoidance_name_result, avoidance_name_datas = self.read_csv_row(rows, row_no, 15, "接触回避剛体", False, str, r"[^\;]+\;", "剛体名;", None)
                arm_alignment_result, arm_alignment_datas = self.read_csv_row(rows, row_no, 16, "位置合わせ", True, int, r"^(0|1)$", "0 もしくは 1", None)
                finger_alignment_result, finger_alignment_datas = self.read_csv_row(rows, row_no, 17, "指位置合わせ", False, int, r"^(0|1)$", "0 もしくは 1", None)
                floor_alignment_result, floor_alignment_datas = self.read_csv_row(rows, row_no, 18, "床位置合わせ", False, int, r"^(0|1)$", "0 もしくは 1", None)
                arm_alignment_length_result, arm_alignment_length_datas = self.read_csv_row(rows, row_no, 19, "手首の距離", False, float, None, None, None)
                finger_alignment_length_result, finger_alignment_length_datas = self.read_csv_row(rows, row_no, 20, "指の距離", False, float, None, None, None)
                floor_alignment_length_result, floor_alignment_length_datas = self.read_csv_row(rows, row_no, 21, "床との距離", False, float, None, None, None)
                arm_check_skip_result, arm_check_skip_datas = self.read_csv_row(rows, row_no, 22, "腕チェックスキップ", True, int, r"^(0|1)$", "0 もしくは 1", None)
                org_camera_motion_result, org_camera_motion_path = self.read_csv_row(rows, row_no, 23, "カメラモーションVMD", False, str, None, None, (".vmd"))
                camera_length_result, camera_length_datas = self.read_csv_row(rows, row_no, 24, "距離稼働範囲", False, float, r"^[1-9]\d*\.?\d*", "1以上", None)
                org_camera_model_result, org_camera_model_path = self.read_csv_row(rows, row_no, 25, "カメラ作成元モデルPMX", False, str, None, None, (".pmx"))
                camera_y_offset_result, camera_y_offset_datas = self.read_csv_row(rows, row_no, 26, "全長Yオフセット", False, float, None, None, None)
                
                result = result & group_no_result & org_motion_result & org_model_result & rep_model_result & stance_center_xz_result \
                    & stance_upper_result & stance_lower_result & stance_leg_ik_result & stance_toe_result & stance_toe_ik_result & stance_shoulder_result \
                    & stance_center_y_result & separate_twist_result & arm_check_skip_result & morph_result & arm_avoidance_result & avoidance_name_result \
                    & arm_alignment_result & finger_alignment_result & floor_alignment_result & arm_alignment_length_result & finger_alignment_length_result \
                    & floor_alignment_length_result & org_camera_motion_result & camera_length_result & org_camera_model_result \
                    & camera_y_offset_result
                
                if result:
                    if prev_group_no != group_no[0]:
                        now_model_no = 1

                        if len(service_data_txt) > 0:
                            # 既存データがある場合、出力
                            logger.info(service_data_txt, decoration=MLogger.DECORATION_BOX)

                        # 先頭モーションの場合
                        service_data_txt = f"\n【グループNo.{group_no[0]}】 \n"

                        arm_avoidance_txt = "あり" if arm_avoidance_datas[0] == 1 else "なし"
                        service_data_txt = f"{service_data_txt}　剛体接触回避: {arm_avoidance_txt}\n"
                        arm_alignment_txt = "あり" if arm_alignment_datas[0] == 1 else "なし"
                        service_data_txt = f"{service_data_txt}　手首位置合わせ: {arm_alignment_txt} ({arm_alignment_length_datas})\n"
                        finger_alignment_txt = "あり" if finger_alignment_datas[0] == 1 else "なし"
                        service_data_txt = f"{service_data_txt}　指位置合わせ: {finger_alignment_txt} ({finger_alignment_length_datas})\n"
                        floor_alignment_txt = "あり" if floor_alignment_datas[0] == 1 else "なし"
                        service_data_txt = f"{service_data_txt}　床位置合わせ: {floor_alignment_txt} ({floor_alignment_length_datas})\n"
                        arm_check_skip_txt = "あり" if arm_check_skip_datas[0] == 1 else "なし"
                        service_data_txt = f"{service_data_txt}　腕チェックスキップ: {arm_check_skip_txt}\n"

                        service_data_txt = f"{service_data_txt}　カメラ: {org_camera_motion_path}\n"
                        service_data_txt = f"{service_data_txt}　距離制限: {camera_length_datas}\n"
                    else:
                        # 複数人モーションの場合、No加算
                        now_model_no += 1

                    service_data_txt = f"{service_data_txt}\n　【人物No.{now_model_no}】 --------- \n"

                    service_data_txt = f"{service_data_txt}　　モーション: {org_motion_path}\n"
                    service_data_txt = f"{service_data_txt}　　作成元モデル: {org_model_path}\n"
                    service_data_txt = f"{service_data_txt}　　変換先モデル: {rep_model_path}\n"
                    service_data_txt = f"{service_data_txt}　　カメラ作成元モデル: {org_camera_model_path}\n"
                    service_data_txt = f"{service_data_txt}　　Yオフセット: {camera_y_offset_datas}\n"
                    
                    detail_stance_list = []
                    if stance_center_xz_datas[0] == 1:
                        detail_stance_list.append("センターXZ補正")
                    if stance_upper_datas[0] == 1:
                        detail_stance_list.append("上半身補正")
                    if stance_lower_datas[0] == 1:
                        detail_stance_list.append("下半身補正")
                    if stance_leg_ik_datas[0] == 1:
                        detail_stance_list.append("足ＩＫ補正")
                    if stance_toe_datas[0] == 1:
                        detail_stance_list.append("つま先補正")
                    if stance_toe_ik_datas[0] == 1:
                        detail_stance_list.append("つま先ＩＫ補正")
                    if stance_shoulder_datas[0] == 1:
                        detail_stance_list.append("肩補正")
                    if stance_center_y_datas[0] == 1:
                        detail_stance_list.append("センターY補正")
                    detail_stance_txt = ", ".join(detail_stance_list)

                    service_data_txt = f"{service_data_txt}　　スタンス追加補正有無: {detail_stance_txt}\n"

                    twist_txt = "あり" if separate_twist_datas[0] == 1 else "なし"
                    service_data_txt = f"{service_data_txt}　　捩り分散有無: {twist_txt}\n"

                    # モーフデータ
                    morph_list = []
                    for morph_data in morph_datas:
                        m = re.findall(r"([^\:]+)\:([^\:]+)\:(\d+\.?\d*)\;", morph_data)
                        morph_list.append(f"{m[0][0]} → {m[0][1]} ({float(m[0][2])})")
                    morph_txt = ", ".join(morph_list)
                    service_data_txt = f"{service_data_txt}　　モーフ置換: {morph_txt}\n"

                    # 接触回避データ
                    arm_avoidance_name_list = []
                    for avoidance_data in avoidance_name_datas:
                        m = re.findall(r"([^\:]+)\;", avoidance_data)
                        arm_avoidance_name_list.append(m[0])
                    arm_avoidance_name_txt = ", ".join(arm_avoidance_name_list)
                    service_data_txt = f"{service_data_txt}　　対象剛体名: {arm_avoidance_name_txt}\n"

                prev_group_no = group_no[0]

        if result:
            if is_exec:
                # 全部OKなら処理開始
                self.load(event, 0)
            else:

                if len(service_data_txt) > 0:
                    # 既存データがある場合、最後に出力
                    logger.info(service_data_txt, decoration=MLogger.DECORATION_BOX)

                # OKかつ確認のみの場合、出力して終了
                logger.info("CSVデータの確認が成功しました。", decoration=MLogger.DECORATION_BOX, title="OK")

                self.enable()
                self.release_tab()
                return
        else:
            logger.error("CSVデータに不整合があるため、処理を中断します", decoration=MLogger.DECORATION_BOX)

            self.enable()
            self.release_tab()

            return

    def read_csv_row(self, rows: list, row_no: int, row_idx: int, row_name: str, row_required: bool, row_type: type, row_regex: str, row_regex_str: str, path_exts: tuple):
        try:
            if row_required and (len(rows) < row_idx or not rows[row_idx]):
                logger.warning("%s行目の%s（%s列目）が設定されていません", row_no + 1, row_name, row_idx + 1)
                return False, None
            
            try:
                if rows[row_idx] and not row_type(rows[row_idx]):
                    pass
            except Exception:
                row_type_str = "半角整数" if row_type == int else "半角数字"
                logger.warning("%s行目の%s（%s列目）の型（%s）が合っていません", row_no + 1, row_name, row_idx + 1, row_type_str)
                return False, None
            
            if rows[row_idx] and row_regex and not re.findall(row_regex, rows[row_idx]):
                logger.warning("%s行目の%s（%s列目）の表示形式（%s）が合っていません", row_no + 1, row_name, row_idx + 1, row_regex_str)
                return False, None

            if rows[row_idx] and path_exts:
                if not rows[row_idx] or (not os.path.exists(rows[row_idx]) or not os.path.isfile(rows[row_idx])):
                    logger.warning("%s行目の%s（%s列目）のファイルが存在していません", row_no + 1, row_name, row_idx + 1)
                    return False, None

                # ファイル名・拡張子
                file_name, ext = os.path.splitext(os.path.basename(rows[row_idx]))
                if (ext not in path_exts):
                    logger.warning("%s行目の%s（%s列目）のファイル拡張子（%s）が合っていません", row_no + 1, row_name, row_idx + 1, \
                                   ','.join(map(str, path_exts)) if len(path_exts) > 1 else path_exts)
                    return False, None

            # 読み取り実施
            if rows[row_idx] and row_regex:
                # 正規表現の場合は、リスト変換して返す
                if row_type:
                    # 型指定がある場合は変換して返す
                    return True, [row_type(v) for v in re.findall(row_regex, rows[row_idx])]
                else:
                    return True, re.findall(row_regex, rows[row_idx])

            if (row_type == float or row_type == int) and not rows[row_idx]:
                # 数値で任意はゼロ設定
                return True, 0
            elif row_type:
                return True, row_type(rows[row_idx])
            
            return True, rows[row_idx]
        except Exception as e:
            logger.warning("%s行目の%s（%s列目）の読み取りに失敗しました\n%s", row_no + 1, row_name, row_idx + 1, e)
            return False, None

    # 読み込み
    def load(self, event, line_idx):
        # グループ単位で設定
        now_group_no = -1
        now_motion_idx = -1
        row_no = 0
        is_buld = False
        with open(self.bulk_csv_file_ctrl.path(), encoding='cp932', mode='r') as f:
            reader = csv.reader(f)
            next(reader)  # ヘッダーを読み飛ばす
            
            for ridx, rows in enumerate(reader):
                row_no = ridx

                if row_no < line_idx:
                    # 自分より前の行の場合、スキップ
                    continue

                group_no_result, group_no = self.read_csv_row(rows, row_no, 0, "グループNo", True, int, r"\d+", "数値のみ", None)

                if len(group_no) == 0:
                    # グループNOが取れなかったから終了
                    return

                if len(group_no) > 0 and row_no == line_idx:
                    # 指定INDEXに到達したら設定して読み取り開始
                    now_motion_idx = 0
                    now_group_no = group_no[0]
                else:
                    now_motion_idx += 1

                if len(group_no) > 0 and group_no[0] != now_group_no:
                    # グループNOが変わっていたら、そのまま終了
                    continue
                
                # bulk対象
                is_buld = True
                
                group_no_result, group_no = self.read_csv_row(rows, row_no, 0, "グループNo", True, int, r"\d+", "数値のみ", None)
                org_motion_result, org_motion_path = self.read_csv_row(rows, row_no, 1, "調整対象モーションVMD/VPD", True, str, None, None, (".vmd", ".vpd"))
                org_model_result, org_model_path = self.read_csv_row(rows, row_no, 2, "モーション作成元モデルPMX", True, str, None, None, (".pmx"))
                rep_model_result, rep_model_path = self.read_csv_row(rows, row_no, 3, "モーション変換先モデルPMX", True, str, None, None, (".pmx"))
                stance_center_xz_result, stance_center_xz_datas = self.read_csv_row(rows, row_no, 4, "センターXZ補正", True, int, r"^(0|1)$", "0 もしくは 1", None)
                stance_upper_result, stance_upper_datas = self.read_csv_row(rows, row_no, 5, "上半身補正", True, int, r"^(0|1)$", "0 もしくは 1", None)
                stance_lower_result, stance_lower_datas = self.read_csv_row(rows, row_no, 6, "下半身補正", True, int, r"^(0|1)$", "0 もしくは 1", None)
                stance_leg_ik_result, stance_leg_ik_datas = self.read_csv_row(rows, row_no, 7, "足ＩＫ補正", True, int, r"^(0|1)$", "0 もしくは 1", None)
                stance_toe_result, stance_toe_datas = self.read_csv_row(rows, row_no, 8, "つま先補正", True, int, r"^(0|1)$", "0 もしくは 1", None)
                stance_toe_ik_result, stance_toe_ik_datas = self.read_csv_row(rows, row_no, 9, "つま先ＩＫ補正", True, int, r"^(0|1)$", "0 もしくは 1", None)
                stance_shoulder_result, stance_shoulder_datas = self.read_csv_row(rows, row_no, 10, "肩補正", True, int, r"^(0|1)$", "0 もしくは 1", None)
                stance_center_y_result, stance_center_y_datas = self.read_csv_row(rows, row_no, 11, "センターY補正", True, int, r"^(0|1)$", "0 もしくは 1", None)
                separate_twist_result, separate_twist_datas = self.read_csv_row(rows, row_no, 12, "捩り分散", True, int, r"^(0|1)$", "0 もしくは 1", None)
                morph_result, morph_datas = self.read_csv_row(rows, row_no, 13, "モーフ置換", False, str, r"[^\:]+\:[^\:]+\:\d+\.?\d*\;", "元:先:大きさ;", None)
                arm_avoidance_result, arm_avoidance_datas = self.read_csv_row(rows, row_no, 14, "接触回避", True, int, r"^(0|1)$", "0 もしくは 1", None)
                avoidance_name_result, avoidance_name_datas = self.read_csv_row(rows, row_no, 15, "接触回避剛体", False, str, r"[^\;]+\;", "剛体名;", None)
                arm_alignment_result, arm_alignment_datas = self.read_csv_row(rows, row_no, 16, "位置合わせ", True, int, r"^(0|1)$", "0 もしくは 1", None)
                finger_alignment_result, finger_alignment_datas = self.read_csv_row(rows, row_no, 17, "指位置合わせ", False, int, r"^(0|1)$", "0 もしくは 1", None)
                floor_alignment_result, floor_alignment_datas = self.read_csv_row(rows, row_no, 18, "床位置合わせ", False, int, r"^(0|1)$", "0 もしくは 1", None)
                arm_alignment_length_result, arm_alignment_length_datas = self.read_csv_row(rows, row_no, 19, "手首の距離", False, float, None, None, None)
                finger_alignment_length_result, finger_alignment_length_datas = self.read_csv_row(rows, row_no, 20, "指の距離", False, float, None, None, None)
                floor_alignment_length_result, floor_alignment_length_datas = self.read_csv_row(rows, row_no, 21, "床との距離", False, float, None, None, None)
                arm_check_skip_result, arm_check_skip_datas = self.read_csv_row(rows, row_no, 22, "腕チェックスキップ", True, int, r"^(0|1)$", "0 もしくは 1", None)
                org_camera_motion_result, org_camera_motion_path = self.read_csv_row(rows, row_no, 23, "カメラモーションVMD", False, str, None, None, (".vmd"))
                camera_length_result, camera_length_datas = self.read_csv_row(rows, row_no, 24, "距離稼働範囲", False, float, None, None, None)
                org_camera_model_result, org_camera_model_path = self.read_csv_row(rows, row_no, 25, "カメラ作成元モデルPMX", False, str, None, None, (".pmx"))
                camera_y_offset_result, camera_y_offset_datas = self.read_csv_row(rows, row_no, 26, "全長Yオフセット", False, float, None, None, None)
                
                if now_motion_idx == 0:
                    # 複数パネルはクリア
                    self.frame.multi_panel_ctrl.on_clear_set(event)

                    # ファイルパネル設定
                    self.frame.file_panel_ctrl.file_set.motion_vmd_file_ctrl.file_ctrl.SetPath(org_motion_path)
                    self.frame.file_panel_ctrl.file_set.org_model_file_ctrl.file_ctrl.SetPath(org_model_path)
                    self.frame.file_panel_ctrl.file_set.rep_model_file_ctrl.file_ctrl.SetPath(rep_model_path)
                    self.frame.file_panel_ctrl.file_set.output_vmd_file_ctrl.file_ctrl.SetPath("")

                    self.frame.file_panel_ctrl.file_set.org_model_file_ctrl.title_parts_ctrl.SetValue(
                        stance_center_xz_datas[0] | stance_upper_datas[0] | stance_lower_datas[0] | stance_leg_ik_datas[0] | \
                        stance_toe_datas[0] | stance_toe_ik_datas[0] | stance_shoulder_datas[0] | stance_center_y_datas[0]
                    )

                    # スタンス追加補正
                    self.frame.file_panel_ctrl.file_set.selected_stance_details = []
                    if stance_center_xz_datas[0] == 1:
                        self.frame.file_panel_ctrl.file_set.selected_stance_details.append(0)
                    if stance_upper_datas[0] == 1:
                        self.frame.file_panel_ctrl.file_set.selected_stance_details.append(1)
                    if stance_lower_datas[0] == 1:
                        self.frame.file_panel_ctrl.file_set.selected_stance_details.append(2)
                    if stance_leg_ik_datas[0] == 1:
                        self.frame.file_panel_ctrl.file_set.selected_stance_details.append(3)
                    if stance_toe_datas[0] == 1:
                        self.frame.file_panel_ctrl.file_set.selected_stance_details.append(4)
                    if stance_toe_ik_datas[0] == 1:
                        self.frame.file_panel_ctrl.file_set.selected_stance_details.append(5)
                    if stance_shoulder_datas[0] == 1:
                        self.frame.file_panel_ctrl.file_set.selected_stance_details.append(6)
                    if stance_center_y_datas[0] == 1:
                        self.frame.file_panel_ctrl.file_set.selected_stance_details.append(7)

                    # 捩り分散
                    self.frame.file_panel_ctrl.file_set.rep_model_file_ctrl.title_parts_ctrl.SetValue(separate_twist_datas[0])

                    # 腕チェックスキップ
                    self.frame.arm_panel_ctrl.arm_check_skip_flg_ctrl.SetValue(arm_check_skip_datas[0])
                    
                    # モーフデータ
                    self.frame.morph_panel_ctrl.bulk_morph_set_dict[1] = []
                    for morph_data in morph_datas:
                        m = re.findall(r"([^\:]+)\:([^\:]+)\:(\d+\.?\d*)\;", morph_data)
                        self.frame.morph_panel_ctrl.bulk_morph_set_dict[1].append((m[0][0], m[0][1], float(m[0][2])))

                    # 接触回避
                    self.frame.arm_panel_ctrl.arm_process_flg_avoidance.SetValue(arm_avoidance_datas[0])

                    # 接触回避データ
                    self.frame.arm_panel_ctrl.bulk_avoidance_set_dict[0] = []
                    for avoidance_data in avoidance_name_datas:
                        m = re.findall(r"([^\:]+)\;", avoidance_data)
                        self.frame.arm_panel_ctrl.bulk_avoidance_set_dict[0].append(m[0][0])

                    # 位置合わせ
                    self.frame.arm_panel_ctrl.arm_process_flg_alignment.SetValue(arm_alignment_datas[0])
                    self.frame.arm_panel_ctrl.arm_alignment_finger_flg_ctrl.SetValue(finger_alignment_datas[0])
                    self.frame.arm_panel_ctrl.arm_alignment_floor_flg_ctrl.SetValue(floor_alignment_datas[0])

                    # 位置合わせ距離
                    self.frame.arm_panel_ctrl.alignment_distance_wrist_slider.SetValue(arm_alignment_length_datas)
                    self.frame.arm_panel_ctrl.alignment_distance_finger_slider.SetValue(finger_alignment_length_datas)
                    self.frame.arm_panel_ctrl.alignment_distance_floor_slider.SetValue(floor_alignment_length_datas)
                    
                    # カメラ
                    self.frame.camera_panel_ctrl.camera_vmd_file_ctrl.file_ctrl.SetPath(org_camera_motion_path)
                    self.frame.camera_panel_ctrl.output_camera_vmd_file_ctrl.file_ctrl.SetPath("")
                    self.frame.camera_panel_ctrl.camera_length_slider.SetValue(camera_length_datas)

                    # カメラ元情報
                    self.frame.camera_panel_ctrl.initialize(event)
                    self.frame.camera_panel_ctrl.camera_set_dict[1].camera_model_file_ctrl.file_ctrl.SetPath(org_camera_model_path)
                    self.frame.camera_panel_ctrl.camera_set_dict[1].camera_offset_y_ctrl.SetValue(camera_y_offset_datas)
                    
                    # 出力パス変更
                    self.frame.file_panel_ctrl.file_set.set_output_vmd_path(event)
                    self.frame.camera_panel_ctrl.set_output_vmd_path(event)
                else:
                    # 複数パネルセット追加
                    self.frame.multi_panel_ctrl.on_add_set(event)

                    # ファイルパネル設定
                    self.frame.multi_panel_ctrl.file_set_list[now_motion_idx - 1].motion_vmd_file_ctrl.file_ctrl.SetPath(org_motion_path)
                    self.frame.multi_panel_ctrl.file_set_list[now_motion_idx - 1].org_model_file_ctrl.file_ctrl.SetPath(org_model_path)
                    self.frame.multi_panel_ctrl.file_set_list[now_motion_idx - 1].rep_model_file_ctrl.file_ctrl.SetPath(rep_model_path)
                    self.frame.multi_panel_ctrl.file_set_list[now_motion_idx - 1].output_vmd_file_ctrl.file_ctrl.SetPath("")

                    self.frame.multi_panel_ctrl.file_set_list[now_motion_idx - 1].org_model_file_ctrl.title_parts_ctrl.SetValue(
                        stance_center_xz_datas[0] | stance_upper_datas[0] | stance_lower_datas[0] | stance_leg_ik_datas[0] | \
                        stance_toe_datas[0] | stance_toe_ik_datas[0] | stance_shoulder_datas[0] | stance_center_y_datas[0]
                    )

                    # スタンス追加補正
                    self.frame.multi_panel_ctrl.file_set_list[now_motion_idx - 1].selected_stance_details = []
                    if stance_center_xz_datas[0] == 1:
                        self.frame.multi_panel_ctrl.file_set_list[now_motion_idx - 1].selected_stance_details.append(0)
                    if stance_upper_datas[0] == 1:
                        self.frame.multi_panel_ctrl.file_set_list[now_motion_idx - 1].selected_stance_details.append(1)
                    if stance_lower_datas[0] == 1:
                        self.frame.multi_panel_ctrl.file_set_list[now_motion_idx - 1].selected_stance_details.append(2)
                    if stance_leg_ik_datas[0] == 1:
                        self.frame.multi_panel_ctrl.file_set_list[now_motion_idx - 1].selected_stance_details.append(3)
                    if stance_toe_datas[0] == 1:
                        self.frame.multi_panel_ctrl.file_set_list[now_motion_idx - 1].selected_stance_details.append(4)
                    if stance_toe_ik_datas[0] == 1:
                        self.frame.multi_panel_ctrl.file_set_list[now_motion_idx - 1].selected_stance_details.append(5)
                    if stance_shoulder_datas[0] == 1:
                        self.frame.multi_panel_ctrl.file_set_list[now_motion_idx - 1].selected_stance_details.append(6)
                    if stance_center_y_datas[0] == 1:
                        self.frame.multi_panel_ctrl.file_set_list[now_motion_idx - 1].selected_stance_details.append(7)

                    # 捩り分散
                    self.frame.multi_panel_ctrl.file_set_list[now_motion_idx - 1].rep_model_file_ctrl.title_parts_ctrl.SetValue(separate_twist_datas[0])

                    # モーフデータ
                    self.frame.morph_panel_ctrl.bulk_morph_set_dict[now_motion_idx + 1] = []
                    for morph_data in morph_datas:
                        m = re.findall(r"([^\:]+)\:([^\:]+)\:(\d+\.?\d*)\;", morph_data)
                        self.frame.morph_panel_ctrl.bulk_morph_set_dict[now_motion_idx + 1].append((m[0][0], m[0][1], float(m[0][2])))

                    # 接触回避データ
                    self.frame.arm_panel_ctrl.bulk_avoidance_set_dict[now_motion_idx - 1] = []
                    for avoidance_data in avoidance_name_datas:
                        m = re.findall(r"([^\:]+)\;", avoidance_data)
                        self.frame.arm_panel_ctrl.bulk_avoidance_set_dict[now_motion_idx - 1].append(m[0][0])

                    # 指位置合わせは常に0(ダイアログ防止)
                    self.frame.arm_panel_ctrl.arm_alignment_finger_flg_ctrl.SetValue(0)

                    # カメラ元情報
                    self.frame.camera_panel_ctrl.initialize(event)
                    self.frame.camera_panel_ctrl.camera_set_dict[now_motion_idx + 1].camera_model_file_ctrl.file_ctrl.SetPath(org_camera_model_path)
                    self.frame.camera_panel_ctrl.camera_set_dict[now_motion_idx + 1].camera_offset_y_ctrl.SetValue(camera_y_offset_datas)
                    
                    # 出力パス変更
                    self.frame.multi_panel_ctrl.file_set_list[now_motion_idx - 1].set_output_vmd_path(event)
        
        if not is_buld:
            # Bulk終了
            self.finish_buld()

            return

        # 一旦リリース
        self.frame.release_tab()
        # ファイルタブに移動
        self.frame.note_ctrl.ChangeSelection(self.frame.file_panel_ctrl.tab_idx)
        # フォーム無効化
        self.frame.file_panel_ctrl.disable()
        # タブ固定
        self.frame.file_panel_ctrl.fix_tab()

        # ファイルタブのコンソール
        sys.stdout = self.frame.file_panel_ctrl.console_ctrl

        self.frame.elapsed_time = 0
        result = True
        result = self.frame.is_valid() and result

        if not result:
            # タブ移動可
            self.frame.release_tab()
            # フォーム有効化
            self.frame.enable()

            return result

        # 読み込み開始
        if self.frame.load_worker:
            logger.error("まだ処理が実行中です。終了してから再度実行してください。", decoration=MLogger.DECORATION_BOX)
        else:
            # 停止ボタンに切り替え
            self.frame.file_panel_ctrl.check_btn_ctrl.SetLabel("読み込み処理停止")
            self.frame.file_panel_ctrl.check_btn_ctrl.Enable()

            # 別スレッドで実行(次行がない場合、-1で終了フラグ)
            self.frame.load_worker = LoadWorkerThread(self.frame, BulkLoadThreadEvent, row_no if row_no > line_idx else -1, True, False, False)
            self.frame.load_worker.start()

        return result
    
    # 読み込み完了処理
    def on_load_result(self, event: wx.Event):
        self.frame.elapsed_time = event.elapsed_time
        
        # タブ移動可
        self.frame.release_tab()
        # フォーム有効化
        self.frame.enable()
        # ワーカー終了
        self.frame.load_worker = None
        # プログレス非表示
        self.frame.file_panel_ctrl.gauge_ctrl.SetValue(0)

        if not event.result:
            # 終了音を鳴らす
            self.frame.sound_finish()
            
            event.Skip()
            return False

        result = self.frame.is_loaded_valid()

        if not result:
            # タブ移動可
            self.frame.release_tab()
            # フォーム有効化
            self.frame.enable()

            event.Skip()
            return False
        
        logger.info("ファイルデータ読み込みが完了しました", decoration=MLogger.DECORATION_BOX, title="OK")

        # フォーム無効化
        self.frame.file_panel_ctrl.disable()
        # タブ固定
        self.frame.file_panel_ctrl.fix_tab()

        if self.frame.worker:
            logger.error("まだ処理が実行中です。終了してから再度実行してください。", decoration=MLogger.DECORATION_BOX)
        else:
            # 停止ボタンに切り替え
            self.frame.file_panel_ctrl.exec_btn_ctrl.SetLabel("VMDサイジング停止")
            self.frame.file_panel_ctrl.exec_btn_ctrl.Enable()

            # 別スレッドで実行
            self.frame.worker = SizingWorkerThread(self.frame, BulkSizingThreadEvent, event.target_idx, self.frame.is_saving, self.frame.is_out_log)
            self.frame.worker.start()

    # スレッド実行結果
    def on_exec_result(self, event: wx.Event):
        # 実行ボタンに切り替え
        self.frame.file_panel_ctrl.exec_btn_ctrl.SetLabel("VMDサイジング実行")
        self.frame.file_panel_ctrl.exec_btn_ctrl.Enable()

        if not event.result:
            # 終了音を鳴らす
            self.frame.sound_finish()

            event.Skip()
            return False
        
        self.frame.elapsed_time += event.elapsed_time
        worked_time = "\n処理時間: {0}".format(self.frame.show_worked_time())
        logger.info(worked_time)

        if self.frame.is_out_log and event.output_log_path and os.path.exists(event.output_log_path):
            # ログ出力対象である場合、追記
            with open(event.output_log_path, mode='a', encoding='utf-8') as f:
                f.write(worked_time)

        # ワーカー終了
        self.frame.worker = None
        
        if event.target_idx >= 0:
            # 次のターゲットがある場合、次を処理
            logger.info("\n----------------------------------")

            return self.load(event, event.target_idx + 1)

        # Bulk終了
        self.finish_buld()

    def finish_buld(self):
        # ファイルタブのコンソール
        sys.stdout = self.frame.file_panel_ctrl.console_ctrl

        # 終了音を鳴らす
        self.frame.sound_finish()

        # ファイルタブのコンソール
        if sys.stdout != self.frame.file_panel_ctrl.console_ctrl:
            sys.stdout = self.frame.file_panel_ctrl.console_ctrl

        # Bulk用データ消去
        self.frame.morph_panel_ctrl.bulk_morph_set_dict = {}
        self.frame.arm_panel_ctrl.bulk_avoidance_set_dict = {}
        self.frame.camera_panel_ctrl.bulk_camera_set_dict = {}

        # タブ移動可
        self.frame.release_tab()
        # フォーム有効化
        self.frame.enable()
        # プログレス非表示
        self.frame.file_panel_ctrl.gauge_ctrl.SetValue(0)

        logger.info("全てのサイジング処理が終了しました", decoration=MLogger.DECORATION_BOX, title="一括処理")
        