# -*- coding: utf-8 -*-
#

import wx
import sys

from form.panel.FilePanel import FilePanel
from form.panel.MorphPanel import MorphPanel
from utils import MFileUtils


class MainFrame(wx.Frame):

    def __init__(self, parent, mydir_path, version_name, logging_level, is_out_log):
        self.version_name = version_name
        self.logging_level = logging_level
        self.is_out_log = is_out_log
        self.mydir_path = mydir_path

        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"VMDサイジング ローカル版 {0}".format(self.version_name), \
                          pos=wx.DefaultPosition, size=wx.Size(600, 650), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        # ファイル履歴読み込み
        self.file_hitories = MFileUtils.read_history(self.mydir_path)

        # ---------------------------------------------

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        bSizer1 = wx.BoxSizer(wx.VERTICAL)

        self.note_ctrl = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
        # self.note_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        self.note_ctrl.SetBackgroundColour("BLUE")

        # ---------------------------------------------

        # ファイルタブ
        self.file_panel_ctrl = FilePanel(self, self.note_ctrl, 0, self.file_hitories)
        self.note_ctrl.AddPage(self.file_panel_ctrl, u"ファイル", True)

        # モーフタブ
        self.morph_panel_ctrl = MorphPanel(self, self.note_ctrl, 0)
        self.note_ctrl.AddPage(self.morph_panel_ctrl, u"モーフ", False)

        # ---------------------------------------------

        # タブ押下時の処理
        self.note_ctrl.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_tab_change)

        # 待機中の処理
        self.Bind(wx.EVT_IDLE, self.on_idle)

        # ---------------------------------------------

        bSizer1.Add(self.note_ctrl, 1, wx.EXPAND, 5)

        # デフォルトの出力先はファイルタブのコンソール
        sys.stdout = self.file_panel_ctrl.console_ctrl

        self.SetSizer(bSizer1)
        self.Layout()

        self.Centre(wx.BOTH)
    
    def on_idle(self, event):
        if self.file_panel_ctrl.worker or self.file_panel_ctrl.load_worker:
            self.file_panel_ctrl.gauge_ctrl.Pulse()

    def on_tab_change(self, event):
        if self.file_panel_ctrl.is_fix_tab:
            self.note_ctrl.ChangeSelection(self.file_panel_ctrl.tab_idx)
            event.Skip()
            return

        elif self.morph_panel_ctrl.is_fix_tab:
            self.note_ctrl.ChangeSelection(self.morph_panel_ctrl.tab_idx)
            event.Skip()
            return

