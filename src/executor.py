# -*- coding: utf-8 -*-
#

import os
import wx
import sys
import logging
import argparse
import winsound
import numpy as np

from form.MainFrame import MainFrame
from module.MOptions import MOptions
from utils.MLogger import MLogger
from utils import MFileUtils

VERSION_NAME = "ver5.00_β45"

# 指数表記なし、有効小数点桁数6、30を超えると省略あり、一行の文字数200
np.set_printoptions(suppress=True, precision=6, threshold=30, linewidth=200)


if __name__ == '__main__':
    mydir_path = MFileUtils.get_mydir_path(sys.argv[0])

    if len(sys.argv) > 3 and "--motion_path" in sys.argv:
        from service.SizingService import SizingService
        from utils.MException import SizingException

        logger = MLogger(__name__)

        # 引数指定がある場合、コマンドライン実行
        try:
            SizingService(MOptions.parse(VERSION_NAME)).execute()
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message, decoration=MLogger.DECORATION_BOX)
        except Exception as e:
            logger.critical("サイジング処理が意図せぬエラーで終了しました。", e, decoration=MLogger.DECORATION_BOX)
        finally:
            logging.shutdown()

        # 終了音を鳴らす
        if os.name == "nt":
            # Windows
            try:
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
            except Exception:
                pass
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument("--verbose", default=20, type=int)
        parser.add_argument("--out_log", default=0, type=int)
        args = parser.parse_args()
        
        # ロギングレベル
        is_out_log = True if args.out_log == 1 else False

        MLogger.initialize(level=args.verbose, is_file=False)

        # 引数指定がない場合、通常起動
        app = wx.App(False)
        icon = wx.Icon(MFileUtils.resource_path('src/vmdsizing.ico'), wx.BITMAP_TYPE_ICO)
        frame = MainFrame(None, mydir_path, VERSION_NAME, args.verbose, is_out_log)
        frame.SetIcon(icon)
        frame.Show(True)
        app.MainLoop()
