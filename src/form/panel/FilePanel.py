# -*- coding: utf-8 -*-
#

import os
import re
import wx
import wx.lib.newevent
import winsound
from form.panel.BasePanel import BasePanel
from form.parts.BaseFilePickerCtrl import BaseFilePickerCtrl
from form.parts.HistoryFilePickerCtrl import HistoryFilePickerCtrl
from form.worker.SizingWorkerThread import SizingWorkerThread
from form.worker.LoadWorkerThread import LoadWorkerThread
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MFormUtils, MFileutils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)

# イベント
(SizingThreadEvent, EVT_SIZING_THREAD) = wx.lib.newevent.NewEvent()
(LoadThreadEvent, EVT_LOAD_THREAD) = wx.lib.newevent.NewEvent()


class FilePanel(BasePanel):
    
    def __init__(self, form, parent, tab_idx, file_hitories):
        super().__init__(form, parent, tab_idx)
        self.file_hitories = file_hitories
        
        self.worker = None
        self.load_worker = None

        # VMD/VPDファイルコントロール
        self.motion_vmd_file_ctrl = HistoryFilePickerCtrl(form, self, u"調整対象モーションVMD/VPDファイル", u"調整対象モーションVMD/VPDファイルを開く", ("vmd", "vpd"), wx.FLP_DEFAULT_STYLE, \
                                                          u"調整したいモーションのVMD/VPDパスを指定してください。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。\nファイル名にアスタリスク（*）を使用すると複数件のデータを一度にサイジングできます。", \
                                                          file_model_spacer=8, title_parts_ctrl=None, file_hitories=self.file_hitories["vmd"], history_max=self.file_hitories["max"], \
                                                          is_change_output=True, is_aster=True, is_save=False)
        self.sizer.Add(self.motion_vmd_file_ctrl.sizer, 0, wx.EXPAND, 0)

        # 作成元の代替モデルFLG
        alternative_model_flg_ctrl = wx.CheckBox(self, wx.ID_ANY, u"代替モデル", wx.DefaultPosition, wx.DefaultSize, 0)
        alternative_model_flg_ctrl.SetToolTip(u"チェックを入れると、センターや上半身などの細かいスタンス補正をスキップできます。")

        # 作成元PMXファイルコントロール
        self.org_model_file_ctrl = HistoryFilePickerCtrl(form, self, u"モーション作成元モデルPMXファイル", u"モーション作成元モデルPMXファイルを開く", ("pmx"), wx.FLP_DEFAULT_STYLE, \
                                                         u"モーション作成に使用されたモデルのPMXパスを指定してください。\n精度は落ちますが、類似したサイズ・ボーン構造のモデルでも代用できます。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。", \
                                                         file_model_spacer=2, title_parts_ctrl=alternative_model_flg_ctrl, file_hitories=self.file_hitories["org_pmx"], \
                                                         history_max=self.file_hitories["max"], is_change_output=False, is_aster=False, is_save=False)
        self.sizer.Add(self.org_model_file_ctrl.sizer, 0, wx.EXPAND, 0)

        # 捩り分散追加FLG
        twist_flg_ctrl = wx.CheckBox(self, wx.ID_ANY, u"捩り分散追加", wx.DefaultPosition, wx.DefaultSize, 0)
        twist_flg_ctrl.SetToolTip(u"チェックを入れると、腕捻り等への分散処理を追加できます。")

        # 変換先PMXファイルコントロール
        self.rep_model_file_ctrl = HistoryFilePickerCtrl(form, self, u"モーション変換先モデルPMXファイル", u"モーション変換先モデルPMXファイルを開く", ("pmx"), wx.FLP_DEFAULT_STYLE, \
                                                         u"実際にモーションを読み込ませたいモデルのPMXパスを指定してください。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。", \
                                                         file_model_spacer=1, title_parts_ctrl=twist_flg_ctrl, file_hitories=self.file_hitories["rep_pmx"], history_max=self.file_hitories["max"], \
                                                         is_change_output=True, is_aster=False, is_save=False)
        self.sizer.Add(self.rep_model_file_ctrl.sizer, 0, wx.EXPAND, 0)

        # 出力先VMDファイルコントロール
        self.output_vmd_file_ctrl = BaseFilePickerCtrl(form, self, u"出力VMDファイル", u"出力VMDファイルを開く", ("vmd"), wx.FLP_OVERWRITE_PROMPT | wx.FLP_SAVE | wx.FLP_USE_TEXTCTRL, \
                                                       u"調整結果のVMD出力パスを指定してください。\nVMDファイルと変換先PMXのファイル名に基づいて自動生成されますが、任意のパスに変更することも可能です。", is_aster=False, is_save=True)
        self.sizer.Add(self.output_vmd_file_ctrl.sizer, 0, wx.EXPAND, 0)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 変換前チェックボタン
        self.check_btn_ctrl = wx.Button(self, wx.ID_ANY, u"変換前チェック", wx.DefaultPosition, wx.Size(200, 50), 0)
        self.check_btn_ctrl.SetToolTip(u"入力されたファイル情報で処理可能かどうか、チェックを行います。")
        self.check_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_check)
        btn_sizer.Add(self.check_btn_ctrl, 0, wx.ALL, 5)

        # 実行ボタン
        self.exec_btn_ctrl = wx.Button(self, wx.ID_ANY, u"VMDサイジング実行", wx.DefaultPosition, wx.Size(200, 50), 0)
        self.exec_btn_ctrl.SetToolTip(u"VMDサイジング処理を実行します。")
        self.exec_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_exec)
        btn_sizer.Add(self.exec_btn_ctrl, 0, wx.ALL, 5)

        self.sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.SHAPED, 5)

        # コンソール
        self.console_ctrl = wx.TextCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(-1, -1), \
                                        wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_NONE | wx.HSCROLL | wx.VSCROLL | wx.WANTS_CHARS)
        self.console_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        self.sizer.Add(self.console_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        # ゲージ
        self.gauge_ctrl = wx.Gauge(self, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL)
        self.gauge_ctrl.SetValue(0)
        self.sizer.Add(self.gauge_ctrl, 0, wx.ALL | wx.EXPAND, 5)

        self.form.Bind(EVT_SIZING_THREAD, self.on_exec_result)
        self.form.Bind(EVT_LOAD_THREAD, self.on_load_result)

        self.fit()

    # 実行前チェック
    def on_check(self, event):
        # フォーム無効化
        self.disable()
        # タブ固定
        self.fix_tab()
        # コンソールクリア
        self.console_ctrl.Clear()
        wx.GetApp().Yield()

        # 一旦読み込み
        self.load()

    # 読み込み
    def load(self, is_exec=False):
        # フォーム無効化
        self.disable()
        # タブ固定
        self.fix_tab()
        # コンソールクリア
        self.console_ctrl.Clear()
        wx.GetApp().Yield()

        result = True
        result = self.motion_vmd_file_ctrl.is_valid() and result
        result = self.org_model_file_ctrl.is_valid() and result
        result = self.rep_model_file_ctrl.is_valid() and result
        result = self.output_vmd_file_ctrl.is_valid() and result

        if not result:
            # タブ移動可
            self.release_tab()
            # フォーム有効化
            self.enable()

            return result

        # 読み込み開始
        if self.load_worker:
            logger.error("まだ処理が実行中です。終了してから再度実行してください。", decoration=MLogger.DECORATION_BOX)
        else:
            # 別スレッドで実行
            self.load_worker = LoadWorkerThread(self.form, LoadThreadEvent, self, is_exec)
            self.load_worker.start()
            self.load_worker.stop_event.set()

        return result

    # 読み込み完了処理
    def on_load_result(self, event):
        # タブ移動可
        self.release_tab()
        # フォーム有効化
        self.enable()
        # ワーカー終了
        self.load_worker = None
        # プログレス非表示
        self.gauge_ctrl.SetValue(0)

        if not event.result:
            logger.error("ファイル読み込み処理に失敗したため、処理を中断します。", decoration=MLogger.DECORATION_BOX)
            
            event.Skip()
            return False

        # 両方のPMXが読めて、モーションも読み込めた場合、キーチェック
        not_org_bones = []
        not_org_morphs = []
        not_rep_bones = []
        not_rep_morphs = []

        motion = self.motion_vmd_file_ctrl.data
        org_pmx = self.org_model_file_ctrl.data
        rep_pmx = self.rep_model_file_ctrl.data

        if motion.motion_cnt == 0:
            logger.warning("ボーンモーションデータにキーフレームが登録されていません。", decoration=MLogger.DECORATION_BOX)
            return False

        result = True

        # ボーン
        for k in motion.frames.keys():
            bone_fnos = motion.get_bone_frame_nos(k)
            if len(bone_fnos) > 1 and (motion.frames[k][bone_fnos[0]].position != MVector3D() or motion.frames[k][bone_fnos[0]].rotation != MQuaternion()):
                # キーが存在しており、かつ初期値ではない値が入っている場合、警告対象
                if k not in org_pmx.bones:
                    not_org_bones.append(k)

                if k not in rep_pmx.bones:
                    not_rep_bones.append(k)

            morph_fnos = motion.get_morph_frame_nos(k)
            if len(morph_fnos) > 1 and (motion.frames[k][morph_fnos[0]].ratio != 0):
                # キーが存在しており、かつ初期値ではない値が入っている場合、警告対象
                if k not in org_pmx.morphs:
                    not_org_morphs.append(k)

                if k not in rep_pmx.morphs:
                    not_rep_morphs.append(k)

        if len(not_org_bones) > 0 or len(not_org_morphs) > 0:
            logger.warning("%sにモーションで使用されているボーン・モーフが不足しています。\nボーン: %s\nモーフ: %s", \
                           self.org_model_file_ctrl.title, ",".join(not_org_bones), ",".join(not_org_morphs), decoration=MLogger.DECORATION_BOX)

        if len(not_rep_bones) > 0 or len(not_rep_morphs) > 0:
            logger.warning("%sにモーションで使用されているボーン・モーフが不足しています。\nボーン: %s\nモーフ: %s", \
                           self.rep_model_file_ctrl.title, ",".join(not_rep_bones), ",".join(not_rep_morphs), decoration=MLogger.DECORATION_BOX)
        
        if not result:
            # タブ移動可
            self.release_tab()
            # フォーム有効化
            self.enable()

            event.Skip()
            return False
        
        logger.info("ファイルデータ読み込みが完了しました", decoration=MLogger.DECORATION_BOX, title="OK")

        if event.is_exec:
            # そのまま実行する場合、サイジング実行処理に遷移

            # フォーム無効化
            self.disable()
            # タブ固定
            self.fix_tab()

            # 履歴保持
            self.motion_vmd_file_ctrl.save()
            self.org_model_file_ctrl.save()
            self.rep_model_file_ctrl.save()
            MFileutils.save_history(self.form.mydir_path, self.file_hitories)

            if self.worker:
                logger.error("まだ処理が実行中です。終了してから再度実行してください。", decoration=MLogger.DECORATION_BOX)
            else:
                # 別スレッドで実行
                self.worker = SizingWorkerThread(self.form, SizingThreadEvent)
                self.worker.start()
                self.worker.stop_event.set()

            event.Skip()
            return True
        
        event.Skip()

    # サイジング実行
    def on_exec(self, event):
        # フォーム無効化
        self.disable()
        # タブ固定
        self.fix_tab()
        # コンソールクリア
        self.console_ctrl.Clear()
        wx.GetApp().Yield()

        # サイジング可否チェック
        self.load(is_exec=True)
    
    # スレッド実行結果
    def on_exec_result(self, event):
        # 終了音を鳴らす
        if os.name == "nt":
            # Windows
            try:
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
            except Exception:
                pass

        if not event.result or self.form.is_out_log:
            # 何か失敗している場合かログ明示出力の場合、ログファイル出力

            # ログパス生成
            output_vmd_path = self.output_vmd_file_ctrl.file_ctrl.GetPath()
            output_log_path = re.sub(r'\.vmd$', '.log', output_vmd_path)

            with open(output_log_path, mode='w') as f:
                f.write(self.console_ctrl.GetValue())

        # ワーカー終了
        self.worker = None
        # タブ移動可
        self.release_tab()
        # フォーム有効化
        self.enable()
        # プログレス非表示
        self.gauge_ctrl.SetValue(0)
    
    # フォーム無効化
    def disable(self):
        self.motion_vmd_file_ctrl.disable()
        self.org_model_file_ctrl.disable()
        self.rep_model_file_ctrl.disable()
        self.output_vmd_file_ctrl.disable()
        self.check_btn_ctrl.Disable()
        self.exec_btn_ctrl.Disable()

    # フォーム無効化
    def enable(self):
        self.motion_vmd_file_ctrl.enable()
        self.org_model_file_ctrl.enable()
        self.rep_model_file_ctrl.enable()
        self.output_vmd_file_ctrl.enable()
        self.check_btn_ctrl.Enable()
        self.exec_btn_ctrl.Enable()



