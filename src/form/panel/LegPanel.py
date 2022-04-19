# -*- coding: utf-8 -*-
#
import wx
import wx.lib.newevent
import numpy as np

from form.panel.BasePanel import BasePanel
from form.parts.FloatSliderCtrl import FloatSliderCtrl
from form.parts.SizingFileSet import SizingFileSet
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class LegPanel(BasePanel):
    
    def __init__(self, frame: wx.Frame, parent: wx.Notebook, tab_idx: int):
        super().__init__(frame, parent, tab_idx)

        # 全体移動量補正 --------------------

        move_correction_tooltip = "センター・足ＩＫなどの移動系ボーンの全体の移動量を補正できます。\n複数人モーションのフォーメーションを全体的に広げたい、少し動きをダイナミックにしたいなどの時に使ってください"
        self.move_correction_title_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 全体移動量補正タイトル
        self.move_correction_title_txt = wx.StaticText(self, wx.ID_ANY, u"全体移動量補正", wx.DefaultPosition, wx.DefaultSize, 0)
        self.move_correction_title_txt.SetToolTip(move_correction_tooltip)
        self.move_correction_title_txt.Wrap(-1)
        self.move_correction_title_txt.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))
        self.move_correction_title_sizer.Add(self.move_correction_title_txt, 0, wx.ALL, 5)
        self.sizer.Add(self.move_correction_title_sizer, 0, wx.ALL, 5)

        # 全体移動量補正説明文
        self.move_correction_description_txt = wx.StaticText(self, wx.ID_ANY, move_correction_tooltip, wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.move_correction_description_txt, 0, wx.ALL, 5)

        # 全体移動量補正スライダー
        self.move_correction_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.move_correction_txt = wx.StaticText(self, wx.ID_ANY, u"全体移動量補正値", wx.DefaultPosition, wx.DefaultSize, 0)
        self.move_correction_txt.SetToolTip(u"身長比率にかける補正値です。デフォルトでは1人の場合は1、複数人の場合は頭身比率を設定しています。")
        self.move_correction_txt.Wrap(-1)
        self.move_correction_sizer.Add(self.move_correction_txt, 0, wx.ALL, 5)

        self.move_correction_label = wx.StaticText(self, wx.ID_ANY, u"（1）", wx.DefaultPosition, wx.DefaultSize, 0)
        self.move_correction_label.SetToolTip(u"現在指定されている全体移動量補正値です。")
        self.move_correction_label.Wrap(-1)
        self.move_correction_sizer.Add(self.move_correction_label, 0, wx.ALL, 5)

        self.move_correction_slider = FloatSliderCtrl(self, wx.ID_ANY, 1, 0.5, 1.5, 0.05, self.move_correction_label, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL)
        self.move_correction_slider.Bind(wx.EVT_SCROLL_CHANGED, self.on_check_move_correction)
        self.move_correction_sizer.Add(self.move_correction_slider, 1, wx.ALL | wx.EXPAND, 5)

        self.sizer.Add(self.move_correction_sizer, 0, wx.ALL | wx.EXPAND, 5)

        self.static_line01 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.sizer.Add(self.static_line01, 0, wx.EXPAND | wx.ALL, 5)

        # オフセット値
        self.leg_offset_set_dict = {}
        # オフセット用ダイアログ
        self.leg_offset_dialog = LegOffsetDialog(self.frame)

        # 足ＩＫオフセット --------------------

        # Bulk用足ＩＫオフセットデータ
        self.bulk_leg_offset_set_dict = {}

        leg_offset_tooltip = "足ＩＫの移動量オフセットを設定できます。\n足を閉じた時に重なってしまったり、全体の移動量は変えずに個別の足ＩＫの移動量だけ調整したい\nといった時に使ってください"

        # 足ＩＫオフセット ----------------
        self.leg_offset_title_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 足ＩＫオフセットタイトル
        self.leg_offset_title_txt = wx.StaticText(self, wx.ID_ANY, u"足ＩＫオフセット", wx.DefaultPosition, wx.DefaultSize, 0)
        self.leg_offset_title_txt.SetToolTip(leg_offset_tooltip)
        self.leg_offset_title_txt.Wrap(-1)
        self.leg_offset_title_txt.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))
        self.leg_offset_title_sizer.Add(self.leg_offset_title_txt, 0, wx.ALL, 5)
        self.sizer.Add(self.leg_offset_title_sizer, 0, wx.ALL, 5)

        # 足ＩＫオフセット説明文
        self.leg_offset_description_txt = wx.StaticText(self, wx.ID_ANY, leg_offset_tooltip, wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.leg_offset_description_txt, 0, wx.ALL, 5)

        self.leg_offset_target_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # オフセット値指定
        self.leg_offset_target_txt_ctrl = wx.TextCtrl(self, wx.ID_ANY, "", wx.DefaultPosition, (450, 80), wx.HSCROLL | wx.VSCROLL | wx.TE_MULTILINE | wx.TE_READONLY)
        self.leg_offset_target_txt_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        self.leg_offset_target_sizer.Add(self.leg_offset_target_txt_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        self.leg_offset_target_btn_ctrl = wx.Button(self, wx.ID_ANY, u"オフセット指定", wx.DefaultPosition, wx.DefaultSize, 0)
        self.leg_offset_target_btn_ctrl.SetToolTip(u"変換先モデルの足ＩＫオフセット値を指定できます")
        self.leg_offset_target_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_click_leg_offset_target)
        self.leg_offset_target_sizer.Add(self.leg_offset_target_btn_ctrl, 0, wx.ALIGN_BOTTOM | wx.ALL, 5)

        self.sizer.Add(self.leg_offset_target_sizer, 0, wx.ALL, 0)

        self.static_line03 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.sizer.Add(self.static_line03, 0, wx.EXPAND | wx.ALL, 5)

        self.fit()
        
    def get_leg_offsets(self):
        if len(self.bulk_leg_offset_set_dict.keys()) > 0:
            # Bulk用データがある場合、優先返還
            return self.bulk_leg_offset_set_dict

        target = {}
        
        # 選択されたオフセット値を入力欄に設定(ハッシュが同じ場合のみ)
        if 1 in self.leg_offset_set_dict and self.leg_offset_set_dict[1].leg_offset_slider:
            if self.leg_offset_set_dict[1].equal_hashdigest(self.frame.file_panel_ctrl.file_set):
                target[0] = self.leg_offset_set_dict[1].leg_offset_slider.GetValue()
            else:
                logger.warning("【No.%s】足ＩＫオフセット設定後、ファイルセットが変更されたため、足ＩＫオフセットをクリアします", 1, decoration=MLogger.DECORATION_BOX)

        for set_no in list(self.leg_offset_set_dict.keys())[1:]:
            if set_no in self.leg_offset_set_dict and self.leg_offset_set_dict[set_no].leg_offset_slider:
                if len(self.frame.multi_panel_ctrl.file_set_list) >= set_no - 1 and self.leg_offset_set_dict[set_no].equal_hashdigest(self.frame.multi_panel_ctrl.file_set_list[set_no - 2]):
                    target[set_no - 1] = self.leg_offset_set_dict[set_no].leg_offset_slider.GetValue()
                else:
                    logger.warning("【No.%s】足ＩＫオフセット設定後、ファイルセットが変更されたため、足ＩＫオフセットをクリアします", set_no, decoration=MLogger.DECORATION_BOX)

        return target
    
    def on_click_leg_offset_target(self, event: wx.Event):
        if self.leg_offset_dialog.ShowModal() == wx.ID_CANCEL:
            return     # the user changed their mind

        self.show_leg_offset()

        self.leg_offset_dialog.Hide()
    
    def show_leg_offset(self):
        # 一旦クリア
        self.leg_offset_target_txt_ctrl.SetValue("")

        # 選択されたオフセット値を入力欄に設定
        texts = []
        for set_no, set_data in self.leg_offset_set_dict.items():
            # 選択肢ごとの表示文言
            texts.append("【No.{0}】　{1}".format(set_no, set_data.leg_offset_slider.GetValue()))

        self.leg_offset_target_txt_ctrl.WriteText(" / ".join(texts))

    def initialize(self, event: wx.Event):

        if 1 in self.leg_offset_set_dict:
            # ファイルタブ用足ＩＫオフセットのファイルセットがある場合
            if self.frame.file_panel_ctrl.file_set.is_loaded():
                # 既にある場合、ハッシュチェック
                if self.leg_offset_set_dict[1].equal_hashdigest(self.frame.file_panel_ctrl.file_set):
                    # 同じである場合、スルー
                    pass
                else:
                    # 違う場合、ファイルセット読み直し
                    self.add_set(1, self.frame.file_panel_ctrl.file_set, replace=True)
            else:
                # ファイルタブが読み込み失敗している場合、読み直し（クリア）
                self.add_set(1, self.frame.file_panel_ctrl.file_set, replace=True)
        else:
            # 空から作る場合、ファイルタブのファイルセット参照
            self.add_set(1, self.frame.file_panel_ctrl.file_set, replace=False)
        
        # multiはあるだけ調べる
        for multi_file_set_idx, multi_file_set in enumerate(self.frame.multi_panel_ctrl.file_set_list):
            set_no = multi_file_set_idx + 2
            if set_no in self.leg_offset_set_dict:
                # 複数タブ用足ＩＫオフセットのファイルセットがある場合
                if multi_file_set.is_loaded():
                    # 既にある場合、ハッシュチェック
                    if self.leg_offset_set_dict[set_no].equal_hashdigest(multi_file_set):
                        # 同じである場合、スルー
                        pass
                    else:
                        # 違う場合、ファイルセット読み直し
                        self.add_set(set_no, multi_file_set, replace=True)
                else:
                    # 複数タブが読み込み失敗している場合、読み直し（クリア）
                    self.add_set(set_no, multi_file_set, replace=True)
            else:
                # 空から作る場合、複数タブのファイルセット参照
                self.add_set(set_no, multi_file_set, replace=False)

        self.show_leg_offset()

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

    def add_set(self, set_idx: int, file_set: SizingFileSet, replace: bool):
        new_leg_offset_set = LegOffsetSet(self.frame, self, self.leg_offset_dialog.scrolled_window, set_idx, file_set)
        if replace:
            # 置き換え
            self.leg_offset_dialog.set_list_sizer.Hide(self.leg_offset_set_dict[set_idx].set_sizer, recursive=True)
            self.leg_offset_dialog.set_list_sizer.Replace(self.leg_offset_set_dict[set_idx].set_sizer, new_leg_offset_set.set_sizer, recursive=True)

            # 置き換えの場合、オフセット値クリア
            self.leg_offset_target_txt_ctrl.SetValue("")
        else:
            # 新規追加
            self.leg_offset_dialog.set_list_sizer.Add(new_leg_offset_set.set_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.leg_offset_set_dict[set_idx] = new_leg_offset_set

        # スクロールバーの表示のためにサイズ調整
        self.leg_offset_dialog.set_list_sizer.Layout()
        self.leg_offset_dialog.set_list_sizer.FitInside(self.leg_offset_dialog.scrolled_window)


class LegOffsetSet():

    def __init__(self, frame: wx.Frame, panel: wx.Panel, window: wx.Window, set_idx: int, file_set: SizingFileSet):
        self.frame = frame
        self.panel = panel
        self.window = window
        self.set_idx = set_idx
        self.file_set = file_set
        self.rep_model_digest = 0 if not file_set.rep_model_file_ctrl.data else file_set.rep_model_file_ctrl.data.digest

        self.set_sizer = wx.StaticBoxSizer(wx.StaticBox(self.window, wx.ID_ANY, "【No.{0}】 {1}".format(set_idx, file_set.rep_model_file_ctrl.data.name[:20])), orient=wx.VERTICAL)
        
        # 足ＩＫオフセット値
        self.leg_offset_label = wx.StaticText(self.window, wx.ID_ANY, "（0）", wx.DefaultPosition, wx.DefaultSize, 0)
        self.leg_offset_label.SetToolTip(u"現在指定されている足ＩＫオフセット値です。実際にこの値が（向きを加味して）足ＩＫに加算されます。")
        self.leg_offset_label.Wrap(-1)
        self.set_sizer.Add(self.leg_offset_label, 0, wx.ALL, 5)

        self.leg_offset_slider = FloatSliderCtrl(self.window, wx.ID_ANY, 0, -2, 2, 0.05, self.leg_offset_label, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL)
        self.set_sizer.Add(self.leg_offset_slider, 1, wx.ALL | wx.EXPAND, 5)

    # 現在のファイルセットのハッシュと同じであるかチェック
    def equal_hashdigest(self, now_file_set: SizingFileSet):
        return self.rep_model_digest == now_file_set.rep_model_file_ctrl.data.digest


class LegOffsetDialog(wx.Dialog):

    def __init__(self, parent):
        super().__init__(parent, id=wx.ID_ANY, title="足ＩＫオフセット指定", pos=(-1, -1), size=(800, 500), style=wx.DEFAULT_DIALOG_STYLE, name="LegOffsetDialog")

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # 説明文
        self.description_txt = wx.StaticText(self, wx.ID_ANY, u"足ＩＫの移動量オフセットを設定できます。実際にこの値が（向きを加味して）足ＩＫに加算されます。\n" \
                                             + u"複数人モーションの場合、あまり大きなオフセットを指定するとフォーメーションが崩れる場合があります。\n" , wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.description_txt, 0, wx.ALL, 5)

        # ボタン
        self.btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.ok_btn = wx.Button(self, wx.ID_OK, "OK")
        self.btn_sizer.Add(self.ok_btn, 0, wx.ALL, 5)

        self.calcel_btn = wx.Button(self, wx.ID_CANCEL, "キャンセル")
        self.btn_sizer.Add(self.calcel_btn, 0, wx.ALL, 5)
        self.sizer.Add(self.btn_sizer, 0, wx.ALL, 5)

        self.static_line01 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.sizer.Add(self.static_line01, 0, wx.EXPAND | wx.ALL, 5)

        self.scrolled_window = wx.ScrolledWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, \
                                                 wx.FULL_REPAINT_ON_RESIZE | wx.VSCROLL | wx.ALWAYS_SHOW_SB)
        self.scrolled_window.SetScrollRate(5, 5)

        # 足ＩＫオフセットセット用基本Sizer
        self.set_list_sizer = wx.BoxSizer(wx.VERTICAL)

        # スクロールバーの表示のためにサイズ調整
        self.scrolled_window.SetSizer(self.set_list_sizer)
        self.scrolled_window.Layout()
        self.sizer.Add(self.scrolled_window, 1, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(self.sizer)
        self.sizer.Layout()
        
        # 画面中央に表示
        self.CentreOnScreen()
        
        # 最初は隠しておく
        self.Hide()
