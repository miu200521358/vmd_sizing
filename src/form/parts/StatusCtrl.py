# -*- coding: utf-8 -*-
#

import wx
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class StatusCtrl(wx.TextCtrl):

    def __init__(self, parent, id=wx.ID_ANY, value="", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, validator=wx.DefaultValidator, name=wx.TextCtrlNameStr):
        super().__init__(parent, id, value, pos, size, style, validator, name)

    def write(self, text):
        try:
            wx.CallAfter(self.SetValue, str(int(text)))
        except: # noqa
            pass

    # def monitor(self, queue):
    #     while True:
    #         # super().write(queue.get())
    #         wx.CallAfter(queue.get())
    #         # 0.1秒待機
    #         time.sleep(0.1)

