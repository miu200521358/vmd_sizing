# -*- coding: utf-8 -*-
#
import wx
import wx.lib.newevent

from form.panel.BasePanel import BasePanel
from form.parts.FloatSliderCtrl import FloatSliderCtrl
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MFormUtils, MFileUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class ArmPanel(BasePanel):
    
    def __init__(self, frame: wx.Frame, parent: wx.Notebook, tab_idx: int):
        super().__init__(frame, parent, tab_idx)

        avoidance_tooltip = "指定文字列が名前に含まれているボーン追従剛体と手首・指先との接触を回避します。\n「頭接触回避」は頭を中心とした球体剛体を自動で計算します。（セミコロン(;)で複数指定可能）"
        alignment_tooltip = "変換先モデルの手首位置が、作成元モデルの手首とほぼ同じ位置になるよう、手首位置を調整します。"

        # 同じグループなので、とりあえず宣言だけしておく
        self.arm_process_flg_avoidance = wx.CheckBox(self, wx.ID_ANY, u"", wx.DefaultPosition, wx.DefaultSize)
        self.arm_process_flg_avoidance.SetToolTip(avoidance_tooltip)
        self.arm_process_flg_avoidance.Bind(wx.EVT_CHECKBOX, self.set_output_vmd_path)
        self.arm_process_flg_alignment = wx.CheckBox(self, wx.ID_ANY, u"", wx.DefaultPosition, wx.DefaultSize)
        self.arm_process_flg_alignment.SetToolTip(alignment_tooltip)
        self.arm_process_flg_alignment.Bind(wx.EVT_CHECKBOX, self.set_output_vmd_path)

        self.description_txt = wx.StaticText(self, wx.ID_ANY, "腕を変換先モデルに合わせて調整する事ができます。\n「接触回避」と「位置合わせ」を合わせて実行できます。（接触回避→位置合わせの順に実行）" + \
                                             "\n腕の動きが、元々のモーションから変わる事があります。いずれもそれなりに時間がかかります。", wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.description_txt, 0, wx.ALL, 5)

        self.static_line01 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.sizer.Add(self.static_line01, 0, wx.EXPAND | wx.ALL, 5)

        # 剛体接触回避 ----------------
        self.avoidance_title_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 剛体接触回避タイトルラジオ
        self.avoidance_title_txt = wx.StaticText(self, wx.ID_ANY, u"接触回避", wx.DefaultPosition, wx.DefaultSize, 0)
        self.avoidance_title_txt.SetToolTip(avoidance_tooltip)
        self.avoidance_title_txt.Wrap(-1)
        self.avoidance_title_txt.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))
        self.avoidance_title_txt.Bind(wx.EVT_LEFT_DOWN, self.on_change_arm_process_avoidance)

        self.avoidance_title_sizer.Add(self.arm_process_flg_avoidance, 0, wx.ALL, 5)
        self.avoidance_title_sizer.Add(self.avoidance_title_txt, 0, wx.ALL, 5)
        self.sizer.Add(self.avoidance_title_sizer, 0, wx.ALL, 5)

        # 剛体接触回避説明文
        self.avoidance_description_txt = wx.StaticText(self, wx.ID_ANY, avoidance_tooltip, wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.avoidance_description_txt, 0, wx.ALL, 5)

        # 剛体名指定
        self.avoidance_target_txt_ctrl = wx.TextCtrl(self, wx.ID_ANY, "頭接触回避", wx.DefaultPosition, (-1, 50), wx.HSCROLL | wx.WANTS_CHARS)
        self.avoidance_target_txt_ctrl.Bind(wx.EVT_TEXT, self.on_change_arm_process_avoidance)
        self.sizer.Add(self.avoidance_target_txt_ctrl, 0, wx.EXPAND | wx.ALL, 5)

        self.static_line03 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.sizer.Add(self.static_line03, 0, wx.EXPAND | wx.ALL, 5)

        # 手首位置合わせ --------------------
        self.alignment_title_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 手首位置合わせタイトルラジオ
        self.alignment_title_txt = wx.StaticText(self, wx.ID_ANY, u"位置合わせ", wx.DefaultPosition, wx.DefaultSize, 0)
        self.alignment_title_txt.SetToolTip("両手を合わせたり、床に手をついたりするモーションを、変換先モデルの手首位置に合わせて調整します。\n" + \
                                            "それぞれの距離を調整することで、位置合わせの適用範囲を調整することができます。")
        self.alignment_title_txt.Wrap(-1)
        self.alignment_title_txt.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))
        self.alignment_title_txt.Bind(wx.EVT_LEFT_DOWN, self.on_change_arm_process_alignment)

        self.alignment_title_sizer.Add(self.arm_process_flg_alignment, 0, wx.ALL, 5)
        self.alignment_title_sizer.Add(self.alignment_title_txt, 0, wx.ALL, 5)
        self.sizer.Add(self.alignment_title_sizer, 0, wx.ALL, 5)

        # 手首位置合わせ説明文
        self.alignment_description_txt = wx.StaticText(self, wx.ID_ANY, alignment_tooltip, wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.alignment_description_txt, 0, wx.ALL, 5)

        # オプションサイザー
        self.alignment_option_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 指位置合わせ
        self.arm_alignment_finger_flg_ctrl = wx.CheckBox(self, wx.ID_ANY, u"指の位置で手首位置合わせを行う", wx.DefaultPosition, wx.DefaultSize, 0)
        self.arm_alignment_finger_flg_ctrl.SetToolTip(u"チェックを入れると、フィンガータットモーション等、指間の距離を基準に手首位置を調整できます。" \
                                                      + "複数人数モーションではOFFのままの方が綺麗になります。")
        self.arm_alignment_finger_flg_ctrl.Bind(wx.EVT_CHECKBOX, self.on_change_arm_process_alignment)
        self.alignment_option_sizer.Add(self.arm_alignment_finger_flg_ctrl, 0, wx.ALL, 5)

        # 床位置合わせ
        self.arm_alignment_floor_flg_ctrl = wx.CheckBox(self, wx.ID_ANY, u"床との位置合わせも一緒に行う", wx.DefaultPosition, wx.DefaultSize, 0)
        self.arm_alignment_floor_flg_ctrl.SetToolTip(u"チェックを入れると、手首が床に沈み込んだり浮いてたりする場合に、元モデルに合わせて手首の位置を調整できます。\nセンター位置も一緒に調整します。")
        self.arm_alignment_floor_flg_ctrl.Bind(wx.EVT_CHECKBOX, self.on_change_arm_process_alignment)
        self.alignment_option_sizer.Add(self.arm_alignment_floor_flg_ctrl, 0, wx.ALL, 5)

        self.sizer.Add(self.alignment_option_sizer, 0, wx.ALL, 5)

        # 手首位置スライダー
        self.alignment_distance_wrist_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.alignment_distance_wrist_txt = wx.StaticText(self, wx.ID_ANY, u"手首間の距離　  ", wx.DefaultPosition, wx.DefaultSize, 0)
        self.alignment_distance_wrist_txt.SetToolTip(u"どのくらい手首が近付いた場合に、手首位置合わせを実行するか指定してください。\n値が小さいほど、手首が近付いた時だけ手首位置合わせを行います。\n距離の単位は、元モデルの手のひらの大きさです。" \
                                                     + "\nサイジング実行時、手首間の距離がメッセージ欄に出てますので、参考にしてください。\nスライダーを最大に設定すると、常に手首位置合わせを行います。（両手剣等に便利です）")
        self.alignment_distance_wrist_txt.Wrap(-1)
        self.alignment_distance_wrist_sizer.Add(self.alignment_distance_wrist_txt, 0, wx.ALL, 5)

        self.alignment_distance_wrist_label = wx.StaticText(self, wx.ID_ANY, u"（1.7）", wx.DefaultPosition, wx.DefaultSize, 0)
        self.alignment_distance_wrist_label.SetToolTip(u"現在指定されている手首間の距離です。元モデルの両手首位置がこの範囲内である場合、手首間の位置合わせを行います。")
        self.alignment_distance_wrist_label.Wrap(-1)
        self.alignment_distance_wrist_sizer.Add(self.alignment_distance_wrist_label, 0, wx.ALL, 5)

        self.alignment_distance_wrist_slider = FloatSliderCtrl(self, wx.ID_ANY, 1.7, 0, 10, 0.1, self.alignment_distance_wrist_label, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL)
        self.alignment_distance_wrist_slider.Bind(wx.EVT_SCROLL_CHANGED, self.on_change_arm_process_alignment)
        self.alignment_distance_wrist_sizer.Add(self.alignment_distance_wrist_slider, 1, wx.ALL | wx.EXPAND, 5)

        self.sizer.Add(self.alignment_distance_wrist_sizer, 0, wx.ALL | wx.EXPAND, 5)

        # 指位置スライダー
        self.alignment_distance_finger_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.alignment_distance_finger_txt = wx.StaticText(self, wx.ID_ANY, u"指間の距離　　  ", wx.DefaultPosition, wx.DefaultSize, 0)
        self.alignment_distance_finger_txt.SetToolTip(u"どのくらい指が近付いた場合に、指位置合わせを実行するか指定してください。\n値が小さいほど、指が近付いた時だけ指位置合わせを行います。\n距離の単位は、元モデルの手のひらの大きさです。\n" \
                                                      + "\nサイジング実行時、指間の距離がメッセージ欄に出てますので、参考にしてください。\nスライダーを最大に設定すると、常に指位置合わせを行います。")
        self.alignment_distance_finger_txt.Wrap(-1)
        self.alignment_distance_finger_sizer.Add(self.alignment_distance_finger_txt, 0, wx.ALL, 5)

        self.alignment_distance_finger_label = wx.StaticText(self, wx.ID_ANY, u"（1.4）", wx.DefaultPosition, wx.DefaultSize, 0)
        self.alignment_distance_finger_label.SetToolTip(u"現在指定されている指間の距離です。元モデルの両指位置がこの範囲内である場合、指間の位置合わせを行います。")
        self.alignment_distance_finger_label.Wrap(-1)
        self.alignment_distance_finger_sizer.Add(self.alignment_distance_finger_label, 0, wx.ALL, 5)

        self.alignment_distance_finger_slider = FloatSliderCtrl(self, wx.ID_ANY, 1.4, 0, 10, 0.1, self.alignment_distance_finger_label, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL)
        self.alignment_distance_finger_slider.Bind(wx.EVT_SCROLL_CHANGED, self.on_change_arm_process_alignment)
        self.alignment_distance_finger_sizer.Add(self.alignment_distance_finger_slider, 1, wx.ALL | wx.EXPAND, 5)

        self.sizer.Add(self.alignment_distance_finger_sizer, 0, wx.ALL | wx.EXPAND, 5)

        # 手首と床との位置スライダー
        self.alignment_distance_floor_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.alignment_distance_floor_txt = wx.StaticText(self, wx.ID_ANY, u"手首と床との距離", wx.DefaultPosition, wx.DefaultSize, 0)
        self.alignment_distance_floor_txt.SetToolTip(u"どのくらい手首と床が近付いた場合に、手首と床との位置合わせを実行するか指定してください。\n値が小さいほど、手首と床が近付いた時だけ位置合わせを行います。\n距離の単位は、元モデルの手のひらの大きさです。" \
                                                     + "\nサイジング実行時、手首と床との間の距離がメッセージ欄に出てますので、参考にしてください。\nスライダーを最大に設定すると、常に手首と床との位置合わせを行います。")
        self.alignment_distance_floor_txt.Wrap(-1)
        self.alignment_distance_floor_sizer.Add(self.alignment_distance_floor_txt, 0, wx.ALL, 5)

        self.alignment_distance_floor_label = wx.StaticText(self, wx.ID_ANY, u"（1.2）", wx.DefaultPosition, wx.DefaultSize, 0)
        self.alignment_distance_floor_label.SetToolTip(u"現在指定されている手首と床との間の距離です。元モデルの両手首と床との距離がこの範囲内である場合、手首と床との位置合わせを行います。")
        self.alignment_distance_floor_label.Wrap(-1)
        self.alignment_distance_floor_sizer.Add(self.alignment_distance_floor_label, 0, wx.ALL, 5)

        self.alignment_distance_floor_slider = FloatSliderCtrl(self, wx.ID_ANY, 1.2, 0, 10, 0.1, self.alignment_distance_floor_label, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL)
        self.alignment_distance_floor_slider.Bind(wx.EVT_SCROLL_CHANGED, self.on_change_arm_process_alignment)
        self.alignment_distance_floor_sizer.Add(self.alignment_distance_floor_slider, 1, wx.ALL | wx.EXPAND, 5)

        self.sizer.Add(self.alignment_distance_floor_sizer, 0, wx.ALL | wx.EXPAND, 5)

        self.static_line04 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.sizer.Add(self.static_line04, 0, wx.EXPAND | wx.ALL, 5)

        # 腕チェックスキップ --------------------
        self.arm_check_skip_sizer = wx.BoxSizer(wx.VERTICAL)

        self.arm_check_skip_flg_ctrl = wx.CheckBox(self, wx.ID_ANY, u"腕～手首のサイジング可能チェックをスキップする", wx.DefaultPosition, wx.DefaultSize, 0)
        self.arm_check_skip_flg_ctrl.SetToolTip(u"サイジング可能チェック（腕IKがあると不可）をスキップして、必ず処理を行うようにします。")
        self.arm_check_skip_sizer.Add(self.arm_check_skip_flg_ctrl, 0, wx.ALL, 5)

        self.arm_check_skip_description = wx.StaticText(self, wx.ID_ANY, u"腕サイジング可能チェック（腕IKがあると不可）をスキップして、必ず腕関係処理を行うようにします。\n" \
                                                        + "※サイジング結果がおかしくなる可能性がありますが、サポート対象外です。", \
                                                        wx.DefaultPosition, wx.DefaultSize, 0)
        self.arm_check_skip_description.Wrap(-1)
        self.arm_check_skip_sizer.Add(self.arm_check_skip_description, 0, wx.ALL, 5)
        self.sizer.Add(self.arm_check_skip_sizer, 0, wx.ALL | wx.EXPAND, 5)

        self.fit()

    # VMD出力ファイルパス生成
    def set_output_vmd_path(self, is_force=False):
        # 念のため出力ファイルパス自動生成（空の場合設定）
        self.frame.file_panel_ctrl.file_set.set_output_vmd_path()

        # multiのも出力ファイルパス自動生成（空の場合設定）
        for file_set in self.frame.multi_panel_ctrl.file_set_list:
            file_set.set_output_vmd_path()
    
    # 処理対象：接触回避に切り替え
    def on_change_arm_process_avoidance(self, event: wx.Event):
        # ラジオボタンかチェックボックスイベントがTrueの場合、切り替え
        if ((isinstance(event.GetEventObject(), wx.RadioButton) or isinstance(event.GetEventObject(), wx.CheckBox)) and event.GetEventObject().GetValue()) \
                or (not isinstance(event.GetEventObject(), wx.RadioButton)):
            self.arm_process_flg_avoidance.SetValue(1)
            # パス再生成
            self.set_output_vmd_path()
        event.Skip()

    # 処理対象：手首位置合わせに切り替え
    def on_change_arm_process_alignment(self, event: wx.Event):
        # ラジオボタンかチェックボックスイベントがTrueの場合、切り替え
        if ((isinstance(event.GetEventObject(), wx.RadioButton) or isinstance(event.GetEventObject(), wx.CheckBox)) and event.GetEventObject().GetValue()) \
                or (not isinstance(event.GetEventObject(), wx.RadioButton)):
            self.arm_process_flg_alignment.SetValue(1)
            # パス再生成
            self.set_output_vmd_path()

        if self.arm_alignment_finger_flg_ctrl.GetValue() and len(self.frame.multi_panel_ctrl.file_set_list) > 0:
            self.frame.on_popup_finger_warning(event)

        event.Skip()

