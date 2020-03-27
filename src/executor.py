# -*- coding: utf-8 -*-
#

import wx
import sys
import logging

from form.MainFrame import MainFrame
from utils import MFileUtils
from utils.MLogger import MLogger

logger = MLogger(__name__)
VERSION_NAME = "ver5.00_β30"


if __name__ == '__main__':
    mydir_path = MFileUtils.get_mydir_path(sys.argv[0])

    if len(sys.argv) > 3 and "--vmd_path" in sys.argv:
        MLogger.initialize(logging.INFO)
        # 引数指定がある場合、コマンドライン実行
        # main.parse_exec()
        pass
    else:
        # ロギングレベル
        logging_level = logging.INFO

        if len(sys.argv) > 2 and "--verbose" in sys.argv:
            print(sys.argv)
            try:
                logging_level = int(sys.argv[-1])
            except Exception:
                logging_level = logging.INFO

        is_out_log = True if "--out_log" in sys.argv else False
        
        MLogger.initialize(logging_level)

        # 引数指定がない場合、通常起動
        app = wx.App(False)
        icon = wx.Icon(MFileUtils.resource_path('src/vmdsizing.ico'), wx.BITMAP_TYPE_ICO)
        frame = MainFrame(None, mydir_path, VERSION_NAME, logging_level, is_out_log)
        frame.SetIcon(icon)
        frame.Show(True)
        app.MainLoop()
