# -*- coding: utf-8 -*-
#
import os
import glob
from datetime import datetime
from utils import MFileutils
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


# VMD出力ファイルパス生成
def set_output_vmd_path(form):
    # モーションVMDパス(アスタリスク込み)
    motion_vmd_all_path = form.file_panel_ctrl.motion_vmd_file_ctrl.file_ctrl.GetPath()
    # モーションVMDパスの拡張子リスト
    file_path_list = [p for p in glob.glob(motion_vmd_all_path) if os.path.isfile(p)]

    # 変換先モデルPMXパス
    rep_pmx_path = form.file_panel_ctrl.rep_model_file_ctrl.file_ctrl.GetPath()

    if len(file_path_list) == 0 or (len(file_path_list) > 0 and not os.path.exists(file_path_list[0])) or not os.path.exists(rep_pmx_path):
        return

    # モーションVMDディレクトリパス
    motion_vmd_dir_path = MFileutils.get_dir_path(file_path_list[0])
    # モーションVMDファイル名・拡張子
    motion_vmd_file_name, motion_vmd_ext = os.path.splitext(os.path.basename(file_path_list[0]))
    # 変換先モデルファイル名・拡張子
    rep_pmx_file_name, _ = os.path.splitext(os.path.basename(rep_pmx_path))

    # 腕サフィックス
    # モーフサフィックス
    # 腕捩り
    # 代替モデル
    suffix = ""

    # 出力ファイルパス生成
    output_vmd_path = os.path.join(motion_vmd_dir_path, "{0}_{1}{2}_{3:%Y%m%d_%H%M%S}{4}".format(motion_vmd_file_name, rep_pmx_file_name, suffix, datetime.now(), motion_vmd_ext))

    form.file_panel_ctrl.output_vmd_file_ctrl.file_ctrl.SetPath(output_vmd_path)

    if len(output_vmd_path) >= 255 and os.name == "nt":
        logger.error("生成予定のファイルパスがWindowsの制限を超えています。\n生成予定パス: {0}".format(output_vmd_path), decoration=MLogger.DECORATION_BOX)


def on_select_all(event, target_ctrl):
    keyInput = event.GetKeyCode()
    if keyInput == 1:  # 1 stands for 'ctrl+a'
        target_ctrl.SelectAll()
    event.Skip()
        