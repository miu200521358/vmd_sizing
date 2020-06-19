# -*- coding: utf-8 -*-
#
import os
import wx

from form.panel.BasePanel import BasePanel
from form.parts.SizingFileSet import SizingFileSet
from form.parts.BaseFilePickerCtrl import BaseFilePickerCtrl
from form.parts.HistoryFilePickerCtrl import HistoryFilePickerCtrl
from utils import MFileUtils
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class CameraPanel(BasePanel):
        
    def __init__(self, frame: wx.Frame, parent: wx.Notebook, tab_idx: int):
        super().__init__(frame, parent, tab_idx)

        self.header_panel = CameraHeaderPanel(self.frame, self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.header_sizer = wx.BoxSizer(wx.VERTICAL)

        self.description_txt = wx.StaticText(self.header_panel, wx.ID_ANY, u"指定されたカメラモーションのサイジングを、ボーンモーションのサイジングと同時に行えます。\n" \
                                             + "全長オフセットYは、カメラに映す変換先モデルの全長を調整するオフセット値を指定できます。", wx.DefaultPosition, wx.DefaultSize, 0)
        self.header_sizer.Add(self.description_txt, 0, wx.ALL, 5)

        self.static_line01 = wx.StaticLine(self.header_panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.header_sizer.Add(self.static_line01, 0, wx.EXPAND | wx.ALL, 5)

        # カメラVMDファイルコントロール
        self.camera_vmd_file_ctrl = HistoryFilePickerCtrl(self.frame, self.header_panel, u"カメラモーションVMD", u"カメラモーションVMDファイルを開く", ("vmd"), wx.FLP_DEFAULT_STYLE, \
                                                          u"調整したいカメラモーションのVMDパスを指定してください。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。", \
                                                          file_model_spacer=0, title_parts_ctrl=None, title_parts2_ctrl=None, file_histories_key="camera_vmd", is_change_output=True, \
                                                          is_aster=False, is_save=False, set_no=1)
        self.header_sizer.Add(self.camera_vmd_file_ctrl.sizer, 1, wx.EXPAND, 0)

        # 出力先VMDファイルコントロール
        self.output_camera_vmd_file_ctrl = BaseFilePickerCtrl(frame, self.header_panel, u"出力カメラVMD", u"出力カメラVMDファイルを開く", ("vmd"), wx.FLP_OVERWRITE_PROMPT | wx.FLP_SAVE | wx.FLP_USE_TEXTCTRL, \
                                                              u"調整結果のカメラVMD出力パスを指定してください。\nカメラVMDファイル名に基づいて自動生成されますが、任意のパスに変更することも可能です。", \
                                                              is_aster=False, is_save=True, set_no=1)
        self.header_sizer.Add(self.output_camera_vmd_file_ctrl.sizer, 1, wx.EXPAND, 0)

        self.header_panel.SetSizer(self.header_sizer)
        self.header_panel.Layout()
        self.sizer.Add(self.header_panel, 0, wx.EXPAND | wx.ALL, 5)

        # カメラセット(key: ファイルセット番号, value: カメラセット)
        self.camera_set_dict = {}
        # カメラセット用基本Sizer
        self.set_list_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.scrolled_window = CameraScrolledWindow(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, \
                                                    wx.FULL_REPAINT_ON_RESIZE | wx.VSCROLL | wx.ALWAYS_SHOW_SB)
        self.scrolled_window.SetScrollRate(5, 5)

        # スクロールバーの表示のためにサイズ調整
        self.scrolled_window.SetSizer(self.set_list_sizer)
        self.scrolled_window.Layout()
        self.sizer.Add(self.scrolled_window, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 5)
        self.sizer.Layout()
        self.fit()
    
    # カメラタブからカメラリスト生成
    def get_camera_list(self, set_no: int):
        if set_no not in self.camera_set_dict:
            # そもそも登録がなければ何もなし
            return []
        else:
            # あれば、そのNoのカメラリスト
            return self.camera_set_dict[set_no].get_camera_list()

    # カメラタブ初期化処理
    def initialize(self, event: wx.Event):
        if 1 not in self.camera_set_dict:
            # 空から作る場合、ファイルタブのファイルセット参照
            self.add_set(1, self.frame.file_panel_ctrl.file_set)
        else:
            # ある場合、モデル名だけ入替
            self.camera_set_dict[1].model_name_txt.setValue("{0} → {1}".format(\
                                                            self.frame.file_panel_ctrl.file_set.org_model_file_ctrl.file_model_ctrl.txt_ctrl.GetValue()[1:-1], \
                                                            self.frame.file_panel_ctrl.file_set.rep_model_file_ctrl.file_model_ctrl.txt_ctrl.GetValue()[1:-1]))
        
        # multiはあるだけ調べる
        for multi_file_set_idx, multi_file_set in enumerate(self.frame.multi_panel_ctrl.file_set_list):
            set_no = multi_file_set_idx + 2
            if set_no not in self.camera_set_dict:
                # 空から作る場合、複数タブのファイルセット参照
                self.add_set(set_no, multi_file_set)
            else:
                # ある場合、モデル名だけ入替
                self.camera_set_dict[set_no].model_name_txt.setValue("{0} → {1}".format(\
                                                                     multi_file_set.org_model_file_ctrl.file_model_ctrl.txt_ctrl.GetValue()[1:-1], \
                                                                     multi_file_set.rep_model_file_ctrl.file_model_ctrl.txt_ctrl.GetValue()[1:-1]))

    def add_set(self, set_idx: int, file_set: SizingFileSet):
        new_camera_set = CameraSet(self.frame, self, self.scrolled_window, set_idx, file_set)
        self.set_list_sizer.Add(new_camera_set.set_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.camera_set_dict[set_idx] = new_camera_set
        
        # スクロールバーの表示のためにサイズ調整
        self.set_list_sizer.Layout()
        self.set_list_sizer.FitInside(self.scrolled_window)

    # フォーム無効化
    def disable(self):
        self.file_set.disable()

    # フォーム無効化
    def enable(self):
        self.file_set.enable()

    def save(self):
        self.camera_vmd_file_ctrl.save()


class CameraScrolledWindow(wx.ScrolledWindow):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

    # 複数モーション用カメラの場合、出力パスは変わらないのでスルー
    def set_output_vmd_path(self, is_force=False):
        pass


class CameraHeaderPanel(wx.Panel):

    def __init__(self, frame, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr):
        super().__init__(parent, id=id, pos=pos, size=size, style=style, name=name)

        self.parent = parent
        self.frame = frame

    # ファイル変更時の処理
    def on_change_file(self, event: wx.Event):
        self.set_output_vmd_path()
    
    def set_output_vmd_path(self, is_force=False):
        output_camera_vmd_path = MFileUtils.get_output_camera_vmd_path(
            self.parent.camera_vmd_file_ctrl.file_ctrl.GetPath(),
            self.frame.file_panel_ctrl.file_set.rep_model_file_ctrl.file_ctrl.GetPath(),
            self.parent.output_camera_vmd_file_ctrl.file_ctrl.GetPath(), is_force)

        self.parent.output_camera_vmd_file_ctrl.file_ctrl.SetPath(output_camera_vmd_path)

        if len(output_camera_vmd_path) >= 255 and os.name == "nt":
            logger.error("生成予定のファイルパスがWindowsの制限を超えています。\n生成予定パス: {0}".format(output_camera_vmd_path), decoration=MLogger.DECORATION_BOX)
        

class CameraSet():

    def __init__(self, frame: wx.Frame, panel: wx.Panel, window: wx.Window, set_idx: int, file_set: SizingFileSet):
        self.frame = frame
        self.panel = panel
        self.window = window
        self.set_idx = set_idx
        self.file_set = file_set

        self.set_sizer = wx.StaticBoxSizer(wx.StaticBox(self.window, wx.ID_ANY, "【No.{0}】".format(set_idx)), orient=wx.VERTICAL)

        self.model_name_txt = wx.StaticText(self.window, wx.ID_ANY, \
                                            "{0} → {1}".format(file_set.org_model_file_ctrl.file_model_ctrl.txt_ctrl.GetValue()[1:-1], \
                                                               file_set.rep_model_file_ctrl.file_model_ctrl.txt_ctrl.GetValue()[1:-1]), wx.DefaultPosition, wx.DefaultSize, 0)
        self.model_name_txt.Wrap(-1)
        self.set_sizer.Add(self.model_name_txt, 0, wx.ALL, 5)

        # カメラPMXファイルコントロール
        self.camera_model_file_ctrl = HistoryFilePickerCtrl(frame, window, u"カメラ作成元モデルPMX", u"カメラ作成元モデルPMXファイルを開く", ("pmx"), wx.FLP_DEFAULT_STYLE, \
                                                            u"カメラ作成に使用されたモデルのPMXパスを指定してください。\n未指定の場合、モーション作成元モデルPMXを使用します。" \
                                                            + "\n精度は落ちますが、類似したサイズ・ボーン構造のモデルでも代用できます。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。", \
                                                            file_model_spacer=20, title_parts_ctrl=None, file_histories_key="camera_pmx", \
                                                            is_change_output=True, is_aster=False, is_save=False, set_no=set_idx)
        self.set_sizer.Add(self.camera_model_file_ctrl.sizer, 1, wx.EXPAND, 0)

        self.offset_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.camera_offset_y_txt = wx.StaticText(self.window, wx.ID_ANY, u"全長Yオフセット", wx.DefaultPosition, wx.DefaultSize, 0)
        self.camera_offset_y_txt.Wrap(-1)
        self.offset_sizer.Add(self.camera_offset_y_txt, 0, wx.ALL, 5)

        # オフセットYコントロール
        self.camera_offset_y_ctrl = wx.SpinCtrlDouble(self.window, id=wx.ID_ANY, size=wx.Size(100, -1), value="0.0", min=-1000, max=1000, initial=0.0, inc=0.1)
        self.camera_offset_y_ctrl.SetToolTip(u"カメラに映す変換先モデルの全長を調整するオフセット値を指定できます。")
        self.camera_offset_y_ctrl.Bind(wx.EVT_MOUSEWHEEL, lambda event: self.frame.on_wheel_spin_ctrl(event, 0.2))
        self.offset_sizer.Add(self.camera_offset_y_ctrl, 0, wx.ALL, 5)

        self.set_sizer.Add(self.offset_sizer, 0, wx.ALL, 0)


