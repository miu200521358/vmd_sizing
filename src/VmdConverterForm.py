# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Oct 26 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import sys
import os
import wrapperutils
import convert_vmd

###########################################################################
## Class VmdConverterFrame
###########################################################################

class VmdConverterFrame ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"VMDコンバーター ver1.00", pos = wx.DefaultPosition, size = wx.Size( 451,271 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_3DLIGHT ) )

		bSizer3 = wx.BoxSizer( wx.VERTICAL )

		bSizer4 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"VMDファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )

		bSizer4.Add( self.m_staticText1, 0, wx.ALL, 5 )

		self.m_fileVmd = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, u"Select a file", u"*.vmd", wx.DefaultPosition, wx.Size( -1,-1 ), wx.FLP_DEFAULT_STYLE )
		bSizer4.Add( self.m_fileVmd, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_btnExec = wx.Button( self, wx.ID_ANY, u"CSV変換実行", wx.DefaultPosition, wx.Size( 150,30 ), 0 )
		bSizer4.Add( self.m_btnExec, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.m_txtConsole = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,100 ), wx.TE_MULTILINE|wx.TE_READONLY|wx.BORDER_NONE|wx.HSCROLL|wx.VSCROLL|wx.WANTS_CHARS )
		self.m_txtConsole.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_3DLIGHT ) )

		bSizer4.Add( self.m_txtConsole, 0, wx.ALL|wx.EXPAND, 5 )


		bSizer3.Add( bSizer4, 1, wx.EXPAND, 5 )

		self.SetSizer( bSizer3 )
		self.Layout()

		self.Centre( wx.BOTH )

		# イベント登録 -----------------------

		# redirect text here
		sys.stdout = self.m_txtConsole

		# Connect Events
		self.m_btnExec.Bind( wx.EVT_BUTTON, self.OnExec )

		# D&Dの実装
		self.m_fileVmd.SetDropTarget(MyFileDropTarget(self, self.m_fileVmd, self.m_staticText1, ".vmd"))

	def __del__( self ):
		pass

	# Virtual event handlers, overide them in your derived class
	def OnExec( self, event ):
		convert_vmd.main(self.m_fileVmd.GetPath())


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
		file_name, input_ext = os.path.splitext(os.path.basename(files[0]))
		# logger.debug("D&D file_name: %s, input_ext: %s", file_name, input_ext)

		if input_ext.lower() == self.ext.lower():
			# 拡張子を許容してたらOK
			self.target_ctrl.SetPath(files[0])

			return True
		
		print("{0}の拡張子が正しくありません。設定可能拡張子: {1}".format(self.label_ctrl.GetLabel(), self.ext.lower()))

		# それ以外は不許可
		return False
