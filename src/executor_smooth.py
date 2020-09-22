# -*- coding: utf-8 -*-
#
import numpy as np
import multiprocessing
import traceback
import logging
import os

from module.MOptions import MSmoothOptions
from service.ConvertSmoothService import ConvertSmoothService
from utils.MException import SizingException

# 指数表記なし、有効小数点桁数6、30を超えると省略あり、一行の文字数200
np.set_printoptions(suppress=True, precision=6, threshold=30, linewidth=200)

# Windowsマルチプロセス対策
multiprocessing.freeze_support()


if __name__ == "__main__":
    if os.name == "nt":
        import winsound     # Windows版のみインポート

    # 引数指定がある場合、コマンドライン実行
    try:
        options = MSmoothOptions.parse("VmdSizing Smooth")

        ConvertSmoothService(options).execute()
    except SizingException as se:
        print("スムージング処理が処理できないデータで終了しました。\n\n%s", se.message)
    except Exception:
        print("スムージング処理が意図せぬエラーで終了しました。")
        print(traceback.format_exc())

    # 終了音を鳴らす
    if os.name == "nt":
        # Windows
        try:
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
        except Exception:
            pass
