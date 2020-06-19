# -*- coding: utf-8 -*-
#
import wx
import copy
from form.parts.BaseFilePickerCtrl import BaseFilePickerCtrl
from utils import MFileUtils
from utils.MLogger import MLogger

logger = MLogger(__name__)


class HistoryFilePickerCtrl(BaseFilePickerCtrl):
    
    def __init__(self, frame, parent, title, message, wildcard, style, tooltip, \
                 file_model_spacer, title_parts_ctrl, title_parts2_ctrl, file_histories_key, is_change_output, is_aster, is_save, set_no):
        
        self.parent = parent
        self.file_histories_key = file_histories_key

        # logger.test(self.frame.file_hitories)

        self.histroy_btn_ctrl = wx.Button(parent, wx.ID_ANY, u"履歴", wx.DefaultPosition, wx.DefaultSize, 0)
        self.histroy_btn_ctrl.SetToolTip(u"これまで指定された{0}を再指定できます。".format(title))

        super().__init__(frame, parent, title, message, wildcard, style, tooltip, file_model_spacer=file_model_spacer, title_parts_ctrl=title_parts_ctrl, \
                         title_parts2_ctrl=title_parts2_ctrl, file_parts_ctrl=self.histroy_btn_ctrl, is_change_output=is_change_output, is_aster=is_aster, \
                         is_save=is_save, set_no=set_no)

        # 「履歴」ボタン押下時処理
        self.histroy_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_show_history)
    
    def save(self):
        if len(self.file_ctrl.GetPath()) > 0 and self.frame.file_hitories and self.file_ctrl.GetPath() in self.frame.file_hitories[self.file_histories_key]:
            # 既に登録されている場合、一旦削除
            self.frame.file_hitories[self.file_histories_key].remove(self.file_ctrl.GetPath())
        
        if not self.frame.file_hitories:
            self.frame.file_hitories[self.file_histories_key] = []

        # 改めて先頭に登録
        if len(self.file_ctrl.GetPath()) > 0:
            self.frame.file_hitories[self.file_histories_key].insert(0, self.file_ctrl.GetPath())
        
        # 上限50件
        self.frame.file_hitories[self.file_histories_key] = self.frame.file_hitories[self.file_histories_key][:50]

    # 履歴ボタンのあるファイルコントロールは直近のパスを開く
    def on_pick_file(self, event):

        if len(self.file_ctrl.GetPath()) == 0 and self.frame.file_hitories and self.file_histories_key in self.frame.file_hitories and len(self.frame.file_hitories[self.file_histories_key]) > 0:
            # パスが未指定である場合、直近のパスを設定してひらく
            self.file_ctrl.SetInitialDirectory(MFileUtils.get_dir_path(self.frame.file_hitories[self.file_histories_key][0]))

        event.Skip()
    
    # 履歴ボタンを開く
    def on_show_history(self, event):

        # 入力行を伸ばす
        hs = copy.deepcopy(self.frame.file_hitories[self.file_histories_key])
        hs.extend(["" for x in range(self.frame.file_hitories["max"] + 1)])

        with wx.SingleChoiceDialog(self.parent, "ファイルを選んでダブルクリック、またはOKボタンをクリックしてください。", caption="ファイル履歴選択",
                                   choices=hs[:(self.frame.file_hitories["max"] + 1)],
                                   style=wx.CAPTION | wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.OK | wx.CANCEL | wx.CENTRE) as choiceDialog:

            if choiceDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind

            # ファイルピッカーに選択したパスを設定
            self.file_ctrl.SetPath(choiceDialog.GetStringSelection())
            self.file_ctrl.UpdatePickerFromTextCtrl()
            self.file_ctrl.SetInitialDirectory(MFileUtils.get_dir_path(choiceDialog.GetStringSelection()))

            # ファイル変更処理
            self.on_change_file(wx.FileDirPickerEvent())
