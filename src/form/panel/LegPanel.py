# -*- coding: utf-8 -*-
#
import wx
import wx.lib.newevent
import numpy as np

from form.panel.BasePanel import BasePanel
from form.parts.FloatSliderCtrl import FloatSliderCtrl
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class LegPanel(BasePanel):
    
    def __init__(self, frame: wx.Frame, parent: wx.Notebook, tab_idx: int):
        super().__init__(frame, parent, tab_idx)

        move_correction_tooltip = "センター・足ＩＫなどの移動系ボーンの移動量を補正できます。\n足の重なりを広げたい、少し動きをダイナミックにしたいなどの時に使ってください"

        # 移動量補正 --------------------

        self.move_correction_title_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 移動量補正タイトル
        self.move_correction_title_txt = wx.StaticText(self, wx.ID_ANY, u"移動量補正", wx.DefaultPosition, wx.DefaultSize, 0)
        self.move_correction_title_txt.SetToolTip(move_correction_tooltip)
        self.move_correction_title_txt.Wrap(-1)
        self.move_correction_title_txt.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))
        self.move_correction_title_sizer.Add(self.move_correction_title_txt, 0, wx.ALL, 5)
        self.sizer.Add(self.move_correction_title_sizer, 0, wx.ALL, 5)

        # 移動量補正説明文
        self.move_correction_description_txt = wx.StaticText(self, wx.ID_ANY, move_correction_tooltip, wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.move_correction_description_txt, 0, wx.ALL, 5)

        # 移動量補正スライダー
        self.move_correction_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.move_correction_txt = wx.StaticText(self, wx.ID_ANY, u"移動量補正値", wx.DefaultPosition, wx.DefaultSize, 0)
        self.move_correction_txt.SetToolTip(u"身長比率にかける補正値です。デフォルトでは1人の場合は1、複数人の場合は頭身比率を設定しています。")
        self.move_correction_txt.Wrap(-1)
        self.move_correction_sizer.Add(self.move_correction_txt, 0, wx.ALL, 5)

        self.move_correction_label = wx.StaticText(self, wx.ID_ANY, u"（1）", wx.DefaultPosition, wx.DefaultSize, 0)
        self.move_correction_label.SetToolTip(u"現在指定されている移動量補正値です。")
        self.move_correction_label.Wrap(-1)
        self.move_correction_sizer.Add(self.move_correction_label, 0, wx.ALL, 5)

        self.move_correction_slider = FloatSliderCtrl(self, wx.ID_ANY, 1, 0.5, 1.5, 0.05, self.move_correction_label, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL)
        self.move_correction_slider.Bind(wx.EVT_SCROLL_CHANGED, self.on_check_move_correction)
        self.move_correction_sizer.Add(self.move_correction_slider, 1, wx.ALL | wx.EXPAND, 5)

        self.sizer.Add(self.move_correction_sizer, 0, wx.ALL | wx.EXPAND, 5)

        self.static_line04 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.sizer.Add(self.static_line04, 0, wx.EXPAND | wx.ALL, 5)

        self.fit()

    def initialize(self, event: wx.Event):

        if len(self.frame.multi_panel_ctrl.file_set_list) == 1:
            total_xz_ratio = 1
        else:
            original_heads_tall_ratios = []
            for file_set in [self.frame.file_panel_ctrl.file_set, *self.frame.multi_panel_ctrl.file_set_list]:
                _, _, original_heads_tall_ratio = file_set.calc_leg_ik_ratio()
                original_heads_tall_ratios.append(original_heads_tall_ratio)

            total_xz_ratio = max(0.5, min(1.5, np.mean(original_heads_tall_ratios)))

        # 複数件ある場合、補正値設定
        self.move_correction_slider.SetValue(total_xz_ratio)
        self.move_correction_label.SetLabel(f"（{total_xz_ratio}）")

        event.Skip()

    # VMD出力ファイルパス生成
    def set_output_vmd_path(self, event, is_force=False):
        # 念のため出力ファイルパス自動生成（空の場合設定）
        self.frame.file_panel_ctrl.file_set.set_output_vmd_path(event)

        # multiのも出力ファイルパス自動生成（空の場合設定）
        for file_set in self.frame.multi_panel_ctrl.file_set_list:
            file_set.set_output_vmd_path(event)
    
    def on_check_move_correction(self, event: wx.Event):
        # パス再生成
        self.set_output_vmd_path(event)

        event.Skip()
