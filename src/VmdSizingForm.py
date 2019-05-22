# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Oct 26 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import wx.richtext
import logging
import sys
import wrapperutils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


###########################################################################
## Class Frame
###########################################################################

class Frame ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"VMDサイジング デスクトップ版 ver1.10", pos = wx.DefaultPosition, size = wx.Size( 651,600 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		self.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_3DLIGHT ) )

		bSizer3 = wx.BoxSizer( wx.VERTICAL )

		bSizer4 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"調整対象vmdファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )

		bSizer4.Add( self.m_staticText1, 0, wx.ALL, 5 )

		self.m_fileVmd = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, u"調整対象vmdファイルを開く", u"*.vmd", wx.DefaultPosition, wx.Size( -1,-1 ), wx.FLP_DEFAULT_STYLE )
		bSizer4.Add( self.m_fileVmd, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText2 = wx.StaticText( self, wx.ID_ANY, u"トレース元モデルボーン構造CSVファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText2.Wrap( -1 )

		bSizer4.Add( self.m_staticText2, 0, wx.ALL, 5 )

		self.m_fileOrgBone = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, u"トレース元モデルボーン構造CSVファイルを開く", u"*.csv", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		bSizer4.Add( self.m_fileOrgBone, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, u"トレース変換先モデルボーン構造CSVファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText3.Wrap( -1 )

		bSizer4.Add( self.m_staticText3, 0, wx.ALL, 5 )

		self.m_fileRepBone = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, u"トレース変換先モデルボーン構造CSVファイルを開く", u"*.csv", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		bSizer4.Add( self.m_fileRepBone, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_staticText4 = wx.StaticText( self, wx.ID_ANY, u"トレース変換先モデル頂点構造CSVファイル (任意)", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )

		bSizer4.Add( self.m_staticText4, 0, wx.ALL, 5 )

		self.m_fileRepVertex = wx.FilePickerCtrl( self, wx.ID_ANY, wx.EmptyString, u"トレース変換先モデル頂点構造CSVファイルを開く", u"*.csv", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		bSizer4.Add( self.m_fileRepVertex, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_btnExec = wx.Button( self, wx.ID_ANY, u"VMDサイジング実行", wx.DefaultPosition, wx.Size( 200,50 ), 0 )
		bSizer4.Add( self.m_btnExec, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.m_txtConsole = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0|wx.VSCROLL|wx.HSCROLL|wx.NO_BORDER|wx.WANTS_CHARS|wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL )
		self.m_txtConsole.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_BTNFACE ) )

		# redirect text here
		sys.stdout = self.m_txtConsole

		bSizer4.Add( self.m_txtConsole, 1, wx.EXPAND |wx.ALL, 5 )


		bSizer3.Add( bSizer4, 1, wx.EXPAND, 5 )


		self.SetSizer( bSizer3 )
		self.Layout()

		self.Centre( wx.BOTH )

		# Connect Events
		self.m_btnExec.Bind( wx.EVT_BUTTON, self.exec )

	def __del__( self ):
		pass


	# Virtual event handlers, overide them in your derived class
	def exec( self, event ):
		event.Skip()

		self.m_txtConsole.Clear()
		
		if wrapperutils.is_valid_inputall(self.m_fileVmd.GetPath(), self.m_fileOrgBone.GetPath(), self.m_fileRepBone.GetPath(), self.m_fileRepVertex.GetPath() ) == False:
			return
		else:
			wrapperutils.exec(self.m_fileVmd.GetPath(), self.m_fileOrgBone.GetPath(), self.m_fileRepBone.GetPath(), self.m_fileRepVertex.GetPath())
