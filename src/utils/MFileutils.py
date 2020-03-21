# -*- coding: utf-8 -*-
#

import sys
import os
import json
import glob
import traceback
from pathlib import Path
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


# リソースファイルのパス
def resource_path(relative):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)


# ファイル履歴読み込み
def read_history(mydir_path):
    # ファイル履歴
    file_hitories = {"vmd": [], "org_pmx": [], "rep_pmx": [], "camera_vmd": [], "camera_pmx": [], "smooth_pmx": [], "max": 20}

    # 履歴JSONファイルがあれば読み込み
    try:
        with open(os.path.join(mydir_path, 'history.json'), 'r') as f:
            file_hitories = json.load(f)
            # キーが揃っているかチェック
            for key in ["vmd", "org_pmx", "rep_pmx", "camera_vmd", "camera_pmx", "smooth_pmx"]:
                if key not in file_hitories:
                    file_hitories[key] = []
            # 最大件数が揃っているかチェック
            if "max" not in file_hitories:
                file_hitories["max"] = 20
    except Exception:
        file_hitories = {"vmd": [], "org_pmx": [], "rep_pmx": [], "camera_vmd": [], "camera_pmx": [], "smooth_pmx": [], "max": 20}

    return file_hitories


def save_history(mydir_path, file_hitories):
    # 入力履歴を保存
    try:
        with open(os.path.join(mydir_path, 'history.json'), 'w') as f:
            json.dump(file_hitories, f, ensure_ascii=False)
    except Exception:
        logger.error("履歴ファイル保存失敗", traceback.format_exc(), decoration=MLogger.DECORATION_SIMPLE)


# パス解決
def get_mydir_path(exec_path):
    logger.test("sys.argv %s", sys.argv)
    
    dir_path = Path(exec_path).parent if hasattr(sys, "frozen") else Path(__file__).parent
    logger.test("get_mydir_path: %s", get_mydir_path)

    return dir_path


# ディレクトリパス
def get_dir_path(base_file_path, is_print=True):
    file_path_list = [p for p in glob.glob(base_file_path) if os.path.isfile(p)]

    if len(file_path_list) == 0:
        return ""

    try:
        # ファイルパスをオブジェクトとして解決し、親を取得する
        return str(Path(file_path_list[0]).resolve().parents[0])
    except Exception as e:
        logger.error("ファイルパスの解析に失敗しました。\nパスに使えない文字がないか確認してください。\nファイルパス: {0}\n\n{1}".format(base_file_path, e.with_traceback(sys.exc_info()[2])), decoration=MLogger.DECORATION_SIMPLE)
        raise e


def escape_filepath(path):
    path = path.replace("\\", r"\\")
    path = path.replace("*", "\\*")
    path = path.replace("+", "\\+")
    path = path.replace(".", "\\.")
    path = path.replace("?", "\\?")
    path = path.replace("{", "\\{")
    path = path.replace("}", "\\}")
    path = path.replace("(", "\\(")
    path = path.replace(")", "\\)")
    path = path.replace("[", "\\[")
    path = path.replace("]", "\\]")
    path = path.replace("{", "\\{")
    path = path.replace("^", "\\^")
    path = path.replace("$", "\\$")
    path = path.replace("-", "\\-")
    path = path.replace("|", "\\|")
    path = path.replace("/", "\\/")

    return path
