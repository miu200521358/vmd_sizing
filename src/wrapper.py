#! env python
# -*- coding: utf-8 -*-

import wx
import sys
import os
from VmdSizingProject3 import VmdSizingProject3

def resource_path(relative):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)

    
if __name__ == '__main__':
    app = wx.App(False)
    icon=wx.Icon(resource_path('src/vmdsizing.ico'),wx.BITMAP_TYPE_ICO)
    frame = VmdSizingProject3(None)
    frame.SetIcon(icon)
    frame.Show(True)
    app.MainLoop()
