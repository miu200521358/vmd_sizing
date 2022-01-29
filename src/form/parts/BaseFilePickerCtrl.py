# -*- coding: utf-8 -*-
#

import glob
import os
import re
import wx
import logging
from mmd.PmxReader import PmxReader
from mmd.VmdReader import VmdReader
from mmd.VpdReader import VpdReader
from utils import MFileUtils
from utils.MException import SizingException
from utils.MLogger import MLogger # noqa
from utils.MException import MKilledException


logger = MLogger(__name__)


class BaseFilePickerCtrl():
    
    # 拡張子別ワイルドカード
    WILDCARD_DICT = {
        ("vmd", "vpd"): u"VMD/VPDファイル (*.vmd, *.vpd)|*.vmd;*.vpd|すべてのファイル (*.*)|*.*",
        ("pmx"): u"PMXファイル (*.pmx)|*.pmx|すべてのファイル (*.*)|*.*",
        ("vmd"): u"VMDファイル (*.vmd)|*.vmd|すべてのファイル (*.*)|*.*",
        ("csv"): u"CSVファイル (*.csv)|*.csv|すべてのファイル (*.*)|*.*",
    }

    def __init__(self, frame, parent, title, message, file_type, style, tooltip, file_model_spacer=0, \
                 title_parts_ctrl=None, file_parts_ctrl=None, title_parts2_ctrl=None, is_change_output=False, is_aster=False, is_save=False, set_no=0, required=True):
        super().__init__()

        self.frame = frame
        self.parent = parent
        self.title = title
        self.message = message
        self.file_type = file_type
        self.style = style
        self.title_parts_ctrl = None
        self.title_parts2_ctrl = None
        self.file_parts_ctrl = None
        self.file_model_ctrl = None
        self.is_change_output = is_change_output
        self.is_aster = is_aster
        self.is_save = is_save
        self.set_no = set_no
        self.required = required
        self.data = None
        self.astr_path = None
        self.target_paths = []

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
        
        # ファイルタイトルパーツ2
        if title_parts2_ctrl:
            self.title_parts2_ctrl = title_parts2_ctrl
            self.title_sizer.Add(self.title_parts2_ctrl, 0, wx.ALL, 5)

        # ファイルモデル
        if file_model_spacer > 0:
            self.file_model_ctrl = FileModelCtrl(parent, self, title, file_model_spacer, self.set_no)
            self.title_sizer.Add(self.file_model_ctrl.spacer_ctrl, 0, wx.ALL, 5)
            self.title_sizer.Add(self.file_model_ctrl.txt_ctrl, 0, wx.ALL, 5)

        self.sizer.Add(self.title_sizer, 1, wx.EXPAND, 0)

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
        self.file_ctrl.SetDropTarget(MFileDropTarget(self, self.is_aster))

        # ファイルパス変更時
        self.file_ctrl.Bind(wx.EVT_FILEPICKER_CHANGED, self.on_change_file)
    
    def on_pick_file(self, event):
        event.Skip()
    
    def on_change_file(self, event):
        # ダイアログFLGクリア
        self.frame.popuped_finger_warning = False
        
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
        
        # アスタリスクを含む場合、オリジナルパス更新
        if "*" in self.file_ctrl.GetPath():
            self.astr_path = "{0}".format(self.file_ctrl.GetPath())
            self.target_paths = [p for p in glob.glob(self.astr_path) if os.path.isfile(p)]
        else:
            self.astr_path = None
            self.target_paths = []

        # 出力ファイル変更対象の場合、出力ファイル更新
        if self.is_change_output:
            self.parent.set_output_vmd_path(event, True)
        
    def disable(self):
        self.file_ctrl.GetPickerCtrl().Disable()
        self.file_ctrl.GetTextCtrl().Disable()
        
        if self.title_parts_ctrl:
            self.title_parts_ctrl.Disable()
        
        if self.title_parts2_ctrl:
            self.title_parts2_ctrl.Disable()
        
        if self.file_parts_ctrl:
            self.file_parts_ctrl.Disable()

    def enable(self):
        self.file_ctrl.GetPickerCtrl().Enable()
        self.file_ctrl.GetTextCtrl().Enable()
        
        if self.title_parts_ctrl:
            self.title_parts_ctrl.Enable()
        
        if self.title_parts2_ctrl:
            self.title_parts2_ctrl.Enable()
        
        if self.file_parts_ctrl:
            self.file_parts_ctrl.Enable()
    
    def is_set_path(self):
        return len(self.file_ctrl.GetPath()) > 0
    
    def is_valid(self):
        if self.set_no == 0:
            # CSVとかのファイルは番号出力なし
            display_set_no = ""
        else:
            display_set_no = "{0}番目の".format(self.set_no)

        if self.is_aster and self.set_no <= 1:
            base_file_path = self.file_ctrl.GetPath()

            if os.path.exists(base_file_path):
                file_path_list = [base_file_path]
            else:
                file_path_list = [p for p in glob.glob(base_file_path) if os.path.isfile(p)]

            if len(file_path_list) == 0:
                logger.error("{0}{1}の条件に合致するファイルが見つかりませんでした。\n入力パス: {2}".format(
                    display_set_no, self.title, self.file_ctrl.GetPath()), decoration=MLogger.DECORATION_BOX)
                return False

            file_path = file_path_list[0]
        else:
            file_path = self.file_ctrl.GetPath()
        
        if not self.is_save and not os.path.exists(file_path):
            if self.required:
                logger.error("{0}{1}が見つかりませんでした。\n入力パス: {2}".format(
                    display_set_no, self.title, self.file_ctrl.GetPath()), decoration=MLogger.DECORATION_BOX)
                return False
            else:
                # 任意の場合、ファイルパスがなければスルー
                return True

        if not self.is_save and not os.path.isfile(file_path):
            logger.error("{0}{1}が正常なファイルとして見つかりませんでした。\n入力パス: {2}".format(
                display_set_no, self.title, self.file_ctrl.GetPath()), decoration=MLogger.DECORATION_BOX)
            return False

        # 拡張子
        _, ext = os.path.splitext(os.path.basename(file_path))

        if ext[1:].lower() not in self.file_type:
            logger.error("{0}{1}の拡張子が正しくありません。\n入力パス: {2}\n設定可能拡張子: {3}".format(
                display_set_no, self.title, self.file_ctrl.GetPath(), self.file_type), decoration=MLogger.DECORATION_BOX)
            return False
        
        # 親ディレクトリ取得
        if self.is_save:
            # 書き込みはそのまま親
            dir_path = os.path.dirname(self.file_ctrl.GetPath())
        else:
            # 読み取りは解析する
            dir_path = MFileUtils.get_dir_path(self.file_ctrl.GetPath())

        if not os.path.exists(dir_path):
            logger.error("{0}{1}の親フォルダが見つかりませんでした。\n入力パス: {2}".format(
                display_set_no, self.title, dir_path), decoration=MLogger.DECORATION_BOX)
            return False

        if not os.path.isdir(dir_path):
            logger.error("{0}{1}の親フォルダが正常なフォルダとして見つかりませんでした。\n入力パス: {2}".format(
                display_set_no, self.title, dir_path), decoration=MLogger.DECORATION_BOX)
            return False

        if not os.access(dir_path, os.W_OK):
            logger.error("{0}{1}の親フォルダに書き込み権限がありません。\n入力パス: {2}".format(
                display_set_no, self.title, dir_path), decoration=MLogger.DECORATION_BOX)
            return False

        # 出力系の場合、自身のファイル上書き用の書き込み権限
        if self.is_save and os.path.isfile(self.file_ctrl.GetPath()) and not os.access(self.file_ctrl.GetPath(), os.W_OK):
            logger.error("{0}{1}に書き込み権限がありません。\n入力パス: {2}".format(
                display_set_no, self.title, self.file_ctrl.GetPath()), decoration=MLogger.DECORATION_BOX)
            return False

        return True
    
    def path(self):
        return self.file_ctrl.GetPath()

    # ファイルセットからの読み込み処理
    def load_from_set(self, target, results):
        results[target] = self.load()

    # ファイル読み込み処理
    def load(self, file_idx=0, is_check=True):
        if not self.is_set_path():
            # パスが指定されてない場合、そのまま終了
            self.data = None
            return True

        if not self.is_valid():
            # 読み込み可能か
            self.data = None
            return False

        try:
            if self.set_no == 0:
                # CSVとかのファイルは番号出力なし
                display_set_no = ""
            else:
                display_set_no = "【No.{0}】 ".format(self.set_no)

            if self.is_aster and self.set_no == 1:
                base_file_path = self.file_ctrl.GetPath()

                if os.path.exists(base_file_path):
                    file_path_list = [base_file_path]
                else:
                    file_path_list = [p for p in glob.glob(base_file_path) if os.path.isfile(p)]

                if len(file_path_list) == 0:
                    # 読み込み可能か
                    self.data = None
                    return False

                file_path = file_path_list[file_idx]
            else:
                file_path = self.file_ctrl.GetPath()

            file_name, input_ext = os.path.splitext(os.path.basename(file_path))

            # 拡張子別にリーダー生成
            if input_ext.lower() == ".vmd":
                reader = VmdReader(file_path)
            elif input_ext.lower() == ".vpd":
                reader = VpdReader(file_path)
            elif input_ext.lower() == ".pmx":
                reader = PmxReader(file_path, is_check=is_check)
            else:
                logger.error("%s%s 読み込み失敗(拡張子不正): %s", display_set_no, self.title, os.path.basename(file_path), decoration=MLogger.DECORATION_BOX)
                return False
            
            # ハッシュ値取得
            new_data_digest = reader.hexdigest()

            if isinstance(self.data, Exception):
                raise self.data

            # 新規データがあり、かつハッシュが違う場合、置き換え
            if new_data_digest and ((self.data and self.data.digest != new_data_digest) or not self.data):
                # ハッシュが取得できてて、過去データがないかハッシュが違う場合、読み込み
                self.data = reader.read_data()
                    
                logger.info("%s%s 読み込み成功: %s", display_set_no, self.title, os.path.basename(file_path))
                return True
            elif new_data_digest and self.data and self.data.digest == new_data_digest:
                # ハッシュが同じ場合、そのままスルー
                logger.info("%s%s 読み込み成功: %s", display_set_no, self.title, os.path.basename(file_path))
                return True
        except MKilledException:
            logger.warning("読み込み処理を中断します。", decoration=MLogger.DECORATION_BOX)
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message, decoration=MLogger.DECORATION_BOX)
        except Exception as e:
            logger.critical("サイジング処理が意図せぬエラーで終了しました。", e, decoration=MLogger.DECORATION_BOX)
        finally:
            logging.shutdown()

        logger.error("%s%s 読み込み失敗: %s", display_set_no, self.title, os.path.basename(file_path), decoration=MLogger.DECORATION_BOX)
        return False


class FileModelCtrl():

    def __init__(self, parent, picker, title, spacer_cnt, set_no):
        super().__init__()

        self.parent = parent
        self.picker = picker
        self.title = title
        self.set_no = set_no
        self.spacer_ctrl = wx.StaticText(parent, wx.ID_ANY, "".join([" " for n in range(spacer_cnt)]))

        width = 300 if self.set_no == 1 else 220

        self.txt_ctrl = wx.TextCtrl(parent, wx.ID_ANY, "（未設定）", wx.DefaultPosition, (width, -1), wx.TE_READONLY | wx.BORDER_NONE | wx.WANTS_CHARS)
        self.txt_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        self.txt_ctrl.SetToolTip(u"{0}に記録されているモデル名です。\n文字列は選択＆コピー可能です。".format(title))

    def set_model(self, target_path):
        self.txt_ctrl.SetValue("（{0}）".format(self.get_model_name()))

    # VMDのモデル名取得
    def get_model_name(self):
        try:
            if self.picker.is_aster:
                base_file_path = self.picker.file_ctrl.GetPath()

                if os.path.exists(base_file_path):
                    file_path_list = [base_file_path]
                else:
                    file_path_list = [p for p in glob.glob(base_file_path) if os.path.isfile(p)]

                if len(file_path_list) == 0:
                    return "取得失敗"

                file_path = file_path_list[0]
            else:
                file_path = self.picker.file_ctrl.GetPath()

            file_name, input_ext = os.path.splitext(os.path.basename(file_path))

            model_name = "未設定"
            if input_ext.lower() == ".vmd":
                reader = VmdReader(file_path)
            elif input_ext.lower() == ".vpd":
                reader = VpdReader(file_path)
            elif input_ext.lower() == ".pmx":
                reader = PmxReader(file_path)
            else:
                return "対象外拡張子"
            
            try:
                model_name = reader.read_model_name()
            except Exception:
                model_name = "取得失敗"

            logger.test("model_name: %s, ", model_name)

            return model_name
        except Exception as e:
            logger.test("get_model_name 失敗", e)

            return "取得失敗"


class MFileDropTarget(wx.FileDropTarget):
    def __init__(self, parent, is_aster):
        self.parent = parent
        self.is_aster = is_aster

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
        
        # アスタリスクOKの場合、フォルダの投入を許可する
        if os.path.isdir(files[0]) and self.is_aster:
            # フォルダを投入された場合、フォルダ内にvmdもしくはvpdがあれば、受け付ける
            child_file_name_exts = [os.path.splitext(filename) for filename in os.listdir(files[0]) if os.path.isfile(os.path.join(files[0], filename))]

            for ft in self.parent.file_type:
                # 親の許容ファイルパス
                for (child_file_name, child_file_ext) in child_file_name_exts:
                    if child_file_ext[1:].lower() == ft:
                        # 子のファイル拡張子が許容拡張子である場合、アスタリスクを入れて許可する
                        astr_path = "{0}\\*.{1}".format(files[0], ft)
                        self.parent.file_ctrl.SetPath(astr_path)

                        # ファイル変更処理
                        self.parent.on_change_file(wx.FileDirPickerEvent())

                        return True
        
        display_file_type = self.parent.file_type
        if type(self.parent.file_type) == tuple:
            display_file_type = ",".join(self.parent.file_type)

        logger.error("{0}の拡張子が正しくありません。\n入力ファイル拡張子: {1}\n設定可能拡張子: {2}".format(self.parent.title, input_ext, display_file_type), decoration=MLogger.DECORATION_BOX)

        # 許容拡張子外の場合、不許可
        return False
