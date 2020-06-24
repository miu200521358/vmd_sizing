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


class FilePanel(BasePanel):
    
    def __init__(self, frame: wx.Frame, parent: wx.Notebook, tab_idx: int, file_hitories: dict):
        super().__init__(frame, parent, tab_idx)
        self.file_hitories = file_hitories

        # ファイルセット
        self.file_set = SizingFileSet(frame, self, self.file_hitories, 1)
        self.sizer.Add(self.file_set.set_sizer, 0, wx.ALL, 0)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 変換前チェックボタン
        self.check_btn_ctrl = wx.Button(self, wx.ID_ANY, u"変換前チェック", wx.DefaultPosition, wx.Size(200, 50), 0)
        self.check_btn_ctrl.SetToolTip(u"入力されたファイル情報で処理可能かどうか、チェックを行います。")
        self.check_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_check)
        btn_sizer.Add(self.check_btn_ctrl, 0, wx.ALL, 5)

        # 実行ボタン
        self.exec_btn_ctrl = wx.Button(self, wx.ID_ANY, u"VMDサイジング実行", wx.DefaultPosition, wx.Size(200, 50), 0)
        self.exec_btn_ctrl.SetToolTip(u"VMDサイジング処理を実行します。")
        self.exec_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_exec)
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

    # 実行前チェック
    def on_check(self, event: wx.Event):
        # 出力先をファイルパネルのコンソールに変更
        sys.stdout = self.console_ctrl

        # フォーム無効化
        self.disable()
        # タブ固定
        self.fix_tab()
        # コンソールクリア
        self.console_ctrl.Clear()
        wx.GetApp().Yield()

        # 履歴保持
        self.save()

        # 一旦読み込み(そのままチェック)
        self.frame.load(target_idx=0)

        event.Skip()

    # サイジング実行
    def on_exec(self, event: wx.Event):
        # 出力先をファイルパネルのコンソールに変更
        sys.stdout = self.console_ctrl

        # フォーム無効化
        self.disable()
        # タブ固定
        self.fix_tab()
        # コンソールクリア
        self.console_ctrl.Clear()
        wx.GetApp().Yield()

        # 履歴保持
        self.save()

        # サイジング可否チェックの後に実行
        self.frame.load(is_exec=True, target_idx=0)

        event.Skip()

    def set_output_vmd_path(self, is_force=False):
        self.file_set.set_output_vmd_path(is_force)
        # カメラ出力パスも一緒に変更する
        self.frame.camera_panel_ctrl.header_panel.set_output_vmd_path()

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
