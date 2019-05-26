# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Oct 26 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
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

class Frame ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"VMDサイジング ローカル版 ver2.00", pos = wx.DefaultPosition, size = wx.Size( 651,600 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_3DLIGHT ) )

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

		self.m_chkAvoidance = wx.CheckBox( self, wx.ID_ANY, u"頭～上半身と腕の接触回避処理を行う　（※それなりに時間がかかります）", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer4.Add( self.m_chkAvoidance, 0, wx.ALL, 5 )

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
		self.Bind( wx.EVT_CLOSE, self.OnClose )

		self.SetSizer( bSizer3 )
		self.Layout()

		self.Centre( wx.BOTH )

	def __del__( self ):
		pass
	
	def OnClose(self, event):
		# スレッド破棄
		if self.worker:
			self.worker.abort()
			self.worker = None

		self.Destroy()

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
			self.worker = WorkerThread(self, self.m_fileVmd.GetPath(), self.m_fileOrgPmx.GetPath(), self.m_fileRepPmx.GetPath(), self.m_fileOutputVmd.GetPath(), self.m_chkAvoidance.IsChecked() )

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
	def __init__(self, notify_window, vmd_path, org_pmx_path, rep_pmx_path, output_vmd_path, is_avoidance):
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
		wrapperutils.exec(self.vmd_path, self.org_pmx_path, self.rep_pmx_path, self.output_vmd_path, self.is_avoidance)

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

			if self.target_ctrl == self.window.m_fileVmd or self.target_ctrl == self.window.m_fileRepPmx:
				# 出力パス生成対象コントロールの場合、VMD生成処理を走らせる
				self.window.CreateOutputVmd(wx.EVT_FILEPICKER_CHANGED)

			return True
		
		print("{0}の拡張子が正しくありません。設定可能拡張子: {1}".format(self.label_ctrl.GetLabel(), self.ext.lower()))

		# それ以外は不許可
		return False
