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

        avoidance_tooltip = u"名前に「接触回避」が含まれている剛体と手首・指先との接触を回避します。"
        alignment_tooltip = u"変換先モデルの手首位置が、作成元モデルの手首とほぼ同じ位置になるよう、手首位置を調整します。"

        # 同じグループなので、とりあえず宣言だけしておく
        self.arm_process_flg_nothing = wx.RadioButton(self, wx.ID_ANY, u"腕関係の処理を行わない", wx.DefaultPosition, wx.DefaultSize, style=wx.RB_GROUP)
        self.arm_process_flg_nothing.SetValue(True)
        self.arm_process_flg_nothing.Bind(wx.EVT_RADIOBUTTON, self.set_output_vmd_path)
        self.arm_process_flg_avoidance = wx.RadioButton(self, wx.ID_ANY, u"", wx.DefaultPosition, wx.DefaultSize)
        self.arm_process_flg_avoidance.SetToolTip(avoidance_tooltip)
        self.arm_process_flg_avoidance.Bind(wx.EVT_RADIOBUTTON, self.set_output_vmd_path)
        self.arm_process_flg_alignment = wx.RadioButton(self, wx.ID_ANY, u"", wx.DefaultPosition, wx.DefaultSize)
        self.arm_process_flg_alignment.SetToolTip(alignment_tooltip)
        self.arm_process_flg_alignment.Bind(wx.EVT_RADIOBUTTON, self.set_output_vmd_path)

        self.description_txt = wx.StaticText(self, wx.ID_ANY, "未実装", wx.DefaultPosition, wx.DefaultSize, 0)
        # self.description_txt = wx.StaticText(self, wx.ID_ANY, "腕を変換先モデルに合わせて調整する事ができます。\n「剛体接触回避」と「手首位置合わせ」のいずれかのみ実行できます。" + \
        #                                      "\n腕の動きが、元々のモーションから変わる事があります。いずれもそれなりに時間がかかります。", wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.description_txt, 0, wx.ALL, 5)

        self.static_line01 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.sizer.Add(self.static_line01, 0, wx.EXPAND | wx.ALL, 5)

        # デフォルト
        self.nothing_title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.nothing_title_sizer.Add(self.arm_process_flg_nothing, 0, wx.ALL, 5)
        self.sizer.Add(self.nothing_title_sizer, 0, wx.ALL, 5)
        
        self.static_line02 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.sizer.Add(self.static_line02, 0, wx.EXPAND | wx.ALL, 5)

        # 剛体接触回避 ----------------
        self.avoidance_title_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 剛体接触回避タイトルラジオ
        self.avoidance_title_txt = wx.StaticText(self, wx.ID_ANY, u"剛体接触回避", wx.DefaultPosition, wx.DefaultSize, 0)
        self.avoidance_title_txt.SetToolTip(avoidance_tooltip)
        self.avoidance_title_txt.Wrap(-1)
        self.avoidance_title_txt.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))

        self.avoidance_title_sizer.Add(self.arm_process_flg_avoidance, 0, wx.ALL, 5)
        self.avoidance_title_sizer.Add(self.avoidance_title_txt, 0, wx.ALL, 5)
        self.sizer.Add(self.avoidance_title_sizer, 0, wx.ALL, 5)

        # 剛体接触回避説明文
        self.avoidance_description_txt = wx.StaticText(self, wx.ID_ANY, avoidance_tooltip, wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.avoidance_description_txt, 0, wx.ALL, 5)

        self.static_line03 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.sizer.Add(self.static_line03, 0, wx.EXPAND | wx.ALL, 5)

        # 手首位置合わせ --------------------
        self.alignment_title_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 手首位置合わせタイトルラジオ
        self.alignment_title_txt = wx.StaticText(self, wx.ID_ANY, u"手首位置合わせ", wx.DefaultPosition, wx.DefaultSize, 0)
        self.alignment_title_txt.SetToolTip("両手を合わせたり、床に手をついたりするモーションを、変換先モデルの手首位置に合わせて調整します。\n" + \
                                            "それぞれの距離を調整することで、位置合わせの適用範囲を調整することができます。")
        self.alignment_title_txt.Wrap(-1)
        self.alignment_title_txt.SetFont(wx.Font(wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString))

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
        self.arm_alignment_finger_flg_ctrl.SetToolTip(u"チェックを入れると、フィンガータットモーション等、指間の距離を基準に手首位置を調整できます。")
        self.alignment_option_sizer.Add(self.arm_alignment_finger_flg_ctrl, 0, wx.ALL, 5)

        # 床位置合わせ
        self.arm_alignment_floor_flg_ctrl = wx.CheckBox(self, wx.ID_ANY, u"床との位置合わせも一緒に行う", wx.DefaultPosition, wx.DefaultSize, 0)
        self.arm_alignment_floor_flg_ctrl.SetToolTip(u"チェックを入れると、手首が床に沈み込んだり浮いてたりする場合に、元モデルに合わせて手首の位置を調整できます。\nセンター位置も一緒に調整します。")
        self.alignment_option_sizer.Add(self.arm_alignment_floor_flg_ctrl, 0, wx.ALL, 5)

        self.sizer.Add(self.alignment_option_sizer, 0, wx.ALL, 5)

        # 手首位置スライダー
        self.alignment_distance_wrist_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.alignment_distance_wrist_txt = wx.StaticText(self, wx.ID_ANY, u"手首間の距離　  ", wx.DefaultPosition, wx.DefaultSize, 0)
        self.alignment_distance_wrist_txt.SetToolTip(u"どのくらい手首が近付いた場合に、手首位置合わせを実行するか指定してください。\n値が小さいほど、手首が近付いた時だけ手首位置合わせを行います。\n距離の単位は、元モデルの手のひらの大きさです。" + 
                                                     "\nサイジング実行時、手首間の距離がメッセージ欄に出てますので、参考にしてください。\nスライダーを最大に設定すると、常に手首位置合わせを行います。（両手剣等に便利です）")
        self.alignment_distance_wrist_txt.Wrap(-1)
        self.alignment_distance_wrist_sizer.Add(self.alignment_distance_wrist_txt, 0, wx.ALL, 5)

        self.alignment_distance_wrist_label = wx.StaticText(self, wx.ID_ANY, u"（1.7）", wx.DefaultPosition, wx.DefaultSize, 0)
        self.alignment_distance_wrist_label.SetToolTip(u"現在指定されている手首間の距離です。元モデルの両手首位置がこの範囲内である場合、手首間の位置合わせを行います。")
        self.alignment_distance_wrist_label.Wrap(-1)
        self.alignment_distance_wrist_sizer.Add(self.alignment_distance_wrist_label, 0, wx.ALL, 5)

        self.alignment_distance_wrist_slider = FloatSliderCtrl(self, wx.ID_ANY, 1.7, 0, 10, 0.1, self.alignment_distance_wrist_label, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL)
        self.alignment_distance_wrist_sizer.Add(self.alignment_distance_wrist_slider, 1, wx.ALL | wx.EXPAND, 5)

        self.sizer.Add(self.alignment_distance_wrist_sizer, 1, wx.ALL | wx.EXPAND, 5)


        

        self.fit()

    # VMD出力ファイルパス生成
    def set_output_vmd_path(self, is_force=False):
        pass

