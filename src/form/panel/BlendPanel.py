# -*- coding: utf-8 -*-
#
import wx
import wx.lib.newevent
import sys

from form.panel.BasePanel import BasePanel
from form.parts.BaseFilePickerCtrl import BaseFilePickerCtrl
from form.parts.ConsoleCtrl import ConsoleCtrl
from form.worker.BlendWorkerThread import BlendWorkerThread
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MFormUtils, MFileUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)

# イベント定義
(BlendThreadEvent, EVT_CSV_THREAD) = wx.lib.newevent.NewEvent()


class BlendPanel(BasePanel):
    
    def __init__(self, frame: wx.Frame, parent: wx.Notebook, tab_idx: int):
        super().__init__(frame, parent, tab_idx)
        self.blend_worker = None

        self.description_txt = wx.StaticText(self, wx.ID_ANY, "指定されたPMXファイルのモーフをランダムに変化させた結果を、VMDファイルとして出力します。\n" \
                                             + "モーフの組み合わせが多くなると破綻する確率が高くなりますので、その状態での一般公開は避けてください。",
                                             wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.description_txt, 0, wx.ALL, 5)

        self.static_line = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.sizer.Add(self.static_line, 0, wx.EXPAND | wx.ALL, 5)

        # PMXファイルコントロール
        self.pmx_file_ctrl = BaseFilePickerCtrl(frame, self, u"PMXファイル", u"PMXファイルを開く", ("pmx"), wx.FLP_DEFAULT_STYLE, \
                                                u"モーフをブレンドさせたいPMXのパスを指定してください。\nD&Dでの指定、開くボタンからの指定ができます。\nパスを指定すると下部欄にモーフリストが表示されます。", \
                                                is_aster=False, is_save=False, set_no=0)
        self.pmx_file_ctrl.file_ctrl.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_change_file)
        self.sizer.Add(self.pmx_file_ctrl.sizer, 0, wx.EXPAND, 0)

        # モーフ選択欄 ---------
        self.morph_sizer = wx.BoxSizer(wx.HORIZONTAL)

        MORPH_TOOLTIP = "ブレンド対象となるモーフを選択して下さい。"

        self.morph_eye_txt = wx.StaticText(self, wx.ID_ANY, "目")
        self.morph_eye_txt.SetToolTip(MORPH_TOOLTIP)
        self.morph_sizer.Add(self.morph_eye_txt, 0, wx.EXPAND | wx.ALL, 5)

        self.morph_eye_list = wx.ListBox(self, id=wx.ID_ANY, pos=wx.DefaultPosition, size=(110, 100), choices=[], style=wx.LB_MULTIPLE | wx.LB_ALWAYS_SB)
        self.morph_eye_list.SetToolTip(MORPH_TOOLTIP)
        self.morph_sizer.Add(self.morph_eye_list, 0, wx.ALL, 5)

        self.morph_eyebrow_txt = wx.StaticText(self, wx.ID_ANY, "眉")
        self.morph_eyebrow_txt.SetToolTip(MORPH_TOOLTIP)
        self.morph_sizer.Add(self.morph_eyebrow_txt, 0, wx.EXPAND | wx.ALL, 5)

        self.morph_eyebrow_list = wx.ListBox(self, id=wx.ID_ANY, pos=wx.DefaultPosition, size=(110, 100), choices=[], style=wx.LB_MULTIPLE | wx.LB_ALWAYS_SB)
        self.morph_eyebrow_list.SetToolTip(MORPH_TOOLTIP)
        self.morph_sizer.Add(self.morph_eyebrow_list, 0, wx.ALL, 5)

        self.morph_lip_txt = wx.StaticText(self, wx.ID_ANY, "口")
        self.morph_lip_txt.SetToolTip(MORPH_TOOLTIP)
        self.morph_sizer.Add(self.morph_lip_txt, 0, wx.EXPAND | wx.ALL, 5)

        self.morph_lip_list = wx.ListBox(self, id=wx.ID_ANY, pos=wx.DefaultPosition, size=(110, 100), choices=[], style=wx.LB_MULTIPLE | wx.LB_ALWAYS_SB)
        self.morph_lip_list.SetToolTip(MORPH_TOOLTIP)
        self.morph_sizer.Add(self.morph_lip_list, 0, wx.ALL, 5)

        self.morph_other_txt = wx.StaticText(self, wx.ID_ANY, "他")
        self.morph_other_txt.SetToolTip(MORPH_TOOLTIP)
        self.morph_sizer.Add(self.morph_other_txt, 0, wx.EXPAND | wx.ALL, 5)

        self.morph_other_list = wx.ListBox(self, id=wx.ID_ANY, pos=wx.DefaultPosition, size=(110, 100), choices=[], style=wx.LB_MULTIPLE | wx.LB_ALWAYS_SB)
        self.morph_other_list.SetToolTip(MORPH_TOOLTIP)
        self.morph_sizer.Add(self.morph_other_list, 0, wx.ALL, 5)

        self.sizer.Add(self.morph_sizer, 0, wx.EXPAND | wx.ALL, 0)

        # モーフ増減値 ---------

        self.value_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # モーフ最小値
        self.morph_value_min_txt = wx.StaticText(self, wx.ID_ANY, u"最小値", wx.DefaultPosition, wx.DefaultSize, 0)
        self.morph_value_min_txt.SetToolTip(u"モーフ増減の最小値です。-10から10の間で設定できます。（小数点可）")
        self.value_sizer.Add(self.morph_value_min_txt, 0, wx.EXPAND | wx.ALL, 5)

        self.morph_spin_min = wx.SpinCtrlDouble(self, id=wx.ID_ANY, size=wx.Size(80, -1), min=-10, max=10, initial=0.0, inc=0.1)
        self.morph_spin_min.SetToolTip(u"モーフ増減の最小値です。-10から10の間で設定できます。（小数点可）")
        self.morph_spin_min.Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.1))
        self.value_sizer.Add(self.morph_spin_min, 0, wx.ALL, 5)

        # モーフ最大値
        self.morph_value_max_txt = wx.StaticText(self, wx.ID_ANY, u"最大値", wx.DefaultPosition, wx.DefaultSize, 0)
        self.morph_value_max_txt.SetToolTip(u"モーフ増減の最大値です。-10から10の間で設定できます。（小数点可）")
        self.value_sizer.Add(self.morph_value_max_txt, 0, wx.EXPAND | wx.ALL, 5)

        self.morph_spin_max = wx.SpinCtrlDouble(self, id=wx.ID_ANY, size=wx.Size(80, -1), min=-10, max=10, initial=1.0, inc=0.1)
        self.morph_spin_max.SetToolTip(u"モーフ増減の最大値です。-10から10の間で設定できます。（小数点可）")
        self.morph_spin_max.Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.1))
        self.value_sizer.Add(self.morph_spin_max, 0, wx.ALL, 5)

        # モーフ増加値
        self.morph_value_inc_txt = wx.StaticText(self, wx.ID_ANY, u"増加値", wx.DefaultPosition, wx.DefaultSize, 0)
        self.morph_value_inc_txt.SetToolTip(u"モーフ増減の増加量です。この増加量分ごとにモーフ組み合わせを生成していきます。0から1の間で設定できます。（小数点可）")
        self.morph_value_inc_txt.Wrap(-1)
        self.value_sizer.Add(self.morph_value_inc_txt, 0, wx.EXPAND | wx.ALL, 5)

        self.morph_spin_inc = wx.SpinCtrlDouble(self, id=wx.ID_ANY, size=wx.Size(80, -1), min=0.01, max=1, initial=0.1, inc=0.05)
        self.morph_spin_inc.SetToolTip(u"モーフ増減の増加量です。この増加量分ごとにモーフ組み合わせを生成していきます。0から1の間で設定できます。（小数点可）")
        self.morph_spin_inc.Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.05))
        self.value_sizer.Add(self.morph_spin_inc, 0, wx.ALL, 5)

        self.sizer.Add(self.value_sizer, 0, wx.EXPAND | wx.ALL, 0)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # モーフブレンド実行ボタン
        self.blend_btn_ctrl = wx.Button(self, wx.ID_ANY, u"モーフブレンド実行", wx.DefaultPosition, wx.Size(200, 50), 0)
        self.blend_btn_ctrl.SetToolTip(u"モーフをブレンドしたVMDを生成します。")
        self.blend_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_convert_blend)
        btn_sizer.Add(self.blend_btn_ctrl, 0, wx.ALL, 5)

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
        self.frame.Bind(EVT_CSV_THREAD, self.on_convert_blend_result)

    def on_change_file(self, event: wx.Event):
        # フォーム無効化
        self.disable()
        # 出力先をCSVパネルのコンソールに変更
        sys.stdout = self.console_ctrl

        # ファイルコントロール自身のパス確定処理
        self.pmx_file_ctrl.on_change_file(event)

        # ファイル読み込み処理
        if self.pmx_file_ctrl.is_valid() and self.pmx_file_ctrl.load():
            # モーフ展開処理
            morph_names = {"目": [], "眉": [], "口": [], "他": []}

            for mk, mv in self.pmx_file_ctrl.data.morphs.items():
                if mv.display:
                    morph_names[mv.get_panel_name()].append(mk)

            self.morph_eye_list.SetItems(morph_names["目"])
            self.morph_eyebrow_list.SetItems(morph_names["眉"])
            self.morph_lip_list.SetItems(morph_names["口"])
            self.morph_other_list.SetItems(morph_names["他"])

        # フォーム有効化
        self.enable()

        event.Skip()

    # フォーム無効化
    def disable(self):
        self.pmx_file_ctrl.disable()
        self.morph_eye_list.Disable()
        self.morph_eyebrow_list.Disable()
        self.morph_lip_list.Disable()
        self.morph_other_list.Disable()
        self.morph_spin_min.Disable()
        self.morph_spin_max.Disable()
        self.morph_spin_inc.Disable()
        self.blend_btn_ctrl.Disable()

    # フォーム無効化
    def enable(self):
        self.pmx_file_ctrl.enable()
        self.morph_eye_list.Enable()
        self.morph_eyebrow_list.Enable()
        self.morph_lip_list.Enable()
        self.morph_other_list.Enable()
        self.morph_spin_min.Enable()
        self.morph_spin_max.Enable()
        self.morph_spin_inc.Enable()
        self.blend_btn_ctrl.Enable()

    # モーフブレンド
    def on_convert_blend(self, event: wx.Event):
        # フォーム無効化
        self.disable()
        # タブ固定
        self.fix_tab()
        # コンソールクリア
        self.console_ctrl.Clear()
        # 出力先をブレンドパネルのコンソールに変更
        sys.stdout = self.console_ctrl

        wx.GetApp().Yield()

        self.elapsed_time = 0
        result = True
        result = self.pmx_file_ctrl.is_valid() and result
        result = self.is_valid() and result

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

        # モーフブレンド開始
        if self.blend_worker:
            logger.error("まだ処理が実行中です。終了してから再度実行してください。", decoration=MLogger.DECORATION_BOX)
        else:
            # 別スレッドで実行
            self.blend_worker = BlendWorkerThread(self.frame, BlendThreadEvent)
            self.blend_worker.start()
            self.blend_worker.stop_event.set()

        return result

        event.Skip()

    # モーフブレンド完了処理
    def on_convert_blend_result(self, event: wx.Event):
        self.elapsed_time = event.elapsed_time

        # 終了音
        self.frame.sound_finish()

        # タブ移動可
        self.release_tab()
        # フォーム有効化
        self.enable()
        # ワーカー終了
        self.blend_worker = None
        # プログレス非表示
        self.gauge_ctrl.SetValue(0)

        if not event.result:
            logger.error("モーフブレンド処理に失敗しました。", decoration=MLogger.DECORATION_BOX)
            
            event.Skip()
            return False

        logger.info("モーフブレンドが完了しました", decoration=MLogger.DECORATION_BOX, title="OK")

        # 出力先をデフォルトに戻す
        sys.stdout = self.frame.file_panel_ctrl.console_ctrl

    def is_valid(self):
        if len(self.morph_eye_list.GetSelections()) + len(self.morph_eyebrow_list.GetSelections()) \
           + len(self.morph_lip_list.GetSelections()) + len(self.morph_other_list.GetSelections()) == 0:
            logger.warning("ブレント対象となるモーフが選択されていません", decoration=MLogger.DECORATION_BOX)
        
            return False
        
        return True


