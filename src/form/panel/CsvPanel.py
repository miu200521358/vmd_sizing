# -*- coding: utf-8 -*-
#
import wx
import wx.lib.newevent
import sys

from form.panel.BasePanel import BasePanel
from form.parts.BaseFilePickerCtrl import BaseFilePickerCtrl
from form.parts.ConsoleCtrl import ConsoleCtrl
from form.worker.CsvWorkerThread import CsvWorkerThread
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MFormUtils, MFileUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)

# イベント定義
(CsvThreadEvent, EVT_CSV_THREAD) = wx.lib.newevent.NewEvent()


class CsvPanel(BasePanel):
    
    def __init__(self, frame: wx.Frame, parent: wx.Notebook, tab_idx: int):
        super().__init__(frame, parent, tab_idx)
        self.convert_csv_worker = None

        self.description_txt = wx.StaticText(self, wx.ID_ANY, "指定されたVMDファイルの解析結果を、ボーン/モーフ/カメラに分けてCSVファイルとして出力します。", wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.description_txt, 0, wx.ALL, 5)

        self.static_line = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.sizer.Add(self.static_line, 0, wx.EXPAND | wx.ALL, 5)

        # CSVファイルコントロール
        self.vmd_file_ctrl = BaseFilePickerCtrl(frame, self, u"VMDファイル", u"VMDファイルを開く", ("vmd"), wx.FLP_DEFAULT_STYLE, \
                                                u"CSVに変換したいVMD出力パスを指定してください。", \
                                                is_aster=False, is_save=False, set_no=0)
        self.sizer.Add(self.vmd_file_ctrl.sizer, 1, wx.EXPAND, 0)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # CSV変換実行ボタン
        self.csv_btn_ctrl = wx.Button(self, wx.ID_ANY, u"CSV変換実行", wx.DefaultPosition, wx.Size(200, 50), 0)
        self.csv_btn_ctrl.SetToolTip(u"VMDをCSVに変換します。")
        self.csv_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_convert_csv)
        btn_sizer.Add(self.csv_btn_ctrl, 0, wx.ALL, 5)

        self.sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.SHAPED, 5)

        # コンソール
        self.console_ctrl = ConsoleCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(-1, 420), \
                                        wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_NONE | wx.HSCROLL | wx.VSCROLL | wx.WANTS_CHARS)
        self.console_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        self.console_ctrl.Bind(wx.EVT_CHAR, lambda event: MFormUtils.on_select_all(event, self.console_ctrl))
        self.sizer.Add(self.console_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        # ゲージ
        self.gauge_ctrl = wx.Gauge(self, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL)
        self.gauge_ctrl.SetValue(0)
        self.sizer.Add(self.gauge_ctrl, 0, wx.ALL | wx.EXPAND, 5)

        self.fit()

        # フレームに変換完了処理バインド
        self.frame.Bind(EVT_CSV_THREAD, self.on_convert_csv_result)

    # フォーム無効化
    def disable(self):
        self.vmd_file_ctrl.disable()
        self.csv_btn_ctrl.Disable()

    # フォーム無効化
    def enable(self):
        self.vmd_file_ctrl.enable()
        self.csv_btn_ctrl.Enable()

    # CSV変換
    def on_convert_csv(self, event: wx.Event):
        # フォーム無効化
        self.disable()
        # タブ固定
        self.fix_tab()
        # コンソールクリア
        self.console_ctrl.Clear()
        # 出力先をCSVパネルのコンソールに変更
        sys.stdout = self.console_ctrl

        wx.GetApp().Yield()

        self.elapsed_time = 0
        result = True
        result = self.vmd_file_ctrl.is_valid() and result

        if not result:
            # 終了音
            self.frame.sound_finish()
            # タブ移動可
            self.release_tab()
            # フォーム有効化
            self.enable()
            # 出力先をデフォルトに戻す
            sys.stdout = self.frame.file_panel_ctrl.console_ctrl

            return result

        # CSV変換開始
        if self.convert_csv_worker:
            logger.error("まだ処理が実行中です。終了してから再度実行してください。", decoration=MLogger.DECORATION_BOX)
        else:
            # 別スレッドで実行
            self.convert_csv_worker = CsvWorkerThread(self.frame, CsvThreadEvent)
            self.convert_csv_worker.start()
            self.convert_csv_worker.stop_event.set()

        return result

        event.Skip()

    # CSV変換完了処理
    def on_convert_csv_result(self, event: wx.Event):
        self.elapsed_time = event.elapsed_time

        # 終了音
        self.frame.sound_finish()

        # タブ移動可
        self.release_tab()
        # フォーム有効化
        self.enable()
        # ワーカー終了
        self.convert_csv_worker = None
        # プログレス非表示
        self.gauge_ctrl.SetValue(0)

        if not event.result:
            logger.error("CSV変換処理に失敗しました。", decoration=MLogger.DECORATION_BOX)
            
            event.Skip()
            return False

        logger.info("CSV変換が完了しました", decoration=MLogger.DECORATION_BOX, title="OK")

        # 出力先をデフォルトに戻す
        sys.stdout = self.frame.file_panel_ctrl.console_ctrl
