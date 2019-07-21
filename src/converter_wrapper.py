#! env python
# -*- coding: utf-8 -*-

import wx
from VmdConverterProject import VmdConverterProject

if __name__ == '__main__':
    app = wx.App(False)
    frame = VmdConverterProject(None)
    frame.Show(True)
    app.MainLoop()