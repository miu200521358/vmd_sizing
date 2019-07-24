#! env python
# -*- coding: utf-8 -*-

import wx
import sys
import os
from VmdConverterProject import VmdConverterProject

def resource_path(relative):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)

if __name__ == '__main__':
    app = wx.App(False)
    icon=wx.Icon(resource_path('src/vmdconverter.ico'),wx.BITMAP_TYPE_ICO)
    frame = VmdConverterProject(None)
    frame.SetIcon(icon)
    frame.Show(True)
    app.MainLoop()