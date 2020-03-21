# -*- coding: utf-8 -*-
#

import re
import os
import wx
import glob
from mmd.PmxReader import PmxReader
from mmd.VmdReader import VmdReader
from mmd.VpdReader import VpdReader
from utils import MFormUtils, MFileutils
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class BaseFilePickerCtrl():
    
    # 拡張子別ワイルドカード
    WILDCARD_DICT = {
        ("vmd", "vpd"): u"VMD/VPDファイル (*.vmd, *.vpd)|*.vmd;*.vpd|すべてのファイル (*.*)|*.*",
        ("pmx"): u"PMXファイル (*.pmx)|*.pmx|すべてのファイル (*.*)|*.*",
        ("vmd"): u"VMDファイル (*.vmd)|*.vmd|すべてのファイル (*.*)|*.*",
    }

    def __init__(self, form, parent, title, message, file_type, style, tooltip, file_model_spacer=0, \
                 title_parts_ctrl=None, file_parts_ctrl=None, is_change_output=False, is_aster=False, is_save=False):
        super().__init__()

        self.form = form
        self.parent = parent
        self.title = title
        self.message = message
        self.file_type = file_type
        self.style = style
        self.title_parts_ctrl = None
        self.file_parts_ctrl = None
        self.file_model_ctrl = None
        self.is_change_output = is_change_output
        self.is_aster = is_aster
        self.is_save = is_save
        self.data = None

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # ------------------------
        # ファイルタイトル
        self.title_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.title_ctrl = wx.StaticText(parent, wx.ID_ANY, title, wx.DefaultPosition, wx.DefaultSize, 0)
        self.title_ctrl.Wrap(-1)

        self.title_sizer.Add(self.title_ctrl, 0, wx.ALL, 5)

        # ファイルタイトルパーツ（チェックボックス等）
        if title_parts_ctrl:
            self.title_parts_ctrl = title_parts_ctrl
            self.title_sizer.Add(self.title_parts_ctrl, 0, wx.ALL, 5)

        # ファイルモデル
        if file_model_spacer > 0:
            self.file_model_ctrl = FileModelCtrl(parent, self, title, file_model_spacer)
            self.title_sizer.Add(self.file_model_ctrl.spacer_ctrl, 0, wx.ALL, 5)
            self.title_sizer.Add(self.file_model_ctrl.txt_ctrl, 0, wx.ALL, 5)

        self.sizer.Add(self.title_sizer, 0, wx.EXPAND, 5)

        # ------------------------
        # ファイルコントロール
        self.file_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.file_ctrl = wx.FilePickerCtrl(parent, wx.ID_ANY, wx.EmptyString, message, BaseFilePickerCtrl.WILDCARD_DICT[self.file_type], wx.DefaultPosition, wx.DefaultSize, style)
        self.file_ctrl.GetPickerCtrl().SetLabel("開く")
        self.file_ctrl.SetToolTip(tooltip)

        self.file_sizer.Add(self.file_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        # ファイルコントロールパーツ（履歴ボタン等）
        if file_parts_ctrl:
            self.file_parts_ctrl = file_parts_ctrl
            self.file_sizer.Add(self.file_parts_ctrl, 0, wx.ALL, 5)

        self.sizer.Add(self.file_sizer, 0, wx.EXPAND, 5)

        # ------------------------
        # 「開く」ボタン押下時処理
        self.file_ctrl.GetPickerCtrl().Bind(wx.EVT_BUTTON, self.on_pick_file)

        # D&Dの実装
        self.file_ctrl.SetDropTarget(MFileDropTarget(self))

        # ファイルパス変更時
        self.file_ctrl.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_change_file)
    
    def on_pick_file(self, event):
        event.Skip()
    
    def on_change_file(self, event):
        # 先頭と末尾の改行は除去
        target_path = self.file_ctrl.GetPath().strip()
        logger.test("target_path strip: %s", target_path)

        # 先頭と末尾のダブルクォーテーションは除去
        target_path = re.sub(r'^\\+\"(\w)\\', r'\1:\\', target_path)
        target_path = target_path.strip("\"")
        logger.test("target_path strip: %s", target_path)

        # 再設定
        self.file_ctrl.SetPath(target_path)

        logger.test("self.file_model_ctrl: %s", self.file_model_ctrl)

        # ファイルモデルがある場合、出力
        if self.file_model_ctrl:
            self.file_model_ctrl.set_model(target_path)
        
        # 出力ファイル変更対象の場合、出力ファイル更新
        if self.is_change_output:
            MFormUtils.create_output_vmd_path(self.form)
    
    def disable(self):
        self.file_ctrl.GetPickerCtrl().Disable()
        self.file_ctrl.GetTextCtrl().Disable()
        
        if self.title_parts_ctrl:
            self.title_parts_ctrl.Disable()
        
        if self.file_parts_ctrl:
            self.file_parts_ctrl.Disable()

    def enable(self):
        self.file_ctrl.GetPickerCtrl().Enable()
        self.file_ctrl.GetTextCtrl().Enable()
        
        if self.title_parts_ctrl:
            self.title_parts_ctrl.Enable()
        
        if self.file_parts_ctrl:
            self.file_parts_ctrl.Enable()
    
    def is_valid(self, is_print=True):
        if self.is_aster:
            file_path_list = [p for p in sorted(glob.glob(self.file_ctrl.GetPath())) if os.path.isfile(p)]

            if len(file_path_list) == 0:
                logger.error("{0}が見つかりませんでした。\n入力パス: {1}".format(self.title, self.file_ctrl.GetPath()), decoration=MLogger.DECORATION_BOX)
                return False

            file_path = file_path_list[0]
        else:
            file_path = self.file_ctrl.GetPath()

        if not self.is_save and not os.path.exists(file_path):
            logger.error("{0}が見つかりませんでした。\n入力パス: {1}".format(self.title, self.file_ctrl.GetPath()), decoration=MLogger.DECORATION_BOX)
            return False

        if not self.is_save and not os.path.isfile(file_path):
            logger.error("{0}が正常なファイルとして見つかりませんでした。\n入力パス: {1}".format(self.title, self.file_ctrl.GetPath()), decoration=MLogger.DECORATION_BOX)
            return False

        # 拡張子
        _, ext = os.path.splitext(os.path.basename(file_path))

        if ext[1:].lower() not in self.file_type:
            logger.error("{0}の拡張子が正しくありません。\n入力パス: {1}\n設定可能拡張子: {2}".format(self.title, self.file_ctrl.GetPath(), self.file_type), decoration=MLogger.DECORATION_BOX)
            return False
        
        # 親ディレクトリ取得
        if self.is_save:
            # 書き込みはそのまま親
            dir_path = os.path.dirname(self.file_ctrl.GetPath())
        else:
            # 読み取りは解析する
            dir_path = MFileutils.get_dir_path(self.file_ctrl.GetPath())

        if not os.path.exists(dir_path):
            logger.error("{0}が見つかりませんでした。\n入力パス: {1}".format(self.title, dir_path), decoration=MLogger.DECORATION_BOX)
            return False

        if not os.path.isdir(dir_path):
            logger.error("{0}が正常なフォルダとして見つかりませんでした。\n入力パス: {1}".format(self.title, dir_path), decoration=MLogger.DECORATION_BOX)
            return False

        if not os.access(dir_path, os.W_OK):
            logger.error("{0}の親フォルダに書き込み権限がありません。\n入力パス: {1}".format(self.title, dir_path), decoration=MLogger.DECORATION_BOX)
            return False

        # 出力系の場合、自身のファイル上書き用の書き込み権限
        if self.is_save and os.path.isfile(self.file_ctrl.GetPath()) and not os.access(self.file_ctrl.GetPath(), os.W_OK):
            logger.error("{0}に書き込み権限がありません。\n入力パス: {1}".format(self.title, self.file_ctrl.GetPath()), decoration=MLogger.DECORATION_BOX)
            return False

        return True

    # ファイル読み込み処理
    def load(self, file_idx=0):
        if not self.is_valid():
            # 読み込み可能か
            self.data = None
            return False

        try:
            if self.is_aster:
                file_path_list = [p for p in sorted(glob.glob(self.file_ctrl.GetPath())) if os.path.isfile(p)]

                if len(file_path_list) == 0:
                    # 読み込み可能か
                    self.data = None
                    return False

                file_path = file_path_list[file_idx]
            else:
                file_path = self.file_ctrl.GetPath()

            file_name, input_ext = os.path.splitext(os.path.basename(file_path))

            logger.test("input_ext: %s", input_ext)

            # 拡張子別にリーダー生成
            if input_ext.lower() == ".vmd":
                reader = VmdReader(file_path)
            elif input_ext.lower() == ".vpd":
                reader = VpdReader(file_path)
            elif input_ext.lower() == ".pmx":
                reader = PmxReader(file_path)
            else:
                return False
            
            # ハッシュ値取得
            new_data_digest = reader.hexdigest()

            # 新規データがあり、かつハッシュが違う場合、置き換え
            if new_data_digest and ((self.data and self.data.digest != new_data_digest) or not self.data):
                # ハッシュが取得できてて、過去データがないかハッシュが違う場合、読み込み
                self.data = reader.read_data()
                logger.info("%s 読み込み成功: %s" % (self.title, os.path.basename(file_path)), decoration=MLogger.DECORATION_SIMPLE)
                return True
            elif new_data_digest and self.data and self.data.digest == new_data_digest:
                # ハッシュが同じ場合、そのままスルー
                logger.info("%s 読み込み成功: %s" % (self.title, os.path.basename(file_path)), decoration=MLogger.DECORATION_SIMPLE)
                return True

        except Exception as e:
            logger.test("load失敗", e)

        logger.error("%s 読み込み失敗: %s" % (self.title, os.path.basename(file_path)), decoration=MLogger.DECORATION_BOX)
        return False


class FileModelCtrl():

    def __init__(self, parent, picker, title, spacer_cnt):
        super().__init__()

        self.parent = parent
        self.picker = picker
        self.title = title
        self.spacer_ctrl = wx.StaticText(parent, wx.ID_ANY, "".join(["　" for n in range(spacer_cnt)]))

        self.txt_ctrl = wx.TextCtrl(parent, wx.ID_ANY, "（未設定）", wx.DefaultPosition, (350, -1), wx.TE_READONLY | wx.BORDER_NONE | wx.WANTS_CHARS)
        self.txt_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        self.txt_ctrl.SetToolTip(u"{0}に記録されているモデル名です。\n文字列は選択＆コピー可能です。".format(title))

    def set_model(self, target_path):
        self.txt_ctrl.SetValue("（{0}）".format(self.get_model_name()))

    # VMDのモデル名取得
    def get_model_name(self):
        try:
            if self.picker.is_aster:
                file_path_list = [p for p in sorted(glob.glob(self.picker.file_ctrl.GetPath())) if os.path.isfile(p)]

                if len(file_path_list) == 0:
                    return "取得失敗"

                file_path = file_path_list[0]
            else:
                file_path = self.picker.file_ctrl.GetPath()

            file_name, input_ext = os.path.splitext(os.path.basename(file_path))

            logger.test("input_ext: %s", input_ext)

            model_name = "未設定"
            if input_ext.lower() == ".vmd":
                reader = VmdReader(file_path)
            elif input_ext.lower() == ".vpd":
                reader = VpdReader(file_path)
            elif input_ext.lower() == ".pmx":
                reader = PmxReader(file_path)
            else:
                return "対象外拡張子"

            model_name = reader.read_model_name()
            if not model_name:
                model_name = "取得失敗"

            logger.test("model_name: %s, ", model_name)

            return model_name
        except Exception as e:
            logger.test("get_model_name 失敗", e)

            return "取得失敗"


class MFileDropTarget(wx.FileDropTarget):
    def __init__(self, parent):
        self.parent = parent

        wx.FileDropTarget.__init__(self)
    
    def OnDropFiles(self, x, y, files):
        # ファイルパスをテキストフィールドに表示
        file_name, input_ext = os.path.splitext(os.path.basename(files[0]))

        logger.test("file_name: %s, input_ext: %s", file_name, input_ext)
        logger.test("input_ext[1:].lower(): %s", input_ext[1:].lower())
        logger.test("self.parent.file_type: %s", self.parent.file_type)
        logger.test("test: %s", input_ext[1:].lower() in self.parent.file_type)

        if input_ext[1:].lower() in self.parent.file_type:
            # 入力拡張子が許容拡張子の場合、設定

            # 拡張子を許容してたらOK
            self.parent.file_ctrl.SetPath(files[0])

            # ファイル変更処理
            self.parent.on_change_file(wx.FileDirPickerEvent())

            return True
        
        display_file_type = self.parent.file_type
        if type(self.parent.file_type) == tuple:
            display_file_type = ",".join(self.parent.file_type)

        logger.error("{0}の拡張子が正しくありません。\n入力ファイル拡張子: {1}\n設定可能拡張子: {2}".format(self.parent.title, input_ext, display_file_type), decoration=MLogger.DECORATION_BOX)

        # 許容拡張子外の場合、不許可
        return False
