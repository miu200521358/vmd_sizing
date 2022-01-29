# -*- coding: utf-8 -*-
#

import os
import wx
import sys
import logging
import argparse
import numpy as np
import traceback
import multiprocessing

from form.MainFrame import MainFrame
from module.MOptions import MOptions
from utils.MLogger import MLogger
from utils import MFileUtils
from service.SizingService import SizingService
from utils.MException import SizingException

VERSION_NAME = "ver5.01.05_β03"

# 指数表記なし、有効小数点桁数6、30を超えると省略あり、一行の文字数200
np.set_printoptions(suppress=True, precision=6, threshold=30, linewidth=200)

# Windowsマルチプロセス対策
multiprocessing.freeze_support()

if __name__ == '__main__':
    mydir_path = MFileUtils.get_mydir_path(sys.argv[0])

    if len(sys.argv) > 3 and "--motion_path" in sys.argv:
        if os.name == "nt":
            import winsound     # Windows版のみインポート

        # 引数指定がある場合、コマンドライン実行
        try:
            SizingService(MOptions.parse(VERSION_NAME)).execute()
        except SizingException as se:
            print("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
        except Exception:
            print("サイジング処理が意図せぬエラーで終了しました。")
            print(traceback.format_exc())
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
        parser.add_argument("--is_saving", default=1, type=int)
        args = parser.parse_args()
        
        # ロギングレベル
        is_out_log = True if args.out_log == 1 else False
        # 省エネモード
        is_saving = True if args.is_saving == 1 else False

        MLogger.initialize(level=args.verbose, is_file=False)

        log_level_name = ""
        if args.verbose == MLogger.FULL:
            # フルデータの場合
            log_level_name = "（全打ち版）"
        elif args.verbose == MLogger.DEBUG_FULL:
            # フルデータの場合
            log_level_name = "（全打ちデバッグ版）"
        elif args.verbose == MLogger.DEBUG:
            # テスト（デバッグ版）の場合
            log_level_name = "（デバッグ版）"
        elif args.verbose == MLogger.TIMER:
            # 時間計測の場合
            log_level_name = "（タイマー版）"
        elif not is_saving:
            # 省エネOFFの場合
            log_level_name = "（ハイスペック版）"
        elif is_out_log:
            # ログありの場合
            log_level_name = "（ログあり版）"

        now_version_name = "{0}{1}".format(VERSION_NAME, log_level_name)

        # 引数指定がない場合、通常起動
        app = wx.App(False)
        icon = wx.Icon(MFileUtils.resource_path('src/vmdsizing.ico'), wx.BITMAP_TYPE_ICO)
        frame = MainFrame(None, mydir_path, now_version_name, args.verbose, is_saving, is_out_log)
        frame.SetIcon(icon)
        frame.Show(True)
        app.MainLoop()
