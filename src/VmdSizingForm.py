# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Oct 26 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import wx.lib.scrolledpanel
import logging
import sys
import os.path
import threading

import wrapperutils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


###########################################################################
## Class Frame
###########################################################################

class MorphFrame(wx.Frame):
	def __init__( self, parent, vmd, org_pmx, rep_pmx):
		self.vmd = vmd
		self.org_pmx = org_pmx
		self.rep_pmx = rep_pmx
		self.parent = parent

		wx.Frame.__init__(self, parent, id = wx.ID_ANY, title = u"モーフ置換定義", size = wx.Size( 400, 500 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL)

		# ルートパネル
		rootPanel = wx.Panel(self, wx.ID_ANY, size = wx.Size( 400, 500 ))

		self.vmd_morphs = [""]
		for mk in org_pmx.morphs.keys():
			if mk in self.vmd.morphs.keys() and (len(self.vmd.morphs[mk]) > 1 or self.vmd.morphs[mk][0].ratio != 0):
				# モーションモーフにキーがあって、かつ初期値が0以外の場合か複数件ある場合
				if mk in self.rep_pmx.morphs.keys():
					# 置換先にある場合は○
					self.vmd_morphs.append("○" + mk)
				else:
					self.vmd_morphs.append("▲" + mk)

		# 元モデルにないモーフ追加
		for vmk in self.vmd.morphs.keys():
			if vmk not in org_pmx.morphs.keys() and (len(self.vmd.morphs[vmk]) > 1 or self.vmd.morphs[vmk][0].ratio != 0):
				if mk in self.rep_pmx.morphs.keys():
					# 置換先にある場合は○
					self.vmd_morphs.append("○" + vmk)
				else:
					self.vmd_morphs.append("▲" + vmk)

		self.rep_morphs = list(self.rep_pmx.morphs.keys())
		self.rep_morphs.insert(0, "")

		# 選択部分
		self.bSizerMorph = wx.BoxSizer( wx.VERTICAL )

		self.morphPanel = wx.lib.scrolledpanel.ScrolledPanel(rootPanel, wx.ID_ANY, size = wx.Size( 400, 380 ) )
		self.morphPanel.SetupScrolling(scroll_x=False, scroll_y=False)
		
		gsize = 2 if len(self.parent.vmd_choice_values) == 0 else len(self.parent.vmd_choice_values) + 1
		# logger.info("gsize: %s", gsize)
		gSizer1 = wx.FlexGridSizer( gsize, 3, 0, 0 )

		gSizer1.Add( wx.StaticText( self.morphPanel, wx.ID_ANY, u"モーションモーフ", wx.DefaultPosition, wx.DefaultSize, 0 ), 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.ALIGN_CENTER|wx.EXPAND, 10 )
		gSizer1.Add( wx.StaticText( self.morphPanel, wx.ID_ANY, u" ", wx.DefaultPosition, wx.DefaultSize, 0 ), 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.ALIGN_CENTER|wx.EXPAND, 10 )
		gSizer1.Add( wx.StaticText( self.morphPanel, wx.ID_ANY, u"置換後モーフ", wx.DefaultPosition, wx.DefaultSize, 0 ), 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.ALIGN_CENTER|wx.EXPAND, 10 )

		self.vmd_choices = []
		self.arrows = []
		self.rep_choices = []

		# モーフ行追加
		if len(self.parent.vmd_choice_values) == 0:
			# 既存がない場合、1件だけ生成
			self.AddMorphLine(None, None, gSizer1)
		else:
			for vcv, rcv in zip(self.parent.vmd_choice_values, self.parent.rep_choice_values):
				self.AddMorphLine(vcv, rcv, gSizer1)

		self.morphPanel.SetSizer( self.bSizerMorph )

		# ボタン部分
		buttonPanel = wx.Panel( rootPanel, wx.ID_ANY )

		bSizer4 = wx.BoxSizer( wx.VERTICAL )
		gSizer2 = wx.GridSizer( 0, 3, 50, 50 )

		self.m_btnAddLine = wx.Button( buttonPanel, wx.ID_ANY, u"行追加", wx.DefaultPosition, wx.Size( 90,30 ), 0 )
		gSizer2.Add( self.m_btnAddLine, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_btnOk = wx.Button( buttonPanel, wx.ID_ANY, u"保存", wx.DefaultPosition, wx.Size( 90,30 ), 0 )
		gSizer2.Add( self.m_btnOk, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_btnCancel = wx.Button( buttonPanel, wx.ID_ANY, u"キャンセル", wx.DefaultPosition, wx.Size( 90,30 ), 0 )
		gSizer2.Add( self.m_btnCancel, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL, 5 )

		bSizer4.Add( gSizer2, 0, wx.ALIGN_CENTER|wx.SHAPED, 5 )

		buttonPanel.SetSizer(bSizer4)

		rootLayout = wx.BoxSizer(wx.VERTICAL)
		rootLayout.Add(self.morphPanel, 0, wx.ALL|wx.EXPAND, 10)
		rootLayout.Add(buttonPanel, 0, wx.ALL|wx.EXPAND, 10)
		
		rootPanel.SetSizer(rootLayout)
		self.Layout()

		self.m_btnAddLine.Bind( wx.EVT_BUTTON, self.OnAddLine )
		self.m_btnOk.Bind( wx.EVT_BUTTON, self.OnOk )
		self.m_btnCancel.Bind( wx.EVT_BUTTON, self.OnCancel )

		# ウィンドウクローズイベント
		self.Bind( wx.EVT_CLOSE, self.OnClose )

	
	def AddMorphLine(self, vcv=None, rcv=None, sizer=None):
		# logger.info("vcv: %s, rcv=%s", vcv, rcv)

		# モーフ選択行追加
		self.vmd_choices.append(wx.Choice(self.morphPanel, id=wx.ID_ANY, choices=self.vmd_morphs))
		self.arrows.append(wx.StaticText( self.morphPanel, wx.ID_ANY, u"→", wx.DefaultPosition, wx.DefaultSize, 0 ))
		# self.arrows[-1].Wrap( -1 )
		self.rep_choices.append(wx.Choice(self.morphPanel, id=wx.ID_ANY, choices=self.rep_morphs))

		# 既存選択肢を再設定
		if vcv and rcv:
			self.vmd_choices[-1].SetSelection(self.vmd_choices[-1].FindString(vcv))
			self.rep_choices[-1].SetSelection(self.rep_choices[-1].FindString(rcv))

		if sizer == None:
			sizer = wx.FlexGridSizer( 0, 3, 0, 0 )

		# 最終行の値を設定
		sizer.Add( self.vmd_choices[-1], 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER|wx.EXPAND, 10 )
		sizer.Add( self.arrows[-1], 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER|wx.EXPAND, 10 )
		sizer.Add( self.rep_choices[-1], 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER|wx.EXPAND, 10 )

		sizer.SetFlexibleDirection( wx.HORIZONTAL )
		# sizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_ALL )

		self.bSizerMorph.Add( sizer, 0, wx.TOP|wx.ALIGN_CENTER|wx.EXPAND, 10 )
		self.bSizerMorph.Layout()
		self.Layout()

	def OnAddLine(self, event):
		# 行追加
		self.AddMorphLine()

	def OnClose(self, event):
		self.Hide()
	
	def OnCancel(self, event):
		self.Hide()
	
	def OnOk(self, event):
		# 一旦初期化
		self.parent.vmd_choice_values = []
		self.parent.rep_choice_values = []

		# モーフ置換文字列リスト生成
		morphTxt = ""
		for vc, rc in zip(self.vmd_choices, self.rep_choices):
			vc_idx = vc.GetSelection()
			rc_idx = rc.GetSelection()
			if vc_idx >= 0 and rc_idx >= 0 and len(vc.GetString(vc_idx)) > 0 and len(rc.GetString(rc_idx)) > 0:
				self.parent.vmd_choice_values.append(vc.GetString(vc_idx)[1:])
				self.parent.rep_choice_values.append(rc.GetString(rc_idx))

				morphTxt += vc.GetString(vc_idx)[1:] +" → "+ rc.GetString(rc_idx) + " / "
		
		# 親にモーフ置換定義文字列表示
		self.parent.m_txtMorph.SetValue(morphTxt)

		self.Hide()
	
	def OnInit(self, parent):
		pass


class Frame ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"VMDサイジング ローカル版 ver2.02", pos = wx.DefaultPosition, size = wx.Size( 651,600 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_3DLIGHT ) )

		# モーフ置換配列
		self.vmd_choice_values = []
		self.rep_choice_values = []

		# ファイル解析情報
		self.vmd = None
		self.org_pmx = None
		self.rep_pmx = None

		bSizer3 = wx.BoxSizer( wx.VERTICAL )

		bSizer4 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"調整対象VMDファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )

		bSizer4.Add( self.m_staticText1, 0, wx.ALL, 5 )

		self.m_fileVmd = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, u"調整対象VMDファイルを開く", u"*.vmd", wx.DefaultPosition, wx.Size( -1,-1 ), wx.FLP_DEFAULT_STYLE )
		bSizer4.Add( self.m_fileVmd, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText2 = wx.StaticText( self, wx.ID_ANY, u"トレース元モデルPMXファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText2.Wrap( -1 )

		bSizer4.Add( self.m_staticText2, 0, wx.ALL, 5 )

		self.m_fileOrgPmx = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, u"トレース元モデルPMXファイルを開く", u"*.pmx", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		bSizer4.Add( self.m_fileOrgPmx, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, u"トレース変換先モデルPMXファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText3.Wrap( -1 )

		bSizer4.Add( self.m_staticText3, 0, wx.ALL, 5 )

		self.m_fileRepPmx = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, u"トレース変換先モデルPMXファイルを開く", u"*.pmx", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		bSizer4.Add( self.m_fileRepPmx, 0, wx.ALL|wx.EXPAND, 5 )

		bSizerAvoidance = wx.BoxSizer( wx.HORIZONTAL )

		self.m_chkAvoidance = wx.CheckBox( self, wx.ID_ANY, u"頭～上半身と腕の接触回避処理を行う　（※それなりに時間がかかります）", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizerAvoidance.Add( self.m_chkAvoidance, 0, wx.ALL, 5 )

		self.m_staticText7 = wx.StaticText( self, wx.ID_ANY, u"接触回避判定先", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizerAvoidance.Add( self.m_staticText7, 0, wx.ALL, 5 )

		self.m_chcAvoidanceTarget = wx.Choice(self, id=wx.ID_ANY, choices=["人差し指", "手首"])
		self.m_chcAvoidanceTarget.SetSelection(0)
		bSizerAvoidance.Add( self.m_chcAvoidanceTarget, 0, wx.ALL, 5 )

		bSizer4.Add(bSizerAvoidance)

		self.m_staticText6 = wx.StaticText( self, wx.ID_ANY, u"モーフ置換設定", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText6.Wrap( -1 )

		bSizer4.Add( self.m_staticText6, 0, wx.ALL, 5 )

		# モーフ切替部分
		gSizer2 = wx.BoxSizer( wx.HORIZONTAL )

		# モーフ切替機能
		self.m_txtMorph = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( 500,40 ), 0|wx.HSCROLL|wx.NO_BORDER|wx.WANTS_CHARS|wx.TE_MULTILINE|wx.TE_READONLY )
		self.m_txtMorph.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )
		gSizer2.Add( self.m_txtMorph, 1, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_btnMorph = wx.Button( self, wx.ID_ANY, u"モーフ指定", wx.DefaultPosition, wx.Size( 100,30 ), 0 )
		gSizer2.Add( self.m_btnMorph, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10 )

		bSizer4.Add( gSizer2, 0, wx.ALIGN_CENTER|wx.SHAPED, 5 )

		self.m_staticText5 = wx.StaticText( self, wx.ID_ANY, u"出力先VMDファイル（変更可）", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText5.Wrap( -1 )

		bSizer4.Add( self.m_staticText5, 0, wx.ALL, 5 )

		self.m_fileOutputVmd = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, u"出力対象VMDファイルを指定する", u"*.vmd", wx.DefaultPosition, wx.Size( -1,-1 ),  wx.FLP_OVERWRITE_PROMPT|wx.FLP_SAVE|wx.FLP_USE_TEXTCTRL )
		bSizer4.Add( self.m_fileOutputVmd, 0, wx.ALL|wx.EXPAND, 5 )

		# ボタン部分
		gSizer1 = wx.GridSizer( 0, 2, 50, 50 )

		self.m_btnCheck = wx.Button( self, wx.ID_ANY, u"変換前チェック", wx.DefaultPosition, wx.Size( 200,50 ), 0 )
		gSizer1.Add( self.m_btnCheck, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_btnExec = wx.Button( self, wx.ID_ANY, u"VMDサイジング実行", wx.DefaultPosition, wx.Size( 200,50 ), 0 )
		gSizer1.Add( self.m_btnExec, 0, wx.ALIGN_CENTER|wx.ALIGN_CENTER_VERTICAL, 5 )

		bSizer4.Add( gSizer1, 0, wx.ALIGN_CENTER|wx.SHAPED, 5 )

		# コンソール
		self.m_txtConsole = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0|wx.VSCROLL|wx.HSCROLL|wx.NO_BORDER|wx.WANTS_CHARS|wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL )
		self.m_txtConsole.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )

		# redirect text here
		sys.stdout = self.m_txtConsole

		bSizer4.Add( self.m_txtConsole, 1, wx.EXPAND |wx.ALL, 5 )

		# 進捗ゲージ
		self.m_Gauge = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
		self.m_Gauge.SetValue(0)
		self.gauge_max = self.m_Gauge.GetSize()[0]
		self.Bind(wx.EVT_IDLE, self.OnIdle)
		bSizer4.Add( self.m_Gauge, 0, wx.ALL|wx.EXPAND, 5 )

		bSizer3.Add( bSizer4, 1, wx.EXPAND, 5 )

		# Connect Events
		self.m_btnMorph.Bind( wx.EVT_BUTTON, self.OnShowMorph )
		self.m_btnCheck.Bind( wx.EVT_BUTTON, self.OnCheck )
		self.m_btnExec.Bind( wx.EVT_BUTTON, self.OnStart )

		# Set up event handler for any worker thread results
		EVT_RESULT(self, self.OnResult)

		# And indicate we don't have a worker thread yet
		self.worker = None

		# 出力ファイルパスの生成
		self.Bind( wx.EVT_FILEPICKER_CHANGED, self.CreateOutputVmd, self.m_fileVmd )
		self.Bind( wx.EVT_FILEPICKER_CHANGED, self.CreateOutputVmd, self.m_fileRepPmx )

		# D&Dの実装
		self.m_fileVmd.SetDropTarget(MyFileDropTarget(self, self.m_fileVmd, self.m_staticText1, ".vmd"))
		self.m_fileOrgPmx.SetDropTarget(MyFileDropTarget(self, self.m_fileOrgPmx, self.m_staticText2, ".pmx"))
		self.m_fileRepPmx.SetDropTarget(MyFileDropTarget(self, self.m_fileRepPmx, self.m_staticText3, ".pmx"))
		self.m_fileOutputVmd.SetDropTarget(MyFileDropTarget(self, self.m_fileOutputVmd, self.m_staticText5, ".vmd"))

		# ウィンドウクローズイベント
		# self.Bind( wx.EVT_CLOSE, self.OnClose )

		self.morphFrame = None

		self.SetSizer( bSizer3 )
		self.Layout()

		self.Centre( wx.BOTH )
		self.Show()

	def __del__( self ):
		pass
	
	def OnClose(self, event):
		# スレッド破棄
		if self.worker:
			self.worker.abort()
			self.worker = None

		self.DestroyChildren()
		self.Destroy()

	def OnShowMorph(self, event):

		if wrapperutils.is_executable(self.m_fileVmd.GetPath(), self.m_fileOrgPmx.GetPath(), self.m_fileRepPmx.GetPath()) == False:
			# 入力情報により処理却下
			return False
		
		if not self.vmd:
			self.vmd = wrapperutils.read_vmd(self.m_fileVmd.GetPath())
		
		if not self.org_pmx:
			self.org_pmx = wrapperutils.read_pmx(self.m_fileOrgPmx.GetPath())
		
		if not self.rep_pmx:
			self.rep_pmx = wrapperutils.read_pmx(self.m_fileRepPmx.GetPath())

		if len(self.vmd.morphs.keys()) == 0:
			print("■■■■■■■■■■■■■■■■■")
			print("■　**INFO**　")
			print("■　VMDデータにモーフが含まれていません。")
			print("■■■■■■■■■■■■■■■■■")
			return False
		
		if not self.morphFrame:
			self.morphFrame = MorphFrame(self, self.vmd, self.org_pmx, self.rep_pmx)

		self.morphFrame.Show()
        

	# チェックボタン押下
	def OnCheck(self, event):
		self.m_txtConsole.Clear()
		self.m_Gauge.Pulse()
		wrapperutils.is_all_sizing(self.m_fileVmd.GetPath(), self.m_fileOrgPmx.GetPath(), self.m_fileRepPmx.GetPath())
		self.m_Gauge.SetValue(0)

	# 実行ボタン押下
	def OnStart(self, event):
		"""Start Computation."""
		# Trigger the worker thread unless it's already busy
		if not self.worker:
			# print('Starting computation')

			self.m_txtConsole.Clear()

			if wrapperutils.is_executable(self.m_fileVmd.GetPath(), self.m_fileOrgPmx.GetPath(), self.m_fileRepPmx.GetPath()) == False:
				# 入力情報により処理却下
				return False

			# 実行ボタン押下不可
			self.m_btnExec.Disable()
			# スレッド実行
			self.worker = WorkerThread(self, self.m_fileVmd.GetPath(), self.m_fileOrgPmx.GetPath(), self.m_fileRepPmx.GetPath(), self.m_fileOutputVmd.GetPath(), self.m_chkAvoidance.IsChecked(), self.m_chcAvoidanceTarget.GetSelection(), self.vmd_choice_values, self.rep_choice_values )

	# 待機中はゲージを動かす
	def OnIdle(self, event):
		if self.worker:
			self.m_Gauge.Pulse()

	# スレッド実行結果
	def OnResult(self, event):
		# スレッド削除
		self.worker = None
		# 実行ボタン押下許可
		self.m_btnExec.Enable()
		# プログレス非表示
		self.m_Gauge.SetValue(0)
	
	# 出力ファイルパスの生成
	def CreateOutputVmd(self, event):	
		# print("CreateOutputVmd2")
		# print("m_fileVmd: %s " % self.m_fileVmd.GetPath())
		# print("m_fileRepPmx: %s " % self.m_fileRepPmx.GetPath())
		new_filepath = wrapperutils.create_output_path(self.m_fileVmd.GetPath(), self.m_fileRepPmx.GetPath())
		# print("new_filepath: %s " % new_filepath)
		if new_filepath is not None:
			self.m_fileOutputVmd.SetPath(new_filepath)

	# モーフ情報クリア
	def ClearMorph(self):
		self.vmd_choice_values = []
		self.rep_choice_values = []
		self.m_txtMorph.SetValue("")

		if self.morphFrame:
			self.morphFrame.Destroy()
			self.morphFrame = None


# ボタンIDの新規発行
ID_START = wx.NewId()

# Define notification event for thread completion
EVT_RESULT_ID = wx.NewId()

def EVT_RESULT(win, func):
	"""Define Result Event."""
	win.Connect(-1, -1, EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
	"""Simple event to carry arbitrary result data."""
	def __init__(self, data):
		"""Init Result Event."""
		wx.PyEvent.__init__(self)
		self.SetEventType(EVT_RESULT_ID)
		self.data = data
		# print("end")

# Thread class that executes processing
class WorkerThread(threading.Thread):
	"""Worker Thread Class."""
	def __init__(self, notify_window, vmd_path, org_pmx_path, rep_pmx_path, output_vmd_path, is_avoidance, avoidance_target, vmd_choice_values, rep_choice_values):
		"""Init Worker Thread Class."""
		threading.Thread.__init__(self)
		self._notify_window = notify_window
		self._want_abort = 0

		# パラメーター設定
		self.vmd_path = vmd_path
		self.org_pmx_path = org_pmx_path
		self.rep_pmx_path = rep_pmx_path
		self.output_vmd_path = output_vmd_path
		self.is_avoidance = is_avoidance
		# 人差し指を接触回避処理するか
		self.avoidance_target = avoidance_target == 0
		self.vmd_choice_values = vmd_choice_values
		self.rep_choice_values = rep_choice_values

		# This starts the thread running on creation, but you could
		# also make the GUI thread responsible for calling this
		self.start()

	def run(self):
		"""Run Worker Thread."""
		# This is the code executing in the new thread. Simulation of
		# a long process (well, 10s here) as a simple loop - you will
		# need to structure your processing so that you periodically
		# peek at the abort variable

		# 処理実行
		wrapperutils.exec(self.vmd_path, self.org_pmx_path, self.rep_pmx_path, self.output_vmd_path, self.is_avoidance, self.avoidance_target, self.vmd_choice_values, self.rep_choice_values)

		# Here's where the result would be returned (this is an
		# example fixed result of the number 10, but it could be
		# any Python object)
		wx.PostEvent(self._notify_window, ResultEvent(None))

	def abort(self):
		"""abort worker thread."""
		# Method for use by main thread to signal an abort
		self._want_abort = 1


class MyFileDropTarget(wx.FileDropTarget):
	def __init__(self, window, target_ctrl, label_ctrl, ext):
		wx.FileDropTarget.__init__(self)
		self.window = window
		# D&D対象
		self.target_ctrl = target_ctrl
		# 処理対象項目のラベル
		self.label_ctrl = label_ctrl
		# 許可拡張子
		self.ext = ext

	def OnDropFiles(self, x, y, files):
		# ファイルパスをテキストフィールドに表示
		_, input_ext = os.path.splitext(os.path.basename(files[0]))

		if input_ext.lower() == self.ext.lower():
			# 拡張子を許容してたらOK
			self.target_ctrl.SetPath(files[0])

			# オブジェクトクリア
			if self.target_ctrl == self.window.m_fileVmd:
				self.window.vmd = None

			if self.target_ctrl == self.window.m_fileOrgPmx:
				self.window.org_pmx = None
				
			if self.target_ctrl == self.window.m_fileRepPmx:
				self.window.rep_pmx = None

			if self.target_ctrl == self.window.m_fileVmd or self.target_ctrl == self.window.m_fileRepPmx:
				# 出力パス生成対象コントロールの場合、VMD生成処理を走らせる
				self.window.CreateOutputVmd(wx.EVT_FILEPICKER_CHANGED)
			
			if self.target_ctrl != self.window.m_fileOutputVmd:
				# 出力ファイル以外はモーフも変わるので初期化
				self.window.ClearMorph()

			return True
		
		print("{0}の拡張子が正しくありません。設定可能拡張子: {1}".format(self.label_ctrl.GetLabel(), self.ext.lower()))

		# それ以外は不許可
		return False
