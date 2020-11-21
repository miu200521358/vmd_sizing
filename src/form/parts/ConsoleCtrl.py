# -*- coding: utf-8 -*-
#

import wx
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class ConsoleCtrl(wx.TextCtrl):

    def __init__(self, parent, logging_level, id=wx.ID_ANY, value="", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, validator=wx.DefaultValidator, name=wx.TextCtrlNameStr):
        super().__init__(parent, id, value, pos, size, style, validator, name)
        self.limit_cnt = 10

        if logging_level <= MLogger.DEBUG:
            # デバッグ版は纏めて出力
            self.limit_cnt = 5000

        self.texts = ""

    def write(self, text, stack=False):
        try:
            self.texts += text

            if len(self.texts) > self.limit_cnt and stack:
                # 一定文字数を超えた場合にのみ出力
                wx.CallAfter(self.AppendText, self.texts)
                self.texts = ""
            elif not stack:
                # stackではない場合、そのまま出力
                wx.CallAfter(self.AppendText, self.texts)
                self.texts = ""

        except: # noqa
            pass

    # def monitor(self, queue):
    #     while True:
    #         # super().write(queue.get())
    #         wx.CallAfter(queue.get())
    #         # 0.1秒待機
    #         time.sleep(0.1)

