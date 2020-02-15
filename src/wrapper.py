#! env python
# -*- coding: utf-8 -*-

import wx
import sys
import os
import main
from VmdSizingProject3 import VmdSizingProject3

def resource_path(relative):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)

    
if __name__ == '__main__':
    if len(sys.argv) > 2 and vmd_path in sys.argv:
        # 引数指定がある場合、コマンドライン実行
        main.parse_exec()
    else:
        # デバッグレベルの指定のみの場合、デバッグを出力する
        is_debug = True if len(sys.argv) > 1 and "--is_debug" in sys.argv else False
        # 引数指定がない場合、通常起動
        app = wx.App(False)
        icon=wx.Icon(resource_path('src/vmdsizing.ico'),wx.BITMAP_TYPE_ICO)
        frame = VmdSizingProject3(None, is_debug)
        frame.SetIcon(icon)
        frame.Show(True)
        app.MainLoop()
