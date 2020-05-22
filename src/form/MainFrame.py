# -*- coding: utf-8 -*-
#
import os
import sys
import wx

from form.panel.FilePanel import FilePanel
from form.panel.MorphPanel import MorphPanel
from form.panel.MultiPanel import MultiPanel
from form.panel.ArmPanel import ArmPanel
from form.panel.CameraPanel import CameraPanel
from form.panel.BlendPanel import BlendPanel
from form.panel.CsvPanel import CsvPanel
from form.panel.VmdPanel import VmdPanel
from form.panel.BezierPanel import BezierPanel
from form.panel.SmoothPanel import SmoothPanel
from form.worker.SizingWorkerThread import SizingWorkerThread
from form.worker.LoadWorkerThread import LoadWorkerThread
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MFormUtils, MFileUtils # noqa
from utils.MLogger import MLogger # noqa

if os.name == "nt":
    import winsound     # Windows版のみインポート

logger = MLogger(__name__)


# イベント
(SizingThreadEvent, EVT_SIZING_THREAD) = wx.lib.newevent.NewEvent()
(LoadThreadEvent, EVT_LOAD_THREAD) = wx.lib.newevent.NewEvent()


class MainFrame(wx.Frame):

    def __init__(self, parent, mydir_path: str, version_name: str, logging_level: int, is_out_log: bool):
        self.version_name = version_name
        self.logging_level = logging_level
        self.is_out_log = is_out_log
        self.mydir_path = mydir_path
        self.elapsed_time = 0
        self.popuped_finger_warning = False
        
        self.worker = None
        self.load_worker = None

        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"VMDサイジング ローカル版 {0}".format(self.version_name), \
                          pos=wx.DefaultPosition, size=wx.Size(600, 650), style=wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL)

        # ファイル履歴読み込み
        self.file_hitories = MFileUtils.read_history(self.mydir_path)

        # ---------------------------------------------

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        bSizer1 = wx.BoxSizer(wx.VERTICAL)

        self.note_ctrl = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
        if self.logging_level == MLogger.FULL or self.logging_level == MLogger.DEBUG_FULL:
            # フルデータの場合
            self.note_ctrl.SetBackgroundColour("RED")
        elif self.logging_level == MLogger.DEBUG:
            # テスト（デバッグ版）の場合
            self.note_ctrl.SetBackgroundColour("CORAL")
        elif self.logging_level == MLogger.TIMER:
            # 時間計測の場合
            self.note_ctrl.SetBackgroundColour("YELLOW")
        elif is_out_log:
            # ログありの場合、色変え
            self.note_ctrl.SetBackgroundColour("AQUAMARINE")
        else:
            self.note_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNSHADOW))

        # ---------------------------------------------

        # ファイルタブ
        self.file_panel_ctrl = FilePanel(self, self.note_ctrl, 0, self.file_hitories)
        self.note_ctrl.AddPage(self.file_panel_ctrl, u"ファイル", True)

        # 複数タブ
        self.multi_panel_ctrl = MultiPanel(self, self.note_ctrl, 1, self.file_hitories)
        self.note_ctrl.AddPage(self.multi_panel_ctrl, u"複数", False)

        # モーフタブ
        self.morph_panel_ctrl = MorphPanel(self, self.note_ctrl, 2)
        self.note_ctrl.AddPage(self.morph_panel_ctrl, u"モーフ", False)

        # 腕タブ
        self.arm_panel_ctrl = ArmPanel(self, self.note_ctrl, 3)
        self.note_ctrl.AddPage(self.arm_panel_ctrl, u"腕", False)

        # カメラタブ
        self.camera_panel_ctrl = CameraPanel(self, self.note_ctrl, 4)
        self.note_ctrl.AddPage(self.camera_panel_ctrl, u"カメラ", False)

        # スムーズタブ
        self.smooth_panel_ctrl = SmoothPanel(self, self.note_ctrl, 5)
        self.note_ctrl.AddPage(self.smooth_panel_ctrl, u"スムーズ", False)

        # ブレンドタブ
        self.blend_panel_ctrl = BlendPanel(self, self.note_ctrl, 6)
        self.note_ctrl.AddPage(self.blend_panel_ctrl, u"ブレンド", False)

        # CSVタブ
        self.csv_panel_ctrl = CsvPanel(self, self.note_ctrl, 7)
        self.note_ctrl.AddPage(self.csv_panel_ctrl, u"CSV", False)

        # VMDタブ
        self.vmd_panel_ctrl = VmdPanel(self, self.note_ctrl, 8)
        self.note_ctrl.AddPage(self.vmd_panel_ctrl, u"VMD", False)
        
        # 補間タブ
        self.bezier_panel_ctrl = BezierPanel(self, self.note_ctrl, 9)
        self.note_ctrl.AddPage(self.bezier_panel_ctrl, u"補間", False)
        
        # ---------------------------------------------

        # タブ押下時の処理
        self.note_ctrl.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.on_tab_change)

        # 待機中の処理
        self.Bind(wx.EVT_IDLE, self.on_idle)

        # ---------------------------------------------

        bSizer1.Add(self.note_ctrl, 1, wx.EXPAND, 5)

        # デフォルトの出力先はファイルタブのコンソール
        sys.stdout = self.file_panel_ctrl.console_ctrl

        # イベントバインド
        self.Bind(EVT_SIZING_THREAD, self.on_exec_result)
        self.Bind(EVT_LOAD_THREAD, self.on_load_result)

        self.SetSizer(bSizer1)
        self.Layout()

        self.Centre(wx.BOTH)
    
    def on_idle(self, event: wx.Event):
        if self.worker or self.load_worker:
            self.file_panel_ctrl.gauge_ctrl.Pulse()
        elif self.csv_panel_ctrl.convert_csv_worker:
            self.csv_panel_ctrl.gauge_ctrl.Pulse()
        elif self.vmd_panel_ctrl.convert_vmd_worker:
            self.vmd_panel_ctrl.gauge_ctrl.Pulse()

    def on_tab_change(self, event: wx.Event):
        if self.file_panel_ctrl.is_fix_tab:
            self.note_ctrl.ChangeSelection(self.file_panel_ctrl.tab_idx)
            event.Skip()
            return

        elif self.morph_panel_ctrl.is_fix_tab:
            # モーフタブの固定が指定されている場合、固定はファイルタブ
            self.note_ctrl.ChangeSelection(self.file_panel_ctrl.tab_idx)
            event.Skip()
            return

        elif self.arm_panel_ctrl.is_fix_tab:
            # 腕タブの固定が指定されている場合、固定はファイルタブ
            self.note_ctrl.ChangeSelection(self.file_panel_ctrl.tab_idx)
            event.Skip()
            return

        elif self.smooth_panel_ctrl.is_fix_tab:
            self.note_ctrl.ChangeSelection(self.smooth_panel_ctrl.tab_idx)
            event.Skip()
            return

        elif self.blend_panel_ctrl.is_fix_tab:
            self.note_ctrl.ChangeSelection(self.blend_panel_ctrl.tab_idx)
            event.Skip()
            return

        elif self.csv_panel_ctrl.is_fix_tab:
            self.note_ctrl.ChangeSelection(self.csv_panel_ctrl.tab_idx)
            event.Skip()
            return

        elif self.vmd_panel_ctrl.is_fix_tab:
            self.note_ctrl.ChangeSelection(self.vmd_panel_ctrl.tab_idx)
            event.Skip()
            return

        if self.note_ctrl.GetSelection() == self.morph_panel_ctrl.tab_idx:
            # コンソールクリア
            self.file_panel_ctrl.console_ctrl.Clear()
            wx.GetApp().Yield()

            # 一旦ファイルタブに固定
            self.note_ctrl.SetSelection(self.file_panel_ctrl.tab_idx)
            self.morph_panel_ctrl.fix_tab()

            logger.info("モーフタブ表示準備開始\nファイル読み込み処理を実行します。少しお待ちください....", decoration=MLogger.DECORATION_BOX)

            # 読み込み処理実行
            self.load(is_morph=True)

        if self.note_ctrl.GetSelection() == self.arm_panel_ctrl.tab_idx:
            # コンソールクリア
            self.file_panel_ctrl.console_ctrl.Clear()
            wx.GetApp().Yield()

            # 一旦ファイルタブに固定
            self.note_ctrl.SetSelection(self.file_panel_ctrl.tab_idx)
            self.arm_panel_ctrl.fix_tab()

            logger.info("腕タブ表示準備開始\nファイル読み込み処理を実行します。少しお待ちください....", decoration=MLogger.DECORATION_BOX)

            # 読み込み処理実行
            self.load(is_arm=True)
                
        if self.note_ctrl.GetSelection() == self.camera_panel_ctrl.tab_idx:
            # カメラタブを開く場合、カメラタブ初期化処理実行
            self.note_ctrl.ChangeSelection(self.camera_panel_ctrl.tab_idx)
            self.camera_panel_ctrl.initialize(event)

    # タブ移動可
    def release_tab(self):
        self.file_panel_ctrl.release_tab()
        self.morph_panel_ctrl.release_tab()
        self.arm_panel_ctrl.release_tab()

    # フォーム入力可
    def enable(self):
        self.file_panel_ctrl.enable()
        # self.morph_panel_ctrl.enable()
    
    # ファイルセットの入力可否チェック
    def is_valid(self):
        result = True
        result = self.file_panel_ctrl.file_set.is_valid() and result

        # multiはあるだけ調べる
        for file_set in self.multi_panel_ctrl.file_set_list:
            result = file_set.is_valid() and result

        return result
    
    # 入力後の入力可否チェック
    def is_loaded_valid(self):
        result = True
        result = self.file_panel_ctrl.file_set.is_loaded_valid() and result

        # multiはあるだけ調べる
        for file_set in self.multi_panel_ctrl.file_set_list:
            result = file_set.is_loaded_valid() and result

        return result
    
    def show_worked_time(self):
        # 経過秒数を時分秒に変換
        td_m, td_s = divmod(self.elapsed_time, 60)

        if td_m == 0:
            worked_time = "{0:02d}秒".format(int(td_s))
        else:
            worked_time = "{0:02d}分{1:02d}秒".format(int(td_m), int(td_s))

        return worked_time

    # 読み込み
    def load(self, is_exec=False, is_morph=False, is_arm=False):
        # フォーム無効化
        self.file_panel_ctrl.disable()
        # タブ固定
        self.file_panel_ctrl.fix_tab()

        self.elapsed_time = 0
        result = True
        result = self.is_valid() and result

        if not result:
            if is_morph or is_arm:
                tab_name = "モーフ" if is_morph else "腕"
                # 読み込み出来なかったらエラー
                logger.error("「ファイル」タブで以下のいずれかのファイルパスが指定されていないため、「{tab_name}」タブが開けません。".format(tab_name=tab_name) \
                             + "\n・調整対象VMDファイル" \
                             + "\n・作成元モデルPMXファイル" \
                             + "\n・変換先モデルPMXファイル" \
                             + "\n既に指定済みの場合、現在読み込み中の可能性があります。" \
                             + "\n特に長いVMDは読み込みに時間がかかります。" \
                             + "\n調整に必要な３ファイルすべてを指定して、" \
                             + "\n「■読み込み成功」のログが出てから、「{tab_name}」タブを開いてください。".format(tab_name=tab_name), decoration=MLogger.DECORATION_BOX)

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
            self.load_worker = LoadWorkerThread(self, LoadThreadEvent, is_exec, is_morph, is_arm)
            self.load_worker.start()
            self.load_worker.stop_event.set()

        return result

    # 読み込み完了処理
    def on_load_result(self, event: wx.Event):
        self.elapsed_time = event.elapsed_time
        
        # タブ移動可
        self.release_tab()
        # フォーム有効化
        self.enable()
        # ワーカー終了
        self.load_worker.join()
        self.load_worker = None
        # プログレス非表示
        self.file_panel_ctrl.gauge_ctrl.SetValue(0)

        if not event.result:
            logger.error("ファイル読み込み処理に失敗したため、処理を中断します。", decoration=MLogger.DECORATION_BOX)
            
            event.Skip()
            return False

        result = self.is_loaded_valid()

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

            # 念のため出力ファイルパス自動生成（空の場合設定）
            self.file_panel_ctrl.file_set.set_output_vmd_path()

            # multiのも出力ファイルパス自動生成（空の場合設定）
            for file_set in self.multi_panel_ctrl.file_set_list:
                file_set.set_output_vmd_path()

            # フォーム無効化
            self.file_panel_ctrl.disable()
            # タブ固定
            self.file_panel_ctrl.fix_tab()

            if self.worker:
                logger.error("まだ処理が実行中です。終了してから再度実行してください。", decoration=MLogger.DECORATION_BOX)
            else:
                # 別スレッドで実行
                self.worker = SizingWorkerThread(self, SizingThreadEvent, self.is_out_log)
                self.worker.start()
                self.worker.stop_event.set()

        elif event.is_morph:
            # モーフタブを開く場合、モーフタブ初期化処理実行
            self.note_ctrl.ChangeSelection(self.morph_panel_ctrl.tab_idx)
            self.morph_panel_ctrl.initialize(event)

        elif event.is_arm:
            # 腕タブを開く場合、腕タブ初期化処理実行
            self.note_ctrl.ChangeSelection(self.arm_panel_ctrl.tab_idx)
            self.arm_panel_ctrl.initialize(event)

        else:
            # 終了音を鳴らす
            self.sound_finish()

            logger.info("\n処理時間: %s", self.show_worked_time())
        
            event.Skip()
            return True

    # スレッド実行結果
    def on_exec_result(self, event: wx.Event):
        self.elapsed_time += event.elapsed_time
        logger.info("\n処理時間: %s", self.show_worked_time())

        # ファイルタブのコンソール
        sys.stdout = self.file_panel_ctrl.console_ctrl

        # 終了音を鳴らす
        self.sound_finish()

        # ワーカー終了
        self.worker.join()
        self.worker = None
        # タブ移動可
        self.release_tab()
        # フォーム有効化
        self.enable()
        # プログレス非表示
        self.file_panel_ctrl.gauge_ctrl.SetValue(0)

    def sound_finish(self):
        # 終了音を鳴らす
        if os.name == "nt":
            # Windows
            try:
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
            except Exception:
                pass

    def on_wheel_spin_ctrl(self, event: wx.Event, inc=0.1):
        # スピンコントロール変更時
        if event.GetWheelRotation() > 0:
            event.GetEventObject().SetValue(event.GetEventObject().GetValue() + inc)
        else:
            event.GetEventObject().SetValue(event.GetEventObject().GetValue() - inc)

    def on_popup_finger_warning(self, event: wx.Event):
        if not self.popuped_finger_warning:
            dialog = wx.MessageDialog(self, "複数人数モーションで指位置合わせがONになっています。\n指の数だけ組み合わせが膨大になり時間がかかりますが、" \
                                      + "その割に余計な指に反応して綺麗になりません。よろしいですか？", style=wx.OK | wx.ICON_WARNING)
            dialog.ShowModal()
            dialog.Destroy()
            self.popuped_finger_warning = True
