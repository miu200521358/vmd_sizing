# -*- coding: utf-8 -*-
#
import wx
import wx.lib.newevent
import sys

from form.panel.BasePanel import BasePanel
from form.parts.SizingFileSet import SizingFileSet
from form.parts.ConsoleCtrl import ConsoleCtrl
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MFormUtils, MFileUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)
TIMER_ID = wx.NewId()


class FilePanel(BasePanel):
    
    def __init__(self, frame: wx.Frame, parent: wx.Notebook, tab_idx: int, file_hitories: dict):
        super().__init__(frame, parent, tab_idx)
        self.file_hitories = file_hitories
        self.timer = None

        # ファイルセット
        self.file_set = SizingFileSet(frame, self, self.file_hitories, 1)
        self.sizer.Add(self.file_set.set_sizer, 0, wx.ALL, 0)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 変換前チェックボタン
        self.check_btn_ctrl = wx.Button(self, wx.ID_ANY, u"変換前チェック", wx.DefaultPosition, wx.Size(200, 50), 0)
        self.check_btn_ctrl.SetToolTip(u"入力されたファイル情報で処理可能かどうか、チェックを行います。")
        self.check_btn_ctrl.Bind(wx.EVT_LEFT_DCLICK, self.on_doubleclick)
        self.check_btn_ctrl.Bind(wx.EVT_LEFT_DOWN, self.on_check_click)
        btn_sizer.Add(self.check_btn_ctrl, 0, wx.ALL, 5)

        # 実行ボタン
        self.exec_btn_ctrl = wx.Button(self, wx.ID_ANY, u"VMDサイジング実行", wx.DefaultPosition, wx.Size(200, 50), 0)
        self.exec_btn_ctrl.SetToolTip(u"VMDサイジング処理を実行します。")
        self.exec_btn_ctrl.Bind(wx.EVT_LEFT_DCLICK, self.on_doubleclick)
        self.exec_btn_ctrl.Bind(wx.EVT_LEFT_DOWN, self.on_exec_click)
        btn_sizer.Add(self.exec_btn_ctrl, 0, wx.ALL, 5)

        self.sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.SHAPED, 5)

        # コンソール
        self.console_ctrl = ConsoleCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(-1, -1), \
                                        wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_NONE | wx.HSCROLL | wx.VSCROLL | wx.WANTS_CHARS)
        self.console_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        self.console_ctrl.Bind(wx.EVT_CHAR, lambda event: MFormUtils.on_select_all(event, self.console_ctrl))
        self.sizer.Add(self.console_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        # ゲージ
        self.gauge_ctrl = wx.Gauge(self, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL)
        self.gauge_ctrl.SetValue(0)
        self.sizer.Add(self.gauge_ctrl, 0, wx.ALL | wx.EXPAND, 5)

        self.fit()
    
    # マルチプロセス用flush
    def print(self, txt):
        print(txt)
        wx.GetApp().Yield()

    # フォーム無効化
    def disable(self):
        self.file_set.disable()
        self.check_btn_ctrl.Disable()
        self.exec_btn_ctrl.Disable()

    # フォーム無効化
    def enable(self):
        self.file_set.enable()
        self.check_btn_ctrl.Enable()
        self.exec_btn_ctrl.Enable()
    
    def on_doubleclick(self, event: wx.Event):
        self.timer.Stop()
        logger.warning("ダブルクリックされました。", decoration=MLogger.DECORATION_BOX)
        event.Skip(False)
        return False
    
    def on_check_click(self, event: wx.Event):
        self.timer = wx.Timer(self, TIMER_ID)
        self.timer.Start(200)
        self.Bind(wx.EVT_TIMER, self.on_check, id=TIMER_ID)

    # 実行前チェック
    def on_check(self, event: wx.Event):
        self.timer.Stop()
        self.Unbind(wx.EVT_TIMER, id=TIMER_ID)
        # 出力先をファイルパネルのコンソールに変更
        sys.stdout = self.console_ctrl

        if self.check_btn_ctrl.GetLabel() == "読み込み処理停止" and self.frame.load_worker:
            # フォーム無効化
            self.disable()
            # 停止状態でボタン押下時、停止
            self.frame.load_worker.stop()

            # タブ移動可
            self.frame.release_tab()
            # フォーム有効化
            self.frame.enable()
            # ワーカー終了
            self.frame.load_worker = None
            # プログレス非表示
            self.gauge_ctrl.SetValue(0)

            logger.warning("読み込み処理を中断します。", decoration=MLogger.DECORATION_BOX)
            
            event.Skip(False)
        elif not self.frame.load_worker:
            # フォーム無効化
            self.disable()
            # タブ固定
            self.fix_tab()
            # コンソールクリア
            self.console_ctrl.Clear()

            # 履歴保持
            self.save()

            # 一旦読み込み(そのままチェック)
            self.frame.load(event, target_idx=0)
            
            event.Skip()
        else:
            logger.error("まだ処理が実行中です。終了してから再度実行してください。", decoration=MLogger.DECORATION_BOX)
            event.Skip(False)

    def on_exec_click(self, event: wx.Event):
        self.timer = wx.Timer(self, TIMER_ID)
        self.timer.Start(200)
        self.Bind(wx.EVT_TIMER, self.on_exec, id=TIMER_ID)

    # サイジング実行
    def on_exec(self, event: wx.Event):
        if self.timer:
            self.timer.Stop()
            self.Unbind(wx.EVT_TIMER, id=TIMER_ID)
            
        # 出力先をファイルパネルのコンソールに変更
        sys.stdout = self.console_ctrl

        if self.exec_btn_ctrl.GetLabel() == "VMDサイジング停止" and self.frame.worker:
            # フォーム無効化
            self.disable()
            # 停止状態でボタン押下時、停止
            self.frame.worker.stop()

            # タブ移動可
            self.frame.release_tab()
            # フォーム有効化
            self.frame.enable()
            # ワーカー終了
            self.frame.worker = None
            # プログレス非表示
            self.gauge_ctrl.SetValue(0)

            logger.warning("VMDサイジングを中断します。", decoration=MLogger.DECORATION_BOX)
            
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
            self.frame.load(event, is_exec=True, target_idx=0)
            
            event.Skip()
        else:
            logger.error("まだ処理が実行中です。終了してから再度実行してください。", decoration=MLogger.DECORATION_BOX)
            event.Skip(False)

    def set_output_vmd_path(self, event, is_force=False):
        self.file_set.set_output_vmd_path(event, is_force)
        # カメラ出力パスも一緒に変更する
        self.frame.camera_panel_ctrl.header_panel.set_output_vmd_path(event)

    def save(self):

        # 履歴保持
        self.frame.file_panel_ctrl.file_set.save()

        # multiのも全部保持
        for file_set in self.frame.multi_panel_ctrl.file_set_list:
            file_set.save()

        # カメラ履歴保持
        self.frame.camera_panel_ctrl.save()

        # カメラ元モデル保持
        for camera_set in self.frame.camera_panel_ctrl.camera_set_dict.values():
            camera_set.camera_model_file_ctrl.save()

        # JSON出力
        MFileUtils.save_history(self.frame.mydir_path, self.frame.file_hitories)
