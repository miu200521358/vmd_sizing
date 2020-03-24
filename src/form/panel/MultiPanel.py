# -*- coding: utf-8 -*-
#
import wx
import wx.lib.newevent

from form.panel.BasePanel import BasePanel
from form.parts.SizingFileSet import SizingFileSet
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MFormUtils, MFileUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class MultiPanel(BasePanel):
    
    def __init__(self, frame: wx.Frame, parent: wx.Notebook, tab_idx: int, file_hitories: dict):
        super().__init__(frame, parent, tab_idx)
        self.file_hitories = file_hitories

        self.header_panel = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.header_sizer = wx.BoxSizer(wx.VERTICAL)

        self.description_txt = wx.StaticText(self.header_panel, wx.ID_ANY, "複数人数モーションなどを比率を合わせてサイジングする事ができます。" \
                                             + "\n縮尺を強制的に変えてますので、足などが元モーションからズレる場合があります。"
                                             + "\n間違えてファイルセットを追加してしまった場合は、４つのファイル欄をすべて空にしてください。", wx.DefaultPosition, wx.DefaultSize, 0)
        self.header_sizer.Add(self.description_txt, 0, wx.ALL, 5)

        self.btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 変換前チェックボタン
        self.add_btn_ctrl = wx.Button(self.header_panel, wx.ID_ANY, u"ファイルセット追加", wx.DefaultPosition, wx.DefaultSize, 0)
        self.add_btn_ctrl.SetToolTip(u"サイジングに必要なファイルセットをパネルに追加します。")
        self.add_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_add_set)
        self.btn_sizer.Add(self.add_btn_ctrl, 0, wx.ALL, 5)

        self.header_sizer.Add(self.btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)
        self.header_panel.SetSizer(self.header_sizer)
        self.header_panel.Layout()
        self.sizer.Add(self.header_panel, 0, wx.EXPAND | wx.ALL, 5)

        # ファイルセット
        self.file_set_list = []
        # ファイルセット用基本Sizer
        self.set_base_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.scrolled_window = MultiFileSetScrolledWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, \
                                                          wx.FULL_REPAINT_ON_RESIZE | wx.VSCROLL | wx.ALWAYS_SHOW_SB)
        # self.scrolled_window.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        # self.scrolled_window.SetBackgroundColour("BLUE")
        self.scrolled_window.SetScrollRate(5, 5)
        self.scrolled_window.set_file_set_list(self.file_set_list)

        self.scrolled_window.SetSizer(self.set_base_sizer)
        self.scrolled_window.Layout()
        self.sizer.Add(self.scrolled_window, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 5)
        self.fit()

    def on_add_set(self, event: wx.Event):
        self.file_set_list.append(SizingFileSet(self.frame, self.scrolled_window, self.file_hitories, len(self.file_set_list) + 2))
        self.set_base_sizer.Add(self.file_set_list[-1].set_sizer, 0, wx.ALL, 5)
        self.set_base_sizer.Layout()
        
        # スクロールバーの表示のためにサイズ調整
        self.sizer.Layout()
        # self.sizer.FitInside(self.scrolled_window)

        event.Skip()

    # フォーム無効化
    def disable(self):
        self.file_set.disable()

    # フォーム無効化
    def enable(self):
        self.file_set.enable()


class MultiFileSetScrolledWindow(wx.ScrolledWindow):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
    
    def set_file_set_list(self, file_set_list):
        self.file_set_list = file_set_list

    def set_output_vmd_path(self, is_force=False):
        for file_set in self.file_set_list:
            file_set.set_output_vmd_path(is_force)

        