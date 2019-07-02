#! env python
# -*- coding: utf-8 -*-

import wx
from VmdSizingProject3 import VmdSizingProject3

if __name__ == '__main__':
    app = wx.App(False)
    frame = VmdSizingProject3(None)
    frame.Show(True)
    app.MainLoop()