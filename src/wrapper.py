#! env python
# -*- coding: utf-8 -*-

import wx
from VmdSizingProjectFrame import VmdSizingProjectFrame

if __name__ == '__main__':
    app = wx.App(False)
    frame = VmdSizingProjectFrame(None)
    frame.Show(True)
    app.MainLoop()