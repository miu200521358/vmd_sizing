# -*- coding: utf-8 -*-
#
import wx
import wx.lib.newevent

from form.panel.BasePanel import BasePanel
from form.parts.FloatSliderCtrl import FloatSliderCtrl
from form.parts.SizingFileSet import SizingFileSet
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MFormUtils, MFileUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class ArmPanel(BasePanel):
    
    def __init__(self, frame: wx.Frame, parent: wx.Notebook, tab_idx: int):
        super().__init__(frame, parent, tab_idx)

        # 剛体リスト
        self.avoidance_set_dict = {}
        # 剛体用ダイアログ
        self.avoidance_dialog = AvoidanceDialog(self.frame)

        avoidance_tooltip = "指定文字列名のボーン追従剛体と手首・指先との接触を回避します。\n選択ボタンから、変換先モデルの回避させたいボーン追従剛体を選択してください。\n" \
                            + "「頭接触回避」は頭を中心とした球体剛体を自動で計算します。"
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
        self.avoidance_title_txt.Bind(wx.EVT_LEFT_DOWN, self.on_check_arm_process_avoidance)

        self.avoidance_title_sizer.Add(self.arm_process_flg_avoidance, 0, wx.ALL, 5)
        self.avoidance_title_sizer.Add(self.avoidance_title_txt, 0, wx.ALL, 5)
        self.sizer.Add(self.avoidance_title_sizer, 0, wx.ALL, 5)

        # 剛体接触回避説明文
        self.avoidance_description_txt = wx.StaticText(self, wx.ID_ANY, avoidance_tooltip, wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.avoidance_description_txt, 0, wx.ALL, 5)

        self.avoidance_target_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 剛体名指定
        self.avoidance_target_txt_ctrl = wx.TextCtrl(self, wx.ID_ANY, "", wx.DefaultPosition, (450, 80), wx.HSCROLL | wx.VSCROLL | wx.TE_MULTILINE | wx.TE_READONLY)
        self.avoidance_target_txt_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        self.avoidance_target_txt_ctrl.Bind(wx.EVT_TEXT, self.on_check_arm_process_avoidance)
        self.avoidance_target_sizer.Add(self.avoidance_target_txt_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        self.avoidance_target_btn_ctrl = wx.Button(self, wx.ID_ANY, u"選択", wx.DefaultPosition, wx.DefaultSize, 0)
        self.avoidance_target_btn_ctrl.SetToolTip(u"変換先モデルにあるボーン追従剛体を選択できます")
        self.avoidance_target_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_click_avoidance_target)
        self.avoidance_target_sizer.Add(self.avoidance_target_btn_ctrl, 0, wx.ALIGN_BOTTOM | wx.ALL, 5)

        self.sizer.Add(self.avoidance_target_sizer, 0, wx.ALL, 0)

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
        self.alignment_title_txt.Bind(wx.EVT_LEFT_DOWN, self.on_check_arm_process_alignment)

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
        self.arm_alignment_finger_flg_ctrl.Bind(wx.EVT_CHECKBOX, self.on_check_arm_process_alignment)
        self.alignment_option_sizer.Add(self.arm_alignment_finger_flg_ctrl, 0, wx.ALL, 5)

        # 床位置合わせ
        self.arm_alignment_floor_flg_ctrl = wx.CheckBox(self, wx.ID_ANY, u"床との位置合わせも一緒に行う", wx.DefaultPosition, wx.DefaultSize, 0)
        self.arm_alignment_floor_flg_ctrl.SetToolTip(u"チェックを入れると、手首が床に沈み込んだり浮いてたりする場合に、元モデルに合わせて手首の位置を調整できます。\nセンター位置も一緒に調整します。")
        self.arm_alignment_floor_flg_ctrl.Bind(wx.EVT_CHECKBOX, self.on_check_arm_process_alignment)
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
        self.alignment_distance_wrist_slider.Bind(wx.EVT_SCROLL_CHANGED, self.on_check_arm_process_alignment)
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
        self.alignment_distance_finger_slider.Bind(wx.EVT_SCROLL_CHANGED, self.on_check_arm_process_alignment)
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
        self.alignment_distance_floor_slider.Bind(wx.EVT_SCROLL_CHANGED, self.on_check_arm_process_alignment)
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
    
    def get_avoidance_target(self):
        target = {}
        if self.arm_process_flg_avoidance.GetValue() == 0:
            return target
        
        # 選択された剛体リストを入力欄に設定
        for set_no, set_data in self.avoidance_set_dict.items():
            target[set_no - 1] = [set_data.rep_avoidance_names[n] for n in set_data.rep_choices.GetSelections()]
        
        return target
    
    def on_click_avoidance_target(self, event: wx.Event):
        if self.avoidance_dialog.ShowModal() == wx.ID_CANCEL:
            return     # the user changed their mind

        # 一旦クリア
        self.avoidance_target_txt_ctrl.SetValue("")

        # 選択された剛体リストを入力欄に設定
        for set_no, set_data in self.avoidance_set_dict.items():
            # 選択肢ごとの表示文言
            selections = [set_data.rep_choices.GetString(n) for n in set_data.rep_choices.GetSelections()]
            self.avoidance_target_txt_ctrl.WriteText("【No.{0}】{1}\n".format(set_no, ', '.join(selections)))

        self.arm_process_flg_avoidance.SetValue(1)
        self.avoidance_dialog.Hide()

    def initialize(self, event: wx.Event):
        if 1 in self.avoidance_set_dict:
            # ファイルタブ用接触回避のファイルセットがある場合
            if self.frame.file_panel_ctrl.file_set.is_loaded():
                # 既にある場合、ハッシュチェック
                if self.avoidance_set_dict[1].equal_hashdigest(self.frame.file_panel_ctrl.file_set):
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
            if set_no in self.avoidance_set_dict:
                # 複数タブ用接触回避のファイルセットがある場合
                if multi_file_set.is_loaded():
                    # 既にある場合、ハッシュチェック
                    if self.avoidance_set_dict[set_no].equal_hashdigest(multi_file_set):
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

    def add_set(self, set_idx: int, file_set: SizingFileSet, replace: bool):
        new_avoidance_set = AvoidanceSet(self.frame, self, self.avoidance_dialog.scrolled_window, set_idx, file_set)
        if replace:
            # 置き換え
            self.avoidance_dialog.set_list_sizer.Hide(self.avoidance_set_dict[set_idx].set_sizer, recursive=True)
            self.avoidance_dialog.set_list_sizer.Replace(self.avoidance_set_dict[set_idx].set_sizer, new_avoidance_set.set_sizer, recursive=True)
        else:
            # 新規追加
            self.avoidance_dialog.set_list_sizer.Add(new_avoidance_set.set_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.avoidance_set_dict[set_idx] = new_avoidance_set

        # スクロールバーの表示のためにサイズ調整
        self.avoidance_dialog.set_list_sizer.Layout()
        self.avoidance_dialog.set_list_sizer.FitInside(self.avoidance_dialog.scrolled_window)

    # VMD出力ファイルパス生成
    def set_output_vmd_path(self, is_force=False):
        # 念のため出力ファイルパス自動生成（空の場合設定）
        self.frame.file_panel_ctrl.file_set.set_output_vmd_path()

        # multiのも出力ファイルパス自動生成（空の場合設定）
        for file_set in self.frame.multi_panel_ctrl.file_set_list:
            file_set.set_output_vmd_path()
    
    # 処理対象：接触回避ON
    def on_check_arm_process_avoidance(self, event: wx.Event):
        # ラジオボタンかチェックボックスイベントがTrueの場合、切り替え
        if ((isinstance(event.GetEventObject(), wx.RadioButton) or isinstance(event.GetEventObject(), wx.CheckBox)) and event.GetEventObject().GetValue()) \
                or (not isinstance(event.GetEventObject(), wx.RadioButton)):
            if self.arm_process_flg_avoidance.GetValue() == 0:
                self.arm_process_flg_avoidance.SetValue(1)
            else:
                self.arm_process_flg_avoidance.SetValue(0)
            # パス再生成
            self.set_output_vmd_path()
        event.Skip()

    # 処理対象：手首位置合わせON
    def on_check_arm_process_alignment(self, event: wx.Event):
        # ラジオボタンかチェックボックスイベントがTrueの場合、切り替え
        if ((isinstance(event.GetEventObject(), wx.RadioButton) or isinstance(event.GetEventObject(), wx.CheckBox)) and event.GetEventObject().GetValue()) \
                or (not isinstance(event.GetEventObject(), wx.RadioButton)):
            if self.arm_process_flg_alignment.GetValue() == 0:
                self.arm_process_flg_alignment.SetValue(1)
            else:
                self.arm_process_flg_alignment.SetValue(0)
            # パス再生成
            self.set_output_vmd_path()

        if self.arm_alignment_finger_flg_ctrl.GetValue() and len(self.frame.multi_panel_ctrl.file_set_list) > 0:
            self.frame.on_popup_finger_warning(event)

        event.Skip()


class AvoidanceSet():

    def __init__(self, frame: wx.Frame, panel: wx.Panel, window: wx.Window, set_idx: int, file_set: SizingFileSet):
        self.frame = frame
        self.panel = panel
        self.window = window
        self.set_idx = set_idx
        self.file_set = file_set
        self.rep_model_digest = 0 if not file_set.rep_model_file_ctrl.data else file_set.rep_model_file_ctrl.data.digest
        self.rep_avoidances = ["頭接触回避 (頭)"]   # 選択肢文言
        self.rep_avoidance_names = ["頭接触回避"]   # 選択肢文言に紐付くモーフ名

        for rigidbody_name, rigidbody in file_set.rep_model_file_ctrl.data.rigidbodies.items():
            # 処理対象剛体：有効なボーン追従剛体
            if rigidbody.isModeStatic() and rigidbody.bone_index in file_set.rep_model_file_ctrl.data.bone_indexes:
                self.rep_avoidances.append("{0} ({1})".format(rigidbody.name, file_set.rep_model_file_ctrl.data.bone_indexes[rigidbody.bone_index]))
                self.rep_avoidance_names.append(rigidbody.name)

        self.set_sizer = wx.StaticBoxSizer(wx.StaticBox(self.window, wx.ID_ANY, "【No.{0}】".format(set_idx)), orient=wx.VERTICAL)

        # 選択コントロール
        self.rep_choices = wx.ListBox(self.window, id=wx.ID_ANY, choices=self.rep_avoidances, style=wx.LB_MULTIPLE | wx.LB_NEEDED_SB, size=(-1, 220))
        # 頭接触回避はデフォルトで選択
        self.rep_choices.SetSelection(0)
        self.set_sizer.Add(self.rep_choices, 0, wx.ALL, 5)

    # 現在のファイルセットのハッシュと同じであるかチェック
    def equal_hashdigest(self, now_file_set: SizingFileSet):
        return self.rep_model_digest == now_file_set.rep_model_file_ctrl.data.digest


class AvoidanceDialog(wx.Dialog):

    def __init__(self, parent):
        super().__init__(parent, id=wx.ID_ANY, title="接触回避剛体選択", pos=(-1, -1), size=(700, 450), style=wx.DEFAULT_DIALOG_STYLE, name="AvoidanceDialog")

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # 説明文
        self.description_txt = wx.StaticText(self, wx.ID_ANY, u"手を回避させたいボーン追従剛体を変換先モデルから選択する事ができます。\n" \
                                             + u"「頭接触回避」は、頭の大きさを自動計算した剛体です。結果が思わしくない場合は、選択を外してください。\n" \
                                             + u"ボーン追従剛体であれば制限はありませんが、あまり多くの剛体を選ぶと手がどこにも避けられず、思わぬ結果になる場合があります。", wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.description_txt, 0, wx.ALL, 5)

        # ボタン
        self.btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.ok_btn = wx.Button(self, wx.ID_OK, "OK")
        self.btn_sizer.Add(self.ok_btn, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        self.calcel_btn = wx.Button(self, wx.ID_CANCEL, "キャンセル")
        self.btn_sizer.Add(self.calcel_btn, 0, wx.ALL, 5)
        self.sizer.Add(self.btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        self.static_line01 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.sizer.Add(self.static_line01, 0, wx.EXPAND | wx.ALL, 5)

        self.scrolled_window = wx.ScrolledWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, \
                                                 wx.FULL_REPAINT_ON_RESIZE | wx.HSCROLL | wx.ALWAYS_SHOW_SB)
        self.scrolled_window.SetScrollRate(5, 5)

        # 接触回避用剛体セット用基本Sizer
        self.set_list_sizer = wx.BoxSizer(wx.HORIZONTAL)

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

