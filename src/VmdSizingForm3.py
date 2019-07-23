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
import time
import re
import csv
import json
from pathlib import Path
from threading import Thread, Event
import traceback

import wrapperutils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VmdSizing").getChild(__name__)

###########################################################################
## Class VmdSizingForm3
###########################################################################

class VmdSizingForm3 ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"VMDサイジング ローカル版 ver3.00β66", pos = wx.DefaultPosition, size = wx.Size( 600,710 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
		
		# 初期化(クラス外の変数) -----------------------
		# モーフ置換配列
		self.vmd_choice_values = []
		self.rep_choice_values = []
		self.rep_rate_values = []

		# ファイル解析情報
		self.vmd_data = None
		self.org_pmx_data = None
		self.rep_pmx_data = None

		# モーフプルダウン
		self.vmd_morphs = None
		self.rep_morphs = None
		self.vmd_choices = None
		self.arrow_choices = None
		self.rep_choices = None
		self.rep_rates = None

		# スレッド用
		self.worker = None

		# ファイル履歴
		self.file_hitories = {"vmd":[],"org_pmx":[],"rep_pmx":[],"max":20}
		# 履歴JSONファイルがあれば読み込み
		try:
			if os.path.exists("history.json"):
				with open('history.json', 'r') as f:
					self.file_hitories = json.load(f)
		except Exception:
			self.file_hitories = {"vmd":[],"org_pmx":[],"rep_pmx":[],"max":20}

		# ---------------------------------------------

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		bSizer1 = wx.BoxSizer( wx.VERTICAL )

		self.m_note = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_note.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_3DLIGHT ) )

		# ファイルタブ ------------------------------------

		self.m_panelFile = wx.Panel( self.m_note, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer4 = wx.BoxSizer( wx.VERTICAL )

		bSizer5 = wx.BoxSizer( wx.HORIZONTAL )

		# self.m_testTxt = wx.TextCtrl( self.m_panelFile, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (300,-1), 0 )
		# bSizer5.Add( self.m_testTxt, 0, wx.ALL, 5 )

		self.m_staticText9 = wx.StaticText( self.m_panelFile, wx.ID_ANY, u"調整対象VMDファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText9.Wrap( -1 )

		bSizer5.Add( self.m_staticText9, 0, wx.ALL, 5 )

		# self.m_vmdTraceTxt = wx.StaticText( self.m_panelFile, wx.ID_ANY, u"　（調整対象VMD未設定）", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_vmdTraceTxt.Wrap( -1 )

		self.m_vmdTraceTxt = wx.TextCtrl( self.m_panelFile, wx.ID_ANY, u"　（調整対象VMD未設定）", wx.DefaultPosition, (300,-1), wx.TE_READONLY|wx.BORDER_NONE|wx.WANTS_CHARS )
		self.m_vmdTraceTxt.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_3DLIGHT ) )
		self.m_vmdTraceTxt.SetToolTip( u"VMDファイルに記録されているモデル名です。選択でコピペ可能です。" )

		bSizer5.Add( self.m_vmdTraceTxt, 0, wx.ALL, 5 )

		bSizer4.Add( bSizer5, 0, wx.EXPAND, 5 )

		bSizer6 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_fileVmd = wx.FilePickerCtrl( self.m_panelFile, wx.ID_ANY, wx.EmptyString, u"調整対象VMDファイルを開く", u"*.vmd", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		# self.m_fileVmd = MyFilePickerCtrl( self, self.m_panelFile, bSizer4, id=wx.ID_ANY, path="", file_message=u"調整対象VMDファイルを開く", wildcard=u"*.vmd", file_style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST, label_ctrl=self.m_staticText9 )
		self.m_fileVmd.GetPickerCtrl().SetLabel("開く")
		self.m_fileVmd.SetToolTip( u"調整したいモーションのVMDパスを指定してください。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。" )
		# self.m_fileVmd.GetTextCtrl().AutoComplete(self.file_hitories["vmd"])

		bSizer6.Add( self.m_fileVmd, 1, wx.ALL|wx.EXPAND, 5 )

		self.m_btnHistoryVmd = wx.Button( self.m_panelFile, wx.ID_ANY, u"履歴", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_btnHistoryVmd.SetToolTip( u"調整したいモーションのVMDパスを指定してください。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。" )
		bSizer6.Add( self.m_btnHistoryVmd, 0, wx.ALL, 5 )

		bSizer4.Add( bSizer6, 0, wx.EXPAND, 5 )

		self.m_staticText10 = wx.StaticText( self.m_panelFile, wx.ID_ANY, u"モーション作成元モデルPMXファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText10.Wrap( -1 )

		bSizer4.Add( self.m_staticText10, 0, wx.ALL, 5 )

		bSizer7 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_fileOrgPmx = wx.FilePickerCtrl( self.m_panelFile, wx.ID_ANY, wx.EmptyString, u"モーション作成元モデルPMXファイルを開く", u"*.pmx", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		# self.m_fileOrgPmx = MyFilePickerCtrl( self, self.m_panelFile, bSizer4, id=wx.ID_ANY, path="", file_message=u"モーション作成元モデルPMXファイルを開く", wildcard=u"*.pmx", file_style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST, label_ctrl=self.m_staticText10 )
		self.m_fileOrgPmx.SetToolTip( u"モーション作成に使用されたモデルのPMXパスを指定してください。\n精度は落ちますが、類似したサイズ・ボーン構造のモデルでも代用できます。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。" )
		# self.m_fileOrgPmx.GetTextCtrl().AutoComplete(self.file_hitories["org_pmx"])
		self.m_fileOrgPmx.GetPickerCtrl().SetLabel("開く")

		bSizer7.Add( self.m_fileOrgPmx, 1, wx.ALL|wx.EXPAND, 5 )

		self.m_btnHistoryOrgPmx = wx.Button( self.m_panelFile, wx.ID_ANY, u"履歴", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_btnHistoryOrgPmx.SetToolTip( u"モーション作成に使用されたモデルのPMXパスを指定してください。\n精度は落ちますが、類似したサイズ・ボーン構造のモデルでも代用できます。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。" )
		bSizer7.Add( self.m_btnHistoryOrgPmx, 0, wx.ALL, 5 )

		bSizer4.Add( bSizer7, 0, wx.EXPAND, 5 )

		self.m_staticText11 = wx.StaticText( self.m_panelFile, wx.ID_ANY, u"モーション変換先モデルPMXファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText11.Wrap( -1 )

		bSizer4.Add( self.m_staticText11, 0, wx.ALL, 5 )

		bSizer8 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_fileRepPmx = wx.FilePickerCtrl( self.m_panelFile, wx.ID_ANY, wx.EmptyString, u"モーション変換先モデルPMXファイルを開く", u"*.pmx", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		# self.m_fileRepPmx = MyFilePickerCtrl( self, self.m_panelFile, bSizer4, id=wx.ID_ANY, path="", file_message=u"モーション変換先モデルPMXファイルを開く", wildcard=u"*.pmx", file_style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST, label_ctrl=self.m_staticText11 )
		self.m_fileRepPmx.GetPickerCtrl().SetLabel("開く")
		self.m_fileRepPmx.SetToolTip( u"実際にモーションを読み込ませたいモデルのPMXパスを指定してください。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。" )
		# self.m_fileRepPmx.GetTextCtrl().AutoComplete(self.file_hitories["rep_pmx"])

		bSizer8.Add( self.m_fileRepPmx, 1, wx.ALL|wx.EXPAND, 5 )

		self.m_btnHistoryRepPmx = wx.Button( self.m_panelFile, wx.ID_ANY, u"履歴", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_btnHistoryRepPmx.SetToolTip( u"実際にモーションを読み込ませたいモデルのPMXパスを指定してください。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。" )
		bSizer8.Add( self.m_btnHistoryRepPmx, 0, wx.ALL, 5 )

		bSizer4.Add( bSizer8, 0, wx.EXPAND, 5 )

		self.m_staticText12 = wx.StaticText( self.m_panelFile, wx.ID_ANY, u"出力VMDファイル（変更可）", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText12.Wrap( -1 )

		bSizer4.Add( self.m_staticText12, 0, wx.ALL, 5 )

		self.m_fileOutputVmd = wx.FilePickerCtrl( self.m_panelFile, wx.ID_ANY, wx.EmptyString, u"モーション変換先モデルPMXファイルを開く", u"*.vmd", wx.DefaultPosition, wx.DefaultSize, wx.FLP_OVERWRITE_PROMPT|wx.FLP_SAVE|wx.FLP_USE_TEXTCTRL )
		# self.m_fileOutputVmd = MyFilePickerCtrl( self, self.m_panelFile, bSizer4, id=wx.ID_ANY, path="", file_message=u"出力VMDファイルを開く", wildcard=u"*.vmd", file_style=wx.FLP_OVERWRITE_PROMPT|wx.FLP_SAVE )
		self.m_fileOutputVmd.GetPickerCtrl().SetLabel("開く")
		self.m_fileOutputVmd.SetToolTip( u"調整結果のVMD出力パスを指定してください。\nVMDファイルと変換先PMXのファイル名に基づいて自動生成されますが、任意のパスに変更することも可能です。" )

		bSizer4.Add( self.m_fileOutputVmd, 0, wx.ALL|wx.EXPAND, 5 )

		bSizer9 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_btnCheck = wx.Button( self.m_panelFile, wx.ID_ANY, u"変換前チェック", wx.DefaultPosition, wx.Size( 200,50 ), 0 )
		self.m_btnCheck.SetToolTip( u"入力されたファイル情報で処理可能かどうか、チェックを行います。" )
		bSizer9.Add( self.m_btnCheck, 0, wx.ALL, 5 )

		self.m_btnExec = wx.Button( self.m_panelFile, wx.ID_ANY, u"VMDサイジング実行", wx.DefaultPosition, wx.Size( 200,50 ), 0 )
		self.m_btnExec.SetToolTip( u"VMDサイジング処理を実行します。" )
		bSizer9.Add( self.m_btnExec, 0, wx.ALL, 5 )


		bSizer4.Add( bSizer9, 0, wx.ALIGN_CENTER|wx.SHAPED, 5 )

		self.m_txtConsole = wx.TextCtrl( self.m_panelFile, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,190 ), wx.TE_MULTILINE|wx.TE_READONLY|wx.BORDER_NONE|wx.HSCROLL|wx.VSCROLL|wx.WANTS_CHARS )
		self.m_txtConsole.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_3DLIGHT ) )

		bSizer4.Add( self.m_txtConsole, 1, wx.ALL|wx.EXPAND, 5 )

		self.m_Gauge = wx.Gauge( self.m_panelFile, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
		self.m_Gauge.SetValue( 0 )
		bSizer4.Add( self.m_Gauge, 0, wx.ALL|wx.EXPAND, 5 )
	
		self.m_panelFile.SetSizer( bSizer4 )
		self.m_panelFile.Layout()
		bSizer4.Fit( self.m_panelFile )
		self.m_note.AddPage( self.m_panelFile, u"ファイル", True )

		# モーフタブ ------------------------------------

		self.m_panelMorph = wx.Panel( self.m_note, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )

		bSizer8 = wx.BoxSizer( wx.VERTICAL )

		self.m_panelMorphHeader = wx.Panel( self.m_panelMorph, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer10 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText132 = wx.StaticText( self.m_panelMorphHeader, wx.ID_ANY, u"モーションに使用されているモーフを、\n変換先モデルにある任意のモーフに置き換える事ができます。\nモーションモーフプルダウンの先頭記号は以下の通りです。\n○　…　モーション・生成元モデル・変換先モデルすべてにあるモーフ\n●　…　モーション・変換先モデルにあり、生成元モデルにないモーフ\n▲　…　モーション・生成元モデルにあり、変換先モデルにないモーフ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText132.Wrap( -1 )
		bSizer10.Add( self.m_staticText132, 0, wx.ALL, 5 )

		bSizer11 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_btnMorphImport = wx.Button( self.m_panelMorphHeader, wx.ID_ANY, u"インポート ...", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_btnMorphImport.SetToolTip( u"モーフ置換データをCSVファイルから読み込みます。\nファイル選択ダイアログが開きます。" )
		bSizer11.Add( self.m_btnMorphImport, 0, wx.ALIGN_RIGHT|wx.ALL, 5 )

		self.m_btnMorphExport = wx.Button( self.m_panelMorphHeader, wx.ID_ANY, u"エクスポート", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_btnMorphExport.SetToolTip( u"モーフ置換データをCSVファイルに出力します。\n調整対象VMDと同じフォルダに出力します。" )
		bSizer11.Add( self.m_btnMorphExport, 0, wx.ALIGN_RIGHT|wx.ALL, 5 )

		self.m_btnAddLine = wx.Button( self.m_panelMorphHeader, wx.ID_ANY, u"行追加", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_btnAddLine.SetToolTip( u"モーフ置換の組み合わせ行を追加します。\n上限はありません。" )
		bSizer11.Add( self.m_btnAddLine, 0, wx.ALIGN_RIGHT|wx.ALL, 5 )

		bSizer10.Add( bSizer11, 0, wx.ALIGN_RIGHT|wx.ALL, 5 )

		self.m_panelMorphHeader.SetSizer( bSizer10 )
		self.m_panelMorphHeader.Layout()
		bSizer10.Fit( self.m_panelMorphHeader )
		bSizer8.Add( self.m_panelMorphHeader, 0, wx.EXPAND |wx.ALL, 5 )

		self.m_scrolledMorph = wx.ScrolledWindow( self.m_panelMorph, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.FULL_REPAINT_ON_RESIZE|wx.VSCROLL )
		self.m_scrolledMorph.SetScrollRate( 5, 5 )

		self.gridMorphSizer = wx.FlexGridSizer( 0, 4, 0, 0 )
		self.gridMorphSizer.SetFlexibleDirection( wx.BOTH )
		self.gridMorphSizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.m_staticText18 = wx.StaticText( self.m_scrolledMorph, wx.ID_ANY, u"モーションモーフ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText18.SetToolTip( u"調整対象VMDに登録されているモーフです。" )
		self.m_staticText18.Wrap( -1 )
		self.gridMorphSizer.Add( self.m_staticText18, 0, wx.ALL, 5 )

		self.m_staticText19 = wx.StaticText( self.m_scrolledMorph, wx.ID_ANY, u"　→　", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText19.Wrap( -1 )
		self.gridMorphSizer.Add( self.m_staticText19, 0, wx.CENTER|wx.ALL, 5 )

		self.m_staticText20 = wx.StaticText( self.m_scrolledMorph, wx.ID_ANY, u"置換後モーフ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText20.SetToolTip( u"モーション変換先モデルで定義されているモーフです。" )
		self.m_staticText20.Wrap( -1 )
		self.gridMorphSizer.Add( self.m_staticText20, 0, wx.ALL, 5 )

		self.m_staticText21 = wx.StaticText( self.m_scrolledMorph, wx.ID_ANY, u"大きさ補正", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText21.SetToolTip( u"置換後モーフの大きさを補正します。" )
		self.m_staticText21.Wrap( -1 )
		self.gridMorphSizer.Add( self.m_staticText21, 0, wx.ALL, 5 )

		self.m_scrolledMorph.SetSizer( self.gridMorphSizer )
		self.m_scrolledMorph.Layout()
		# self.gridMorphSizer.Fit( self.m_scrolledMorph )
		bSizer8.Add( self.m_scrolledMorph, 1, wx.ALL|wx.EXPAND|wx.FIXED_MINSIZE, 5 )


		self.m_panelMorph.SetSizer( bSizer8 )
		self.m_panelMorph.Layout()
		bSizer8.Fit( self.m_panelMorph )
		self.m_note.AddPage( self.m_panelMorph, u"モーフ", False )


		# 腕タブ ------------------------------------

		self.m_panelArm = wx.Panel( self.m_note, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )

		bSizer13 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText7 = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"腕を変換先モデルに合わせて調整する事ができます。\n「腕接触回避」と「手首位置合わせ」のいずれか片方しか選択できません。\n腕の動きが、元々のモーションから変わる事があります。\nいずれもそれなりに時間がかかります。", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText7.Wrap( -1 )

		bSizer13.Add( self.m_staticText7, 0, wx.ALL, 5 )
		
		self.m_staticline1 = wx.StaticLine( self.m_panelArm, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer13.Add( self.m_staticline1, 0, wx.EXPAND |wx.ALL, 5 )

		# 同じグループなので、とりあえず宣言だけしておく
		self.m_radioArmNone = wx.RadioButton( self.m_panelArm, wx.ID_ANY, u"腕関係の処理を行わない", wx.DefaultPosition, wx.DefaultSize, style=wx.RB_GROUP )
		self.m_radioArmNone.SetValue( True )

		self.m_radioAvoidance = wx.RadioButton( self.m_panelArm, wx.ID_ANY, u"頭に腕が貫通しないよう、腕接触回避を行う", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_radioAvoidance.SetToolTip( u"頭部に腕が貫通しないよう、腕の角度を小さくして、接触を回避する処理を行います。" )
		self.m_radioArmIK = wx.RadioButton( self.m_panelArm, wx.ID_ANY, u"変換先モデルの体型に合わせて、手首位置を調整する", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_radioArmIK.SetToolTip( u"変換先モデルの手首を、作成元モデルの手首とほぼ同じ位置に揃えるよう、手首位置を調整します。" )

		bSizer13.Add( self.m_radioArmNone, 0, wx.ALL, 5 )

		self.m_staticlineNone = wx.StaticLine( self.m_panelArm, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer13.Add( self.m_staticlineNone, 0, wx.EXPAND |wx.ALL, 5 )

		self.m_staticText91 = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"腕接触回避", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText91.Wrap( -1 )

		self.m_staticText91.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )
		bSizer13.Add( self.m_staticText91, 0, wx.ALL, 5 )

		self.m_staticText92 = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"ねんどろ風など、頭身が大幅に異なる場合に、\n頭部に腕が貫通してしまうのを軽減できます。", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText92.Wrap( -1 )

		bSizer13.Add( self.m_staticText92, 0, wx.ALL, 5 )


		bSizer13.Add( self.m_radioAvoidance, 0, wx.ALL, 5 )

		bSizer7 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText13 = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"腕接触回避判定先", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText13.Wrap( -1 )

		self.m_staticText13.SetToolTip( u"貫通しないよう腕接触回避を行うターゲットを選べます。\n指定が人差し指で腕が離れすぎてしまう場合に、手首に切り替えてみてください。" )

		bSizer7.Add( self.m_staticText13, 0, wx.ALL, 5 )

		self.m_radioAvoidanceFinger = wx.RadioButton( self.m_panelArm, wx.ID_ANY, u"人差し指", wx.DefaultPosition, wx.DefaultSize, style=wx.RB_GROUP )
		self.m_radioAvoidanceFinger.SetToolTip( u"人差し指が頭部と接触しないよう、接触回避を行います。" )
		self.m_radioAvoidanceFinger.SetValue( True )
		bSizer7.Add( self.m_radioAvoidanceFinger, 0, wx.ALL, 5 )

		self.m_radioAvoidanceWrist = wx.RadioButton( self.m_panelArm, wx.ID_ANY, u"手首", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_radioAvoidanceWrist.SetToolTip( u"手首が頭部と接触しないよう、接触回避を行います。\n人差し指の指定より、頭部との距離が近くなります。" )
		bSizer7.Add( self.m_radioAvoidanceWrist, 0, wx.ALL, 5 )


		bSizer13.Add( bSizer7, 0, wx.EXPAND, 5 )

		self.m_staticline2 = wx.StaticLine( self.m_panelArm, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer13.Add( self.m_staticline2, 0, wx.EXPAND |wx.ALL, 5 )

		self.m_staticText911 = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"手首位置合わせ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText911.Wrap( -1 )

		self.m_staticText911.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )

		bSizer13.Add( self.m_staticText911, 0, wx.ALL, 5 )

		self.m_staticText93 = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"両手を合わせるなどのモーションを、変換先モデルの手首位置に合わせて調整します。\n手首間の距離を調整することで、位置合わせの適用範囲を調整することができます。\nサイジング実行時、手首間の距離がメッセージ欄に出てますので、参考にしてください。", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText93.Wrap( -1 )

		bSizer13.Add( self.m_staticText93, 0, wx.ALL, 5 )

		bSizer13.Add( self.m_radioArmIK, 0, wx.ALL, 5 )

		bSizer15 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText39 = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"手首間の距離", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText39.SetToolTip( u"どのくらい手首が近付いた場合に、手首位置合わせを実行するか指定してください。\n値が小さいほど、手首が近付いた時だけ手首位置合わせを行います。\nスライダーを最大に設定すると、常に手首位置合わせを行います。（両手剣等に便利です）" )
		self.m_staticText39.Wrap( -1 )

		bSizer15.Add( self.m_staticText39, 0, wx.ALL, 5 )

		self.m_vmdHandDistanceTxt = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"　（1.7）", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_vmdHandDistanceTxt.SetToolTip( u"現在指定されている手首間の距離です。" )
		self.m_vmdHandDistanceTxt.Wrap( -1 )

		bSizer15.Add( self.m_vmdHandDistanceTxt, 0, wx.ALL, 5 )

		bSizer13.Add( bSizer15, 0, wx.ALL, 5 )

		# 小数点を許可したスライダー
		self.m_sliderHandDistance = FloatSlider( self.m_panelArm, wx.ID_ANY, 1.7, 0, 10, 0.1, self.m_vmdHandDistanceTxt, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		bSizer13.Add( self.m_sliderHandDistance, 0, wx.ALL|wx.EXPAND, 5 )

		# self.m_staticText391 = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"手首のZ位置補正オフセット", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText391.Wrap( -1 )

		# self.m_staticText391.SetToolTip( u"鎧や胸板などで、手首のZ位置をもう少しずらしたい、という時にオフセット値を指定してください。\nプラス値で身体に近付き、マイナス値で身体から離れます" )

		# self.m_sliderHandDistance = FloatSlider( wx.SpinCtrlDouble( self.m_scrolledMorph, id=wx.ID_ANY, size=wx.Size( 200,-1 ), value="0.0", min=-1000, max=1000, initial=0.0, inc=0.1 ) )
		# bSizer13.Add( self.m_sliderHandDistance, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_panelArm.SetSizer( bSizer13 )
		self.m_panelArm.Layout()
		bSizer13.Fit( self.m_panelArm )
		self.m_note.AddPage( self.m_panelArm, u"腕", False )

		# FAQ ------------------------------------

		self.m_scrolledFAQ = wx.ScrolledWindow( self.m_note, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.VSCROLL )
		self.m_scrolledFAQ.SetScrollRate( 5, 5 )
		bSizer8 = wx.BoxSizer( wx.VERTICAL )

		self.m_staticText132 = wx.StaticText( self.m_scrolledFAQ, wx.ID_ANY, u"Q:　モーション作成元モデルが入手できない（分からない）場合、どうしたらいいの？", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText132.Wrap( -1 )

		bSizer8.Add( self.m_staticText132, 0, wx.ALL, 5 )

		self.m_staticText14 = wx.StaticText( self.m_scrolledFAQ, wx.ID_ANY, u"A:　身長やボーン構造が似ているモデルで代用可能です。\n　　一旦代理モデルにモーションを読み込み、そのモデルに合わせて、モーションを調整してください。\n　　生成元として代理モデルを、調整対象モーションとして一次修正したモーションを\n　　指定する事で、ある程度互換性を持ってサイジングできます。\n　　代理モデルの選び方としては、膝をついたり、手を合わせたりするような、\n　　「ここ何とかしてほしいんだけど」という所の修正がいらない、もしくは、\n　　修正ができるだけ少ない、というのが目安になります。", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText14.Wrap( -1 )

		bSizer8.Add( self.m_staticText14, 0, wx.ALL, 5 )

		self.m_staticline5 = wx.StaticLine( self.m_scrolledFAQ, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer8.Add( self.m_staticline5, 0, wx.EXPAND |wx.ALL, 5 )

		self.m_staticText30 = wx.StaticText( self.m_scrolledFAQ, wx.ID_ANY, u"Q:　サイジングしたら、膝の位置がおかしくなってしまった", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText30.Wrap( -1 )

		bSizer8.Add( self.m_staticText30, 0, wx.ALL, 5 )

		self.m_staticText31 = wx.StaticText( self.m_scrolledFAQ, wx.ID_ANY, u"A:　足の長さか何かが原因で、うまく調整できない場合があります。（調査継続中です）\n　　その場合、センターZを少し前後に動かしていただくと、\n　　大抵の場合、膝をつけるようになると思います。\n　　センターZで直らない場合、足ボーンの角度を変更してみてください。", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText31.Wrap( -1 )

		bSizer8.Add( self.m_staticText31, 0, wx.ALL, 5 )

		self.m_staticline3 = wx.StaticLine( self.m_scrolledFAQ, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer8.Add( self.m_staticline3, 0, wx.EXPAND |wx.ALL, 5 )

		self.m_staticText15 = wx.StaticText( self.m_scrolledFAQ, wx.ID_ANY, u"Q:　槍とかのモーションの場合、どうしたらいいの？", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText15.Wrap( -1 )

		bSizer8.Add( self.m_staticText15, 0, wx.ALL, 5 )

		self.m_staticText16 = wx.StaticText( self.m_scrolledFAQ, wx.ID_ANY, u"A:　槍の場合、剣よりも両手の距離が離れますので、手首位置合わせの\n　　「手首間の距離」」デフォルト値では、足りない場面もあると思います。\n　　槍に限らず、常に両手の位置を元モーションと同じ位置に揃えたい場合は、\n　　「手首間の距離」スライダーを最大値（10）に設定してください。", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText16.Wrap( -1 )

		bSizer8.Add( self.m_staticText16, 0, wx.ALL, 5 )

		self.m_staticline4 = wx.StaticLine( self.m_scrolledFAQ, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer8.Add( self.m_staticline4, 0, wx.EXPAND |wx.ALL, 5 )

		self.m_staticText171 = wx.StaticText( self.m_scrolledFAQ, wx.ID_ANY, u"Q:　ちっちゃい子とかで、腕接触回避と手首位置合わせの両方を使いたい場合はどうしたらいいの？", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText171.Wrap( -1 )

		bSizer8.Add( self.m_staticText171, 0, wx.ALL, 5 )

		self.m_staticText18 = wx.StaticText( self.m_scrolledFAQ, wx.ID_ANY, u"A:　一旦、腕接触回避のモーションと、手首位置合わせのモーションを別々に生成してください。\n　　腕接触回避のモーションを読み込んだモデルと、\n　　手首位置合わせのモーションを読み込んだモデルを用意します。\n　　腕接触回避の方をベースにして、手首位置合わせで調整したいフレーム間だけ、\n　　手首位置合わせのモーションからコピペしてください。\n　　（手首位置合わせはキーフレームが増えている場合があるためです）", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText18.Wrap( -1 )

		bSizer8.Add( self.m_staticText18, 0, wx.ALL, 5 )


		self.m_scrolledFAQ.SetSizer( bSizer8 )
		self.m_scrolledFAQ.Layout()
		bSizer8.Fit( self.m_scrolledFAQ )
		self.m_note.AddPage( self.m_scrolledFAQ, u"FAQ", False )




		bSizer1.Add( self.m_note, 1, wx.EXPAND, 5 )

		# イベント登録 -----------------------

		# redirect text here
		sys.stdout = self.m_txtConsole

		# Connect Events
		self.m_btnCheck.Bind( wx.EVT_BUTTON, self.OnCheck )
		self.m_btnExec.Bind( wx.EVT_BUTTON, self.OnExec )
		self.m_btnAddLine.Bind( wx.EVT_BUTTON, self.OnAddMorphLine )
		self.m_btnMorphExport.Bind( wx.EVT_BUTTON, self.OnMorphExport )
		self.m_btnMorphImport.Bind( wx.EVT_BUTTON, self.OnMorphImport )
		
		self.Bind(wx.EVT_IDLE, self.OnIdle)

		# Set up event handler for any worker thread results
		EVT_RESULT(self, self.OnResult)
		READ_EVT_RESULT(self, self.OnReadResult)

		# And indicate we don't have a worker thread yet
		self.worker = None
		self.read_workers = []

		# D&Dの実装
		self.m_fileVmd.SetDropTarget(MyFileDropTarget(self, self.m_fileVmd, self.m_staticText9, ".vmd"))
		self.m_fileOrgPmx.SetDropTarget(MyFileDropTarget(self, self.m_fileOrgPmx, self.m_staticText10, ".pmx"))
		self.m_fileRepPmx.SetDropTarget(MyFileDropTarget(self, self.m_fileRepPmx, self.m_staticText11, ".pmx"))
		self.m_fileOutputVmd.SetDropTarget(MyFileDropTarget(self, self.m_fileOutputVmd, self.m_staticText12, ".vmd"))

		# ファイルパス変更時の処理
		self.m_fileVmd.Bind( wx.EVT_FILEPICKER_CHANGED, lambda event: self.OnChangeFile(event, self.m_fileVmd, self.m_staticText9, ".vmd"))
		self.m_fileOrgPmx.Bind( wx.EVT_FILEPICKER_CHANGED, lambda event: self.OnChangeFile(event, self.m_fileOrgPmx, self.m_staticText10, ".pmx"))
		self.m_fileRepPmx.Bind( wx.EVT_FILEPICKER_CHANGED, lambda event: self.OnChangeFile(event, self.m_fileRepPmx, self.m_staticText11, ".pmx"))
		# self.m_fileOutputVmd.Bind( wx.EVT_FILEPICKER_CHANGED, self.OnCreateOutputVmd)

		# ファイル履歴ボタン押下時の処理
		self.m_btnHistoryVmd.Bind(wx.EVT_BUTTON, lambda event: self.OnShowHistory(event, self.file_hitories["vmd"], self.file_hitories["max"], self.m_fileVmd, self.m_staticText9, ".vmd"))
		self.m_btnHistoryOrgPmx.Bind(wx.EVT_BUTTON, lambda event: self.OnShowHistory(event, self.file_hitories["org_pmx"], self.file_hitories["max"], self.m_fileOrgPmx, self.m_staticText10, ".pmx"))
		self.m_btnHistoryRepPmx.Bind(wx.EVT_BUTTON, lambda event: self.OnShowHistory(event, self.file_hitories["rep_pmx"], self.file_hitories["max"], self.m_fileRepPmx, self.m_staticText11, ".pmx"))

		# # # ファイルパス変更時の処理
		# self.m_fileVmd.Bind( wx.EVT_FILEPICKER_CHANGED, lambda event: self.OnLoadFile(event, self.m_fileVmd, self.m_staticText9, ".vmd") )
		# self.m_fileOrgPmx.Bind( wx.EVT_FILEPICKER_CHANGED, lambda event: self.OnLoadFile(event, self.m_fileOrgPmx, self.m_staticText10, ".pmx") )
		# self.m_fileRepPmx.Bind( wx.EVT_FILEPICKER_CHANGED, lambda event: self.OnLoadFile(event, self.m_fileRepPmx, self.m_staticText11, ".pmx") )
		# self.m_fileOutputVmd.Bind( wx.EVT_FILEPICKER_CHANGED, lambda event: self.OnLoadFile(event, self.m_fileOutputVmd, self.m_staticText12, ".vmd") )

		# 読み込み処理は、モーフタブ押下・事前チェック・実行のいずれか押下時のみ、ファイルロードを行う
		# self.m_fileVmd.GetPickerCtrl().Bind( wx.EVT_BUTTON, lambda event: self.OnLoadFile(event, self.m_fileVmd, self.m_staticText9, ".vmd"))
		# self.m_fileVmd.GetTextCtrl().Bind( wx.EVT_KILL_FOCUS, lambda event: self.OnLoadFile(event, self.m_fileVmd, self.m_staticText9, ".vmd"))

		# self.m_fileOrgPmx.GetPickerCtrl().Bind( wx.EVT_FILEPICKER_CHANGED, lambda event: self.OnLoadFile(event, self.m_fileOrgPmx, self.m_staticText10, ".pmx"))
		# self.m_fileOrgPmx.GetTextCtrl().Bind( wx.EVT_KILL_FOCUS, lambda event: self.OnLoadFile(event, self.m_fileOrgPmx, self.m_staticText10, ".pmx"))

		# self.m_fileRepPmx.GetPickerCtrl().Bind( wx.EVT_FILEPICKER_CHANGED, lambda event: self.OnLoadFile(event, self.m_fileRepPmx, self.m_staticText11, ".pmx"))
		# self.m_fileRepPmx.GetTextCtrl().Bind( wx.EVT_KILL_FOCUS, lambda event: self.OnLoadFile(event, self.m_fileRepPmx, self.m_staticText11, ".pmx"))

		# タブ押下時の処理
		self.m_note.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnTabChange)

		# 腕処理ラジオボタンの切り替え
		self.m_radioArmNone.Bind(wx.EVT_RADIOBUTTON, self.OnCreateOutputVmd)
		self.m_radioAvoidance.Bind(wx.EVT_RADIOBUTTON, self.OnCreateOutputVmd)
		self.m_radioArmIK.Bind(wx.EVT_RADIOBUTTON, self.OnCreateOutputVmd)

		# 接触回避のラジオボタンの切り替え
		self.m_radioAvoidanceFinger.Bind(wx.EVT_RADIOBUTTON, self.OnChangeAvoidanceTarget)
		self.m_radioAvoidanceWrist.Bind(wx.EVT_RADIOBUTTON, self.OnChangeAvoidanceTarget)

		# スライダーの変更時
		self.m_sliderHandDistance.Bind(wx.EVT_SCROLL_CHANGED, self.OnChangeArmIKHandDistance)

		# 終了時の処理
		self.Bind(wx.EVT_CLOSE, self.OnClose)

		self.SetSizer( bSizer1 )
		self.Layout()

		self.Centre( wx.BOTH )
	
	def OnShowHistory(self, event, hitories, maxc, target_ctrl, label_ctrl, ext):
		with wx.SingleChoiceDialog(self, "ファイルを選んでダブルクリック、またはOKボタンをクリックしてください。", caption ="ファイル履歴選択",
							choices=hitories[:maxc],
							style=wx.CAPTION|wx.CLOSE_BOX|wx.SYSTEM_MENU|wx.OK|wx.CANCEL|wx.CENTRE) as choiceDialog:

			if choiceDialog.ShowModal() == wx.ID_CANCEL:
				return     # the user changed their mind
			
			target_ctrl.SetPath(choiceDialog.GetStringSelection())
			# ファイル変更処理
			self.OnChangeFile(event, target_ctrl, label_ctrl, ext)

	def OnClose(self, event):
		for h in logger.handlers:
			print("logger.handlers: %s", h)
			# ハンドラを終了させる
			h.flush()
			h.close()
			# ファイルロガーを手放す
			logger.removeHandler(h) 
		# 最後にログを終了させる
		logging.shutdown()

		# print("OnClose")
		if self.worker:
			# スレッドを止める
			self.worker.stop()
			self.worker = None

		# 入力履歴を保存		
		try:
			with open('history.json', 'w') as f:
				json.dump(self.file_hitories, f, ensure_ascii=False)
		except Exception:
			print("保存失敗")
			print(traceback.format_exc())

		self.Destroy()

	def __del__( self ):
		# 最後にログを終了させる
		logging.shutdown()

		# print("__del__")
		if self.worker:
			# スレッドを止める
			self.worker.stop()
			self.worker = None
	
	# 接触回避で処理対象を変えたら、親の選択有効
	def OnChangeAvoidanceTarget(self, event):
		self.m_radioAvoidance.SetValue(1)
	
	# 腕IKでスライダーを変えたら、親の選択有効
	def OnChangeArmIKHandDistance(self, event):
		self.m_radioArmIK.SetValue(1)
	
	def OnTabChange(self, event):
		if self.worker:
			# サイジング実行時はタブ移動不可
			self.m_note.SetSelection(0)
			event.Skip()
			return 

		if self.m_note.GetSelection() == 1:

			if not self.vmd_data or not self.org_pmx_data or not self.rep_pmx_data \
				or (self.vmd_data and self.vmd_data.path != self.m_fileVmd.GetPath()) \
				or (self.org_pmx_data and self.org_pmx_data.path != self.m_fileOrgPmx.GetPath()) \
				or (self.rep_pmx_data and self.rep_pmx_data.path != self.m_fileRepPmx.GetPath()):
				print("モーフタブ表示準備中…少々お待ちください")
				# 一旦メインに戻す
				self.m_note.SetSelection(0)
				# 全件読み込み
				self.LoadFiles(True)

			# if self.vmd_data == None:
			# 	# まだ読み込めていない場合、VMD読み込み
			# 	self.vmd_data = wrapperutils.read_vmd(self.m_fileVmd.GetPath(), self.m_staticText9.GetLabel(), False)

			# if self.org_pmx_data == None:
			# 	# まだ読み込めていない場合、PMX読み込み
			# 	self.org_pmx_data = wrapperutils.read_pmx(self.m_fileOrgPmx.GetPath(), self.m_staticText10.GetLabel(), False)

			# if self.rep_pmx_data == None:
			# 	# まだ読み込めていない場合、PMX読み込み
			# 	self.rep_pmx_data = wrapperutils.read_pmx(self.m_fileRepPmx.GetPath(), self.m_staticText11.GetLabel(), False)

			if not self.vmd_data or not self.org_pmx_data or not self.rep_pmx_data:
				dialog = wx.MessageDialog(self, "ファイルの指定が不足しているため、「モーフ」タブはまだ開けません\n詳しくはメッセージ欄をご確認ください。", 'ファイル指定が不足しています', style=wx.OK)
				dialog.ShowModal()
				dialog.Destroy()

				print("■■■■■■■■■■■■■■■■■")
				print("■　**ERROR**　")
				print("■　「ファイル」タブで以下のいずれかのファイルパスが指定されていないため、「モーフ」タブが開けません。")
				print("■　・調整対象VMDファイル")
				print("■　・モーション作成元モデルPMXファイル")
				print("■　・モーション変換先モデルPMXファイル")
				print("■　既に指定済みの場合、現在読み込み中の可能性があります。")
				print("■　特に長いVMDは読み込みに時間がかかります。")
				print("■　調整に必要な３ファイルすべてを指定して、")
				print("■　「■読み込み成功」のログが出てから、「モーフ」タブを開いてください。")
				print("■■■■■■■■■■■■■■■■■")
				
				self.m_note.SetSelection(0)
			else:
				# モーフタブ新規の場合、モーフプルダウン生成
				if not self.vmd_morphs or not self.rep_morphs:

					logger.debug("vmd_data: %s", self.vmd_data.morphs.keys())
					logger.debug("org_pmx_data: %s", self.org_pmx_data.morphs.keys())
					logger.debug("rep_pmx_data: %s", self.rep_pmx_data.morphs.keys())

					self.vmd_morphs = [""]
					for mk, mkv in self.org_pmx_data.morphs.items():
						if mk in self.vmd_data.morphs.keys() and (len(self.vmd_data.morphs[mk]) > 1 or self.vmd_data.morphs[mk][0].ratio != 0):
							# モーションモーフにキーがあって、かつ初期値が0以外の場合か複数件ある場合
							if mk in self.rep_pmx_data.morphs.keys() and self.rep_pmx_data.morphs[mk].display == True:
								# 置換先にある場合は○
								self.vmd_morphs.append( mkv.get_panel_name() +"○:" + mk)
							else:
								self.vmd_morphs.append( mkv.get_panel_name() +"▲:" + mk)

					# 元モデルにないモーフ追加
					for vmk in self.vmd_data.morphs.keys():
						if vmk not in self.org_pmx_data.morphs.keys() and (len(self.vmd_data.morphs[vmk]) > 1 or self.vmd_data.morphs[vmk][0].ratio != 0):
							if vmk in self.rep_pmx_data.morphs.keys() and self.rep_pmx_data.morphs[vmk].display == True:
								# 置換先にある場合は○
								self.vmd_morphs.append("？●:" + vmk)
							else:
								self.vmd_morphs.append("？▲:" + vmk)

					# 変換先は表示されているモーフのみ対象とする
					self.rep_morphs = [""]
					for rmk, rmv in self.rep_pmx_data.morphs.items():
						if rmv.display == True:
							self.rep_morphs.append( rmv.get_panel_name() +":" + rmk)
					
					# モーフ行追加
					self.AddMorphLine()

					logger.debug("vmd_morphs: %s", self.vmd_morphs)
					logger.debug("rep_morphs: %s", self.rep_morphs)

				self.m_note.SetSelection(1)
					
	def AddMorphLine(self):
		# self.vmd_morphs = ["", "testA"]
		# self.rep_morphs = ["", "testB"]

		# 元モーフ
		if not self.vmd_choices:
			self.vmd_choices = []

		self.vmd_choices.append(wx.Choice( self.m_scrolledMorph, id=wx.ID_ANY, choices=self.vmd_morphs ))
		self.vmd_choices[-1].SetSelection( 0 )
		self.gridMorphSizer.Add( self.vmd_choices[-1], 0, wx.ALL, 5 )
			
		# 矢印
		if not self.arrow_choices:
			self.arrow_choices = []

		self.arrow_choices.append(wx.StaticText( self.m_scrolledMorph, wx.ID_ANY, u"　→　", wx.DefaultPosition, wx.DefaultSize, 0 ))
		self.arrow_choices[-1].Wrap( -1 )
		self.gridMorphSizer.Add( self.arrow_choices[-1], 0, wx.CENTER|wx.ALL, 5 )

		# 変換先モーフ
		if not self.rep_choices:
			self.rep_choices = []

		self.rep_choices.append(wx.Choice( self.m_scrolledMorph, id=wx.ID_ANY, choices=self.rep_morphs ))
		self.rep_choices[-1].SetSelection( 0 )
		self.gridMorphSizer.Add( self.rep_choices[-1], 0, wx.ALL, 5 )

		# 変換割合
		if not self.rep_rates:
			self.rep_rates = []

		self.rep_rates.append(wx.SpinCtrlDouble( self.m_scrolledMorph, id=wx.ID_ANY, size=wx.Size( 80,-1 ), value="1.0", min=0, max=10, initial=1.0, inc=0.01 ))
		self.gridMorphSizer.Add( self.rep_rates[-1], 0, wx.ALL, 5 )

		self.gridMorphSizer.Layout()
		# スクロールバーの表示のためにサイズ調整
		self.gridMorphSizer.FitInside( self.m_scrolledMorph )

		# 前行のイベントの変更
		if len(self.vmd_choices) > 1:
			# self.vmd_choices[-2].Unbind(wx.EVT_CHOICE)
			# self.rep_choices[-2].Unbind(wx.EVT_CHOICE)
			# プルダウンを切り替えたときにファイル出力パスを切り替える
			self.vmd_choices[-1].Bind(wx.EVT_CHOICE, self.OnCreateOutputVmd)
			self.rep_choices[-1].Bind(wx.EVT_CHOICE, self.OnCreateOutputVmd)

		# 新規行のイベントの追加
		self.vmd_choices[-1].Bind(wx.EVT_CHOICE, self.OnFillAddMorphLine)
		self.rep_choices[-1].Bind(wx.EVT_CHOICE, self.OnFillAddMorphLine)

		# self.Refresh()

		# logger.debug("item: %s, size: %s", self.gridMorphSizer.GetItemCount(), self.gridMorphSizer.GetSize())

	def OnFillAddMorphLine(self, event):
		# 一旦出力ファイル設定
		self.OnCreateOutputVmd(wx.EVT_FILEPICKER_CHANGED)

		# logger.debug("OnFillAddMorphLine: vmd_choices: %s, rep_choices: %s", self.vmd_choices[-1].GetSelection(), self.rep_choices[-1].GetSelection() > 0)
		# 最終行のモーフが選択されていたらモーフ行追加
		if self.vmd_choices[-1].GetSelection() > 0 and self.rep_choices[-1].GetSelection() > 0:
			self.AddMorphLine()

	def OnAddMorphLine(self, event):
		# モーフ行追加
		self.AddMorphLine()

	# モーフの組み合わせエクスポート
	def OnMorphExport(self, event):
		# モーフ出力の組み合わせ取得
		vmd_choice_values, rep_choice_values, rep_rate_values = self.create_morph_data()

		# モーフ出力パス
		output_moprh_path = wrapperutils.create_output_morph_path(self.m_fileVmd.GetPath(), self.m_fileOrgPmx.GetPath(), self.m_fileRepPmx.GetPath())

		try:
			with open(output_moprh_path, encoding='cp932', mode='w', newline='') as f:
				cw = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
				cw.writerow(vmd_choice_values)
				cw.writerow(rep_choice_values)
				cw.writerow(rep_rate_values)

				# f.write(','.join([str("\"{0}\"".format(i)) for i in vmd_choice_values]))
				# f.write("\n")
				# f.write(','.join([str("\"{0}\"".format(i)) for i in rep_choice_values]))
				# f.write("\n")
				# f.write(','.join([str(i) for i in rep_rate_values]))
				# f.write("\n")

			print("出力成功: %s" % output_moprh_path)

			dialog = wx.MessageDialog(self, "モーフデータのエクスポートに成功しました \n'%s'" % (output_moprh_path), style=wx.OK)
			dialog.ShowModal()
			dialog.Destroy()

		except Exception:
			dialog = wx.MessageDialog(self, "モーフデータのエクスポートに失敗しました \n'%s'\n\n%s." % (output_moprh_path, traceback.format_exc()), style=wx.OK)
			dialog.ShowModal()
			dialog.Destroy()


	# モーフの組み合わせインポート
	def OnMorphImport(self, event):
		# モーフ入力パス
		input_moprh_path = wrapperutils.create_output_morph_path(self.m_fileVmd.GetPath(), self.m_fileOrgPmx.GetPath(), self.m_fileRepPmx.GetPath())
		input_morph_dir_path = str(Path(input_moprh_path).resolve().parents[0])

		with wx.FileDialog(self, "モーフ組み合わせCSVを読み込む", wildcard="*.csv",
							defaultDir=input_morph_dir_path,
							style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

			if fileDialog.ShowModal() == wx.ID_CANCEL:
				return     # the user changed their mind

			# Proceed loading the file chosen by the user
			pathname = fileDialog.GetPath()
			try:
				with open(pathname, 'r') as f:
					cr = csv.reader(f, delimiter=",", quotechar='"')
					morph_lines = [row for row in cr]

					vmd_choice_values = morph_lines[0]
					rep_choice_values = morph_lines[1]
					rep_rate_values = morph_lines[2]
					
					logger.debug("vmd_choice_values: %s", vmd_choice_values)
					logger.debug("rep_choice_values: %s", rep_choice_values)
					logger.debug("rep_rate_values: %s", rep_rate_values)

					if len(vmd_choice_values) == 0 or len(rep_choice_values) == 0 or len(rep_rate_values) == 0:
						return

					for vcv, rcv, rrv in zip(vmd_choice_values, rep_choice_values, rep_rate_values):
						vc = self.vmd_choices[-1]
						rc = self.rep_choices[-1]
						rr = self.rep_rates[-1]
						# 全件なめる
						for v, c in [(vcv, vc), (rcv, rc)]:
							logger.info("v: %s, c: %s", v, c)
							is_seted = False
							for n in range(c.GetCount()):
								for p in ["目", "眉", "口", "他", "？"]:
									for s in ["", "○", "●", "▲"]:
										# パネル情報を含める
										txt = "{0}{1}:{2}".format(p, s, v)
										# if v == vcv:
										# 	logger.debug("txt: %s, c.GetString(n): %s", txt, c.GetString(n))
										if c.GetString(n).strip() == txt:
											logger.debug("[HIT] txt: %s, c.GetString(n): %s, n: %s", txt, c.GetString(n), n)
											# パネルとモーフ名で一致している場合、採用
											c.SetSelection(n)
											is_seted = True
											break
									if is_seted:
										break
						# 大きさ補正を設定する
						if rrv and wrapperutils.is_decimal(rrv):
							rr.SetValue(rrv)
						# モーフ行追加
						self.AddMorphLine()

			except Exception:
				dialog = wx.MessageDialog(self, "CSVファイルが読み込めませんでした '%s'\n\n%s." % (pathname, traceback.format_exc()), style=wx.OK)
				dialog.ShowModal()
				dialog.Destroy()
	
	# モーフのクリア処理
	def ClearMorph(self):
		self.vmd_morphs = None
		self.rep_morphs = None
		self.vmd_choices = None
		self.rep_choices = None
		self.rep_rates = None
		self.vmd_choice_values = []
		self.rep_choice_values = []
		self.rep_rate_values = []

		logger.debug("ClearMorph: size: %s", self.gridMorphSizer.GetItemCount())
		
		inner_item_count = self.gridMorphSizer.GetItemCount()
		if inner_item_count > 4:
			for n in range(inner_item_count-1, 3, -1):
				# ヘッダを残してプルダウンを削除
				self.gridMorphSizer.Hide(n)
				self.gridMorphSizer.Remove(n)
				logger.debug("** count: %s", self.gridMorphSizer.GetItemCount())
			
			self.gridMorphSizer.Layout()
			self.m_scrolledMorph.Layout()
	
	def LoadFiles(self, is_print=True):
		is_vmd = self.LoadOneFile(self.m_fileVmd, self.m_staticText9, ".vmd", is_print)
		is_org_pmx = self.LoadOneFile(self.m_fileOrgPmx, self.m_staticText10, ".pmx", is_print)
		is_rep_pmx = self.LoadOneFile(self.m_fileRepPmx, self.m_staticText11, ".pmx", is_print)

		# 全ファイル一括チェック
		return is_vmd and is_org_pmx and is_rep_pmx

	def LoadOneFile(self, target_ctrl, label_ctrl, ext, is_print=True):
		# 先頭と末尾の改行は除去
		target_path = target_ctrl.GetPath().strip()
		logger.debug("target_ctrl.GetPath(): %s", target_ctrl.GetPath())

		# 先頭と末尾のダブルクォーテーションは除去
		target_path = re.sub(r'^\\+\"(\w)\\', r'\1:\\', target_ctrl.GetPath())
		target_path = target_path.strip("\"")
		logger.debug("target_path: %s", target_path)

		target_ctrl.SetPath(target_path)

		# メインスレッドで読み込む
		if target_ctrl == self.m_fileVmd:
			if not wrapperutils.is_valid_file(target_ctrl.GetPath(), label_ctrl.GetLabel(), ext, is_print):
				logger.info("vmd_data クリア: %s", target_ctrl.GetPath())
				# 読み込めるファイルではない場合、オブジェクトをクリアして終了
				self.vmd_data = None

				return False
			else:
				logger.info("vmd_data 読み込み: %s", target_ctrl.GetPath())
				# VMD読み込む
				self.vmd_data = wrapperutils.read_vmd(target_ctrl.GetPath(), label_ctrl.GetLabel(), is_print)

				# 出力ファイル以外はモーフも変わるので初期化
				self.ClearMorph()

				return True

		if target_ctrl == self.m_fileOrgPmx:
			if not wrapperutils.is_valid_file(target_ctrl.GetPath(), label_ctrl.GetLabel(), ext, is_print):
				logger.info("org_pmx_data クリア: %s", target_ctrl.GetPath())
				self.org_pmx_data = None

				return False
			else:
				logger.info("org_pmx_data 読み込み: %s", target_ctrl.GetPath())
				# 元PMX読み込む
				self.org_pmx_data = wrapperutils.read_pmx(target_ctrl.GetPath(), label_ctrl.GetLabel(), is_print)

				# 出力ファイル以外はモーフも変わるので初期化
				self.ClearMorph()

				return True

		if target_ctrl == self.m_fileRepPmx:
			if not wrapperutils.is_valid_file(target_ctrl.GetPath(), label_ctrl.GetLabel(), ext, is_print):
				logger.info("rep_pmx_data クリア: %s", target_ctrl.GetPath())
				self.rep_pmx_data = None

				return False
			else:
				logger.info("rep_pmx_data 読み込み: %s", target_ctrl.GetPath())
				# 先PMX読み込む
				self.rep_pmx_data = wrapperutils.read_pmx(target_ctrl.GetPath(), label_ctrl.GetLabel(), is_print)

				# 出力ファイル以外はモーフも変わるので初期化
				self.ClearMorph()

				return True



	# ファイル切り替え処理実行
	def OnChangeFile(self, event, target_ctrl, label_ctrl, ext):
		# 先頭と末尾の改行は除去
		target_path = target_ctrl.GetPath().strip()
		logger.debug("target_ctrl.GetPath(): %s", target_ctrl.GetPath())

		# 先頭と末尾のダブルクォーテーションは除去
		target_path = re.sub(r'^\\+\"(\w)\\', r'\1:\\', target_ctrl.GetPath())
		target_path = target_path.strip("\"")
		logger.debug("target_path: %s", target_path)

		target_ctrl.SetPath(target_path)

		if not target_path or not wrapperutils.is_valid_file(target_ctrl.GetPath(), label_ctrl.GetLabel(), ext, True):
			# 読み込めるファイルではない場合、オブジェクトをクリアして終了

			if target_ctrl == self.m_fileVmd:
				self.vmd_data = None

			if target_ctrl == self.m_fileOrgPmx:
				self.org_pmx_data = None

			if target_ctrl == self.m_fileRepPmx:
				self.rep_pmx_data = None

			event.Skip()
			return

		# 出力ファイル以外はモーフも変わるので初期化
		self.ClearMorph()

		# 一旦出力ファイル設定
		self.OnCreateOutputVmd(event)

		# ファイルの読み込み処理は行わない
		# """Start Computation."""
		# # Trigger the worker thread unless it's already busy
		# # 別スレッドで読み込み処理実行
		# self.read_workers.append(ReadWorkerThread(self, target_ctrl, label_ctrl))

		return

	# 待機中はゲージを動かす
	def OnIdle(self, event):
		if self.worker:
			self.m_Gauge.Pulse()

	# チェックボタン押下
	def OnCheck(self, event):
		self.m_txtConsole.Clear()
		wx.GetApp().Yield()
		
		self.m_Gauge.Pulse()

		# 全件読み込み		
		if not self.LoadFiles(True):
			self.m_Gauge.SetValue(0)
			return False

		# if self.vmd_data == None:
		# 	# まだ読み込めていない場合、VMD読み込み
		# 	self.vmd_data = wrapperutils.read_vmd(self.m_fileVmd.GetPath(), self.m_staticText9.GetLabel(), False)

		# if self.org_pmx_data == None:
		# 	# まだ読み込めていない場合、VMD読み込み
		# 	self.org_pmx_data = wrapperutils.read_pmx(self.m_fileOrgPmx.GetPath(), self.m_staticText10.GetLabel(), False)

		# if self.rep_pmx_data == None:
		# 	# まだ読み込めていない場合、VMD読み込み
		# 	self.rep_pmx_data = wrapperutils.read_pmx(self.m_fileRepPmx.GetPath(), self.m_staticText11.GetLabel(), False)

		# 読み込み処理が終わったらサイジングできるかチェック
		wrapperutils.is_all_sizing(self.vmd_data, self.org_pmx_data, self.rep_pmx_data)

		self.m_Gauge.SetValue(0)

		return True
	
	# モーフデータリスト生成
	def create_morph_data(self):
		logger.info("create_morph_data")
		# モーフ置換文字列リスト生成
		vmd_choice_values = []
		rep_choice_values = []
		rep_rate_values = []

		morph_pair = {}
		logger.info("self.vmd_choices: %s", self.vmd_choices)
		logger.info("self.rep_choices: %s", self.rep_choices)
		logger.info("self.rep_rates: %s", self.rep_rates)
		if self.vmd_choices and self.rep_choices:
			for vc, rc, rr in zip(self.vmd_choices, self.rep_choices, self.rep_rates):
				vc_idx = vc.GetSelection()
				rc_idx = rc.GetSelection()
				logger.info("vc_idx: %s, rc_idx: %s", vc_idx, rc_idx)
				if vc_idx >= 0 and rc_idx >= 0 and len(vc.GetString(vc_idx)) > 0 and len(rc.GetString(rc_idx)) > 0:
					# Prefixを除去する
					vcv = vc.GetString(vc_idx)[3:]
					rcv = rc.GetString(rc_idx)[2:]

					if (vcv,rcv) in morph_pair.keys():
						# 元と先が同じ場合、処理スルー
						continue

					# リストに追加
					vmd_choice_values.append(vcv)
					rep_choice_values.append(rcv)
					# 念のため、丸め
					rep_rate_values.append(round(rr.GetValue(), 10))
					# ペアとして登録する
					morph_pair[(vcv,rcv)] = True							

		logger.info("vmd_choice_values: %s", vmd_choice_values)
		logger.info("rep_choice_values: %s", rep_choice_values)
		logger.info("rep_rate_values: %s", rep_rate_values)
		
		return 	vmd_choice_values, rep_choice_values, rep_rate_values


	# 実行ボタン押下
	def OnExec(self, event):
		if not self.worker:
			self.m_txtConsole.Clear()
			wx.GetApp().Yield()

			# 全件読み込み		
			if not self.LoadFiles(True):
				return False

			# if self.vmd_data == None:
			# 	# まだ読み込めていない場合、VMD読み込み
			# 	self.vmd_data = wrapperutils.read_vmd(self.m_fileVmd.GetPath(), self.m_staticText9.GetLabel(), False)

			# if self.org_pmx_data == None:
			# 	# まだ読み込めていない場合、PMX読み込み
			# 	self.org_pmx_data = wrapperutils.read_pmx(self.m_fileOrgPmx.GetPath(), self.m_staticText10.GetLabel(), False)

			# if self.rep_pmx_data == None:
			# 	# まだ読み込めていない場合、PMX読み込み
			# 	self.rep_pmx_data = wrapperutils.read_pmx(self.m_fileRepPmx.GetPath(), self.m_staticText11.GetLabel(), False)

			if self.vmd_data and self.org_pmx_data and self.rep_pmx_data:
				# 一旦初期化
				self.vmd_choice_values = []
				self.rep_choice_values = []
				self.rep_rate_values = []

				# モーフデータ生成				
				self.vmd_choice_values, self.rep_choice_values, self.rep_rate_values = self.create_morph_data()

				# ファイル入力不可
				self.m_fileVmd.Disable()
				self.m_fileOrgPmx.Disable()
				self.m_fileRepPmx.Disable()
				self.m_fileOutputVmd.Disable()
				# 履歴ボタン押下不可
				self.m_btnHistoryVmd.Disable()
				self.m_btnHistoryOrgPmx.Disable()
				self.m_btnHistoryRepPmx.Disable()
				# 実行ボタン押下不可
				self.m_btnExec.Disable()
				self.m_btnCheck.Disable()

				# 出力ファイルパスがなければ生成
				if not self.m_fileOutputVmd.GetPath():
					output_vmd_path = wrapperutils.create_output_path(self.m_fileVmd.GetPath(), self.m_fileRepPmx.GetPath(), self.m_radioAvoidance.GetValue(), self.m_radioArmIK.GetValue(), (self.vmd_choices and len(self.vmd_choices) > 0))
					if output_vmd_path:
						self.m_fileOutputVmd.SetPath(output_vmd_path)

				# error_path = re.sub(r'\.vmd$', ".log", self.m_fileOutputVmd.GetPath())
				# self.error_file_handlers.append(logging.FileHandler(error_path))
				# self.error_file_handlers = None
				
				# 履歴保持
				if not self.m_fileVmd.GetPath() in self.file_hitories["vmd"]:
					self.file_hitories["vmd"].insert(0, self.m_fileVmd.GetPath())
					self.m_fileVmd.GetTextCtrl().AutoComplete(self.file_hitories["vmd"][:self.file_hitories["max"]])
				
				# 履歴保持
				if not self.m_fileOrgPmx.GetPath() in self.file_hitories["org_pmx"]:
					self.file_hitories["org_pmx"].insert(0, self.m_fileOrgPmx.GetPath())
					self.m_fileOrgPmx.GetTextCtrl().AutoComplete(self.file_hitories["org_pmx"][:self.file_hitories["max"]])
				
				# 履歴保持
				if not self.m_fileRepPmx.GetPath() in self.file_hitories["rep_pmx"]:
					self.file_hitories["rep_pmx"].insert(0, self.m_fileRepPmx.GetPath())
					self.m_fileRepPmx.GetTextCtrl().AutoComplete(self.file_hitories["rep_pmx"][:self.file_hitories["max"]])

				# スレッド実行
				self.worker = ExecWorkerThread(self)
				self.worker.start()
				self.worker.stop_event.set()
		else:
			print("まだ処理が実行中です。終了してから再度実行してください。")

	# スレッド実行結果
	def OnResult(self, event):
		if len(self.read_workers) > 0:
			# 読み込みスレッドが動いている場合、delする
			del self.read_workers[0]
			logger.debug("read_workers: %s", len(self.read_workers))

		# スレッド削除
		self.worker = None
		# 実行ボタン押下許可
		self.m_btnExec.Enable()
		self.m_btnCheck.Enable()
		# ファイル入力可
		self.m_fileVmd.Enable()
		self.m_fileOrgPmx.Enable()
		self.m_fileRepPmx.Enable()
		self.m_fileOutputVmd.Enable()
		# 履歴ボタン押下可
		self.m_btnHistoryVmd.Enable()
		self.m_btnHistoryOrgPmx.Enable()
		self.m_btnHistoryRepPmx.Enable()
		# プログレス非表示
		self.m_Gauge.SetValue(0)
		# モーフ置換配列クリア
		self.vmd_choice_values = []
		self.rep_choice_values = []
		self.rep_rate_values = []
		# 一旦出力ファイル設定
		# self.OnCreateOutputVmd(wx.EVT_FILEPICKER_CHANGED)

	# スレッド実行結果
	def OnReadResult(self, event):
		if len(self.read_workers) > 0:
			# 読み込みスレッドが動いている場合、delする
			del self.read_workers[0]
			logger.debug("read_workers: %s", len(self.read_workers))

		# プログレス非表示
		self.m_Gauge.SetValue(0)
		
	def ShowTraceModel(self, event):
		if wrapperutils.is_valid_file(self.m_fileVmd.GetPath(), "調整対象VMDファイル", ".vmd", False) == False:
			return False
		
		# モデル名表示追加
		model_name = wrapperutils.read_vmd_modelname(self.m_fileVmd.GetPath())
		if model_name == None:
			self.m_vmdTraceTxt.SetValue("　（トレース元モデル取得失敗）")
		else:
			self.m_vmdTraceTxt.SetValue("　（トレース元: "+ model_name +"）")

	# 出力ファイルパスの生成
	def OnCreateOutputVmd(self, event):	
		# print("OnCreateOutputVmd")
		# print("m_fileVmd: %s " % self.m_fileVmd.GetPath())
		# print("m_fileRepPmx: %s " % self.m_fileRepPmx.GetPath())
		# print("self.vmd_choices: %s" % self.vmd_choices)
		# print("(self.vmd_choices and len(self.vmd_choices) > 0): %s" % (self.vmd_choices and len(self.vmd_choices) > 0))
		new_filepath = wrapperutils.create_output_path(self.m_fileVmd.GetPath(), self.m_fileRepPmx.GetPath(), self.m_radioAvoidance.GetValue(), self.m_radioArmIK.GetValue(), (self.vmd_choices and len(self.vmd_choices) > 0))
		# print("new_filepath: %s " % new_filepath)
		if new_filepath is not None:
			self.m_fileOutputVmd.SetPath(new_filepath)

		if self.m_fileVmd.GetPath() != "":
			# VMDファイルパスが空でなければ、トレースモデル名表示
			self.ShowTraceModel(event)
		else:
			self.m_vmdTraceTxt.SetValue("　（調整対象VMD未設定）")

	

# Define notification event for thread completion
EVT_RESULT_ID = wx.NewId()
READ_EVT_RESULT_ID = wx.NewId()

def EVT_RESULT(win, func):
	"""Define Result Event."""
	win.Connect(-1, -1, EVT_RESULT_ID, func)

def READ_EVT_RESULT(win, func):
	"""Define Result Event."""
	win.Connect(-1, -1, READ_EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
	"""Simple event to carry arbitrary result data."""
	def __init__(self, data):
		"""Init Result Event."""
		wx.PyEvent.__init__(self)
		self.SetEventType(EVT_RESULT_ID)

class ReadResultEvent(wx.PyEvent):
	"""Simple event to carry arbitrary result data."""
	def __init__(self, data, target_ctrl, label_ctrl):
		"""Init Result Event."""
		wx.PyEvent.__init__(self)
		self.SetEventType(READ_EVT_RESULT_ID)

		if data:
			print("■解析成功　{0}: {1}".format(label_ctrl.GetLabel(), target_ctrl.GetPath()))
		else:
			print("■解析失敗　{0}: {1}".format(label_ctrl.GetLabel(), target_ctrl.GetPath()))

# Thread class that executes processing
class ReadWorkerThread(Thread):
	"""Worker Thread Class."""
	def __init__(self, notify_window, target_ctrl, label_ctrl):
		"""Init Worker Thread Class."""
		Thread.__init__(self)
		self._notify_window = notify_window
		self._want_abort = 0
		# メイン終了時にもスレッド終了する
		self.daemon = True

		# パラメーター設定
		self.target_ctrl = target_ctrl
		self.label_ctrl = label_ctrl

		# This starts the thread running on creation, but you could
		# also make the GUI thread responsible for calling this
		self.start()

	def run(self):
		"""Run Worker Thread."""
		# This is the code executing in the new thread. Simulation of
		# a long process (well, 10s here) as a simple loop - you will
		# need to structure your processing so that you periodically
		# peek at the abort variable

		if self.target_ctrl == self._notify_window.m_fileVmd:
			logger.info("run vmd")

			# VMD読み込む
			self._notify_window.vmd_data = wrapperutils.read_vmd(self.target_ctrl.GetPath(), self.label_ctrl.GetLabel(), False)

			# Here's where the result would be returned (this is an
			# example fixed result of the number 10, but it could be
			# any Python object)
			wx.PostEvent(self._notify_window, ReadResultEvent(self._notify_window.vmd_data, self.target_ctrl, self.label_ctrl))

		if self.target_ctrl == self._notify_window.m_fileOrgPmx:
			logger.info("run org_pmx_data")

			# 元PMX読み込む
			self._notify_window.org_pmx_data = wrapperutils.read_pmx(self.target_ctrl.GetPath(), self.label_ctrl.GetLabel(), False)

			# Here's where the result would be returned (this is an
			# example fixed result of the number 10, but it could be
			# any Python object)
			wx.PostEvent(self._notify_window, ReadResultEvent(self._notify_window.org_pmx_data, self.target_ctrl, self.label_ctrl))

		if self.target_ctrl == self._notify_window.m_fileRepPmx:
			logger.info("run rep_pmx_data")

			# 先PMX読み込む
			self._notify_window.rep_pmx_data = wrapperutils.read_pmx(self.target_ctrl.GetPath(), self.label_ctrl.GetLabel(), False)

			# Here's where the result would be returned (this is an
			# example fixed result of the number 10, but it could be
			# any Python object)
			wx.PostEvent(self._notify_window, ReadResultEvent(self._notify_window.rep_pmx_data, self.target_ctrl, self.label_ctrl))



	def abort(self):
		"""abort worker thread."""
		# Method for use by main thread to signal an abort
		self._want_abort = 1


# Thread class that executes processing
# http://nobunaga.hatenablog.jp/entry/2016/06/03/204450
class ExecWorkerThread(Thread):
	"""Worker Thread Class."""
	def __init__(self, notify_window):
		"""Init Worker Thread Class."""
		Thread.__init__(self)
		self._notify_window = notify_window
		self._want_abort = 0
		self.stop_event = Event()
		# メイン終了時にもスレッド終了する
		self.daemon = True

	def stop(self):
		self.stop_event.set()

	def run(self):
		"""Run Worker Thread."""
		# This is the code executing in the new thread. Simulation of
		# a long process (well, 10s here) as a simple loop - you will
		# need to structure your processing so that you periodically
		# peek at the abort variable

		# 処理実行
		wrapperutils.exec(
			self._notify_window.vmd_data
			, self._notify_window.org_pmx_data
			, self._notify_window.rep_pmx_data
			, self._notify_window.m_fileVmd.GetPath()
			, self._notify_window.m_fileOrgPmx.GetPath()
			, self._notify_window.m_fileRepPmx.GetPath()
			, self._notify_window.m_fileOutputVmd.GetPath()
			, self._notify_window.m_radioAvoidance.GetValue()
			, self._notify_window.m_radioAvoidanceFinger.GetValue()
			, self._notify_window.m_radioArmIK.GetValue()
			, self._notify_window.m_sliderHandDistance.GetValue()
			, self._notify_window.vmd_choice_values
			, self._notify_window.rep_choice_values			
			, self._notify_window.rep_rate_values
		)

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
		file_name, input_ext = os.path.splitext(os.path.basename(files[0]))
		# logger.debug("D&D file_name: %s, input_ext: %s", file_name, input_ext)

		if input_ext.lower() == self.ext.lower():
			# 拡張子を許容してたらOK
			self.target_ctrl.SetPath(files[0])

			if self.target_ctrl == self.window.m_fileVmd or self.target_ctrl == self.window.m_fileRepPmx:
				# 出力パス生成対象コントロールの場合、VMD生成処理を走らせる
				self.window.OnCreateOutputVmd(wx.EVT_FILEPICKER_CHANGED)
			
			if self.target_ctrl == self.window.m_fileVmd:
				# VMDファイルの場合、トレース元モデル表示
				self.window.ShowTraceModel(wx.EVT_FILEPICKER_CHANGED)

			# オブジェクトクリア
			if self.target_ctrl == self.window.m_fileVmd:
				self.window.vmd_data = None

			if self.target_ctrl == self.window.m_fileOrgPmx:
				self.window.org_pmx_data = None
				
			if self.target_ctrl == self.window.m_fileRepPmx:
				self.window.rep_pmx_data = None

			# # 出力ファイル以外はデータ読み込み
			# if self.target_ctrl != self.window.m_fileOutputVmd:
			# 	self.window.OnLoadFile(wx.EVT_FILEPICKER_CHANGED, self.target_ctrl, self.label_ctrl, self.ext)

			return True
		
		print("{0}の拡張子が正しくありません。設定可能拡張子: {1}".format(self.label_ctrl.GetLabel(), self.ext.lower()))

		# それ以外は不許可
		return False


class FloatSlider(wx.Slider):

	def __init__(self, parent, id, value, minval, maxval, res,
				 label, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.SL_HORIZONTAL,
				 name='floatslider'):
		self._value = value
		self._min = minval
		self._max = maxval
		self._res = res
		self._label = label
		ival, imin, imax = [round(v/res) for v in (value, minval, maxval)]
		self._islider = super(FloatSlider, self)
		self._islider.__init__(
			parent, id, ival, imin, imax, pos=pos, size=size, style=style, name=name
		)
		self.Bind(wx.EVT_SCROLL, self._OnScroll)

	def _OnScroll(self, event):
		ival = self._islider.GetValue()
		imin = self._islider.GetMin()
		imax = self._islider.GetMax()
		if ival == imin:
			self._value = self._min
		elif ival == imax:
			self._value = self._max
		else:
			self._value = ival * self._res
		
		# logger.debug('OnScroll: value=%f, ival=%d', self._value, ival)
		self._label.SetLabel(  u"　（{0}）".format( round(self._value, 3)) )

		event.Skip()

	def GetValue(self):
		return self._value

	def GetMin(self):
		return self._min

	def GetMax(self):
		return self._max

	def GetRes(self):
		return self._res

	def SetValue(self, value):
		self._islider.SetValue(round(value/self._res))
		self._value = value

	def SetMin(self, minval):
		self._islider.SetMin(round(minval/self._res))
		self._min = minval

	def SetMax(self, maxval):
		self._islider.SetMax(round(maxval/self._res))
		self._max = maxval

	def SetRes(self, res):
		self._islider.SetRange(round(self._min/res), round(self._max/res))
		self._islider.SetValue(round(self._value/res))
		self._res = res

	def SetRange(self, minval, maxval):
		self._islider.SetRange(round(minval/self._res), round(maxval/self._res))
		self._min = minval
		self._max = maxval


