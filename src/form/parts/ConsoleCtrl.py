# -*- coding: utf-8 -*-
#

import wx
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class ConsoleCtrl(wx.TextCtrl):

    def __init__(self, parent, id=wx.ID_ANY, value="", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, validator=wx.DefaultValidator, name=wx.TextCtrlNameStr):
        super().__init__(parent, id, value, pos, size, style, validator, name)

    def monitor(self, queue):
        while True:
            # super().write(queue.get())
            wx.CallAfter(queue.get())
