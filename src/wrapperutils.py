#! env python
# -*- coding: utf-8 -*-

import os.path
import traceback
import copy
from datetime import datetime
from pathlib import Path
from PyQt5.QtGui import QQuaternion, QVector3D
import re

import main
from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader
from VmdReader import VmdReader
import utils

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VmdSizing").getChild(__name__)

def is_executable(vmd_path, org_pmx_path, rep_pmx_path):

    # 調整対象vmdファイル
    is_vmd = is_valid_file(vmd_path, "調整対象VMDファイル", ".vmd")

    # モーション作成元モデルPMXファイル
    is_org_pmx = is_valid_file(org_pmx_path, "モーション作成元モデルPMXファイル", ".pmx")

    # モーション変換先モデルPMXファイル
    is_rep_pmx = is_valid_file(rep_pmx_path, "モーション変換先モデルPMXファイル", ".pmx")

    # 全ファイル一括チェック
    return is_vmd and is_org_pmx and is_rep_pmx

def is_valid_file(file_path, file_type, ext, is_print=True):

    if not os.path.exists(file_path):
        if is_print:
            print("■■■■■■■■■■■■■■■■■")
            print("■　**ERROR**　")
            print("■　"+ file_type +"が見つかりませんでした。")
            print("■　入力パス: "+ file_path )
            print("■■■■■■■■■■■■■■■■■")

        return False
    
    if not os.path.isfile(file_path):
        if is_print:
            print("■■■■■■■■■■■■■■■■■")
            print("■　**ERROR**　")
            print("■　"+ file_type +"が正常なファイルとして見つかりませんでした。")
            print("■　入力パス: "+ file_path )
            print("■■■■■■■■■■■■■■■■■")

        return False
    
    # ボーンCSVファイル名・拡張子
    file_name, test_ext = os.path.splitext(os.path.basename(file_path))
    # logger.info("file_name: %s, test_ext: %s", file_name, test_ext)

    if ext.lower() != test_ext.lower():
        if is_print:
            print("■■■■■■■■■■■■■■■■■")
            print("■　**ERROR**　")
            print("■　"+ file_type +"の拡張子が正しくありません。")
            print("■　入力パス: "+ file_path )
            print("■　設定可能拡張子: "+ ext )
            print("■■■■■■■■■■■■■■■■■")

        return False
    
    return True

def is_all_sizing(motion, org_pmx, rep_pmx, error_file_handler=None, error_file_logger=None):
    if org_pmx and rep_pmx and motion:
        not_org_bones = []
        not_org_morphs = []
        not_rep_bones = []
        not_rep_morphs = []

        # 両方のPMXが読めて、モーションも読み込めた場合、キーチェック
        
        # ボーン
        for k in motion.frames.keys():
            if len(motion.frames[k]) > 1 or (motion.frames[k][0].position != QVector3D() or motion.frames[k][0].rotation != QQuaternion()):
                # print("k :%s, len: %s, pos: %s, rot: %s" % ( k, len(motion.frames[k]), motion.frames[k][0].position, motion.frames[k][0].rotation))

                # キーが存在しており、かつ初期値ではない値が入っている場合、警告対象
                if k not in org_pmx.bones:
                    not_org_bones.append(k)

                if k not in rep_pmx.bones:
                    not_rep_bones.append(k)

        # モーフ
        for k in motion.morphs.keys():
            if len(motion.morphs[k]) > 1 or motion.morphs[k][0].ratio != 0:
                # print("k :%s, len: %s, ratio: %s" % ( k, len(motion.morphs[k]), motion.morphs[k][0].ratio != 0))
                # if k == "瞳縦潰れ":
                #     print([x.frame for x in motion.morphs[k]])
                # キーが存在しており、かつ初期値ではない値が入っている場合、警告対象
                if k not in org_pmx.morphs:
                    not_org_morphs.append(k)

                if k not in rep_pmx.morphs:
                    not_rep_morphs.append(k)

        # 何かしら不足しているか
        is_shortage = False
        
        if len(not_org_bones) > 0 or len(not_org_morphs) > 0:
            if error_file_handler:
                error_file_logger = utils.create_error_file_logger(motion, org_pmx, rep_pmx, error_file_handler)
                print_method = error_file_logger.info
            else:
                print_method = print

            print_method("■■■■■■■■■■■■■■■■■")
            print_method("■　**WARNING**　")
            print_method("■　トレース元のモデルにモーションで使用されているボーン・モーフが不足しています。")
            print_method("■　ボーン: %s" % ",".join(not_org_bones))
            print_method("■　モーフ: %s" % ",".join(not_org_morphs))
            print_method("■■■■■■■■■■■■■■■■■")

            is_shortage = True

        if len(not_rep_bones) > 0 or len(not_rep_morphs) > 0:
            if error_file_handler:
                error_file_logger = utils.create_error_file_logger(motion, org_pmx, rep_pmx, error_file_handler)
                print_method = error_file_logger.info
            else:
                print_method = print

            print_method("■■■■■■■■■■■■■■■■■")
            print_method("■　**WARNING**　")
            print_method("■　変換後のモデルにモーションで使用されているボーン・モーフが不足しています。")
            print_method("■　ボーン: %s" % ",".join(not_rep_bones))
            print_method("■　モーフ: %s" % ",".join(not_rep_morphs))
            print_method("■■■■■■■■■■■■■■■■■")

            is_shortage = True

        if is_shortage == False and not error_file_handler:
            # OKのメッセージはUIログのみ
            print("■■■■■■■■■■■■■■■■■")
            print("■　**OK**　")
            print("■　変換後のモデルにモーションで使用されているボーン・モーフが揃っています。")
            print("■■■■■■■■■■■■■■■■■")

            return True, None

    return False

def read_vmd(path, filetype="vmd", is_print=True):
    if is_valid_file(path, filetype, ".vmd", is_print) == False:
        return None

    reader = VmdReader()
    try:
        vmd = reader.read_vmd_file(path)
    except Exception as e:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMDデータの解析に失敗しました。")
        print("■■■■■■■■■■■■■■■■■")
        
        print(traceback.format_exc())

        return None
            
    return vmd

def read_vmd_modelname(path):
    if is_valid_file(path, "vmd", ".vmd", False) == False:
        return None

    reader = VmdReader()
    try:
        model_name = reader.read_vmd_file_modelname(path)
    except Exception as e:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMDデータの解析に失敗しました。")
        print("■■■■■■■■■■■■■■■■■")
        
        print(traceback.format_exc())

        return None
            
    return model_name


def read_pmx(path, filetype="pmx", is_print=True):
    if is_valid_file(path, filetype, ".pmx", is_print) == False:
        return None

    reader = PmxReader()
    try:
        pmx = reader.read_pmx_file(path)
    except Exception as e:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　PMXデータの解析に失敗しました。")
        print("■■■■■■■■■■■■■■■■■")
        
        print(traceback.format_exc())

        return None
            
    return pmx


def exec(motion, org_pmx, rep_pmx, vmd_path, org_pmx_path, rep_pmx_path, output_vmd_path, is_avoidance, is_avoidance_finger, is_hand_ik, hand_distance, vmd_choice_values, rep_choice_values, rep_rate_values, error_file_handler):
    print("■■■■■■■■■■■■■■■■■")
    print("■　VMDサイジング処理実行")
    print("■■■■■■■■■■■■■■■■■")

    error_path = re.sub(r'\.vmd$', ".log", output_vmd_path)
    error_file_handler = logging.FileHandler(error_path)
    error_file_logger = None

    try:
        if not output_vmd_path:
            output_vmd_path = create_output_path(vmd_path, rep_pmx_path, is_avoidance, is_hand_ik, len(vmd_choice_values) > 0)
            if output_vmd_path == None:
                return False
        
        # ディレクトリ作っとく
        new_dir = os.path.dirname(output_vmd_path)
        if os.path.exists(new_dir) == False:
            print("出力対象vmdファイル用フォルダ作成 %s" % new_dir)
            os.makedirs(new_dir, exist_ok=True)
        else:
            if os.path.isdir(new_dir) == False:
                print("■■■■■■■■■■■■■■■■■")
                print("■　**ERROR**　")
                print("■　生成予定のファイルパスのフォルダ構成が正しくないため、処理を中断します。")
                print("■　生成予定パス: "+ output_vmd_path )
                print("■■■■■■■■■■■■■■■■■")

                return False

        # VMD読み込み
        if not motion:
            motion = read_vmd(vmd_path)

        # トレース元モデル
        if not org_pmx:
            org_pmx = read_pmx(org_pmx_path)

        # 変換先モデル
        if not rep_pmx:
            rep_pmx = read_pmx(rep_pmx_path)
        
        if motion and org_pmx and rep_pmx:
            # ファイル出力タイプでサイジングチェック
            is_all_sizing(motion, org_pmx, rep_pmx, error_file_handler, error_file_logger)

            # 実処理実行
            # 読み込んだモーションデータそのものを弄らないよう、コピーした結果を渡す
            main.main(copy.deepcopy(motion), org_pmx, rep_pmx, output_vmd_path, is_avoidance, is_avoidance_finger, is_hand_ik, hand_distance, vmd_choice_values, rep_choice_values, rep_rate_values, error_file_handler, error_file_logger)
        else:
            print("ファイルデータが正しく読み込まれていないようです。\nもう一度ボタンをクリックしてみてください。")
            return False

    except SizingException as e:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMDサイジング処理が処理できないデータで終了しました。")
        print("■■■■■■■■■■■■■■■■■")
        print("")
        print(e.message)

        error_file_logger = utils.create_error_file_logger(motion, org_pmx, rep_pmx, error_file_handler)
        
        error_file_logger.error("■■■■■■■■■■■■■■■■■")
        error_file_logger.error("■　**ERROR**　")
        error_file_logger.error("■　VMDサイジング処理が処理できないデータで終了しました。")
        error_file_logger.error("■■■■■■■■■■■■■■■■■")

        error_file_logger.error(e.message)

    except Exception:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMDサイジング処理が意図せぬエラーで終了しました。")
        print("■■■■■■■■■■■■■■■■■")

        print(traceback.format_exc())

        error_file_logger = utils.create_error_file_logger(motion, org_pmx, rep_pmx, error_file_handler)
        
        error_file_logger.error("■■■■■■■■■■■■■■■■■")
        error_file_logger.error("■　**ERROR**　")
        error_file_logger.error("■　VMDサイジング処理が意図せぬエラーで終了しました。")
        error_file_logger.error("■■■■■■■■■■■■■■■■■")

        error_file_logger.error(traceback.format_exc())
    finally:
        logging.shutdown()

def create_output_path(vmd_path, replace_pmx_path, is_avoidance, is_arm_ik, is_morph):
    # print("vmd_path: %s " % vmd_path)
    # print("replace_pmx_path: %s" % replace_pmx_path)
    # print("is_morph: %s" % is_morph)

    if not os.path.exists(vmd_path) or not os.path.exists(replace_pmx_path):
        return None

    # ボーンCSVファイル名・拡張子
    bone_filename, _ = os.path.splitext(os.path.basename(replace_pmx_path))

    # 腕サフィックス
    arm_suffix = ""
    if is_avoidance: arm_suffix = "A"
    if is_arm_ik: arm_suffix = "P"

    # モーフサフィックス
    morph_suffix = ""
    if is_morph: morph_suffix = "M"

    output_vmd_path = os.path.join(str(Path(vmd_path).resolve().parents[0]), os.path.basename(vmd_path).replace(".vmd", "_{1}{2}{3}_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now(), bone_filename, morph_suffix, arm_suffix)))

    if len(output_vmd_path) >= 255 and os.name == "nt":
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　生成予定のファイルパスがWindowsの制限を超えているため、処理を中断します。")
        print("■　生成予定パス: "+ output_vmd_path )
        print("■■■■■■■■■■■■■■■■■")
        return None
    
    return output_vmd_path
