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
import os
import time
import re
import csv
import json
import copy
from pathlib import Path
from threading import Thread, Event
import traceback

import wrapperutils
import convert_vmd
import blend_pmx
import convert_csv
import slice_frame_keys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VmdSizing").getChild(__name__)

###########################################################################
## Class VmdSizingForm3
###########################################################################

class VmdSizingForm3 ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"VMDサイジング ローカル版 ver4.02_β03", pos = wx.DefaultPosition, size = wx.Size( 600,600 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
		
		# 初期化(クラス外の変数) -----------------------
		# モーフ置換配列
		self.vmd_choice_values = []
		self.rep_choice_values = []
		self.rep_rate_values = []

		# 分割配列
		self.slice_frame_values = []

		# ファイル解析情報
		self.vmd_data = None
		self.org_pmx_data = None
		self.rep_pmx_data = None
		self.camera_vmd_data = None
		self.camera_pmx_data = None

		# モーフプルダウン
		self.vmd_morphs = None
		self.rep_morphs = None
		self.vmd_choices = None
		self.arrow_choices = None
		self.rep_choices = None
		self.rep_rates = None
		self.slice_frames = None

		# スレッド用
		self.worker = None
		# CSVスレッド用
		self.csv_worker = None
		# VMDスレッド用
		self.vmd_worker = None
		# 補間曲線分割スレッド用
		self.slice_worker = None
		# ブレンドスレッド用
		self.blend_worker = None

		# ファイル履歴
		self.file_hitories = {"vmd":[],"org_pmx":[],"rep_pmx":[],"camera_vmd":[],"camera_pmx":[],"max":20}
		# 履歴JSONファイルがあれば読み込み
		try:
			with open(wrapperutils.get_mypath('history.json'), 'r') as f:
				self.file_hitories = json.load(f)
				# キーが揃っているかチェック
				for key in ["vmd", "org_pmx", "rep_pmx", "camera_vmd", "camera_pmx"]:
					if key not in self.file_hitories:
						self.file_hitories[key] = []
				# 最大件数が揃っているかチェック
				if "max" not in self.file_hitories:
					self.file_hitories["max"] = 20
		except Exception:
			self.file_hitories = {"vmd":[],"org_pmx":[],"rep_pmx":[],"camera_vmd":[],"camera_pmx": [],"max":20}

			# msg = wrapperutils.get_mypath('history.json')
			# msg += "\n"
			# msg += traceback.format_exc()
			# msg += "\n"
			# dialog = wx.MessageDialog(self, msg, style=wx.OK)
			# dialog.ShowModal()
			# dialog.Destroy()


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

		self.m_staticText9 = wx.StaticText( self.m_panelFile, wx.ID_ANY, u"調整対象モーションVMDファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText9.Wrap( -1 )

		bSizer5.Add( self.m_staticText9, 0, wx.ALL, 5 )

		self.m_vmdTraceTxt = wx.TextCtrl( self.m_panelFile, wx.ID_ANY, u"　（調整対象VMD未設定）", wx.DefaultPosition, (300,-1), wx.TE_READONLY|wx.BORDER_NONE|wx.WANTS_CHARS )
		self.m_vmdTraceTxt.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_3DLIGHT ) )
		self.m_vmdTraceTxt.SetToolTip( u"VMDファイルに記録されているモデル名です。選択でコピペ可能です。" )

		bSizer5.Add( self.m_vmdTraceTxt, 0, wx.ALL, 5 )

		bSizer4.Add( bSizer5, 0, wx.EXPAND, 5 )

		bSizer6 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_fileVmd = wx.FilePickerCtrl( self.m_panelFile, wx.ID_ANY, wx.EmptyString, u"調整対象モーションVMDファイルを開く", u"VMDファイル (*.vmd)|*.vmd|すべてのファイル (*.*)|*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		self.m_fileVmd.GetPickerCtrl().SetLabel("開く")
		self.m_fileVmd.SetToolTip( u"調整したいモーションのVMDパスを指定してください。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。" )

		bSizer6.Add( self.m_fileVmd, 1, wx.ALL|wx.EXPAND, 5 )

		self.m_btnHistoryVmd = wx.Button( self.m_panelFile, wx.ID_ANY, u"履歴", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_btnHistoryVmd.SetToolTip( u"これまで指定された調整対象モーションVMDパスが再指定できます。" )
		bSizer6.Add( self.m_btnHistoryVmd, 0, wx.ALL, 5 )

		bSizer4.Add( bSizer6, 0, wx.EXPAND, 5 )

		self.m_staticText10 = wx.StaticText( self.m_panelFile, wx.ID_ANY, u"モーション作成元モデルPMXファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText10.Wrap( -1 )

		bSizer4.Add( self.m_staticText10, 0, wx.ALL, 5 )

		bSizer7 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_fileOrgPmx = wx.FilePickerCtrl( self.m_panelFile, wx.ID_ANY, wx.EmptyString, u"モーション作成元モデルPMXファイルを開く", u"PMXファイル (*.pmx)|*.pmx|すべてのファイル (*.*)|*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		self.m_fileOrgPmx.SetToolTip( u"モーション作成に使用されたモデルのPMXパスを指定してください。\n精度は落ちますが、類似したサイズ・ボーン構造のモデルでも代用できます。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。" )
		self.m_fileOrgPmx.GetPickerCtrl().SetLabel("開く")

		bSizer7.Add( self.m_fileOrgPmx, 1, wx.ALL|wx.EXPAND, 5 )

		self.m_btnHistoryOrgPmx = wx.Button( self.m_panelFile, wx.ID_ANY, u"履歴", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_btnHistoryOrgPmx.SetToolTip( u"これまで指定されたモーション作成元モデルPMXパスが再指定できます。" )
		bSizer7.Add( self.m_btnHistoryOrgPmx, 0, wx.ALL, 5 )

		bSizer4.Add( bSizer7, 0, wx.EXPAND, 5 )

		self.m_staticText11 = wx.StaticText( self.m_panelFile, wx.ID_ANY, u"モーション変換先モデルPMXファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText11.Wrap( -1 )

		bSizer4.Add( self.m_staticText11, 0, wx.ALL, 5 )

		bSizer8 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_fileRepPmx = wx.FilePickerCtrl( self.m_panelFile, wx.ID_ANY, wx.EmptyString, u"モーション変換先モデルPMXファイルを開く", u"PMXファイル (*.pmx)|*.pmx|すべてのファイル (*.*)|*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		self.m_fileRepPmx.GetPickerCtrl().SetLabel("開く")
		self.m_fileRepPmx.SetToolTip( u"実際にモーションを読み込ませたいモデルのPMXパスを指定してください。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。" )

		bSizer8.Add( self.m_fileRepPmx, 1, wx.ALL|wx.EXPAND, 5 )

		self.m_btnHistoryRepPmx = wx.Button( self.m_panelFile, wx.ID_ANY, u"履歴", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_btnHistoryRepPmx.SetToolTip( u"これまで指定されたモーションVMDパスが再指定できます。" )
		bSizer8.Add( self.m_btnHistoryRepPmx, 0, wx.ALL, 5 )

		bSizer4.Add( bSizer8, 0, wx.EXPAND, 5 )

		self.m_staticText12 = wx.StaticText( self.m_panelFile, wx.ID_ANY, u"出力VMDファイル（変更可）", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText12.Wrap( -1 )

		bSizer4.Add( self.m_staticText12, 0, wx.ALL, 5 )

		self.m_fileOutputVmd = wx.FilePickerCtrl( self.m_panelFile, wx.ID_ANY, wx.EmptyString, u"出力VMDファイルを開く", u"VMDファイル (*.vmd)|*.vmd|すべてのファイル (*.*)|*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_OVERWRITE_PROMPT|wx.FLP_SAVE|wx.FLP_USE_TEXTCTRL )
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

		self.m_staticText7 = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"腕を変換先モデルに合わせて調整する事ができます。\n「腕接触回避」と「手首位置合わせ」のいずれか片方しか選択できません。\n腕の動きが、元々のモーションから変わる事があります。いずれもそれなりに時間がかかります。", wx.DefaultPosition, wx.DefaultSize, 0 )
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

		self.m_staticText92 = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"ねんどろ風など、頭身が大幅に異なる場合に、頭部に腕が貫通してしまうのを軽減できます。", wx.DefaultPosition, wx.DefaultSize, 0 )
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

		self.m_staticText93 = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"両手を合わせるなどのモーションを、変換先モデルの手首位置に合わせて調整します。\nそれぞれの距離を調整することで、位置合わせの適用範囲を調整することができます。\nモーションの中で、手首や足がどの辺の位置にいるかは、メッセージ欄に出力されます。", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText93.Wrap( -1 )

		bSizer13.Add( self.m_staticText93, 0, wx.ALL, 5 )

		bSizer13.Add( self.m_radioArmIK, 0, wx.ALL, 5 )

		bSizer16 = wx.BoxSizer( wx.HORIZONTAL )

		# 床位置合わせ
		self.m_checkFloorArmDistance = wx.CheckBox( self.m_panelArm, wx.ID_ANY, u"床との位置合わせも一緒に行う", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_checkFloorArmDistance.SetToolTip( u"手首が床に沈み込んだり浮いてたりする場合、元モデルに合わせて手首の位置を調整します。\nセンター位置も一緒に調整します。" )
		bSizer16.Add( self.m_checkFloorArmDistance, 0, wx.ALL, 5 )

		self.m_staticText94 = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"（", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer16.Add( self.m_staticText94, 0, wx.ALL, 5 )

		# センターを上げる
		self.m_checkFloorArmDistanceUp = wx.CheckBox( self.m_panelArm, wx.ID_ANY, u"センターを上げる", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_checkFloorArmDistanceUp.SetToolTip( u"センターYを上げる処理を許可します。" )
		bSizer16.Add( self.m_checkFloorArmDistanceUp, 0, wx.ALL, 5 )

		# センターを下げる
		self.m_checkFloorArmDistanceDown = wx.CheckBox( self.m_panelArm, wx.ID_ANY, u"センターを下げる", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_checkFloorArmDistanceDown.SetToolTip( u"センターYを下げる処理を許可します。" )
		bSizer16.Add( self.m_checkFloorArmDistanceDown, 0, wx.ALL, 5 )

		self.m_staticText95 = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"）", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer16.Add( self.m_staticText95, 0, wx.ALL, 5 )

		bSizer13.Add( bSizer16, 0, wx.ALL, 5 )

		bSizer15 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText39 = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"手首間の距離　  ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText39.SetToolTip( u"どのくらい手首が近付いた場合に、手首位置合わせを実行するか指定してください。\n値が小さいほど、手首が近付いた時だけ手首位置合わせを行います。\nサイジング実行時、手首間の距離がメッセージ欄に出てますので、参考にしてください。\nスライダーを最大に設定すると、常に手首位置合わせを行います。（両手剣等に便利です）" )
		self.m_staticText39.Wrap( -1 )

		bSizer15.Add( self.m_staticText39, 0, wx.ALL, 5 )

		self.m_vmdHandDistanceTxt = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"（1.7）", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_vmdHandDistanceTxt.SetToolTip( u"現在指定されている手首間の距離です。元モデルの両手首位置がこの範囲内である場合、手首間の位置合わせを行います。" )
		self.m_vmdHandDistanceTxt.Wrap( -1 )

		bSizer15.Add( self.m_vmdHandDistanceTxt, 0, wx.ALL, 5 )

		# 小数点を許可したスライダー
		self.m_sliderHandDistance = FloatSlider( self.m_panelArm, wx.ID_ANY, 1.7, 0, 10, 0.1, self.m_vmdHandDistanceTxt, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		bSizer15.Add( self.m_sliderHandDistance, 1, wx.ALL|wx.EXPAND, 5 )

		bSizer13.Add( bSizer15, 1, wx.ALL|wx.EXPAND, 5 )

		# -------------

		bSizerHandFloor15 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText40 = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"手首と床との距離", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText40.SetToolTip( u"どのくらい手首が床と近付いた場合に、手首と床の位置合わせを実行するか指定してください。\n値が小さいほど、手首が床に近付いた時だけ手首と床の位置合わせを行います。\n距離の単位は、元モデルの手のひらの大きさです。" )
		self.m_staticText40.Wrap( -1 )

		bSizerHandFloor15.Add( self.m_staticText40, 0, wx.ALL, 5 )

		self.m_vmdHandFloorDistanceTxt = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"（1.5）", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_vmdHandFloorDistanceTxt.SetToolTip( u"現在指定されている手首ボーンと床の距離です。元モデルの手首ボーン位置と床がこの範囲内である場合、手首と床の位置合わせを行います。" )
		self.m_vmdHandFloorDistanceTxt.Wrap( -1 )

		bSizerHandFloor15.Add( self.m_vmdHandFloorDistanceTxt, 0, wx.ALL, 5 )

		# 小数点を許可したスライダー
		self.m_sliderHandFloorDistance = FloatSlider( self.m_panelArm, wx.ID_ANY, 1.5, 0, 10, 0.1, self.m_vmdHandFloorDistanceTxt, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		bSizerHandFloor15.Add( self.m_sliderHandFloorDistance, 1, wx.ALL|wx.EXPAND, 5 )
		
		bSizer13.Add( bSizerHandFloor15, 1, wx.ALL|wx.EXPAND, 5 )

		# -------------

		bSizerLegFloor15 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_staticText40 = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"足と床との距離　", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText40.SetToolTip( u"どのくらい足が床と近付いた場合に、足と床の位置合わせを実行するか指定してください。\n値が小さいほど、足が床に近付いた時だけ足と床の位置合わせを行います。\n距離の単位は、元モデルの手のひらの大きさです。" )
		self.m_staticText40.Wrap( -1 )

		bSizerLegFloor15.Add( self.m_staticText40, 0, wx.ALL, 5 )

		self.m_vmdLegFloorDistanceTxt = wx.StaticText( self.m_panelArm, wx.ID_ANY, u"（1.5）", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_vmdLegFloorDistanceTxt.SetToolTip( u"現在指定されている足ボーンと床の距離です。元モデルの足ボーン位置と床がこの範囲内である場合、足と床の位置合わせを行います。" )
		self.m_vmdLegFloorDistanceTxt.Wrap( -1 )

		bSizerLegFloor15.Add( self.m_vmdLegFloorDistanceTxt, 0, wx.ALL, 5 )

		# 小数点を許可したスライダー
		self.m_sliderLegFloorDistance = FloatSlider( self.m_panelArm, wx.ID_ANY, 1.5, 0, 10, 0.1, self.m_vmdLegFloorDistanceTxt, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		bSizerLegFloor15.Add( self.m_sliderLegFloorDistance, 1, wx.ALL|wx.EXPAND, 5 )

		bSizer13.Add( bSizerLegFloor15, 1, wx.ALL|wx.EXPAND, 5 )

		# -------------

		self.m_panelArm.SetSizer( bSizer13 )
		self.m_panelArm.Layout()
		bSizer13.Fit( self.m_panelArm )
		self.m_note.AddPage( self.m_panelArm, u"腕", False )

		# # モーフブレンド ------------------------------------

		# self.m_panelBlend = wx.Panel( self.m_note, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )

		# bSizerBlend3 = wx.BoxSizer( wx.VERTICAL )

		# bSizerBlend4 = wx.BoxSizer( wx.VERTICAL )

		# self.m_blend_staticText7 = wx.StaticText( self.m_panelBlend, wx.ID_ANY, u"指定されたPMXファイルのモーフを徐々に変化させた結果を、PMXファイルとして出力します。\n最小値から最大値までの範囲で増加量ごとに区切ってモーフを登録していきます。\nモーフの組み合わせが多くなると破綻する確率が非常に高くなりますので、その状態での公開は避けてください。", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_blend_staticText7.Wrap( -1 )

		# bSizerBlend4.Add( self.m_blend_staticText7, 0, wx.ALL, 5 )

		# self.m_blend_staticline5 = wx.StaticLine( self.m_panelBlend, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		# bSizerBlend4.Add( self.m_blend_staticline5, 0, wx.EXPAND |wx.ALL, 5 )

		# self.m_blend_staticText1 = wx.StaticText( self.m_panelBlend, wx.ID_ANY, u"PMXファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_blend_staticText1.Wrap( -1 )

		# bSizerBlend4.Add( self.m_blend_staticText1, 0, wx.ALL, 5 )

		# self.m_blend_filePmx = wx.FilePickerCtrl( self.m_panelBlend, wx.ID_ANY, wx.EmptyString, u"PMXファイルを選択してください", u"PMXファイル (*.pmx)|*.pmx|すべてのファイル (*.*)|*.*", wx.DefaultPosition, wx.Size( -1,-1 ), wx.FLP_DEFAULT_STYLE )
		# self.m_blend_filePmx.GetPickerCtrl().SetLabel("開く")
		# bSizerBlend4.Add( self.m_blend_filePmx, 0, wx.ALL|wx.EXPAND, 5 )

		# bSizerBlend5 = wx.BoxSizer( wx.HORIZONTAL )

		# # # 対象パネル
		# # self.m_blend_staticText11 = wx.StaticText( self.m_panelBlend, wx.ID_ANY, u"パネル", wx.DefaultPosition, wx.DefaultSize, 0 )
		# # self.m_blend_staticText11.SetToolTip( u"モーフを生成するパネルを選択してください。" )
		# # self.m_blend_staticText11.Wrap( -1 )
		# # bSizerBlend5.Add( self.m_blend_staticText11, 0, wx.ALL, 5 )

		# # self.m_blend_comboPanel = wx.ComboBox( self.m_panelBlend, id=wx.ID_ANY, value="目", pos=wx.DefaultPosition, size=wx.DefaultSize, choices=["目","眉","口","他"], style=wx.CB_DROPDOWN|wx.CB_READONLY )
		# # bSizerBlend5.Add( self.m_blend_comboPanel, 0, wx.ALL, 5 )

		# # モーフ最小値
		# self.m_blend_staticText8 = wx.StaticText( self.m_panelBlend, wx.ID_ANY, u"最小値", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_blend_staticText8.SetToolTip( u"モーフ増減の最小値です。-10から10の間で設定できます。（小数点可）" )
		# self.m_blend_staticText8.Wrap( -1 )
		# bSizerBlend5.Add( self.m_blend_staticText8, 0, wx.ALL, 5 )

		# self.m_blend_spinMin = wx.SpinCtrlDouble( self.m_panelBlend, id=wx.ID_ANY, size=wx.Size( 80,-1 ), min=-10, max=10, initial=0.0, inc=0.1 )
		# bSizerBlend5.Add( self.m_blend_spinMin, 0, wx.ALL, 5 )

		# # モーフ最大値
		# self.m_blend_staticText9 = wx.StaticText( self.m_panelBlend, wx.ID_ANY, u"最大値", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_blend_staticText9.SetToolTip( u"モーフ増減の最大値です。-10から10の間で設定できます。（小数点可）" )
		# self.m_blend_staticText9.Wrap( -1 )
		# bSizerBlend5.Add( self.m_blend_staticText9, 0, wx.ALL, 5 )

		# self.m_blend_spinMax = wx.SpinCtrlDouble( self.m_panelBlend, id=wx.ID_ANY, size=wx.Size( 80,-1 ), min=-10, max=10, initial=1.0, inc=0.1 )
		# bSizerBlend5.Add( self.m_blend_spinMax, 0, wx.ALL, 5 )

		# # モーフ増加量
		# self.m_blend_staticText10 = wx.StaticText( self.m_panelBlend, wx.ID_ANY, u"増加量", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_blend_staticText10.SetToolTip( u"モーフ増減の増加量です。この増加量分ごとにモーフ組み合わせを生成していきます。0から1の間で設定できます。（小数点可）" )
		# self.m_blend_staticText10.Wrap( -1 )
		# bSizerBlend5.Add( self.m_blend_staticText10, 0, wx.ALL, 5 )

		# self.m_blend_spinInc = wx.SpinCtrlDouble( self.m_panelBlend, id=wx.ID_ANY, size=wx.Size( 80,-1 ), min=0, max=1, initial=0.1, inc=0.1 )
		# bSizerBlend5.Add( self.m_blend_spinInc, 0, wx.ALL, 5 )

		# bSizerBlend4.Add( bSizerBlend5, 0, wx.ALL, 5 )

		# self.m_blend_btnExec = wx.Button( self.m_panelBlend, wx.ID_ANY, u"モーフブレンドVMD生成", wx.DefaultPosition, wx.Size( 200,50 ), 0 )
		# bSizerBlend4.Add( self.m_blend_btnExec, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		# self.m_blend_txtConsole = wx.TextCtrl( self.m_panelBlend, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,370 ), wx.TE_MULTILINE|wx.TE_READONLY|wx.BORDER_NONE|wx.HSCROLL|wx.VSCROLL|wx.WANTS_CHARS )
		# self.m_blend_txtConsole.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_3DLIGHT ) )

		# bSizerBlend4.Add( self.m_blend_txtConsole, 1, wx.ALL|wx.EXPAND, 5 )

		# self.m_blend_Gauge = wx.Gauge( self.m_panelBlend, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
		# self.m_blend_Gauge.SetValue( 0 )
		# bSizerBlend4.Add( self.m_blend_Gauge, 0, wx.ALL|wx.EXPAND, 5 )
	
		# bSizerBlend3.Add( bSizerBlend4, 0, wx.EXPAND, 5 )

		# self.m_panelBlend.SetSizer( bSizerBlend3 )
		# self.m_panelBlend.Layout()
		# bSizerBlend3.Fit( self.m_panelBlend )
		# self.m_note.AddPage( self.m_panelBlend, u"モーフブレンド", False )

		# カメラタブ ------------------------------------

		self.m_panelCamera = wx.Panel( self.m_note, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizerCamera4 = wx.BoxSizer( wx.VERTICAL )

		self.m_camera_staticText7 = wx.StaticText( self.m_panelCamera, wx.ID_ANY, u"指定されたカメラモーションのサイジングを、モーションのサイジングと同時に行えます。", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_camera_staticText7.Wrap( -1 )

		bSizerCamera4.Add( self.m_camera_staticText7, 0, wx.ALL, 5 )

		self.m_camera_staticline5 = wx.StaticLine( self.m_panelCamera, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizerCamera4.Add( self.m_camera_staticline5, 0, wx.EXPAND |wx.ALL, 5 )

		self.m_camera_staticText9 = wx.StaticText( self.m_panelCamera, wx.ID_ANY, u"カメラVMDファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_camera_staticText9.Wrap( -1 )

		bSizerCamera4.Add( self.m_camera_staticText9, 0, wx.ALL, 5 )

		bSizerCamera6 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_camera_fileVmd = wx.FilePickerCtrl( self.m_panelCamera, wx.ID_ANY, wx.EmptyString, u"カメラVMDファイルを開く", u"VMDファイル (*.vmd)|*.vmd|すべてのファイル (*.*)|*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		self.m_camera_fileVmd.GetPickerCtrl().SetLabel("開く")
		self.m_camera_fileVmd.SetToolTip( u"調整したいカメラのVMDパスを指定してください。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。" )

		bSizerCamera6.Add( self.m_camera_fileVmd, 1, wx.ALL|wx.EXPAND, 5 )

		self.m_camera_btnHistoryVmd = wx.Button( self.m_panelCamera, wx.ID_ANY, u"履歴", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_camera_btnHistoryVmd.SetToolTip( u"これまで指定されたカメラVMDパスが再指定できます。" )
		bSizerCamera6.Add( self.m_camera_btnHistoryVmd, 0, wx.ALL, 5 )

		bSizerCamera4.Add( bSizerCamera6, 0, wx.EXPAND, 5 )

		self.m_camera_staticText10 = wx.StaticText( self.m_panelCamera, wx.ID_ANY, u"カメラ作成元モデルPMXファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_camera_staticText10.Wrap( -1 )

		bSizerCamera4.Add( self.m_camera_staticText10, 0, wx.ALL, 5 )

		bSizerCamera7 = wx.BoxSizer( wx.HORIZONTAL )

		self.m_camera_fileOrgPmx = wx.FilePickerCtrl( self.m_panelCamera, wx.ID_ANY, wx.EmptyString, u"カメラ作成元モデルPMXファイルを開く", u"PMXファイル (*.pmx)|*.pmx|すべてのファイル (*.*)|*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		self.m_camera_fileOrgPmx.SetToolTip( u"カメラ作成に使用されたモデルのPMXパスを指定してください。\n未指定の場合、モーション作成元モデルPMXを使用します。\n精度は落ちますが、類似したサイズ・ボーン構造のモデルでも代用できます。\nD&Dでの指定、開くボタンからの指定、履歴からの選択ができます。" )
		self.m_camera_fileOrgPmx.GetPickerCtrl().SetLabel("開く")

		bSizerCamera7.Add( self.m_camera_fileOrgPmx, 1, wx.ALL|wx.EXPAND, 5 )

		self.m_camera_btnHistoryOrgPmx = wx.Button( self.m_panelCamera, wx.ID_ANY, u"履歴", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_camera_btnHistoryOrgPmx.SetToolTip( u"これまで指定されたカメラ作成元モデルPMXパスが再指定できます。" )
		bSizerCamera7.Add( self.m_camera_btnHistoryOrgPmx, 0, wx.ALL, 5 )

		bSizerCamera4.Add( bSizerCamera7, 0, wx.EXPAND, 5 )

		self.m_camera_staticText12 = wx.StaticText( self.m_panelCamera, wx.ID_ANY, u"出力カメラVMDファイル（変更可）", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_camera_staticText12.Wrap( -1 )

		bSizerCamera4.Add( self.m_camera_staticText12, 0, wx.ALL, 5 )

		self.m_camera_fileOutputVmd = wx.FilePickerCtrl( self.m_panelCamera, wx.ID_ANY, wx.EmptyString, u"出力カメラVMDファイルを開く", u"VMDカメラ (*.vmd)|*.vmd|すべてのカメラ (*.*)|*.*", wx.DefaultPosition, wx.DefaultSize, wx.FLP_OVERWRITE_PROMPT|wx.FLP_SAVE|wx.FLP_USE_TEXTCTRL )
		self.m_camera_fileOutputVmd.GetPickerCtrl().SetLabel("開く")
		self.m_camera_fileOutputVmd.SetToolTip( u"調整結果のカメラVMD出力パスを指定してください。\nカメラVMDファイルと変換先PMXファイル名に基づいて自動生成されますが、任意のパスに変更することも可能です。" )

		bSizerCamera4.Add( self.m_camera_fileOutputVmd, 0, wx.ALL|wx.EXPAND, 5 )
	
		self.m_camera_staticline5 = wx.StaticLine( self.m_panelCamera, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizerCamera4.Add( self.m_camera_staticline5, 0, wx.EXPAND |wx.ALL, 5 )

		# 全長Yオフセット
		self.m_camera_staticText8 = wx.StaticText( self.m_panelCamera, wx.ID_ANY, u"全長Yオフセット値", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_camera_staticText8.SetToolTip( u"全長Yオフセット値" )
		self.m_camera_staticText8.Wrap( -1 )
		bSizerCamera4.Add( self.m_camera_staticText8, 0, wx.ALL, 5 )

		self.m_camera_staticText11 = wx.StaticText( self.m_panelCamera, wx.ID_ANY,  u"カメラに映す変換先モデルの全長を調整するオフセット値を指定できます。\n変換先モデルの全長は、頭ボーンにウェイトが100%乗っている頂点のうち最も上にある頂点を計算対象とします。\nそのため、帽子や角など、頭に付属しているパーツで全長に含めたくないパーツがある場合、\nその分をマイナス値で入力してください。\n逆にアホ毛等を全長に含めたい場合、その分をプラス値で入力してください。\n-1000から1000の間で設定できます。（小数点可）", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizerCamera4.Add( self.m_camera_staticText11, 0, wx.ALL, 5 )

		self.m_camera_spinYoffset = wx.SpinCtrlDouble( self.m_panelCamera, id=wx.ID_ANY, size=wx.Size( 80,-1 ), min=-1000, max=1000, initial=0.0, inc=0.1 )
		bSizerCamera4.Add( self.m_camera_spinYoffset, 0, wx.ALL, 5 )

		self.m_panelCamera.SetSizer( bSizerCamera4 )
		self.m_panelCamera.Layout()
		bSizerCamera4.Fit( self.m_panelCamera )
		self.m_note.AddPage( self.m_panelCamera, u"カメラ", False )

		# CSV ------------------------------------

		self.m_panelCsv = wx.Panel( self.m_note, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )

		bSizerCsv3 = wx.BoxSizer( wx.VERTICAL )

		bSizerCsv4 = wx.BoxSizer( wx.VERTICAL )

		self.m_csv_staticText7 = wx.StaticText( self.m_panelCsv, wx.ID_ANY, u"指定されたVMDファイルの解析結果を、ボーン/モーフ/カメラに分けてCSVファイルとして出力します。", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_csv_staticText7.Wrap( -1 )

		bSizerCsv4.Add( self.m_csv_staticText7, 0, wx.ALL, 5 )

		self.m_csv_staticline5 = wx.StaticLine( self.m_panelCsv, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizerCsv4.Add( self.m_csv_staticline5, 0, wx.EXPAND |wx.ALL, 5 )

		self.m_csv_staticText1 = wx.StaticText( self.m_panelCsv, wx.ID_ANY, u"VMDファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_csv_staticText1.Wrap( -1 )

		bSizerCsv4.Add( self.m_csv_staticText1, 0, wx.ALL, 5 )

		self.m_csv_fileVmd = wx.FilePickerCtrl( self.m_panelCsv, wx.ID_ANY, wx.EmptyString, u"VMDファイルを選択してください", u"VMDファイル (*.vmd)|*.vmd|すべてのファイル (*.*)|*.*", wx.DefaultPosition, wx.Size( -1,-1 ), wx.FLP_DEFAULT_STYLE )
		self.m_csv_fileVmd.GetPickerCtrl().SetLabel("開く")
		bSizerCsv4.Add( self.m_csv_fileVmd, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_csv_btnExec = wx.Button( self.m_panelCsv, wx.ID_ANY, u"CSV変換実行", wx.DefaultPosition, wx.Size( 200,50 ), 0 )
		bSizerCsv4.Add( self.m_csv_btnExec, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.m_csv_txtConsole = wx.TextCtrl( self.m_panelCsv, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,370 ), wx.TE_MULTILINE|wx.TE_READONLY|wx.BORDER_NONE|wx.HSCROLL|wx.VSCROLL|wx.WANTS_CHARS )
		self.m_csv_txtConsole.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_3DLIGHT ) )

		bSizerCsv4.Add( self.m_csv_txtConsole, 1, wx.ALL|wx.EXPAND, 5 )

		self.m_csv_Gauge = wx.Gauge( self.m_panelCsv, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
		self.m_csv_Gauge.SetValue( 0 )
		bSizerCsv4.Add( self.m_csv_Gauge, 0, wx.ALL|wx.EXPAND, 5 )
	
		bSizerCsv3.Add( bSizerCsv4, 0, wx.EXPAND, 5 )

		self.m_panelCsv.SetSizer( bSizerCsv3 )
		self.m_panelCsv.Layout()
		bSizerCsv3.Fit( self.m_panelCsv )
		self.m_note.AddPage( self.m_panelCsv, u"CSV", False )

		# VMD ------------------------------------

		self.m_panelVmd = wx.Panel( self.m_note, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )

		bSizerVmd3 = wx.BoxSizer( wx.VERTICAL )

		bSizerVmd4 = wx.BoxSizer( wx.VERTICAL )

		self.m_vmd_staticText7 = wx.StaticText( self.m_panelVmd, wx.ID_ANY, u"指定されたCSVファイル（ボーン＋モーフ or カメラ）を、VMDファイルとして出力します。\nモデルモーション（ボーン・モーフ）とカメラモーション（カメラ）は別々に出力できます。\nCSVのフォーマットは、CSVタブで出力したデータと同じものを定義してください。", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_vmd_staticText7.Wrap( -1 )

		bSizerVmd4.Add( self.m_vmd_staticText7, 0, wx.ALL, 5 )

		self.m_vmd_staticline5 = wx.StaticLine( self.m_panelVmd, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizerVmd4.Add( self.m_vmd_staticline5, 0, wx.EXPAND |wx.ALL, 5 )

		self.m_vmd_staticText1 = wx.StaticText( self.m_panelVmd, wx.ID_ANY, u"CSVファイル（ボーン）", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_vmd_staticText1.Wrap( -1 )

		bSizerVmd4.Add( self.m_vmd_staticText1, 0, wx.ALL, 5 )

		self.m_vmd_fileCsvBone = wx.FilePickerCtrl( self.m_panelVmd, wx.ID_ANY, wx.EmptyString, u"CSVファイルを選択してください", u"CSVファイル (*.csv)|*.csv|すべてのファイル (*.*)|*.*", wx.DefaultPosition, wx.Size( -1,-1 ), wx.FLP_DEFAULT_STYLE )
		self.m_vmd_fileCsvBone.GetPickerCtrl().SetLabel("開く")
		bSizerVmd4.Add( self.m_vmd_fileCsvBone, 0, wx.ALL|wx.EXPAND, 5 )


		self.m_vmd_morph_staticText1 = wx.StaticText( self.m_panelVmd, wx.ID_ANY, u"CSVファイル（モーフ）", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_vmd_morph_staticText1.Wrap( -1 )

		bSizerVmd4.Add( self.m_vmd_morph_staticText1, 0, wx.ALL, 5 )

		self.m_vmd_fileCsvMorph = wx.FilePickerCtrl( self.m_panelVmd, wx.ID_ANY, wx.EmptyString, u"CSVファイルを選択してください", u"CSVファイル (*.csv)|*.csv|すべてのファイル (*.*)|*.*", wx.DefaultPosition, wx.Size( -1,-1 ), wx.FLP_DEFAULT_STYLE )
		self.m_vmd_fileCsvMorph.GetPickerCtrl().SetLabel("開く")
		bSizerVmd4.Add( self.m_vmd_fileCsvMorph, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_vmd_staticline6 = wx.StaticLine( self.m_panelVmd, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizerVmd4.Add( self.m_vmd_staticline6, 0, wx.EXPAND |wx.ALL, 5 )

		self.m_vmd_camera_staticText1 = wx.StaticText( self.m_panelVmd, wx.ID_ANY, u"CSVファイル（カメラ）", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_vmd_camera_staticText1.Wrap( -1 )

		bSizerVmd4.Add( self.m_vmd_camera_staticText1, 0, wx.ALL, 5 )

		self.m_vmd_fileCsvCamera = wx.FilePickerCtrl( self.m_panelVmd, wx.ID_ANY, wx.EmptyString, u"CSVファイルを選択してください", u"CSVファイル (*.csv)|*.csv|すべてのファイル (*.*)|*.*", wx.DefaultPosition, wx.Size( -1,-1 ), wx.FLP_DEFAULT_STYLE )
		self.m_vmd_fileCsvCamera.GetPickerCtrl().SetLabel("開く")
		bSizerVmd4.Add( self.m_vmd_fileCsvCamera, 0, wx.ALL|wx.EXPAND, 5 )



		self.m_vmd_btnExec = wx.Button( self.m_panelVmd, wx.ID_ANY, u"VMD変換実行", wx.DefaultPosition, wx.Size( 200,50 ), 0 )
		bSizerVmd4.Add( self.m_vmd_btnExec, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		self.m_vmd_txtConsole = wx.TextCtrl( self.m_panelVmd, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,370 ), wx.TE_MULTILINE|wx.TE_READONLY|wx.BORDER_NONE|wx.HSCROLL|wx.VSCROLL|wx.WANTS_CHARS )
		self.m_vmd_txtConsole.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_3DLIGHT ) )

		bSizerVmd4.Add( self.m_vmd_txtConsole, 1, wx.ALL|wx.EXPAND, 5 )

		self.m_vmd_Gauge = wx.Gauge( self.m_panelVmd, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
		self.m_vmd_Gauge.SetValue( 0 )
		bSizerVmd4.Add( self.m_vmd_Gauge, 0, wx.ALL|wx.EXPAND, 5 )
	
		bSizerVmd3.Add( bSizerVmd4, 0, wx.EXPAND, 5 )

		self.m_panelVmd.SetSizer( bSizerVmd3 )
		self.m_panelVmd.Layout()
		bSizerVmd3.Fit( self.m_panelVmd )
		self.m_note.AddPage( self.m_panelVmd, u"VMD", False )


		# # 分割タブ ------------------------------------

		# self.m_panelSlice = wx.Panel( self.m_note, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )

		# bSliceSizer8 = wx.BoxSizer( wx.VERTICAL )

		# self.m_panelSliceHeader = wx.Panel( self.m_panelSlice, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		# bSliceSizer10 = wx.BoxSizer( wx.VERTICAL )

		# self.m_slice_staticText132 = wx.StaticText( self.m_panelSliceHeader, wx.ID_ANY, u"VMDのキーを補間曲線を維持しつつ分割する事ができます。\n分割前の補間曲線を維持するため、指定したキーに加えて、更に分割キーが追加される場合があります。\n分割キー値が0の項目はスキップします。", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_slice_staticText132.Wrap( -1 )
		# bSliceSizer10.Add( self.m_slice_staticText132, 0, wx.ALL, 5 )

		# self.m_slice_staticline5 = wx.StaticLine( self.m_panelSliceHeader, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		# bSliceSizer10.Add( self.m_slice_staticline5, 0, wx.EXPAND |wx.ALL, 5 )

		# self.m_slice_staticText1 = wx.StaticText( self.m_panelSliceHeader, wx.ID_ANY, u"VMDファイル", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_slice_staticText1.Wrap( -1 )

		# bSliceSizer10.Add( self.m_slice_staticText1, 0, wx.ALL, 5 )

		# self.m_slice_fileVmd = wx.FilePickerCtrl( self.m_panelSliceHeader, wx.ID_ANY, wx.EmptyString, u"VMDファイルを選択してください", u"VMDファイル (*.vmd)|*.vmd|すべてのファイル (*.*)|*.*", wx.DefaultPosition, wx.Size( -1,-1 ), wx.FLP_DEFAULT_STYLE )
		# self.m_slice_fileVmd.GetPickerCtrl().SetLabel("開く")
		# bSliceSizer10.Add( self.m_slice_fileVmd, 0, wx.ALL|wx.EXPAND, 5 )

		# self.m_slice_btnAddLine = wx.Button( self.m_panelSliceHeader, wx.ID_ANY, u"キー追加", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_slice_btnAddLine.SetToolTip( u"分割フレーム番号欄を追加します。\n上限はありません。" )
		# bSliceSizer10.Add( self.m_slice_btnAddLine, 0, wx.ALIGN_RIGHT|wx.ALL, 5 )

		# self.m_panelSliceHeader.SetSizer( bSliceSizer10 )
		# self.m_panelSliceHeader.Layout()
		# bSliceSizer10.Fit( self.m_panelSliceHeader )

		# bSliceSizer8.Add( self.m_panelSliceHeader, 0, wx.EXPAND |wx.ALL, 5 )

		# self.m_scrolledSlice = wx.ScrolledWindow( self.m_panelSlice, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.FULL_REPAINT_ON_RESIZE|wx.VSCROLL )
		# self.m_scrolledSlice.SetScrollRate( 5, 5 )

		# self.gridSliceSizer = wx.FlexGridSizer( 0, 6, 0, 0 )
		# self.gridSliceSizer.SetFlexibleDirection( wx.BOTH )
		# self.gridSliceSizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		# self.m_scrolledSlice.SetSizer( self.gridSliceSizer )
		# self.m_scrolledSlice.Layout()
		# # self.gridSliceSizer.Fit( self.m_scrolledSlice )
		# bSliceSizer8.Add( self.m_scrolledSlice, 1, wx.ALL|wx.EXPAND|wx.FIXED_MINSIZE, 5 )

		# bSizerSlice4 = wx.BoxSizer( wx.VERTICAL )

		# self.m_slice_btnExec = wx.Button( self.m_panelSlice, wx.ID_ANY, u"分割実行", wx.DefaultPosition, wx.Size( 200,50 ), 0 )
		# bSizerSlice4.Add( self.m_slice_btnExec, 0, wx.ALIGN_CENTER|wx.ALL, 5 )

		# self.m_slice_txtConsole = wx.TextCtrl( self.m_panelSlice, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,120 ), wx.TE_MULTILINE|wx.TE_READONLY|wx.BORDER_NONE|wx.HSCROLL|wx.VSCROLL|wx.WANTS_CHARS )
		# self.m_slice_txtConsole.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_3DLIGHT ) )

		# bSizerSlice4.Add( self.m_slice_txtConsole, 1, wx.ALL|wx.EXPAND, 5 )

		# self.m_slice_Gauge = wx.Gauge( self.m_panelSlice, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
		# self.m_slice_Gauge.SetValue( 0 )
		# bSizerSlice4.Add( self.m_slice_Gauge, 0, wx.ALL|wx.EXPAND, 5 )
	
		# bSliceSizer8.Add( bSizerSlice4, 0, wx.EXPAND, 5 )

		# self.m_panelSlice.SetSizer( bSliceSizer8 )
		# self.m_panelSlice.Layout()
		# bSliceSizer8.Fit( self.m_panelSlice )
		# self.m_note.AddPage( self.m_panelSlice, u"分割", False )

		# ---------------------------

		bSizer1.Add( self.m_note, 1, wx.EXPAND, 5 )

		# イベント登録 -----------------------

		# redirect text here
		sys.stdout = self.m_txtConsole

		# ボタン押下時の処理
		self.m_btnCheck.Bind( wx.EVT_BUTTON, self.OnCheck )
		self.m_btnExec.Bind( wx.EVT_BUTTON, self.OnExec )
		self.m_btnAddLine.Bind( wx.EVT_BUTTON, self.OnAddMorphLine )
		self.m_btnMorphExport.Bind( wx.EVT_BUTTON, self.OnMorphExport )
		self.m_btnMorphImport.Bind( wx.EVT_BUTTON, self.OnMorphImport )
		self.m_csv_btnExec.Bind( wx.EVT_BUTTON, self.OnCsvExec )
		self.m_vmd_btnExec.Bind( wx.EVT_BUTTON, self.OnVmdExec )
		# self.m_blend_btnExec.Bind( wx.EVT_BUTTON, self.OnBlendExec )
		# self.m_slice_btnAddLine.Bind( wx.EVT_BUTTON, self.OnAddSliceCell )
		# self.m_slice_btnExec.Bind( wx.EVT_BUTTON, self.OnSliceExec )
		
		self.Bind(wx.EVT_IDLE, self.OnIdle)

		# Set up event handler for any worker thread results
		EVT_RESULT(self, self.OnResult)
		CSV_EVT_RESULT(self, self.OnCsvResult)
		VMD_EVT_RESULT(self, self.OnVmdResult)
		# SLICE_EVT_RESULT(self, self.OnSliceResult)
		BLEND_EVT_RESULT(self, self.OnBlendResult)

		# And indicate we don't have a worker thread yet
		self.worker = None
		self.csv_worker = None
		self.vmd_worker = None
		# self.slice_worker = None
		self.blend_worker = None

		# D&Dの実装
		self.m_fileVmd.SetDropTarget(MyFileDropTarget(self, self.m_fileVmd, self.m_staticText9, ".vmd"))
		self.m_fileOrgPmx.SetDropTarget(MyFileDropTarget(self, self.m_fileOrgPmx, self.m_staticText10, ".pmx"))
		self.m_fileRepPmx.SetDropTarget(MyFileDropTarget(self, self.m_fileRepPmx, self.m_staticText11, ".pmx"))
		self.m_fileOutputVmd.SetDropTarget(MyFileDropTarget(self, self.m_fileOutputVmd, self.m_staticText12, ".vmd"))
		self.m_camera_fileVmd.SetDropTarget(MyFileDropTarget(self, self.m_camera_fileVmd, self.m_camera_staticText9, ".vmd"))
		self.m_camera_fileOrgPmx.SetDropTarget(MyFileDropTarget(self, self.m_camera_fileOrgPmx, self.m_camera_staticText10, ".pmx"))
		self.m_camera_fileOutputVmd.SetDropTarget(MyFileDropTarget(self, self.m_camera_fileOutputVmd, self.m_camera_staticText12, ".vmd"))
		self.m_csv_fileVmd.SetDropTarget(MyFileDropTarget(self, self.m_csv_fileVmd, self.m_csv_staticText1, ".vmd"))
		self.m_vmd_fileCsvBone.SetDropTarget(MyFileDropTarget(self, self.m_vmd_fileCsvBone, self.m_vmd_staticText1, ".csv"))
		self.m_vmd_fileCsvMorph.SetDropTarget(MyFileDropTarget(self, self.m_vmd_fileCsvMorph, self.m_vmd_morph_staticText1, ".csv"))
		self.m_vmd_fileCsvCamera.SetDropTarget(MyFileDropTarget(self, self.m_vmd_fileCsvCamera, self.m_vmd_camera_staticText1, ".csv"))
		# self.m_slice_fileVmd.SetDropTarget(MyFileDropTarget(self, self.m_slice_fileVmd, self.m_slice_staticText1, ".vmd"))
		# self.m_blend_filePmx.SetDropTarget(MyFileDropTarget(self, self.m_blend_filePmx, self.m_staticText11, ".pmx"))

		# ファイルパス変更時の処理
		self.m_fileVmd.Bind( wx.EVT_FILEPICKER_CHANGED, lambda event: self.OnChangeFile(event, self.m_fileVmd, self.m_staticText9, ".vmd"))
		self.m_fileOrgPmx.Bind( wx.EVT_FILEPICKER_CHANGED, lambda event: self.OnChangeFile(event, self.m_fileOrgPmx, self.m_staticText10, ".pmx"))
		self.m_fileRepPmx.Bind( wx.EVT_FILEPICKER_CHANGED, lambda event: self.OnChangeFile(event, self.m_fileRepPmx, self.m_staticText11, ".pmx"))
		self.m_camera_fileVmd.Bind( wx.EVT_FILEPICKER_CHANGED, lambda event: self.OnChangeFile(event, self.m_camera_fileVmd, self.m_camera_staticText9, ".vmd"))
		self.m_camera_fileOrgPmx.Bind( wx.EVT_FILEPICKER_CHANGED, lambda event: self.OnChangeFile(event, self.m_camera_fileOrgPmx, self.m_camera_staticText10, ".pmx"))

		# ファイル履歴ボタン押下時の処理
		self.m_btnHistoryVmd.Bind(wx.EVT_BUTTON, lambda event: self.OnShowHistory(event, self.file_hitories["vmd"], self.file_hitories["max"]+1, self.m_fileVmd, self.m_staticText9, ".vmd"))
		self.m_btnHistoryOrgPmx.Bind(wx.EVT_BUTTON, lambda event: self.OnShowHistory(event, self.file_hitories["org_pmx"], self.file_hitories["max"]+1, self.m_fileOrgPmx, self.m_staticText10, ".pmx"))
		self.m_btnHistoryRepPmx.Bind(wx.EVT_BUTTON, lambda event: self.OnShowHistory(event, self.file_hitories["rep_pmx"], self.file_hitories["max"]+1, self.m_fileRepPmx, self.m_staticText11, ".pmx"))
		self.m_camera_btnHistoryVmd.Bind(wx.EVT_BUTTON, lambda event: self.OnShowHistory(event, self.file_hitories["camera_vmd"], self.file_hitories["max"]+1, self.m_camera_fileVmd, self.m_camera_staticText9, ".vmd"))
		self.m_camera_btnHistoryOrgPmx.Bind(wx.EVT_BUTTON, lambda event: self.OnShowHistory(event, self.file_hitories["camera_pmx"], self.file_hitories["max"]+1, self.m_camera_fileOrgPmx, self.m_camera_staticText10, ".pmx"))

		# ファイル入力欄で全選択イベント
		self.m_fileVmd.GetTextCtrl().Bind(wx.EVT_CHAR, lambda event: self.OnFileSelectAll(event, self.m_fileVmd.GetTextCtrl()))
		self.m_fileOrgPmx.GetTextCtrl().Bind(wx.EVT_CHAR, lambda event: self.OnFileSelectAll(event, self.m_fileOrgPmx.GetTextCtrl()))
		self.m_fileRepPmx.GetTextCtrl().Bind(wx.EVT_CHAR, lambda event: self.OnFileSelectAll(event, self.m_fileRepPmx.GetTextCtrl()))
		self.m_fileOutputVmd.GetTextCtrl().Bind(wx.EVT_CHAR, lambda event: self.OnFileSelectAll(event, self.m_fileOutputVmd.GetTextCtrl()))
		self.m_camera_fileVmd.GetTextCtrl().Bind(wx.EVT_CHAR, lambda event: self.OnFileSelectAll(event, self.m_camera_fileVmd.GetTextCtrl()))
		self.m_camera_fileOrgPmx.GetTextCtrl().Bind(wx.EVT_CHAR, lambda event: self.OnFileSelectAll(event, self.m_camera_fileOrgPmx.GetTextCtrl()))
		self.m_csv_fileVmd.GetTextCtrl().Bind(wx.EVT_CHAR, lambda event: self.OnFileSelectAll(event, self.m_csv_fileVmd.GetTextCtrl()))
		self.m_vmd_fileCsvBone.GetTextCtrl().Bind(wx.EVT_CHAR, lambda event: self.OnFileSelectAll(event, self.m_vmd_fileCsvBone.GetTextCtrl()))
		self.m_vmd_fileCsvMorph.GetTextCtrl().Bind(wx.EVT_CHAR, lambda event: self.OnFileSelectAll(event, self.m_vmd_fileCsvMorph.GetTextCtrl()))
		self.m_vmd_fileCsvCamera.GetTextCtrl().Bind(wx.EVT_CHAR, lambda event: self.OnFileSelectAll(event, self.m_vmd_fileCsvCamera.GetTextCtrl()))
		# self.m_slice_fileVmd.GetTextCtrl().Bind(wx.EVT_CHAR, lambda event: self.OnFileSelectAll(event, self.m_slice_fileVmd.GetTextCtrl()))
		# self.m_blend_filePmx.GetTextCtrl().Bind(wx.EVT_CHAR, lambda event: self.OnFileSelectAll(event, self.m_blend_filePmx.GetTextCtrl()))
		# メッセージ欄も全選択可とする
		self.m_txtConsole.Bind(wx.EVT_CHAR, lambda event: self.OnFileSelectAll(event, self.m_txtConsole))

		# タブ押下時の処理
		self.m_note.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnTabChange)

		# 腕処理ラジオボタンの切り替え
		self.m_radioArmNone.Bind(wx.EVT_RADIOBUTTON, self.OnChangeArmRadio)
		self.m_radioAvoidance.Bind(wx.EVT_RADIOBUTTON, self.OnChangeArmRadio)
		self.m_radioArmIK.Bind(wx.EVT_RADIOBUTTON, self.OnChangeArmRadio)

		# 床位置合わせのチェックボックス切り替え
		self.m_checkFloorArmDistance.Bind(wx.EVT_CHECKBOX, self.OnChangeFloorArmDistance)

		# 接触回避のラジオボタンの切り替え
		self.m_radioAvoidanceFinger.Bind(wx.EVT_RADIOBUTTON, self.OnChangeAvoidanceTarget)
		self.m_radioAvoidanceWrist.Bind(wx.EVT_RADIOBUTTON, self.OnChangeAvoidanceTarget)

		# スライダーの変更時
		self.m_sliderHandDistance.Bind(wx.EVT_SCROLL_CHANGED, self.OnChangeArmIKHandDistance)

		# スライダーの変更時
		self.m_sliderHandFloorDistance.Bind(wx.EVT_SCROLL_CHANGED, self.OnChangeArmIKFloorDistance)
		self.m_sliderLegFloorDistance.Bind(wx.EVT_SCROLL_CHANGED, self.OnChangeArmIKFloorDistance)

		# # 分割フレームのセル追加
		# self.AddSliceCell()

		# 終了時の処理
		self.Bind(wx.EVT_CLOSE, self.OnClose)

		self.SetSizer( bSizer1 )
		self.Layout()

		self.Centre( wx.BOTH )

	# ファイル入力欄で全選択イベント
	def OnFileSelectAll(self, event, target_ctrl):
		keyInput = event.GetKeyCode()
		if keyInput == 1:  # 1 stands for 'ctrl+a'
			target_ctrl.SelectAll()
		event.Skip()		

	def OnCsvExec( self, event ):
		self.DisableInput()

		self.m_csv_txtConsole.Clear()
		wx.GetApp().Yield()

		# CSVコンソールに切り替え
		sys.stdout = self.m_csv_txtConsole

		self.DisableInput()

		if wrapperutils.is_valid_file(self.m_csv_fileVmd.GetPath(), "VMDファイル", ".vmd", True) == False:

			self.EnableInput()
			# プログレス非表示
			self.m_csv_Gauge.SetValue(0)

			# 元に戻す
			sys.stdout = self.m_txtConsole

			event.Skip()
			return

		if not self.csv_worker:
			# スレッド実行
			self.csv_worker = CsvWorkerThread(self)
			self.csv_worker.start()
			self.csv_worker.stop_event.set()
		else:
			print("まだ処理が実行中です。終了してから再度実行してください。")

			# 元に戻す
			sys.stdout = self.m_txtConsole


	def OnVmdExec( self, event ):
		self.DisableInput()

		self.m_vmd_txtConsole.Clear()
		wx.GetApp().Yield()

		# VMDコンソールに切り替え
		sys.stdout = self.m_vmd_txtConsole

		self.DisableInput()

		if len(self.m_vmd_fileCsvBone.GetPath()) == 0 \
			and len(self.m_vmd_fileCsvMorph.GetPath()) == 0 \
			and len(self.m_vmd_fileCsvCamera.GetPath()) == 0:

			print("■■■■■■■■■■■■■■■■■")
			print("■　**ERROR**　")
			print("■　CSVファイルが1件も指定されていません。")
			print("■■■■■■■■■■■■■■■■■")

			self.EnableInput()
			# プログレス非表示
			self.m_vmd_Gauge.SetValue(0)

			# 元に戻す
			sys.stdout = self.m_txtConsole

			event.Skip()
			return

		if (len(self.m_vmd_fileCsvBone.GetPath()) > 0 and \
			wrapperutils.is_valid_file(self.m_vmd_fileCsvBone.GetPath(), "ボーンCSVファイル", ".csv", True) == False) or \
			(len(self.m_vmd_fileCsvMorph.GetPath()) > 0 and \
			wrapperutils.is_valid_file(self.m_vmd_fileCsvMorph.GetPath(), "モーフCSVファイル", ".csv", True) == False) or \
			(len(self.m_vmd_fileCsvCamera.GetPath()) > 0 and \
			wrapperutils.is_valid_file(self.m_vmd_fileCsvCamera.GetPath(), "カメラCSVファイル", ".csv", True) == False):

			self.EnableInput()
			# プログレス非表示
			self.m_vmd_Gauge.SetValue(0)

			# 元に戻す
			sys.stdout = self.m_txtConsole

			event.Skip()
			return

		if not self.vmd_worker:
			# スレッド実行
			self.vmd_worker = VmdWorkerThread(self)
			self.vmd_worker.start()
			self.vmd_worker.stop_event.set()
		else:
			print("まだ処理が実行中です。終了してから再度実行してください。")

			# 元に戻す
			sys.stdout = self.m_txtConsole


	def OnSliceExec( self, event ):
		self.DisableInput()

		self.m_slice_txtConsole.Clear()
		wx.GetApp().Yield()

		# 分割コンソールに切り替え
		sys.stdout = self.m_slice_txtConsole

		self.DisableInput()

		if wrapperutils.is_valid_file(self.m_slice_fileVmd.GetPath(), "VMDファイル", ".vmd", True) == False:

			self.EnableInput()
			# プログレス非表示
			self.m_slice_Gauge.SetValue(0)

			# 元に戻す
			sys.stdout = self.m_txtConsole

			event.Skip()
			return

		if not self.slice_worker:
			# 分割キーデータ生成				
			self.slice_frame_values = self.create_slice_frame_data()

			# スレッド実行
			self.slice_worker = SliceWorkerThread(self)
			self.slice_worker.start()
			self.slice_worker.stop_event.set()
		else:
			print("まだ処理が実行中です。終了してから再度実行してください。")

			# 元に戻す
			sys.stdout = self.m_txtConsole


	def OnShowHistory(self, event, hitories, maxc, target_ctrl, label_ctrl, ext):
		# 入力行を伸ばす
		hs = copy.deepcopy(hitories)
		hs.extend(["" for x in range(maxc)])

		with wx.SingleChoiceDialog(self, "ファイルを選んでダブルクリック、またはOKボタンをクリックしてください。", caption ="ファイル履歴選択",
							choices=hs[:maxc],
							style=wx.CAPTION|wx.CLOSE_BOX|wx.SYSTEM_MENU|wx.OK|wx.CANCEL|wx.CENTRE) as choiceDialog:

			if choiceDialog.ShowModal() == wx.ID_CANCEL:
				return     # the user changed their mind
			
			# ファイルピッカーに選択したパスを設定
			target_ctrl.SetPath(choiceDialog.GetStringSelection())
			target_ctrl.UpdatePickerFromTextCtrl()
			target_ctrl.SetInitialDirectory(wrapperutils.get_dir_path(choiceDialog.GetStringSelection()))

			# ファイル変更処理
			self.OnChangeFile(wx.FileDirPickerEvent(), target_ctrl, label_ctrl, ext)

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
		
		if self.csv_worker:
			# スレッドを止める
			self.csv_worker.stop()
			self.csv_worker = None

		# 入力履歴を保存		
		try:
			with open(wrapperutils.get_mypath('history.json'), 'w') as f:
				json.dump(self.file_hitories, f, ensure_ascii=False)
		except Exception:
			print("history.json保存失敗")
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
	
		if self.csv_worker:
			# スレッドを止める
			self.csv_worker.stop()
			self.csv_worker = None

		if self.vmd_worker:
			# スレッドを止める
			self.vmd_worker.stop()
			self.vmd_worker = None

	# 接触回避で処理対象を変えたら、親の選択有効
	def OnChangeAvoidanceTarget(self, event):
		self.m_radioAvoidance.SetValue(1)
		# パス再設定
		self.OnCreateOutputVmd(event)
	
	# 腕IKでスライダーを変えたら、親の選択有効
	def OnChangeArmIKHandDistance(self, event):
		self.m_radioArmIK.SetValue(1)
		# パス再設定
		self.OnCreateOutputVmd(event)
	
	# 腕IKでスライダーを変えたら、親の選択有効
	def OnChangeArmIKFloorDistance(self, event):
		self.m_radioArmIK.SetValue(1)
		self.m_checkFloorArmDistance.SetValue(1)
		# センターYは両方有効
		self.m_checkFloorArmDistanceUp.SetValue(self.m_checkFloorArmDistance.GetValue())
		self.m_checkFloorArmDistanceDown.SetValue(self.m_checkFloorArmDistance.GetValue())
		# パス再設定
		self.OnCreateOutputVmd(event)

	# 腕IKで床にチェックを入れたら、親の選択有効
	def OnChangeFloorArmDistance(self, event):
		self.m_radioArmIK.SetValue(1)
		# センターYは両方有効
		self.m_checkFloorArmDistanceUp.SetValue(self.m_checkFloorArmDistance.GetValue())
		self.m_checkFloorArmDistanceDown.SetValue(self.m_checkFloorArmDistance.GetValue())
		# パス再設定
		self.OnCreateOutputVmd(event)
	
	def OnChangeArmRadio(self, event):
		if not self.m_radioArmIK.GetValue():
			# 腕IKの選択を外した場合、床位置合わせチェックOFF
			self.m_checkFloorArmDistance.SetValue(0)
			# センターYは両方有効
			self.m_checkFloorArmDistanceUp.SetValue(0)
			self.m_checkFloorArmDistanceDown.SetValue(0)

		# パス再設定
		self.OnCreateOutputVmd(event)

	def OnTabChange(self, event):
		if self.worker:
			# サイジング実行時はタブ移動不可
			self.m_note.SetSelection(0)
			event.Skip()
			return 

		# if self.blend_worker:
		# 	# ブレンドモーフ生成時はタブ移動不可
		# 	self.m_note.SetSelection(3)
		# 	event.Skip()
		# 	return 

		if self.csv_worker:
			# CSVコンバート時はタブ移動不可
			self.m_note.SetSelection(4)
			event.Skip()
			return 

		if self.vmd_worker:
			# VMDコンバート時はタブ移動不可
			self.m_note.SetSelection(5)
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

		# # パス再設定
		# self.OnCreateOutputVmd(event)
		# self.OnCreateOutputCameraVmd(event)

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
		input_morph_dir_path = wrapperutils.get_dir_path(input_moprh_path)

		with wx.FileDialog(self, "モーフ組み合わせCSVを読み込む", wildcard=u"CSVファイル (*.csv)|*.csv|すべてのファイル (*.*)|*.*",
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
							logger.debug("v: %s, c: %s", v, c)
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

		# パス再設定
		self.OnCreateOutputVmd(wx.EVT_TEXT)


	def AddSliceCell(self):
		# フレーム番号
		if not self.slice_frames:
			self.slice_frames = []

		self.slice_frames.append(wx.SpinCtrl( self.m_scrolledSlice, id=wx.ID_ANY, size=wx.Size( 80,-1 ), value="0", min=0, initial=1 ))
		self.gridSliceSizer.Add( self.slice_frames[-1], 0, wx.ALL, 5 )

		self.gridSliceSizer.Layout()
		# スクロールバーの表示のためにサイズ調整
		self.gridSliceSizer.FitInside( self.m_scrolledSlice )

	def OnAddSliceCell(self, event):
		# フレーム列追加
		self.AddSliceCell()

	
	def LoadFiles(self, is_print=True):
		is_pre_vmd = self.PreLoadOneFile(self.m_fileVmd, self.m_staticText9, ".vmd", is_print)
		is_pre_org_pmx = self.PreLoadOneFile(self.m_fileOrgPmx, self.m_staticText10, ".pmx", is_print)
		is_pre_rep_pmx = self.PreLoadOneFile(self.m_fileRepPmx, self.m_staticText11, ".pmx", is_print)
		# カメラは初期値OKとする
		is_pre_camera_vmd = True
		is_pre_camera_pmx = True
		if self.m_camera_fileVmd.GetPath():
			# パスが指定してあってNGの場合、結果保持
			is_pre_camera_vmd = self.PreLoadOneFile(self.m_camera_fileVmd, self.m_camera_staticText9, ".vmd", is_print)
		if self.m_camera_fileOrgPmx.GetPath():
			# パスが指定してあってNGの場合、結果保持
			is_pre_camera_pmx = self.PreLoadOneFile(self.m_camera_fileOrgPmx, self.m_camera_staticText10, ".pmx", is_print)

		if is_pre_vmd and is_pre_org_pmx and is_pre_rep_pmx and is_pre_camera_vmd and is_pre_camera_pmx:
			is_vmd = self.LoadOneFile(self.m_fileVmd, self.m_staticText9, ".vmd", is_print)
			is_org_pmx = self.LoadOneFile(self.m_fileOrgPmx, self.m_staticText10, ".pmx", is_print)
			is_rep_pmx = self.LoadOneFile(self.m_fileRepPmx, self.m_staticText11, ".pmx", is_print)

			is_camera_vmd = True
			if self.m_camera_fileVmd.GetPath():
				is_camera_vmd = self.LoadOneFile(self.m_camera_fileVmd, self.m_camera_staticText9, ".vmd", is_print)

			is_camera_pmx = True
			if self.m_camera_fileOrgPmx.GetPath():
				is_camera_pmx = self.LoadOneFile(self.m_camera_fileOrgPmx, self.m_camera_staticText10, ".pmx", is_print)

			# 全ファイル一括チェック
			return is_vmd and is_org_pmx and is_rep_pmx and is_camera_vmd and is_camera_pmx \
				and self.checkOutputVmdPath(self.m_fileOutputVmd, self.m_staticText12) \
				and ((not self.m_camera_fileOutputVmd) or \
					(self.m_camera_fileOutputVmd and self.checkOutputVmdPath(self.m_camera_fileOutputVmd, self.m_camera_staticText12)))
		
		return False
	
	def checkOutputVmdPath(self, target_ctrl, label_ctrl):
		if not target_ctrl.GetPath():
			# ファイルパスがない場合、生成
			self.OnCreateOutputVmd(wx.EVT_FILEPICKER_CHANGED)
		
		label_text = label_ctrl.GetLabel().strip("（変更可）")

		if len(target_ctrl.GetPath()) >= 255 and os.name == "nt":
			print("■■■■■■■■■■■■■■■■■")
			print("■　**ERROR**　")
			print("■　"+ label_text +"がWindowsの制限を超えているため、処理を中断します。")
			print("■　"+ label_text +"パス: "+ target_ctrl.GetPath() )
			print("■■■■■■■■■■■■■■■■■")
			return False
		
		logger.debug("文字超制限OK")
		
		# 親ディレクトリ取得
		dir_path = wrapperutils.get_dir_path(target_ctrl.GetPath())

		logger.debug("ディレクトリパス生成")

		if not dir_path or not os.path.exists(dir_path) or not os.path.isdir(dir_path):
			print("■■■■■■■■■■■■■■■■■")
			print("■　**ERROR**　")
			print("■　"+ label_text +"パスのフォルダ構成が正しくないため、処理を中断します。")
			print("■　"+ label_text +"パス: "+ target_ctrl.GetPath() )
			print("■■■■■■■■■■■■■■■■■")
			return False

		if dir_path and not os.access(dir_path, os.W_OK):
			print("■■■■■■■■■■■■■■■■■")
			print("■　**ERROR**　")
			print("■　"+ label_text +"パスの親フォルダに書き込み権限がありません。")
			print("■　"+ label_text +"パス: "+ target_ctrl.GetPath() )
			print("■■■■■■■■■■■■■■■■■")
			return False

		if target_ctrl.GetPath() and os.path.exists(target_ctrl.GetPath()) and not os.access(target_ctrl.GetPath(), os.W_OK):
			print("■■■■■■■■■■■■■■■■■")
			print("■　**ERROR**　")
			print("■　"+ label_text +"パスに書き込み権限がありません。")
			print("■　"+ label_text +"パス: "+ target_ctrl.GetPath() )
			print("■■■■■■■■■■■■■■■■■")
			return False

		return True

	def PreLoadOneFile(self, target_ctrl, label_ctrl, ext, is_print=True):
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
				logger.debug("vmd_data クリア: %s", target_ctrl.GetPath())
				# 読み込めるファイルではない場合、オブジェクトをクリアして終了
				self.vmd_data = None
				self.camera_vmd_data = None

				if is_print:
					print("%s 読み込み失敗: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))

				return False
			else:
				return True

		if target_ctrl == self.m_fileOrgPmx:
			if not wrapperutils.is_valid_file(target_ctrl.GetPath(), label_ctrl.GetLabel(), ext, is_print):
				logger.debug("org_pmx_data クリア: %s", target_ctrl.GetPath())
				self.org_pmx_data = None
				self.camera_pmx_data = None

				if is_print:
					print("%s 読み込み失敗: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))

				return False
			else:
				return True

		if target_ctrl == self.m_fileRepPmx:
			if not wrapperutils.is_valid_file(target_ctrl.GetPath(), label_ctrl.GetLabel(), ext, is_print):
				logger.debug("rep_pmx_data クリア: %s", target_ctrl.GetPath())
				self.rep_pmx_data = None

				if is_print:
					print("%s 読み込み失敗: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))

				return False
			else:
				return True

		# メインスレッドで読み込む
		if target_ctrl == self.m_camera_fileVmd:
			if not wrapperutils.is_valid_file(target_ctrl.GetPath(), label_ctrl.GetLabel(), ext, is_print):
				logger.debug("camera_vmd_data クリア: %s", target_ctrl.GetPath())
				# 読み込めるファイルではない場合、オブジェクトをクリアして終了
				self.camera_vmd_data = None

				if is_print:
					print("%s 読み込み失敗: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))

				return False
			else:
				return True

		if target_ctrl == self.m_camera_fileOrgPmx:
			if not wrapperutils.is_valid_file(target_ctrl.GetPath(), label_ctrl.GetLabel(), ext, is_print):
				logger.debug("camera_pmx_data クリア: %s", target_ctrl.GetPath())
				self.camera_pmx_data = None

				if is_print:
					print("%s 読み込み失敗: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))

				return False
			else:
				return True

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
				logger.debug("vmd_data クリア: %s", target_ctrl.GetPath())
				# 読み込めるファイルではない場合、オブジェクトをクリアして終了
				self.vmd_data = None
				self.camera_vmd_data = None			

				if is_print:
					print("%s 読み込み失敗: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))

				return False
			else:
				logger.debug("vmd_data 読み込み: %s", target_ctrl.GetPath())
				# VMD読み込む
				new_vmd_data = wrapperutils.read_vmd(target_ctrl.GetPath(), label_ctrl.GetLabel(), is_print)

				if not self.vmd_data or not new_vmd_data or (self.vmd_data and new_vmd_data and self.vmd_data.digest != new_vmd_data.digest):
					# ハッシュが違う場合、データが違うとみなして更新
					self.vmd_data = new_vmd_data
					self.camera_vmd_data = None

					# 出力ファイル以外はモーフも変わるので初期化
					self.ClearMorph()

				if is_print:
					if new_vmd_data:
						print("%s 読み込み成功: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))
					else:
						print("%s 読み込み失敗: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))
						return False

				return True

		if target_ctrl == self.m_fileOrgPmx:
			if not wrapperutils.is_valid_file(target_ctrl.GetPath(), label_ctrl.GetLabel(), ext, is_print):
				logger.debug("org_pmx_data クリア: %s", target_ctrl.GetPath())
				self.org_pmx_data = None
				self.camera_pmx_data = None

				if is_print:
					print("%s 読み込み失敗: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))

				return False
			else:
				logger.debug("org_pmx_data 読み込み: %s", target_ctrl.GetPath())
				# 元PMX読み込む
				new_org_pmx_data = wrapperutils.read_pmx(target_ctrl.GetPath(), label_ctrl.GetLabel(), is_print)

				if not self.org_pmx_data or not new_org_pmx_data or (self.org_pmx_data and new_org_pmx_data and self.org_pmx_data.digest != new_org_pmx_data.digest):
					# ハッシュが違う場合、データが違うとみなして更新
					self.org_pmx_data = new_org_pmx_data

					# 出力ファイル以外はモーフも変わるので初期化
					self.ClearMorph()

				if is_print:
					if new_org_pmx_data:
						print("%s 読み込み成功: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))
					else:
						print("%s 読み込み失敗: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))
						return False

				return True

		if target_ctrl == self.m_fileRepPmx:
			if not wrapperutils.is_valid_file(target_ctrl.GetPath(), label_ctrl.GetLabel(), ext, is_print):
				logger.debug("rep_pmx_data クリア: %s", target_ctrl.GetPath())
				self.rep_pmx_data = None

				if is_print:
					print("%s 読み込み失敗: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))

				return False
			else:
				logger.debug("rep_pmx_data 読み込み: %s", target_ctrl.GetPath())
				# 先PMX読み込む
				new_rep_pmx_data = wrapperutils.read_pmx(target_ctrl.GetPath(), label_ctrl.GetLabel(), is_print)

				if not self.rep_pmx_data or not new_rep_pmx_data or (self.rep_pmx_data and new_rep_pmx_data and self.rep_pmx_data.digest != new_rep_pmx_data.digest):
					# ハッシュが違う場合、データが違うとみなして更新
					self.rep_pmx_data = new_rep_pmx_data

					# 出力ファイル以外はモーフも変わるので初期化
					self.ClearMorph()

				if is_print:
					if new_rep_pmx_data:
						print("%s 読み込み成功: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))
					else:
						print("%s 読み込み失敗: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))
						return False

				return True

		# メインスレッドで読み込む
		if target_ctrl == self.m_camera_fileVmd:
			if not wrapperutils.is_valid_file(target_ctrl.GetPath(), label_ctrl.GetLabel(), ext, is_print):
				logger.debug("camera_vmd_data クリア: %s", target_ctrl.GetPath())
				# 読み込めるファイルではない場合、オブジェクトをクリアして終了
				self.camera_vmd_data = None

				if is_print:
					print("%s 読み込み失敗: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))

				return False
			else:
				logger.debug("camera_vmd_data 読み込み: %s", target_ctrl.GetPath())
				# VMD読み込む
				new_camera_vmd_data = wrapperutils.read_vmd(target_ctrl.GetPath(), label_ctrl.GetLabel(), is_print)

				if not self.camera_vmd_data or not new_camera_vmd_data or (self.camera_vmd_data and new_camera_vmd_data and self.camera_vmd_data.digest != new_camera_vmd_data.digest):
					# ハッシュが違う場合、データが違うとみなして更新
					self.camera_vmd_data = new_camera_vmd_data

				if is_print:
					if new_camera_vmd_data:
						print("%s 読み込み成功: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))
					else:
						print("%s 読み込み失敗: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))
						return False

				return True

		if target_ctrl == self.m_camera_fileOrgPmx:
			if not wrapperutils.is_valid_file(target_ctrl.GetPath(), label_ctrl.GetLabel(), ext, is_print):
				logger.debug("camera_pmx_data クリア: %s", target_ctrl.GetPath())
				self.camera_pmx_data = None

				if is_print:
					print("%s 読み込み失敗: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))

				return False
			else:
				logger.debug("camera_pmx_data 読み込み: %s", target_ctrl.GetPath())
				# 元PMX読み込む
				new_camera_pmx_data = wrapperutils.read_pmx(target_ctrl.GetPath(), label_ctrl.GetLabel(), is_print)

				if not self.camera_pmx_data or not new_camera_pmx_data or (self.camera_pmx_data and new_camera_pmx_data and self.camera_pmx_data.digest != new_camera_pmx_data.digest):
					# ハッシュが違う場合、データが違うとみなして更新
					self.camera_pmx_data = new_camera_pmx_data

				if is_print:
					if new_camera_pmx_data:
						print("%s 読み込み成功: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))
					else:
						print("%s 読み込み失敗: %s" % ( label_ctrl.GetLabel(),target_ctrl.GetPath() ))
						return False

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

		# 一旦出力ファイル設定
		self.OnCreateOutputVmd(event)
		self.OnCreateOutputCameraVmd(event)

		if target_ctrl == self.m_fileVmd:
			self.vmd_data = None
			self.camera_vmd_data = None

		if target_ctrl == self.m_fileOrgPmx:
			self.org_pmx_data = None
			self.camera_pmx_data = None

		if target_ctrl == self.m_fileRepPmx:
			self.rep_pmx_data = None

		if target_ctrl == self.m_camera_fileVmd:
			self.camera_vmd_data = None

		if target_ctrl == self.m_camera_fileOrgPmx:
			self.camera_pmx_data = None

		event.Skip()
		return

	# 待機中はゲージを動かす
	def OnIdle(self, event):
		if self.worker:
			self.m_Gauge.Pulse()

		if self.csv_worker:
			self.m_csv_Gauge.Pulse()

		# if self.blend_worker:
		# 	self.m_blend_Gauge.Pulse()

	# チェックボタン押下
	def OnCheck(self, event):
		self.m_txtConsole.Clear()
		wx.GetApp().Yield()
		
		# 全件読み込み	
		if not self.LoadFiles(True):
			self.m_Gauge.SetValue(0)
			return False

		# 読み込み処理が終わったらサイジングできるかチェック
		# カメラPMXはチェックするネタが無いのでとりあえず対象外
		wrapperutils.is_all_sizing(self.vmd_data, self.org_pmx_data, self.rep_pmx_data, self.camera_vmd_data)

		self.m_Gauge.SetValue(0)

		return True
	
	# モーフデータリスト生成
	def create_morph_data(self):
		logger.debug("create_morph_data")
		# モーフ置換文字列リスト生成
		vmd_choice_values = []
		rep_choice_values = []
		rep_rate_values = []

		morph_pair = {}
		logger.debug("self.vmd_choices: %s", self.vmd_choices)
		logger.debug("self.rep_choices: %s", self.rep_choices)
		logger.debug("self.rep_rates: %s", self.rep_rates)
		if self.vmd_choices and self.rep_choices:
			for vc, rc, rr in zip(self.vmd_choices, self.rep_choices, self.rep_rates):
				vc_idx = vc.GetSelection()
				rc_idx = rc.GetSelection()
				logger.debug("vc_idx: %s, rc_idx: %s", vc_idx, rc_idx)
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
					rep_rate_values.append(rr.GetValue())
					# ペアとして登録する
					morph_pair[(vcv,rcv)] = True							

		logger.debug("vmd_choice_values: %s", vmd_choice_values)
		logger.debug("rep_choice_values: %s", rep_choice_values)
		logger.debug("rep_rate_values: %s", rep_rate_values)
		
		return 	vmd_choice_values, rep_choice_values, rep_rate_values

	def create_slice_frame_data(self):
		logger.debug("create_slice_frame_data")

		slice_frame_values = []

		if self.slice_frames:
			for sf in self.slice_frames:
				if sf.GetValue() > 0:
					slice_frame_values.append(sf.GetValue())
		
		return slice_frame_values

	def DisableInput(self):
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

		# CSV
		# 実行ボタン押下不可
		self.m_csv_btnExec.Disable()
		# ファイル入力不可
		self.m_csv_fileVmd.Disable()

		# VMD
		# 実行ボタン押下不可
		self.m_vmd_btnExec.Disable()
		# ファイル入力不可
		self.m_vmd_fileCsvBone.Disable()
		self.m_vmd_fileCsvMorph.Disable()
		self.m_vmd_fileCsvCamera.Disable()

		# カメラ
		self.m_camera_fileVmd.Disable()
		self.m_camera_fileOutputVmd.Disable()
		self.m_camera_fileOrgPmx.Disable()
		self.m_camera_btnHistoryVmd.Disable()
		self.m_camera_btnHistoryOrgPmx.Disable()

		# # 分割
		# # 行追加ボタン押下不可
		# self.m_slice_btnAddLine.Disable()
		# # 実行ボタン押下不可
		# self.m_slice_btnExec.Disable()
		# # ファイル入力不可
		# self.m_slice_fileVmd.Disable()

		# # ブレンド
		# self.m_blend_filePmx.Disable()
		# self.m_blend_spinMin.Disable()
		# self.m_blend_spinMax.Disable()
		# self.m_blend_spinInc.Disable()
		# self.m_blend_btnExec.Disable()
	
	def EnableInput(self):
		# ファイル入力可
		self.m_fileVmd.Enable()
		self.m_fileOrgPmx.Enable()
		self.m_fileRepPmx.Enable()
		self.m_fileOutputVmd.Enable()
		# 履歴ボタン押下可
		self.m_btnHistoryVmd.Enable()
		self.m_btnHistoryOrgPmx.Enable()
		self.m_btnHistoryRepPmx.Enable()
		# 実行ボタン押下許可
		self.m_btnExec.Enable()
		self.m_btnCheck.Enable()

		# CSV
		# 実行ボタン押下可
		self.m_csv_btnExec.Enable()
		# ファイル入力可
		self.m_csv_fileVmd.Enable()
		self.m_vmd_fileCsvMorph.Enable()
		self.m_vmd_fileCsvCamera.Enable()

		# VMD
		# 実行ボタン押下可
		self.m_vmd_btnExec.Enable()
		# ファイル入力可
		self.m_vmd_fileCsvBone.Enable()

		# カメラ
		self.m_camera_fileVmd.Enable()
		self.m_camera_fileOutputVmd.Enable()
		self.m_camera_fileOrgPmx.Enable()
		self.m_camera_btnHistoryVmd.Enable()
		self.m_camera_btnHistoryOrgPmx.Enable()

		# # 分割
		# # 行追加ボタン押下不可
		# self.m_slice_btnAddLine.Enable()
		# # 実行ボタン押下不可
		# self.m_slice_btnExec.Enable()
		# # ファイル入力不可
		# self.m_slice_fileVmd.Enable()

		# # ブレンド
		# self.m_blend_filePmx.Enable()
		# self.m_blend_spinMin.Enable()
		# self.m_blend_spinMax.Enable()
		# self.m_blend_spinInc.Enable()
		# self.m_blend_btnExec.Enable()
	
	# 実行ボタン押下
	def OnExec(self, event):
		if not self.worker:
			self.DisableInput()

			self.m_txtConsole.Clear()
			wx.GetApp().Yield()

			self.DisableInput()

			# 全件読み込み		
			try:
				if not self.LoadFiles(True):
					self.EnableInput()
					# プログレス非表示
					self.m_Gauge.SetValue(0)

					return False
			except Exception:
				# 読み込みエラーが起きたら有効化
				self.EnableInput()

				return False

			if self.vmd_data and self.org_pmx_data and self.rep_pmx_data:
				# 一旦初期化
				self.vmd_choice_values = []
				self.rep_choice_values = []
				self.rep_rate_values = []

				# モーフデータ生成				
				self.vmd_choice_values, self.rep_choice_values, self.rep_rate_values = self.create_morph_data()

				# パス再設定
				self.OnCreateOutputVmd(event)
				self.OnCreateOutputCameraVmd(event)

				# 履歴保持
				if self.m_fileVmd.GetPath() in self.file_hitories["vmd"]:
					# 既に登録されている場合、一旦削除
					self.file_hitories["vmd"].remove(self.m_fileVmd.GetPath())
				# 改めて先頭に登録
				if self.m_fileVmd.GetPath():
					self.file_hitories["vmd"].insert(0, self.m_fileVmd.GetPath())
				
				# 履歴保持
				if self.m_fileOrgPmx.GetPath() in self.file_hitories["org_pmx"]:
					self.file_hitories["org_pmx"].remove(self.m_fileOrgPmx.GetPath())
				if self.m_fileOrgPmx.GetPath():
					self.file_hitories["org_pmx"].insert(0, self.m_fileOrgPmx.GetPath())
				
				# 履歴保持
				if self.m_fileRepPmx.GetPath() in self.file_hitories["rep_pmx"]:
					self.file_hitories["rep_pmx"].remove(self.m_fileRepPmx.GetPath())
				if self.m_fileRepPmx.GetPath():
					self.file_hitories["rep_pmx"].insert(0, self.m_fileRepPmx.GetPath())

				# 履歴保持
				if self.m_camera_fileVmd.GetPath() in self.file_hitories["camera_vmd"]:
					self.file_hitories["camera_vmd"].remove(self.m_camera_fileVmd.GetPath())
				if self.m_camera_fileVmd.GetPath():
					self.file_hitories["camera_vmd"].insert(0, self.m_camera_fileVmd.GetPath())

				# 履歴保持
				if self.m_camera_fileOrgPmx.GetPath() in self.file_hitories["camera_pmx"]:
					self.file_hitories["camera_pmx"].remove(self.m_camera_fileOrgPmx.GetPath())
				if self.m_camera_fileOrgPmx.GetPath():
					self.file_hitories["camera_pmx"].insert(0, self.m_camera_fileOrgPmx.GetPath())

				# 入力履歴を保存		
				try:
					with open(wrapperutils.get_mypath('history.json'), 'w') as f:
						json.dump(self.file_hitories, f, ensure_ascii=False)
				except Exception:
					print("history.json保存失敗")
					print(traceback.format_exc())

					# msg = wrapperutils.get_mypath('history.json')
					# msg += "\n"
					# msg += traceback.format_exc()
					# msg += "\n"
					# dialog = wx.MessageDialog(self, msg, style=wx.OK)
					# dialog.ShowModal()
					# dialog.Destroy()

				# スレッド実行
				self.worker = ExecWorkerThread(self)
				self.worker.start()
				self.worker.stop_event.set()
		else:
			print("まだ処理が実行中です。終了してから再度実行してください。")

	# スレッド実行結果
	def OnResult(self, event):

		# スレッド削除
		self.worker = None
		# 入力有効化
		self.EnableInput()
		# プログレス非表示
		self.m_Gauge.SetValue(0)
		# モーフ置換配列クリア
		self.vmd_choice_values = []
		self.rep_choice_values = []
		self.rep_rate_values = []

	# スレッド実行結果
	def OnCsvResult(self, event):
		# スレッド削除
		self.csv_worker = None
		# 入力有効化
		self.EnableInput()
		# プログレス非表示
		self.m_csv_Gauge.SetValue(0)

		# コンソールを元に戻す
		sys.stdout = self.m_txtConsole		

	# スレッド実行結果
	def OnVmdResult(self, event):
		# スレッド削除
		self.vmd_worker = None
		# 入力有効化
		self.EnableInput()
		# プログレス非表示
		self.m_vmd_Gauge.SetValue(0)

		# コンソールを元に戻す
		sys.stdout = self.m_txtConsole		

	# スレッド実行結果
	def OnSliceResult(self, event):
		# スレッド削除
		self.slice_worker = None
		# 入力有効化
		self.EnableInput()
		# プログレス非表示
		self.m_slice_Gauge.SetValue(0)
		# 分割配列初期化
		self.slice_frame_values = []

		# コンソールを元に戻す
		sys.stdout = self.m_txtConsole		

	def OnBlendExec( self, event ):
		self.DisableInput()

		self.m_blend_txtConsole.Clear()
		wx.GetApp().Yield()

		# BLENDコンソールに切り替え
		sys.stdout = self.m_blend_txtConsole

		self.DisableInput()

		if wrapperutils.is_valid_file(self.m_blend_filePmx.GetPath(), "PMXファイル", ".pmx", True) == False:

			self.EnableInput()
			# プログレス非表示
			self.m_blend_Gauge.SetValue(0)

			# 元に戻す
			sys.stdout = self.m_txtConsole

			event.Skip()
			return

		if self.m_blend_spinInc.GetValue() == 0:
			print("増加量は、0以外の値を入力してください。")

			self.EnableInput()
			# プログレス非表示
			self.m_blend_Gauge.SetValue(0)

			# 元に戻す
			sys.stdout = self.m_txtConsole

			event.Skip()
			return

		if not self.blend_worker:
			# スレッド実行
			self.blend_worker = BlendWorkerThread(self)
			self.blend_worker.start()
			self.blend_worker.stop_event.set()
		else:
			print("まだ処理が実行中です。終了してから再度実行してください。")

			# 元に戻す
			sys.stdout = self.m_txtConsole

	# スレッド実行結果
	def OnBlendResult(self, event):
		# スレッド削除
		self.blend_worker = None
		# 入力有効化
		self.EnableInput()
		# プログレス非表示
		self.m_blend_Gauge.SetValue(0)

		# コンソールを元に戻す
		sys.stdout = self.m_txtConsole		
		
	def ShowTraceModel(self, event):
		if wrapperutils.is_valid_file(self.m_fileVmd.GetPath(), "調整対象VMDファイル", ".vmd", False) == False:
			return False
		
		# モデル名表示追加
		model_name = wrapperutils.read_vmd_modelname(self.m_fileVmd.GetPath())
		if model_name == None:
			self.m_vmdTraceTxt.SetValue("　（VMD登録モデル取得失敗）")
		else:
			self.m_vmdTraceTxt.SetValue("　（VMD登録モデル: "+ model_name +"）")

	# 出力ファイルパスの生成
	def OnCreateOutputVmd(self, event):	
		logger.debug("OnCreateOutputVmd")
		logger.debug("m_fileVmd: %s " , self.m_fileVmd.GetPath())
		logger.debug("m_fileRepPmx: %s ",  self.m_fileRepPmx.GetPath())
		logger.debug("event: %s ",  type(event))
		logger.debug("wx.EVT_FILEPICKER_CHANGED: %s ",  type(wx.EVT_FILEPICKER_CHANGED))
		logger.debug("isinstance(event, wx.EVT_FILEPICKER_CHANGED): %s ", isinstance(event, wx.FileDirPickerEvent))

		if wrapperutils.is_auto_output_path(self.m_fileOutputVmd.GetPath(), self.m_fileVmd.GetPath(), self.m_fileRepPmx.GetPath(), isinstance(event, wx.FileDirPickerEvent)):
			# モーフ出力の組み合わせ取得
			vmd_choice_values, _, _ = self.create_morph_data()
			logger.debug("vmd_choice_values: %s", len(vmd_choice_values))

			# 現在設定されているパスが空か、自動生成パスルールに合う場合のみ、再設定
			new_filepath = wrapperutils.create_output_path(self.m_fileVmd.GetPath(), self.m_fileRepPmx.GetPath(), self.m_radioAvoidance.GetValue(), self.m_radioArmIK.GetValue(), len(vmd_choice_values) > 0)
			logger.debug("new_filepath: %s ", new_filepath)
			if new_filepath is not None:
				self.m_fileOutputVmd.SetPath(new_filepath)
			else:
				self.m_fileOutputVmd.SetPath("")

		if self.m_fileVmd.GetPath() != "":
			logger.debug("ShowTraceModel: %s ", self.m_fileOutputVmd.GetPath())
			# VMDファイルパスが空でなければ、トレースモデル名表示
			self.ShowTraceModel(event)
		else:
			self.m_vmdTraceTxt.SetValue("　（調整対象VMD未設定）")

	def OnCreateOutputCameraVmd(self, event):
		logger.debug("OnCreateOutputCameraVmd")
		logger.debug("m_camera_fileVmd: %s " , self.m_camera_fileVmd.GetPath())
		logger.debug("m_fileRepPmx: %s ",  self.m_fileRepPmx.GetPath())
		logger.debug("event: %s ",  type(event))
		logger.debug("wx.EVT_FILEPICKER_CHANGED: %s ",  type(wx.EVT_FILEPICKER_CHANGED))
		logger.debug("isinstance(event, wx.EVT_FILEPICKER_CHANGED): %s ", isinstance(event, wx.FileDirPickerEvent))

		if wrapperutils.is_auto_output_camera_path(self.m_camera_fileOutputVmd.GetPath(), self.m_camera_fileVmd.GetPath(), self.m_fileRepPmx.GetPath(), isinstance(event, wx.FileDirPickerEvent)):
			# 現在設定されているパスが空か、自動生成パスルールに合う場合のみ、再設定
			new_filepath = wrapperutils.create_output_camera_path(self.m_camera_fileVmd.GetPath(), self.m_fileRepPmx.GetPath())
			logger.debug("new_filepath: %s ", new_filepath)
			if new_filepath is not None:
				self.m_camera_fileOutputVmd.SetPath(new_filepath)
			else:
				self.m_camera_fileOutputVmd.SetPath("")


# Define notification event for thread completion
EVT_RESULT_ID = wx.NewId()
CSV_EVT_RESULT_ID = wx.NewId()
VMD_EVT_RESULT_ID = wx.NewId()
SLICE_EVT_RESULT_ID = wx.NewId()
BLEND_EVT_RESULT_ID = wx.NewId()

def EVT_RESULT(win, func):
	"""Define Result Event."""
	win.Connect(-1, -1, EVT_RESULT_ID, func)

def CSV_EVT_RESULT(win, func):
	"""Define Result Event."""
	win.Connect(-1, -1, CSV_EVT_RESULT_ID, func)

def VMD_EVT_RESULT(win, func):
	"""Define Result Event."""
	win.Connect(-1, -1, VMD_EVT_RESULT_ID, func)

def BLEND_EVT_RESULT(win, func):
	"""Define Result Event."""
	win.Connect(-1, -1, BLEND_EVT_RESULT_ID, func)

def SLICE_EVT_RESULT(win, func):
	"""Define Result Event."""
	win.Connect(-1, -1, SLICE_EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
	"""Simple event to carry arbitrary result data."""
	def __init__(self, data):
		"""Init Result Event."""
		wx.PyEvent.__init__(self)
		self.SetEventType(EVT_RESULT_ID)

class CsvResultEvent(wx.PyEvent):
	"""Simple event to carry arbitrary result data."""
	def __init__(self, data):
		"""Init Result Event."""
		wx.PyEvent.__init__(self)
		self.SetEventType(CSV_EVT_RESULT_ID)

class VmdResultEvent(wx.PyEvent):
	"""Simple event to carry arbitrary result data."""
	def __init__(self, data):
		"""Init Result Event."""
		wx.PyEvent.__init__(self)
		self.SetEventType(VMD_EVT_RESULT_ID)

class SliceResultEvent(wx.PyEvent):
	"""Simple event to carry arbitrary result data."""
	def __init__(self, data):
		"""Init Result Event."""
		wx.PyEvent.__init__(self)
		self.SetEventType(SLICE_EVT_RESULT_ID)

class BlendResultEvent(wx.PyEvent):
	"""Simple event to carry arbitrary result data."""
	def __init__(self, data):
		"""Init Result Event."""
		wx.PyEvent.__init__(self)
		self.SetEventType(BLEND_EVT_RESULT_ID)

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
			, self._notify_window.m_checkFloorArmDistance.GetValue()
			, self._notify_window.m_checkFloorArmDistanceUp.GetValue()
			, self._notify_window.m_checkFloorArmDistanceDown.GetValue()
			, self._notify_window.m_sliderHandFloorDistance.GetValue()
			, self._notify_window.m_sliderLegFloorDistance.GetValue()
			, self._notify_window.vmd_choice_values
			, self._notify_window.rep_choice_values			
			, self._notify_window.rep_rate_values
			, self._notify_window.camera_vmd_data
			, self._notify_window.m_camera_fileVmd.GetPath()
			, self._notify_window.camera_pmx_data
			, self._notify_window.m_camera_fileOrgPmx.GetPath()
			, self._notify_window.m_camera_fileOutputVmd.GetPath()
			, self._notify_window.m_camera_spinYoffset.GetValue()
		)

		# Here's where the result would be returned (this is an
		# example fixed result of the number 10, but it could be
		# any Python object)
		wx.PostEvent(self._notify_window, ResultEvent(None))

	def abort(self):
		"""abort worker thread."""
		# Method for use by main thread to signal an abort
		self._want_abort = 1


# Thread class that executes processing
# http://nobunaga.hatenablog.jp/entry/2016/06/03/204450
class CsvWorkerThread(Thread):
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

		convert_csv.main(self._notify_window.m_csv_fileVmd.GetPath())

		# Here's where the result would be returned (this is an
		# example fixed result of the number 10, but it could be
		# any Python object)
		wx.PostEvent(self._notify_window, CsvResultEvent(None))

	def abort(self):
		"""abort worker thread."""
		# Method for use by main thread to signal an abort
		self._want_abort = 1



# Thread class that executes processing
# http://nobunaga.hatenablog.jp/entry/2016/06/03/204450
class VmdWorkerThread(Thread):
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

		convert_vmd.main(
			self._notify_window.m_vmd_fileCsvBone.GetPath(),
			self._notify_window.m_vmd_fileCsvMorph.GetPath(),
			self._notify_window.m_vmd_fileCsvCamera.GetPath()
		)

		# Here's where the result would be returned (this is an
		# example fixed result of the number 10, but it could be
		# any Python object)
		wx.PostEvent(self._notify_window, VmdResultEvent(None))

	def abort(self):
		"""abort worker thread."""
		# Method for use by main thread to signal an abort
		self._want_abort = 1



# Thread class that executes processing
# http://nobunaga.hatenablog.jp/entry/2016/06/03/204450
class SliceWorkerThread(Thread):
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

		slice_frame_keys.main(self._notify_window.m_slice_fileVmd.GetPath(), self._notify_window.slice_frame_values)

		# Here's where the result would be returned (this is an
		# example fixed result of the number 10, but it could be
		# any Python object)
		wx.PostEvent(self._notify_window, SliceResultEvent(None))

	def abort(self):
		"""abort worker thread."""
		# Method for use by main thread to signal an abort
		self._want_abort = 1


# Thread class that executes processing
# http://nobunaga.hatenablog.jp/entry/2016/06/03/204450
class BlendWorkerThread(Thread):
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
		
		blend_pmx.main( \
			self._notify_window.m_blend_filePmx.GetPath(), \
			self._notify_window.m_blend_spinMin.GetValue(), \
			self._notify_window.m_blend_spinMax.GetValue(), \
			self._notify_window.m_blend_spinInc.GetValue() \
			# self._notify_window.m_blend_comboPanel.GetValue()
		)

		# Here's where the result would be returned (this is an
		# example fixed result of the number 10, but it could be
		# any Python object)
		wx.PostEvent(self._notify_window, BlendResultEvent(None))

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
				self.window.OnCreateOutputVmd(wx.FileDirPickerEvent())
				self.window.OnCreateOutputCameraVmd(wx.FileDirPickerEvent())
			
			if self.target_ctrl == self.window.m_camera_fileVmd:
				# カメラ出力パス生成対象コントロールの場合、VMD生成処理を走らせる
				self.window.OnCreateOutputCameraVmd(wx.FileDirPickerEvent())
			
			# if self.target_ctrl == self.window.m_fileVmd:
			# 	# VMDファイルの場合、VMD登録モデル表示
			# 	self.window.ShowTraceModel(wx.EVT_FILEPICKER_CHANGED)

			# オブジェクトクリア
			if self.target_ctrl == self.window.m_fileVmd:
				self.window.vmd_data = None

			if self.target_ctrl == self.window.m_fileOrgPmx:
				self.window.org_pmx_data = None
				self.window.camera_pmx_data = None
				
			if self.target_ctrl == self.window.m_fileRepPmx:
				self.window.rep_pmx_data = None

			if self.target_ctrl == self.window.m_camera_fileVmd:
				self.window.camera_vmd = None

			if self.target_ctrl == self.window.m_camera_fileOrgPmx:
				self.window.camera_pmx_data = None
				
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
		self._label.SetLabel(  u"（{0}）".format( round(self._value, 3)) )

		event.Skip()

	def GetValue(self):
		return round(self._value, 3)

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


