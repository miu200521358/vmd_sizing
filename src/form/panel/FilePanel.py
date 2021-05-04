# -*- coding: utf-8 -*-
#
import wx
from wx.core import TreeItemId
import wx.lib.newevent
import sys

from form.panel.BasePanel import BasePanel
from form.parts.SizingFileSet import SizingFileSet
from form.parts.ConsoleCtrl import ConsoleCtrl
from form.parts.StatusCtrl import StatusCtrl
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MFormUtils, MFileUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)
TIMER_ID = wx.NewId()


class FilePanel(BasePanel):
    
    def __init__(self, frame: wx.Frame, parent: wx.Notebook, tab_idx: int, file_hitories: dict):
        super().__init__(frame, parent, tab_idx)
        self.file_hitories = file_hitories
        self.timer = None
        self.tree_process_dict = {}

        # ファイルセット
        self.file_set = SizingFileSet(frame, self, self.file_hitories, 1)
        self.sizer.Add(self.file_set.set_sizer, 0, wx.ALL, 0)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 変換前チェックボタン
        self.check_btn_ctrl = wx.Button(self, wx.ID_ANY, u"変換前チェック", wx.DefaultPosition, wx.Size(200, 50), 0)
        self.check_btn_ctrl.SetToolTip(u"入力されたファイル情報で処理可能かどうか、チェックを行います。")
        self.check_btn_ctrl.Bind(wx.EVT_LEFT_DCLICK, self.on_doubleclick)
        self.check_btn_ctrl.Bind(wx.EVT_LEFT_DOWN, self.on_check_click)
        btn_sizer.Add(self.check_btn_ctrl, 0, wx.ALL, 5)

        # 実行ボタン
        self.exec_btn_ctrl = wx.Button(self, wx.ID_ANY, u"VMDサイジング実行", wx.DefaultPosition, wx.Size(200, 50), 0)
        self.exec_btn_ctrl.SetToolTip(u"VMDサイジング処理を実行します。")
        self.exec_btn_ctrl.Bind(wx.EVT_LEFT_DCLICK, self.on_doubleclick)
        self.exec_btn_ctrl.Bind(wx.EVT_LEFT_DOWN, self.on_exec_click)
        btn_sizer.Add(self.exec_btn_ctrl, 0, wx.ALL, 5)

        self.sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.SHAPED, 5)

        # コンソール
        self.console_ctrl = ConsoleCtrl(self, self.frame.logging_level, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(-1, -1), \
                                        wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_NONE | wx.HSCROLL | wx.VSCROLL | wx.WANTS_CHARS)
        self.console_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        self.console_ctrl.Bind(wx.EVT_CHAR, lambda event: MFormUtils.on_select_all(event, self.console_ctrl))
        self.sizer.Add(self.console_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        status_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 進捗ダイアログ
        self.process_dialog = None

        # 進捗ステータス
        self.before_bracket_ctrl = wx.TextCtrl(self, wx.ID_ANY, "(", wx.DefaultPosition, wx.Size(5, -1), wx.TE_READONLY | wx.BORDER_NONE | wx.WANTS_CHARS)
        self.before_bracket_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        status_sizer.Add(self.before_bracket_ctrl, 0, wx.ALIGN_LEFT, 5)

        self.now_process_ctrl = StatusCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(20, -1), wx.TE_READONLY | wx.BORDER_NONE | wx.WANTS_CHARS)
        self.now_process_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        self.now_process_ctrl.SetToolTip(u"現在進んでいるの大まかな処理数です。クリックすると、具体的な処理進捗がダイアログで表示されます。")
        self.now_process_ctrl.Bind(wx.EVT_LEFT_DOWN, self.show_process_dialog)
        status_sizer.Add(self.now_process_ctrl, 0, wx.ALIGN_LEFT, 5)

        self.slash_ctrl = wx.TextCtrl(self, wx.ID_ANY, "/", wx.DefaultPosition, wx.Size(5, -1), wx.TE_READONLY | wx.BORDER_NONE | wx.WANTS_CHARS)
        self.slash_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        status_sizer.Add(self.slash_ctrl, 0, wx.ALIGN_LEFT, 5)

        self.total_process_ctrl = StatusCtrl(self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size(20, -1), wx.TE_READONLY | wx.BORDER_NONE | wx.WANTS_CHARS)
        self.total_process_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        self.total_process_ctrl.SetToolTip(u"全体の大まかな処理数です。クリックすると、具体的な処理進捗がダイアログで表示されます。")
        self.total_process_ctrl.Bind(wx.EVT_LEFT_DOWN, self.show_process_dialog)
        status_sizer.Add(self.total_process_ctrl, 0, wx.ALIGN_LEFT, 5)

        self.after_bracket_ctrl = wx.TextCtrl(self, wx.ID_ANY, ")", wx.DefaultPosition, wx.Size(5, -1), wx.TE_READONLY | wx.BORDER_NONE | wx.WANTS_CHARS)
        self.after_bracket_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        status_sizer.Add(self.after_bracket_ctrl, 0, wx.ALIGN_LEFT, 5)

        # ゲージ
        self.gauge_ctrl = wx.Gauge(self, wx.ID_ANY, 100, wx.DefaultPosition, wx.Size(550, -1), wx.GA_HORIZONTAL)
        self.gauge_ctrl.SetValue(0)
        status_sizer.Add(self.gauge_ctrl, 0, wx.ALL | wx.EXPAND, 5)

        self.sizer.Add(status_sizer, 0, wx.ALL, 0)

        self.fit()
    
    def show_process_dialog(self, event: wx.Event):
        if self.process_dialog:
            # 既にある場合、一旦破棄
            self.process_dialog.Destroy()

        self.process_dialog = ProcessDialog(self.frame, self)
        self.process_dialog.Show()

        event.Skip()

    # マルチプロセス用flush
    def print(self, txt):
        print(txt)
        wx.GetApp().Yield()

    # フォーム無効化
    def disable(self):
        self.file_set.disable()
        self.check_btn_ctrl.Disable()
        self.exec_btn_ctrl.Disable()

    # フォーム無効化
    def enable(self):
        self.file_set.enable()
        self.check_btn_ctrl.Enable()
        self.exec_btn_ctrl.Enable()
    
    def on_doubleclick(self, event: wx.Event):
        self.timer.Stop()
        logger.warning("ダブルクリックされました。", decoration=MLogger.DECORATION_BOX)
        event.Skip(False)
        return False
    
    def on_check_click(self, event: wx.Event):
        self.timer = wx.Timer(self, TIMER_ID)
        self.timer.Start(200)
        self.Bind(wx.EVT_TIMER, self.on_check, id=TIMER_ID)

    # 実行前チェック
    def on_check(self, event: wx.Event):
        self.timer.Stop()
        self.Unbind(wx.EVT_TIMER, id=TIMER_ID)
        # 出力先をファイルパネルのコンソールに変更
        sys.stdout = self.console_ctrl

        if self.check_btn_ctrl.GetLabel() == "読み込み処理停止" and self.frame.load_worker:
            # フォーム無効化
            self.disable()
            # 停止状態でボタン押下時、停止
            self.frame.load_worker.stop()

            # タブ移動可
            self.frame.release_tab()
            # フォーム有効化
            self.frame.enable()
            # ワーカー終了
            self.frame.load_worker = None
            # プログレス非表示
            self.gauge_ctrl.SetValue(0)

            logger.warning("読み込み処理を中断します。", decoration=MLogger.DECORATION_BOX)
            
            event.Skip(False)
        elif not self.frame.load_worker:
            # フォーム無効化
            self.disable()
            # タブ固定
            self.fix_tab()
            # コンソールクリア
            self.console_ctrl.Clear()

            # 履歴保持
            self.save()

            # 一旦読み込み(そのままチェック)
            self.frame.load(event, target_idx=0)
            
            event.Skip()
        else:
            logger.error("まだ処理が実行中です。終了してから再度実行してください。", decoration=MLogger.DECORATION_BOX)
            event.Skip(False)

    def on_exec_click(self, event: wx.Event):
        self.timer = wx.Timer(self, TIMER_ID)
        self.timer.Start(200)
        self.Bind(wx.EVT_TIMER, self.on_exec, id=TIMER_ID)

    # サイジング実行
    def on_exec(self, event: wx.Event):
        if self.timer:
            self.timer.Stop()
            self.Unbind(wx.EVT_TIMER, id=TIMER_ID)
            
        # 出力先をファイルパネルのコンソールに変更
        sys.stdout = self.console_ctrl

        if self.exec_btn_ctrl.GetLabel() == "VMDサイジング停止" and self.frame.worker:
            # フォーム無効化
            self.disable()
            # 停止状態でボタン押下時、停止
            self.frame.worker.stop()

            # タブ移動可
            self.frame.release_tab()
            # フォーム有効化
            self.frame.enable()
            # ワーカー終了
            self.frame.worker = None
            # プログレス非表示
            self.gauge_ctrl.SetValue(0)

            logger.warning("VMDサイジングを中断します。", decoration=MLogger.DECORATION_BOX)
            
            event.Skip(False)
        elif not self.frame.worker:
            # フォーム無効化
            self.disable()
            # タブ固定
            self.fix_tab()
            # コンソールクリア
            self.console_ctrl.Clear()

            # 履歴保持
            self.save()

            # サイジング可否チェックの後に実行
            self.frame.load(event, is_exec=True, target_idx=0)
            
            event.Skip()
        else:
            logger.error("まだ処理が実行中です。終了してから再度実行してください。", decoration=MLogger.DECORATION_BOX)
            event.Skip(False)

    def set_output_vmd_path(self, event, is_force=False):
        self.file_set.set_output_vmd_path(event, is_force)
        # カメラ出力パスも一緒に変更する
        self.frame.camera_panel_ctrl.header_panel.set_output_vmd_path(event, is_force)

    def save(self):

        # 履歴保持
        self.frame.file_panel_ctrl.file_set.save()

        # multiのも全部保持
        for file_set in self.frame.multi_panel_ctrl.file_set_list:
            file_set.save()

        # カメラ履歴保持
        self.frame.camera_panel_ctrl.save()

        # カメラ元モデル保持
        for camera_set in self.frame.camera_panel_ctrl.camera_set_dict.values():
            camera_set.camera_model_file_ctrl.save()

        # JSON出力
        MFileUtils.save_history(self.frame.mydir_path, self.frame.file_hitories)


class ProcessDialog(wx.Dialog):

    def __init__(self, frame: wx.Frame, panel: wx.Panel):
        super().__init__(frame, id=wx.ID_ANY, title="進捗ダイアログ", pos=(-1, -1), size=(700, 450), style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)

        self.frame = frame
        self.panel = panel

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # データツリー
        self.tree_ctrl = wx.TreeCtrl(self, id=wx.ID_ANY, pos=(-1, -1), size=(650, 400), style=wx.TR_ROW_LINES)
        # 初期化
        self.initialize(self.panel.tree_process_dict)

        self.sizer.Add(self.tree_ctrl, 0, wx.ALL, 5)

        self.SetSizer(self.sizer)
        self.sizer.Layout()
        
        # 画面中央に表示
        self.CentreOnScreen()
        
        # 最初は隠しておく
        self.Hide()

    # 初期化
    def initialize(self, tree_dict: dict):
        # Root
        tr_root_ctrl = self.tree_ctrl.AddRoot(text="VMDサイジング")

        # ツリー追加
        self.append_tree(tree_dict, tr_root_ctrl)

    # ツリー追加
    def append_tree(self, item_dict: dict, parent_ctrl: TreeItemId):
        for tk, tv in item_dict.items():
            if isinstance(tv, bool) and tv:
                # 処理が終了している場合、アイコン追加
                display_ctrl = self.tree_ctrl.AppendItem(parent=parent_ctrl, text=("○ {0}".format(tk)))
                self.tree_ctrl.SetItemTextColour(display_ctrl, "BLUE")
            elif isinstance(tv, bool) and not tv:
                # 終了していない場合
                display_ctrl = self.tree_ctrl.AppendItem(parent=parent_ctrl, text=("－ {0}".format(tk)))
                self.tree_ctrl.SetItemTextColour(display_ctrl, "GREY")
            else:
                display_ctrl = self.tree_ctrl.AppendItem(parent=parent_ctrl, text=tk)

            if isinstance(tv, dict):
                # 下位が辞書の場合、ループ再帰
                self.append_tree(tv, display_ctrl)
            
        self.tree_ctrl.ExpandAllChildren(parent_ctrl)

