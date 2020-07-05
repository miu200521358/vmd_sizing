# -*- coding: utf-8 -*-
#

from datetime import datetime
import sys
import os
import json
import glob
import traceback
from pathlib import Path
import re

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
    file_hitories = {"vmd": [], "org_pmx": [], "rep_pmx": [], "camera_vmd": [], "camera_pmx": [], "smooth_vmd": [], "smooth_pmx": [], "max": 50}

    # 履歴JSONファイルがあれば読み込み
    try:
        with open(os.path.join(mydir_path, 'history.json'), 'r') as f:
            file_hitories = json.load(f)
            # キーが揃っているかチェック
            for key in ["vmd", "org_pmx", "rep_pmx", "camera_vmd", "camera_pmx", "smooth_pmx", "smooth_vmd"]:
                if key not in file_hitories:
                    file_hitories[key] = []
            # 最大件数は常に上書き
            file_hitories["max"] = 50
    except Exception:
        file_hitories = {"vmd": [], "org_pmx": [], "rep_pmx": [], "camera_vmd": [], "camera_pmx": [], "smooth_vmd": [], "smooth_pmx": [], "max": 50}

    return file_hitories


def save_history(mydir_path, file_hitories):
    # 入力履歴を保存
    try:
        with open(os.path.join(mydir_path, 'history.json'), 'w') as f:
            json.dump(file_hitories, f, ensure_ascii=False)
    except Exception:
        logger.error("履歴ファイル保存失敗", traceback.format_exc())


# パス解決
def get_mydir_path(exec_path):
    logger.test("sys.argv %s", sys.argv)
    
    dir_path = Path(exec_path).parent if hasattr(sys, "frozen") else Path(__file__).parent
    logger.test("get_mydir_path: %s", get_mydir_path)

    return dir_path


# ディレクトリパス
def get_dir_path(base_file_path, is_print=True):
    if os.path.exists(base_file_path):
        file_path_list = [base_file_path]
    else:
        file_path_list = [p for p in glob.glob(base_file_path) if os.path.isfile(p)]

    if len(file_path_list) == 0:
        return ""

    try:
        # ファイルパスをオブジェクトとして解決し、親を取得する
        return str(Path(file_path_list[0]).resolve().parents[0])
    except Exception as e:
        logger.error("ファイルパスの解析に失敗しました。\nパスに使えない文字がないか確認してください。\nファイルパス: {0}\n\n{1}".format(base_file_path, e.with_traceback(sys.exc_info()[2])))
        raise e
    

# モーフ置換組み合わせファイル
def get_output_morph_path(base_file_path: str, org_pmx_path: str, rep_pmx_path: str):
    # モーションVMDパスの拡張子リスト
    if os.path.exists(base_file_path):
        file_path_list = [base_file_path]
    else:
        file_path_list = [p for p in glob.glob(base_file_path) if os.path.isfile(p)]

    if len(file_path_list) == 0 or (len(file_path_list) > 0 and not os.path.exists(file_path_list[0])) or not os.path.exists(rep_pmx_path):
        return ""

    # モーションVMDディレクトリパス
    motion_vmd_dir_path = get_dir_path(file_path_list[0])
    # モーションVMDファイル名・拡張子
    motion_vmd_file_name, motion_vmd_ext = os.path.splitext(os.path.basename(file_path_list[0]))
    # 作成元モデルファイル名・拡張子
    org_pmx_file_name, _ = os.path.splitext(os.path.basename(org_pmx_path))
    # 変換先モデルファイル名・拡張子
    rep_pmx_file_name, _ = os.path.splitext(os.path.basename(rep_pmx_path))

    # 出力ファイルパス生成
    new_output_morph_path = os.path.join(motion_vmd_dir_path, "{0}_{1}_{2}{3}".format(motion_vmd_file_name, org_pmx_file_name, rep_pmx_file_name, ".csv"))

    return new_output_morph_path


# VMD出力ファイルパス生成
# base_file_path: モーションVMDパス(アスタリスク込み)
# rep_pmx_path: 変換先モデルPMXパス
# detail_stance_flg: スタンス詳細再現FLG
# twist_flg: 捩り分散
# arm_process_flg_avoidance: 接触回避
# arm_process_flg_alignment: 手首位置合わせ
# is_morphs: モーフ置換有無
# output_vmd_path: 出力ファイルパス
def get_output_vmd_path(base_file_path: str, rep_pmx_path: str, detail_stance_flg: bool, twist_flg: bool, \
                        arm_process_flg_avoidance: bool, arm_process_flg_alignment: bool, is_morphs: bool, output_vmd_path: str, is_force=False):
    # モーションVMDパスの拡張子リスト
    if os.path.exists(base_file_path):
        file_path_list = [base_file_path]
    else:
        file_path_list = [p for p in glob.glob(base_file_path) if os.path.isfile(p)]

    if len(file_path_list) == 0 or (len(file_path_list) > 0 and not os.path.exists(file_path_list[0])) or not os.path.exists(rep_pmx_path):
        return ""

    # モーションVMDディレクトリパス
    motion_vmd_dir_path = get_dir_path(file_path_list[0])
    # モーションVMDファイル名・拡張子
    motion_vmd_file_name, motion_vmd_ext = os.path.splitext(os.path.basename(file_path_list[0]))
    # 変換先モデルファイル名・拡張子
    rep_pmx_file_name, _ = os.path.splitext(os.path.basename(rep_pmx_path))

    # モーフ

    # スタンス追加補正
    # 捩り分散
    # 腕
    suffix = "{0}{1}{2}{3}{4}".format(
        ("S" if detail_stance_flg else ""),
        ("T" if twist_flg else ""),
        ("M" if is_morphs else ""),
        ("I" if arm_process_flg_avoidance else ""),
        ("P" if arm_process_flg_alignment else "")
    )

    if len(suffix) > 0:
        suffix = "_{0}".format(suffix)

    # 出力ファイルパス生成
    new_output_vmd_path = os.path.join(motion_vmd_dir_path, "{0}_{1}{2}_{3:%Y%m%d_%H%M%S}{4}".format(motion_vmd_file_name, rep_pmx_file_name, suffix, datetime.now(), ".vmd"))

    # ファイルパス自体が変更されたか、自動生成ルールに則っている場合、ファイルパス変更
    if is_force or is_auto_vmd_output_path(output_vmd_path, motion_vmd_dir_path, motion_vmd_file_name, ".vmd", rep_pmx_file_name):

        try:
            open(new_output_vmd_path, 'w')
            os.remove(new_output_vmd_path)
        except Exception:
            logger.warning("出力ファイルパスの生成に失敗しました。以下の原因が考えられます。\n" \
                           + "・ファイルパスが255文字を超えている\n" \
                           + "・ファイルパスに使えない文字列が含まれている（例) \\　/　:　*　?　\"　<　>　|）" \
                           + "・出力ファイルパスの親フォルダに書き込み権限がない" \
                           + "・出力ファイルパスに書き込み権限がない")

        return new_output_vmd_path
    
    return output_vmd_path


# 自動生成ルールに則ったパスか
def is_auto_vmd_output_path(output_vmd_path: str, motion_vmd_dir_path: str, motion_vmd_file_name: str, motion_vmd_ext: str, rep_pmx_file_name: str):
    if not output_vmd_path:
        # 出力パスがない場合、置き換え対象
        return True

    # 新しく設定しようとしている出力ファイルパスの正規表現
    escaped_motion_vmd_file_name = escape_filepath(os.path.join(motion_vmd_dir_path, motion_vmd_file_name))
    escaped_rep_pmx_file_name = escape_filepath(rep_pmx_file_name)
    escaped_motion_vmd_ext = escape_filepath(motion_vmd_ext)

    new_output_vmd_pattern = re.compile(r'^%s_%s%s%s$' % (escaped_motion_vmd_file_name, \
                                        escaped_rep_pmx_file_name, r"_?\w*_\d{8}_\d{6}", escaped_motion_vmd_ext))
    
    logger.debug("new_output_vmd_pattern: %s", new_output_vmd_pattern)
    
    # 自動生成ルールに則ったファイルパスである場合、合致あり
    return re.match(new_output_vmd_pattern, output_vmd_path) is not None


# カメラVMD出力ファイルパス生成
# base_file_path: モーションカメラVMDパス
# rep_pmx_path: 変換先モデルPMXパス
# output_camera_vmd_path: 出力ファイルパス
def get_output_camera_vmd_path(base_file_path: str, rep_pmx_path: str, output_camera_vmd_path: str, is_force=False):
    # モーションカメラVMDパスの拡張子リスト
    if not os.path.exists(base_file_path) or not os.path.exists(rep_pmx_path):
        return ""

    # モーションカメラVMDディレクトリパス
    motion_camera_vmd_dir_path = get_dir_path(base_file_path)
    # モーションカメラVMDファイル名・拡張子
    motion_camera_vmd_file_name, motion_camera_vmd_ext = os.path.splitext(os.path.basename(base_file_path))
    # 変換先モデルファイル名・拡張子
    rep_pmx_file_name, _ = os.path.splitext(os.path.basename(rep_pmx_path))

    # 出力ファイルパス生成
    new_output_camera_vmd_path = os.path.join(motion_camera_vmd_dir_path, "{0}_{1}_{2:%Y%m%d_%H%M%S}{3}".format(motion_camera_vmd_file_name, rep_pmx_file_name, datetime.now(), ".vmd"))

    # ファイルパス自体が変更されたか、自動生成ルールに則っている場合、ファイルパス変更
    if is_force or is_auto_camera_vmd_output_path(output_camera_vmd_path, motion_camera_vmd_dir_path, motion_camera_vmd_file_name, ".vmd", rep_pmx_file_name):

        try:
            open(new_output_camera_vmd_path, 'w')
            os.remove(new_output_camera_vmd_path)
        except Exception:
            logger.warning("出力ファイルパスの生成に失敗しました。以下の原因が考えられます。\n" \
                           + "・ファイルパスが255文字を超えている\n" \
                           + "・ファイルパスに使えない文字列が含まれている（例) \\　/　:　*　?　\"　<　>　|）" \
                           + "・出力ファイルパスの親フォルダに書き込み権限がない" \
                           + "・出力ファイルパスに書き込み権限がない")

        return new_output_camera_vmd_path

    return output_camera_vmd_path


# 自動生成ルールに則ったパスか
def is_auto_camera_vmd_output_path(output_camera_vmd_path: str, motion_camera_vmd_dir_path: str, motion_camera_vmd_file_name: str, motion_camera_vmd_ext: str, rep_pmx_file_name: str):
    if not output_camera_vmd_path:
        # 出力パスがない場合、置き換え対象
        return True

    # 新しく設定しようとしている出力ファイルパスの正規表現
    escaped_motion_camera_vmd_file_name = escape_filepath(os.path.join(motion_camera_vmd_dir_path, motion_camera_vmd_file_name))
    escaped_rep_pmx_file_name = escape_filepath(rep_pmx_file_name)
    escaped_motion_camera_vmd_ext = escape_filepath(motion_camera_vmd_ext)

    new_output_camera_vmd_pattern = re.compile(r'^%s_%s%s%s$' % (escaped_motion_camera_vmd_file_name, \
                                               escaped_rep_pmx_file_name, r"_\d{8}_\d{6}", escaped_motion_camera_vmd_ext))
    
    # 自動生成ルールに則ったファイルパスである場合、合致あり
    return re.match(new_output_camera_vmd_pattern, output_camera_vmd_path) is not None


# スムージングVMD出力ファイルパス生成
# base_file_path: モーションスムージングVMDパス
# pmx_path: 変換先モデルPMXパス
# output_smooth_vmd_path: 出力ファイルパス
def get_output_smooth_vmd_path(base_file_path: str, pmx_path: str, output_smooth_vmd_path: str, interpolation: int, loop_cnt: int, is_force=False):
    # モーションスムージングVMDパスの拡張子リスト
    if not os.path.exists(base_file_path) or not os.path.exists(pmx_path):
        return ""

    # モーションスムージングVMDディレクトリパス
    motion_smooth_vmd_dir_path = get_dir_path(base_file_path)
    # モーションスムージングVMDファイル名・拡張子
    motion_smooth_vmd_file_name, motion_smooth_vmd_ext = os.path.splitext(os.path.basename(base_file_path))
    # 変換先モデルファイル名・拡張子
    rep_pmx_file_name, _ = os.path.splitext(os.path.basename(pmx_path))

    # 補間方法
    suffix = "{0}{1}{2}".format(
        ("F" if interpolation == 0 else ""),
        ("C" if interpolation == 1 else ""),
        ("V" if interpolation == 2 else ""),
    )

    if len(suffix) > 0:
        suffix = "_{0}".format(suffix)
    
    suffix = "{0}_L{1}".format(suffix, loop_cnt)

    # 出力ファイルパス生成
    new_output_smooth_vmd_path = os.path.join(motion_smooth_vmd_dir_path, "{0}_{1}{2}_{3:%Y%m%d_%H%M%S}{4}".format(motion_smooth_vmd_file_name, rep_pmx_file_name, suffix, datetime.now(), ".vmd"))

    # ファイルパス自体が変更されたか、自動生成ルールに則っている場合、ファイルパス変更
    if is_force or is_auto_smooth_vmd_output_path(output_smooth_vmd_path, motion_smooth_vmd_dir_path, motion_smooth_vmd_file_name, ".vmd", rep_pmx_file_name):

        try:
            open(new_output_smooth_vmd_path, 'w')
            os.remove(new_output_smooth_vmd_path)
        except Exception:
            logger.warning("出力ファイルパスの生成に失敗しました。以下の原因が考えられます。\n" \
                           + "・ファイルパスが255文字を超えている\n" \
                           + "・ファイルパスに使えない文字列が含まれている（例) \\　/　:　*　?　\"　<　>　|）" \
                           + "・出力ファイルパスの親フォルダに書き込み権限がない" \
                           + "・出力ファイルパスに書き込み権限がない")

        return new_output_smooth_vmd_path

    return output_smooth_vmd_path


# 自動生成ルールに則ったパスか
def is_auto_smooth_vmd_output_path(output_smooth_vmd_path: str, motion_smooth_vmd_dir_path: str, motion_smooth_vmd_file_name: str, motion_smooth_vmd_ext: str, rep_pmx_file_name: str):
    if not output_smooth_vmd_path:
        # 出力パスがない場合、置き換え対象
        return True

    # 新しく設定しようとしている出力ファイルパスの正規表現
    escaped_motion_smooth_vmd_file_name = escape_filepath(os.path.join(motion_smooth_vmd_dir_path, motion_smooth_vmd_file_name))
    escaped_rep_pmx_file_name = escape_filepath(rep_pmx_file_name)
    escaped_motion_smooth_vmd_ext = escape_filepath(motion_smooth_vmd_ext)

    new_output_smooth_vmd_pattern = re.compile(r'^%s_%s%s%s$' % (escaped_motion_smooth_vmd_file_name, \
                                               escaped_rep_pmx_file_name, r"_?\w*_L\d+_\d{8}_\d{6}", escaped_motion_smooth_vmd_ext))
    
    # 自動生成ルールに則ったファイルパスである場合、合致あり
    return re.match(new_output_smooth_vmd_pattern, output_smooth_vmd_path) is not None


def escape_filepath(path: str):
    path = path.replace("\\", "\\\\")
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
