# -*- coding: utf-8 -*-
#
from datetime import datetime
import glob
import os
import re
import wx
import wx.lib.newevent

from form.parts.BaseFilePickerCtrl import BaseFilePickerCtrl
from form.parts.HistoryFilePickerCtrl import HistoryFilePickerCtrl
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MFormUtils, MFileUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class SizingFileSet():

    def __init__(self, frame: wx.Frame, panel: wx.Panel, file_hitories: dict, set_no):
        self.file_hitories = file_hitories
        self.panel = panel
        self.set_no = set_no

        if self.set_no == 1:
            # ファイルパネルのはそのまま追加
            self.set_sizer = wx.BoxSizer(wx.VERTICAL)
        else:
            self.set_sizer = wx.StaticBoxSizer(wx.StaticBox(self.panel, wx.ID_ANY, "【No.{0}】".format(set_no)), orient=wx.VERTICAL)

        able_aster_toottip = "ファイル名にアスタリスク（*）を使用すると複数件のデータを一度にサイジングできます。" if self.set_no == 1 else "一括指定はできません。"
        # VMD/VPDファイルコントロール
        self.motion_vmd_file_ctrl = HistoryFilePickerCtrl(frame, panel, u"調整対象モーションVMD/VPDファイル", u"調整対象モーションVMD/VPDファイルを開く", ("vmd", "vpd"), wx.FLP_DEFAULT_STYLE, \
                                                          u"調整したいモーションのVMD/VPDパスを指定してください。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。\n{0}".format(able_aster_toottip), \
                                                          file_model_spacer=8, title_parts_ctrl=None, file_histories_key="vmd", is_change_output=True, is_aster=True, is_save=False, set_no=set_no)
        self.set_sizer.Add(self.motion_vmd_file_ctrl.sizer, 1, wx.EXPAND, 0)

        # 作成元の代替モデルFLG
        substitute_model_flg_ctrl = wx.CheckBox(panel, wx.ID_ANY, u"代替モデル", wx.DefaultPosition, wx.DefaultSize, 0)
        substitute_model_flg_ctrl.SetToolTip(u"チェックを入れると、センターや上半身などの細かいスタンス補正をスキップできます。")
        substitute_model_flg_ctrl.Bind(wx.EVT_CHECKBOX, self.set_output_vmd_path)

        # 作成元PMXファイルコントロール
        self.org_model_file_ctrl = HistoryFilePickerCtrl(frame, panel, u"モーション作成元モデルPMXファイル", u"モーション作成元モデルPMXファイルを開く", ("pmx"), wx.FLP_DEFAULT_STYLE, \
                                                         u"モーション作成に使用されたモデルのPMXパスを指定してください。\n精度は落ちますが、類似したサイズ・ボーン構造のモデルでも代用できます。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。", \
                                                         file_model_spacer=2, title_parts_ctrl=substitute_model_flg_ctrl, file_histories_key="org_pmx", is_change_output=False, is_aster=False, \
                                                         is_save=False, set_no=set_no)
        self.set_sizer.Add(self.org_model_file_ctrl.sizer, 1, wx.EXPAND, 0)

        # 捩り分散追加FLG
        twist_flg_ctrl = wx.CheckBox(panel, wx.ID_ANY, u"捩り分散追加", wx.DefaultPosition, wx.DefaultSize, 0)
        twist_flg_ctrl.SetToolTip(u"チェックを入れると、腕捻り等への分散処理を追加できます。")
        twist_flg_ctrl.Bind(wx.EVT_CHECKBOX, self.set_output_vmd_path)

        # 変換先PMXファイルコントロール
        self.rep_model_file_ctrl = HistoryFilePickerCtrl(frame, panel, u"モーション変換先モデルPMXファイル", u"モーション変換先モデルPMXファイルを開く", ("pmx"), wx.FLP_DEFAULT_STYLE, \
                                                         u"実際にモーションを読み込ませたいモデルのPMXパスを指定してください。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。", \
                                                         file_model_spacer=1, title_parts_ctrl=twist_flg_ctrl, file_histories_key="rep_pmx", is_change_output=True, is_aster=False, \
                                                         is_save=False, set_no=set_no)
        self.set_sizer.Add(self.rep_model_file_ctrl.sizer, 1, wx.EXPAND, 0)

        # 出力先VMDファイルコントロール
        self.output_vmd_file_ctrl = BaseFilePickerCtrl(frame, panel, u"出力VMDファイル", u"出力VMDファイルを開く", ("vmd"), wx.FLP_OVERWRITE_PROMPT | wx.FLP_SAVE | wx.FLP_USE_TEXTCTRL, \
                                                       u"調整結果のVMD出力パスを指定してください。\nVMDファイルと変換先PMXのファイル名に基づいて自動生成されますが、任意のパスに変更することも可能です。", \
                                                       is_aster=False, is_save=True, set_no=set_no)
        self.set_sizer.Add(self.output_vmd_file_ctrl.sizer, 1, wx.EXPAND, 0)

    def save(self):
        self.motion_vmd_file_ctrl.save()
        self.org_model_file_ctrl.save()
        self.rep_model_file_ctrl.save()

    # フォーム無効化
    def disable(self):
        self.motion_vmd_file_ctrl.disable()
        self.org_model_file_ctrl.disable()
        self.rep_model_file_ctrl.disable()
        self.output_vmd_file_ctrl.disable()

    # フォーム無効化
    def enable(self):
        self.motion_vmd_file_ctrl.enable()
        self.org_model_file_ctrl.enable()
        self.rep_model_file_ctrl.enable()
        self.output_vmd_file_ctrl.enable()

    # ファイル読み込み前のチェック
    def is_valid(self):
        result = True
        if self.set_no == 1:
            # 1番目は必ず調べる
            result = self.motion_vmd_file_ctrl.is_valid() and result
            result = self.org_model_file_ctrl.is_valid() and result
            result = self.rep_model_file_ctrl.is_valid() and result
            result = self.output_vmd_file_ctrl.is_valid() and result
        else:
            # 2番目以降は、ファイルが揃ってたら調べる
            if self.motion_vmd_file_ctrl.is_set_path() or self.org_model_file_ctrl.is_set_path() or \
               self.rep_model_file_ctrl.is_set_path() or self.output_vmd_file_ctrl.is_set_path():
                result = self.motion_vmd_file_ctrl.is_valid() and result
                result = self.org_model_file_ctrl.is_valid() and result
                result = self.rep_model_file_ctrl.is_valid() and result
                result = self.output_vmd_file_ctrl.is_valid() and result

        return result

    # 入力後の入力可否チェック
    def is_loaded_valid(self):
        if self.set_no == 0:
            # CSVとかのファイルは番号出力なし
            display_set_no = ""
        else:
            display_set_no = "{0}番目の".format(self.set_no)
        
        # 両方のPMXが読めて、モーションも読み込めた場合、キーチェック
        not_org_bones = []
        not_org_morphs = []
        not_rep_bones = []
        not_rep_morphs = []

        motion = self.motion_vmd_file_ctrl.data
        org_pmx = self.org_model_file_ctrl.data
        rep_pmx = self.rep_model_file_ctrl.data

        if not motion or not org_pmx or not rep_pmx:
            # どれか読めてなければそのまま終了
            return True

        if motion.motion_cnt == 0:
            logger.warning("%sボーンモーションデータにキーフレームが登録されていません。", display_set_no, decoration=MLogger.DECORATION_BOX)
            return True

        result = True

        # ボーン
        for k in motion.bones.keys():
            bone_fnos = motion.get_bone_fnos(k)
            if len(bone_fnos) > 1 and (motion.bones[k][bone_fnos[0]].position != MVector3D() or motion.bones[k][bone_fnos[0]].rotation != MQuaternion()):
                # キーが存在しており、かつ初期値ではない値が入っている場合、警告対象
                if k not in org_pmx.bones:
                    not_org_bones.append(k)

                if k not in rep_pmx.bones:
                    not_rep_bones.append(k)

            morph_fnos = motion.get_morph_fnos(k)
            if len(morph_fnos) > 1 and (motion.bones[k][morph_fnos[0]].ratio != 0):
                # キーが存在しており、かつ初期値ではない値が入っている場合、警告対象
                if k not in org_pmx.morphs:
                    not_org_morphs.append(k)

                if k not in rep_pmx.morphs:
                    not_rep_morphs.append(k)

        if len(not_org_bones) > 0 or len(not_org_morphs) > 0:
            logger.warning("%s%sにモーションで使用されているボーン・モーフが不足しています。\nボーン: %s\nモーフ: %s", \
                           display_set_no, self.org_model_file_ctrl.title, ",".join(not_org_bones), ",".join(not_org_morphs), decoration=MLogger.DECORATION_BOX)

        if len(not_rep_bones) > 0 or len(not_rep_morphs) > 0:
            logger.warning("%s%sにモーションで使用されているボーン・モーフが不足しています。\nボーン: %s\nモーフ: %s", \
                           display_set_no, self.rep_model_file_ctrl.title, ",".join(not_rep_bones), ",".join(not_rep_morphs), decoration=MLogger.DECORATION_BOX)
        
        return result

    def is_loaded(self):
        result = True
        if self.is_valid():
            result = self.motion_vmd_file_ctrl.data and result
            result = self.org_model_file_ctrl.data and result
            result = self.rep_model_file_ctrl.data and result
        else:
            result = False
        
        return result

    def load(self):
        result = True
        try:
            result = self.motion_vmd_file_ctrl.load() and result
            result = self.org_model_file_ctrl.load() and result
            result = self.rep_model_file_ctrl.load() and result
        except Exception:
            result = False
        
        return result

    # VMD出力ファイルパス生成
    def set_output_vmd_path(self, is_force=False):
        output_vmd_path = MFileUtils.get_output_vmd_path(
            self.motion_vmd_file_ctrl.file_ctrl.GetPath(),
            self.rep_model_file_ctrl.file_ctrl.GetPath(),
            self.org_model_file_ctrl.title_parts_ctrl.GetValue(),
            self.rep_model_file_ctrl.title_parts_ctrl.GetValue(),
            self.output_vmd_file_ctrl.file_ctrl.GetPath(), is_force)

        self.output_vmd_file_ctrl.file_ctrl.SetPath(output_vmd_path)

        if len(output_vmd_path) >= 255 and os.name == "nt":
            logger.error("生成予定のファイルパスがWindowsの制限を超えています。\n生成予定パス: {0}".format(output_vmd_path), decoration=MLogger.DECORATION_BOX)
